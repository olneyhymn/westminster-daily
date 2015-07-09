import datetime as dt
import os

from flask import Flask, session, render_template, request_started
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


def get_today_content():
    month = dt.datetime.today().month
    day = dt.datetime.today().day
    return data.get_day(month, day)


@app.errorhandler(404)
def page_not_found(e):
    return render_content(get_today_content()), 404


@app.route('/')
def render_today():
    return render_content(get_today_content())


@app.route('/<regex("[0-1][0-9]"):month>/<regex("[0-9][0-9]"):day>')
def render_day(month, day):
    try:
        content = data.get_day(month, day)
    except:
        content = get_today_content()
    return render_content(content)


def render_content(content):
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
                               content=body)
    else:
        return render_template('catechism_t.html',
                               content=content)
