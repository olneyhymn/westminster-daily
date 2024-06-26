from feedgen.feed import FeedGenerator
import datetime as dt
import pytz
from premailer import transform
import markdown
from functools import lru_cache
from bs4 import BeautifulSoup

URL = "https://reformedconfessions.com/westminster-daily"
FILENAME = "podcast.rss"
NUMBER_OF_DAYS = 30


@lru_cache()
def markdown_parser(month, day):

    with open(f"content/{month}/{day}.md", "r") as f:
        md = f.read()
    markdown_parser = markdown.Markdown(
        extensions=["meta", "footnotes"],
        extension_configs={"footnotes": {"BACKLINK_TEXT": ""}},
    )
    return markdown_parser, markdown_parser.convert(md)


def meta(month, day):
    return markdown_parser(month, day)[0].Meta


def content(month, day):
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
    fg = FeedGenerator()
    fg.load_extension("podcast")
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
    fg.id("https://feedpress.me/westminster-daily-audio")
    fg.title("Westminster Daily")
    fg.author({"name": "Westminster Daily"})
    fg.subtitle("Listen to the Westminster Confession and Catechisms in a year.")
    fg.link(href=f"{URL}/")
    fg.link(href="https://feedpress.me/westminster-daily-audio", rel="self")
    fg.language("en")

    now = dt.datetime.now(tz=pytz.timezone("US/Eastern"))

    for date in (now - dt.timedelta(n) for n in reversed(range(NUMBER_OF_DAYS))):
        date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        month = date.strftime("%m")
        day = date.strftime("%d")
        url = f"{URL}/{month}/{day}/"
        mp3_url = f"https://d2pmxb5xfppxte.cloudfront.net/static/audio/{month}{day}.mp3"
        fe = fg.add_entry()
        fe.id(url)
        fe.enclosure(mp3_url, 0, "audio/mpeg")
        fe.title(meta(month, day)["pagetitle"][0])
        fe.link(href=url)
        fe.guid(url, permalink=True)
        fe.content(content(month, day), type="CDATA")
        fe.updated(date)
        fe.published(date)

    fg.rss_file(FILENAME, pretty=True)  # Write the RSS feed to a file


if __name__ == "__main__":
    main()
