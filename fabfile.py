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

import os
import sh
import sys
import datetime as dt

from fabric.api import env, local, run, task
from fabric.api import cd
from fabric.colors import red, green, blue

from flask_application.data import get_today_content

APP_NAME = "flask_application"
PROJ_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_NAME = "example.com"

env.hosts = ['user@remotehost']
code_dir = '/path/to/repos/destination'
sys.path.append(PROJ_DIR)

"""
def _transfer_files(src, dst, ssh_port=None):
    ssh_port = ssh_port or 22
    assert os.getenv('SSH_AUTH_SOCK') is not None # Ensure ssh-agent is running
    if not src.endswith('/'):
        src = src + '/'
    if dst.endswith('/'):
        dst = dst[:-1]
    local('rsync -avh --delete-before --copy-unsafe-links -e "ssh -p {0}" {1} {2}'.format(ssh_port, src, dst), capture=False)
"""


@task
def pre_deploy():
    '''Add, commit and push the Git repo before final deployment.'''
    local("git add -p && git commit")
    local("git push")


@task
def deploy():
    global code_dir
    '''Final deployment of the application to Heroku'''
    with cd(code_dir):
        run("git pull")
        run("git push heroku master")


@task
def init(site_name=SITE_NAME):
    '''Call env_setup, env_init, and skeletonize for one-step init'''
    print green(u"Call env_setup, env_init, and skeletonize for one-step init:")
    env_setup()
    env_init(site_name=site_name)
    skeletonize()


@task
def env_init(site_name=SITE_NAME):
    '''Initialize with this site hostname.'''
    print green(u"Initializing new site configuration...")

    #
    # Generate secret key and update config file
    #
    import random
    import string

    CHARS = string.letters + string.digits
    SECRET_KEY = "".join([random.choice(CHARS) for i in range(50)])

    print blue("Configuring the secret key...")
    os.chdir(PROJ_DIR)
    try:
        sh.sed("-i.bak",
               "-e s/SECRET_KEY *= *.*/SECRET_KEY = '{0}'/g".format(SECRET_KEY),
               "{0}/config.py".format(APP_NAME))
        sh.rm(f="config.py.bak")
    except sh.ErrorReturnCode:
        print red("Could not configure SECRET_KEY for config.py")
        exit(1)

    #
    # Set the site name, the user defined site hostname
    #
    print blue("Configuring the SITE_NAME '{0}'.".format(site_name))
    try:
        sh.sed("-i.bak",
               "-es/SITE_NAME\s*=\s*.*/SITE_NAME = '{0}'/g".format(site_name),
               "{0}/config.py".format(APP_NAME))
        sh.rm(f="config.py.bak")
    except sh.ErrorReturnCode:
        print red("Could not configure SITE_NAME for config.py")
        exit(1)


@task
def env_setup():
    '''Initialize environment with requisite Python modules.'''
    print green("Installing requisite modules...")

    # Install our requistite modules for the website.
    sh.pip("install", r="requirements.txt")

    import platform
    if platform.python_version_tuple() < (2, 7):
        sh.pip("install", "unittest2")


@task
def skeletonize():
    '''Update Skeleton HTML5-Boilerplate.'''
    print green("Skeletonizing the project directory...")

    # Skeleton
    print blue("Installing skeleton HTML5 Boilerplate.")
    os.chdir(PROJ_DIR)
    sh.git.submodule.update(init=True)

    os.chdir(PROJ_DIR + "/skeleton")
    # sh.git.pull("origin", "master")
    sh.rsync("-av", "images", "{0}/{1}/static/".format(PROJ_DIR, APP_NAME))
    sh.rsync("-av", "stylesheets", "{0}/{1}/static/".format(PROJ_DIR, APP_NAME))
    sh.rsync("-av", "index.html", "{0}/{1}/templates/base_t.html".format(PROJ_DIR, APP_NAME))
    os.chdir(PROJ_DIR)

    # Patch the base template with templating tags
    print blue("Patching the base template.")
    os.chdir(PROJ_DIR + "/{0}/templates/".format(APP_NAME))
    template_patch = open("base_t.patch".format(APP_NAME))
    sh.patch(strip=0, _in=template_patch)
    template_patch.close()
    os.chdir(PROJ_DIR)

    # Jquery
    print blue("Installing jquery 1.9.0.")
    os.chdir(PROJ_DIR + "/" + APP_NAME + "/static/js")
    sh.curl("http://code.jquery.com/jquery-1.9.0.min.js", O=True)
    os.chdir(PROJ_DIR)


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
    local('env TEST=yes python tests.py', capture=False)


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
"""
@task
def server_setup():
    '''Setup the server environment.'''
    global SITE_NAME

    local_dir = os.getcwd()
    remote_dir = os.path.join('/home', os.getlogin(), 'web', SITE_NAME, 'private', SITE_NAME)
    run('mkdir -p {0}'.format(remote_dir))
    _transfer_files(local_dir, env.host + ':' + remote_dir, ssh_port=env.port)
    run('cd {0} && bash setup/server_setup.bash {1}'.format(remote_dir, SITE_NAME))
"""


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
def tweet():
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

    month, day, content = get_today_content()
    description = ", ".join(c['long_citation'] for c in content)
    url = "{base}{month:0>2}/{day:0>2}".format(base=base_url, month=month, day=day)

    try:
        # Attempt tweet
        t.statuses.update(status="Westminster Daily: {} {}".format(description, url))
    except tw.api.TwitterHTTPError as e:
        if any(error['code'] == 186 for error in e.response_data['errors']):
            # Tweet too long. Try a shorter tweet.
            description = ", ".join(c['citation'] for c in content)
            t.statuses.update(status="Westminster Daily: {} {}".format(description, url))
        else:
            print "Unhandled exception", e
        return
    print "Tweeted", description
