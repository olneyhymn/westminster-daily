import boto3
import datetime as dt
import os
import facebook
import pytz
import requests
from retrying import retry
from urllib.request import urlopen

bucket = 'reformedconfessions.com'
index = 'westminster-daily/index.html'
feed = 'westminster-daily/feed.rss'
base_url = 'http://reformedconfessions.com.s3-website-us-east-1.amazonaws.com/westminster-daily/'


def update_feed_and_homepage(a, b):
    s3 = boto3.client('s3')
    date = dt.datetime.now()

    copy_source = {
        'Bucket': bucket,
        'Key': 'westminster-daily/{date:%m}/{date:%d}/index.html'.format(date=date)
    }
    s3.copy(copy_source,
            bucket,
            index,
            )
    copy_source = {
        'Bucket': bucket,
        'Key': 'westminster-daily/{date:%m}/{date:%d}/feed.rss'.format(date=date)
    }
    s3.copy(copy_source,
            bucket,
            index,
            )
    s3.put_object_acl(ACL='public-read', Bucket=bucket, Key=feed)
    s3.put_object_acl(ACL='public-read', Bucket=bucket, Key=index)


def update_facebook(a, b):
    api = facebook.GraphAPI(os.environ['FB_ACCESS_TOKEN'])

    month, day, content = get_today_content(tz="US/Eastern", prooftexts=False)
    url = "{base}{month:0>2}/{day:0>2}".format(base=base_url, month=month, day=day)
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
    base_url = "http://reformedconfessions.com/westminster-daily/"
    cred = {
        "consumer_key": os.environ['TW_CONSUMER_KEY'],
        "consumer_secret": os.environ['TW_CONSUMER_SECRET'],
        "token": os.environ['TW_TOKEN'],
        "token_secret": os.environ['TW_TOKEN_SECRET'],
    }
    auth = tw.OAuth(**cred)
    t = tw.Twitter(auth=auth)

    month, day, content = get_today_content(tz="US/Eastern")
    description = get_day_title(month, day)
    url = "{base}{month:0>2}/{day:0>2}".format(base=base_url, month=month, day=day)

    try:
        # Attempt tweet
        url = "http://www.reformedconfessions.com/static/images/docs/{:0>2}{:0>2}-full.png".format(month, day)
        imagedata = urlopen(url).read()
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


def get_today_content(tz="US/Eastern", prooftexts=False):
    tz = pytz.timezone(tz)
    month = dt.datetime.now(tz=tz).strftime('%m')
    day = dt.datetime.now(tz=tz).strftime('%d')
    return month, day, get_day(month, day, prooftexts)['content']


def get_day(month, day, prooftexts=False):

    url = "{base_url}{month}/{day}.json".format(base_url=base_url, month=month, day=day)
    print(url)
    return requests.get(url).json()


def get_day_title(month, day):
    return get_day(month, day)['title']
