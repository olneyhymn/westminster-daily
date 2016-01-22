#!env python
import sys
from pprint import pprint


def show(obj):
    '''Show the dump of the properties of the object.'''
    pprint(vars(obj))


if sys.flags.interactive:
    from flask_application import *
    print 'Loading Flask App in console mode. Use show(<obj)> to introspect.'
elif __name__ == '__main__':
    from flask_application import app
    app.run(host = "127.0.0.1", port = 8080)
