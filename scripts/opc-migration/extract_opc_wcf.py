#!/usr/bin/env python3
"""Extract the OPC proof-text apparatus for the Westminster Confession from
CFLayout.pdf using font-size classification (10pt body, 8pt footnotes,
12pt headings, <7.5pt superscript markers).

Produces opc-wcf.json:
  { "<chapter>": {
      "title": str,
      "paragraphs": { "<n>": {"text": str-with-{letter}-markers, "markers": [...] } },
      "footnotes": { "<letter>": {"refs": [...], "see_refs": [...]} } } }
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar, LTTextContainer, LTTextLine

ABBREV = {
    'Gen': 'Genesis', 'Ex': 'Exodus', 'Exod': 'Exodus', 'Lev': 'Leviticus',
    'Num': 'Numbers', 'Deut': 'Deuteronomy', 'Josh': 'Joshua', 'Judg': 'Judges',
    'Ruth': 'Ruth', 'Sam': 'Samuel', 'Kings': 'Kings', 'Chron': 'Chronicles',
    'Ezra': 'Ezra', 'Neh': 'Nehemiah', 'Esth': 'Esther', 'Job': 'Job',
    'Ps': 'Psalm', 'Prov': 'Proverbs', 'Eccl': 'Ecclesiastes',
    'Song': 'Song of Solomon', 'Isa': 'Isaiah', 'Jer': 'Jeremiah',
    'Lam': 'Lamentations', 'Ezek': 'Ezekiel', 'Dan': 'Daniel', 'Hos': 'Hosea',
    'Joel': 'Joel', 'Amos': 'Amos', 'Obad': 'Obadiah', 'Jonah': 'Jonah',
    'Mic': 'Micah', 'Nah': 'Nahum', 'Hab': 'Habakkuk', 'Zeph': 'Zephaniah',
    'Hag': 'Haggai', 'Zech': 'Zechariah', 'Mal': 'Malachi', 'Matt': 'Matthew',
    'Mark': 'Mark', 'Luke': 'Luke', 'John': 'John', 'Acts': 'Acts',
    'Rom': 'Romans', 'Cor': 'Corinthians', 'Gal': 'Galatians',
    'Eph': 'Ephesians', 'Phil': 'Philippians', 'Col': 'Colossians',
    'Thess': 'Thessalonians', 'Tim': 'Timothy', 'Titus': 'Titus',
    'Philem': 'Philemon', 'Heb': 'Hebrews', 'James': 'James', 'Jas': 'James',
    'Pet': 'Peter', 'Jude': 'Jude', 'Rev': 'Revelation',
}
BOOK_PAT = '|'.join(sorted(ABBREV, key=len, reverse=True))
REF_RE = re.compile(
    rf'(See\s+|Cf\.\s+)?'
    rf'((?:[1-3]\s)?(?:{BOOK_PAT}))\.?\s'
    rf'(\d+(?::\d+)?(?:[–-]\d+(?::\d+)?)?(?:,\s*\d+(?:[–-]\d+)?)*)'
)
FOOTNOTE_START = re.compile(r"^([a-z][′’']?)\.\s+(.+)$")
CHAPTER_RE = re.compile(r'^Chapter\s+(\d+)$')
PARA_START = re.compile(r'^(\d+)\.\s+(.*)$')
RUNNING_HEAD = re.compile(r'^(the\s+)?confession of faith$|^chapter\s+\d+$|^\d+$', re.I)


def line_pieces(line):
    """Return (text_with_markers, dominant_size). Superscript chars (<7.5pt)
    become {x} placeholders."""
    sizes = Counter()
    out = []
    marker_buf = []
    for ch in line:
        if not isinstance(ch, LTChar):
            if marker_buf:
                out.append('{' + ''.join(marker_buf) + '}')
                marker_buf = []
            out.append(ch.get_text() if hasattr(ch, 'get_text') else ' ')
            continue
        c = ch.get_text()
        if ch.size < 7.5 and c.strip():
            marker_buf.append(c)
            continue
        if marker_buf:
            out.append('{' + ''.join(marker_buf) + '}')
            marker_buf = []
        sizes[round(ch.size)] += 1
        out.append(c)
    if marker_buf:
        out.append('{' + ''.join(marker_buf) + '}')
    text = re.sub(r'\s+', ' ', ''.join(out)).strip()
    dom = sizes.most_common(1)[0][0] if sizes else 0
    return text, dom


def normalize_refs(refstr, book):
    refstr = refstr.replace('–', '-').replace('—', '-')
    out = []
    chapter = None
    for piece in refstr.split(','):
        piece = piece.strip()
        if not piece:
            continue
        if ':' in piece:
            chapter = piece.split(':')[0].split('-')[0]
            out.append(f'{book} {piece}')
        elif chapter is not None:
            out.append(f'{book} {chapter}:{piece}')
        else:
            out.append(f'{book} {piece}')
    return out


def parse_refs(text):
    """All concrete Scripture refs in print order. See/Cf cross-references ARE
    included — the original OPC-derived catechism data carries them (verified
    against SCLayout/LCLayout: WSC 91, WLC 116, WLC 174), so the WCF must too.
    Only non-Scripture notes ('See chapter 5, section 4') yield no refs."""
    refs = []
    for m in REF_RE.finditer(text):
        raw_book, verses = m.group(2), m.group(3)
        parts = raw_book.split()
        book = f'{parts[0]} {ABBREV[parts[1]]}' if len(parts) == 2 else ABBREV[parts[0]]
        refs.extend(normalize_refs(verses, book))
    return refs, []


def main():
    pdf = sys.argv[1]
    chapters = {}
    chapter = None
    title_pending = False
    para = None
    body_parts = {}
    markers_seq = []   # (chapter, para, letter) in document order
    footnotes_seq = [] # [letter, [text pieces]] in document order

    lines = []
    for page in extract_pages(pdf):
        page_lines = []
        for el in page:
            if isinstance(el, LTTextContainer):
                for line in el:
                    if isinstance(line, LTTextLine):
                        text, size = line_pieces(line)
                        if text:
                            page_lines.append((line.y0, line.x0, text, size))
        # reading order: top to bottom
        page_lines.sort(key=lambda t: (-t[0], t[1]))
        for _, _, text, size in page_lines:
            lines.append((text, size))

    for text, size in lines:
        # running heads/folios are small; never confuse with 12pt "Chapter N" headings
        if size < 11 and RUNNING_HEAD.match(text.strip()):
            continue
        if size >= 11:
            m = CHAPTER_RE.match(text)
            if m:
                chapter = m.group(1)
                chapters[chapter] = {'title': '', 'paragraphs': {}}
                title_pending = True
                para = None
                fn_letter = None
            elif title_pending and chapter:
                chapters[chapter]['title'] = text
                title_pending = False
            continue
        if chapter is None:
            continue
        if size >= 9:  # body
            pm = PARA_START.match(text)
            if pm:
                para = pm.group(1)
                body_parts.setdefault((chapter, para), []).append(pm.group(2))
            elif para is not None:
                body_parts[(chapter, para)].append(text)
            for mk in re.findall(r'\{([^}]+)\}', text):
                markers_seq.append((chapter, para, mk.replace('’', "'").replace('′', "'")))
        else:  # footnote (8pt)
            fm = FOOTNOTE_START.match(text)
            if fm and (REF_RE.match(fm.group(2)) or fm.group(2).startswith(('See', 'Cf.'))):
                letter = fm.group(1).replace('’', "'").replace('′', "'")
                footnotes_seq.append([letter, [fm.group(2)]])
            elif footnotes_seq:
                footnotes_seq[-1][1].append(text)

    # Pair markers and footnotes by document order; letters are the checksum
    if len(markers_seq) != len(footnotes_seq):
        print(f'WARNING: {len(markers_seq)} markers vs {len(footnotes_seq)} footnote blocks')
    mismatches = [
        (i, mk, fn[0]) for i, (mk, fn) in enumerate(zip(
            [m[2] for m in markers_seq], footnotes_seq)) if mk != fn[0]
    ]
    if mismatches:
        print(f'WARNING: {len(mismatches)} letter mismatches, first: {mismatches[:5]}')

    # Renumber per paragraph: markers become {1},{2},... and footnotes key 1..n
    per_para_count = {}
    assignments = {}  # global marker index -> (ch, para, number)
    for i, (ch, para, letter) in enumerate(markers_seq):
        n = per_para_count.get((ch, para), 0) + 1
        per_para_count[(ch, para)] = n
        assignments[i] = (ch, para, n)

    for (ch, para), pieces in body_parts.items():
        text = re.sub(r'\s+', ' ', ' '.join(pieces)).strip()
        # replace {letter} occurrences left-to-right with per-paragraph numbers
        idxs = [i for i, (c, p, _) in enumerate(markers_seq) if (c, p) == (ch, para)]
        it = iter(idxs)
        text = re.sub(r'\{[^}]+\}', lambda m: '{%d}' % assignments[next(it)][2], text)
        chapters[ch]['paragraphs'][para] = {
            'text': text,
            'footnotes': {},
        }
    for i, (letter, pieces) in enumerate(footnotes_seq):
        if i not in assignments:
            continue
        ch, para, n = assignments[i]
        blob = ' '.join(pieces)
        refs, see_refs = parse_refs(blob)
        entry = {'letter': letter, 'refs': refs, 'see_refs': see_refs}
        if not refs and not see_refs:
            # internal cross-reference, e.g. "See chapter 5, section 4."
            entry['note'] = blob.strip()
        chapters[ch]['paragraphs'].setdefault(para, {'text': '', 'footnotes': {}})
        chapters[ch]['paragraphs'][para]['footnotes'][str(n)] = entry

    out = Path(__file__).parent / 'opc-wcf.json'
    out.write_text(json.dumps(chapters, indent=1))

    problems = []
    total_markers = total_refs = 0
    for ch, data in sorted(chapters.items(), key=lambda kv: int(kv[0])):
        for para, pdata in sorted(data['paragraphs'].items(), key=lambda kv: int(kv[0])):
            n_mk = len(re.findall(r'\{\d+\}', pdata['text']))
            n_fn = len(pdata['footnotes'])
            empty = [k for k, f in pdata['footnotes'].items()
                     if not f['refs'] and not f['see_refs'] and not f.get('note')]
            if n_mk != n_fn or empty:
                problems.append(f'{ch}.{para}: {n_mk} markers vs {n_fn} footnotes, empty {empty}')
            total_markers += n_mk
            total_refs += sum(len(f['refs']) for f in pdata['footnotes'].values())
    print(f'{len(chapters)} chapters, {total_markers} markers, {total_refs} refs')
    if problems:
        print('PROBLEMS:')
        for p in problems:
            print(' ', p)
    else:
        print('All paragraphs align.')


if __name__ == '__main__':
    main()
