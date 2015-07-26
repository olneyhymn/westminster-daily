import datetime as dt
import pytz

import flask_application.data as data


def test_today_content():
    month, day, content = data.get_today_content(tz='UTC')
    tz = pytz.timezone('UTC')
    assert month == dt.datetime.now(tz=tz).month
    assert day == dt.datetime.now(tz=tz).day
