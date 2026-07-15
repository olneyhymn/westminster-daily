## 2026-07-13 — Print book typography
Tim flagged the first draft's spacing as unprofessional. Lessons:
- Zoom a rendered page to 100%+ and audit vertical rhythm before calling a layout done: stranded labels (a footnote number alone on its line), mixed leading between adjacent small-text blocks, and redundant text (topic repeating the question) all read as amateur.
- Small-text blocks (citations, footnotes) need their own tighter leading, never the body's.
- Labels/numbers belong in a hanging grid column beside content, not inline before a block (which line-breaks).

## 2026-07-13 — Vertical rhythm (second spacing correction)
Tim flagged vertical spacing again after the first fix. Root cause both times: I tuned individual gaps instead of designing a spacing *scale*. Lessons:
- Design vertical space as a hierarchy first (small within unit / medium between units / large between sections, ~1:2:4), then assign values — never tune gaps one at a time.
- Typst blocks carry implicit above/below spacing; set them explicitly to 0 wherever a v() or scale value is meant to govern, or the printed gap won't match the designed one.
- A separator rule must visually attach to what it introduces (asymmetric space), and must live in the same unbreakable block as it, or page breaks strand it.

## 2026-07-14 — Token economy for large audits
The first OPC audit burned ~6M tokens; the redo found more truth for ~2% of that. Rules:
- Prefer text/structured sources over PDF-vision agents; a machine-readable yardstick (Creeds.json) turned 30 page-reading agents into one Python diff.
- Mechanically normalize + diff BEFORE any model judgment; agents should only see genuine mismatches, batched (~25/agent), never one-agent-per-item.
- Never switch models mid-workflow — it invalidates the resume cache and re-runs completed stages.
- Fingerprint the provenance/edition of both sides FIRST (a single distinctive reading like Ps 19:1-3 vs 1-4, or 1 John 5:7's presence, identifies an edition) — auditing against the wrong yardstick produced 727 false findings.
- Mine prior runs' journals before re-running anything; the data is already paid for.

## 2026-07-14 — Validate against the primary source, not your own pipeline
The migration self-audit (data vs my own extraction) showed 171/171 clean while
two systematic bugs lived in the extraction/transform themselves (See/Cf groups
partially dropped; nested poetry spans duplicated). Random spot validation by
independent agents against the source PDFs caught both. Lessons:
- A self-audit that shares code with the pipeline under test can only catch
  write-side bugs, never extraction-side bugs. Always validate a sample against
  the primary source through an independent path.
- When a validator finds one instance of a rule-based bug, sweep for the rule,
  not the instance (the See/Cf bug affected 19 of 20 multi-ref groups).
- Check actual data conventions before adopting a policy ("drop See refs" was
  wrong; the existing catechism data carried them).
