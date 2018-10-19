from flask_frozen import Freezer
from flask_application.app import app
import datetime as dt

freezer = Freezer(app)
app.testing = True
app.config['SERVER_NAME'] = 'reformedconfessions.com'


@freezer.register_generator
def render_fixed_day_json():
    for i in range(366):
        date = dt.datetime(2016, 1, 1) + dt.timedelta(days=i)
        yield {'month': date.strftime('%m'), 'day': date.strftime('%d')}


if __name__ == '__main__':
    freezer.freeze()
