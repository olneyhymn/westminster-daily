import datetime as dt
import pytz
import pytest

import flask_application.data as data


def test_today_content():
    month, day, content = data.get_today_content(tz='UTC')
    tz = pytz.timezone('UTC')
    assert month == dt.datetime.now(tz=tz).month
    assert day == dt.datetime.now(tz=tz).day


def test_get_day():
    jan1 = data.get_day(1, 1)
    assert len(jan1) == 2
    assert {d['citation'] for d in jan1} == {"WLC 1", "WSC 1"}

    jan2 = data.get_day(1, 2)
    assert len(jan2) == 1
    assert {d['citation'] for d in jan2} == {"WCF 1.1"}

    oct19 = data.get_day(10, 19)
    assert len(oct19) == 2
    assert {d['citation'] for d in oct19} == {"WCF 25.1", "WLC 64"}

    with pytest.raises(data.DataException):
        data.get_day(4, 31)


def test_leap_get_day():
    assert data.get_day(2, 29) == data.get_day(2, 28)

def test_confession():
    wcf11 = data.get_confession("wcf", "1", "1")
    assert wcf11['type'] == 'confession'
    assert wcf11['abbv'] == 'wcf'
    assert wcf11['name'] == 'Confession of Faith'
    assert wcf11['section_title'] == ""
    assert wcf11['chapter'] == "1"
    assert wcf11['paragraph'] == "1"
    assert wcf11['citation'] == "WCF 1.1"
    assert wcf11['long_citation'] == "Confession of Faith 1.1"
    assert wcf11['body'] == "Although the light of nature, and the works " \
                            "of creation and providence do so far manifest the goodness, wisdom, and power of " \
                            "God, as to leave men unexcusable; yet are they not sufficient to give that " \
                            "knowledge of God, and of his will, which is necessary unto salvation. Therefore " \
                            "it pleased the Lord, at sundry times, and in divers manners, to reveal himself, " \
                            "and to declare that his will unto his church; and afterwards, for the better " \
                            "preserving and propagating of the truth, and for the more sure establishment and " \
                            "comfort of the church against the corruption of the flesh, and the malice of " \
                            "Satan and of the world, to commit the same wholly unto writing: which maketh the " \
                            "Holy Scripture to be most necessary; those former ways of God's revealing his " \
                            "will unto his people being now ceased."


def test_larger_catechism_q1():
    wlc11 = data.get_catechism('wlc', '1')
    assert wlc11['type'] == 'catechism'
    assert wlc11['abbv'] == 'wlc'
    assert wlc11['name'] == 'Larger Catechism'
    assert wlc11['section_title'] == ''
    assert wlc11['number'] == '1'
    assert wlc11['citation'] == 'WLC 1'
    assert wlc11['long_citation'] == 'Larger Catechism 1'
    assert wlc11['answer'] == 'Man\'s chief and highest end is to glorify God, and fully to enjoy him forever.'
    assert wlc11['question'] == 'What is the chief and highest end of man?'


def test_larger_catechism_all_exists():
    for question in range(1, 197):
        assert data.get_catechism('wlc', str(question))
    with pytest.raises(data.DataException):
        data.get_catechism('wlc', '198')
    with pytest.raises(data.DataException):
        data.get_catechism('wlc', '0')



def test_shorter_catechism_all_exists():
    for question in range(1, 107):
        assert data.get_catechism('wsc', str(question))
    with pytest.raises(data.DataException):
        data.get_catechism('wsc', '108')
    with pytest.raises(data.DataException):
        data.get_catechism('wsc', '0')


def test_westminster_confession_all_exists():
    for c, s in [(1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9), (1, 10),
                 (2, 1), (2, 2), (2, 3), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6), (3, 7),
                 (3, 8), (4, 1), (4, 2), (5, 1), (5, 2), (5, 3), (5, 4), (5, 5), (5, 6), (5, 7),
                 (6, 1), (6, 2), (6, 3), (6, 4), (6, 5), (6, 6), (7, 1), (7, 2), (7, 3), (7, 4),
                 (7, 5), (7, 6), (8, 1), (8, 2), (8, 3), (8, 4), (8, 5), (8, 6), (8, 7), (8, 8),
                 (9, 1), (9, 2), (9, 3), (9, 4), (9, 5), (10, 1), (10, 2), (10, 3), (10, 4), (11, 1),
                 (11, 2), (11, 3), (11, 4), (11, 5), (11, 6), (12, 1), (13, 1), (13, 2), (13, 3), (14, 1),
                 (14, 2), (14, 3), (15, 1), (15, 2), (15, 3), (15, 4), (15, 5), (15, 6), (16, 1), (16, 2),
                 (16, 3), (16, 4), (16, 5), (16, 6), (16, 7), (17, 1), (17, 2), (17, 3), (18, 1), (18, 2),
                 (18, 3), (18, 4), (19, 1), (19, 2), (19, 3), (19, 4), (19, 5), (19, 6), (19, 7), (20, 1),
                 (20, 2), (20, 3), (20, 4), (21, 1), (21, 2), (21, 3), (21, 4), (21, 5), (21, 6), (21, 7),
                 (21, 8), (22, 1), (22, 2), (22, 3), (22, 4), (22, 5), (22, 6), (22, 7), (23, 1), (23, 2),
                 (23, 3), (23, 4), (24, 1), (24, 2), (24, 3), (24, 4), (24, 5), (24, 6), (25, 1), (25, 2),
                 (25, 3), (25, 4), (25, 5), (25, 6), (26, 1), (26, 2), (26, 3), (27, 1), (27, 2), (27, 3),
                 (27, 4), (27, 5), (28, 1), (28, 2), (28, 3), (28, 4), (28, 5), (28, 6), (28, 7), (29, 1),
                 (29, 2), (29, 3), (29, 4), (29, 5), (29, 6), (29, 7), (29, 8), (30, 1), (30, 2), (30, 3),
                 (30, 4), (31, 1), (31, 2), (31, 3), (31, 4), (32, 1), (32, 2), (32, 3), (33, 1), (33, 2),
                 (33, 3)]:
        assert data.get_confession('wcf', c, s)

    with pytest.raises(data.DataException):
        data.get_confession('wcf', 0, 0)
    with pytest.raises(data.DataException):
        data.get_confession('wcf', 1, 11)
    with pytest.raises(data.DataException):
        data.get_confession('wcf', 33, 4)
    with pytest.raises(data.DataException):
        data.get_confession('wcf', 34, 1)
