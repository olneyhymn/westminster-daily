from __future__ import absolute_import
from builtins import range
import datetime as dt
import os
import premailer

from flask import Flask, render_template
from flask import request
from flask import jsonify
from flask_flatpages import FlatPages
from flask_bower import Bower


from werkzeug.routing import BaseConverter

from . import config
from . import data
from . import feed


LEAP_YEAR = 2008


# create our application
app = Flask(__name__)
pages = FlatPages(app)
Bower(app)


def _inline_styles(s, *args, **kwargs):
    pm = premailer.Premailer(s, *args, **kwargs)
    return pm.transform()

app.jinja_env.filters['inline_styles'] = _inline_styles

if os.environ.get("DEV", "no") == "yes":
    app.config.from_object(config.DevelopmentConfig)
else:
    app.config.from_object(config.ProductionConfig)


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


def get_date(date, which='today', field='m'):
    if which == "today":
        pass
    elif which == "yesterday":
        date = date - dt.timedelta(days=1)
    elif which == "tomorrow":
        date = date + dt.timedelta(days=1)
    else:
        raise NotImplemented()
    return date.strftime('%{}'.format(field))

app.jinja_env.filters['get_date'] = get_date


@app.errorhandler(KeyError)
def page_not_found(e):
    return render_template('404_t.html', message=e), 404


@app.route('/westminster-daily/feed.rss')
def recent_westminster_daily_feed():
    return _feed(prooftexts=True).get_response()


@app.route('/westminster-daily/<regex("[0-1][0-9]"):month>/<regex("[0-3][0-9]"):day>/feed.rss')
def feed_by_day(month, day):
    start_date = dt.datetime(year=2017, day=int(day), month=int(month))
    return _feed(prooftexts=True, start_date=start_date, count=10).get_response()


def _feed(prooftexts, start_date=None, count=62):
    return feed.make_feed(app.config['SITE_TITLE'], request.url,
                          request.url_root, app.config['TZ'],
                          prooftexts, start_date, count)


@app.route('/westminster-daily/test/<regex("[0-1][0-9]"):month>/<regex("[0-3][0-9]"):day>')
@app.route('/westminster-daily/test/<regex("[0-1][0-9]"):month>/<regex("[0-3][0-9]"):day>/')
def render_test(month, day):
    content = data.get_day(month, day, prooftexts=True)
    return render_daily_page(month, day, content, template='feed_item_t.html')


@app.route('/')
def render_today_legacy():
    return render_template('paragraph_page_t.html',
                           title="reformedconfessions.com",
                           content=pages.get_or_404("about"))


@app.route('/westminster-daily/reading-plan/')
def reading_plan():
    page_title = "A Daily Reading"
    start = dt.datetime(2004, 1, 1)
    dates = [start + dt.timedelta(days=i) for i in range(365)]
    content = [(d, data.get_day_title(d.month, d.day)) for d in dates]
    return render_template('reading_plan_t.html',
                           page_title=page_title,
                           content=content)


@app.route('/about')
@app.route('/about/')
def about_page():
    return render_template('paragraph_page_t.html',
                           title="A Daily Reading",
                           content=pages.get_or_404("about"))



@app.route('/westminster-daily')
@app.route('/westminster-daily/')
def render_today():
    page_title = "A Daily Reading"
    content = data.get_today_content(tz=app.config['TZ'], prooftexts=show_prooftexts())
    return render_daily_page(*content, page_title=page_title,
                             url="/westminster-daily", static=False)


@app.route('/westminster-daily/<regex("[0-1][0-9]"):month>/<regex("[0-3][0-9]"):day>/data.json')
def render_fixed_day_json(month, day):
    content = data.get_day(month, day, prooftexts=False)
    content_with_prooftexts = data.get_day(month, day, prooftexts=True)
    title = data.get_day_title(month, day)
    feed_data = feed.render_feed_page(content_with_prooftexts)
    return jsonify({'content': content,
                    'content_with_prooftexts': content_with_prooftexts,
                    'title': title,
                    'feed': feed_data})


@app.route('/westminster-daily/<regex("[0-1][0-9]"):month>/<regex("[0-3][0-9]"):day>')
@app.route('/westminster-daily/<regex("[0-1][0-9]"):month>/<regex("[0-3][0-9]"):day>/')
def render_fixed_day(month, day):
    content = data.get_day(month, day, prooftexts=show_prooftexts())
    return render_daily_page(month, day, content, static=True)


# Render page for generating facebook/twitter images
@app.route('/i/<regex("[0-1][0-9]"):month>/<regex("[0-9][0-9]"):day>.html')
def render_image_page(month, day):
    content = data.get_day(month, day, prooftexts=False)
    return render_daily_page(month, day, content, template='image_t.html')


# Render main page
def render_daily_page(month, day, content, page_title=None,
                      template='content_page_t.html', static=False, url=None):
    if page_title is None:
        page_title = data.get_day_title(month, day)
    if url is None:
        url = request.url
    prooftexts = any(len(c["prooftexts"]) for c in content)
    description = ", ".join(c['long_citation'] for c in content)
    return render_template(template,
                           prooftexts = prooftexts,
                           content=content,
                           date=get_date(month, day),
                           page_title=page_title,
                           description=description,
                           static=static,
                           url=url)


def show_prooftexts():
    return 'hide-prooftexts' not in request.args


def get_date(month, day):
    date = dt.date(LEAP_YEAR, int(month), int(day))
    return date
