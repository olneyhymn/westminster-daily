import datetime as dt
import simplejson as json
import os
import pytz
import re

from collections import OrderedDict


catechisms = {
    "wcf": "Confession of Faith",
    "wlc": "Larger Catechism",
    "wsc": "Shorter Catechism",
}


def get(name, *args, **kwargs):
    if name.lower() == "wcf":
        return get_confession(name.lower(), *args, **kwargs)
    else:
        return get_catechism(name.lower(), *args)


def _convert_footnotes(body, prooftexts=True):
    pattern = r"<span data-prooftexts='.*?' data-prooftexts-index='([0-9]+)'>(.*?)</span>"
    if prooftexts:
        return re.sub(pattern,
                      r"\2<sup id='fnref:\1'><a href='#fn:\1' rel='footnote'>\1</a></sup>",
                      body, count=1000)
    else:
        return re.sub(pattern, r"\2", body, count=1000)


def _get_prooftexts(body):
    return re.findall(r"<span data-prooftexts='.*?' data-prooftexts-index='([0-9]+)'>",
                      body)


def get_confession(name, chapter, section, prooftexts=True):
    chapter = str(chapter)
    section = str(section)
    root_path = os.path.dirname(os.path.realpath(__file__))
    json_path = os.path.join(root_path, "static/confessions/{}.json".format("wcf"))
    try:
        with open(json_path, "r") as f:
            wcf = json.load(f, object_pairs_hook=OrderedDict)
        return {
            "type": "confession",
            "abbv": name,
            "name": catechisms[name],
            "section_title": "",
            "chapter": chapter,
            "paragraph": section,
            "citation": "{} {}.{}".format(name.upper(), chapter, section),
            "long_citation": "{} {}.{}".format(catechisms[name], chapter, section),
            "body": _convert_footnotes(wcf[chapter]['body'][section], prooftexts),
            "prooftexts": {pt: wcf[chapter]['prooftexts'][pt]
                           for pt in _get_prooftexts(wcf[chapter]['body'][section])}
        }
    except KeyError:
        raise KeyError("Cannot find data for {} {}.{}.".format(name.upper(), chapter, section))


def get_catechism(name, question):
    question = str(question)
    root_path = os.path.dirname(os.path.realpath(__file__))
    json_path = os.path.join(root_path, "static/confessions/{}.json".format(name))
    try:
        with open(json_path, "r") as f:
            catechism = json.load(f, object_pairs_hook=OrderedDict)
        return {
            "type": "catechism",
            "abbv": name,
            "name": catechisms[name],
            "section_title": "",
            "citation": "{} {}".format(name.upper(), question),
            "long_citation": "{} {}".format(catechisms[name], question),
            "number": question,
            "question": catechism[question]["question"],
            "answer": catechism[question]["answer"],
        }
    except:
        raise KeyError("Cannot find data for {} {}.".format(name.upper(), question))


