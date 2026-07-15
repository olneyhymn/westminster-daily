#!/usr/bin/env python3
"""Apply the staged OPC migration: fetch ESV text for changed footnote groups,
then rewrite content/MM/DD/data.json and content/MM/DD.md.

Requires ESV_API_KEY (https://api.esv.org). Fetches are cached in
staged/esv-cache.json, so the script is safe to re-run/resume.

Usage:
  apply_migration.py fetch          # fetch + cache all needed passages
  apply_migration.py validate      # transform one passage, print legacy HTML
  apply_migration.py write          # rewrite data.json + md (requires full cache)
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
CONTENT = ROOT / 'content'
CACHE = HERE / 'staged' / 'esv-cache.json'

API = 'https://api.esv.org/v3/passage/html/'
PARAMS = {
    'include-passage-references': 'false',
    'include-verse-numbers': 'false',
    'include-first-verse-numbers': 'false',
    'include-footnotes': 'false',
    'include-headings': 'false',
    'include-short-copyright': 'false',
    'include-audio-link': 'false',
}


def load_manifests():
    groups = []
    for name in ('fetch-manifest.json', 'catechism-fetch-manifest.json'):
        p = HERE / 'staged' / name
        if p.exists():
            groups.extend(json.loads(p.read_text()))
    return groups


def all_refs(groups):
    refs = []
    seen = set()
    for g in groups:
        for r in g['refs']:
            if r not in seen:
                seen.add(r)
                refs.append(r)
    return refs


def fetch_ref(ref, key):
    q = urllib.parse.urlencode({'q': ref, **PARAMS})
    req = urllib.request.Request(f'{API}?{q}', headers={'Authorization': f'Token {key}'})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    passages = data.get('passages') or []
    if not passages:
        raise ValueError(f'no passage returned for {ref!r} '
                         f'(canonical: {data.get("canonical")!r})')
    return passages[0]


def to_legacy(ref, v3_html):
    """Convert a v3 API passage to the site's legacy blob section:
    <h5>Ref</h5> <div class="esv-text">INNER</div>

    Legacy poetry looks like:
      <div class="block-indent"><p class="line-group">line<br />
      <span class="indent"></span>indented line ...</p></div>
    while v3 emits:
      <p class="block-indent"><span class="line">..</span><br />
      <span class="indent line">..</span>... with &nbsp; indentation,
      <b class="chapter-num"> markers, and h4.psalm-title headings."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(v3_html, 'html.parser')

    for sel in (('h2', {}), ('h3', {}), ('h4', {'class_': 'psalm-title'}),
                ('b', {'class_': 'chapter-num'}), ('span', {'class_': 'chapter-num'})):
        for el in soup.find_all(sel[0], **sel[1]):
            el.decompose()

    def clean_inner(tag):
        inner = tag.decode_contents()
        inner = inner.replace(' ', ' ')
        inner = re.sub(r'\s+', ' ', inner).strip()
        # divine-name small caps, matching the legacy blobs
        inner = re.sub(r'\bLORD\b', '<span class="small-caps">Lord</span>', inner)
        inner = re.sub(r'\bGOD\b', '<span class="small-caps">God</span>', inner)
        return inner

    parts = []
    for p_tag in soup.find_all('p'):
        classes = p_tag.get('class') or []
        if 'block-indent' in classes:
            lines = []
            for span in p_tag.find_all('span', class_='line'):
                inner = clean_inner(span)
                if not inner:
                    continue
                if 'indent' in (span.get('class') or []):
                    inner = '<span class="indent"></span>' + inner
                lines.append(inner)
            if lines:
                body = '<br />\n'.join(lines)
                parts.append(f'<div class="block-indent">\n'
                             f'<p class="line-group">{body}</p>\n</div>')
        else:
            inner = clean_inner(p_tag)
            if inner:
                cls = ' class="same-paragraph"' if 'same-paragraph' in classes else ''
                parts.append(f'<p{cls}>{inner}</p>')

    if not parts:  # fallback: flatten whatever came back
        flat = re.sub(r'\s+', ' ', soup.get_text()).strip()
        parts = [f'<p>{flat}</p>']
    inner = '\n'.join(parts)
    return f'<h5>{ref}</h5>\n<div class="esv-text">{inner}\n</div>'


