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
