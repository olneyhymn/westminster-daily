#!/usr/bin/env python3
"""Add paragraph numbers to Westminster Confession of Faith readings.

Updates .md files and data.json body fields to include paragraph number spans,
matching the pattern already present in the feed HTML.
"""

import json
import os
import re
import sys

CONTENT_DIR = os.path.join(os.path.dirname(__file__), "content")
SPAN_TEMPLATE = '<span class="paragraph-number">{n}.</span> '


def extract_paragraph_from_citation(citation):
    """Extract paragraph number from citation like 'WCF 1.3' -> '3'."""
    match = re.match(r"WCF \d+\.(\d+)", citation)
    return match.group(1) if match else None


def process_data_json(data_path):
    """Add paragraph numbers to confession entries in data.json."""
    with open(data_path, "r") as f:
        data = json.load(f)

    modified = False

    for entry in data.get("content", []):
        if entry.get("type") != "confession":
            continue
        paragraph = entry.get("paragraph", "")
        if not paragraph:
            continue
        expected = extract_paragraph_from_citation(entry.get("citation", ""))
        if expected and expected != paragraph:
            print(f"WARNING: paragraph mismatch in {data_path}: "
                  f"paragraph={paragraph}, citation says {expected}")
        span = SPAN_TEMPLATE.format(n=paragraph)
        if not entry["body"].startswith(span):
            entry["body"] = span + entry["body"]
            modified = True

    for entry in data.get("content_with_prooftexts", []):
        if entry.get("type") != "confession":
            continue
        paragraph = entry.get("paragraph", "")
        if not paragraph:
            continue
        span = SPAN_TEMPLATE.format(n=paragraph)
        if not entry["body"].startswith(span):
            entry["body"] = span + entry["body"]
            modified = True

    if modified:
        with open(data_path, "w") as f:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    return modified


def process_md_file(md_path, confessions):
    """Add paragraph numbers after ##### Chapter headings in .md files.

    confessions: list of (paragraph, body_start) tuples from data.json
    """
    with open(md_path, "r") as f:
        lines = f.readlines()

    modified = False

    for paragraph, body_start in confessions:
        span = SPAN_TEMPLATE.format(n=paragraph)

        # Find ##### Chapter heading, then the next non-blank line is the body
        for i, line in enumerate(lines):
            if not line.startswith("##### Chapter"):
                continue
            # Find next non-blank line after the heading
            for j in range(i + 1, len(lines)):
                stripped = lines[j].strip()
                if not stripped:
                    continue
                # This is the body line — check it hasn't already been modified
                if stripped.startswith('<span class="paragraph-number">'):
                    break
                # Handle case where line has wrong Q-style span (e.g. confession
                # formatted as catechism question)
                q_pattern = f'<span class="q">Q {paragraph}.</span> '
                if stripped.startswith(q_pattern):
                    lines[j] = lines[j].replace(q_pattern, span, 1)
                    modified = True
                    break
                # Verify this line matches the body start (first word)
                first_word = body_start.split()[0]
                if stripped.startswith(first_word):
                    lines[j] = span + lines[j]
                    modified = True
                break

    if modified:
        with open(md_path, "w") as f:
            f.writelines(lines)
    return modified


def main():
    modified_json = 0
    modified_md = 0
    total_confessions = 0

    for month in sorted(os.listdir(CONTENT_DIR)):
        month_dir = os.path.join(CONTENT_DIR, month)
        if not os.path.isdir(month_dir) or not re.match(r"\d{2}", month):
            continue

        for day in sorted(os.listdir(month_dir)):
            day_dir = os.path.join(month_dir, day)
            data_path = os.path.join(day_dir, "data.json")
            if not os.path.isdir(day_dir) or not os.path.exists(data_path):
                continue

            md_path = os.path.join(CONTENT_DIR, month, f"{day}.md")

            # Read data.json to find confession entries
            with open(data_path, "r") as f:
                data = json.load(f)

            confessions = []
            for entry in data.get("content", []):
                if entry.get("type") == "confession" and entry.get("paragraph"):
                    confessions.append((entry["paragraph"], entry["body"]))
                    total_confessions += 1

            if not confessions:
                continue

            # Process .md BEFORE data.json so we use original body text for matching
            if os.path.exists(md_path) and process_md_file(md_path, confessions):
                modified_md += 1

            if process_data_json(data_path):
                modified_json += 1

    print(f"Total confession entries: {total_confessions}")
    print(f"Modified data.json files: {modified_json}")
    print(f"Modified .md files: {modified_md}")


if __name__ == "__main__":
    main()
