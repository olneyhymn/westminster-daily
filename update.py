import datetime as dt
import os
import pytz

from urllib.request import urlopen
from flask_application.data import get_day_api

bucket = 'reformedconfessions.com'
index = 'westminster-daily/index.html'
feed = 'westminster-daily/feed.rss'
base_url = 'http://reformedconfessions.com/'
file_url = 'http://reformedconfessions.com/'
api_url = '{file_url}westminster-daily/'.format(file_url=file_url)


tz = pytz.timezone("US/Eastern")
month = dt.datetime.now(tz=tz).strftime('%m')
day = dt.datetime.now(tz=tz).strftime('%d')


def tweet(a, b):
    """Send tweet with todays content"""
    import twitter as tw
    cred = {
        "consumer_key": os.environ['TW_CONSUMER_KEY'],
        "consumer_secret": os.environ['TW_CONSUMER_SECRET'],
        "token": os.environ['TW_TOKEN'],
        "token_secret": os.environ['TW_TOKEN_SECRET'],
    }
    auth = tw.OAuth(**cred)
    t = tw.Twitter(auth=auth)

    day_data = get_day_api(month, day, api_url=api_url)
    content = day_data['content']
    description = day_data['title']
    url = "{base}westminster-daily/{month:0>2}/{day:0>2}".format(base=base_url, month=month, day=day)

    try:
        # Attempt tweet
        image_url = "{}static/images/docs/{:0>2}{:0>2}-full.png".format(file_url, month, day)
        imagedata = urlopen(image_url).read()
        t_up = tw.Twitter(domain='upload.twitter.com', auth=auth)
        id_img1 = t_up.media.upload(media=imagedata)["media_id_string"]
        t.statuses.update(status="{} {}".format(description, url),
                          media_ids=id_img1)
    except tw.api.TwitterHTTPError as e:
        if any(error['code'] == 186 for error in e.response_data['errors']):
            # Tweet too long. Try a shorter tweet.
            description = ", ".join(c['citation'] for c in content)
            t.statuses.update(status="{} {}".format(description, url))
        else:
            pass
            # log.error("%s %s", "Unhandled exception", str(e))
        return
    # log.info("%s %s", "Tweeted", str(description))
