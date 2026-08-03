#!/usr/bin/env python3
"""
Generate one evergreen page per catechism question and per confession chapter.

The site is addressed entirely by calendar date. Nobody searches for "the
reading for March 25" -- they search for "Westminster Shorter Catechism
Question 1" or "Westminster Confession chapter 3". Worse, 32 of the 33
Confession chapters are split across several dates, so no page anywhere on the
site holds a complete chapter.

Everything needed to fix that already exists in content/MM/DD/data.json, which
carries citation, number, chapter, question, answer, and body for every day.
This script reshapes that into:

    /westminster-shorter-catechism/        index of all 107
    /westminster-shorter-catechism/1/      one question
    /westminster-larger-catechism/         index of all 196
    /westminster-larger-catechism/39/
    /westminster-confession/               index of all 33 chapters
    /westminster-confession/3/             a whole chapter, all paragraphs

Each page links back to the date(s) on which it is read, so the reference tree
and the daily plan reinforce each other rather than competing.

Note: these pages carry no ESV text. Proof texts live only in the per-day
`content_with_prooftexts` HTML and stay on the date pages, so the reference
tree is entirely public-domain material.
"""

from __future__ import annotations

import html
import json
import shutil
from collections import defaultdict
from pathlib import Path

CONTENT_DIR = Path("content")
OUTPUT_DIR = Path("content-reference")

DOCUMENTS = {
    "wsc": {
        "slug": "westminster-shorter-catechism",
        "title": "Westminster Shorter Catechism",
        "short": "Shorter Catechism",
        "blurb": (
            "The Westminster Shorter Catechism sets out the theology of "
            "Scripture in 107 questions and answers. It was completed by the "
            "Westminster Assembly in 1647 and has been memorized by "
            "Presbyterian children and adults ever since."
        ),
    },
    "wlc": {
        "slug": "westminster-larger-catechism",
        "title": "Westminster Larger Catechism",
        "short": "Larger Catechism",
        "blurb": (
            "The Westminster Larger Catechism expands on the Shorter in 196 "
            "questions and answers, with fuller treatment of the law, the "
            "sacraments, prayer, and the church."
        ),
    },
    "wcf": {
        "slug": "westminster-confession",
        "title": "Westminster Confession of Faith",
        "short": "Confession of Faith",
        "blurb": (
            "The Westminster Confession of Faith organizes the core teaching "
            "of Scripture into thirty-three topically arranged chapters. It "
            "has served as the doctrinal standard of Presbyterian churches "
            "since the seventeenth century."
        ),
    },
}


def load_days() -> list[tuple[str, str, dict]]:
    """Every (month, day, data) triple in the content tree, in calendar order."""
    days = []
    for path in sorted(CONTENT_DIR.glob("*/*/data.json")):
        month, day = path.parent.parts[-2:]
        with path.open() as f:
            days.append((month, day, json.load(f)))
    return days


def collect():
    """
    Fold the per-day data into per-question and per-chapter records.

    Returns {abbv: {key: record}} where key is the question number or the
    chapter number, and each record carries the text plus every date on which
    it is read. A handful of readings are assigned twice by the plan, which is
    why `dates` is a list.
    """
    entries: dict[str, dict[str, dict]] = {k: {} for k in DOCUMENTS}

    for month, day, data in load_days():
        for item in data.get("content", []):
            abbv = item.get("abbv")
            if abbv not in DOCUMENTS:
                continue

            if item.get("type") == "confession":
                key = item.get("chapter")
                if not key:
                    continue
                record = entries[abbv].setdefault(
                    key,
                    {
                        "key": key,
                        "title": item.get("title", ""),
                        "paragraphs": {},
                        "dates": [],
                    },
                )
                paragraph = item.get("paragraph")
                if paragraph and paragraph not in record["paragraphs"]:
                    record["paragraphs"][paragraph] = item.get("body", "")
                if not record["title"] and item.get("title"):
                    record["title"] = item["title"]
            else:
                key = item.get("number")
                if not key:
                    continue
                record = entries[abbv].setdefault(
                    key,
                    {
                        "key": key,
                        "question": item.get("question", ""),
                        "answer": item.get("answer", ""),
                        "citation": item.get("citation", ""),
                        "dates": [],
                    },
                )

            if (month, day) not in record["dates"]:
                record["dates"].append((month, day))

    return entries


def sort_key(key: str) -> tuple:
    """Numeric ordering, tolerating any non-numeric key by sorting it last."""
    try:
        return (0, int(key))
    except (TypeError, ValueError):
        return (1, key)


def chapter_heading(record: dict) -> str:
    """'Chapter 1: Of the Holy Scripture' -> 'Of the Holy Scripture'."""
    title = record.get("title") or ""
    if ":" in title:
        return title.split(":", 1)[1].strip()
    return title.strip()


def date_links(dates: list[tuple[str, str]]) -> str:
    """Link back to the daily reading(s) this appears in."""
    if not dates:
        return ""
    from datetime import date as _date

    parts = []
    for month, day in dates:
        # Leap year, so a Feb 29 reading still formats.
        label = _date(2024, int(month), int(day)).strftime("%B %-d")
        parts.append(f'<a href="/westminster-daily/{month}/{day}">{label}</a>')
    joined = " and ".join(parts) if len(parts) < 3 else ", ".join(parts)
    return (
        f'<p class="reference-dates">Read on {joined} '
        f'in the <a href="/westminster-daily/">Westminster Daily</a> plan, '
        f"where the proof texts are printed in full.</p>"
    )


