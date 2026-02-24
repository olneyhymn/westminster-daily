# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "feedgen==1.0.0",      # For generating RSS feeds
#     "pytz==2025.2",        # For timezone handling
#     "premailer==3.10.0",   # For HTML email preprocessing
#     "markdown==3.5.1",     # For parsing markdown content
#     "beautifulsoup4==4.12.2",  # For HTML parsing and manipulation
# ]
# ///

"""
Heidelberg Weekly RSS Feed Generator

This script generates an RSS feed for the Heidelberg Weekly content, which provides
weekly readings from the Heidelberg Catechism. The feed includes
the last 8 weeks of content, with each entry containing the formatted content
and metadata for that week's reading.

The script:
1. Reads markdown content files for each week
2. Converts markdown to HTML
3. Processes the HTML for proper display
4. Generates an RSS feed with entries for each week
5. Saves the feed to heidelberg-feed.rss
"""

from feedgen.feed import FeedGenerator
import datetime as dt
import pytz
from premailer import transform
import markdown
from functools import lru_cache
from bs4 import BeautifulSoup, NavigableString

# Base URL for the website and output filename
URL = "https://reformedconfessions.com/heidelberg-weekly"
FILENAME = "heidelberg-feed.rss"
NUMBER_OF_WEEKS = 8  # Number of weeks of content to include in the feed


