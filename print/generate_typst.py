#!/usr/bin/env python3
"""Generate a Typst source file for the Westminster Daily print book.

Reads all content/MM/DD/data.json files and produces print/westminster-daily.typ.
"""

import json
import os
import re
import html as html_module
from datetime import date, timedelta
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString

CONTENT_DIR = Path(__file__).resolve().parent.parent / "content"
OUTPUT_FILE = Path(__file__).resolve().parent / "westminster-daily.typ"

MONTHS = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def escape_typst(text: str) -> str:
    """Escape characters that are special in Typst markup."""
    text = text.replace("\\", "\\\\")
    text = text.replace("#", "\\#")
    text = text.replace("@", "\\@")
    text = text.replace("$", "\\$")
    text = text.replace("<", "\\<")
    text = text.replace(">", "\\>")
    text = text.replace("*", "\\*")
    text = text.replace("_", "\\_")
    text = text.replace("[", "\\[")
    text = text.replace("]", "\\]")
    # Typst uses smart quotes by default, pass through literal quotes
    return text


def count_verses(reference: str) -> int | None:
    """Count the number of verses in a Scripture reference.

    Returns None for multi-chapter references (always citation-only).
    """
    # Multi-chapter references like "Hebrews 8-10" or "Hebrews 8:1-10:39"
    if re.search(r'\d+[:-]\d+[:-]\d+', reference):
        # Could be "Book X:Y-Z" with large numbers, check further
        pass

    # Match "Book Chapter:VerseStart-VerseEnd"
    m = re.search(r':(\d+)\s*[-–]\s*(\d+)\s*$', reference)
    if m:
        start, end = int(m.group(1)), int(m.group(2))
        if end >= start:
            return end - start + 1
        return None

    # Match "Book Chapter:Verse" (single verse)
    m = re.search(r':(\d+)\s*$', reference)
    if m:
        return 1

    # Multi-chapter like "Hebrews 8-10" (no colon, just chapter range)
    m = re.search(r'(\d+)\s*[-–]\s*(\d+)\s*$', reference)
    if m and ':' not in reference:
        return None  # Multi-chapter, always citation-only

    return None


def parse_prooftext_html(html_str: str) -> list[dict]:
    """Parse an ESV prooftext HTML string into a list of {reference, text, is_poetry} dicts."""
    soup = BeautifulSoup(html_str, "html.parser")
    results = []

    h5_tags = soup.find_all("h5")
    for h5 in h5_tags:
        reference = h5.get_text(strip=True)
        # Find the next esv-text div
        esv_div = h5.find_next("div", class_="esv-text")
        if not esv_div:
            results.append({"reference": reference, "text": "", "is_poetry": False})
            continue

        is_poetry = bool(esv_div.find("p", class_="line-group"))
        text = extract_esv_text(esv_div, is_poetry)
        results.append({"reference": reference, "text": text, "is_poetry": is_poetry})

    return results


def extract_esv_text(div, is_poetry: bool) -> str:
    """Extract formatted text from an esv-text div, converting to Typst markup."""
    # Remove copyright links and surrounding "(ESV)" text
    for a in div.find_all("a", class_="copyright"):
        # Walk up to find and clean the "(ESV)" text
        prev_sib = a.previous_sibling
        next_sib = a.next_sibling
        if isinstance(prev_sib, NavigableString):
            prev_sib.replace_with(str(prev_sib).rstrip().rstrip("("))
        if isinstance(next_sib, NavigableString):
            next_sib.replace_with(str(next_sib).lstrip().lstrip(")"))
        a.decompose()

    # Remove chapter numbers like "8:1 " or "53:1 "
    for span in div.find_all("span", class_="chapter-num"):
        span.decompose()

    if is_poetry:
        text = extract_poetry(div)
    else:
        text = extract_prose(div)

    # Final cleanup of any leftover "(ESV)" or "( )" artifacts
    text = re.sub(r'\s*\(\s*\)\s*$', '', text)
    text = re.sub(r'\s*\(\s*ESV\s*\)\s*$', '', text)
    text = re.sub(r'\s*\(\s*\)\s*', ' ', text)
    return text.rstrip()


