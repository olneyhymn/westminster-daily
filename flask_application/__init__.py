import datetime as dt
import pytz
import os
import premailer

from functools import wraps
from flask import Flask, render_template
from flask import Markup, request, redirect
from flask import send_from_directory
from markdown import markdown
from werkzeug.routing import BaseConverter
from werkzeug.contrib.atom import AtomFeed
from werkzeug.contrib.cache import SimpleCache

import config
import data

LEAP_YEAR = 2008


# create our application
app = Flask(__name__)
cache = SimpleCache()

if os.environ.get("DEV", "no") == "yes":
    app.config.from_object(config.DevelopmentConfig)
else:
    app.config.from_object(config.ProductionConfig)


def cached(timeout=0 if app.debug else 60 * 60, key='view/%s'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = key % request.url
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
    return format_datetime(date + dt.timedelta(days=1), post=" &gt; ")


def prev_datetime(date):
    return format_datetime(date - dt.timedelta(days=1), pre=" &lt; ")


def today_datetime(date):
    return format_datetime(date)


def format_datetime(date, pre=None, post=None):
    pre = "" if pre is None else pre
    post = "" if post is None else post
    title = data.get_day_title(date.strftime('%m'), date.strftime('%d'))
    return Markup("<a href=\"/westminster-daily/{month}/{day}\" title=\"{title}\">{pre}{Month} {Day}{post}</a>".format(
        month=date.strftime('%m'),
        day=date.strftime('%d'),
        Month=date.strftime("%-b"),
        Day=date.strftime("%-d"),
        pre=pre,
        post=post,
        title=title
    ))

app.jinja_env.filters['today'] = today_datetime
app.jinja_env.filters['tomorrow'] = next_datetime
app.jinja_env.filters['yesterday'] = prev_datetime


@app.template_filter('inline_styles')
def inline_styles(s, *args, **kwargs):
    pm = premailer.Premailer(s, *args, **kwargs)
    return pm.transform()


@app.errorhandler(KeyError)
def page_not_found(e):
    return render_template('404_t.html', message=e.message), 404


@app.route('/feed.rss')
def recent_westminster_daily_feed_legacy():
    return redirect('/westminster-daily/feed.rss', code=301)


@app.route('/westminster-daily/feed.rss')
@cached()
def recent_westminster_daily_feed():
    return _feed(prooftexts=True).get_response()


@app.route('/westminster-daily/feed_no_prooftexts.rss')
@cached()
def recent_westminster_daily_feed_without_prooftexts():
    return _feed(prooftexts=False).get_response()


def _feed(prooftexts):
    feed = AtomFeed(app.config['SITE_TITLE'],
                    author=app.config['SITE_TITLE'],
                    feed_url=request.url,
                    url=request.url_root)
    now = dt.datetime.now(tz=pytz.timezone(app.config['TZ']))
    for date in (now - dt.timedelta(n) for n in range(62)):
        month = date.strftime('%m')
        day = date.strftime('%d')
        content = data.get_day(str(date.month), str(date.day), prooftexts=prooftexts)
        page_title = data.get_day_title(month, day)
        url = "http://{}/westminster-daily/{}/{}".format(request.host, month, day)

        feed.add(page_title,
                 render_daily_page(month, day, content,
                                   template='feed_item_t.html',
                                   url=url),
                 content_type='html',
                 url=url,
                 published=date,
                 updated=date)
    return feed


@app.route('/westminster-daily/test/<regex("[0-1][0-9]"):month>/<regex("[0-3][0-9]"):day>')
@app.route('/westminster-daily/test/<regex("[0-1][0-9]"):month>/<regex("[0-3][0-9]"):day>/')
@cached()
def render_test(month, day):
    content = data.get_day(month, day, prooftexts=True)
    return render_daily_page(month, day, content, template='feed_item_t.html')


@app.route('/westminster-daily/feed_test.rss')
@cached()
def recent_westminster_daily_feed_test():
    return _feed_test(prooftexts=True).get_response()


def _feed_test(prooftexts):
    feed = AtomFeed(app.config['SITE_TITLE'],
                    author=app.config['SITE_TITLE'],
                    feed_url=request.url,
                    url=request.url_root)
    now = dt.datetime.now(tz=pytz.timezone(app.config['TZ']))
    for date in (now - dt.timedelta(n) for n in range(30)):
        month = date.strftime('%m')
        day = date.strftime('%d')
        content = data.get_day(str(date.month), str(date.day), prooftexts=prooftexts)
        page_title = data.get_day_title(month, day)
        url = "http://{}/westminster-daily/{}/{}".format(request.host, month, day)

        feed.add(page_title,
                 render_daily_page(month, day, content,
                                   template='feed_item_t.html',
                                   url=url),
                 content_type='html',
                 url=url,
                 published=date,
                 updated=date)
    return feed


@app.route('/')
def render_today_legacy():
    return redirect('/westminster-daily', code=301)


@app.route('/robots.txt')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])