def get_week_number_for_date(date):
    """
    Calculate the week number (1-52) for a given date based on Sundays.
    Week 1 starts on the first Sunday of January.

    Args:
        date (datetime): The date to calculate week number for

    Returns:
        int: Week number (1-52)
    """
    # Find first Sunday of January for the year
    jan_1 = dt.datetime(date.year, 1, 1, tzinfo=date.tzinfo)
    days_until_sunday = (6 - jan_1.weekday()) % 7

    if days_until_sunday == 0 and jan_1.weekday() == 6:
        first_sunday = jan_1
    else:
        first_sunday = jan_1 + dt.timedelta(days=days_until_sunday)
        if first_sunday.day > 7:
            first_sunday = jan_1 + dt.timedelta(days=(6 - jan_1.weekday()))

    # Calculate weeks since first Sunday
    days_diff = (date - first_sunday).days
    week_number = (days_diff // 7) % 52

    return week_number + 1  # Return 1-52


@lru_cache()
def markdown_parser(week_num):
    """
    Parse the markdown content for a specific week.

    Args:
        week_num (int): Week number (1-52)

    Returns:
        tuple: (markdown parser instance, converted HTML content)
    """
    week_fmt = f"{week_num:02d}"
    with open(f"content-heidelberg/week-{week_fmt}/index.md", "r") as f:
        md = f.read()
    markdown_parser = markdown.Markdown(
        extensions=["meta", "footnotes"],
        extension_configs={"footnotes": {"BACKLINK_TEXT": ""}},
    )
    return markdown_parser, markdown_parser.convert(md)


def meta(week_num):
    """
    Extract metadata from the markdown content for a specific week.

    Args:
        week_num (int): Week number (1-52)

    Returns:
        dict: Metadata from the markdown file
    """
    return markdown_parser(week_num)[0].Meta


def style_html(soup):
    """
    Apply inline styles to HTML elements for RSS feed display.

    Styles various elements for consistent rendering across RSS readers
    and email clients that may not support external stylesheets.
    """
    # 1. h4 (source label) — subtle small-caps label
    for h4 in soup.find_all("h4"):
        h4["style"] = (
            "font-size: 11px; font-weight: normal; letter-spacing: 2px; "
            "text-transform: uppercase; color: #8B7355; margin: 0 0 2px 0;"
        )

    # 2. h5 (chapter title) — dignified italic chapter heading
    for h5 in soup.find_all("h5"):
        h5["style"] = (
            "font-size: 15px; font-weight: normal; font-style: italic; "
            "color: #5C1A2A; margin: 0 0 16px 0;"
        )

    # 3. span.q (Q/A labels) — burgundy accent
    for span in soup.find_all("span", class_="q"):
        span["style"] = "font-weight: bold; color: #5C1A2A;"

    # 4. sup (footnote numbers) — muted, smaller
    for sup in soup.find_all("sup"):
        sup["style"] = "font-size: 11px; color: #8B7355;"

    # 5. hr in .footnote — styled border
    for footnote_div in soup.find_all("div", class_="footnote"):
        for hr in footnote_div.find_all("hr"):
            hr["style"] = (
                "border: none; border-top: 1px solid #D6CBAF; "
                "margin: 24px 0 16px 0;"
            )

    # 6. ol in footnotes — smaller than body text
    for footnote_div in soup.find_all("div", class_="footnote"):
        for ol in footnote_div.find_all("ol"):
            ol["style"] = (
                "padding-left: 18px; margin: 0; font-size: 14px; "
                "line-height: 1.7; color: #3D2E1F;"
            )

    # 7. h5 inside footnotes — burgundy verse labels (overrides #2)
    for footnote_div in soup.find_all("div", class_="footnote"):
        for h5 in footnote_div.find_all("h5"):
            h5["style"] = (
                "font-size: 13px; font-weight: bold; color: #5C1A2A; "
                "margin: 14px 0 4px 0;"
            )

    # 8. div.esv-text — left-border blockquote effect for scripture
    for div in soup.find_all("div", class_="esv-text"):
        div["style"] = "padding-left: 12px; border-left: 2px solid #D6CBAF;"

    # 9. span.small-caps — for "LORD"
    for span in soup.find_all("span", class_="small-caps"):
        span["style"] = "font-variant: small-caps;"

    # 10. span.indent — replace with em space for email client compatibility
    for span in soup.find_all("span", class_="indent"):
        span.replace_with(NavigableString("\u2003"))

    # 11. div.block-indent — hanging indent for poetry
    for div in soup.find_all("div", class_="block-indent"):
        div["style"] = "padding-left: 16px; text-indent: -16px;"


def content(week_num):
    """
    Process and format the content for a specific week.

    This function:
    1. Converts markdown to HTML
    2. Processes the HTML for email compatibility
    3. Removes unnecessary HTML elements
    4. Applies inline styles for RSS display
    5. Cleans up whitespace and special characters

    Args:
        week_num (int): Week number (1-52)

    Returns:
        str: Processed HTML content
    """
    md_as_html = markdown_parser(week_num)[1]
    # Process HTML for email compatibility
    c = transform(md_as_html, preserve_internal_links=True)
    soup = BeautifulSoup(c, "lxml")
    # Remove all anchor tags while preserving their content
    for a in soup.find_all("a"):
        a.unwrap()
    # Apply inline styles for RSS readers
    style_html(soup)
    c = str(soup)
    # Extract just the body content
    c = c[(c.find("body") + len("body>")) : -len("</body></html>")]
    # Clean up whitespace and special characters
    c = c.replace("\n", "")
    c = c.replace("\xa0", " ")
    return c


def main():
    """
    Generate the RSS feed with entries for the last NUMBER_OF_WEEKS weeks.

    This function:
    1. Sets up the feed generator with basic metadata
    2. Iterates through the last NUMBER_OF_WEEKS weeks
    3. Creates an entry for each week with content and metadata
    4. Saves the feed to heidelberg-feed.rss
    """
    # Initialize the feed generator
    fg = FeedGenerator()
    fg.id(f"{URL}/{FILENAME}")
    fg.title("Heidelberg Weekly")
    fg.author({"name": "Heidelberg Weekly"})
    fg.subtitle("Read through the Heidelberg Catechism in a year.")
    fg.link(href=f"{URL}/")
    fg.link(href=f"{URL}/feed.rss", rel="self")
    fg.language("en")

    # Get current time in Eastern timezone
    now = dt.datetime.now(tz=pytz.timezone("US/Eastern"))

    # Get current week number
    current_week = get_week_number_for_date(now)

    # Generate entries for each of the last NUMBER_OF_WEEKS weeks
    for i in reversed(range(NUMBER_OF_WEEKS)):
        # Calculate week number (going backwards from current week)
        week_num = ((current_week - i - 1) % 52) + 1
        week_fmt = f"{week_num:02d}"

        # Calculate the Sunday date for this week
        # Find first Sunday of January
        jan_1 = dt.datetime(now.year, 1, 1, tzinfo=now.tzinfo)
        days_until_sunday = (6 - jan_1.weekday()) % 7
        if days_until_sunday == 0 and jan_1.weekday() == 6:
            first_sunday = jan_1
        else:
            first_sunday = jan_1 + dt.timedelta(days=days_until_sunday)

        # Calculate this week's Sunday
        week_date = first_sunday + dt.timedelta(weeks=week_num - 1)
        week_date = week_date.replace(hour=0, minute=0, second=0, microsecond=0)

        url = f"{URL}/week-{week_fmt}/"

        # Create feed entry
        fe = fg.add_entry()
        fe.id(url)
        fe.title(meta(week_num)["pagetitle"][0])
        fe.link(href=url)
        fe.guid(url, permalink=True)
        fe.content(content(week_num), type="CDATA")
        fe.updated(week_date)
        fe.published(week_date)

    # Write the RSS feed to file
    fg.rss_file(FILENAME, pretty=True)


if __name__ == "__main__":
    main()
