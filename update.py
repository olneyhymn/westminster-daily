import boto3
import datetime as dt
import os
import facebook
import pytz

from retrying import retry
from urllib.request import urlopen
from flask_application.data import get_day_api
from flask_application.feed import make_feed

bucket = 'reformedconfessions.com'
index = 'westminster-daily/index.html'
feed = 'westminster-daily/feed.rss'
base_url = 'http://reformedconfessions.com/'
file_url = 'http://reformedconfessions.com/'
api_url = '{file_url}westminster-daily/'.format(file_url=file_url)


tz = pytz.timezone("US/Eastern")
month = dt.datetime.now(tz=tz).strftime('%m')
day = dt.datetime.now(tz=tz).strftime('%d')


def update_feed_and_homepage(a, b):
    s3 = boto3.client('s3')
    date = dt.datetime.now()
    feed_contents = make_feed("Westminster Daily",
                              "http://feedpress.me/westminster-daily",
                              "http://www.reformedconfessions.com/westminster-daily/",
                              "US/Eastern",
                              prooftexts=True,
                              count=10,
                              api=True).to_string()

    copy_source = {
        'Bucket': bucket,
        'Key': 'westminster-daily/{date:%m}/{date:%d}/index.html'.format(date=date)
    }
    s3.copy(copy_source,
            bucket,
            index,
            )

    s3.put_object(Body=feed_contents,
                  Bucket=bucket,
                  Key='westminster-daily/feed.rss'.format(date=date),
                  ContentType="text/xml"
                  )

    s3.put_object_acl(ACL='public-read', Bucket=bucket, Key=feed)
    s3.put_object_acl(ACL='public-read', Bucket=bucket, Key=index)


def update_facebook(a, b):
    api = facebook.GraphAPI(os.environ['FB_ACCESS_TOKEN'])
    content = get_day_api(month, day, False, api_url=api_url)['content']
    url = "{base}westminster-daily/{month:0>2}/{day:0>2}".format(base=base_url, month=month, day=day)
    attachment = {'link': url}

    content = make_facebook_string(content)

    if (month, day) in [(1, 4), (7, 5)]:
        content = "" # Days have html formatting

    _post_facebook(api, content, attachment)


@retry(wait_exponential_multiplier=1000,
       stop_max_attempt_number=10,
       retry_on_exception=facebook.GraphAPIError)
def _post_facebook(api, content, attachment):
    api.put_wall_post(content, attachment=attachment)


def make_facebook_string(content):
    c_strings = []
    for c in content:
        if c['type'] == 'confession':
            c_strings.append("""{}

{}

""".format(c['long_citation'], c['body']))
        elif c['type'] == 'catechism':
            c_strings.append("""{}

Q. {}
A. {}

""".format(c['long_citation'], c['question'], c['answer']))
    return ''.join(c_strings)


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