@app.route('/westminster-daily/reading-plan')
@cached()
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
@cached()
def about_page():
    page_title = "A Daily Reading"
    content = Markup(markdown("""
Since the 17th century, the Westminster Confession of Faith and Catechisms have served as a doctrinal standard for Presbyterian churches. In the [Orthodox Presbyterian Church (OPC)](http://www.opc.org), "Ministers, elders, and deacons... are required to believe the Bible as the only infallible rule of faith and practice, to sincerely receive and adopt the Confession of Faith and Catechisms as containing the system of doctrine taught in Scripture" (Preface to the Book of Church Order, 2014).

The Westminster Confession organizes the core teaching of Scripture in thirty three, topically-arranged chapters. The Shorter Catechism outlines the theology of Scripture in the form of 107 questions and answers. The Larger Catechism expands on the Shorter with 196 questions and (typically longer) answers.

Dr. Chad Van Dixhorn's commendation [the Larger Catechism](http://www.opc.org/new_horizons/NH00/0010b.html) points the reader to benefit of studying all three documents:

> There are many reasons why the Larger Catechism is worth our study. It unifies Presbyterians who use it as one of their church standards. It gives us the meat of the Word of God. It places a greater emphasis on, and gives fuller explanations of, doctrines that maturing Christians need to hear. It emphasizes aspects of the gospel and draws directly from Scripture in a way that other catechisms do not. And the Larger Catechism emphasizes the church, the ministry, preaching, and the sacraments at a time when Presbyterians&mdash;and in fact all Christians&mdash;need to hear of them.

To encourage Christians to read the Westminster Standards, Dr. Joey Pipa Jr. has prepared [a calendar of readings](/westminster-daily/reading-plan) from these three documents. By following his calendar, you will read through the Standards every year. With this site, you can find the daily readings at [reformedconfessions.com/westminster-daily](http://www.reformedconfessions.com/westminster-daily), on [Facebook](https://www.facebook.com/westminsterdaily/), on [Twitter](https://twitter.com/refconfessions), and in your [email](https://feed.press/e/mailverify?feed_id=westminster-daily).

Dr. Pipa provides the follow recommendations with [his original
plan](https://www.gpts.edu/resources/documents/Calendar%20Readings%20in%20WestminsterNumbered.pdf).

1. Use this calendar along with your daily Bible reading or with your
family in family worship.
2. Read section for the day and read proof texts.
3. Memorize the Shorter Catechism on days assigned. Review the
Shorter Catechism on the Lord's Day.
4. Select Scripture texts to memorize along with catechism and
review on the Lord's Day as well.
Some catechism questions are out of numerical order for thematic
purposes. The format coordinates with that used in the "Harmony of the
Westminster Confession and Catechism" by Dr. Morton Smith.

The proof texts here are taken from [The Confession of Faith and Catechisms](http://www.opc.org/confessions.html) by the OPC. Currently, we only provide proof texts for the Confession; we are working on adding those for the Catechisms.

May the Lord bless you as you "press on" to know Him ([Hosea 6](http://www.esvbible.org/Hosea6:3/)).
"""))
    return render_template('paragraph_page_t.html',
                           page_title=page_title,
                           content=content)


@app.route('/westminster-daily')
@cached()
def render_today():
    page_title = "A Daily Reading"
    content = data.get_today_content(tz=app.config['TZ'], prooftexts=show_prooftexts())
    return render_daily_page(*content, page_title=page_title,
                             url="http://{}/westminster-daily".format(request.host))


@app.route('/<regex("[0-1][0-9]"):month>/<regex("[0-3][0-9]"):day>')
@app.route('/<regex("[0-1][0-9]"):month>/<regex("[0-3][0-9]"):day>/')
def render_fixed_day_legacy(month, day):
    url = "http://{host}/westminster-daily/{month:0>2}/{day:0>2}".format(host=request.host,
                                                                         path=request.path,
                                                                         month=month,
                                                                         day=day)
    return redirect(url, code=301)


@app.route('/westminster-daily/<regex("[0-1][0-9]"):month>/<regex("[0-3][0-9]"):day>')
@app.route('/westminster-daily/<regex("[0-1][0-9]"):month>/<regex("[0-3][0-9]"):day>/')
@cached()
def render_fixed_day(month, day):
    content = data.get_day(month, day, prooftexts=show_prooftexts())
    return render_daily_page(month, day, content, static=True)


@app.route('/c/<regex("(wsc|wlc)"):document>/<regex("[0-9]{1,3}"):number>')
def render_catechism_section(document, number):
    content = [data.get_catechism(document, int(number))]
    return render_daily_page(1, 1, content, static=True)


@app.route('/c/wcf/<regex("[0-9]{1,2}"):chapter>/<regex("[0-9]{1,2}"):paragraph>')
def render_confession_section(chapter, paragraph):
    content = [data.get_confession('wcf', int(chapter), int(paragraph))]
    return render_daily_page(1, 1, content,  static=True)


# Render page for generating facebook/twitter images
@app.route('/i/<regex("[0-1][0-9]"):month>/<regex("[0-9][0-9]"):day>')
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
