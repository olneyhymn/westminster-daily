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
import json
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
    return ElevenLabs(api_key=os.environ["ELEVEN_LABS_API_KEY"])


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


MOCKUP_SHAPES = {
    ("03", "25"): "One catechism question — the commonest shape of the year",
    ("01", "14"): "Confession prose, no question — 171 days look like this",
    ("01", "01"): "Two documents in one day — 122 days pair readings",
}


def write_manifest(candidates):
    """
    Record the audition: full voice ids, their labels, and the file each one
    produced. The dashboard reads this instead of calling the API, so browsing
    the results never spends credits or needs a key.
    """
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {
        "candidates": [
            dict(voice, solo=f"solo/{solo_filename(voice)}") for voice in candidates
        ],
        "mockups": [
            {
                "day": f"{month}/{day}",
                "file": f"mockup/{month}{day}.mp3",
                "shape": shape,
            }
            for (month, day), shape in MOCKUP_SHAPES.items()
        ],
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def cmd_manifest(args):
    write_manifest(
        [v for v in male_voices(client()) if not args.voices
         or v["id"] in args.voices.split(",")]
    )
    print(f"wrote {OUT / 'manifest.json'}")


def solo_filename(voice):
    safe = "".join(c if c.isalnum() else "-" for c in voice["name"])
    return f"{safe}-{voice['id'][:8]}.mp3"


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
    catalogue = male_voices(api)
    if args.voices:
        wanted = args.voices.split(",")
        by_id = {v["id"]: v for v in catalogue}
        candidates = [by_id[v] for v in wanted if v in by_id]
    else:
        candidates = catalogue[: args.limit]
    print(f"auditioning {len(candidates)} voices on {month}/{day}")
    write_manifest(candidates)
    for voice in candidates:
        destination = OUT / "solo" / solo_filename(voice)
        segments = day_segments(month, day, lambda role: voice["id"])
        render(api, segments, destination)
        print(f"  {destination.name}")


def cmd_handoff(args):
    """
    The same day, once per respondent, with the catechist held constant.

    A mockup shows one handoff; this shows the seam as the only variable, which
    is the comparison that decides whether a rotation is audible or wasted.
    """
    api = client()
    cast = load_json(REPO / "audio" / "cast.json")
    manifest = json.loads((OUT / "manifest.json").read_text())
    names = {c["id"]: c["name"].split(" - ")[0] for c in manifest["candidates"]}
    month, day = args.day.split("/")
    fixed = {
        "catechist": cast["voices"]["catechist"],
        "confessor": cast["voices"]["confessor"],
    }

    entries = []
    for key in cast["respondents"]:
        voice_id = cast["voices"][key]
        name = names.get(voice_id, key)
        destination = OUT / "handoff" / f"{name}.mp3"
        render(api, day_segments(month, day, lambda role: fixed.get(role, voice_id)),
               destination)
        entries.append({
            "respondent": name,
            "file": f"handoff/{name}.mp3",
            "day": f"{month}/{day}",
        })
        print(f"  {destination.name}")

    manifest["handoffs"] = {
        "day": f"{month}/{day}",
        "catechist": names.get(fixed["catechist"], "catechist"),
        "takes": entries,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))


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

    manifest = sub.add_parser("manifest", help="rewrite manifest.json only")
    manifest.add_argument("--voices", default="")

    solo = sub.add_parser("solo", help="each candidate reads the same day")
    solo.add_argument("--day", default="03/25")
    solo.add_argument("--limit", type=int, default=12)
    solo.add_argument("--voices", default="",
                      help="comma-separated voice ids; overrides --limit")

    handoff = sub.add_parser(
        "handoff", help="one day per respondent, catechist held constant")
    handoff.add_argument("--day", default="03/25")

    mockup = sub.add_parser("mockup", help="a cast reads real days end to end")
    mockup.add_argument(
        "--cast", required=True,
        help="three voice ids: catechist,respondent,confessor",
    )

    args = parser.parse_args()
    {
        "list": cmd_list,
        "solo": cmd_solo,
        "mockup": cmd_mockup,
        "manifest": cmd_manifest,
        "handoff": cmd_handoff,
    }[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
