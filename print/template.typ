// Westminster Daily — Print Book Template
// 6" × 9" trim size, print-ready for Amazon KDP (no bleed)

#let sans-font = "Source Sans 3"
#let proof-size = 9pt
#let current-date = state("current-date", "")

#let book-setup(body) = {
  set page(
    width: 6in,
    height: 9in,
    margin: (
      inside: 0.8in,
      outside: 0.75in,
      top: 0.7in,
      bottom: 0.65in,
    ),
    numbering: "1",
    number-align: center,
    header: context {
      // Suppress the running header on month-opening pages
      let month-starts = query(heading.where(level: 1))
        .filter(h => h.location().page() == here().page())
      if month-starts.len() == 0 {
        let date = current-date.get()
        if date != "" {
          let pg = counter(page).get().first()
          let alignment = if calc.even(pg) { left } else { right }
          align(alignment)[
            #text(font: sans-font, size: 7.5pt, fill: luma(110), tracking: 1pt)[#upper(date)]
          ]
        }
      }
    },
  )

  set text(
    font: "Libertinus Serif",
    size: 11pt,
    lang: "en",
    hyphenate: true,
    costs: (orphan: 500%, widow: 500%),
  )

  set par(
    leading: 7.5pt,
    justify: true,
  )

  // Month headings (level 1) — rendered as month-opening headers, tracked for the ToC
  show heading.where(level: 1): it => {
    v(10pt)
    align(center)[
      #text(font: sans-font, size: 17pt, weight: "bold", tracking: 1.5pt)[#upper(it.body)]
    ]
    v(4pt)
    line(length: 100%, stroke: 0.75pt + luma(150))
    v(2pt)
  }

  body
}

// Month header — starts a new page, emits an outlined heading
#let month-header(name) = {
  pagebreak(weak: true)
  heading(level: 1, outlined: true, name)
}

// Table of contents (months)
#let month-toc() = {
  align(center)[
    #text(font: sans-font, size: 15pt, weight: "bold", tracking: 1pt)[CONTENTS]
  ]
  v(18pt)
  set par(justify: false)
  outline(
    title: none,
    target: heading.where(level: 1),
    indent: 0pt,
  )
}

