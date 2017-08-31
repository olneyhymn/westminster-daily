#!/usr/bin/env python

# http://flask.pocoo.org/docs/config/#development-production
from __future__ import absolute_import

class Config(object):
    SITE_TITLE = "Westminster Daily"
    SITE_TAGLINE = "Read the Westminster Standards in a year."
    TZ = 'US/Eastern'
    SECRET_KEY = ''
    SITE_NAME = 'reformedconfessions.com'
    MEMCACHED_SERVERS = ['localhost:11211']
    SYS_ADMINS = ['feedback@reformedconfessions.com']


class ProductionConfig(Config):
    DEBUG = False


class DevelopmentConfig(Config):
    '''Use "if app.debug" anywhere in your code, that code will run in development code.'''
    DEBUG = True