def build_blob(refs, cache):
    sections = '\n'.join(to_legacy(r, cache[r]) for r in refs)
    # closing ESV attribution, matching legacy blobs
    return (f'<div class="esv">{sections}\n'
            f'<p class="copyright-line">(<a href="http://www.esv.org" '
            f'class="copyright">ESV</a>)</p>\n</div>')


def fetch_group(refs, key):
    """One API call per footnote group (semicolon-joined passages) — stays far
    inside ESV's daily/query limits. Returns {ref: passage_html}."""
    q = urllib.parse.urlencode({'q': '; '.join(refs), **PARAMS})
    req = urllib.request.Request(f'{API}?{q}', headers={'Authorization': f'Token {key}'})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    passages = data.get('passages') or []
    if len(passages) != len(refs):
        raise ValueError(f'{len(passages)} passages for {len(refs)} refs '
                         f'(canonical: {data.get("canonical")!r})')
    return dict(zip(refs, passages))


def cmd_fetch():
    key = os.environ.get('ESV_API_KEY')
    if not key:
        sys.exit('ESV_API_KEY not set')
    groups = load_manifests()
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    todo = [g for g in groups if any(r not in cache for r in g['refs'])]
    print(f'{len(groups)} groups, {len(todo)} need fetching')
    for i, g in enumerate(todo, 1):
        refs = [r for r in g['refs'] if r not in cache]
        try:
            cache.update(fetch_group(refs, key))
        except Exception as e:
            print(f"  group FAIL {g['unit']} [{g['n']}]: {e}; retrying per-ref")
            for r in refs:
                try:
                    cache[r] = fetch_ref(r, key)
                except Exception as e2:
                    print(f'    FAIL {r}: {e2}')
                time.sleep(1.0)
        if i % 20 == 0:
            CACHE.write_text(json.dumps(cache, indent=0))
            print(f'  {i}/{len(todo)}')
        time.sleep(1.0)  # ~1 request/second, well under ESV rate limits
    CACHE.write_text(json.dumps(cache, indent=0))
    missing = [r for r in all_refs(groups) if r not in cache]
    print(f'done; {len(missing)} still missing' + (f': {missing[:10]}' if missing else ''))


def cmd_validate():
    key = os.environ.get('ESV_API_KEY')
    if not key:
        sys.exit('ESV_API_KEY not set')
    ref = sys.argv[2] if len(sys.argv) > 2 else 'Psalm 19:1-4'
    raw = fetch_ref(ref, key)
    print('--- raw v3 ---')
    print(raw[:1200])
    print('--- legacy ---')
    print(to_legacy(ref, raw)[:1200])


def sup_md(prefix, n):
    return f'[^fnref:{prefix}{n}]'


def rewrite_md(md_path, item_kind, prefix, new_body_plain_with_sups, groups, cache):
    """Replace an item's footnote markers/definitions in a day's markdown."""
    text = md_path.read_text()
    # 1. footnote definitions: drop all existing [^fnref:PREFIXn]: lines
    text = re.sub(rf'^\[\^fnref:{prefix}\d+\]:.*$\n?', '', text, flags=re.M)
    # 2. body: markdown body uses [^fnref:PREFIXn] markers; regenerate from the
    #    HTML body by converting sup tags to markdown markers
    md_body = re.sub(
        rf"<sup id='fnref:{prefix}(\d+)'>.*?</sup>",
        lambda m: sup_md(prefix, m.group(1)),
        new_body_plain_with_sups,
    )
    # find and replace the old body paragraph (starts with the paragraph-number
    # span for confession, or Q./A. lines for catechism) — caller supplies a
    # regex via item_kind
    old_body_re = re.compile(item_kind, re.M)
    if not old_body_re.search(text):
        return None
    text = old_body_re.sub(lambda m: md_body.replace('\\', '\\\\'), text, count=1)
    # 3. append fresh footnote definitions at the end
    defs = []
    for n in sorted(groups, key=int):
        blob = groups[n].get('esv') or build_blob(groups[n]['refs'], cache)
        blob = re.sub(r'\s*\n\s*', ' ', blob)
        defs.append(f'[^fnref:{prefix}{n}]: {blob}')
    text = text.rstrip('\n') + '\n\n' + '\n\n'.join(defs) + '\n'
    return text


