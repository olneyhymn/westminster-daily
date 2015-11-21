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

from flask_application.data import get_today_content

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


@task
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
    ''' '''
    server = sh.python('runserver.py', _bg=True)
    print "starting server with pid {}".format(server.pid)
    for date in (dt.datetime(2004, int(month), 01) + dt.timedelta(n) for n in range(31)):
        webkit2png = sh.Command("/usr/local/bin/webkit2png")
        p = webkit2png(date.strftime('http://0.0.0.0:8080/i/%m/%d'),
                       selector="#content",
                       filename=date.strftime('%m%d'),
                       fullsize=True,
                       dir="flask_application/static/images/docs/",
                       )
        print p.ran
        print "stdout: ", p.stdout
        print "stderr: ", p.stderr


@task
def clean():
    '''Clear the cached .pyc files.'''
    local("find . \( -iname '*.pyc' -o -name '*~' \) -exec rm -v {} \;", capture=False)
    local("rm -rf htmlcov", capture=False)


@task
def get_heroku_config():
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


@task
def update_facebook():
    import facebook
    api = facebook.GraphAPI(os.environ['FB_ACCESS_TOKEN'])

    month, day, content = get_today_content(tz="US/Eastern")
    base_url = "http://reformedconfessions.com/"
    url = "{base}{month:0>2}/{day:0>2}".format(base=base_url, month=month, day=day)
    attachment = {'link': url}

    try:
        status = api.put_wall_post('', attachment=attachment)
        log.info(status)
    except facebook.GraphAPIError as e:
        print e


@task
def tweet():
    '''Send tweet with todays content
    '''
    import twitter as tw
    base_url = "http://reformedconfessions.com/"
    cred = {
        "consumer_key": os.environ['TW_CONSUMER_KEY'],
        "consumer_secret": os.environ['TW_CONSUMER_SECRET'],
        "token": os.environ['TW_TOKEN'],
        "token_secret": os.environ['TW_TOKEN_SECRET'],
    }
    auth = tw.OAuth(**cred)
    t = tw.Twitter(auth=auth)

    month, day, content = get_today_content(tz="US/Eastern")
    description = ", ".join(c['long_citation'] for c in content)
    url = "{base}{month:0>2}/{day:0>2}".format(base=base_url, month=month, day=day)

    try:
        # Attempt tweet
        t.statuses.update(status="{}: {} {}".format(APP_NAME, description, url))
    except tw.api.TwitterHTTPError as e:
        if any(error['code'] == 186 for error in e.response_data['errors']):
            # Tweet too long. Try a shorter tweet.
            description = ", ".join(c['citation'] for c in content)
            t.statuses.update(status="Westminster Daily: {} {}".format(description, url))
        else:
            log.error("%s %s", "Unhandled exception", str(e))
        return
    log.info("%s %s", "Tweeted", str(description))
