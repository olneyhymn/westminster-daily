#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Run 'fab --list' to see list of available commands.

References:
# http://docs.fabfile.org/en/1.0.1/usage/execution.html#how-host-lists-are-constructed
'''

from __future__ import with_statement
import platform
assert ('2', '6') <= platform.python_version_tuple() < ('3', '0')

import logging
import os
import sh
import sys
import datetime as dt

from fabric.api import local, task

from flask_application.data import get_today_content, get_day_title

APP_NAME = "Westminster Daily"
PROJ_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_NAME = "reformedconfessions.com"

sys.path.append(PROJ_DIR)

log = logging.getLogger()
log.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
log.addHandler(ch)


@task
def console():
    '''Load the application in an interactive console.'''
    local('env DEV=yes python -i runserver.py', capture=False)


@task(alias='preview')
def server():
    '''Run the dev server'''
    os.chdir(PROJ_DIR)
    local('env DEV=yes python runserver.py', capture=False)


@task
def test():
    '''Run the test suite'''
    local('py.test --verbose   --full-trace', capture=False)


@task
def build_images(month):

    image_path = 'flask_application/static/images/docs/'
    server = sh.python('runserver.py', _bg=True)
    print "starting server with pid {}".format(server.pid)
    for date in (dt.datetime(2004, int(month), 01) + dt.timedelta(n) for n in range(31)):
        webkit2png = sh.Command("/usr/local/bin/webkit2png")
        p = webkit2png(date.strftime('http://0.0.0.0:8080/i/%m/%d'),
                       selector="#content",
                       filename=date.strftime('%m%d'),
                       fullsize=True,
                       dir=image_path,
                       **{"ignore-ssl-check": True}
                       )
        print p.ran
        pngquant = sh.Command('/usr/local/bin/pngquant')
        pngquant("--force",
                 "--ext", ".png",
                 "--quality", "65-80",
                 "{}{}-full.png".format(image_path, date.strftime('%m%d')))


@task
def clean():
    '''Clear the cached .pyc files.'''
    local("find . \( -iname '*.pyc' -o -name '*~' \) -exec rm -v {} \;", capture=False)
    local("rm -rf htmlcov", capture=False)


@task
def get_heroku_config():
    """Get commands for updating heroku environmental variables
    """
    print "heroku config:set", "{}={}".format("FB_ACCESS_TOKEN", os.environ['FB_ACCESS_TOKEN'])
    print "heroku config:set", "{}={}".format("TW_CONSUMER_KEY", os.environ['TW_CONSUMER_KEY'])
    print "heroku config:set", "{}={}".format("TW_CONSUMER_SECRET", os.environ['TW_CONSUMER_SECRET'])
    print "heroku config:set", "{}={}".format("TW_TOKEN", os.environ['TW_TOKEN'])
    print "heroku config:set", "{}={}".format("TW_TOKEN_SECRET", os.environ['TW_TOKEN_SECRET'])


@task
def configure_tweet():
    '''Tweet today's confession post
    '''
    import twitter as tw

    cred = {
        "consumer_key": os.environ['TW_CONSUMER_KEY'],
        "consumer_secret": os.environ['TW_CONSUMER_SECRET'],
        "app_name": "Reformed Confessions"
    }
    oauth_token, oauth_token_secret = tw.oauth_dance(**cred)
    print "oauth_token", oauth_token
    print "oauth_token_secret", oauth_token_secret


def make_facebook_string(content):
    c_strings = []
    for c in content:
        if c['type'] == 'confession':
            c_strings.append("""{}

{}

""".format(c['long_citation'], c['body']))
        elif c['type'] == 'catechism':
            c_strings.append("""{}

Q. {}
A. {}

""".format(c['long_citation'], c['question'], c['answer']))
    return ''.join(c_strings)


@task
def update_facebook():
    import facebook
    api = facebook.GraphAPI(os.environ['FB_ACCESS_TOKEN'])

    month, day, content = get_today_content(tz="US/Eastern", prooftexts=False)
    base_url = "http://reformedconfessions.com/westminster-daily/"
    url = "{base}{month:0>2}/{day:0>2}".format(base=base_url, month=month, day=day)
    attachment = {'link': url}

    content = make_facebook_string(content)

    if (month, day) in [(1, 4), (7, 5)]:
        content = "" # Days have html formatting

    try:
        status = api.put_wall_post(content, attachment=attachment)
        log.info(status)
    except facebook.GraphAPIError as e:
        print e


@task
def tweet():
    '''Send tweet with todays content
    '''
    import twitter as tw
    base_url = "http://reformedconfessions.com/westminster-daily/"
    cred = {
        "consumer_key": os.environ['TW_CONSUMER_KEY'],
        "consumer_secret": os.environ['TW_CONSUMER_SECRET'],
        "token": os.environ['TW_TOKEN'],
        "token_secret": os.environ['TW_TOKEN_SECRET'],
    }
    auth = tw.OAuth(**cred)
    t = tw.Twitter(auth=auth)

    month, day, content = get_today_content(tz="US/Eastern")
    description = get_day_title(month, day)
    url = "{base}{month:0>2}/{day:0>2}".format(base=base_url, month=month, day=day)

    try:
        # Attempt tweet
        with open("flask_application/static/images/docs/{:0>2}{:0>2}-full.png".format(month, day), "rb") as imagefile:
            imagedata = imagefile.read()
        t_up = tw.Twitter(domain='upload.twitter.com', auth=auth)
        id_img1 = t_up.media.upload(media=imagedata)["media_id_string"]
        t.statuses.update(status="{} {}".format(description, url),
                          media_ids=id_img1)
    except tw.api.TwitterHTTPError as e:
        if any(error['code'] == 186 for error in e.response_data['errors']):
            # Tweet too long. Try a shorter tweet.
            description = ", ".join(c['citation'] for c in content)
            t.statuses.update(status="{} {}".format(description, url))
        else:
            log.error("%s %s", "Unhandled exception", str(e))
        return
    log.info("%s %s", "Tweeted", str(description))
