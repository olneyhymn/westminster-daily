import datetime as dt
import os

from dateutil import parser
from flask import Flask, session, render_template, request_started
from flask import Markup, abort
from werkzeug import SharedDataMiddleware
from werkzeug.routing import BaseConverter

import data

# create our application
app = Flask(__name__)

# Config
if app.config['DEBUG']:
    app.config.from_object('flask_application.config.DevelopmentConfig')
    app.logger.info("Config: Development")
else:
    app.config.from_object('flask_application.config.ProductionConfig')
    app.logger.info("Config: Production")

# Source: http://www.jeffff.com/serving-media-in-the-flask-local-dev-server:w


def serve_static(sender):
    if app.config['DEBUG']:
        app.wsgi_app = SharedDataMiddleware(app.wsgi_app,
                                            {'/': os.path.join(os.path.dirname(__file__), 'static')})

request_started.connect(serve_static, app)


class RegexConverter(BaseConverter):

    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


app.url_map.converters['regex'] = RegexConverter


@app.before_request
def before_request():
    session["debug"] = app.debug


@app.after_request
def after_request(response):
    return response


@app.context_processor
def inject_site_defaults():
    return dict(site_title="Westminster Standards")


def next_datetime(date):
    return format_datetime(parser.parse(date) + dt.timedelta(days=1), post=" > ")


def prev_datetime(date):
    return format_datetime(parser.parse(date) - dt.timedelta(days=1), pre=" < ")


def today_datetime(date):
    return format_datetime(parser.parse(date))


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



def get_today_content():
    month = dt.datetime.today().month
    day = dt.datetime.today().day
    return month, day, data.get_day(month, day)


@app.errorhandler(data.DataException)
def page_not_found(e):
    return render_template('404_t.html', message=e.message), 404


@app.route('/')
def render_today():
    page_title = "A Daily Reading"
    content = get_today_content()
    return render_content(*content, page_title=page_title)


@app.route('/<regex("[0-1][0-9]"):month>/<regex("[0-9][0-9]"):day>')
def render_day(month, day):
    content = data.get_day(month, day)
    return render_content(month, day, content)


# Render page for generating facebook/twitter images
@app.route('/i/<regex("[0-1][0-9]"):month>/<regex("[0-9][0-9]"):day>')
def render_image_page(month, day):
    content = data.get_day(month, day)
    return render_content(month, day, content, template='image_t.html')


# Render main page
def render_content(month, day, content, page_title=None, template='content_page_t.html'):
    if page_title is None:
        page_title = ", ".join(c['citation'] for c in content)
    return render_template(template,
                           content=content,
                           date=get_date(month, day),
                           page_title=page_title)


def get_date(month, day):
    now = dt.datetime.now()
    date = dt.date(now.year, int(month), int(day))
    return date
