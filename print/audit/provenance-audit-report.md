# Westminster Daily Proof-Text Audit — Corrected Report (v2)

**Date:** 2026-07-14
**Supersedes:** `opc-audit-report.md` (v1), whose WCF findings used the wrong yardstick.

---

## 1. The provenance discovery

The v1 audit compared everything against the OPC's proof-text PDFs and concluded our
data followed "a traditional edition" throughout. Investigating Tim's recollection that
the data was built from OPC sources revealed the truth: **the data has mixed lineage.**

| Document | Source lineage | Evidence |
|---|---|---|
| WCF | Traditional/1647 apparatus | Fingerprints (Ps 19:1–3, no John 17:3, Prov 22:19–21, 1 John 5:7 at 2.3) match the 1647 "humble advice" apparatus exactly; both OPC PDF editions (2005 and current) differ at every one of these points |
| WSC | OPC revised apparatus | Q1 matches OPC SCLayout.pdf verbatim, both footnotes, all 12 refs |
| WLC | OPC revised apparatus | Q1 matches OPC LCLayout.pdf verbatim, both footnotes, all 9 refs |

Repo history is consistent: WCF proofs entered Dec 20, 2015 (`c54e02c`); WSC proofs
Jan 13, 2016 (`ad5a7d7`) — different sessions, evidently different sources. The About
page's blanket attribution to OPC is accurate only for the catechisms.

Consequently:
- The v1 "27 confirmed WCF typos" are **retracted** — they were OPC readings measured
  against our traditional apparatus (e.g., our Ps 19:1–3 is the correct 1647 reading).
- The v1 "edition difference" bucket (727 raw WCF findings) is explained and closed.
- The catechism findings from v1 were measured against the right yardstick and are
  adjudicated below.

## 2. Method (v2)

- **WCF:** mechanically diffed against Creeds.json's 1647 transcription (machine-readable,
  same apparatus family) after canonicalizing references in code. 474→49 candidate rows.
- **Catechisms:** re-used the v1 audit's per-unit extractions from the OPC PDFs (44
  candidate findings).
- All 93 candidates adjudicated by three Opus reviewers testing each disputed verse
  against the clause its footnote supports, with targeted PDF page re-reads for the
  doubtful catechism items.
- Total model spend: ~215K tokens (v1: ~6M).

## 3. Confirmed corrections — Westminster Confession (8)

All judged by which verse actually supports the clause:

| Ref | Fix | Why |
|---|---|---|
| WCF 10.2 fn3 | Ezekiel 36:**37** → 36:**27** | "Spirit put within you" (effectual calling) |
| WCF 16.7 fn5 | Titus 3:**15** → 3:**5** | "not by works of righteousness" |
| WCF 19.2 fn1 | Exodus **24:1** → **34:1** | hewing the two tables of the law |
| WCF 21.3 fn2 | Psalm 65:**6** → 65:**2** | "O thou that hearest prayer" |
| WCF 21.3 fn6 | Genesis **17:27** → **18:27** | Abraham's "dust and ashes" humility in prayer |
| WCF 27.1 fn3 | Galatians 3:**17** → 3:**27** | "baptized into Christ… put on Christ" |
| WCF 30.1 fn1 | Acts 20:**18** → 20:**28** | "overseers, to feed the church of God" |
| WCF 33.3 fn1 | Luke 21:**7** → 21:**27** | "Son of man coming in a cloud" |

The remaining 41 WCF rows: 7 typos in the *yardstick* transcription (ours correct,
e.g., Mark 14:23, 1 Tim 2:5), 16 representation artifacts, 18 edition variants
(concentrated in the American-revision chapters 20, 22–24, 31, 33).

## 4. Confirmed corrections — Catechisms (18 distinct)

Verified against the OPC PDFs (our catechisms' source):

**Wrong verse:**
- WSC 9 fn1: Psalm 33:**19** → 33:**9** ("he spake, and it was done")
- WLC 29 fn1: Mark 9:43, 45–47, 48 → Mark 9:**43–44, 46, 48** (KJV "worm" refrain verses)
- WLC 83 fn4: Mark 9:43–45 → Mark 9:**44**
- WLC 113 fn32: Matthew 23:**13–15** → 23:**14**
- WLC 179 fn9: Isaiah 46 → Isaiah **46:9**

**Dropped references (add):**
- WSC 75 fn1: Ephesians 4:28; 2 Thessalonians 3:10; 1 Timothy 5:8
- WLC 4 fn1: 1 Corinthians 2:13 · WLC 99 fn7: Exodus 20:7 · WLC 105 fn43: Luke 12:19
- WLC 117 fn5 and WLC 121 fn2: Luke 23:56 · WLC 140 fn1: Exodus 20:15
- WLC 145 fn3: Proverbs 6:19 · WLC 157 fn1: Exodus 24:7 · WLC 162 fn3: Exodus 12:48

**Spurious references (remove):**
- WLC 25 fn3: Romans 3:23 · WLC 73 fn3: Galatians 2:16 · WLC 99 fn3: Proverbs 1:19

**Misfiled block:**
- WLC 65 fn1 → WLC 66 fn1: John 1:16; Ephesians 3:16–19; Philippians 3:10; Romans 6:5–6

Not errors: 5 notation-only differences (OPC "See"/"ff."/"Psalm 92 title" conventions;
plus one OPC misprint — "Ps. 26:4" for Isaiah 26:4 at WLC 104 — that our data already
has right). 12 of the 44 v1 findings were reporter errors caused by footnotes
continuing across PDF page breaks.

## 5. Recommendations

1. **Apply the 26 corrections** (8 WCF + 18 catechism). Changed/added references need
   ESV text re-fetched (API key required). Removals and the Q65/Q66 refile need no fetch.
2. **Fix the About page**: proofs for the *catechisms* follow the OPC edition; proofs
   for the *Confession* follow the traditional (1647/American) apparatus. Same note in
   the print book's front matter.
3. **Regression test**: freeze the corrected reference set (normalized) and diff in CI
   so future edits can't silently alter references.
4. Print book impact: one curated passage is affected — Ephesians 3:16–19 (printed
   Oct 20) moves from WLC 65 fn1 to WLC 66 fn1 in the refile, so
   `print/curation/10.json` needs a matching update (the build's mismatch check will
   flag it). Five other corrections change citation lists on days with printed
   passages but leave the printed passages themselves untouched. Rebuild after fixes.
