import datetime as dt
import simplejson as json
import os

from collections import namedtuple, OrderedDict


catechisms = {
    "wcf": "Westminster Confession of Faith",
    "wlc": "Westminster Larger Catechsim",
    "wsc": "Westminster Shorter Catechsim",
}


Excerpt = namedtuple("Excerpt", "abbv doc_title data")


def get(name, *args):
    if name.lower() == "wcf":
        return get_confession(name.lower(), *args)
    else:
        return get_catechism(name.lower(), *args)


def get_confession(name, chapter, section):
    chapter = str(chapter)
    section = str(section)
    root_path = os.path.dirname(os.path.realpath(__file__))
    json_path = os.path.join(root_path, "static/confessions/{}.json".format("wcf"))
    with open(json_path, "r") as f:
        wcf = json.load(f, object_pairs_hook=OrderedDict)
    try:
        return Excerpt("wcf",
                       "Westminster Confession of Faith",
                       {chapter: {section: wcf[chapter]['body'][section]}})
    except:
        print "error!", chapter, section
        raise Exception("Cannot find confession.")


def get_catechism(name, question):
    question = str(question)
    root_path = os.path.dirname(os.path.realpath(__file__))
    json_path = os.path.join(root_path, "static/confessions/{}.json".format(name))
    with open(json_path, "r") as f:
        catechism = json.load(f, object_pairs_hook=OrderedDict)
    try:
        return Excerpt(name,
                       catechisms[name],
                       {question: catechism[question]})
    except:
        raise Exception("Cannot find catechism.")


