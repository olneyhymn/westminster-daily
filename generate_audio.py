# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "elevenlabs>=2.5.0",
#     "inflect>=7.4.0",
# ]
# ///

"""
Generate the Westminster Daily podcast audio.

The catechisms are dialogue: a question asked, an answer given. The first
generation of this audio read both halves in one flat voice, which collapsed a
call-and-response into a monologue and left every episode of the year sounding
like every other. This script casts the roles instead:

    catechist   reads the citation and the question
    respondent  reads the answer, rotating across a pool so the year varies
    confessor   reads Confession prose, which has no question to ask

The respondent is chosen by hashing the date, so it is stable across runs:
regenerating one day never reshuffles the rest.

Each segment is synthesised on its own and concatenated with measured silence,
which puts pacing under this script's control rather than leaving it to the
model's reading of a break tag.

Usage:
    uv run generate_audio.py --days all
    uv run generate_audio.py --days 03/25 --force
    uv run generate_audio.py --days 03
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import inflect
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

REPO = Path(__file__).parent
CONTENT = REPO / "content"
CAST_FILE = REPO / "audio" / "cast.json"
OVERRIDES_FILE = REPO / "audio" / "overrides.json"
DEFAULT_OUT = REPO / "audio" / "out"
MUSIC = REPO / "audio" / "music"
# Rendered speech, keyed by what determines how it sounds. Arrangement --
# music, gaps, the order of things -- is assembly, and assembly must never
# cost an API call for words already spoken once.
CACHE = REPO / "audio" / "cache"

# Matches the existing catalogue exactly (mono, 44.1 kHz, 128 kbps), so
# regenerated files drop into S3 without changing the shape of the feed.
# Podcast loudness target for mono. Episodes were landing anywhere from -24 to
# -20 LUFS, because the voices differ in inherent level and nothing was
# levelling them, so a listener met a four-decibel step between one day and the
# next and reached for the volume. Measured first and applied as a flat gain,
# so nothing is compressed and the pauses stay as quiet as they were written.
TARGET_LUFS = -19.0
TRUE_PEAK = -1.5
LOUDNESS_RANGE = 11.0

OUTPUT_FORMAT = "mp3_44100_128"
SAMPLE_RATE = 44100
BITRATE = "128k"

TAG_RE = re.compile(r"<[^>]*>")
NUMBER_RE = re.compile(r"\d+")

# Confession bodies open with a paragraph-number span. On the page it is the
# marker in the margin; read aloud it lands immediately after the citation has
# already said the same number, so every one of the 171 Confession readings
# announced its paragraph twice. Drop the element and its contents.
PARAGRAPH_NUMBER_RE = re.compile(
    r"<span[^>]*paragraph-number[^>]*>.*?</span>", re.S
)

# Silence around each part of the reading, in seconds. The citation needs room
# before the question lands; the beat between question and answer is what makes
# the handoff between the two voices audible as a handoff.
# Podcast pacing is tighter than a daily office wants. These are set for
# formation rather than for holding attention: the citation is a new frame and
# needs room, the seam between readings is a real boundary, and the answer
# follows its question closely because it is the response to that question --
# lengthening that particular beat would turn a reply into a recitation.
GAP_AFTER_CITATION = 1.75
GAP_AFTER_QUESTION = 0.5
GAP_AFTER_SECTION = 2.25

# Held silence before the file ends. A reading that stops the instant the last
# word lands gives the listener nowhere to put it, and on a walk this is the
# part actually used.
CLOSING_SILENCE = 4.0

# The longest answer is 1,783 characters and the model reads it as one
# unbroken breath: listening tests put the onset of drone at about forty-five
# seconds, with list items run together and no room to absorb any of them.
# These readings are semicolon-delimited lists by construction, so the
# punctuation already marks where a reader would breathe. Anything past the
# limit is broken at those marks and the pieces are rejoined with a short
# silence.
#
# The limit was 400 first, which listening tests scored no better than no
# split at all: a 400-character chunk is still twenty-five seconds of
# uninterrupted list. At 180 the same passage rated 8/10 against 5/10. Going
# further the other way loses too -- inline break tags scored 6/10, and
# slowing the voice to 0.90 scored worst of all at 4/10, so the fix is
# granularity, not tempo.
MAX_UNBROKEN = 180
GAP_WITHIN_SECTION = 0.35
CLAUSE_RE = re.compile(r"(?<=[;.])\s+")


@dataclass(frozen=True)
class Segment:
    """One continuous stretch of speech in a single voice."""

    role: str
    text: str
    gap_after: float


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def strip_html(raw):
    """Drop tags and entity padding so prooftext markup is never spoken."""
    return TAG_RE.sub(" ", PARAGRAPH_NUMBER_RE.sub(" ", raw)).replace("&nbsp;", " ")


def numbers_to_words(text):
    """
    Spell out digits so the model reads "thirty-nine", not "three nine".

    The previous implementation collected every match and then ran a plain
    str.replace for each one, so an earlier, shorter number rewrote the digits
    of a later one: "Confession of Faith 1.10" came out as "one.one0". Doing it
    as a single pass of re.sub over non-overlapping matches cannot corrupt a
    number it has already passed.
    """
    engine = inflect.engine()
    return NUMBER_RE.sub(lambda m: engine.number_to_words(m.group()), text)


def speakable(text):
    """Normalise any content field into something worth handing to the model."""
    return re.sub(r"\s+", " ", numbers_to_words(strip_html(text))).strip()


def spoken_citation(long_citation):
    """
    "Confession of Faith 1.10" -> "Confession of Faith one, paragraph ten".

    Confession citations are chapter-and-paragraph; read literally the period
    becomes a sentence break and the paragraph number sounds like a new thought.
    """
    return speakable(long_citation.replace(".", ", paragraph "))


def apply_overrides(data, month, day, overrides):
    """
    Swap in hand-written text for the two readings that do not survive
    text-to-speech as authored: the table of the books of Scripture and the
    rules for understanding the commandments. Both are lists whose original
    markup reads as a run-on sentence.
    """
    key = f"{month}/{day}"
    if key not in overrides:
        return data
    rule = overrides[key]
    data["content"][rule["index"]][rule["field"]] = rule["text"]
    return data


def clauses(text, limit=MAX_UNBROKEN):
    """
    Group a long reading into breath-sized pieces, splitting only at the
    punctuation an editor already placed. Clauses are packed up to the limit
    rather than emitted one per piece, so a run of short items still reads as
    a list instead of a series of announcements.
    """
    if len(text) <= limit:
        return [text]
    grouped, buffer = [], ""
    for clause in CLAUSE_RE.split(text):
        if buffer and len(buffer) + len(clause) + 1 > limit:
            grouped.append(buffer)
            buffer = clause
        else:
            buffer = f"{buffer} {clause}".strip()
    if buffer:
        grouped.append(buffer)
    return grouped


def breathe(role, text, gap_after):
    """One reading, as one or more segments in the same voice."""
    pieces = clauses(text)
    return [
        Segment(role, piece, gap_after if i == len(pieces) - 1 else GAP_WITHIN_SECTION)
        for i, piece in enumerate(pieces)
    ]


def sting(part, music):
    """
    A music segment carries a filename where speech carries text.

    Rendering it is a copy rather than a synthesis, so the same segment list,
    the same fingerprint and the same concatenation handle both without a
    parallel code path.
    """
    if not music or not music.get(part):
        return []
    gap = music.get(f"gap_after_{part}", 0.3)
    return [Segment("music", f"{music['style']}-{part}", gap)]


def same_reading(first, second):
    """
    True when two sections ask and answer in identical words.

    Both halves must match. The Shorter and Larger Catechism reach the same
    answer from different questions on 01/15, and collapsing that pair would
    drop a question the reader never gets back -- so answer equality alone is
    not enough to justify saying it once.
    """
    if "question" not in first or "question" not in second:
        return False
    return (
        speakable(first["question"]) == speakable(second["question"])
        and speakable(first["answer"]) == speakable(second["answer"])
    )


def runs_for(sections):
    """
    Group consecutive sections that are word-for-word the same reading.

    The Shorter Catechism condenses the Larger, so on eight days of the year
    the two coincide exactly and one voice would otherwise say the same
    sentence twice in a row, which sounds like a fault in the tape rather than
    two documents agreeing. A run is read once under both citations.
    """
    runs = []
    for section in sections:
        if runs and same_reading(runs[-1][-1], section):
            runs[-1].append(section)
        else:
            runs.append([section])
    return runs


def segments_for(data, respondent, music=None):
    """
    Break a day's reading into role-tagged segments, in order.

    `respondent` may be one voice for the whole day or a callable taking the
    run's index, which is what lets two readings in one day answer in
    different voices.
    """
    voice_for = respondent if callable(respondent) else (lambda i: respondent)
    segments = list(sting("intro", music))
    sections = runs_for(data["content"])
    for i, run in enumerate(sections):
        section = run[0]
        last = i == len(sections) - 1
        tail = 0.0 if last else GAP_AFTER_SECTION
        if i and music:
            # Between readings the catechist already names the next citation,
            # so the marker is there to say "a new reading" before he does.
            segments += sting("seam", music)
        # One reading, every citation that carries it.
        citation = ", and ".join(spoken_citation(s["long_citation"]) for s in run)
        segments += breathe("catechist", citation, GAP_AFTER_CITATION)
        if "question" in section:
            segments += breathe(
                "catechist", speakable(section["question"].replace("?", "")),
                GAP_AFTER_QUESTION,
            )
            segments += breathe(voice_for(i), speakable(section["answer"]), tail)
        else:
            segments += breathe("confessor", speakable(section["body"]), tail)
    return segments + sting("outro", music)


@lru_cache(maxsize=1)
def catechism_runs():
    """
    Every reading that asks a question, in calendar order, mapped to its
    position.

    Counting readings rather than days does two things: Confession-only days
    no longer leave gaps that drift the pool out of step, and a day holding
    two readings draws two consecutive voices, so the pair answer in different
    ones. That matters most on the days the two catechisms nearly coincide,
    where one voice twice sounds like a stutter.
    """
    overrides = load_json(OVERRIDES_FILE)
    order = {}
    for month, day in resolve_days("all"):
        data = apply_overrides(
            load_json(CONTENT / month / day / "data.json"), month, day, overrides
        )
        for i, run in enumerate(runs_for(data["content"])):
            if "question" in run[0]:
                order[(month, day, i)] = len(order)
    return order


def respondent_for(month, day, pool, run=0):
    """
    Pick the answering voice by where the day falls among the days that have
    an answer to give.

    This was an md5 of the date, which distributes acceptably across a year
    and badly across a month: one voice took 53% of April and a third or more
    of eight months, with runs of four consecutive days -- a rotation the
    listener cannot hear is a rotation that was not worth building. Walking the
    pool in order gives every voice 41 or 42 of the 208 days and never repeats
    one two days running.
    """
    return pool[catechism_runs().get((month, day, run), 0) % len(pool)]


def fingerprint(segments, cast, model):
    """
    Identify a rendering by everything that could change how it sounds, so a
    re-run regenerates a day when its text or its casting moved and skips it
    otherwise.
    """
    payload = json.dumps(
        {
            "segments": [(s.role, s.text, s.gap_after) for s in segments],
            "voices": {s.role: cast["voices"][s.role]
                       for s in segments if s.role != "music"},
            "settings": cast["settings"],
            "model": model,
            "tail": CLOSING_SILENCE,
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


SPOKEN = {"hits": 0, "misses": 0, "characters": 0}


def speech_key(text, voice_id, settings, model):
    """Everything that decides how a line sounds, and nothing that does not."""
    payload = json.dumps(
        {"text": text, "voice": voice_id, "settings": settings, "model": model},
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def synthesise(client, text, voice_id, settings, model):
    """
    Render one segment to mp3 bytes, reusing the recording if these exact
    words have been spoken by this voice at these settings before.

    Adding music to a finished month used to re-synthesise every word in it,
    because the day's fingerprint covers arrangement as well as speech. The
    cache separates the two: rearranging is free, and only genuinely new words
    reach the API.
    """
    cached = CACHE / f"{speech_key(text, voice_id, settings, model)}.mp3"
    if cached.exists():
        SPOKEN["hits"] += 1
        return cached.read_bytes()
    stream = client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id=model,
        output_format=OUTPUT_FORMAT,
        voice_settings=VoiceSettings(**settings),
    )
    audio = b"".join(stream)
    CACHE.mkdir(parents=True, exist_ok=True)
    cached.write_bytes(audio)
    SPOKEN["misses"] += 1
    SPOKEN["characters"] += len(text)
    return audio


def ffmpeg(args):
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args],
        check=True,
    )


def write_silence(path, seconds):
    ffmpeg([
        "-f", "lavfi", "-i", f"anullsrc=r={SAMPLE_RATE}:cl=mono",
        "-t", str(seconds), "-c:a", "libmp3lame", "-b:a", BITRATE,
        "-ac", "1", "-ar", str(SAMPLE_RATE), str(path),
    ])


def concat(parts, destination):
    """
    Join the rendered parts. Re-encoding rather than stream-copying: the parts
    come from two sources (the API and ffmpeg's own silence) and only a real
    encode guarantees one continuous, seekable file at the end.
    """
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as manifest:
        for part in parts:
            escaped = str(part).replace("'", r"'\''")
            manifest.write(f"file '{escaped}'\n")
        manifest_path = manifest.name
    try:
        ffmpeg([
            "-f", "concat", "-safe", "0", "-i", manifest_path,
            "-c:a", "libmp3lame", "-b:a", BITRATE,
            "-ac", "1", "-ar", str(SAMPLE_RATE), str(destination),
        ])
    finally:
        os.unlink(manifest_path)


def measure_loudness(path):
    """Read the file's loudness so the correction can be a known, flat gain."""
    probe = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af",
         f"loudnorm=I={TARGET_LUFS}:TP={TRUE_PEAK}:LRA={LOUDNESS_RANGE}"
         ":print_format=json", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    report = probe.stderr
    start, end = report.rfind("{"), report.rfind("}")
    if start < 0 or end < 0:
        return None
    try:
        return json.loads(report[start:end + 1])
    except ValueError:
        return None


def normalise(path):
    """
    Bring one episode to the target, measuring first.

    Single-pass loudnorm rides the level as it goes, which pumps the quiet
    beats between question and answer. Measuring first allows linear mode: one
    gain for the whole file, so the balance written into it survives.
    """
    measured = measure_loudness(path)
    if not measured:
        return False
    settings = ":".join([
        f"loudnorm=I={TARGET_LUFS}", f"TP={TRUE_PEAK}", f"LRA={LOUDNESS_RANGE}",
        f"measured_I={measured['input_i']}",
        f"measured_TP={measured['input_tp']}",
        f"measured_LRA={measured['input_lra']}",
        f"measured_thresh={measured['input_thresh']}",
        "linear=true", "print_format=summary",
    ])
    levelled = path.with_suffix(".levelled.mp3")
    ffmpeg(["-i", str(path), "-af", settings, "-ac", "1", "-ar", str(SAMPLE_RATE),
            "-c:a", "libmp3lame", "-b:a", BITRATE, str(levelled)])
    levelled.replace(path)
    return True


def render_day(client, month, day, cast, overrides, out_dir, force):
    data_path = CONTENT / month / day / "data.json"
    if not data_path.exists():
        return None

    data = apply_overrides(load_json(data_path), month, day, overrides)
    def respondent(run):
        return respondent_for(month, day, cast["respondents"], run)

    segments = segments_for(data, respondent, cast.get("music"))
    model = cast["model"]

    destination = out_dir / f"{month}{day}.mp3"
    sidecar = out_dir / f"{month}{day}.json"
    stamp = fingerprint(segments, cast, model)

    if not force and destination.exists() and sidecar.exists():
        if load_json(sidecar).get("fingerprint") == stamp:
            return "cached"

    with tempfile.TemporaryDirectory() as workdir:
        workdir = Path(workdir)
        parts = []
        for i, segment in enumerate(segments):
            part = workdir / f"{i:03d}.mp3"
            if segment.role == "music":
                part.write_bytes((MUSIC / f"{segment.text}.mp3").read_bytes())
            else:
                part.write_bytes(
                    synthesise(
                        client,
                        segment.text,
                        cast["voices"][segment.role],
                        cast["settings"],
                        model,
                    )
                )
            parts.append(part)
            if segment.gap_after > 0:
                gap = workdir / f"{i:03d}-gap.mp3"
                write_silence(gap, segment.gap_after)
                parts.append(gap)
        if CLOSING_SILENCE:
            close = workdir / "zzz-close.mp3"
            write_silence(close, CLOSING_SILENCE)
            parts.append(close)
        out_dir.mkdir(parents=True, exist_ok=True)
        concat(parts, destination)
    normalise(destination)

    voices = sorted({s.role for s in segments if s.role.startswith("respondent_")})
    sidecar.write_text(
        json.dumps(
            {
                "fingerprint": stamp,
                "respondent": voices,
                "model": model,
                "characters": sum(len(s.text) for s in segments if s.role != "music"),
                "segments": [{"role": s.role, "text": s.text} for s in segments],
            },
            indent=2,
        )
    )
    return ", ".join(v.split("_")[1] for v in voices) or "confession"


def verify(days, cast, overrides, out_dir):
    """
    Check that every requested day is on disk and current.

    A render can stop halfway -- the API runs out of quota, the network drops
    -- and the days already written still look perfectly good on their own.
    Measuring the output cannot tell you a file is simply older than the
    configuration that was supposed to produce it, so this compares each
    sidecar's fingerprint against what today's cast and text would generate.

    Returns the list of problems, empty when everything is current.
    """
    problems = []
    for month, day in days:
        destination = out_dir / f"{month}{day}.mp3"
        sidecar = out_dir / f"{month}{day}.json"
        if not destination.exists():
            problems.append(f"{month}/{day}: missing")
            continue
        if not sidecar.exists():
            problems.append(f"{month}/{day}: no sidecar, cannot tell if current")
            continue

        data = apply_overrides(
            load_json(CONTENT / month / day / "data.json"), month, day, overrides
        )
        segments = segments_for(
            data,
            lambda run: respondent_for(month, day, cast["respondents"], run),
            cast.get("music"),
        )
        if load_json(sidecar).get("fingerprint") != fingerprint(
            segments, cast, cast["model"]
        ):
            problems.append(f"{month}/{day}: stale, predates the current settings")
            continue

        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "stream=codec_name,sample_rate,channels", "-of", "csv=p=0",
             str(destination)],
            capture_output=True, text=True,
        )
        if probe.stdout.strip() != f"mp3,{SAMPLE_RATE},1":
            problems.append(f"{month}/{day}: wrong format ({probe.stdout.strip()})")
            continue

        measured = measure_loudness(destination)
        if measured:
            level = float(measured["input_i"])
            if not TARGET_LUFS - 2.5 <= level <= TARGET_LUFS + 2.5:
                problems.append(f"{month}/{day}: {level:.1f} LUFS, off target")
    return problems


