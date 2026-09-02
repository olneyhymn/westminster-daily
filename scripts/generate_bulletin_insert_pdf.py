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

PARCHMENT = "#e8e0d2"
CREAM = "#fffdf7"
DARK_BROWN = "#2c1810"
BROWN_TEXT = "#6b5d45"
BURGUNDY = "#5c1a2a"
GOLD = "#c4a265"
BORDER = "#d6cbaf"

SITE_URL = "https://reformedconfessions.com/westminster-daily/"
START_URL = "https://reformedconfessions.com/westminster-daily/start"
FEEDBACK_URL = "https://reformedconfessions.com/westminster-daily/feedback"


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


def draw_label(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    font_name: str,
    font_size: float,
    color: str = BROWN_TEXT,
) -> None:
    c.setFont(font_name, font_size)
    c.setFillColor(color)
    c.drawString(x, y, text)


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


def draw_bullet(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    max_width: float,
    fonts: dict[str, str],
    font_size: float = 9.4,
    leading: float = 12.0,
) -> float:
    c.setFillColor(GOLD)
    c.circle(x + 3, y + 3.5, 2.3, stroke=0, fill=1)
    return draw_wrapped(
        c,
        text,
        x + 14,
        y,
        max_width - 14,
        fonts["body"],
        font_size,
        leading,
    )


def draw_insert(c: canvas.Canvas, y0: float, fonts: dict[str, str]) -> None:
    x0 = 0.36 * inch
    y_margin = 0.24 * inch
    w = PAGE_W - 2 * x0
    h = HALF_H - 2 * y_margin

    panel_y = y0 + y_margin
    c.setFillColor(CREAM)
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.75)
    c.rect(x0, panel_y, w, h, stroke=1, fill=1)

    inset = 0.12 * inch
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.45)
    c.rect(x0 + inset, panel_y + inset, w - 2 * inset, h - 2 * inset, stroke=1, fill=0)

    left = x0 + 0.33 * inch
    top = panel_y + h - 0.38 * inch
    qr_size = 1.12 * inch
    qr_x = x0 + w - 0.33 * inch - qr_size
    qr_y = panel_y + h - 1.86 * inch
    text_width = qr_x - left - 0.28 * inch

    draw_label(c, "Westminster Daily", left, top, fonts["bold"], 11.0)
    c.setFillColor(BURGUNDY)
    c.setFont(fonts["bold"], 23)
    c.drawString(left, top - 0.35 * inch, "Read the Westminster")
    c.drawString(left, top - 0.69 * inch, "Standards in a year")

    c.setStrokeColor(GOLD)
    c.setLineWidth(1.1)
    c.line(left, top - 0.86 * inch, left + 2.25 * inch, top - 0.86 * inch)

    y = top - 1.12 * inch
    y = draw_wrapped(
        c,
        "One short daily reading from the Westminster Confession of Faith, "
        "Larger Catechism, and Shorter Catechism, with proof texts printed in full.",
        left,
        y,
        text_width,
        fonts["body"],
        10.1,
        12.8,
    )
    y -= 6
    y = draw_wrapped(
        c,
        "Based on Dr. Joseph A. Pipa Jr.'s Calendar of Readings. Start any day, "
        "or read together as a congregation so everyone is on the same page.",
        left,
        y,
        text_width,
        fonts["italic"],
        9.25,
        11.7,
        BROWN_TEXT,
    )

    section_top = panel_y + 1.78 * inch
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.45)
    c.line(left, section_top + 0.18 * inch, x0 + w - 0.33 * inch, section_top + 0.18 * inch)

    left_col_width = 3.25 * inch
    right_col_x = left + 3.78 * inch
    right_col_width = x0 + w - 0.33 * inch - right_col_x

    c.setFillColor(BURGUNDY)
    c.setFont(fonts["bold"], 10.2)
    c.drawString(left, section_top, "How to start")
    y = section_top - 0.23 * inch
    start_steps = [
        f"Scan the code or visit {SITE_URL.removeprefix('https://').rstrip('/')}.",
        "Read today's selection with the Scripture proof texts.",
        "Subscribe by email or podcast for the daily reminder.",
    ]
    for item in start_steps:
        y = draw_bullet(c, item, left, y, left_col_width, fonts, 8.85, 11.0) - 1.5

    c.setFillColor(BURGUNDY)
    c.setFont(fonts["bold"], 10.2)
    c.drawString(right_col_x, section_top, "Use it for")
    y = section_top - 0.23 * inch
    use_cases = [
        "Private reading",
        "Family worship",
        "A congregation reading together",
    ]
    for item in use_cases:
        y = draw_bullet(c, item, right_col_x, y, right_col_width, fonts, 8.85, 11.0) - 1.5

    c.setFillColor(PARCHMENT)
    c.setStrokeColor(BORDER)
    c.roundRect(qr_x - 7, qr_y - 7, qr_size + 14, qr_size + 39, 5, stroke=1, fill=1)
    draw_qr(c, START_URL, qr_x, qr_y + 26, qr_size)
    c.setFillColor(BURGUNDY)
    c.setFont(fonts["bold"], 10.5)
    c.drawCentredString(qr_x + qr_size / 2, qr_y + 10, "Start today")
    c.setFillColor(BROWN_TEXT)
    c.setFont(fonts["body"], 7.4)
    c.drawCentredString(qr_x + qr_size / 2, qr_y - 3, "scan or visit the site")

    footer_y = panel_y + 0.33 * inch
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.45)
    c.line(left, footer_y + 0.19 * inch, x0 + w - 0.33 * inch, footer_y + 0.19 * inch)
    c.setFillColor(BROWN_TEXT)
    c.setFont(fonts["body"], 8.2)
    c.drawString(left, footer_y, "Free - no advertising")
    c.drawRightString(
        x0 + w - 0.33 * inch,
        footer_y,
        f"Questions: {FEEDBACK_URL.removeprefix('https://')}",
    )


def draw_cut_line(c: canvas.Canvas) -> None:
    c.setStrokeColor(GOLD)
    c.setDash(4, 4)
    c.setLineWidth(0.6)
    c.line(0.35 * inch, HALF_H, PAGE_W - 0.35 * inch, HALF_H)
    c.setDash()


def build_pdf(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fonts = register_fonts()
    c = canvas.Canvas(str(output), pagesize=letter, invariant=1)
    c.setTitle("Westminster Daily Bulletin Insert")
    c.setAuthor("Tim Hopper")
    c.setSubject("Half-page bulletin insert for Westminster Daily")
    c.setFillColor(PARCHMENT)
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
