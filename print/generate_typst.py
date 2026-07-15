#!/usr/bin/env python3
"""Generate a Typst source file for the Westminster Daily print book.

Reads all content/MM/DD/data.json files plus curation data from print/curation/*.json
and produces print/westminster-daily.typ.

Proof-text rules (spec v2):
- Every reference is listed, grouped under its footnote number.
- References selected in the curation files are printed in full (ESV text).
- A global budget of <1,000 printed ESV verses is enforced.
"""

import json
import re
import html as html_module
from datetime import date, timedelta
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString

CONTENT_DIR = Path(__file__).resolve().parent.parent / "content"
CURATION_DIR = Path(__file__).resolve().parent / "curation"
OUTPUT_FILE = Path(__file__).resolve().parent / "westminster-daily.typ"

VERSE_BUDGET = 1000

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


def normalize_plain(html_str: str) -> str:
    """Reduce an HTML/text snippet to normalized plain text for comparison."""
    text = BeautifulSoup(html_str, "html.parser").get_text()
    text = html_module.unescape(text)
    return re.sub(r"\s+", " ", text).strip().lower().rstrip("?.")


def reading_metadata(item: dict) -> str:
    """Emit a Typst metadata marker for the Standards index."""
    doc = item.get("abbv", "").upper()
    if item.get("type") == "catechism":
        num = item.get("number", "")
        if doc in ("WSC", "WLC") and str(num).isdigit():
            return f'#metadata((kind: "rd", doc: "{doc}", num: {int(num)}))\n'
    elif item.get("type") == "confession":
        ch = item.get("chapter", "")
        if str(ch).isdigit():
            title = re.sub(r"^Chapter \d+:\s*", "", item.get("title", ""))
            return f'#metadata((kind: "rd", doc: "WCF", ch: {int(ch)}, title: {json.dumps(title)}))\n'
    return ""


def topic_is_redundant(topic: str, items: list[dict]) -> bool:
    """True when the day's topic adds nothing over the readings' own headers."""
    t = normalize_plain(topic)
    t_base = re.sub(r",? part \d+$", "", t)
    for item in items:
        if item.get("type") == "catechism":
            if normalize_plain(item.get("question", "")) == t:
                return True
        else:
            title = normalize_plain(item.get("title", ""))
            title = re.sub(r"^chapter \d+:\s*", "", title)
            if title == t_base:
                return True
    return False


def normalize_ref(reference: str) -> str:
    """Normalize a Scripture reference for matching (dashes, whitespace)."""
    ref = reference.replace("–", "-").replace("—", "-")
    ref = re.sub(r"\s+", " ", ref).strip()
    return ref


def count_verses(reference: str) -> int | None:
    """Count the number of verses in a Scripture reference.

    Returns None when the count can't be determined (multi-chapter ranges,
    whole-chapter citations).
    """
    ref = normalize_ref(reference)

    # Cross-chapter range like "Hebrews 8:1-10:39"
    if re.search(r"\d+:\d+\s*-\s*\d+:\d+", ref):
        return None

    # "Book Chapter:VerseStart-VerseEnd"
    m = re.search(r":(\d+)\s*-\s*(\d+)\s*$", ref)
    if m:
        start, end = int(m.group(1)), int(m.group(2))
        if end >= start:
            return end - start + 1
        return None

    # "Book Chapter:Verse" (single verse)
    if re.search(r":(\d+)\s*$", ref):
        return 1

    # Single-chapter books cite verses without a chapter ("Jude 24", "Obadiah 10-14")
    if re.match(r'^(Jude|Obadiah|Philemon|2 John|3 John)\b', ref):
        m = re.search(r'(\d+)\s*-\s*(\d+)\s*$', ref)
        if m:
            return int(m.group(2)) - int(m.group(1)) + 1
        if re.search(r'\d+\s*$', ref):
            return 1

    # Whole chapter(s): "Psalm 119" or "Hebrews 8-10"
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
    """Extract poetry text, preserving line structure and document order
    (mixed passages interleave prose paragraphs with line-groups)."""
    lines = []
    for p in div.find_all("p"):
        if "line-group" in (p.get("class") or []):
            lines.extend(process_poetry_p(p))
        else:
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
    """Load all data.json files in calendar order (Feb 29 omitted)."""
    days = []
    # Use 2024 as base year so the calendar iterates cleanly
    start = date(2024, 1, 1)
    end = date(2024, 12, 31)

    d = start
    while d <= end:
        if d.month == 2 and d.day == 29:
            d += timedelta(days=1)
            continue
        mm = f"{d.month:02d}"
        dd = f"{d.day:02d}"
        data_path = CONTENT_DIR / mm / dd / "data.json"
        if data_path.exists():
            with open(data_path) as f:
                data = json.load(f)
            days.append({
                "month": d.month,
                "day": d.day,
                "key": f"{mm}-{dd}",
                "month_name": MONTHS[d.month],
                "data": data,
            })
        d += timedelta(days=1)

    return days


