import json, requests, time
with open('/Users/tdhopper/repos/westminster-daily/flask_application/static/confessions/wcf.json', 'r') as f:
    j = json.load(f)
for k, v in j.items():
    j[k]['prooftext_verses'] = {}
    for kk, vv in v['prooftexts'].items():
        r = requests.request("GET", "http://www.esvapi.org/v2/rest/passageQuery",
                             params={"include-verse-numbers": 0,
                                     "include-footnotes": 0,
                                     "include-audio-link": 0,
                                     "include-headings": 0,
                                     "include-first-verse-numbers": 0,
                                     "include-subheadings": 0,
                                     "key": "IP",
                                     "passage": vv
                                    })
        print r.url
        j[k]['prooftext_verses'][kk] = r.text
    time.sleep(1)
    
with open('/Users/tdhopper/repos/westminster-daily/flask_application/static/confessions/wcf.json', 'w') as f:
    json.dump(j, f)