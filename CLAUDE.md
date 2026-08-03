# Westminster Daily

A static site and daily email that cover the Westminster Standards in a year on
Dr. Pipa's calendar. Pandoc templates, a Makefile, and a Cloudflare worker that
sends the email.

## Read DESIGN.md first

**Read `DESIGN.md`** before changing any colour, type size, spacing, or layout,
on the site or in the email. It carries the palette roles, the type scale, and
the contrast floors. Follow `~/.claude/PROSE.md` for any prose readers will see.

## Find the files

- `content/MM/DD.md`: the 366 daily readings. Frontmatter carries `day_number`,
  computed with the same fixed table as `worker/src/index.js` so the web page
  and the email subject always agree. That table ignores leap years on purpose.
- `templates/base.html`: every site page. `templates/heidelberg-base.html`:
  Heidelberg Weekly.
- `templates/newsletter-buttondown.html`: the email. `worker/src/template.html`
  is a gitignored copy that `npm run sync-template` regenerates; never edit it.
- `static/scss/custom.scss`: all the styling except imports and one utility
  class in `main.scss`.

## Build

`make all` is the entry point. `make og-image DATE=03/25` rebuilds a single
Open Graph image while iterating; `make print-book` builds the PDF.

CSS compiles from SCSS, so a style change needs a rebuild before it appears in
`build/`. The browser then serves a cached `main.css` until you hard-reload.

## Deploy

Two GitHub workflows:

- **Pages**: any push to master, plus daily at 06:00 UTC to publish the day's
  page.
- **Worker**: pushes to master touching `worker/**`,
  `templates/newsletter-buttondown.html`, or its own file. The worker reads the
  published `feed.rss` and sends at 09:00 UTC, three hours after the scheduled
  Pages build.
