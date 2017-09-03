import datetime as dt

from flask_application.app import app


def test_rss():
    with app.test_client() as c:
        response = c.get('/westminster-daily/feed.rss', follow_redirects=False)
        assert response.status_code == 200
        assert response.mimetype == 'application/atom+xml'
        assert response.content_length > 100000


def test_daily_westminster_pages_exist():
    start_date = dt.date(2015, 1, 1)

    with app.test_client() as c:
        response = c.get('/westminster-daily')
        assert response.status_code == 301
        response = c.get('/westminster-daily/')
        assert response.status_code == 200

        for days in range(365):
            date = start_date + dt.timedelta(days=days)
            month, day = date.month, date.day
            response = c.get('/westminster-daily/{month:02d}/{day:02d}/'.format(month=month, day=day),
                             follow_redirects=False)
            assert response.status_code == 200

            response = c.get('/westminster-daily/{month:02d}/{day:02d}'.format(month=month, day=day),
                             follow_redirects=False)
            assert response.status_code == 301


def test_chief_end_of_man():
    with app.test_client() as c:
        response = c.get('westminster-daily/01/01/')
        assert "chief end of man" in response.data
        response = c.get('westminster-daily/01/02/')
        assert "better preserving and propagating" in response.data


def test_daily_westminster_bad_days():
    with app.test_client() as c:
        response = c.get('westminster-daily/1/1/')
        assert response.status_code == 404
        response = c.get('westminster-daily/1/1', follow_redirects=True)
        assert response.status_code == 404
        response = c.get('westminster-daily/01/32/')
        assert response.status_code == 404
        response = c.get('westminster-daily/01/32', follow_redirects=True)
        assert response.status_code == 404
        response = c.get('westminster-daily/02/30/')
        assert response.status_code == 404
        response = c.get('westminster-daily/02/30', follow_redirects=True)
        assert response.status_code == 404
        response = c.get('westminster-daily/04/31/')
        assert response.status_code == 404
        response = c.get('westminster-daily/04/31', follow_redirects=True)
        assert response.status_code == 404


def test_daily_leap_day():
    with app.test_client() as c:
        response = c.get('westminster-daily/02/29/')
        assert response.status_code == 200


def test_about_page():
    with app.test_client() as c:
        response = c.get('about/')
        assert response.status_code == 200
        response = c.get('about')
        assert response.status_code == 301
