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

// Date header for each day — hairline rule above; topic (when given) on its
// own line beneath the date
#let date-header(month, day, topic: none, first: false) = {
  current-date.update(month + " " + day)
  if not first {
    v(16pt)
    line(length: 100%, stroke: 0.5pt + luma(150))
    v(8pt)
  } else {
    v(6pt)
  }
  block(width: 100%, sticky: true)[
    #text(font: sans-font, size: 12.5pt, weight: "bold")[#month #day]
    #if topic != none {
      v(2pt)
      text(size: 9.5pt, style: "italic", fill: luma(90))[#topic]
    }
  ]
  v(4pt)
}

// Document label — small caps
#let document-label(label) = {
  block(above: 7pt, below: 4pt, sticky: true)[
    #text(
      font: sans-font,
      size: 8.5pt,
      fill: luma(50),
      weight: "regular",
      tracking: 0.3pt,
    )[#smallcaps(label)]
  ]
}

// Separator between multiple entries within the same day — clean space;
// the small-caps document label marks the new reading
#let entry-separator() = {
  v(10pt)
}

// Confession chapter title
#let confession-title(title) = {
  block(sticky: true, above: 3pt, below: 4pt)[
    #text(size: 9.5pt, style: "italic")[#title]
  ]
}

// Catechism question — bold italic, ragged right (display lines are never justified)
#let catechism-question(q) = {
  block(sticky: true, above: 0pt, below: 4pt)[
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

// Prooftext section wrapper — full-width hairline rule
#let prooftext-section(content) = {
  v(6pt)
  line(length: 100%, stroke: 0.5pt + luma(150))
  v(1pt)
  content
  v(2pt)
}

// Curated prooftext printed in full — bold sans reference run in with the text
#let prooftext-full(reference, content) = {
  block(above: 0pt, below: 3.5pt)[
    #text(font: sans-font, size: 8pt, weight: "bold", fill: luma(40))[#reference]#h(4pt)#text(size: proof-size)[#content]
  ]
}

// Citation-only references — italic, small, ragged right
#let prooftext-citation(references) = {
  block(above: 0pt, below: 0pt)[
    #set par(justify: false)
    #text(size: proof-size, style: "italic", fill: luma(40))[#references]
  ]
}

// Prooftext group — hanging number beside the content
#let prooftext-group(num, content) = {
  block(above: 6pt, below: 0pt, breakable: false, inset: (left: 4pt))[
    #set par(leading: 4.5pt)
    #grid(
      columns: (15pt, 1fr),
      column-gutter: 3pt,
      text(font: sans-font, size: 8pt, weight: "bold", fill: luma(40))[#num.],
      content,
    )
  ]
}
