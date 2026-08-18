# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "elevenlabs>=2.5.0",
#     "inflect>=7.4.0",
# ]
# ///

"""
Audition male voices before committing the year to a cast.

Two passes, because they answer different questions:

  solo    every candidate reads the same short day, so they can be compared
          against each other on identical text
  mockup  a proposed cast reads several real days end to end, so the handoff
          between catechist and respondent can be judged as a listener hears it

Nothing here writes to the catalogue. Output lands in audio/bakeoff/ for
listening; the winners go into audio/cast.json by hand.

Usage:
    uv run scripts/audio_bakeoff.py list
    uv run scripts/audio_bakeoff.py solo --day 03/25 --limit 12
    uv run scripts/audio_bakeoff.py mockup --cast VOICE_A,VOICE_B,VOICE_C
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from elevenlabs.client import ElevenLabs  # noqa: E402

from generate_audio import (  # noqa: E402
    CONTENT,
    apply_overrides,
    concat,
    load_json,
    segments_for,
    synthesise,
    write_silence,
)

REPO = Path(__file__).parent.parent
OUT = REPO / "audio" / "bakeoff"
SETTINGS = load_json(REPO / "audio" / "cast.json")["settings"]
MODEL = load_json(REPO / "audio" / "cast.json")["model"]

# Days chosen to cover the three shapes the year actually takes: a single
# catechism question, a Confession prose paragraph, and a day that pairs two
# readings from different documents.
MOCKUP_DAYS = [("03", "25"), ("01", "14"), ("01", "01")]


def client():
    return ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])


def male_voices(api):
    """Every English-ish male voice the account can reach, newest first."""
    found = []
    for voice in api.voices.get_all().voices:
        labels = voice.labels or {}
        if (labels.get("gender") or "").lower() != "male":
            continue
        found.append(
            {
                "id": voice.voice_id,
                "name": voice.name,
                "accent": labels.get("accent", ""),
                "age": labels.get("age", ""),
                "use_case": labels.get("use_case", labels.get("description", "")),
            }
        )
    return found


def cmd_list(args):
    for voice in male_voices(client()):
        print(f"{voice['id']}  {voice['name']:<22} {voice['age']:<12} "
              f"{voice['accent']:<12} {voice['use_case']}")


def render(api, segments, destination):
    """Synthesise role-tagged segments and join them with their gaps."""
    import tempfile

    with tempfile.TemporaryDirectory() as workdir:
        workdir = Path(workdir)
        parts = []
        for i, (voice_id, text, gap) in enumerate(segments):
            part = workdir / f"{i:03d}.mp3"
            part.write_bytes(synthesise(api, text, voice_id, SETTINGS, MODEL))
            parts.append(part)
            if gap > 0:
                silence = workdir / f"{i:03d}-gap.mp3"
                write_silence(silence, gap)
                parts.append(silence)
        destination.parent.mkdir(parents=True, exist_ok=True)
        concat(parts, destination)


def day_segments(month, day, voice_for):
    overrides = load_json(REPO / "audio" / "overrides.json")
    data = apply_overrides(
        load_json(CONTENT / month / day / "data.json"), month, day, overrides
    )
    return [
        (voice_for(s.role), s.text, s.gap_after)
        for s in segments_for(data, "respondent")
    ]


def cmd_solo(args):
    """One candidate, one day, whole reading in that single voice."""
    api = client()
    month, day = args.day.split("/")
    candidates = male_voices(api)[: args.limit]
    print(f"auditioning {len(candidates)} voices on {month}/{day}")
    for voice in candidates:
        safe = "".join(c if c.isalnum() else "-" for c in voice["name"])
        destination = OUT / "solo" / f"{safe}-{voice['id'][:8]}.mp3"
        segments = day_segments(month, day, lambda role: voice["id"])
        render(api, segments, destination)
        print(f"  {destination.name}")


def cmd_mockup(args):
    """A proposed cast reading real days, to judge the handoff."""
    api = client()
    catechist, respondent, confessor = args.cast.split(",")
    roles = {"catechist": catechist, "confessor": confessor}
    for month, day in MOCKUP_DAYS:
        destination = OUT / "mockup" / f"{month}{day}.mp3"
        segments = day_segments(
            month, day, lambda role: roles.get(role, respondent)
        )
        render(api, segments, destination)
        print(f"  {destination}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="print every male voice on the account")

    solo = sub.add_parser("solo", help="each candidate reads the same day")
    solo.add_argument("--day", default="03/25")
    solo.add_argument("--limit", type=int, default=12)

    mockup = sub.add_parser("mockup", help="a cast reads real days end to end")
    mockup.add_argument(
        "--cast", required=True,
        help="three voice ids: catechist,respondent,confessor",
    )

    args = parser.parse_args()
    {"list": cmd_list, "solo": cmd_solo, "mockup": cmd_mockup}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