def load_curation() -> dict:
    """Load curation selections from print/curation/*.json.

    Each file maps "MM-DD" -> { citation -> { footnote_num -> [references] } }.
    Returns the merged mapping with normalized references.
    """
    curation: dict = {}
    if not CURATION_DIR.exists():
        return curation
    for path in sorted(CURATION_DIR.glob("*.json")):
        with open(path) as f:
            data = json.load(f)
        for day_key, citations in data.items():
            day_sel = curation.setdefault(day_key, {})
            for citation, groups in citations.items():
                cit_sel = day_sel.setdefault(citation, {})
                for num, refs in groups.items():
                    cit_sel[num] = [normalize_ref(r) for r in refs]
    return curation


class BudgetTracker:
    """Tracks printed verses and curation mismatches across the build."""

    def __init__(self):
        self.printed_verses = 0
        self.printed_passages = 0
        self.uncountable: list[str] = []
        self.unmatched: list[str] = []

    def add(self, reference: str, context: str):
        n = count_verses(reference)
        if n is None:
            self.uncountable.append(f"{context}: {reference}")
            n = 5  # conservative fallback so the budget stays honest
        self.printed_verses += n
        self.printed_passages += 1


def format_prooftexts(prooftexts: dict, selection: dict, context: str,
                      tracker: BudgetTracker) -> str:
    """Format prooftexts into Typst markup.

    Every reference is listed under its footnote number. References named in
    `selection` (footnote_num -> [normalized refs]) are printed in full; all
    others appear as citations only.
    """
    if not prooftexts:
        return ""

    lines = []
    sorted_keys = sorted(prooftexts.keys(), key=lambda k: int(k))

    # Track which selected refs we actually found, to flag curation typos
    wanted = {(num, ref) for num, refs in selection.items() for ref in refs}

    for key in sorted_keys:
        html_str = prooftexts[key]
        passages = parse_prooftext_html(html_str)

        if not passages:
            continue

        selected_refs = selection.get(key, [])

        full_texts = []
        citation_only = []

        for passage in passages:
            ref = normalize_ref(passage["reference"])
            if ref in selected_refs:
                full_texts.append(passage)
                wanted.discard((key, ref))
            else:
                citation_only.append(passage)

        group_parts = []

        for passage in full_texts:
            ref = escape_typst(passage["reference"])
            text = passage["text"]  # Already Typst-escaped during extraction
            tracker.add(passage["reference"], context)
            if passage["is_poetry"]:
                # Drop empty lines (artifacts of literal newlines in the
                # source HTML, e.g. inside words-of-Christ spans)
                poetry_lines = [ln.rstrip() for ln in text.split("\n") if ln.strip()]
                poetry_text = " \\\n".join(poetry_lines)
                group_parts.append(f'#prooftext-full[{ref}][{poetry_text}]')
            else:
                group_parts.append(f'#prooftext-full[{ref}][{text}]')

        if citation_only:
            refs = ", ".join(escape_typst(p["reference"]) for p in citation_only)
            if full_texts:
                group_parts.append(f'#prooftext-citation(see-also: true)[{refs}]')
            else:
                group_parts.append(f'#prooftext-citation[{refs}]')

        if group_parts:
            content = "\n".join(group_parts)
            lines.append(f'#prooftext-group[{key}][\n{content}\n]')

    for num, ref in sorted(wanted):
        tracker.unmatched.append(f"{context} [{num}]: {ref}")

    return "\n".join(lines)


def generate_front_matter() -> str:
    """Generate the front matter pages."""
    return r'''// Suppress page numbers on front matter (running header stays; it
// renders nothing until the first date-header sets the state)
#set page(numbering: none)

// Half title — upper third, letter-spaced
#v(1.6in)
#align(center)[
  #text(font: sans-font, size: 13pt, weight: "semibold", tracking: 2.5pt)[THE WESTMINSTER DAILY]
]
#pagebreak()

// Blank verso
#pagebreak()

// Title page
#v(1.9in)
#align(center)[
  #text(font: sans-font, size: 26pt, weight: "bold")[The Westminster Daily]
  #v(14pt)
  #text(font: sans-font, size: 13pt)[A Daily Reading Plan through]
  #v(4pt)
  #text(font: sans-font, size: 13pt)[the Westminster Standards]
  #v(40pt)
  #text(font: sans-font, size: 10.5pt)[Compiled and edited by Tim Hopper]
  #v(8pt)
  #text(font: sans-font, size: 9.5pt)[Following the reading calendar of Dr.~Joseph A. Pipa Jr.]
]
#v(1fr)
#align(center)[
  #text(font: sans-font, size: 9pt, tracking: 1pt)[westminsterdaily.com]
]
#v(0.35in)
#pagebreak()

// Copyright page
#set par(justify: false)
#v(1fr)
#text(size: 8pt)[
  \u{00A9} 2026 Tim Hopper. All rights reserved.

  #v(6pt)

  Scripture quotations are from the ESV\u{00AE} Bible (The Holy Bible, English Standard Version\u{00AE}), copyright \u{00A9} 2001 by Crossway, a publishing ministry of Good News Publishers. Used by permission. All rights reserved.

  #v(6pt)

  The Westminster Confession of Faith, the Westminster Shorter Catechism, and the Westminster Larger Catechism are in the public domain. Scripture proof-text citations follow the edition of the Standards published by the Orthodox Presbyterian Church.

  #v(6pt)

  westminsterdaily.com
]
#set par(justify: true)
#pagebreak()

// Table of contents
#month-toc()
#pagebreak()

// Date locator (verso facing the introduction)
#day-locator()

// Introduction opens on a recto
#pagebreak(to: "odd")

// Introduction — PLACEHOLDER: Tim writes this (see tasks/todo.md)
#align(center)[#text(font: sans-font, size: 16pt, weight: "bold")[Introduction]]
#v(48pt)
#align(center)[
  #text(size: 10pt, style: "italic", fill: luma(40))[\[ Introduction to be written. \]]
]

// Body opens on a recto with folio 1; restore page numbers
#pagebreak(to: "odd")
#set page(numbering: "1")
#counter(page).update(1)
'''


