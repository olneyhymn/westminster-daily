> **SUPERSEDED (2026-07-14):** This report's WCF findings used the wrong yardstick
> (our WCF follows the traditional/1647 apparatus, not OPC's). See
> `provenance-audit-report.md` for the corrected audit.

# Westminster Daily Proof-Text Audit

**Source of truth:** OPC official proof-text editions (CFLayout.pdf / SCLayout.pdf / LCLayout.pdf, opc.org)
**Our data:** `content/*/*/data.json` (drives westminsterdaily.com and the print book)
**Date:** 2026-07-14

---

## 1. Executive summary

Our proof-text data is broadly accurate. Of **474 doctrinal units** compared, **297 (63%)** matched the OPC edition cleanly after normalization (abbreviations, verse ranges, list-style citations, and "See" cross-references all treated as equivalent).

The **399 raw discrepancies** flagged fall into two very different buckets, and the distinction is the central finding of this audit:

1. **A systematically different proof-text edition (the large majority).** Our data follows the **traditional American Presbyterian proof-text set** (the fuller/original Westminster proofs), while the OPC PDFs reproduce the **OPC's own revised apparatus**. The OPC editorial committee re-selected proof texts throughout: adding "See" cross-references, dropping the disputed Johannine Comma (1 John 5:7), substituting whole references (e.g. Luke 17:10 for Job 22:2-3 at WCF 2.2), and re-grouping texts across adjacent sections. These are **not errors in our data** — they are two legitimately different published editions. The evidence for this is strong and repeated: the divergences are bidirectional (we carry texts OPC lacks *and* lack texts OPC carries), they involve whole coherent proof texts rather than single-digit slips, and they cluster by clause in a way that tracks known editorial revisions.

2. **A small set of genuine transcription errors in our data (actionable).** These are one-verse or one-reference slips against an otherwise-matching footnote — a dropped end verse (Ps 19:1-**3** vs 19:1-**4**), a dropped opening reference (John 17:3), a transposed digit (Job 34:**10** vs 34:**20**). These we should fix. See Section 2.

**Verdict:** Trust the data. The overwhelming majority of the noise is an edition difference, not inaccuracy. There is a short, well-bounded list of true typos worth correcting, and a decision to make about whether to *state* which edition we follow (recommended — see Section 5).

---

## 2. Confirmed likely data errors (actionable)

These were verified adversarially against the OPC PDFs and classified as **transcription slips** — a single reference or verse off from an otherwise-aligned footnote. All are in the Westminster Confession of Faith (WCF). Recommended action is to correct our `data.json` to match, since these are almost certainly our own typos rather than a genuine edition variant.

| Unit | Fn | Ours | OPC (correct) | Recommended action |
|------|----|------|---------------|--------------------|
| WCF 1.1 | 1 | Psalm 19:1-3 | Psalm 19:1-4 | Extend end verse to 4 |
| WCF 1.1 | 2 | (absent) | John 17:3 | Add John 17:3 (opens the footnote) |
| WCF 1.2 | 1 | 2 Timothy 3:16 | 2 Timothy 3:15-16 | Widen range to 3:15-16 |
| WCF 1.4 | 1 | (absent) | Revelation 1:1-2 | Add Rev 1:1-2 (closes the footnote) |
| WCF 1.6 | 1 | 2 Timothy 3:15-17 | 2 Timothy 3:16-17 | Fix start verse to 16 |
| WCF 1.8 | 1 | (absent) | Psalm 119:89 | Add Ps 119:89 |
| WCF 1.9 | 1 | Acts 15:15-16 | Acts 15:15 | Drop v16 |
| WCF 1.9 | 1 | (absent) | John 5:46 | Add John 5:46 |
| WCF 2.1 | 1 | (absent) | Galatians 3:20 | Add "See Gal. 3:20" |
| WCF 2.1 | 5 | (absent) | John 1:18 | Add "See John 1:18" |
| WCF 2.1 | 11 | (absent) | Romans 11:34 | Add "See Rom. 11:34" |
| WCF 2.1 | 16 | Exodus 3:14 only | Isaiah 45:5-6 + Exodus 3:14 | Add primary proof Isa 45:5-6 |
| WCF 2.1 | 19 | (absent) | John 3:16 | Add John 3:16 |
| WCF 2.1 | 24 | Nahum 1:2-3 | Nahum 1:2-3, 6 | Add v6 |
| WCF 2.2 | 1 | John 5:26 only | Jeremiah 10:10 + John 5:26 | Add primary proof Jer 10:10 |
| WCF 3.3 | 1 | Matthew 25:41 | Matthew 25:31, 41 | Add v31 |
| WCF 3.3 | 1 | (absent) | Jude 6 | Add Jude 6 |
| WCF 3.5 | 1 | Romans 8:30 | Romans 8:28-30 | Widen range to 8:28-30 |
| WCF 3.5 | 2 | (missing 3 refs) | + Rom 9:15, Eph 2:8-9, Eph 1:5 | Add the three refs; fn2 shows corruption signs |
| WCF 3.8 | 2 | 2 Peter 1:10 only | + 1 Thessalonians 1:4-5 | Add 1 Thess 1:4-5 |
| WCF 5.3 | 1 | Acts 27:31, 27:44 | + Acts 27:24 | Add Acts 27:24 (opens the series) |
| WCF 5.3 | 2 | Job 34:10 | Job 34:20 | Fix verse (transposed digit) |
| WCF 5.7 | 1 | (absent) | Matthew 16:18 | Add Matt 16:18 |
| WCF 6.2 | 2 | Ephesians 2:1 | Ephesians 2:1-3 | Widen range to 2:1-3 |
| WCF 6.2 | 3 | Romans 3:10-18 | Romans 3:10-19 | Fix end verse to 19 |
| WCF 6.5 | 1 | Romans 7:23 | Romans 7:21-23 | Widen range to 7:21-23 |
| WCF 7.5 | 4 | Galatians 3:7-9, 14 | + Psalm 32:1-2, 32:5 | Add the Psalm 32 references |

**Notes on two of these:**
- **WCF 2.1 fn16** and **WCF 2.2 fn1** show the same signature: our data kept the OPC *cross-reference* ("See X") but dropped the *primary* proof text. A genuine alternate edition would carry the primary proof, so these read as slips, not edition choices.
- **WCF 3.5 fn2** is the one entry classified as likely-error despite involving three missing refs — the surrounding footnotes align cleanly with OPC and fn2 alone shows corruption (has Rom 9:16 but not 9:15; carries a misplaced Eph 1:4 that belongs to fn1; drops the whole Eph 2:8-9 citation). Worth a manual look.

---

## 3. Edition differences (not errors — summarized by pattern)

The bulk of flagged discrepancies are the OPC's revised proof-text apparatus diverging from the traditional set our data follows. Rather than enumerate all of them, here are the recurring patterns with representative examples.

### Pattern A — OPC adds "See ..." cross-references we don't carry
The OPC edition systematically supplements primary proofs with "See" cross-references. Our (traditional) edition often carries only the primary proof.
- WCF 2.1 runs this throughout: fn18 ("See Rev. 4:11"), fn3 ("See Ps. 139:6"), fn2 ("See Gal. 3:20") all present in OPC, absent in ours.
- WCF 3.4 fn1 omits the entire OPC "See John 10:14-16, 27-28; 17:2, 6, 9-12" block.

### Pattern B — Whole-reference substitutions
Same clause, different proof text — both legitimate historic proofs.
- **WCF 2.2 fn6:** ours Job 22:2-3 vs OPC Luke 17:10 ("we are unprofitable servants"). (This footnote was flagged extra-in-ours but is actually a substitution — OPC's fn is not empty.)
- **WCF 5.6 fn4/fn5:** ours Deut 2:30 / Ps 81:11-12 vs OPC Gen 4:8 / Ps 109:6 + Luke 22:3 — the classic original-Westminster proofs vs OPC's revision.
- **WCF 5.4 fn2:** ours Acts 14:16 vs OPC John 12:40 + 2 Thess 2:11.

### Pattern C — The Johannine Comma
- **WCF 2.3 fn1:** ours includes **1 John 5:7** (the text-critically disputed Comma) as a Trinity proof; the modern OPC edition omits it. A hallmark old-edition vs modern-edition difference.

### Pattern D — Cross-section regrouping
The two editions assign the same texts to adjacent sections differently.
- **WCF 1.2 / 1.3:** Luke 24:27,44 and Rev 22:18-19 sit in different paragraphs between the editions.

### Pattern E — Fuller vs leaner sets / range width
Our traditional set is sometimes fuller, sometimes leaner, and often cites narrower verse ranges.
- **WCF 1.1 fn6, 1.5 fn2, 1.8 fn4:** OPC carries several additional proofs; ours is leaner.
- **WCF 3.1, 6.3, 7.1, 7.4:** ours carries extra traditional proofs OPC dropped (e.g. Rom 11:33 / 9:15 / 9:18 at 3.1; Gen 1:27-28, 2:16-17, 1 Cor 15:45 at 6.3).
- **WCF 4.2 fn7, 5.5 fn2, 8.4 fn5:** ours cites cherry-picked verses where OPC gives a continuous range (e.g. ours Ps 77:1,10,12 vs OPC 77:1-12; ours "Matthew 26-27" vs OPC "Matt. 26:67-68, 27:27-50").

These patterns repeat across WCF chapters 1-10 and are the reason a raw diff looks alarming while the underlying data is sound.

---

## 4. Coverage & method

- **Units total:** 474
- **Clean after normalization:** 297 (63%)
- **Units with ≥1 flagged discrepancy:** 177
- **Raw findings:** 399
- **Adversarially verified:** 90
  - **Confirmed:** 89
  - **Refuted / modified:** 1 (WCF 2.2 fn6 — reported as extra-in-ours, actually a substitution; OPC's footnote was not empty)
- **Not individually verified:** 309 (a representative sample was spot-checked; see below)

**Method.** Each unit's footnotes were extracted from `data.json` and aligned letter-by-letter to the OPC PDF footnotes (accounting for the OPC's skipped letter "j"). References were normalized for abbreviation, verse-range dash style, comma-list style, and "See/Cf." cross-reference prefixes before comparing, so only genuine content differences were flagged. Verified findings were re-checked directly against the PDF page images, including reading the quoted proof-text prose to disambiguate verse boundaries (this is how e.g. Job 34:**20** vs **10** and Rom 8:28-**39** vs reported 28-30 were caught).

**What was sampled rather than fully verified.** The 309 unverified findings are concentrated in WCF chapters 8-10 and beyond and in the catechisms (SC/LC). Spot-checks of that tail (WCF 7.6, 8.x, 9.x, 10.1 in the sample) show the **same two-bucket split** — overwhelmingly edition differences (Pattern A-E above), with occasional one-verse slips of the kind in Section 2. The unverified tail is therefore expected to contain a modest number of additional true errors of the same character, but no evidence of a different underlying problem.

---

## 5. Recommendations

1. **Fix the confirmed transcription errors in Section 2.** These 27 items (all WCF ch. 1-7) are almost certainly our own typos. Correcting them is low-risk and improves fidelity regardless of which edition we claim to follow. Prioritize the ones that drop a *primary* proof (WCF 2.1 fn16, 2.2 fn1, 3.3 Jude 6, 5.7 Matt 16:18) since those omit real content, over the range-width tweaks.

2. **Do not "correct" the edition differences.** They are not wrong. Mechanically conforming our data to the OPC PDF would erase the traditional American Presbyterian proof-text set our edition preserves — including the Johannine Comma and the fuller original proofs — which many users may specifically want.

3. **Decide and document which edition we follow.** The strongest single improvement is a short note on the site's about/reading-plan page and in the print book's front matter stating that our proof texts follow the **traditional (original/American) Westminster proof-text set**, and that the OPC's modern edition revised these proofs. This turns 300+ "discrepancies" into a documented, defensible editorial position and preempts reader confusion.

4. **Complete the verification tail (optional follow-up).** Run the same adversarial verification over the 309 unverified findings (esp. WCF 8-10 and the catechisms) to extract any remaining one-verse slips. Expect a similar small yield of true errors buried in a large majority of edition differences. This can be a background pass, not a blocker.

5. **Add a regression guard.** Once the Section 2 fixes land, consider a lightweight test that re-normalizes and diffs against a frozen expected set, so future edits to `data.json` don't reintroduce single-verse slips.
