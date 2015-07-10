import datetime as dt
import os

from dateutil import parser
from flask import Flask, session, render_template, request_started
from flask import Markup
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
    return dict(site_title="Daily Westminster")


def next_datetime(date):
    return format_datetime(parser.parse(date) + dt.timedelta(days=1))


def prev_datetime(date):
    return format_datetime(parser.parse(date) - dt.timedelta(days=1))


def today_datetime(date):
    return format_datetime(parser.parse(date))


def format_datetime(date):
    return Markup("<a href=\"/{month}/{day}\">{Month} {Day}</a>".format(
            month=date.strftime('%m'),
            day=date.strftime('%d'),
            Month=date.strftime("%-B"),
            Day=date.strftime("%-d"),
        ))

app.jinja_env.filters['today'] = today_datetime
app.jinja_env.filters['tomorrow'] = next_datetime
app.jinja_env.filters['yesterday'] = prev_datetime



def get_today_content():
    month = dt.datetime.today().month
    day = dt.datetime.today().day
    return month, day, data.get_day(month, day)


@app.errorhandler(404)
def page_not_found(e):
    return render_content(*get_today_content()), 404


@app.route('/')
def render_today():
    return render_content(*get_today_content())


@app.route('/<regex("[0-1][0-9]"):month>/<regex("[0-9][0-9]"):day>')
def render_day(month, day):
    try:
        content = data.get_day(month, day)
    except:
        content = get_today_content()
    return render_content(month, day, content)


def render_content(month, day, content):
    get_date(month, day)
    if content[0].abbv == "wcf":
        assert len(content) == 1
        content = content[0]
        chapter = content.data.keys()[0]
        section = content.data.values()[0].keys()[0]
        body = content.data[chapter][section]
        return render_template('confession_t.html',
                               title=content.doc_title,
                               chapter=chapter,
                               section=section,
                               content=body,
                               date=get_date(month, day))
    else:
        return render_template('catechism_t.html',
                               content=content,
                               date=get_date(month, day))

def get_date(month, day):
    now = dt.datetime.now()
    date = dt.date(now.year, int(month), int(day))
    return date