def generate_typst(days: list[dict], curation: dict, tracker: BudgetTracker) -> str:
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
        day_key = day_info["key"]
        month_name = day_info["month_name"]
        data = day_info["data"]
        day_curation = curation.get(day_key, {})

        # Month header on first day of month
        is_first_of_month = month != current_month
        if is_first_of_month:
            current_month = month
            parts.append(f'\n#month-header[{month_name}]\n')

        first_flag = "true" if is_first_of_month else "false"
        topic = data.get("title", "")
        # Suppress the topic line when it merely repeats one of the day's
        # catechism questions, or when a confession chapter title already
        # conveys it ("Of good works, part 3" vs "Chapter 16: Of Good Works")
        content_items = data.get("content_with_prooftexts", [])
        if topic and not topic_is_redundant(topic, content_items):
            parts.append(
                f'#date-header([{month_name}], [{day}], '
                f'topic: [{escape_typst(topic)}], first: {first_flag})\n'
            )
        else:
            parts.append(f'#date-header([{month_name}], [{day}], first: {first_flag})\n')
        parts.append(f'#metadata((kind: "day", m: {month}, d: {day}))\n')

        # Content items
        for i, item in enumerate(content_items):
            item_type = item.get("type", "")
            long_citation = item.get("long_citation", "")
            citation = item.get("citation", "")

            # Add separator between multiple entries within the same day
            if i > 0:
                parts.append('\n#entry-separator()\n')

            parts.append(f'\n#document-label[{escape_typst(long_citation)}]\n')
            parts.append(reading_metadata(item))

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

            # Prooftexts — all references listed, curated ones in full
            prooftexts = item.get("prooftexts", {})
            if prooftexts:
                selection = day_curation.get(citation, {})
                context = f"{day_key} {citation}"
                pt_markup = format_prooftexts(prooftexts, selection, context, tracker)
                if pt_markup:
                    parts.append(f'\n#prooftext-section[\n{pt_markup}\n]\n')

    # Back matter: index of the Standards (clear the running-date state so
    # index pages carry no date header)
    parts.append('\n#current-date.update("")\n')
    parts.append('#standards-index()\n')

    # End on an even physical page count (KDP/IngramSpark expect it).
    # pagebreak(to: "even") always lands on an even page: +1 blank from an
    # odd page, +2 from an even one.
    parts.append('#pagebreak(to: "even")\n')

    return "".join(parts)


def main():
    print("Loading daily readings...")
    days = load_all_days()
    print(f"  Loaded {len(days)} days")

    print("Loading curation...")
    curation = load_curation()
    print(f"  Curation for {len(curation)} days")

    tracker = BudgetTracker()

    print("Generating Typst source...")
    typst_source = generate_typst(days, curation, tracker)

    print(f"Writing {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w") as f:
        f.write(typst_source)

    print(f"  Written {len(typst_source):,} characters")
    print()
    print("Verse budget report:")
    print(f"  Printed passages: {tracker.printed_passages}")
    print(f"  Printed verses:   {tracker.printed_verses} / {VERSE_BUDGET}")
    if tracker.uncountable:
        print(f"  Uncountable references (assumed 5 verses each):")
        for item in tracker.uncountable:
            print(f"    - {item}")
    if tracker.unmatched:
        print(f"  CURATION MISMATCHES (selected but not found):")
        for item in tracker.unmatched:
            print(f"    - {item}")
    if tracker.printed_verses >= VERSE_BUDGET:
        raise SystemExit(f"ERROR: verse budget exceeded ({tracker.printed_verses} >= {VERSE_BUDGET})")
    print()
    print("Done! Run: typst compile print/westminster-daily.typ")


if __name__ == "__main__":
    main()
