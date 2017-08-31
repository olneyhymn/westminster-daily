import datetime as dt
import pytz
import premailer

from werkzeug.contrib.atom import AtomFeed
from jinja2 import Environment, PackageLoader

import data


jinja = Environment(
    loader=PackageLoader('flask_application', 'templates')
)


def _inline_styles(s, *args, **kwargs):
    pm = premailer.Premailer(s, *args, **kwargs)
    return pm.transform()

jinja.filters['inline_styles'] = _inline_styles


def make_feed(site_title, feed_url, url, timezone, prooftexts, start_date=None, count=62):
    feed = AtomFeed(site_title,
                    author=site_title,
                    feed_url=feed_url,
                    url=url)
    if start_date is None:
        now = dt.datetime.now(tz=pytz.timezone(timezone))
    else:
        now = start_date
    for date in (now - dt.timedelta(n) for n in range(count)):
        month = date.strftime('%m')
        day = date.strftime('%d')
        content = data.get_day(str(date.month), str(date.day), prooftexts=prooftexts)
        page_title = data.get_day_title(month, day)
        url = 'http://reformedconfessions.com/westminster-daily/{date:%m}/{date:%d}/'.format(date=date)

        feed.add(page_title,
                 render_feed_page(month, day, content,
                                  url=url),
                 content_type='html',
                 url=url,
                 published=date,
                 updated=date)
    return feed


def render_feed_page(month, day, content, page_title=None,
                     static=False, url=None):
    if page_title is None:
        page_title = data.get_day_title(month, day)
    if url is None:
        raise ValueError("url must be provided")
    prooftexts = any(len(c["prooftexts"]) for c in content)
    description = ", ".join(c['long_citation'] for c in content)
    template = jinja.get_template('feed_item_t.html')
    return template.render(prooftexts = prooftexts,
                           content=content,
                           date=get_date(month, day),
                           page_title=page_title,
                           description=description,
                           static=static,
                           url=url)


def get_date(month, day):
    date = dt.date(2008, int(month), int(day))
    return date