plan = ([('WLC', 1), ('WSC', 1)], [('WCF', 1, 1)], [('WLC', 2)], [('WCF', 1, 2)],
        [('WLC', 3), ('WSC', 2)], [('WCF', 1, 3)], [('WCF', 1, 4)], [('WCF', 1, 5)],
        [('WLC', 4)], [('WCF', 1, 6)], [('WCF', 1, 7)], [('WCF', 1, 8)], [('WCF', 1, 9)],
        [('WCF', 1, 10)], [('WLC', 5), ('WSC', 3)], [('WLC', 6)], [('WCF', 2, 1)],
        [('WLC', 7), ('WSC', 4)], [('WLC', 8), ('WSC', 5)], [('WCF', 2, 2)],
        [('WCF', 2, 3)], [('WLC', 9), ('WSC', 6)], [('WLC', 10)], [('WLC', 11)],
        [('WCF', 3, 1)], [('WLC', 12), ('WSC', 7)], [('WCF', 3, 2)], [('WCF', 3, 3)],
        [('WLC', 13)], [('WCF', 3, 4)], [('WCF', 3, 5)], [('WCF', 3, 6)], [('WCF', 3, 7)],
        [('WCF', 3, 8)], [('WLC', 14), ('WSC', 8)], [('WCF', 4, 1)], [('WLC', 15), ('WSC', 9)],
        [('WLC', 16)], [('WCF', 4, 2)], [('WLC', 17), ('WSC', 10)], [('WCF', 5, 1)],
        [('WLC', 18), ('WSC', 11)], [('WCF', 5, 2)], [('WCF', 5, 3)], [('WCF', 5, 4)],
        [('WLC', 19)], [('WCF', 5, 5)], [('WCF', 5, 6)], [('WCF', 5, 7)], [('WCF', 6, 1)],
        [('WLC', 21), ('WSC', 13)], [('WLC', 24), ('WSC', 14)], [('WSC', 15)],
        [('WCF', 6, 2)], [('WCF', 6, 3)], [('WLC', 22), ('WSC', 16)], [('WLC', 23), ('WSC', 17)],
        [('WCF', 6, 4)], [('WLC', 25), ('WSC', 18)], [('WLC', 25), ('WSC', 18)], [('WCF', 6, 5)], [('WLC', 26)],
        [('WCF', 6, 6)], [('WLC', 27), ('WSC', 19)], [('WLC', 28)], [('WLC', 29)],
        [('WCF', 7, 1)], [('WLC', 20), ('WSC', 12)], [('WCF', 7, 2)], [('WCF', 7, 3)],
        [('WLC', 30), ('WSC', 20)], [('WLC', 31)], [('WLC', 32)], [('WCF', 7, 4)],
        [('WCF', 7, 5)], [('WLC', 33)], [('WLC', 34)], [('WCF', 7, 6)], [('WLC', 35)],
        [('WCF', 8, 1)], [('WCF', 8, 2)], [('WLC', 26), ('WSC', 21)], [('WLC', 37), ('WSC', 22)],
        [('WLC', 38)], [('WLC', 39)], [('WLC', 40)], [('WLC', 41)], [('WCF', 8, 3)],
        [('WLC', 42), ('WSC', 23)], [('WLC', 43), ('WSC', 24)], [('WCF', 8, 4)],
        [('WCF', 8, 5)], [('WLC', 44), ('WSC', 25)], [('WLC', 45), ('WSC', 26)],
        [('WLC', 46), ('WSC', 27)], [('WLC', 47)], [('WLC', 48)], [('WLC', 49)],
        [('WLC', 50)], [('WLC', 51), ('WSC', 28)], [('WLC', 52)], [('WLC', 53)],
        [('WLC', 54)], [('WLC', 55)], [('WLC', 56)], [('WCF', 8, 6)], [('WCF', 8, 7)],
        [('WCF', 8, 8)], [('WLC', 57)], [('WCF', 9, 1)], [('WCF', 9, 2)], [('WCF', 9, 3)],
        [('WCF', 9, 4)], [('WCF', 9, 5)], [('WLC', 57)], [('WLC', 58), ('WSC', 29)],
        [('WLC', 59), ('WSC', 30)], [('WCF', 10, 1)], [('WLC', 67), ('WSC', 31)],
        [('WLC', 68)], [('WCF', 10, 2)], [('WCF', 10, 3)], [('WCF', 10, 4)],
        [('WLC', 60)], [('WSC', 32)], [('WCF', 11, 1)], [('WLC', 70), ('WSC', 33)],
        [('WCF', 11, 2)], [('WCF', 11, 3)], [('WLC', 71)], [('WCF', 11, 4)],
        [('WCF', 11, 5)], [('WCF', 11, 6)], [('WCF', 12, 1)], [('WLC', 74), ('WSC', 34)],
        [('WCF', 13, 1)], [('WLC', 75), ('WSC', 35)], [('WCF', 13, 2), ('WLC', 78)],
        [('WCF', 13, 3)], [('WLC', 77)], [('WSC', 36)], [('WLC', 153), ('WSC', 85)],
        [('WCF', 14, 1)], [('WLC', 72), ('WSC', 86)], [('WCF', 14, 2)], [('WLC', 73)],
        [('WCF', 14, 3)], [('WCF', 15, 1)], [('WCF', 15, 2)], [('WLC', 76), ('WSC', 87)],
        [('WCF', 15, 3)], [('WCF', 15, 4)], [('WCF', 15, 5)], [('WCF', 15, 6)],
        [('WCF', 16, 1)], [('WCF', 16, 2)], [('WCF', 16, 3)], [('WCF', 16, 4)],
        [('WCF', 16, 5)], [('WCF', 16, 6)], [('WCF', 16, 7)], [('WCF', 17, 1)],
        [('WLC', 79)], [('WCF', 17, 2)], [('WCF', 17, 3)], [('WCF', 18, 1)],
        [('WLC', 80)], [('WCF', 18, 2)], [('WCF', 18, 3)], [('WLC', 81)], [('WCF', 18, 4)],
        [('WLC', 91), ('WSC', 39)], [('WCF', 19, 1)], [('WLC', 92), ('WSC', 40)],
        [('WLC', 93)], [('WCF', 19, 2)], [('WLC', 98), ('WSC', 41)], [('WCF', 19, 3)],
        [('WCF', 19, 4)], [('WCF', 19, 5)], [('WLC', 94)], [('WLC', 95)], [('WLC', 96)],
        [('WCF', 19, 6)], [('WLC', 97)], [('WCF', 19, 7)], [('WLC', 99)], [('WLC', 100)],
        [('WLC', 101)], [('WSC', 43)], [('WSC', 44)], [('WLC', 102), ('WSC', 42)],
        [('WLC', 103), ('WSC', 45)], [('WLC', 104), ('WSC', 46)], [('WLC', 105), ('WSC', 47)],
        [('WLC', 106), ('WSC', 48)], [('WLC', 107), ('WSC', 49)], [('WLC', 108), ('WSC', 50)],
        [('WLC', 109), ('WSC', 51)], [('WLC', 110), ('WSC', 52)], [('WLC', 111), ('WSC', 53)],
        [('WLC', 112), ('WSC', 54)], [('WLC', 113), ('WSC', 55)], [('WLC', 114), ('WSC', 56)],
        [('WLC', 115), ('WSC', 57)], [('WLC', 116), ('WSC', 58)], [('WSC', 59)],
        [('WLC', 117), ('WSC', 60)], [('WLC', 118)], [('WLC', 119), ('WSC', 61)],
        [('WLC', 120), ('WSC', 62)], [('WLC', 121)], [('WLC', 122), ('WSC', 42)],
        [('WLC', 123), ('WSC', 63)], [('WLC', 124)], [('WLC', 125)], [('WLC', 126), ('WSC', 64)],
        [('WLC', 127)], [('WLC', 128), ('WSC', 65)], [('WLC', 129)], [('WLC', 130)],
        [('WLC', 131)], [('WLC', 132)], [('WLC', 133), ('WSC', 66)], [('WLC', 134), ('WSC', 67)],
        [('WLC', 135), ('WSC', 68)], [('WLC', 136), ('WSC', 69)], [('WLC', 137), ('WSC', 70)],
        [('WLC', 138), ('WSC', 71)], [('WLC', 139), ('WSC', 72)], [('WLC', 140), ('WSC', 73)],
        [('WLC', 141), ('WSC', 74)], [('WLC', 142), ('WSC', 75)], [('WLC', 143), ('WSC', 76)],
        [('WLC', 144), ('WSC', 77)], [('WLC', 145), ('WSC', 78)], [('WLC', 146), ('WSC', 79)],
        [('WLC', 147), ('WSC', 80)], [('WLC', 148), ('WSC', 81)], [('WLC', 149), ('WSC', 82)],
        [('WLC', 150), ('WSC', 83)], [('WLC', 151)], [('WLC', 152), ('WSC', 84)],
        [('WCF', 20, 1)], [('WCF', 20, 2)], [('WCF', 20, 3)], [('WCF', 20, 4)],
        [('WCF', 21, 1)], [('WCF', 21, 2)], [('WCF', 21, 3), ('WLC', 185)],
        [('WLC', 178), ('WSC', 98)], [('WLC', 179)], [('WLC', 180)], [('WLC', 181)],
        [('WLC', 182)], [('WCF', 21, 4)], [('WLC', 183)], [('WLC', 184)], [('WCF', 21, 5)],
        [('WCF', 21, 6)], [('WCF', 21, 7)], [('WLC', 116), ('WSC', 59)], [('WCF', 21, 8)],
        [('WLC', 117), ('WSC', 60)], [('WLC', 186), ('WSC', 99)], [('WLC', 187)],
        [('WLC', 188)], [('WLC', 189), ('WSC', 0)], [('WLC', 190), ('WSC', 1)],
        [('WLC', 191), ('WSC', 102)], [('WLC', 192), ('WSC', 103)], [('WLC', 193), ('WSC', 4)],
        [('WLC', 194), ('WSC', 5)], [('WLC', 195), ('WSC', 6)], [('WLC', 196), ('WSC', 107)],
        [('WCF', 22, 1)], [('WCF', 22, 2)], [('WCF', 22, 3)], [('WCF', 22, 4)],
        [('WCF', 22, 5)], [('WCF', 22, 6)], [('WCF', 22, 7)], [('WCF', 23, 1)],
        [('WCF', 23, 2)], [('WCF', 23, 3)], [('WCF', 23, 4)], [('WCF', 24, 1)],
        [('WCF', 24, 2)], [('WCF', 24, 3)], [('WCF', 24, 4)], [('WCF', 24, 5)],
        [('WCF', 24, 6)], [('WCF', 25, 1), ('WLC', 64)], [('WLC', 65)], [('WCF', 25, 2), ('WLC', 62)],
        [('WCF', 25, 3), ('WLC', 63)], [('WCF', 25, 4)], [('WCF', 25, 5), ('WLC', 61)],
        [('WCF', 25, 6)], [('WCF', 26, 1), ('WLC', 66)], [('WCF', 26, 2)],
        [('WCF', 26, 3)], [('WLC', 69)], [('WLC', 82)], [('WLC', 83), ('WSC', 36)],
        [('WLC', 86), ('WSC', 37)], [('WLC', 90), ('WSC', 38)], [('WLC', 153), ('WSC', 85)],
        [('WLC', 154), ('WSC', 88)], [('WLC', 155), ('WSC', 89)], [('WLC', 156)],
        [('WLC', 157), ('WSC', 90)], [('WLC', 158)], [('WLC', 159)], [('WLC', 160)],
        [('WCF', 27, 1)], [('WLC', 162), ('WSC', 92)], [('WCF', 27, 2), ('WLC', 163)],
        [('WCF', 27, 3)], [('WLC', 161), ('WSC,', 91)], [('WCF', 2, 4)], [('WLC', 164), ('WSC', 93)],
        [('WCF', 27, 5)], [('WCF', 28, 1)], [('WLC', 165), ('WSC', 94)], [('WCF', 28, 2)],
        [('WCF', 28, 3)], [('WCF', 28, 4)], [('WLC', 166), ('WSC', 95)], [('WCF', 28, 5)],
        [('WCF', 28, 6)], [('WCF', 28, 7)], [('WLC', 167)], [('WCF', 29, 1)],
        [('WLC', 168), ('WSC', 96)], [('WCF', 29, 2)], [('WCF', 29, 3), ('WLC', 169)],
        [('WCF', 29, 4)], [('WCF', 29, 5)], [('WCF', 29, 6)], [('WCF', 29, 7), ('WLC', 170)],
        [('WCF', 29, 8)], [('WLC', 171), ('WSC', 97)], [('WLC', 172)], [('WLC', 173)],
        [('WLC', 174)], [('WLC', 175)], [('WLC', 176)], [('WLC', 177)], [('WCF', 30, 1)],
        [('WCF', 30, 2)], [('WCF', 30, 3)], [('WCF', 30, 4)], [('WCF', 31, 1)],
        [('WCF', 31, 2)], [('WCF', 31, 3)], [('WCF', 31, 4)], [('WLC', 84)],
        [('WCF', 32, 1)], [('WLC', 85), ('WSC', 37)], [('WCF', 32, 2), ('WLC', 87)],
        [('WCF', 32, 3)], [('WCF', 33, 1), ('WLC', 88)], [('WCF', 33, 2), ('WLC', 89)],
        [('WLC', 90), ('WSC', 38)], [('WCF', 33, 3)])


def get_day(month, day):
    day_of_year = (dt.datetime(2004, int(month), int(day)) - dt.datetime(2004, 1, 1)).days
    refs = plan[day_of_year]
    # return refs
    return [get(*ref) for ref in refs]
