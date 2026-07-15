#!/usr/bin/env python3
"""Stage the 18 confirmed catechism corrections (audit v2) against the daily
data.json files. Every touched footnote group is re-fetched from the ESV API,
so this only records the corrected ref lists + fetch manifest entries.

Fix list source: print/audit/provenance-audit-report.md §4, verified against
the OPC PDFs (our catechisms' source edition).
"""

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
CONTENT = ROOT / 'content'

# (abbv, question, footnote) -> list of ops
# ops: ('replace', old, new) | ('add', ref) | ('add_after', ref, anchor) | ('remove', ref)
FIXES = {
    ('wsc', '9', '1'): [('replace', 'Psalm 33:19', 'Psalm 33:9')],
    ('wsc', '75', '1'): [('add', 'Ephesians 4:28'), ('add', '2 Thessalonians 3:10'),
                         ('add', '1 Timothy 5:8')],
    ('wlc', '4', '1'): [('add_after', '1 Corinthians 2:13', '1 Corinthians 2:6-7')],
    ('wlc', '25', '3'): [('remove', 'Romans 3:23')],
    ('wlc', '29', '1'): [('replace', 'Mark 9:43', 'Mark 9:43-44'),
                         ('replace', 'Mark 9:45-47', 'Mark 9:46')],
    ('wlc', '65', '1'): [('remove', 'John 1:16'), ('remove', 'Ephesians 3:16-19'),
                         ('remove', 'Philippians 3:10'), ('remove', 'Romans 6:5-6')],
    ('wlc', '66', '1'): [('add', 'John 1:16'), ('add', 'Ephesians 3:16-19'),
                         ('add', 'Philippians 3:10'), ('add', 'Romans 6:5-6')],
    ('wlc', '73', '3'): [('remove', 'Galatians 2:16')],
    ('wlc', '83', '4'): [('replace', 'Mark 9:43-45', 'Mark 9:44')],
    ('wlc', '99', '3'): [('remove', 'Proverbs 1:19')],
    ('wlc', '99', '7'): [('add_after', 'Exodus 20:7', 'Jeremiah 18:7-8')],
    ('wlc', '105', '43'): [('add', 'Luke 12:19')],
    ('wlc', '113', '32'): [('replace', 'Matthew 23:13-15', 'Matthew 23:14')],
    ('wlc', '117', '5'): [('add_after', 'Luke 23:56', 'Luke 23:54')],
    ('wlc', '121', '2'): [('add_after', 'Luke 23:56', 'Luke 23:54')],
    ('wlc', '140', '1'): [('add', 'Exodus 20:15')],
    ('wlc', '145', '3'): [('add', 'Proverbs 6:19')],
    ('wlc', '157', '1'): [('add_after', 'Exodus 24:7', 'Psalm 19:10')],
    ('wlc', '162', '3'): [('add', 'Exodus 12:48')],
    ('wlc', '179', '9'): [('replace', 'Isaiah 46', 'Isaiah 46:9')],
}


def apply_ops(refs, ops, context):
    refs = list(refs)
    problems = []
    for op in ops:
        if op[0] == 'replace':
            _, old, new = op
            if old in refs:
                refs[refs.index(old)] = new
            else:
                problems.append(f'{context}: replace target {old!r} not found in {refs}')
        elif op[0] == 'remove':
            _, ref = op
            if ref in refs:
                refs.remove(ref)
            else:
                problems.append(f'{context}: remove target {ref!r} not found in {refs}')
        elif op[0] == 'add':
            if op[1] not in refs:
                refs.append(op[1])
        elif op[0] == 'add_after':
            _, ref, anchor = op
            if ref in refs:
                continue
            if anchor in refs:
                refs.insert(refs.index(anchor) + 1, ref)
            else:
                problems.append(f'{context}: add_after anchor {anchor!r} not found; appended')
                refs.append(ref)
    return refs, problems


def main():
    staged = {}
    manifest = []
    all_problems = []
    seen = set()

    for data_path in sorted(CONTENT.glob('*/*/data.json')):
        day = f'{data_path.parent.parent.name}-{data_path.parent.name}'
        data = json.loads(data_path.read_text())
        for item in data.get('content_with_prooftexts', []):
            if item.get('type') != 'catechism':
                continue
            abbv, num = item.get('abbv'), str(item.get('number'))
            for fn in list(item.get('prooftexts', {})):
                key = (abbv, num, fn)
                if key not in FIXES:
                    continue
                current = re.findall(r'<h5>(.*?)</h5>', item['prooftexts'][fn])
                new_refs, problems = apply_ops(current, FIXES[key],
                                               f'{day} {abbv.upper()} {num} [{fn}]')
                all_problems.extend(problems)
                staged.setdefault(day, {})[f'{abbv.upper()} {num}|{fn}'] = {
                    'refs': new_refs, 'esv': None}
                manifest.append({'day': day, 'unit': f'{abbv.upper()} {num}',
                                 'n': int(fn), 'refs': new_refs})
                seen.add(key)

    missing = set(FIXES) - seen
    out = HERE / 'staged'
    out.mkdir(exist_ok=True)
    (out / 'catechism-changes.json').write_text(json.dumps(staged, indent=1))
    (out / 'catechism-fetch-manifest.json').write_text(json.dumps(manifest, indent=1))

    print(f'{len(manifest)} group applications staged across '
          f'{len(staged)} days ({len(seen)} of {len(FIXES)} fixes found)')
    if missing:
        print('FIXES NOT FOUND:', sorted(missing))
    if all_problems:
        print('PROBLEMS:')
        for p in all_problems:
            print(' ', p)


if __name__ == '__main__':
    main()