def extract_prose(div) -> str:
    """Extract prose text from a div."""
    parts = []
    for p in div.find_all("p"):
        text = process_inline(p)
        text = text.strip()
        if text:
            parts.append(text)
    if not parts:
        text = process_inline(div)
        text = text.strip()
        if text:
            parts.append(text)
    return " ".join(parts)


def extract_poetry(div) -> str:
    """Extract poetry text, preserving line structure."""
    lines = []
    for p in div.find_all("p", class_="line-group"):
        stanza_lines = process_poetry_p(p)
        if stanza_lines:
            lines.extend(stanza_lines)
    # Also get any non-poetry paragraphs mixed in
    for p in div.find_all("p"):
        if "line-group" not in (p.get("class") or []):
            text = process_inline(p).strip()
            if text:
                lines.append(text)
    return "\n".join(lines)


def process_poetry_p(p) -> list[str]:
    """Process a poetry paragraph, returning lines."""
    lines = []
    current_line = ""

    for child in p.children:
        if isinstance(child, NavigableString):
            current_line += process_text_node(str(child))
        elif child.name == "br":
            if current_line.strip():
                lines.append(current_line.strip())
            current_line = ""
        elif child.name == "span":
            classes = child.get("class", [])
            if "indent" in classes:
                current_line += "#h(1.5em)"
            elif "small-caps" in classes:
                text = escape_typst(child.get_text())
                current_line += f"#smallcaps[{text}]"
            elif "woc" in classes:
                # Words of Christ - just include the text
                current_line += process_inline(child)
            else:
                current_line += process_inline(child)
        elif child.name == "p":
            # Nested paragraph (shouldn't happen often)
            if current_line.strip():
                lines.append(current_line.strip())
                current_line = ""
            nested = process_poetry_p(child)
            lines.extend(nested)
        else:
            current_line += process_inline(child)

    if current_line.strip():
        lines.append(current_line.strip())

    return lines


def process_table(table) -> str:
    """Convert an HTML table to a Typst grid (used for WCF 1.2 book lists)."""
    rows = table.find_all("tr")
    if not rows:
        return ""

    # Count columns from first row
    first_cells = rows[0].find_all("td")
    ncols = len(first_cells) if first_cells else 3

    cells = []
    for row in rows:
        tds = row.find_all("td")
        for td in tds:
            text = html_module.unescape(td.get_text()).strip()
            text = escape_typst(text)
            cells.append(f"[{text}]")

    col_spec = ", ".join(["1fr"] * ncols)
    grid_cells = ",\n  ".join(cells)
    return f"\n#grid(columns: ({col_spec}), gutter: 2pt,\n  {grid_cells}\n)\n"


def process_inline(element) -> str:
    """Process inline HTML, converting to Typst markup."""
    parts = []
    for child in element.children:
        if isinstance(child, NavigableString):
            parts.append(process_text_node(str(child)))
        elif child.name == "span":
            classes = child.get("class", [])
            if "small-caps" in classes:
                text = escape_typst(child.get_text())
                parts.append(f"#smallcaps[{text}]")
            elif "indent" in classes:
                parts.append("#h(1.5em)")
            elif "woc" in classes:
                parts.append(process_inline(child))
            elif "chapter-num" in classes:
                pass  # Skip chapter numbers
            else:
                parts.append(process_inline(child))
        elif child.name == "sup":
            text = escape_typst(child.get_text())
            parts.append(f"#super[{text}]")
        elif child.name == "br":
            parts.append("\n")
        elif child.name == "a":
            if "copyright" in (child.get("class") or []):
                continue
            parts.append(process_inline(child))
        elif child.name in ("b", "strong"):
            text = process_inline(child)
            parts.append(f"*{text}*")
        elif child.name in ("i", "em"):
            text = process_inline(child)
            parts.append(f"_{text}_")
        elif child.name == "table":
            parts.append(process_table(child))
        elif child.name in ("center", "tbody", "thead"):
            # Pass through container elements
            parts.append(process_inline(child))
        elif child.name == "div":
            # Recurse into divs
            parts.append(process_inline(child))
        elif child.name == "p":
            text = process_inline(child)
            if text.strip():
                parts.append(" " + text.strip())
        else:
            parts.append(process_inline(child))
    return "".join(parts)


