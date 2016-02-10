import datetime as dt
import simplejson as json
import os
import pytz
import re

from collections import OrderedDict

from metadata import plan as _plan
from metadata import plan_titles as _plan_titles


catechism_names = {
    "wcf": "Confession of Faith",
    "wlc": "Larger Catechism",
    "wsc": "Shorter Catechism",
}


docs = {}
root_path = os.path.dirname(os.path.realpath(__file__))
doc_path = "static/confessions/{}.json"
with open(os.path.join(root_path, doc_path.format("wcf")), "r") as f:
    docs["wcf"] = json.load(f, object_pairs_hook=OrderedDict)
with open(os.path.join(root_path, doc_path.format("wsc")), "r") as f:
    docs["wsc"] = json.load(f, object_pairs_hook=OrderedDict)
with open(os.path.join(root_path, doc_path.format("wlc")), "r") as f:
    docs["wlc"] = json.load(f, object_pairs_hook=OrderedDict)


def get(name, *args, **kwargs):
    if name.lower() == "wcf":
        return get_confession(name.lower(), *args, **kwargs)
    else:
        return get_catechism(name.lower(), *args, **kwargs)


def _convert_footnotes(name, body, prooftexts=True):
    pattern = r"<span data-prooftexts='.*?' data-prooftexts-index='([0-9]+)'>(.*?)</span>"
    global match_index
    match_index = 0

    def sub(m):
        global match_index
        match_index += 1
        return "{two}<sup id='fnref:{name}{one}'><a href='#fn:{name}{one}' rel='footnote' style='text-decoration: none;'>{one}</a></sup>".format(name=name, one=match_index, two=m.group(2))
    if prooftexts:
        return re.sub(pattern,
                      sub,
                      body)
    else:
        return re.sub(pattern, r"\2", body, count=1000)


def _get_prooftexts(body, prooftexts=True):
    if not prooftexts:
        return []
    return re.findall(r"<span data-prooftexts='.*?' data-prooftexts-index='([0-9]+)'>",
                      body)


def get_confession(name, chapter, section, prooftexts=True):
    chapter = str(chapter)
    section = str(section)
    try:
        return {
            "type": "confession",
            "abbv": name,
            "name": catechism_names[name],
            "section_title": "",
            "chapter": chapter,
            "paragraph": section,
            "title": docs["wcf"][chapter]['title'],
            "citation": "{} {}.{}".format(name.upper(), chapter, section),
            "long_citation": "{} {}.{}".format(catechism_names[name], chapter, section),
            "body": _convert_footnotes(name, docs["wcf"][chapter]['body'][section], prooftexts),
            "prooftexts": {i: docs['wcf'][chapter]['prooftext_verses'][pt]
                           for i, pt in enumerate(_get_prooftexts(docs['wcf'][chapter]['body'][section], prooftexts), 1)}
        }
    except KeyError:
        raise KeyError("Cannot find data for {} {}.{}.".format(name.upper(), chapter, section))


def get_catechism(name, question, prooftexts=True):
    question = str(question)
    catechism = docs[name]
    return {
        "type": "catechism",
        "abbv": name,
        "name": catechism_names[name],
        "section_title": "",
        "citation": "{} {}".format(name.upper(), question),
        "long_citation": "{} {}".format(catechism_names[name], question),
        "number": question,
        "question": catechism[question]["question"],
        "answer": _convert_footnotes(name, catechism[question]["answer"], prooftexts),
        "prooftexts": {i: catechism[question]['prooftext_verses'][pt]
                       for i, pt in enumerate(_get_prooftexts(catechism[question]['answer'], prooftexts), 1)}
    }


def get_day_title(month, day):
    return _plan_titles[_get_day_of_year(month, day)]


def _get_day_of_year(month, day):
    return (dt.datetime(2004, int(month), int(day)) - dt.datetime(2004, 1, 1)).days


def get_day(month, day, prooftexts=True):
    try:
        day_of_year = _get_day_of_year(month, day)
    except:
        raise KeyError("Error parsing date (month: {} day: {}).".format(month, day))
    refs = _plan[day_of_year]
    return [get(*ref, prooftexts=prooftexts) for ref in refs]


def get_today_content(tz='UTC', prooftexts=True):
    tz = pytz.timezone(tz)
    month = dt.datetime.now(tz=tz).month
    day = dt.datetime.now(tz=tz).day
    return month, day, get_day(month, day, prooftexts)
