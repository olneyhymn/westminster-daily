#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Run 'fab --list' to see list of available commands.

References:
# http://docs.fabfile.org/en/1.0.1/usage/execution.html#how-host-lists-are-constructed
"""

from __future__ import with_statement
import platform
assert ('2', '6') <= platform.python_version_tuple() < ('3', '0')

import time
import logging
import os
import sh
import sys
import datetime as dt


from fabric.api import local, task

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
def build_images(month):

    image_path = 'flask_application/static/images/docs/'
    server = sh.python('runserver.py', _bg=True)
    print "starting server with pid {}".format(server.pid)
    time.sleep(5)
    for date in (dt.datetime(2004, int(month), 01) + dt.timedelta(n) for n in range(1)):
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
def images_to_s3():
    local('s3cmd put --acl-public images/* s3://reformedconfessions')


@task
def catechism_to_yaml(name="wlc"):
    """Generate YAML file for catechism
    """
    import re
    import json
    import yaml

    with open('./flask_application/static/confessions/{}.json'.format(name), 'r') as f:
        catechism = json.load(f, object_hook=ascii_encode_dict)

    for k, v in catechism.items():
        del v['prooftext_verses']

    catechism2 = {}
    for k, v in catechism.items():
        catechism2[int(k)] = v
        for pk in list(v['prooftexts'].keys()):
            v['prooftexts'][int(pk)] = v['prooftexts'][pk]
            del v['prooftexts'][(pk)]
        a = v['answer']
        pattern = r"<span data-prooftexts='.*?' data-prooftexts-index='([0-9]+)'>(.*?)</span>"
        v['answer'] = re.sub(pattern, r"\2[\1]", a)

        #
        v['1question'] = v['question']
        v['2answer'] = v['answer']
        v['3prooftexts'] = v['prooftexts']
        del v['question']
        del v['answer']
        del v['prooftexts']

    print (yaml.dump(catechism2, default_flow_style=False, width=120)
               .replace("1question", "Q")
               .replace("2answer", "A")
               .replace("3prooftexts", "proofs")
           )


@task
def confession_to_yaml():
    """Generate YAML file for WCF"""
    import re
    import json
    import yaml

    with open('../westminster-daily/flask_application/static/confessions/wcf.json', 'r') as f:
        catechism = json.load(f, object_hook=ascii_encode_dict)

    for k, v in catechism.items():
        del v['prooftext_verses']

    catechism2 = {}
    for k, v in catechism.items():
        catechism2[int(k)] = v
        for pk in list(v['prooftexts'].keys()):
            v['prooftexts'][int(pk)] = v['prooftexts'][pk]
            del v['prooftexts'][(pk)]
        body = {int(k): v for k, v in v['body'].items()}
        for k2, v2 in body.items():
            pattern = r"<span data-prooftexts='.*?' data-prooftexts-index='([0-9]+)'>(.*?)</span>"

            body[k2] = re.sub(pattern, r"\2[\1]", v2)

        #
        v['body'] = body
        v['1title'] = v['title']
        del v['title']

    print (yaml.dump(catechism2, default_flow_style=False, width=120)
               .replace("1title", "title")
           )