_plan = ([('WSC', 1), ('WLC', 1)], [('WCF', 1, 1)], [('WLC', 2)], [('WCF', 1, 2)],
         [('WSC', 2), ('WLC', 3)], [('WCF', 1, 3)], [('WCF', 1, 4)], [('WCF', 1, 5)],
         [('WLC', 4)], [('WCF', 1, 6)], [('WCF', 1, 7)], [('WCF', 1, 8)], [('WCF', 1, 9)],
         [('WCF', 1, 10)], [('WSC', 3), ('WLC', 5)], [('WLC', 6)], [('WCF', 2, 1)],
         [('WSC', 4), ('WLC', 7)], [('WSC', 5), ('WLC', 8)], [('WCF', 2, 2)],
         [('WCF', 2, 3)], [('WSC', 6), ('WLC', 9)], [('WLC', 10)], [('WLC', 11)],
         [('WCF', 3, 1)], [('WSC', 7), ('WLC', 12)], [('WCF', 3, 2)], [('WCF', 3, 3)],
         [('WLC', 13)], [('WCF', 3, 4)], [('WCF', 3, 5)], [('WCF', 3, 6)], [('WCF', 3, 7)],
         [('WCF', 3, 8)], [('WSC', 8), ('WLC', 14)], [('WCF', 4, 1)], [('WSC', 9), ('WLC', 15)],
         [('WLC', 16)], [('WCF', 4, 2)], [('WSC', 10), ('WLC', 17)], [('WCF', 5, 1)],
         [('WSC', 11), ('WLC', 18)], [('WCF', 5, 2)], [('WCF', 5, 3)], [('WCF', 5, 4)],
         [('WLC', 19)], [('WCF', 5, 5)], [('WCF', 5, 6)], [('WCF', 5, 7)], [('WCF', 6, 1)],
         [('WSC', 13), ('WLC', 21)], [('WSC', 14), ('WLC', 24)], [('WSC', 15)],
         [('WCF', 6, 2)], [('WCF', 6, 3)], [('WSC', 16), ('WLC', 22)], [('WSC', 17), ('WLC', 23)],
         [('WCF', 6, 4)], [('WSC', 18), ('WLC', 25)], [('WSC', 18), ('WLC', 25)], [('WCF', 6, 5)], [('WLC', 26)],
         [('WCF', 6, 6)], [('WSC', 19), ('WLC', 27)], [('WLC', 28)], [('WLC', 29)],
         [('WCF', 7, 1)], [('WSC', 12), ('WLC', 20)], [('WCF', 7, 2)], [('WCF', 7, 3)],
         [('WSC', 20), ('WLC', 30)], [('WLC', 31)], [('WLC', 32)], [('WCF', 7, 4)],
         [('WCF', 7, 5)], [('WLC', 33)], [('WLC', 34)], [('WCF', 7, 6)], [('WLC', 35)],
         [('WCF', 8, 1)], [('WCF', 8, 2)], [('WSC', 21), ('WLC', 26)], [('WSC', 22), ('WLC', 37)],
         [('WLC', 38)], [('WLC', 39)], [('WLC', 40)], [('WLC', 41)], [('WCF', 8, 3)],
         [('WSC', 23), ('WLC', 42)], [('WSC', 24), ('WLC', 43)], [('WCF', 8, 4)],
         [('WCF', 8, 5)], [('WSC', 25), ('WLC', 44)], [('WSC', 26), ('WLC', 45)],
         [('WSC', 27), ('WLC', 46)], [('WLC', 47)], [('WLC', 48)], [('WLC', 49)],
         [('WLC', 50)], [('WSC', 28), ('WLC', 51)], [('WLC', 52)], [('WLC', 53)],
         [('WLC', 54)], [('WLC', 55)], [('WLC', 56)], [('WCF', 8, 6)], [('WCF', 8, 7)],
         [('WCF', 8, 8)], [('WLC', 57)], [('WCF', 9, 1)], [('WCF', 9, 2)], [('WCF', 9, 3)],
         [('WCF', 9, 4)], [('WCF', 9, 5)], [('WLC', 57)], [('WSC', 29), ('WLC', 58)],
         [('WSC', 30), ('WLC', 59)], [('WCF', 10, 1)], [('WSC', 31), ('WLC', 67)],
         [('WLC', 68)], [('WCF', 10, 2)], [('WCF', 10, 3)], [('WCF', 10, 4)],
         [('WLC', 60)], [('WSC', 32)], [('WCF', 11, 1)], [('WSC', 33), ('WLC', 70)],
         [('WCF', 11, 2)], [('WCF', 11, 3)], [('WLC', 71)], [('WCF', 11, 4)],
         [('WCF', 11, 5)], [('WCF', 11, 6)], [('WCF', 12, 1)], [('WSC', 34), ('WLC', 74)],
         [('WCF', 13, 1)], [('WSC', 35), ('WLC', 75)], [('WCF', 13, 2), ('WLC', 78)],
         [('WCF', 13, 3)], [('WLC', 77)], [('WSC', 36)], [('WSC', 85), ('WLC', 153)],
         [('WCF', 14, 1)], [('WSC', 86), ('WLC', 72)], [('WCF', 14, 2)], [('WLC', 73)],
         [('WCF', 14, 3)], [('WCF', 15, 1)], [('WCF', 15, 2)], [('WSC', 87), ('WLC', 76)],
         [('WCF', 15, 3)], [('WCF', 15, 4)], [('WCF', 15, 5)], [('WCF', 15, 6)],
         [('WCF', 16, 1)], [('WCF', 16, 2)], [('WCF', 16, 3)], [('WCF', 16, 4)],
         [('WCF', 16, 5)], [('WCF', 16, 6)], [('WCF', 16, 7)], [('WCF', 17, 1)],
         [('WLC', 79)], [('WCF', 17, 2)], [('WCF', 17, 3)], [('WCF', 18, 1)],
         [('WLC', 80)], [('WCF', 18, 2)], [('WCF', 18, 3)], [('WLC', 81)], [('WCF', 18, 4)],
         [('WSC', 39), ('WLC', 91)], [('WCF', 19, 1)], [('WSC', 40), ('WLC', 92)],
         [('WLC', 93)], [('WCF', 19, 2)], [('WSC', 41), ('WLC', 98)], [('WCF', 19, 3)],
         [('WCF', 19, 4)], [('WCF', 19, 5)], [('WLC', 94)], [('WLC', 95)], [('WLC', 96)],
         [('WCF', 19, 6)], [('WLC', 97)], [('WCF', 19, 7)], [('WLC', 99)], [('WLC', 100)],
         [('WLC', 101)], [('WSC', 43)], [('WSC', 44)], [('WSC', 42), ('WLC', 102)],
         [('WSC', 45), ('WLC', 103)], [('WSC', 46), ('WLC', 104)], [('WSC', 47), ('WLC', 105)],
         [('WSC', 48), ('WLC', 106)], [('WSC', 49), ('WLC', 107)], [('WSC', 50), ('WLC', 108)],
         [('WSC', 51), ('WLC', 109)], [('WSC', 52), ('WLC', 110)], [('WSC', 53), ('WLC', 111)],
         [('WSC', 54), ('WLC', 112)], [('WSC', 55), ('WLC', 113)], [('WSC', 56), ('WLC', 114)],
         [('WSC', 57), ('WLC', 115)], [('WSC', 58), ('WLC', 116)], [('WSC', 59)],
         [('WSC', 60), ('WLC', 117)], [('WLC', 118)], [('WSC', 61), ('WLC', 119)],
         [('WSC', 62), ('WLC', 120)], [('WLC', 121)], [('WSC', 42), ('WLC', 122)],
         [('WSC', 63), ('WLC', 123)], [('WLC', 124)], [('WLC', 125)], [('WSC', 64), ('WLC', 126)],
         [('WLC', 127)], [('WSC', 65), ('WLC', 128)], [('WLC', 129)], [('WLC', 130)],
         [('WLC', 131)], [('WLC', 132)], [('WSC', 66), ('WLC', 133)], [('WSC', 67), ('WLC', 134)],
         [('WSC', 68), ('WLC', 135)], [('WSC', 69), ('WLC', 136)], [('WSC', 70), ('WLC', 137)],
         [('WSC', 71), ('WLC', 138)], [('WSC', 72), ('WLC', 139)], [('WSC', 73), ('WLC', 140)],
         [('WSC', 74), ('WLC', 141)], [('WSC', 75), ('WLC', 142)], [('WSC', 76), ('WLC', 143)],
         [('WSC', 77), ('WLC', 144)], [('WSC', 78), ('WLC', 145)], [('WSC', 79), ('WLC', 146)],
         [('WSC', 80), ('WLC', 147)], [('WSC', 81), ('WLC', 148)], [('WSC', 82), ('WLC', 149)],
         [('WSC', 83), ('WLC', 150)], [('WLC', 151)], [('WSC', 84), ('WLC', 152)],
         [('WCF', 20, 1)], [('WCF', 20, 2)], [('WCF', 20, 3)], [('WCF', 20, 4)],
         [('WCF', 21, 1)], [('WCF', 21, 2)], [('WCF', 21, 3), ('WLC', 185)],
         [('WSC', 98), ('WLC', 178)], [('WLC', 179)], [('WLC', 180)], [('WLC', 181)],
         [('WLC', 182)], [('WCF', 21, 4)], [('WLC', 183)], [('WLC', 184)], [('WCF', 21, 5)],
         [('WCF', 21, 6)], [('WCF', 21, 7)], [('WSC', 59), ('WLC', 116)], [('WCF', 21, 8)],
         [('WSC', 60), ('WLC', 117)], [('WSC', 99), ('WLC', 186)], [('WLC', 187)],
         [('WLC', 188)], [('WSC', 100), ('WLC', 189)], [('WSC', 101), ('WLC', 190)],
         [('WSC', 102), ('WLC', 191)], [('WSC', 103), ('WLC', 192)], [('WSC', 104), ('WLC', 193)],
         [('WSC', 105), ('WLC', 194)], [('WSC', 106), ('WLC', 195)], [('WSC', 107), ('WLC', 196)],
         [('WCF', 22, 1)], [('WCF', 22, 2)], [('WCF', 22, 3)], [('WCF', 22, 4)],
         [('WCF', 22, 5)], [('WCF', 22, 6)], [('WCF', 22, 7)], [('WCF', 23, 1)],
         [('WCF', 23, 2)], [('WCF', 23, 3)], [('WCF', 23, 4)], [('WCF', 24, 1)],
         [('WCF', 24, 2)], [('WCF', 24, 3)], [('WCF', 24, 4)], [('WCF', 24, 5)],
         [('WCF', 24, 6)], [('WCF', 25, 1), ('WLC', 64)], [('WLC', 65)], [('WCF', 25, 2), ('WLC', 62)],
         [('WCF', 25, 3), ('WLC', 63)], [('WCF', 25, 4)], [('WCF', 25, 5), ('WLC', 61)],
         [('WCF', 25, 6)], [('WCF', 26, 1), ('WLC', 66)], [('WCF', 26, 2)],
         [('WCF', 26, 3)], [('WLC', 69)], [('WLC', 82)], [('WSC', 36), ('WLC', 83)],
         [('WSC', 37), ('WLC', 86)], [('WSC', 38), ('WLC', 90)], [('WSC', 85), ('WLC', 153)],
         [('WSC', 88), ('WLC', 154)], [('WSC', 89), ('WLC', 155)], [('WLC', 156)],
         [('WSC', 90), ('WLC', 157)], [('WLC', 158)], [('WLC', 159)], [('WLC', 160)],
         [('WCF', 27, 1)], [('WSC', 92), ('WLC', 162)], [('WCF', 27, 2), ('WLC', 163)],
         [('WCF', 27, 3)], [('WLC', 161), ('WSC', 91)], [('WCF', 27, 4)], [('WSC', 93), ('WLC', 164)],
         [('WCF', 27, 5)], [('WCF', 28, 1)], [('WSC', 94), ('WLC', 165)], [('WCF', 28, 2)],
         [('WCF', 28, 3)], [('WCF', 28, 4)], [('WSC', 95), ('WLC', 166)], [('WCF', 28, 5)],
         [('WCF', 28, 6)], [('WCF', 28, 7)], [('WLC', 167)], [('WCF', 29, 1)],
         [('WSC', 96), ('WLC', 168)], [('WCF', 29, 2)], [('WCF', 29, 3), ('WLC', 169)],
         [('WCF', 29, 4)], [('WCF', 29, 5)], [('WCF', 29, 6)], [('WCF', 29, 7), ('WLC', 170)],
         [('WCF', 29, 8)], [('WSC', 97), ('WLC', 171)], [('WLC', 172)], [('WLC', 173)],
         [('WLC', 174)], [('WLC', 175)], [('WLC', 176)], [('WLC', 177)], [('WCF', 30, 1)],
         [('WCF', 30, 2)], [('WCF', 30, 3)], [('WCF', 30, 4)], [('WCF', 31, 1)],
         [('WCF', 31, 2)], [('WCF', 31, 3)], [('WCF', 31, 4)], [('WLC', 84)],
         [('WCF', 32, 1)], [('WSC', 37), ('WLC', 85)], [('WCF', 32, 2), ('WLC', 87)],
         [('WCF', 32, 3)], [('WCF', 33, 1), ('WLC', 88)], [('WCF', 33, 2), ('WLC', 89)],
         [('WSC', 38), ('WLC', 90)], [('WCF', 33, 3)])


def get_day(month, day, prooftexts=True):
    try:
        day_of_year = (dt.datetime(2004, int(month), int(day)) - dt.datetime(2004, 1, 1)).days
    except:
        raise KeyError("Error parsing date (month: {} day: {}).".format(month, day))
    refs = _plan[day_of_year]
    # return refs
    return [get(*ref, prooftexts=prooftexts) for ref in refs]


def get_today_content(tz='UTC', prooftexts=True):
    tz = pytz.timezone(tz)
    month = dt.datetime.now(tz=tz).month
    day = dt.datetime.now(tz=tz).day
    return month, day, get_day(month, day, prooftexts)
