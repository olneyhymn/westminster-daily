# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "feedgen==1.0.0",
#     "pytz==2025.2",
#     "premailer==3.10.0",
#     "markdown==3.5.1",
#     "beautifulsoup4==4.12.2",
# ]
# ///

"""
Script to generate an RSS podcast feed for the Westminster Daily podcast.

This script creates an RSS feed that contains the last 30 days of podcast episodes
for the Westminster Daily podcast, which provides daily readings from the Westminster
Confession and Catechisms. The feed includes metadata, audio file URLs, and formatted
content for each episode.

The script processes markdown files containing the daily content, converts them to HTML,
and generates a podcast-compatible RSS feed that can be consumed by podcast players.
"""

from feedgen.feed import FeedGenerator
import datetime as dt
import pytz
from premailer import transform
import markdown
from functools import lru_cache
from bs4 import BeautifulSoup

# Constants for the podcast feed configuration
URL = "https://reformedconfessions.com/westminster-daily"  # Base URL for the podcast
FILENAME = "podcast.rss"  # Output RSS feed filename
NUMBER_OF_DAYS = 30  # Number of days of content to include in the feed


@lru_cache()
def markdown_parser(month, day):
    """
    Parse markdown content for a specific date.
    
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
    Extract metadata from the markdown file for a specific date.
    
    Args:
        month (str): Two-digit month (01-12)
        day (str): Two-digit day (01-31)
        
    Returns:
        dict: Metadata from the markdown file
    """
    return markdown_parser(month, day)[0].Meta


def content(month, day):
    """
    Process and format the content for a specific date.
    
    This function:
    1. Converts markdown to HTML
    2. Processes the HTML with premailer
    3. Cleans up the HTML using BeautifulSoup
    4. Removes unnecessary tags and whitespace
    
    Args:
        month (str): Two-digit month (01-12)
        day (str): Two-digit day (01-31)
        
    Returns:
        str: Cleaned and formatted HTML content
    """
    md_as_html = markdown_parser(month, day)[1]
    c = transform(md_as_html, preserve_internal_links=True)
    soup = BeautifulSoup(c, features="lxml")
    for a in soup.findAll("a"):
        a.replaceWithChildren()
    c = str(soup)
    c = c[(c.find("body") + len("body>")) : -len("</body></html>")]
    c = c.replace("\n", "")
    c = c.replace("\xa0", " ")
    return c


def main():
    """
    Generate the podcast RSS feed.
    
    This function:
    1. Creates and configures the RSS feed generator
    2. Sets up podcast-specific metadata
    3. Processes the last 30 days of content
    4. Generates the RSS feed file
    """
    # Initialize the feed generator and load podcast extension
    fg = FeedGenerator()
    fg.load_extension("podcast")
    
    # Configure podcast metadata
    fg.podcast.itunes_category("Religion & Spirituality", "Christianity")
    fg.podcast.itunes_explicit("clean")
    fg.podcast.itunes_subtitle(
        "Listen to the Westminster Confession and Catechisms in a year."
    )
    fg.podcast.itunes_summary(
        "Listen to the Westminster Confession and Catechisms in a year.  Based on Calendar of Readings in the Westminster Standards by Dr. Joey Pipa."
    )
    fg.podcast.itunes_owner(name="Westminster Daily", email="tim@waiting-tables.com")
    fg.podcast.itunes_image("https://reformedconfessions.com/images/pulpit_full.png")
    fg.podcast.itunes_author("Westminster Daily")
    
    # Configure feed metadata
    fg.id("https://feedpress.me/westminster-daily-audio")
    fg.title("Westminster Daily")
    fg.author({"name": "Westminster Daily"})
    fg.subtitle("Listen to the Westminster Confession and Catechisms in a year.")
    fg.link(href=f"{URL}/")
    fg.link(href="https://feedpress.me/westminster-daily-audio", rel="self")
    fg.language("en")

    # Get current time in Eastern timezone
    now = dt.datetime.now(tz=pytz.timezone("US/Eastern"))

    # Process the last 30 days of content
    for date in (now - dt.timedelta(n) for n in reversed(range(NUMBER_OF_DAYS))):
        # Normalize date to start of day
        date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        month = date.strftime("%m")
        day = date.strftime("%d")
        
        # Generate URLs for the episode
        url = f"{URL}/{month}/{day}/"
        mp3_url = f"https://d2pmxb5xfppxte.cloudfront.net/static/audio/{month}{day}.mp3"
        
        # Add entry to the feed
        fe = fg.add_entry()
        fe.id(url)
        fe.enclosure(mp3_url, 0, "audio/mpeg")
        fe.title(meta(month, day)["pagetitle"][0])
        fe.link(href=url)
        fe.guid(url, permalink=True)
        fe.content(content(month, day), type="CDATA")
        fe.updated(date)
        fe.published(date)

    # Write the RSS feed to a file
    fg.rss_file(FILENAME, pretty=True)


if __name__ == "__main__":
    main()
