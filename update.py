import boto3
import datetime as dt


bucket = 'reformedconfessions.com'
index = 'westminster-daily/index.html'
feed = 'westminster-daily/feed.rss'


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
