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
Westminster Daily RSS Feed Generator

This script generates an RSS feed for the Westminster Daily content, which provides
daily readings from the Westminster Confession and Catechisms. The feed includes
the last 30 days of content, with each entry containing the formatted content
and metadata for that day's reading.

The script:
1. Reads markdown content files for each day
2. Converts markdown to HTML
3. Processes the HTML for proper display
4. Generates an RSS feed with entries for each day
5. Saves the feed to feed.rss
"""

from feedgen.feed import FeedGenerator
import datetime as dt
import pytz
from premailer import transform
import markdown
from functools import lru_cache
from bs4 import BeautifulSoup

# Base URL for the website and output filename
URL = "https://reformedconfessions.com/westminster-daily"
FILENAME = "feed.rss"
NUMBER_OF_DAYS = 30  # Number of days of content to include in the feed


@lru_cache()
def markdown_parser(month, day):
    """
    Parse the markdown content for a specific day.

    Args:
        month (str): Two-digit month (01-12)
        day (str): Two-digit day (01-31)

    Returns:
        tuple: (markdown parser instance, converted HTML content)
    """
    with open(f"content/{month}/{day}.md", "r") as f:
        md = f.read()
    markdown_parser = markdown.Markdown(
        extensions=["meta", "footnotes"],
        extension_configs={"footnotes": {"BACKLINK_TEXT": ""}},
    )
    return markdown_parser, markdown_parser.convert(md)


def meta(month, day):
    """
    Extract metadata from the markdown content for a specific day.

    Args:
        month (str): Two-digit month (01-12)
        day (str): Two-digit day (01-31)

    Returns:
        dict: Metadata from the markdown file
    """
    return markdown_parser(month, day)[0].Meta


def content(month, day):
    """
    Process and format the content for a specific day.

    This function:
    1. Converts markdown to HTML
    2. Processes the HTML for email compatibility
    3. Removes unnecessary HTML elements
    4. Cleans up whitespace and special characters

    Args:
        month (str): Two-digit month (01-12)
        day (str): Two-digit day (01-31)

    Returns:
        str: Processed HTML content
    """
    md_as_html = markdown_parser(month, day)[1]
    # Process HTML for email compatibility
    c = transform(md_as_html, preserve_internal_links=True)
    soup = BeautifulSoup(c, "lxml")
    # Remove all anchor tags while preserving their content
    for a in soup.find_all("a"):
        a.unwrap()
    c = str(soup)
    # Extract just the body content
    c = c[(c.find("body") + len("body>")) : -len("</body></html>")]
    # Clean up whitespace and special characters
    c = c.replace("\n", "")
    c = c.replace("\xa0", " ")
    return c


def main():
    """
    Generate the RSS feed with entries for the last NUMBER_OF_DAYS days.

    This function:
    1. Sets up the feed generator with basic metadata
    2. Iterates through the last NUMBER_OF_DAYS days
    3. Creates an entry for each day with content and metadata
    4. Saves the feed to feed.rss
    """
    # Initialize the feed generator
    fg = FeedGenerator()
    fg.id(f"{URL}/{FILENAME}")
    fg.title("Westminster Daily")
    fg.author({"name": "Westminster Daily"})
    fg.subtitle("Read through the Westminster Confession and Catechisms in a year.")
    fg.link(href=f"{URL}/")
    fg.link(href=f"{URL}/{FILENAME}", rel="self")
    fg.language("en")

    # Get current time in Eastern timezone
    now = dt.datetime.now(tz=pytz.timezone("US/Eastern"))

    # Generate entries for each day
    for date in (now - dt.timedelta(n) for n in reversed(range(NUMBER_OF_DAYS))):
        # Set time to midnight
        date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        month = date.strftime("%m")
        day = date.strftime("%d")
        url = f"{URL}/{month}/{day}/"

        # Create feed entry
        fe = fg.add_entry()
        fe.id(url)
        fe.title(meta(month, day)["pagetitle"][0])
        fe.link(href=url)
        fe.guid(url, permalink=True)
        fe.content(content(month, day), type="CDATA")
        fe.updated(date)
        fe.published(date)

    # Write the RSS feed to file
    fg.rss_file(FILENAME, pretty=True)


if __name__ == "__main__":
    main()
