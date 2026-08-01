# Westminster Daily — Print Book Spec (v2)

## Overview

Generate a print-ready PDF of the Westminster Daily reading plan (366 daily entries) for
sale via Amazon KDP print-on-demand. The book presents the Westminster Confession of
Faith, Shorter Catechism, and Larger Catechism organized as a calendar-year daily reader,
with curated ESV proof texts.

## Target Specs

- **Trim size:** 6" × 9" (KDP standard)
- **Target length:** ~450 pages
- **POD platform:** Amazon KDP — B&W interior, no bleed, single-page PDF, fonts embedded
- **Paper:** cream (devotional feel; final choice at KDP setup)
- **Binding:** perfect-bound paperback
- **PDF engine:** Typst (`print/` pipeline: Python generator → `.typ` → PDF)

## Content Organization

- **Order:** Calendar date (January 1 – December 31; Feb 29 omitted, 365 readings)
- **Entries flow** — a day may share a page or run over; no forced page-per-day
- **Month transitions:** prominent month header at the first day of each month (no
  divider pages)

## Content Per Daily Entry

1. **Date header** — e.g., "January 12"
2. **Topic title** — the day's `title` from `data.json` (e.g., "Of God's covenant with
   man, part 5")
3. **One or more readings**, each with:
   - Document citation label (e.g., "Shorter Catechism 1", "Confession of Faith 7.5")
   - Catechisms: Question (bold italic) + Answer
   - Confession: chapter title + body text
4. **Proof texts** (see below)

## Proof Text Rules (v2 — changed from v1)

- **Every proof-text reference is listed**, grouped under its superscript footnote
  number, matching the numbering in the catechism/confession text.
- **Curated passages are printed in full** (ESV text); all other references appear as
  citations only.
- **Curation criteria**, in priority order:
  1. **Doctrinally load-bearing** — the classic *sedes doctrinae* for the day's doctrine
  2. **Devotionally rich** — passages that warm the heart and pray well
- **Global budget: <1,000 ESV verses printed across the whole book.** Works
  out to ~2–3 printed verses per day on average (~83 verses/month guideline).
  > ⚠️ **This 1,000 figure is unverified and probably wrong.** Crossway's
  > published standard-use limit is **500 verses**, and their terms exclude
  > works quoting Scripture "in a commentary or other biblical reference
  > work," which may void the allowance for this book altogether. The budget
  > constant has deliberately not been lowered, because enforcing 500 means
  > re-curating and cutting ~244 verses from a finished interior — a content
  > decision, not a correction. See `tasks/todo.md`. Resolve before shipping.
- Curation is stored as data (per-month JSON in `print/curation/`), not code, so
  selections are reviewable and editable by hand.
- The build reports total printed verse count and fails loudly if the budget is exceeded.

## Visual Style: Modern Reformed

- Body: clean serif (Libertinus Serif); headers/labels: sans-serif
- Catechism questions bold italic; answers regular; confession body regular
- Proof texts: smaller size in a distinct indented block; citation-only references
  italic and small
- Generous margins and leading for a 6×9 devotional; larger gutter for binding
- Black text only; no ornament

## Page Layout

- Margins sized for KDP 6×9 at ~450 pages (gutter ≥ 0.75" per KDP spec for 301–500
  pages; outer/top/bottom ≥ 0.25", target ~0.75")
- **Running headers:** dictionary-style — each page's header shows the month and date
  current at the top of that page
- Page numbers centered at bottom

## Navigation

- **Month table of contents** — one page, months with page numbers
- **Date locator** — one-page front-matter grid (month × day → page)
- **Index of the Standards** — back matter: WCF chapters with page ranges,
  WSC/WLC question numbers with pages (generated from Typst metadata queries)
- Running date headers (above)

## Front Matter

1. Half title — "The Westminster Daily"
2. Title page — full title, subtitle ("A Daily Reading Plan through the Westminster
   Standards"), "Compiled and edited by Tim Hopper", credit to Dr. Joseph A. Pipa Jr.'s
   reading calendar
3. Copyright page — copyright notice, required ESV permission statement,
   westminsterdaily.com
4. Table of contents (months)
5. Introduction (~1 page) — written by Tim (build carries a placeholder page
   until then; see tasks/todo.md)

## Build Process

1. `print/generate_typst.py` reads 366 `content/MM/DD/data.json` files (calendar order,
   `content_with_prooftexts`)
2. Reads curation data from `print/curation/*.json`; prints curated passages in full,
   everything else citation-only
3. Emits `print/westminster-daily.typ`; Typst compiles to PDF
4. Build prints the verse-budget report

## Curation Workflow

1. Digest script dumps each month's readings + proof-text references with verse counts
2. Curator (Claude, reviewed by Tim) selects passages per day against the criteria and
   monthly verse guideline
3. January produced first as a calibration sample; remaining months follow after
   approval

## Licensing

- ESV: stay within Crossway standard-use terms (see the budget warning above —
  the real published limit is 500 verses, not 1,000); required
  copyright notice on copyright page. Owner verifies before publication.
- Dr. Pipa's reading calendar: owner to confirm permission for commercial use
- Westminster Standards text: public domain

## Out of Scope (deferred)

- Cover design (needs final page count; KDP wraparound PDF — follow-up task)
- Hardcover, eBook/Kindle
- Standards index / Scripture index
- Color printing
