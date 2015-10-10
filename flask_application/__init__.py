import datetime as dt
import pytz

from dateutil import parser
from functools import wraps
from flask import Flask, render_template
from flask import Markup, request
from werkzeug.routing import BaseConverter
from werkzeug.contrib.atom import AtomFeed
from werkzeug.contrib.cache import SimpleCache

import config
import data

LEAP_YEAR = 2008


# create our application
app = Flask(__name__)
cache = SimpleCache()
app.config.from_object(config.Config)


def cached(timeout=0 if app.config['DEBUG'] else 60 * 60, key='view/%s'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = key % request.path
            rv = cache.get(cache_key)
            if rv is not None:
                return rv
            rv = f(*args, **kwargs)
            cache.set(cache_key, rv, timeout=timeout)
            return rv
        return decorated_function
    return decorator


class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]
app.url_map.converters['regex'] = RegexConverter


@app.context_processor
def inject_site_defaults():
    return dict(site_title=app.config['SITE_TITLE'],
                tagline=app.config['SITE_TAGLINE'],
                )


def next_datetime(date):
    return format_datetime(date + dt.timedelta(days=1), post=" > ")


def prev_datetime(date):
    return format_datetime(date - dt.timedelta(days=1), pre=" < ")


def today_datetime(date):
    return format_datetime(date)


def format_datetime(date, pre=None, post=None):
    pre = "" if pre is None else pre
    post = "" if post is None else post
    return Markup("<a href=\"/{month}/{day}\">{pre}{Month} {Day}{post}</a>".format(
        month=date.strftime('%m'),
        day=date.strftime('%d'),
        Month=date.strftime("%-b"),
        Day=date.strftime("%-d"),
        pre=pre,
        post=post,
    ))

app.jinja_env.filters['today'] = today_datetime
app.jinja_env.filters['tomorrow'] = next_datetime
app.jinja_env.filters['yesterday'] = prev_datetime


@app.errorhandler(data.DataException)
def page_not_found(e):
    return render_template('404_t.html', message=e.message), 404


@app.route('/feed.rss')
@cached()
def recent_feed():
    feed = AtomFeed(app.config['SITE_TITLE'],
                    author=app.config['SITE_TITLE'],
                    feed_url=request.url,
                    url=request.url_root)
    now = dt.datetime.now(tz=pytz.timezone(app.config['TZ']))
    for date in (now - dt.timedelta(n) for n in range(365)):
        date = date.date()
        month = date.strftime('%m')
        day = date.strftime('%d')
        content = data.get_day(str(date.month), str(date.day))
        page_title = ", ".join(c['long_citation'] for c in content)
        url = "http://{}/{}/{}".format(request.host, month, day)
        feed.add(page_title,
                 render_content(month, day, content, url=url, template='content_body_t.html'),
                 content_type='html',
                 url=url,
                 published=date,
                 updated=date,
                 )
    return feed.get_response()


@app.route('/')
@cached()
def render_today():
    page_title = "A Daily Reading"
    content = data.get_today_content(tz=app.config['TZ'])
    url = "http://{host}/".format(host=request.host)
    return render_content(*content, page_title=page_title, url=url)


@app.route('/<regex("[0-1][0-9]"):month>/<regex("[0-9][0-9]"):day>')
@app.route('/<regex("[0-1][0-9]"):month>/<regex("[0-9][0-9]"):day>/')
@cached()
def render_day(month, day):
    content = data.get_day(month, day)
    url = "http://{host}/{month:0>2}/{day:0>2}".format(host=request.host,
                                                       path=request.path,
                                                       month=month,
                                                       day=day)
    return render_content(month, day, content, url=url, static=True)


# Render page for generating facebook/twitter images
@app.route('/i/<regex("[0-1][0-9]"):month>/<regex("[0-9][0-9]"):day>')
def render_image_page(month, day):
    content = data.get_day(month, day)
    return render_content(month, day, content, template='image_t.html')


# Render main page
def render_content(month, day, content, page_title=None,
                   template='content_page_t.html', url=None, static=False):
    if page_title is None:
        page_title = ", ".join(c['citation'] for c in content)
    description = ", ".join(c['long_citation'] for c in content)
    return render_template(template,
                           content=content,
                           date=get_date(month, day),
                           page_title=page_title,
                           description=description,
                           url=url,
                           static=static)


def get_date(month, day):
    date = dt.date(LEAP_YEAR, int(month), int(day))
    return date
