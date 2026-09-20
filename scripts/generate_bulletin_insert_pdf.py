#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "reportlab==4.4.9",
# ]
# ///

"""Generate a half-page Westminster Daily bulletin insert PDF."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


PAGE_W, PAGE_H = letter
HALF_H = PAGE_H / 2

DARK_BROWN = "#2C1810"
BROWN_TEXT = "#6B5D45"
BURGUNDY = "#5C1A2A"
GOLD = "#C4A265"

START_URL = "https://reformedconfessions.com/westminster-daily/start"
SITE_URL = "https://reformedconfessions.com/westminster-daily/"
SITE_LABEL = "reformedconfessions.com/westminster-daily"


def register_fonts() -> dict[str, str]:
    """Use Georgia when available, falling back to PDF built-in Times faces."""

    supplemental = Path("/System/Library/Fonts/Supplemental")
    candidates = {
        "body": ("Georgia", supplemental / "Georgia.ttf", "Times-Roman"),
        "bold": ("Georgia-Bold", supplemental / "Georgia Bold.ttf", "Times-Bold"),
        "italic": ("Georgia-Italic", supplemental / "Georgia Italic.ttf", "Times-Italic"),
        "bold_italic": (
            "Georgia-BoldItalic",
            supplemental / "Georgia Bold Italic.ttf",
            "Times-BoldItalic",
        ),
    }

    fonts: dict[str, str] = {}
    for role, (font_name, path, fallback) in candidates.items():
        if path.exists():
            pdfmetrics.registerFont(TTFont(font_name, str(path)))
            fonts[role] = font_name
        else:
            fonts[role] = fallback
    return fonts


def fit_lines(
    text: str,
    font_name: str,
    font_size: float,
    max_width: float,
) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if pdfmetrics.stringWidth(candidate, font_name, font_size) <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = word
    if current:
        lines.append(current)
    return lines


def draw_wrapped(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    max_width: float,
    font_name: str,
    font_size: float,
    leading: float,
    color: str = DARK_BROWN,
) -> float:
    c.setFont(font_name, font_size)
    c.setFillColor(color)
    for line in fit_lines(text, font_name, font_size, max_width):
        c.drawString(x, y, line)
        y -= leading
    return y


def draw_qr(c: canvas.Canvas, url: str, x: float, y: float, size: float) -> None:
    widget = qr.QrCodeWidget(url)
    bounds = widget.getBounds()
    qr_width = bounds[2] - bounds[0]
    qr_height = bounds[3] - bounds[1]
    drawing = Drawing(
        size,
        size,
        transform=[size / qr_width, 0, 0, size / qr_height, 0, 0],
    )
    drawing.add(widget)
    renderPDF.draw(drawing, c, x, y)


def draw_rule(
    c: canvas.Canvas,
    x1: float,
    y: float,
    x2: float,
    color: str = GOLD,
    width: float = 0.9,
) -> None:
    c.setStrokeColor(color)
    c.setLineWidth(width)
    c.line(x1, y, x2, y)


def draw_insert(c: canvas.Canvas, y0: float, fonts: dict[str, str]) -> None:
    """Typeset a half-letter invitation on unprinted paper, with one action."""
    left = 36
    right = PAGE_W - left
    width = right - left
    c.saveState()
    c.translate(0, y0)

    c.setFillColor(BURGUNDY)
    c.setFont(fonts["body"], 32)
    c.drawString(left, 344, "Westminster Daily")
    c.setFont(fonts["italic"], 19)
    c.drawString(left, 312, "Read the Westminster Standards in a year.")
    draw_rule(c, left, 291, right, width=1)

    draw_wrapped(
        c,
        "The plan pairs short readings from the Westminster Confession of Faith, "
        "Larger Catechism, and Shorter Catechism with Scripture proof texts.",
        left, 265, width, fonts["body"], 13, 20,
    )
    c.setFillColor(BROWN_TEXT)
    c.setFont(fonts["body"], 9.5)
    c.drawString(left, 219, "The schedule follows Dr. Joseph Pipa Jr.’s Calendar of Readings.")

    c.setFillColor(DARK_BROWN)
    c.setFont(fonts["body"], 13)
    c.drawString(left, 187, "Begin any day of the year.")
    c.drawString(left, 167, "Read on your own, with your family, or together as a church.")

    c.setFillColor(BURGUNDY)
    c.setFont(fonts["bold"], 14)
    c.drawString(left, 119, "Find today’s reading")
    draw_wrapped(
        c,
        "Scan the code or visit the site for today’s reading. You can also "
        "subscribe to the daily email or podcast for free.",
        left, 97, 405, fonts["body"], 11.5, 17,
    )
    c.setFillColor(DARK_BROWN)
    c.setFont(fonts["body"], 11)
    c.drawString(left, 53, SITE_LABEL)
    c.linkURL(SITE_URL, (left, 50, left + pdfmetrics.stringWidth(
        SITE_LABEL, fonts["body"], 11), 65), relative=1)
    draw_qr(c, START_URL, right - 96, 45, 96)
    c.linkURL(START_URL, (right - 96, 45, right, 141), relative=1)
    c.restoreState()


def draw_cut_line(c: canvas.Canvas) -> None:
    c.setStrokeColor(BROWN_TEXT)
    c.setDash(3, 5)
    c.setLineWidth(0.75)
    c.line(0.35 * inch, HALF_H, PAGE_W - 0.35 * inch, HALF_H)
    c.setDash()


def build_pdf(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fonts = register_fonts()
    c = canvas.Canvas(str(output), pagesize=letter, invariant=1)
    c.setTitle("Westminster Daily Bulletin Insert")
    c.setAuthor("Tim Hopper")
    c.setSubject("Half-page bulletin insert for Westminster Daily")
    c.setFillColor("#ffffff")
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    draw_insert(c, HALF_H, fonts)
    draw_insert(c, 0, fonts)
    draw_cut_line(c)
    c.showPage()
    c.save()


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/pdf/westminster-daily-bulletin-insert.pdf"),
        help="PDF output path",
    )
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    build_pdf(args.output)
    print(args.output)


if __name__ == "__main__":
    main()
