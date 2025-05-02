"""
Script to fetch Bible verses from the ESV API for Westminster Confession prooftexts.

This script:
1. Loads the Westminster Confession of Faith JSON file
2. For each section and prooftext:
   - Queries the ESV API to get the verse text
   - Stores the verse text in the JSON structure
3. Saves the updated JSON with verse texts back to file

The ESV API is queried with parameters to get clean verse text without 
numbers, footnotes, headings etc. A 1 second delay is added between requests
to avoid overwhelming the API.

Note: Requires a valid ESV API key (currently using "IP")
"""

import json
import requests
import time

# Load the Westminster Confession JSON
with open('/Users/tdhopper/repos/westminster-daily/flask_application/static/confessions/wcf.json', 'r') as f:
    j = json.load(f)

# Process each section
for k, v in j.items():
    j[k]['prooftext_verses'] = {}
    # Process each prooftext in the section
    for kk, vv in v['prooftexts'].items():
        # Query ESV API for verse text
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
    # Delay to avoid overwhelming API
    time.sleep(1)

# Save updated JSON back to file    
with open('/Users/tdhopper/repos/westminster-daily/flask_application/static/confessions/wcf.json', 'w') as f:
    json.dump(j, f)