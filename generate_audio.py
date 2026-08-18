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
from pathlib import Path

import inflect
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

REPO = Path(__file__).parent
CONTENT = REPO / "content"
CAST_FILE = REPO / "audio" / "cast.json"
OVERRIDES_FILE = REPO / "audio" / "overrides.json"
DEFAULT_OUT = REPO / "audio" / "out"

# Matches the existing catalogue exactly (mono, 44.1 kHz, 128 kbps), so
# regenerated files drop into S3 without changing the shape of the feed.
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
GAP_AFTER_CITATION = 1.0
GAP_AFTER_QUESTION = 0.5
GAP_AFTER_SECTION = 1.0


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


def segments_for(data, respondent):
    """Break a day's reading into role-tagged segments, in order."""
    segments = []
    sections = data["content"]
    for i, section in enumerate(sections):
        last = i == len(sections) - 1
        segments.append(
            Segment("catechist", spoken_citation(section["long_citation"]),
                    GAP_AFTER_CITATION)
        )
        if "question" in section:
            segments.append(
                Segment("catechist", speakable(section["question"].replace("?", "")),
                        GAP_AFTER_QUESTION)
            )
            segments.append(
                Segment(respondent, speakable(section["answer"]),
                        0.0 if last else GAP_AFTER_SECTION)
            )
        else:
            segments.append(
                Segment("confessor", speakable(section["body"]),
                        0.0 if last else GAP_AFTER_SECTION)
            )
    return segments


def respondent_for(month, day, pool):
    """
    Pick the answering voice from the date alone.

    md5 rather than hash(): Python salts str hashing per process, so hash()
    would hand the same day a different voice on every run and quietly
    invalidate the whole cache.
    """
    digest = hashlib.md5(f"{month}{day}".encode()).hexdigest()
    return pool[int(digest, 16) % len(pool)]


def fingerprint(segments, cast, model):
    """
    Identify a rendering by everything that could change how it sounds, so a
    re-run regenerates a day when its text or its casting moved and skips it
    otherwise.
    """
    payload = json.dumps(
        {
            "segments": [(s.role, s.text, s.gap_after) for s in segments],
            "voices": {s.role: cast["voices"][s.role] for s in segments},
            "settings": cast["settings"],
            "model": model,
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def synthesise(client, text, voice_id, settings, model):
    """Render one segment to mp3 bytes."""
    stream = client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id=model,
        output_format=OUTPUT_FORMAT,
        voice_settings=VoiceSettings(**settings),
    )
    return b"".join(stream)


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


def render_day(client, month, day, cast, overrides, out_dir, force):
    data_path = CONTENT / month / day / "data.json"
    if not data_path.exists():
        return None

    data = apply_overrides(load_json(data_path), month, day, overrides)
    respondent = respondent_for(month, day, cast["respondents"])
    segments = segments_for(data, respondent)
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
        out_dir.mkdir(parents=True, exist_ok=True)
        concat(parts, destination)

    sidecar.write_text(
        json.dumps(
            {
                "fingerprint": stamp,
                "respondent": respondent,
                "model": model,
                "characters": sum(len(s.text) for s in segments),
                "segments": [{"role": s.role, "text": s.text} for s in segments],
            },
            indent=2,
        )
    )
    return respondent


def resolve_days(spec):
    """Turn "all", "03" or "03/25" into an ordered list of (month, day)."""
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
    parser.add_argument("--days", default="all", help='"all", "03", or "03/25"')
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--force", action="store_true",
                        help="re-render even when the fingerprint matches")
    parser.add_argument("--dry-run", action="store_true",
                        help="report casting and character counts, call nothing")
    args = parser.parse_args()

    cast = load_json(CAST_FILE)
    overrides = load_json(OVERRIDES_FILE)
    days = resolve_days(args.days)

    if args.dry_run:
        total = 0
        tally = {}
        for month, day in days:
            data = apply_overrides(
                load_json(CONTENT / month / day / "data.json"), month, day, overrides
            )
            respondent = respondent_for(month, day, cast["respondents"])
            segments = segments_for(data, respondent)
            total += sum(len(s.text) for s in segments)
            for segment in segments:
                tally[segment.role] = tally.get(segment.role, 0) + len(segment.text)
        print(f"{len(days)} days, {total:,} characters")
        print(f"estimated cost: ${total / 1000 * 0.10:,.2f} at $0.10/1k")
        for role, count in sorted(tally.items(), key=lambda kv: -kv[1]):
            print(f"  {role:<12} {count:>7,} chars")
        return

    client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])
    for month, day in days:
        result = render_day(client, month, day, cast, overrides, args.out, args.force)
        print(f"{month}/{day}: {result}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
