# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "feedgen==1.0.0",
#     "premailer==3.10.0",
#     "markdown==3.5.1",
#     "beautifulsoup4==4.12.2",
#     "lxml",
#     "pytz==2025.2",
#     "httpx",
# ]
# ///
"""
Send the current day's Westminster Daily reading as a Buttondown email.

Reads today's markdown (US/Eastern) from content/MM/DD.md, renders it using the
same logic as generate_feed.py, injects it into templates/newsletter-buttondown.html,
and POSTs to the Buttondown API.

Env:
    BUTTONDOWN_API_KEY  required
    WD_DATE             optional, MM-DD override for testing (e.g. 03-25)
    WD_DRY_RUN          if set, print the email instead of sending

Usage:
    uv run scripts/send_buttondown_email.py
    WD_DRY_RUN=1 WD_DATE=03-25 uv run scripts/send_buttondown_email.py
"""
from __future__ import annotations

import os
import sys
import datetime as dt
from pathlib import Path

import pytz
import httpx

# Reuse the exact rendering used by the RSS feed.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from generate_feed import content as render_content, meta  # noqa: E402

SITE_URL = "https://reformedconfessions.com/westminster-daily"
TEMPLATE_PATH = (
    Path(__file__).resolve().parent.parent / "templates" / "newsletter-buttondown.html"
)
BUTTONDOWN_URL = "https://api.buttondown.com/v1/emails"


def today_month_day() -> tuple[str, str]:
    override = os.environ.get("WD_DATE")
    if override:
        month, day = override.split("-")
        return month, day
    now = dt.datetime.now(tz=pytz.timezone("US/Eastern"))
    return now.strftime("%m"), now.strftime("%d")


def build_email(month: str, day: str) -> tuple[str, str]:
    title = meta(month, day)["pagetitle"][0]
    body_html = render_content(month, day)

    template = TEMPLATE_PATH.read_text()
    email_html = template.replace("__ENTRY_CONTENT__", body_html)
    subject = f"Westminster Daily : {title}"
    return subject, email_html


def send(subject: str, body: str) -> None:
    api_key = os.environ.get("BUTTONDOWN_API_KEY")
    if not api_key:
        sys.exit("BUTTONDOWN_API_KEY is not set")

    resp = httpx.post(
        BUTTONDOWN_URL,
        headers={
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json",
            "X-Buttondown-Live-Dangerously": "true",
        },
        json={
            "subject": subject,
            "body": body,
            "email_type": "public",
            "status": "about_to_send",
        },
        timeout=30.0,
    )
    if resp.status_code >= 300:
        sys.exit(f"Buttondown API error {resp.status_code}: {resp.text}")
    print(f"Sent: {subject}")


def main() -> None:
    month, day = today_month_day()
    subject, body = build_email(month, day)

    if os.environ.get("WD_DRY_RUN"):
        print(f"SUBJECT: {subject}\n")
        print(body)
        return

    send(subject, body)


if __name__ == "__main__":
    main()
