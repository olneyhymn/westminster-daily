import datetime as dt

from dateutil import parser
from flask import Flask, render_template
from flask import Markup, request
from werkzeug.routing import BaseConverter

import data

# create our application
app = Flask(__name__)


class RegexConverter(BaseConverter):

    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


app.url_map.converters['regex'] = RegexConverter


@app.context_processor
def inject_site_defaults():
    return dict(site_title="Westminster Standards",
                tagline="Read through the Westminster Standards in a year.",
                )


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
    url = "http://{host}/".format(host=request.host)
    return render_content(*content, page_title=page_title, url=url)


@app.route('/<regex("[0-1][0-9]"):month>/<regex("[0-9][0-9]"):day>')
@app.route('/<regex("[0-1][0-9]"):month>/<regex("[0-9][0-9]"):day>/')
def render_day(month, day):
    content = data.get_day(month, day)
    url = "http://{host}/{month:0>2}/{day:0>2}".format(host=request.host,
                                                       path=request.path,
                                                       month=month,
                                                       day=day)
    return render_content(month, day, content, url=url)


# Render page for generating facebook/twitter images
@app.route('/i/<regex("[0-1][0-9]"):month>/<regex("[0-9][0-9]"):day>')
def render_image_page(month, day):
    content = data.get_day(month, day)
    return render_content(month, day, content, template='image_t.html')


# Render main page
def render_content(month, day, content, page_title=None, template='content_page_t.html', url=None):
    if page_title is None:
        page_title = ", ".join(c['citation'] for c in content)
    description = ", ".join(c['long_citation'] for c in content)
    return render_template(template,
                           content=content,
                           date=get_date(month, day),
                           page_title=page_title,
                           description=description,
                           url=url)


def get_date(month, day):
    leap_year = 2008
    date = dt.date(leap_year, int(month), int(day))
    return date