def cmd_write():
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    wcf_staged = json.loads((HERE / 'staged' / 'wcf-changes.json').read_text())
    cat_staged_p = HERE / 'staged' / 'catechism-changes.json'
    cat_staged = json.loads(cat_staged_p.read_text()) if cat_staged_p.exists() else {}

    # verify cache completeness
    missing = set()
    for day, units in wcf_staged.items():
        for unit, ch in units.items():
            for n, g in ch['groups'].items():
                if g['esv'] is None:
                    missing.update(r for r in g['refs'] if r not in cache)
    for day, units in cat_staged.items():
        for unit_key, g in units.items():
            missing.update(r for r in g['refs'] if r not in cache)
    if missing:
        sys.exit(f'{len(missing)} refs missing from cache; run fetch first. '
                 f'e.g. {sorted(missing)[:5]}')

    feed_days = set()
    days_written = 0
    for data_path in sorted(CONTENT.glob('*/*/data.json')):
        mm = data_path.parent.parent.name
        dd = data_path.parent.name
        day = f'{mm}-{dd}'
        w = wcf_staged.get(day, {})
        c = cat_staged.get(day, {})
        if not w and not c:
            continue
        data = json.loads(data_path.read_text())
        md_path = CONTENT / mm / f'{dd}.md'
        changed = False

        for item in data.get('content_with_prooftexts', []):
            if item.get('type') == 'confession' and item.get('abbv') == 'wcf':
                unit = f"{item['chapter']}.{item['paragraph']}"
                if unit not in w:
                    continue
                ch = w[unit]
                item['body'] = ch['new_body']
                item['prooftexts'] = {
                    n: (g['esv'] or build_blob(g['refs'], cache))
                    for n, g in ch['groups'].items()
                }
                changed = True
                # markdown: confession body begins with the paragraph-number span
                para_n = item['paragraph']
                md = rewrite_md(
                    md_path,
                    rf'^<span class="paragraph-number">{para_n}\.</span>.*$',
                    'wcf', ch['new_body'], ch['groups'], cache)
                if md is None:
                    print(f'  WARN {day}: md body not found for WCF {unit}')
                else:
                    md_path.write_text(md)
            elif item.get('type') == 'catechism':
                key_base = f"{item['abbv'].upper()} {item['number']}"
                for fn in list(item.get('prooftexts', {})):
                    k = f'{key_base}|{fn}'
                    if k not in c:
                        continue
                    blob = build_blob(c[k]['refs'], cache)
                    item['prooftexts'][fn] = blob
                    changed = True
                    # markdown footnote definition swap (marker unchanged)
                    prefix = item['abbv']
                    text = md_path.read_text()
                    blob_flat = re.sub(r'\s*\n\s*', ' ', blob)
                    new_text, nsub = re.subn(
                        rf'^\[\^fnref:{prefix}{fn}\]:.*$',
                        lambda m: f'[^fnref:{prefix}{fn}]: {blob_flat}'.replace('\\', '\\\\'),
                        text, count=1, flags=re.M)
                    if nsub:
                        md_path.write_text(new_text)
                    else:
                        print(f'  WARN {day}: md footnote fnref:{prefix}{fn} not found')

        if changed:
            data_path.write_text(json.dumps(data, indent=0, ensure_ascii=False))
            feed_days.add(day)
            days_written += 1

    print(f'wrote {days_written} days')
    (HERE / 'staged' / 'feed-regen-days.json').write_text(
        json.dumps(sorted(feed_days), indent=1))
    print(f'{len(feed_days)} days need their data.json "feed" field regenerated '
          f'(list: staged/feed-regen-days.json)')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'fetch'
    {'fetch': cmd_fetch, 'validate': cmd_validate, 'write': cmd_write}[cmd]()
