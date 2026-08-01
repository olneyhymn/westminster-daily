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
import json
import pytz
from premailer import transform
import markdown
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

# Constants for the podcast feed configuration
URL = "https://reformedconfessions.com/westminster-daily"  # Base URL for the podcast
FILENAME = "podcast.rss"  # Output RSS feed filename

# Expose the full year of episodes. Walking back 365 days covers every
# calendar day exactly once (Feb 29 has no content), each with a real past
# publication date, so the whole catalogue is visible to directories and
# podcast search instead of a 30-day sliver.
NUMBER_OF_DAYS = 365

# Stable identity for the show itself. Without this every directory derives
# its own GUID from the feed URL, so the show fragments across platforms and
# a future feed move would orphan it.
PODCAST_GUID = "d9282da9-ef51-5b85-9393-1338eb8077af"


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


@lru_cache()
def day_data(month, day):
    """
    Load the per-day data.json, which carries the structured citations.

    Returns None when the file is absent so callers can fall back to the
    markdown metadata.
    """
    try:
        with open(f"content/{month}/{day}/data.json", "r") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def episode_title(month, day):
    """
    Build a searchable episode title for a specific date.

    Titles used to be the bare question, which left eight pairs of episodes
    with byte-identical names (WLC 101 and WSC 43 both ask about the preface
    to the Ten Commandments) and gave podcast search nothing to match on.
    Prefixing the citation disambiguates them and puts the terms people
    actually search for -- "Shorter Catechism 63", "WLC 123" -- in the title.
    """
    fallback = meta(month, day)["pagetitle"][0]
    data = day_data(month, day)
    if not data:
        return fallback

    title = data.get("title") or fallback
    citations = [c["citation"] for c in data.get("content", []) if c.get("citation")]
    if not citations:
        return title
    return f"{' + '.join(citations)} — {title}"


def enclosure_length(mp3_url):
    """
    Look up the audio file's byte size.

    The enclosure length was hardcoded to 0 on every item, which is a spec
    violation and a submission risk. The files live on S3 rather than in the
    repo, so this needs a HEAD request. Falls back to 0 rather than failing
    the build if S3 is unreachable.
    """
    try:
        req = Request(mp3_url, method="HEAD")
        with urlopen(req, timeout=10) as resp:
            return int(resp.headers.get("Content-Length", 0))
    except Exception:
        return 0


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
    # "clean" is a legacy value; the current spec wants true/false and
    # validators reject the old form.
    fg.podcast.itunes_explicit("no")
    fg.podcast.itunes_subtitle(
        "Listen to the Westminster Confession and Catechisms in a year."
    )
    fg.podcast.itunes_summary(
        "Listen to the Westminster Confession and Catechisms in a year.  Based on Calendar of Readings in the Westminster Standards by Dr. Joey Pipa."
    )
    # Spotify, YouTube, and Amazon all prove feed ownership by mailing a code
    # to this address, so it has to be deliverable. waiting-tables.com has no
    # MX records at all; this one routes through Cloudflare Email Routing.
    fg.podcast.itunes_owner(
        name="Westminster Daily", email="podcast@reformedconfessions.com"
    )
    fg.podcast.itunes_image("https://reformedconfessions.com/images/pulpit_full.png")
    fg.podcast.itunes_author("Westminster Daily")
    
    # Configure feed metadata
    # Was a FeedPress URL that no longer sits in the delivery path.
    fg.id(f"{URL}/")
    fg.title("Westminster Daily")
    fg.author({"name": "Westminster Daily"})
    fg.subtitle("Listen to the Westminster Confession and Catechisms in a year.")
    fg.link(href=f"{URL}/")
    fg.link(href=f"{URL}/{FILENAME}", rel="self")
    fg.language("en")

    # Get current time in Eastern timezone
    now = dt.datetime.now(tz=pytz.timezone("US/Eastern"))

    # Walk back a full year, oldest first.
    dates = [
        (now - dt.timedelta(n)).replace(hour=0, minute=0, second=0, microsecond=0)
        for n in reversed(range(NUMBER_OF_DAYS))
    ]

    def mp3_for(date):
        return (
            "https://s3.amazonaws.com/www.reformedconfessions.com"
            f"/westminster-daily/static/audio/{date:%m}{date:%d}.mp3"
        )

    # Size every enclosure concurrently; 366 serial HEAD requests would
    # dominate the build.
    with ThreadPoolExecutor(max_workers=16) as pool:
        lengths = list(pool.map(lambda d: enclosure_length(mp3_for(d)), dates))

    for date, length in zip(dates, lengths):
        month = date.strftime("%m")
        day = date.strftime("%d")

        url = f"{URL}/{month}/{day}"
        # The guid previously omitted the year, so every episode collided
        # with the same calendar day from the year before and clients
        # deduplicated it away -- anyone subscribed longer than a year
        # silently stopped receiving episodes. A tag URI keeps the guid
        # unique per airing without pretending to be a permalink.
        guid = f"tag:reformedconfessions.com,{date:%Y}:westminster-daily/{month}/{day}"

        fe = fg.add_entry()
        fe.id(url)
        fe.enclosure(mp3_for(date), length, "audio/mpeg")
        fe.title(episode_title(month, day))
        fe.link(href=url)
        fe.guid(guid, permalink=False)
        fe.content(content(month, day), type="CDATA")
        fe.updated(date)
        fe.published(date)

    # Write the RSS feed to a file
    fg.rss_file(FILENAME, pretty=True)

    # Inject xml-stylesheet processing instruction so browsers render
    # the feed with podcast.xsl while podcast apps ignore it.
    stylesheet_pi = (
        '<?xml-stylesheet type="text/xsl" '
        'href="/westminster-daily/podcast.xsl"?>\n'
    )
    with open(FILENAME, "r", encoding="utf-8") as f:
        rss = f.read()
    xml_decl_end = rss.find("?>") + len("?>")
    rss = rss[:xml_decl_end] + "\n" + stylesheet_pi + rss[xml_decl_end:].lstrip("\n")

    # feedgen has no podcast-namespace support, so declare it and stamp the
    # show guid by hand.
    rss = rss.replace(
        "<rss ",
        '<rss xmlns:podcast="https://podcastindex.org/namespace/1.0" ',
        1,
    )
    rss = rss.replace(
        "<channel>",
        f"<channel>\n    <podcast:guid>{PODCAST_GUID}</podcast:guid>",
        1,
    )

    with open(FILENAME, "w", encoding="utf-8") as f:
        f.write(rss)


if __name__ == "__main__":
    main()
