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
                      r"\2<sup id='fnref:\1'><a href='#fn:\1' rel='footnote' style='text-decoration: none;'>&bull;</a></sup>",
                      body, count=1000)
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
                           for pt in _get_prooftexts(wcf[chapter]['body'][section], prooftexts)}
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

_plan_titles = ["What is the chief and highest end of man?", "Of the holy Scripture, part 1", "How doth it appear that there is a God?",
                "Of the holy Scripture, part 2", "What rule hath God given to direct us how we may glorify and enjoy him?",
                "Of the holy Scripture, part 3", "Of the holy Scripture, part 4", "Of the holy Scripture, part 5",
                "How doth it appear that the Scriptures are the Word of God?", "Of the holy Scripture, part 6",
                "Of the holy Scripture, part 7", "Of the holy Scripture, part 8", "Of the holy Scripture, part 9",
                "Of the holy Scripture, part 10", "What do the scriptures principally teach?", "What do the Scriptures make known of God?",
                "Of God, and of the holy Trinity, part 1", "What is God?", "Are there more Gods than one?",
                "Of God, and of the holy Trinity, part 2", "Of God, and of the holy Trinity, part 3",
                "How many persons are there in the Godhead?", "What are the personal properties of the three persons in the Godhead?",
                "How doth it appear that the Son and the Holy Ghost are God equal with the Father?", "Of God's eternal decree, part 1",
                "What are the decrees of God?", "Of God's eternal decree, part 2", "Of God's eternal decree, part 3",
                "What hath God especially decreed concerning angels and men?", "Of God's eternal decree, part 4",
                "Of God's eternal decree, part 5", "Of God's eternal decree, part 6", "Of God's eternal decree, part 7",
                "Of God's eternal decree, part 8", "How doth God execute his decrees?", "Of creation, part 1",
                "What is the work of creation?", "How did God create angels?", "Of creation, part 2", "How did God create man?",
                "Of providence, part 1", "What are God's works of providence?", "Of providence, part 2", "Of providence, part 3",
                "Of providence, part 4", "What is God's providence towards the angels?", "Of providence, part 5", "Of providence, part 6",
                "Of providence, part 7", "Of the fall of man, of sin, and of the punishment thereof, part 1",
                "Did man continue in that estate wherein God at first created him?", "What is sin?",
                "What was the sin whereby our first parents fell from the estate wherein they were created?",
                "Of the fall of man, of sin, and of the punishment thereof, part 2",
                "Of the fall of man, of sin, and of the punishment thereof, part 3", "Did all mankind fall in Adam's first transgression?",
                "Into what estate did the fall bring mankind?", "Of the fall of man, of sin, and of the punishment thereof, part 4",
                "Wherein consists the sinfulness of that estate whereinto man fell?",
                "Wherein consists the sinfulness of that estate whereinto man fell?",
                "Of the fall of man, of sin, and of the punishment thereof, part 5",
                "How is original sin conveyed from our first parents unto their posterity?",
                "Of the fall of man, of sin, and of the punishment thereof, part 6", "What misery did the fall bring upon mankind?",
                "What are the punishments of sin in this world?", "What are the punishments of sin in the world to come?",
                "Of God's covenant with man, part 1", "What was the providence of God toward man in the estate in which he was created?",
                "Of God's covenant with man, part 2", "Of God's covenant with man, part 3",
                "Did God leave all mankind to perish in the estate of sin and misery?", "With whom was the covenant of grace made?",
                "How is the grace of God manifested in the second covenant?", "Of God's covenant with man, part 4",
                "Of God's covenant with man, part 5", "Was the covenant of grace always administered after one and the same manner?",
                "How was the covenant of grace administered under the Old Testament?", "Of God's covenant with man, part 6",
                "How is the covenant of grace administered under the New Testament?", "Of Christ the mediator, part 1",
                "Of Christ the mediator, part 2", "Who is the redeemer of God's elect?",
                "How did Christ, being the Son of God, become man?", "Why was it requisite that the mediator should be God?",
                "Why was it requisite that the mediator should be man?", "Why was it requisite that the mediator should be God and man in one person?", "Why was our mediator called Jesus?",
                "Of Christ the mediator, part 3", "What offices doth Christ execute as our redeemer?",
                "How doth Christ execute the office of a prophet?", "Of Christ the mediator, part 4", "Of Christ the mediator, part 5",
                "How doth Christ execute the office of a priest?", "How doth Christ execute the office of a king?",
                "What was the estate of Christ's humiliation?", "How did Christ humble himself in his conception and birth?",
                "How did Christ humble himself in his life?", "How did Christ humble himself in his death?",
                "Wherein consisted Christ's humiliation after his death?", "What was the estate of Christ's exaltation?",
                "How was Christ exalted in his resurrection?", "How was Christ exalted in his ascension?",
                "How is Christ exalted in his sitting at the right hand of God?", "How doth Christ make intercession?",
                "How is Christ to be exalted in his coming again to judge the world?", "Of Christ the mediator, part 6",
                "Of Christ the mediator, part 7", "Of Christ the mediator, part 8", "What benefits hath Christ procured by his mediation?",
                "Of free will, part 1", "Of free will, part 2", "Of free will, part 3", "Of free will, part 4", "Of free will, part 5",
                "What benefits hath Christ procured by his mediation?", "How are we made partakers of the redemption purchased by Christ?",
                "How doth the Spirit apply to us the redemption purchased by Christ?", "Of effectual calling, part 1",
                "What is effectual calling?", "Are the elect only effectually called?", "Of effectual calling, part 2",
                "Of effectual calling, part 3", "Of effectual calling, part 4", "Can they who have never heard the gospel be saved?",
                "What benefits do they that are effectually called partake of in this life?", "Of justification, part 1",
                "What is justification?", "Of justification, part 2", "Of justification, part 3",
                "How is justification an act of God's free grace?", "Of justification, part 4", "Of justification, part 5",
                "Of justification, part 6", "Of adoption, part 1", "What is adoption?", "Of sanctification, part 1",
                "What is sanctification?", "Whence ariseth the imperfection of sanctification in believers?", "Of sanctification, part 3",
                "Wherein do justification and sanctification differ?", "What are the benefits which in this life do accompany justification?",
                "What doth God require of us that we may escape his wrath and curse due to us for sin?", "Of saving faith, part 1",
                "What is faith in Jesus Christ?", "Of saving faith, part 2", "How doth faith justify a sinner in the sight of God?",
                "Of saving faith, part 3", "Of repentance unto life, part 1", "Of repentance unto life, part 2",
                "What is repentance unto life?", "Of repentance unto life, part 3", "Of repentance unto life, part 4",
                "Of repentance unto life, part 5", "Of repentance unto life, part 6", "Of good works, part 1", "Of good works, part 2",
                "Of good works, part 3", "Of good works, part 4", "Of good works, part 5", "Of good works, part 6",
                "Of good works, part 7", "Of the perseverance of the saints, part 1",
                "May not true believers fall away from the state of grace?", "Of the perseverance of the saints, part 2",
                "Of the perseverance of the saints, part 3", "Of the assurance of grace and salvation, part 1",
                "Can true believers be infallibly assured that they are in the estate of grace?",
                "Of the assurance of grace and salvation, part 2", "Of the assurance of grace and salvation, part 3",
                "Are all true believers at all times assured of their present being in the estate of grace?",
                "Of the assurance of grace and salvation, part 4", "What is the duty which God requireth of man?",
                "Of the law of God, part 1", "What did God at first reveal to man for the rule of his obedience?",
                "What is the moral law?", "Of the law of God, part 2", "Where is the moral law summarily comprehended?",
                "Of the law of God, part 3", "Of the law of God, part 4", "Of the law of God, part 5",
                "Is there any use of the moral law since the fall?", "Of what use is the moral law to all men?",
                "What particular use is there of the moral law to unregenerate men?", "Of the law of God, part 6",
                "What special use is there of the moral law to the regenerate?", "Of the law of God, part 7",
                "What rules are to be observed for the right understanding of the Ten Commandments?",
                "What special things are we to consider in the Ten Commandments?", "What is the preface to the Ten Commandments?",
                "What is the preface to the ten commandments?", "What doth the preface to the ten commandments teach us?",
                "What is the sum of the four commandments which contain our duty to God?", "Which is the first commandment?",
                "What is required in the first commandment?", "What is forbidden in the first commandment?",
                "What are we specially taught by these words, before me, in the first commandment?", "Which is the second commandment?",
                "What are the duties required in the second commandment?", "What sins are forbidden in the second commandment?",
                "What are the reasons annexed to the second commandment, the more to enforce it?", "Which is the third commandment?",
                "What is required in the third commandment?", "What are the sins forbidden in the third commandment?",
                "What reasons are annexed to the third commandment?", "Which is the fourth commandment?",
                "What is required in the fourth commandment?", "Which day of the seven hath God appointed to be the weekly sabbath?",
                "How is the sabbath or the Lord's day to be sanctified?", "Why is the charge of keeping the sabbath more specially directed to governors of families?",
                "What are the sins forbidden in the fourth commandment?", "What are the reasons annexed to the fourth commandment, the more to enforce it?",
                "Why is the word Remember set in the beginning of the fourth commandment?",
                "What is the sum of the six commandments which contain our duty to man?", "Which is the fifth commandment?",
                "Who are meant by father and mother in the fifth commandment?", "Why are superiors styled Father and Mother?",
                "What is the general scope of the fifth commandment?", "What is the honor that inferiors owe to their superiors?",
                "What are the sins of inferiors against their superiors?", "What is required of superiors towards their inferiors?",
                "What are the sins of superiors?", "What are the duties of equals?", "What are the sins of equals?",
                "What is the reason annexed to the fifth commandment, the more to enforce it?", "Which is the sixth commandment?",
                "What are the duties required in the sixth commandment?", "What are the sins forbidden in the sixth commandment?",
                "Which is the seventh commandment?", "What are the duties required in the seventh commandment?",
                "What are the sins forbidden in the seventh commandment?", "Which is the eighth commandment?",
                "What are the duties required in the eighth commandment?", "What are the sins forbidden in the eighth commandment?",
                "Which is the ninth commandment?", "What are the duties required in the ninth commandment?",
                "What are the sins forbidden in the ninth commandment?", "Which is the tenth commandment?",
                "What are the duties required in the tenth commandment?", "What are the sins forbidden in the tenth commandment?",
                "Is any man able perfectly to keep the commandments of God?", "Are all transgressions of the law of God equally heinous in themselves?",
                "What are those aggravations that make some sins more heinous than others?",
                "What doth every sin deserve at the hands of God?", "Of Christian liberty, and liberty of conscience, part 1",
                "Of Christian liberty, and liberty of conscience, part 2", "Of Christian liberty, and liberty of conscience, part 3",
                "Of Christian liberty, and liberty of conscience, part 4", "Of religious worship, and the sabbath day, part 1",
                "Of religious worship, and the sabbath day, part 2", "How are we to pray?", "What is prayer?",
                "Are we to pray unto God only?", "What is it to pray in the name of Christ?", "Why are we to pray in the name of Christ?",
                "How doth the Spirit help us to pray?", "Of religious worship, and the sabbath day, part 4", "For whom are we to pray?",
                "For what things are we to pray?", "Of religious worship, and the sabbath day, part 5",
                "Of religious worship, and the sabbath day, part 6", "Of religious worship, and the sabbath day, part 7",
                "Which day of the seven hath God appointed to be the weekly sabbath?", "Of religious worship, and the sabbath day, part 8",
                "How is the sabbath or the Lord's day to be sanctified?", "What rule hath God given for our direction in the duty of prayer?", "How is the Lord's prayer to be used?",
                "Of how many parts doth the Lord's prayer consist?", "What doth the preface of the Lord's prayer teach us?",
                "What do we pray for in the first petition?", "What do we pray for in the second petition?",
                "What do we pray for in the third petition?", "What do we pray for in the fourth petition?",
                "What do we pray for in the fifth petition?", "What do we pray for in the sixth petition?",
                "What doth the conclusion of the Lord's prayer teach us?", "Of lawful oaths and vows, part 1",
                "Of lawful oaths and vows, part 2", "Of lawful oaths and vows, part 3", "Of lawful oaths and vows, part 4",
                "Of lawful oaths and vows, part 5", "Of lawful oaths and vows, part 6", "Of lawful oaths and vows, part 7",
                "Of the civil magistrate, part 1", "Of the civil magistrate, part 2", "Of the civil magistrate, part 3",
                "Of the civil magistrate, part 4", "Of marriage and divorce, part 1", "Of marriage and divorce, part 2",
                "Of marriage and divorce, part 3", "Of marriage and divorce, part 4", "Of marriage and divorce, part 5",
                "Of marriage and divorce, part 6", "What is the invisible church?",
                "What special benefits do the members of the invisible church enjoy by Christ?", "What is the visible church?",
                "What are the special privileges of the visible church?", "Of the church, part 4",
                "Are all they saved who hear the gospel, and live in the church?", "Of the church, part 6",
                "What is that union which the elect have with Christ?", "Of the communion of saints, part 2",
                "Of the communion of saints, part 3", "What is the communion in grace which the members of the invisible church have with Christ?",
                "What is the communion in glory which the members of the invisible church have with Christ?",
                "What is the communion with Christ which the members of the invisible church enjoy?",
                "What benefits do believers receive from Christ at death?", "What benefits do believers receive from Christ at the resurrection?",
                "What doth God require of us that we may escape his wrath and curse due to us for sin?",
                "What are the outward means whereby Christ communicates the benefits of his mediation?",
                "How is the word made effectual to salvation?", "Is the Word of God to be read by all?",
                "How is the word to be read and heard, that it may become effectual to salvation?",
                "By whom is the Word of God to be preached?", "How is the Word of God to be preached by those that are called thereunto?",
                "What is required of those that hear the word preached?", "Of the sacraments, part 1", "What is a sacrament?",
                "What are the parts of a sacrament?", "Of the sacraments, part 3",
                "How do the sacraments become effectual means of salvation?", "Of the sacraments, part 4",
                "Which are the sacraments of the New Testament?", "Of the sacraments, part 5", "Of baptism, part 1", "What is baptism?",
                "Of baptism, part 2", "Of baptism, part 3", "Of baptism, part 4", "To whom is baptism to be administered?",
                "Of baptism, part 5", "Of baptism, part 6", "Of baptism, part 7", "How is baptism to be improved by us?",
                "Of the lord's supper, part 1", "What is the Lord's supper?", "Of the lord's supper, part 2",
                "How hath Christ appointed bread and wine to be given and received?", "Of the lord's supper, part 4",
                "Of the lord's supper, part 5", "Of the lord's supper, part 6",
                "How do they that worthily communicate in the Lord's supper feed upon Christ therein?", "Of the lord's supper, part 8",
                "What is required to the worthy receiving of the Lord's supper?",
                "May one who doubteth of his being in Christ come to the Lord's supper?",
                "May any who profess the faith, and desire to come to the Lord's supper, be kept from it?",
                "What is required of them that receive the sacrament of the Lord's supper?",
                "What is the duty of Christians, after they have received the Lord's supper?",
                "Wherein do the sacraments of baptism and the Lord's supper agree?",
                "Wherein do the sacraments of baptism and the Lord's supper differ?", "Of church censures, part 1",
                "Of church censures, part 2", "Of church censures, part 3", "Of church censures, part 4", "Of synods and councils, part 1",
                "Of synods and councils, part 2", "Of synods and councils, part 3", "Of synods and councils, part 4", "Shall all men die?",
                "Of the state of men after death, and of the resurrection of the dead, part 1",
                "What benefits do believers receive from Christ at death?", "What are we to believe concerning the resurrection?",
                "Of the state of men after death, and of the resurrection of the dead, part 3",
                "What shall immediately follow after the resurrection?", "What shall be done to the wicked at the day of judgment?",
                "What benefits do believers receive from Christ at the resurrection?",
                "Of the last judgment, part 3"]


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
    # return refs
    return [get(*ref, prooftexts=prooftexts) for ref in refs]


def get_today_content(tz='UTC', prooftexts=True):
    tz = pytz.timezone(tz)
    month = dt.datetime.now(tz=tz).month
    day = dt.datetime.now(tz=tz).day
    return month, day, get_day(month, day, prooftexts)
