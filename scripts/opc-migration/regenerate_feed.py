# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "feedgen==1.0.0",
#     "pytz==2025.2",
#     "premailer==3.10.0",
#     "markdown==3.5.1",
#     "beautifulsoup4==4.12.2",
#     "lxml",
# ]
# ///
"""Regenerate the pre-rendered `feed` field in every content/MM/DD/data.json.

The stored values were exported once from the retired Flask app (2020, Georgia
inline styles). The daily email worker injects data.feed into
templates/newsletter-buttondown.html, whose design pairs with the styling in
generate_feed.py's content() pipeline — so we regenerate every day with that
pipeline, both to pick up the migrated proof texts and to unify email styling.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from generate_feed import content  # noqa: E402

CONTENT = ROOT / 'content'


def main():
    done = failed = 0
    for data_path in sorted(CONTENT.glob('*/*/data.json')):
        mm = data_path.parent.parent.name
        dd = data_path.parent.name
        try:
            fragment = content(mm, dd)
        except Exception as e:
            print(f'FAIL {mm}/{dd}: {e}')
            failed += 1
            continue
        data = json.loads(data_path.read_text())
        data['feed'] = fragment
        data_path.write_text(json.dumps(data, indent=0, ensure_ascii=False))
        done += 1
    print(f'regenerated {done} feed fields, {failed} failures')


if __name__ == '__main__':
    main()
