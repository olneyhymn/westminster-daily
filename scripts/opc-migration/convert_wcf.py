#!/usr/bin/env python3
"""Convert WCF daily data.json items from the traditional apparatus to the
OPC apparatus (scripts/opc-migration/opc-wcf.json).

Dry-run by default: prints stats and writes staged changes + fetch manifest to
scripts/opc-migration/staged/. Nothing in content/ is modified until apply.

Strategy per confession item (chapter.paragraph):
- Keep OUR body text verbatim; anchor each OPC marker position into it by
  matching the words preceding the marker in the OPC text.
- Rebuild <sup> markers at anchored positions, renumbered 1..n per paragraph.
- For each new footnote group: if its normalized ref-set equals one of the old
  groups' ref-sets, reuse that group's ESV HTML; otherwise add to the fetch
  manifest (ESV API call needed).
- OPC "See"/"Cf." cross-refs and note-only footnotes are dropped (consistent
  with the catechisms' existing convention); dropped content is logged.
"""

import html
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
CONTENT = ROOT / 'content'

SUP_RE = re.compile(r"<sup id='fnref:wcf\d+'>.*?</sup>", re.S)
PARA_NUM_RE = re.compile(r'<span class="paragraph-number">(\d+)\.</span>\s*')


def norm_ref(ref):
    ref = ref.replace('–', '-').replace('—', '-')
    ref = re.sub(r'\s+', ' ', ref).strip()
    ref = ref.replace('Psalms ', 'Psalm ')
    return ref


def norm_refset(refs):
    return tuple(sorted(norm_ref(r) for r in refs))


def norm_for_anchor(s):
    """Aggressive normalization for anchor matching."""
    s = html.unescape(s)
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', '', s)
    return s


def build_charmap(text):
    """Map normalized-char index -> original index for `text`."""
    mapping = []
    for i, ch in enumerate(html.unescape(text).lower()):
        if re.match(r'[a-z0-9]', ch):
            mapping.append(i)
    return mapping


def anchor_positions(our_plain, opc_text):
    """Return original-text insertion offsets for each OPC marker, or None per
    marker on failure."""
    segments = re.split(r'\{\d+\}', opc_text)
    unescaped = html.unescape(our_plain)
    norm_target = norm_for_anchor(our_plain)
    charmap = build_charmap(our_plain)
    positions = []
    search_from = 0
    for seg in segments[:-1]:
        found = None
        words = seg.split()
        for k in (8, 6, 4, 3):
            anchor = norm_for_anchor(' '.join(words[-k:]))
            if not anchor:
                continue
            idx = norm_target.find(anchor, search_from)
            if idx == -1:
                continue
            end_norm = idx + len(anchor) - 1
            orig = charmap[end_norm] + 1
            # advance past trailing punctuation/quotes so the sup lands after them
            while orig < len(unescaped) and unescaped[orig] in ';:,.!?)’”':
                orig += 1
            found = orig
            search_from = end_norm
            break
        positions.append(found)
    return positions


def sup_html(n):
    return (f"<sup id='fnref:wcf{n}'><a href='#fn:wcf{n}' rel='footnote' "
            f"style='text-decoration: none;'>{n}</a></sup>")


def main():
    opc = json.loads((HERE / 'opc-wcf.json').read_text())

    stats = {'items': 0, 'anchored': 0, 'anchor_fail': 0,
             'groups_total': 0, 'groups_reused': 0, 'groups_fetch': 0,
             'markers_dropped': 0}
    staged = {}
    manifest = []
    dropped = []
    failures = []

    for data_path in sorted(CONTENT.glob('*/*/data.json')):
        day = f'{data_path.parent.parent.name}-{data_path.parent.name}'
        data = json.loads(data_path.read_text())
        for item in data.get('content_with_prooftexts', []):
            if item.get('type') != 'confession' or item.get('abbv') != 'wcf':
                continue
            ch, para = str(item['chapter']), str(item['paragraph'])
            unit = f'{ch}.{para}'
            opc_para = opc.get(ch, {}).get('paragraphs', {}).get(para)
            if not opc_para:
                failures.append(f'{day} {unit}: no OPC paragraph')
                continue
            stats['items'] += 1

            body = item['body']
            m = PARA_NUM_RE.match(body)
            prefix = m.group(0) if m else ''
            plain = SUP_RE.sub('', body[len(prefix):])

            # Select OPC footnotes: drop note-only; renumber survivors
            new_groups = []
            for n in sorted(opc_para['footnotes'], key=int):
                fn = opc_para['footnotes'][n]
                if fn.get('note') and not fn['refs']:
                    dropped.append(f'{unit} marker {n}: {fn["note"]}')
                    stats['markers_dropped'] += 1
                    new_groups.append(None)  # keep index alignment with markers
                else:
                    new_groups.append(fn)

            positions = anchor_positions(plain, opc_para['text'])
            if any(p is None for p in positions):
                bad = [i + 1 for i, p in enumerate(positions) if p is None]
                failures.append(f'{day} {unit}: anchor failed for markers {bad}')
                stats['anchor_fail'] += 1
                continue
            stats['anchored'] += 1

            # Build new body: insert sups at positions (descending), renumber
            unescaped = html.unescape(plain)
            keep = [(pos, g) for pos, g in zip(positions, new_groups) if g is not None]
            inserts = []
            for new_n, (pos, g) in enumerate(keep, 1):
                inserts.append((pos, new_n, g))
            new_body = unescaped
            for pos, new_n, _ in sorted(inserts, key=lambda t: -t[0]):
                new_body = new_body[:pos] + sup_html(new_n) + new_body[pos:]
            new_body = prefix + new_body

            # Old groups by normalized ref-set (for ESV reuse)
            old_by_refset = {}
            old_prooftexts = item.get('prooftexts', {})
            # ours-wcf refs per group come from parsing h5s; reproduce cheaply:
            for k, esv_html in old_prooftexts.items():
                refs = re.findall(r'<h5>(.*?)</h5>', esv_html)
                old_by_refset[norm_refset(refs)] = esv_html

            groups_out = {}
            for pos, new_n, g in inserts:
                stats['groups_total'] += 1
                refs = [norm_ref(r) for r in g['refs']]
                key = norm_refset(refs)
                if key in old_by_refset:
                    stats['groups_reused'] += 1
                    groups_out[str(new_n)] = {'refs': refs, 'esv': old_by_refset[key]}
                else:
                    stats['groups_fetch'] += 1
                    groups_out[str(new_n)] = {'refs': refs, 'esv': None}
                    manifest.append({'day': day, 'unit': unit, 'n': new_n, 'refs': refs})

            staged.setdefault(day, {})[unit] = {
                'new_body': new_body,
                'groups': groups_out,
            }

    out = HERE / 'staged'
    out.mkdir(exist_ok=True)
    (out / 'wcf-changes.json').write_text(json.dumps(staged, indent=1))
    (out / 'fetch-manifest.json').write_text(json.dumps(manifest, indent=1))
    (out / 'dropped-notes.json').write_text(json.dumps(dropped, indent=1))

    print(json.dumps(stats, indent=1))
    if failures:
        print(f'{len(failures)} FAILURES:')
        for f in failures[:30]:
            print(' ', f)
    total_fetch_refs = sum(len(m['refs']) for m in manifest)
    print(f'fetch manifest: {len(manifest)} groups, {total_fetch_refs} refs')


if __name__ == '__main__':
    main()