def process_text_node(text: str) -> str:
    """Process a text node, unescaping HTML entities and escaping for Typst."""
    text = html_module.unescape(text)
    return escape_typst(text)


def parse_answer_body(html_str: str) -> str:
    """Parse an answer or body HTML string, converting <sup> tags to Typst."""
    soup = BeautifulSoup(html_str, "html.parser")

    # Remove any <a> tags inside <sup> tags (footnote links)
    for sup in soup.find_all("sup"):
        for a in sup.find_all("a"):
            a.replace_with(a.get_text())

    result = process_inline(soup)
    # Clean up extra whitespace
    result = re.sub(r'\s+', ' ', result).strip()
    return result


def load_all_days() -> list[dict]:
    """Load all data.json files in calendar order."""
    days = []
    # Use 2024 as base year (leap year, so Feb 29 exists)
    start = date(2024, 1, 1)
    end = date(2024, 12, 31)

    d = start
    while d <= end:
        mm = f"{d.month:02d}"
        dd = f"{d.day:02d}"
        data_path = CONTENT_DIR / mm / dd / "data.json"
        if data_path.exists():
            with open(data_path) as f:
                data = json.load(f)
            days.append({
                "month": d.month,
                "day": d.day,
                "month_name": MONTHS[d.month],
                "data": data,
            })
        d += timedelta(days=1)

    return days


def format_prooftexts(prooftexts: dict) -> str:
    """Format prooftexts dict into Typst markup.

    For each numbered group, parse the HTML and apply the verse-count rule:
    - ≤2 verses: include full text
    - >2 verses: citation only
    """
    if not prooftexts:
        return ""

    lines = []
    # Sort by numeric key
    sorted_keys = sorted(prooftexts.keys(), key=lambda k: int(k))

    for key in sorted_keys:
        html_str = prooftexts[key]
        passages = parse_prooftext_html(html_str)

        if not passages:
            continue

        full_texts = []
        citation_only = []

        for passage in passages:
            ref = passage["reference"]
            verse_count = count_verses(ref)

            if verse_count is not None and verse_count <= 2:
                full_texts.append(passage)
            else:
                citation_only.append(passage)

        group_parts = []

        # Full text passages
        for passage in full_texts:
            ref = escape_typst(passage["reference"])
            text = passage["text"]  # Already Typst-escaped during extraction
            if passage["is_poetry"]:
                # Format poetry with line breaks
                poetry_lines = text.split("\n")
                formatted_lines = []
                for line in poetry_lines:
                    formatted_lines.append(line)
                poetry_text = " \\\n".join(formatted_lines)
                group_parts.append(f'#prooftext-full[{ref}][{poetry_text}]')
            else:
                group_parts.append(f'#prooftext-full[{ref}][{text}]')

        # Citation-only passages
        if citation_only:
            refs = ", ".join(escape_typst(p["reference"]) for p in citation_only)
            group_parts.append(f'#prooftext-citation[{refs}]')

        if group_parts:
            content = "\n".join(group_parts)
            lines.append(f'#prooftext-group[{key}][\n{content}\n]')

    return "\n".join(lines)


