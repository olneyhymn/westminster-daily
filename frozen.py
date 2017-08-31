from flask_frozen import Freezer
from flask_application.app import app
import datetime as dt

freezer = Freezer(app)
app.config['SERVER_NAME'] = 'reformedconfessions.com.s3-website-us-east-1.amazonaws.com'


@freezer.register_generator
def render_fixed_day_json():
    for i in range(366):
        date = dt.datetime(2017, 1, 1) + dt.timedelta(days=i)
        yield {'month': date.strftime('%m'), 'day': date.strftime('%d')}


@freezer.register_generator
def feed_by_day():
    for i in range(366):
        date = dt.datetime(2017, 1, 1) + dt.timedelta(days=i)
        yield {'month': date.strftime('%m'), 'day': date.strftime('%d')}


if __name__ == '__main__':
    freezer.freeze()