// Date locator — one-page grid mapping every date to its folio
#let day-locator() = {
  align(center)[
    #text(font: sans-font, size: 13pt, weight: "bold", tracking: 1pt)[FIND A DATE]
  ]
  v(4pt)
  align(center)[
    #text(size: 8.5pt, style: "italic", fill: luma(40))[The page on which each day's reading begins]
  ]
  v(10pt)
  context {
    let days = query(metadata)
      .filter(m => type(m.value) == dictionary and m.value.at("kind", default: "") == "day")
    let pg = (:)
    for m in days {
      pg.insert(str(m.value.m) + "-" + str(m.value.d), counter(page).at(m.location()).first())
    }
    let months = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")
    let cells = ()
    cells.push([])
    for mo in months {
      cells.push(align(center)[#text(font: sans-font, weight: "bold", size: 6.5pt)[#mo]])
    }
    for d in range(1, 32) {
      cells.push(align(right)[#text(font: sans-font, weight: "bold", size: 6.5pt)[#d]])
      for mm in range(1, 13) {
        let key = str(mm) + "-" + str(d)
        if key in pg {
          cells.push(align(center)[#text(size: 7pt)[#pg.at(key)]])
        } else {
          cells.push(align(center)[#text(size: 7pt, fill: luma(150))[--]])
        }
      }
    }
    grid(
      columns: (auto,) + ((1fr,) * 12),
      row-gutter: 5.2pt,
      column-gutter: 2pt,
      ..cells,
    )
  }
}

// Index of the Standards — every chapter and question with its page(s)
#let standards-index() = {
  pagebreak(weak: true)
  heading(level: 1, outlined: true)[Index of the Standards]
  v(2pt)
  align(center)[
    #text(size: 8.5pt, style: "italic", fill: luma(40))[Where each portion of the Standards is read]
  ]
  v(8pt)
  set par(justify: false)
  context {
    let rds = query(metadata)
      .filter(m => type(m.value) == dictionary and m.value.at("kind", default: "") == "rd")
    let pageof(m) = counter(page).at(m.location()).first()

    // Confession of Faith, grouped by chapter with page ranges
    let chapters = (:)
    for m in rds.filter(m => m.value.doc == "WCF") {
      let key = str(m.value.ch)
      let entry = chapters.at(key, default: (title: m.value.title, pages: ()))
      entry.pages.push(pageof(m))
      chapters.insert(key, entry)
    }
    text(font: sans-font, size: 9.5pt, weight: "bold", tracking: 0.3pt)[#smallcaps[Confession of Faith]]
    v(4pt)
    for key in chapters.keys().sorted(key: k => int(k)) {
      let e = chapters.at(key)
      let pgs = e.pages.sorted()
      let range-str = if pgs.first() == pgs.last() { str(pgs.first()) } else { str(pgs.first()) + "\u{2013}" + str(pgs.last()) }
      block(above: 2.5pt, below: 0pt)[
        #text(size: 8.5pt)[*#key* #h(4pt) #e.title #box(width: 1fr) #range-str]
      ]
    }
    v(10pt)

    // Catechisms: question number -> page(s), set in columns
    let catechism(label, doc) = {
      let qs = (:)
      for m in rds.filter(m => m.value.doc == doc) {
        let key = str(m.value.num)
        let pages = qs.at(key, default: ())
        pages.push(pageof(m))
        qs.insert(key, pages)
      }
      let entries = qs.keys().sorted(key: k => int(k)).map(key =>
        text(size: 8pt)[*#key* #h(3pt) #qs.at(key).sorted().dedup().map(str).join(", ")]
      )
      let ncols = 6
      let per = calc.ceil(entries.len() / ncols)
      text(font: sans-font, size: 9.5pt, weight: "bold", tracking: 0.3pt)[#smallcaps(label)]
      v(4pt)
      grid(
        columns: (1fr,) * ncols,
        column-gutter: 10pt,
        ..range(ncols).map(c => {
          let chunk = entries.slice(c * per, calc.min((c + 1) * per, entries.len()))
          stack(dir: ttb, spacing: 3pt, ..chunk)
        }),
      )
      v(10pt)
    }
    catechism("Shorter Catechism", "WSC")
    catechism("Larger Catechism", "WLC")
  }
}

// Date header for each day — hairline rule above; topic (when given) on its
// own line beneath the date
// Spacing scale: small gaps live inside a reading, the medium gap sits
// between readings, and the large gap + rule marks a new day. Blocks carry
// explicit above/below so no implicit spacing sneaks in.
#let date-header(month, day, topic: none, first: false) = {
  current-date.update(month + " " + day)
  // Rule + date form one unbreakable sticky unit so a page break can never
  // strand the rule; the big between-day gap is the block's `above`
  block(
    width: 100%,
    sticky: true,
    breakable: false,
    above: if first { 6pt } else { 26pt },
    below: 0pt,
  )[
    #if not first {
      line(length: 100%, stroke: 0.5pt + luma(150))
      v(6pt)
    }
    #text(font: sans-font, size: 12.5pt, weight: "bold")[#month #day]
    #if topic != none {
      v(2pt)
      text(size: 9.5pt, style: "italic", fill: luma(90))[#topic]
    }
  ]
}

// Document label — small caps
#let document-label(label) = {
  block(above: 11pt, below: 6pt, sticky: true)[
    #text(
      font: sans-font,
      size: 8.5pt,
      fill: luma(50),
      weight: "regular",
      tracking: 0.3pt,
    )[#smallcaps(label)]
  ]
}

// Separator between multiple entries within the same day — medium gap
// (the following document label adds its own 8pt), clearly smaller than
// the between-day gap
#let entry-separator() = {
  v(6pt)
}

// Confession chapter title
#let confession-title(title) = {
  block(sticky: true, above: 6pt, below: 6pt)[
    #text(size: 9.5pt, style: "italic")[#title]
  ]
}

// Catechism question — bold italic, ragged right (display lines are never justified)
#let catechism-question(q) = {
  block(sticky: true, above: 6pt, below: 5pt)[
    #set par(justify: false)
    #text(weight: "bold", style: "italic")[Q. #q]
  ]
}

// Catechism answer
#let catechism-answer(a) = {
  text[A. #a]
}

// Confession body paragraph
#let confession-body(b) = {
  text[#b]
}

// Prooftext section wrapper — the rule caps the proof block: more air
// above (toward the answer) than below (toward the first group)
#let prooftext-section(content) = {
  v(7pt)
  line(length: 100%, stroke: 0.5pt + luma(150))
  v(0pt)
  content
}

// Curated prooftext printed in full — bold sans reference run in with the text
#let prooftext-full(reference, content) = {
  block(above: 0pt, below: 3.5pt)[
    #text(font: sans-font, size: 8pt, weight: "bold", fill: luma(40))[#reference]#h(4pt)#text(size: proof-size)[#content]
  ]
}

// Citation-only references — italic, small, ragged right. When they follow
// a printed passage in the same group, a "See also" prefix marks them as
// further reading rather than part of the quotation.
#let prooftext-citation(references, see-also: false) = {
  block(above: 0pt, below: 0pt)[
    #set par(justify: false)
    #if see-also {
      text(font: sans-font, size: 7pt, fill: luma(40), tracking: 0.3pt)[#smallcaps[See also]]
      h(4pt)
    }
    #text(size: proof-size, style: "italic", fill: luma(40))[#references]
  ]
}

// Prooftext group — hanging number beside the content
#let prooftext-group(num, content) = {
  block(above: 5pt, below: 0pt, breakable: false, inset: (left: 4pt))[
    #set par(leading: 4.5pt)
    #grid(
      columns: (15pt, 1fr),
      column-gutter: 3pt,
      text(font: sans-font, size: 8pt, weight: "bold", fill: luma(40))[#num.],
      content,
    )
  ]
}
