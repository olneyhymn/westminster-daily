#!/usr/bin/env python3
"""
Sitemap generator for reformedconfessions.com

Scans content/ for daily Westminster Daily readings (content/MM/DD.md) and
content-heidelberg/ for weekly Heidelberg Catechism readings
(content-heidelberg/week-NN/index.md), and writes a sitemap.xml listing the
canonical URL for every page on the site.

Usage:
    python3 scripts/generate_sitemap.py build/sitemap.xml

No third-party dependencies -- stdlib only.
"""

import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

BASE_URL = "https://reformedconfessions.com"

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = REPO_ROOT / "content"
HEIDELBERG_CONTENT_DIR = REPO_ROOT / "content-heidelberg"

DAILY_FILE_RE = re.compile(r"^(?P<mm>\d{2})/(?P<dd>\d{2})\.md$")
WEEK_DIR_RE = re.compile(r"^week-(?P<num>\d{2})$")


def find_daily_urls(content_dir: Path) -> list[str]:
    """Find every content/MM/DD.md file and return its canonical URL.

    Explicitly excludes content/index.md, content/about.md, and
    content/reading-plan.md -- those are not part of the MM/DD glob and are
    handled (or intentionally skipped) elsewhere.
    """
    urls = []
    for path in sorted(content_dir.glob("*/*.md")):
        relative = path.relative_to(content_dir).as_posix()
        match = DAILY_FILE_RE.match(relative)
        if not match:
            continue
        mm, dd = match.group("mm"), match.group("dd")
        urls.append(f"{BASE_URL}/westminster-daily/{mm}/{dd}")
    return urls


def find_heidelberg_urls(heidelberg_content_dir: Path) -> list[str]:
    """Find every content-heidelberg/week-NN/index.md file and return its
    canonical (trailing-slash) URL."""
    urls = []
    if not heidelberg_content_dir.exists():
        return urls
    for path in sorted(heidelberg_content_dir.glob("week-*/index.md")):
        week_dir = path.parent.name
        match = WEEK_DIR_RE.match(week_dir)
        if not match:
            continue
        urls.append(f"{BASE_URL}/heidelberg-weekly/{week_dir}/")
    return urls


def static_urls() -> list[str]:
    return [
        f"{BASE_URL}/westminster-daily/about",
        f"{BASE_URL}/westminster-daily/reading-plan",
    ]


def build_sitemap(urls: list[str]) -> str:
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for url in urls:
        lines.append("  <url>")
        lines.append(f"    <loc>{escape(url)}</loc>")
        lines.append("  </url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <output-path>", file=sys.stderr)
        sys.exit(1)

    output_path = Path(sys.argv[1])

    daily_urls = find_daily_urls(CONTENT_DIR)
    heidelberg_urls = find_heidelberg_urls(HEIDELBERG_CONTENT_DIR)
    urls = daily_urls + heidelberg_urls + static_urls()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_sitemap(urls), encoding="utf-8")

    print(
        f"Wrote {len(urls)} URLs to {output_path} "
        f"({len(daily_urls)} daily, {len(heidelberg_urls)} heidelberg, "
        f"{len(static_urls())} static)"
    )


if __name__ == "__main__":
    main()
