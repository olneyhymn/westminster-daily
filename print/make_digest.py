#!/usr/bin/env python3
"""Dump a month's readings as a curation digest.

Usage: python make_digest.py MM > digests/MM.md

For each day: title, each reading's question/answer (or confession body) with [n]
footnote markers, and each footnote's references with verse counts.
"""

import json
import re
import sys
import html as html_module
from pathlib import Path

from bs4 import BeautifulSoup

from generate_typst import count_verses, CONTENT_DIR


def plain_text_with_markers(html_str: str) -> str:
    """Convert answer/body HTML to plain text with [n] footnote markers."""
    soup = BeautifulSoup(html_str, "html.parser")
    for sup in soup.find_all("sup"):
        sup.replace_with(f"[{sup.get_text()}]")
    text = html_module.unescape(soup.get_text())
    return re.sub(r"\s+", " ", text).strip()


def prooftext_refs(html_str: str) -> list[str]:
    """Extract references from a prooftext HTML block."""
    soup = BeautifulSoup(html_str, "html.parser")
    return [h5.get_text(strip=True) for h5 in soup.find_all("h5")]


def main():
    mm = sys.argv[1]
    month_dir = CONTENT_DIR / mm
    for day_dir in sorted(month_dir.iterdir()):
        data_path = day_dir / "data.json"
        if not data_path.exists():
            continue
        dd = day_dir.name
        with open(data_path) as f:
            data = json.load(f)

        print(f"## {mm}-{dd} — {data.get('title', '')}\n")

        for item in data.get("content_with_prooftexts", []):
            citation = item.get("citation", "")
            if item.get("type") == "catechism":
                q = plain_text_with_markers(item.get("question", ""))
                a = plain_text_with_markers(item.get("answer", ""))
                print(f"### {citation}")
                print(f"Q. {q}")
                print(f"A. {a}")
            else:
                title = item.get("title", "")
                body = plain_text_with_markers(item.get("body", ""))
                print(f"### {citation} — {title}")
                print(body)

            prooftexts = item.get("prooftexts", {})
            for num in sorted(prooftexts.keys(), key=int):
                refs = prooftext_refs(prooftexts[num])
                ref_strs = []
                for r in refs:
                    n = count_verses(r)
                    ref_strs.append(f"{r} ({n if n is not None else '?'})")
                print(f"  [{num}] {'; '.join(ref_strs)}")
            print()


if __name__ == "__main__":
    main()
