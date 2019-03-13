from __future__ import absolute_import
from builtins import str
from builtins import range
import datetime as dt
import pytz

try:
    import premailer
except:
    pass

from werkzeug.contrib.atom import AtomFeed

from . import data


API_URL = 'http://reformedconfessions.com/'


def make_feed(site_title, feed_url, url, timezone, prooftexts, start_date=None, count=62, api=False):
    feed = AtomFeed(site_title,
                    author=site_title,
                    feed_url=feed_url,
                    url=url)
    if start_date is None:
        now = dt.datetime.now(tz=pytz.timezone(timezone))
    else:
        now = start_date
    for date in (now - dt.timedelta(n) for n in range(count)):
        date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        month = date.strftime('%m')
        day = date.strftime('%d')
        if api is False:
            content = data.get_day(str(date.month), str(date.day), prooftexts=prooftexts)
            rendered_content = render_feed_page(content)
            page_title = data.get_day_title(month, day)
        else:
            day_data = data.get_day_api(month, day, prooftexts, api_url=API_URL)
            page_title = day_data['title']
            rendered_content = day_data['feed']

        url = 'http://reformedconfessions.com/westminster-daily/{date:%m}/{date:%d}/'.format(date=date)

        feed.add(page_title,
                 rendered_content,
                 content_type='html',
                 url=url,
                 published=date,
                 updated=date)
    return feed


def render_feed_page(content):
    from jinja2 import Environment, PackageLoader
    jinja = Environment(
        loader=PackageLoader('flask_application', 'templates')
    )


    def _inline_styles(s, *args, **kwargs):
        pm = premailer.Premailer(s, *args, **kwargs)
        return pm.transform()

    jinja.filters['inline_styles'] = _inline_styles
    template = jinja.get_template('feed_item_t.html')
    return template.render(content=content)


def get_date(month, day):
    date = dt.date(2008, int(month), int(day))
    return date