def generate_front_matter() -> str:
    """Generate the front matter pages."""
    return r'''// Suppress page numbers on front matter
#set page(numbering: none, header: none)

// Half title
#align(center + horizon)[
  #text(font: sans-font, size: 20pt, weight: "bold")[The Westminster Daily]
]
#pagebreak()

// Blank verso
#pagebreak()

// Title page
#align(center + horizon)[
  #text(font: sans-font, size: 28pt, weight: "bold")[The Westminster Daily]
  #v(12pt)
  #text(font: sans-font, size: 14pt)[A Daily Reading Plan through]
  #v(4pt)
  #text(font: sans-font, size: 14pt)[the Westminster Standards]
  #v(24pt)
  #text(font: sans-font, size: 11pt, fill: luma(100))[with prooftexts from the ESV]
]
#pagebreak()

// Copyright page
#set par(justify: false)
#v(1fr)
#text(size: 8pt)[
  Scripture quotations are from the ESV\u{00AE} Bible (The Holy Bible, English Standard Version\u{00AE}), copyright \u{00A9} 2001 by Crossway, a publishing ministry of Good News Publishers. Used by permission. All rights reserved.

  #v(6pt)

  The Westminster Confession of Faith, the Westminster Shorter Catechism, and the Westminster Larger Catechism are public domain.
]
#set par(justify: true)
#pagebreak()

// Introduction
#align(center)[#text(font: sans-font, size: 16pt, weight: "bold")[Introduction]]
#v(12pt)

The Westminster Standards --- the Confession of Faith, the Shorter Catechism, and the Larger Catechism --- are among the most carefully crafted summaries of biblical teaching ever produced. Completed in the 1640s by the Westminster Assembly, they have served generations of Christians as guides for understanding what Scripture teaches.

#v(6pt)

This book divides the Standards into 366 daily readings, one for each day of the year including leap day. Each day's reading includes the relevant portion of the Standards along with the Scripture prooftexts cited by the Assembly. Short prooftexts (two verses or fewer) are printed in full; longer passages are given as citations for the reader to look up.

#v(6pt)

The readings cycle through the Shorter Catechism, the Larger Catechism, and the Confession of Faith across the year. May this daily engagement with these faithful summaries of God's Word be a means of grace in your life.

#pagebreak()

// Restore page numbers and headers, reset counter to 1
#set page(numbering: "1")
#counter(page).update(1)
'''


def generate_typst(days: list[dict]) -> str:
    """Generate the complete Typst source."""
    parts = []

    # Preamble
    parts.append('#import "template.typ": *\n')
    parts.append("#show: book-setup\n")

    # Front matter
    parts.append(generate_front_matter())

    current_month = 0

    for day_info in days:
        month = day_info["month"]
        day = day_info["day"]
        month_name = day_info["month_name"]
        data = day_info["data"]

        # Month header on first day of month
        is_first_of_month = month != current_month
        if is_first_of_month:
            current_month = month
            parts.append(f'\n#month-header[{month_name}]\n')

        # Date header — use first-date-header after month header (no extra rule)
        if is_first_of_month:
            parts.append(f'#first-date-header[{month_name}][{day}]\n')
        else:
            parts.append(f'#date-header[{month_name}][{day}]\n')

        # Content items
        content_items = data.get("content_with_prooftexts", [])
        for i, item in enumerate(content_items):
            item_type = item.get("type", "")
            long_citation = item.get("long_citation", "")

            # Add separator between multiple entries within the same day
            if i > 0:
                parts.append('\n#entry-separator()\n')

            parts.append(f'\n#document-label[{escape_typst(long_citation)}]\n')

            if item_type == "catechism":
                question = parse_answer_body(item.get("question", ""))
                answer = parse_answer_body(item.get("answer", ""))
                parts.append(f'#catechism-question[{question}]\n')
                parts.append(f'#catechism-answer[{answer}]\n')
            elif item_type == "confession":
                title = item.get("title", "")
                if title:
                    parts.append(f'#confession-title[{escape_typst(title)}]\n')
                body = parse_answer_body(item.get("body", ""))
                parts.append(f'#confession-body[{body}]\n')

            # Prooftexts
            prooftexts = item.get("prooftexts", {})
            if prooftexts:
                pt_markup = format_prooftexts(prooftexts)
                if pt_markup:
                    parts.append(f'\n#prooftext-section[\n{pt_markup}\n]\n')

    return "".join(parts)


def main():
    print("Loading daily readings...")
    days = load_all_days()
    print(f"  Loaded {len(days)} days")

    print("Generating Typst source...")
    typst_source = generate_typst(days)

    print(f"Writing {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w") as f:
        f.write(typst_source)

    print(f"  Written {len(typst_source):,} characters")
    print("Done! Run: typst compile print/westminster-daily.typ")


if __name__ == "__main__":
    main()
