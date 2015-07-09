#!/usr/bin/env python

# http://flask.pocoo.org/docs/config/#development-production

class Config(object):
    SECRET_KEY = 'RZ2fEn3kjVf3kbFciDkHW5kJEHIY1hVzcsx3FgJ8eHBUrBP0HN'
    SITE_NAME = 'example.com'
    MEMCACHED_SERVERS = ['localhost:11211']
    SYS_ADMINS = ['foo@example.com']

class ProductionConfig(Config):
    DEBUG = False

class DevelopmentConfig(Config):
    '''Use "if app.debug" anywhere in your code, that code will run in development code.'''
    DEBUG = True
