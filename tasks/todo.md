# Print book TODOs

- [ ] **Write the Introduction** — the build currently has a placeholder page
      ("Introduction to be written"); replace the placeholder block in
      `print/generate_typst.py` (`generate_front_matter`) with Tim's prose
- [ ] Cover design — KDP wraparound PDF; spine width from final page count
- [ ] Order a physical proof before publishing (verify rules/grays on paper)
- [ ] Verify ESV standard-use compliance against the *actual* Crossway terms.
      The 1,000-verse figure used throughout this repo (SPEC-print-book.md,
      `print/generate_typst.py:25`) does not match Crossway's published
      standard-use limit, which is **500 verses**, and their terms exclude
      works that quote Scripture "in a commentary or other biblical reference
      work" — which may void the standard-use allowance for this book
      entirely. The build currently prints 744, i.e. under the number we
      assumed and over the number Crossway publishes.
      Deliberately NOT changed: enforcing 500 means re-curating proof texts
      and cutting ~244 verses from a nearly-finished interior. That is a
      content decision, not a bug fix. Resolve before the book ships —
      either by re-curating, by asking Crossway for a written license, or by
      moving proof texts to a public-domain translation.
- [x] Proof-text strategy: standardized on the OPC edition (2026-07-14;
      see print/audit/provenance-audit-report.md and scripts/opc-migration/)
- [ ] Consider a courtesy note to the OPC Committee on Christian Education
      about using their proof-text edition commercially (bundle with Pipa ask)
- [ ] Confirm permission from Dr. Joseph Pipa for commercial use of the
      reading calendar
- [ ] KDP setup: 6×9 paperback, cream paper, list price
