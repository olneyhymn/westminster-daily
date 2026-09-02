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
GOLD = "#b5924e"
BORDER = "#c4a265"
LIGHT_RULE = "#d6cbaf"

SITE_URL = "https://reformedconfessions.com/westminster-daily/"
START_URL = "https://reformedconfessions.com/westminster-daily/start"
FEEDBACK_URL = "https://reformedconfessions.com/westminster-daily/feedback"
SITE_LABEL = "reformedconfessions.com/westminster-daily"
FEEDBACK_LABEL = "reformedconfessions.com/feedback"


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


def draw_rule(
    c: canvas.Canvas,
    x1: float,
    y: float,
    x2: float,
    color: str = GOLD,
    width: float = 0.8,
) -> None:
    c.setStrokeColor(color)
    c.setLineWidth(width)
    c.line(x1, y, x2, y)


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


def draw_step(
    c: canvas.Canvas,
    number: int,
    label: str,
    text: str,
    x: float,
    y: float,
    width: float,
    fonts: dict[str, str],
) -> None:
    c.setStrokeColor(GOLD)
    c.setFillColor(CREAM)
    c.setLineWidth(0.8)
    c.circle(x + 7, y + 5, 8, stroke=1, fill=1)

    c.setFillColor(BURGUNDY)
    c.setFont(fonts["bold"], 8.5)
    c.drawCentredString(x + 7, y + 2.1, str(number))

    c.setFont(fonts["bold"], 10.0)
    c.drawString(x + 20, y + 2, label)
    draw_wrapped(
        c,
        text,
        x + 20,
        y - 10,
        width - 20,
        fonts["body"],
        7.8,
        9.2,
        BROWN_TEXT,
    )


def draw_cta_panel(
    c: canvas.Canvas,
    x: float,
    y_top: float,
    width: float,
    height: float,
    fonts: dict[str, str],
) -> None:
    c.setFillColor(PARCHMENT)
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.9)
    c.roundRect(x, y_top - height, width, height, 5, stroke=1, fill=1)

    qr_size = 0.9 * inch
    qr_x = x + (width - qr_size) / 2
    qr_y = y_top - 0.16 * inch - qr_size
    draw_qr(c, START_URL, qr_x, qr_y, qr_size)

    c.setFillColor(BURGUNDY)
    c.setFont(fonts["bold"], 12.0)
    c.drawCentredString(x + width / 2, qr_y - 17, "Start today")
    c.setFillColor(BROWN_TEXT)
    c.setFont(fonts["body"], 7.4)
    c.drawCentredString(x + width / 2, qr_y - 31, "Scan or visit")
    c.setFont(fonts["bold"], 6.6)
    c.drawCentredString(x + width / 2, qr_y - 43, "reformedconfessions.com")
    c.drawCentredString(x + width / 2, qr_y - 53, "/westminster-daily")


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
    c.setStrokeColor(LIGHT_RULE)
    c.setLineWidth(0.55)
    c.rect(x0 + inset, panel_y + inset, w - 2 * inset, h - 2 * inset, stroke=1, fill=0)

    left = x0 + 0.33 * inch
    right = x0 + w - 0.33 * inch
    top = panel_y + h - 0.32 * inch
    cta_w = 1.66 * inch
    cta_h = 2.05 * inch
    cta_x = right - cta_w
    cta_top = top + 4
    text_width = 3.72 * inch

    draw_label(c, "Westminster Daily", left, top, fonts["bold"], 12.0)
    c.setFillColor(BURGUNDY)
    c.setFont(fonts["bold"], 22.2)
    c.drawString(left, top - 0.35 * inch, "Read the Westminster")
    c.drawString(left, top - 0.69 * inch, "Standards in a year")

    draw_rule(c, left, top - 0.85 * inch, left + 2.18 * inch, GOLD, 1.1)
    draw_cta_panel(c, cta_x, cta_top, cta_w, cta_h, fonts)

    y = top - 1.08 * inch
    y = draw_wrapped(
        c,
        "One short daily reading from the Westminster Confession of Faith, "
        "Larger Catechism, and Shorter Catechism, with proof texts printed in full.",
        left,
        y,
        text_width,
        fonts["body"],
        9.75,
        13.2,
    )
    y -= 5
    y = draw_wrapped(
        c,
        "Based on Dr. Joseph A. Pipa Jr.'s Calendar of Readings.",
        left,
        y,
        text_width,
        fonts["italic"],
        7.9,
        10.0,
        BROWN_TEXT,
    )
    y -= 1
    draw_wrapped(
        c,
        "Start any day, or read together as a congregation.",
        left,
        y,
        text_width,
        fonts["bold"],
        8.45,
        10.5,
        BURGUNDY,
    )

    section_top = panel_y + 2.33 * inch
    draw_rule(c, left, section_top + 0.17 * inch, right, LIGHT_RULE, 0.65)

    steps_width = 4.4 * inch
    step_width = 1.38 * inch
    right_col_x = left + 4.65 * inch
    right_col_width = right - right_col_x

    c.setFillColor(BURGUNDY)
    c.setFont(fonts["bold"], 10.2)
    c.drawString(left, section_top, "How to start")
    step_y = section_top - 0.31 * inch
    draw_step(c, 1, "Scan", "Open today's reading.", left, step_y, step_width, fonts)
    draw_step(
        c,
        2,
        "Read",
        "Use the proof texts printed in full.",
        left + steps_width / 3,
        step_y,
        step_width,
        fonts,
    )
    draw_step(
        c,
        3,
        "Subscribe",
        "Get email or podcast reminders.",
        left + steps_width * 2 / 3,
        step_y,
        step_width,
        fonts,
    )

    c.setFillColor(BURGUNDY)
    c.setFont(fonts["bold"], 9.4)
    c.drawString(right_col_x, section_top, "Use it for")
    y = section_top - 0.23 * inch
    use_cases = [
        "Private reading",
        "Family worship",
        "Reading together as a church",
    ]
    for item in use_cases:
        y = draw_bullet(c, item, right_col_x, y, right_col_width, fonts, 7.85, 9.8) - 1.2

    footer_y = panel_y + 0.33 * inch
    draw_rule(c, left, footer_y + 0.19 * inch, right, LIGHT_RULE, 0.65)
    c.setFillColor(BROWN_TEXT)
    c.setFont(fonts["body"], 8.2)
    c.drawString(left, footer_y, "Free / No advertising")
    c.drawRightString(
        right,
        footer_y,
        f"Questions: {FEEDBACK_LABEL}",
    )


def draw_cut_line(c: canvas.Canvas) -> None:
    c.setStrokeColor(GOLD)
    c.setDash(4, 4)
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
