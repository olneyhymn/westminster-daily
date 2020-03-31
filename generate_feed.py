from feedgen.feed import FeedGenerator
import datetime as dt
import pytz
from premailer import transform
import markdown
from functools import lru_cache
from bs4 import BeautifulSoup

URL = "https://pandoc--westminster-daily.netlify.com/westminster-daily"
FILENAME = "feed.rss"
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
    c = c[(c.find("body") + len("body>")) : -len("</body></html>")]
    c = c.replace("&nbsp;", "")
    soup = BeautifulSoup(c)
    for a in soup.findAll("a"):
        a.replaceWithChildren()
    return str(soup)


def main():
    fg = FeedGenerator()
    fg.id(f"{URL}/{FILENAME}")
    fg.title("Westminster Daily")
    fg.author({"name": "Westminster Daily"})
    fg.link(href=URL, rel="alternate")
    fg.subtitle("Read through the Westminster Confession and Catechisms in a year.")
    fg.link(href=f"{URL}/{FILENAME}", rel="self")
    fg.language("en")

    now = dt.datetime.now(tz=pytz.timezone("US/Eastern"))

    for date in (now - dt.timedelta(n) for n in reversed(range(NUMBER_OF_DAYS))):
        date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        month = date.strftime("%m")
        day = date.strftime("%d")
        url = f"{URL}/{month}/{day}/"

        fe = fg.add_entry()
        fe.id(url)
        fe.title(meta(month, day)["pagetitle"][0])
        fe.link(href=url)
        fe.guid(url, permalink=True)
        fe.content(content(month, day), type="CDATA")
        fe.updated(date)
        fe.published(date)

    fg.rss_file(FILENAME, pretty=True)  # Write the RSS feed to a file


if __name__ == "__main__":
    main()
