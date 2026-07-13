// Westminster Daily — Print Book Template
// 7" × 10" trim size, print-ready

#let sans-font = "Gill Sans"
#let proof-size = 8pt
#let current-month = state("current-month", "")

#let book-setup(body) = {
  set page(
    width: 7in,
    height: 10in,
    margin: (
      inside: 1.125in,
      outside: 0.75in,
      top: 0.75in,
      bottom: 0.75in,
    ),
    numbering: "1",
    number-align: center,
    header: context {
      let month = current-month.get()
      if month != "" {
        let pg = counter(page).get().first()
        let is-even = calc.even(pg)
        let alignment = if is-even { left } else { right }
        align(alignment)[
          #text(font: sans-font, size: 7.5pt, fill: luma(130), tracking: 0.5pt)[#upper(month)]
        ]
      }
    },
  )

  set text(
    font: "Libertinus Serif",
    size: 9.5pt,
    lang: "en",
  )

  set par(
    leading: 5.5pt,
    justify: true,
  )

  body
}

// Month header — at top of first day's section
#let month-header(name) = {
  current-month.update(name)
  pagebreak(weak: true)
  v(4pt)
  align(center)[
    #text(font: sans-font, size: 18pt, weight: "bold")[#upper(name)]
  ]
  v(6pt)
  line(length: 100%, stroke: 0.5pt + luma(180))
}

// Date header for each day — with hairline rule above
#let date-header(month, day) = {
  v(14pt)
  line(length: 100%, stroke: 0.15pt + luma(210))
  v(5pt)
  block(width: 100%)[
    #text(font: sans-font, size: 13pt, weight: "bold")[#month #day]
  ]
  v(3pt)
}

// First date header after month header — no extra rule needed
#let first-date-header(month, day) = {
  v(6pt)
  block(width: 100%)[
    #text(font: sans-font, size: 13pt, weight: "bold")[#month #day]
  ]
  v(3pt)
}

// Document label — small caps, more prominent
#let document-label(label) = {
  v(5pt)
  text(
    font: sans-font,
    size: 8.5pt,
    fill: luma(50),
    weight: "regular",
    tracking: 0.3pt,
  )[#smallcaps(label)]
  v(2pt)
}

// Separator between multiple entries within the same day
#let entry-separator() = {
  v(8pt)
  align(center)[
    #text(size: 8pt, fill: luma(150), tracking: 6pt)[{\*} {\*} {\*}]
  ]
  v(4pt)
}

// Confession chapter title
#let confession-title(title) = {
  text(size: 9pt, style: "italic")[#title]
  linebreak()
}

// Catechism question — bold italic
#let catechism-question(q) = {
  text(weight: "bold", style: "italic")[Q. #q]
  linebreak()
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
  v(5pt)
  line(length: 100%, stroke: 0.25pt + luma(190))
  v(3pt)
  content
  v(3pt)
}

// Prooftext with full text — reference in sans-serif, inline with text
#let prooftext-full(reference, content) = {
  block(above: 3.5pt, below: 0pt, inset: (left: 10pt))[
    #set par(leading: 4pt)
    #text(font: sans-font, size: 7pt, weight: "bold", fill: luma(60))[#reference] #h(3pt) #text(size: proof-size)[#content]
  ]
}

// Prooftext citation only — italic, no label
#let prooftext-citation(references) = {
  block(above: 3pt, below: 0pt, inset: (left: 10pt))[
    #text(size: proof-size, style: "italic", fill: luma(60))[#references]
  ]
}

// Prooftext group — numbered, with subtle left border
#let prooftext-group(num, content) = {
  block(
    above: 5pt,
    below: 1pt,
    inset: (left: 6pt, top: 2pt, bottom: 2pt),
    stroke: (left: 1.5pt + luma(200)),
  )[
    #text(font: sans-font, size: 7.5pt, weight: "bold", fill: luma(60))[#num.] #content
  ]
}
