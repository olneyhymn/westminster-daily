import datetime as dt
import pytz

import flask_application.data as data


def test_today_content():
    month, day, content = data.get_today_content(tz='UTC')
    tz = pytz.timezone('UTC')
    assert month == dt.datetime.now(tz=tz).month
    assert day == dt.datetime.now(tz=tz).day


def test_get_day():
    pass


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


def test_catechism():
    pass
