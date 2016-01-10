import re
from flask_application import data

FONT = """font-family: "Georgia", "Times New Roman", serif;"""


def format_prooftexts(prooftexts):
    keys = sorted([int(i) for i in prooftexts.keys()])
    out = []
    for k in keys:
        out.append(prooftexts[str(k)])

        out.append("<hr />")
    texts = "<div style='padding-left:2em'>" + "\n".join(out) + "</div>"
    return texts


def generate_day_email(month, day, prooftexts=True):
    email = []
    for c in data.get_day(month, day):
        email.append("<h3 style='{}'>{}</h3>".format(FONT, c['long_citation']))
        if 'body' in c:
            b = re.sub(r"<a.*?footnote.*?>&bull;</a>", "&bull;", c['body'])
            email.append(b)
        else:
            email.append(c['question'])
            email.append("<br />")
            b = re.sub(r"<a.*?footnote.*?>&bull;</a>", "&bull;", c['answer'])
            email.append(b)
        if 'prooftexts' in c:
            email.append(format_prooftexts(c['prooftexts']))
    body = "\n".join(email)
    body = "<span style='{}'>{}</span>".format(FONT, body)
    return body, data.get_day_title(month, day)


def send_day(month, day, prooftexts=True):
    body, title = generate_day_email(month, day, prooftexts)

    import requests

    key = 'key-b517e79e7c5d5001c1ff72921711ecb1'
    sandbox = 'sandboxc8c1e79c8ab24d2989942d0cb5627b83.mailgun.org'
    recipient = 'tdhopper@gmail.com'

    request_url = 'https://api.mailgun.net/v2/{0}/messages'.format(sandbox)
    request = requests.post(request_url, auth=('api', key), data={
        'from': 'hello@example.com',
        'to': recipient,
        'subject': title,
        'html': body,
    })

    print 'Status: {0}'.format(request.status_code)
    print 'Body:   {0}'.format(request.text)