def resolve_days(spec):
    """
    Turn "all", "03", "03/25", or a comma-separated list of those into an
    ordered list of (month, day). A list keeps a run of dates in one process,
    which matters because each invocation otherwise pays for a fresh
    interpreter and a fresh client.
    """
    if "," in spec:
        seen, days = set(), []
        for part in spec.split(","):
            for entry in resolve_days(part.strip()):
                if entry not in seen:
                    seen.add(entry)
                    days.append(entry)
        return days
    if spec == "all":
        return sorted(
            (p.parent.parent.name, p.parent.name)
            for p in CONTENT.glob("*/*/data.json")
        )
    if "/" in spec:
        month, day = spec.split("/")
        return [(month, day)]
    return sorted(
        (p.parent.parent.name, p.parent.name)
        for p in CONTENT.glob(f"{spec}/*/data.json")
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", default="all",
                        help='"all", "03", "03/25", or a comma-separated list')
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--force", action="store_true",
                        help="re-render even when the fingerprint matches")
    parser.add_argument("--dry-run", action="store_true",
                        help="report casting and character counts, call nothing")
    parser.add_argument("--verify", action="store_true",
                        help="check the days on disk are present and current, "
                             "render nothing; exits non-zero if any are not")
    args = parser.parse_args()

    cast = load_json(CAST_FILE)
    overrides = load_json(OVERRIDES_FILE)
    days = resolve_days(args.days)

    if args.verify:
        problems = verify(days, cast, overrides, args.out)
        for problem in problems:
            print(f"  {problem}")
        print(f"{len(days) - len(problems)} of {len(days)} current.")
        return 1 if problems else 0

    if args.dry_run:
        total = 0
        tally = {}
        for month, day in days:
            data = apply_overrides(
                load_json(CONTENT / month / day / "data.json"), month, day, overrides
            )
            segments = segments_for(
                data,
                lambda run: respondent_for(month, day, cast["respondents"], run),
                cast.get("music"),
            )
            total += sum(len(s.text) for s in segments if s.role != "music")
            for segment in segments:
                if segment.role == "music":
                    continue
                tally[segment.role] = tally.get(segment.role, 0) + len(segment.text)
        cached = sum(
            len(s.text)
            for m, d in days
            for s in segments_for(
                apply_overrides(
                    load_json(CONTENT / m / d / "data.json"), m, d, overrides
                ),
                lambda run: respondent_for(m, d, cast["respondents"], run),
                cast.get("music"),
            )
            if s.role != "music"
            and (CACHE / f"{speech_key(s.text, cast['voices'][s.role], cast['settings'], cast['model'])}.mp3").exists()
        )
        due = total - cached
        print(f"{len(days)} days, {total:,} characters")
        print(f"already recorded: {cached:,}   to synthesise: {due:,}")
        print(f"estimated cost: ${due / 1000 * 0.10:,.2f} at $0.10/1k")
        for role, count in sorted(tally.items(), key=lambda kv: -kv[1]):
            print(f"  {role:<12} {count:>7,} chars")
        return

    client = ElevenLabs(api_key=os.environ["ELEVEN_LABS_API_KEY"])
    failures, consecutive = [], 0
    for month, day in days:
        try:
            result = render_day(
                client, month, day, cast, overrides, args.out, args.force
            )
            consecutive = 0
        except Exception as exc:
            # One transient error should not throw away a long run, but a
            # steady stream of them means the quota is gone or the key is
            # dead, and every further call is a wasted round trip.
            failures.append((f"{month}/{day}", str(exc).split("\n")[0][:160]))
            consecutive += 1
            print(f"{month}/{day}: FAILED — {failures[-1][1]}", flush=True)
            if consecutive >= 3:
                print("\nthree failures running; stopping.", flush=True)
                break
            continue
        print(f"{month}/{day}: {result}", flush=True)

    problems = verify(days, cast, overrides, args.out)
    if failures or problems:
        print(f"\n{len(failures)} failed to render, "
              f"{len(problems)} not current after the run:", flush=True)
        for day, why in failures[:10]:
            print(f"  {day}: {why}", flush=True)
        for problem in problems[:10]:
            print(f"  {problem}", flush=True)
        return 1
    print(f"\nall {len(days)} days rendered and verified.", flush=True)
    print(f"speech: {SPOKEN['hits']} reused, {SPOKEN['misses']} newly recorded "
          f"({SPOKEN['characters']:,} characters billed)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
