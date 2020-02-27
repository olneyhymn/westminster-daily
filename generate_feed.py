from feedgen.feed import FeedGenerator
import datetime as dt
import pytz
from flask_application import data

fg = FeedGenerator()
fg.id("http://reformedconfessions.com/westminster-daily/feed.rss")
fg.title("Westminster Daily")
fg.author({"name": "Westminster Daily"})
fg.link(href="http://reformedconfessions.com/", rel="alternate")
# fg.logo('http://ex.com/logo.jpg')
fg.subtitle("Read through the Westminster Confession and Catechisms in a year.")
fg.link(href="http://reformedconfessions.com/westminster-daily/feed.rss", rel="self")
fg.language("en")

now = dt.datetime.now(tz=pytz.timezone("US/Eastern"))

for date in (now - dt.timedelta(n) for n in range(2)):
    date = date.replace(hour=0, minute=0, second=0, microsecond=0)
    month = date.strftime("%m")
    day = date.strftime("%d")
    day_data = data.get_day_api(month, day, False)
    page_title = day_data["title"]
    rendered_content = day_data["feed"]

    url = "http://reformedconfessions.com/westminster-daily/{date:%m}/{date:%d}/".format(
        date=date
    )

    fe = fg.add_entry()
    fe.id(url)
    fe.title(page_title,)
    fe.link(href=url)
    fe.content(rendered_content, type="CDATA")
    fe.updated(date)
    fe.published(date)


atomfeed = fg.atom_str(pretty=True)  # Get the ATOM feed as string
rssfeed = fg.rss_str(pretty=True)  # Get the RSS feed as string
fg.atom_file("atom.xml")  # Write the ATOM feed to a file
fg.rss_file("rss.xml")  # Write the RSS feed to a file