def front_matter(pagetitle: str, canonical: str, extra: dict) -> str:
    lines = ["---", f'pagetitle: "{pagetitle}"', f"canonical_url: {canonical}"]
    for key, value in extra.items():
        if value:
            lines.append(f'{key}: "{value}"')
    lines.append("---")
    return "\n".join(lines)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + "\n", encoding="utf-8")


def render_item(abbv: str, record: dict, prev_rec, next_rec) -> str:
    doc = DOCUMENTS[abbv]
    key = record["key"]
    slug = doc["slug"]

    if abbv == "wcf":
        heading = chapter_heading(record)
        pagetitle = f"{doc['title']} Chapter {key}: {heading}"
        paragraphs = sorted(record["paragraphs"].items(), key=lambda kv: sort_key(kv[0]))
        body = "\n".join(f"<div class=\"wcf-paragraph\">{b}</div>" for _, b in paragraphs)
        heading_html = (
            f"<h1>{html.escape(doc['title'], quote=False)}</h1>\n"
            f"<h2>Chapter {html.escape(key)}: {html.escape(heading, quote=False)}</h2>"
        )
    else:
        question = record["question"]
        answer = record["answer"]
        pagetitle = f"{doc['title']} Q{key}: {question}"
        body = (
            f'<div class="reference-qa">'
            f'<p class="q"><span class="q-label">Q. {html.escape(key)}.</span> '
            f"{html.escape(question, quote=False)}</p>"
            f'<p class="a"><span class="q-label">A.</span> {html.escape(answer, quote=False)}</p>'
            f"</div>"
        )
        heading_html = (
            f"<h1>{html.escape(doc['title'], quote=False)}</h1>\n"
            f"<h2>Question {html.escape(key)}</h2>"
        )

    # Guillemets and gold separators, matching the daily site's date row.
    nav = []
    if prev_rec:
        label = "Chapter" if abbv == "wcf" else "Q"
        sep = " " if abbv == "wcf" else ""
        nav.append(
            f'<a href="/{slug}/{prev_rec["key"]}/">&lsaquo;&nbsp;{label}{sep}{prev_rec["key"]}</a>'
        )
    unit = "chapters" if abbv == "wcf" else "questions"
    nav.append(f'<a href="/{slug}/">All {unit}</a>')
    if next_rec:
        label = "Chapter" if abbv == "wcf" else "Q"
        sep = " " if abbv == "wcf" else ""
        nav.append(
            f'<a href="/{slug}/{next_rec["key"]}/">{label}{sep}{next_rec["key"]}&nbsp;&rsaquo;</a>'
        )
    joiner = '<span class="reference-nav__sep">&middot;</span>'
    nav_html = '<div class="reference-nav">' + joiner.join(nav) + "</div>"

    meta = front_matter(
        pagetitle.replace('"', "'"),
        f"/{slug}/{key}/",
        {
            "doc_title": doc["title"],
            "doc_slug": slug,
            "item_key": key,
            "own_heading": "true",
        },
    )

    return "\n\n".join(
        [meta, heading_html, body, date_links(record["dates"]), nav_html]
    )


def render_index(abbv: str, records: list[dict]) -> str:
    doc = DOCUMENTS[abbv]
    slug = doc["slug"]

    rows = []
    for record in records:
        key = record["key"]
        if abbv == "wcf":
            label = f"Chapter {key}"
            text = chapter_heading(record)
        else:
            label = f"Q{key}"
            text = record["question"]
        rows.append(
            f'<li><a href="/{slug}/{key}/">'
            f'<strong>{html.escape(label, quote=False)}.</strong> {html.escape(text, quote=False)}</a></li>'
        )

    meta = front_matter(
        doc["title"],
        f"/{slug}/",
        {"doc_title": doc["title"], "doc_slug": slug, "own_heading": "true"},
    )

    unit = "chapter" if abbv == "wcf" else "question"
    return "\n\n".join(
        [
            meta,
            f"<h1>{html.escape(doc['title'], quote=False)}</h1>",
            f"<p class=\"reference-blurb\">{html.escape(doc['blurb'], quote=False)}</p>",
            f'<p class="reference-blurb">Each {unit} has its own page below. '
            f'To read the whole of the Westminster Standards over a year, '
            f'one short reading a day, see '
            f'<a href="/westminster-daily/start">Westminster Daily</a>.</p>',
            f'<ul class="reference-index">{"".join(rows)}</ul>',
        ]
    )


def main() -> None:
    entries = collect()

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)

    total = 0
    for abbv, doc in DOCUMENTS.items():
        records = [
            entries[abbv][key] for key in sorted(entries[abbv], key=sort_key)
        ]
        slug = doc["slug"]

        write(OUTPUT_DIR / slug / "index.md", render_index(abbv, records))
        total += 1

        for i, record in enumerate(records):
            prev_rec = records[i - 1] if i > 0 else None
            next_rec = records[i + 1] if i + 1 < len(records) else None
            write(
                OUTPUT_DIR / slug / record["key"] / "index.md",
                render_item(abbv, record, prev_rec, next_rec),
            )
            total += 1

        print(f"  {doc['title']}: {len(records)} pages")

    print(f"Wrote {total} reference pages to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
