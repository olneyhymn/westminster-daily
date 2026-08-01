# Growth plan

Written 2026-08-01 from six parallel research passes (SEO, email lifecycle,
podcast distribution, church/institutional adoption, product loops, and an
adversarial review of the premise).

## The diagnosis

**The ceiling is roughly 10x, not 100x.** Two independent estimates put the
realistic serviceable audience at 4,000–10,000 people worldwide — confessional
Westminster-holding bodies come to ~600K including children, and the funnel
from there to "would adopt a year-long daily catechism plan from a third-party
digital feed" is brutal. 500 subscribers is 5–12% of that ceiling. Success
looks like 3,000–5,000 subscribers. It will not feel like taking off.

**Nothing in the system ever asked anyone to pass it on.** The daily email —
~100,000 opens a year, the best attention this project owns — had no subscribe
link, so every forward was a dead end. Podcast show notes have no subscribe
path. The X account posted the complete reading twice a day, which *delivered
the product* rather than pointing at it. Five distribution channels, zero
capture. You cannot conclude the audience is exhausted from a system that has
never made the ask.

**Nothing was addressable by what people search for.** Every URL was a calendar
date. Small church sites with one URL per question rank #1 on these terms;
opc.org's catechism page has no anchors and doesn't rank at all.

**And one channel was silently broken.** The podcast GUID omitted the year, so
anyone subscribed longer than ~12 months had stopped receiving episodes.

## The @refconfessions result

5,300 followers, no measurable conversion. This is real evidence and it kills a
whole class of strategy: restarting X, Facebook page posting, Instagram,
Threads, Shorts, paid social, and any "build an audience first" plan. All rely
on accumulating attention and hoping it converts.

It does **not** condemn:

- **Search.** Intent-driven. Someone typing "Westminster Shorter Catechism Q1"
  already wants the object.
- **Institutional and relational distribution.** Carries authority endorsement,
  which is the mechanism that actually produces habit adoption here.
- **Forwarding from an existing reader.** Personal endorsement plus proof the
  sender keeps the habit.

One cheap test remains: a single pinned conversion post at the dormant account.
**Measure on impressions, not followers** — a dormant account reaches 1–5%, so
a null result on low reach teaches nothing. >50 signups in 14 days refutes the
pessimistic case; <15 on >2,000 impressions closes the book on social. This
harvests accumulated stock, not flow — even a good result would not justify
resuming a posting cadence.

## Done (branch: growth-fixes)

- **Podcast feed.** Year-scoped GUIDs, window widened 30 → 365 days, citations
  in episode titles, real enclosure lengths, `itunes:explicit` corrected,
  `podcast:guid` added, feed id repointed off FeedPress.
- **Daily email.** Subscribe link for forwarded readers, share line, "Day N of
  365" in subject and body.
- **`/westminster-daily/start`.** The mid-year on-ramp, the January restart, how
  to follow, and Pipa's four recommendations (previously buried in About).
- **339 reference pages.** One per Shorter Catechism question (107), Larger
  Catechism question (196), and complete Confession chapter (33), plus three
  indexes. Cross-linked both ways with the date pages. Sitemap 422 → 764.
- **Documented that the ESV verse budget is wrong** (1,000 assumed, 500 is
  Crossway's published limit). Constant deliberately unchanged.
- **`www` fixed.** The cause was not a missing redirect: `www` had two live A
  records pointing at Netlify (13.52.188.95, 52.52.192.191) left over from the
  migration, and the Pages project had `reformedconfessions.com` but never the
  www variant. Both A records replaced with `CNAME www →
  westminster-daily.pages.dev`. Every path now 200s. Canonical tags already
  point at the apex, so Google consolidates rather than seeing duplicates.
- **Podcast owner email made deliverable.** `<itunes:owner>` published
  `tim@waiting-tables.com`, and that domain has no MX records at all — the
  address could not receive mail. Spotify, YouTube, and Amazon all verify feed
  ownership by mailing a code there, so every one of them would have stalled
  silently. Now `podcast@reformedconfessions.com`, routed to `t@ehop.me` by
  Cloudflare Email Routing on the podcast's own domain.
- **Submitted to Spotify** — 28.2% of podcast listening, previously absent.
  https://open.spotify.com/show/033ZFBJEpXBSSmKaUQDvn8. Hosting stays on
  Cloudflare; Spotify polls the feed. Filed under Society & Culture (Culture,
  Society): **Spotify's taxonomy has no Religion & Spirituality option**, which
  is worth knowing before wondering why. The Apple feed still declares
  `Religion & Spirituality > Christianity` and is unaffected.
- **Podcast downloads now measured.** Enclosures route through an
  [OP3](https://op3.dev) counting redirect with the show guid attached. The
  build's own HEAD requests deliberately bypass the prefix — sizing 365
  enclosures through it would register 365 downloads per build.
- **Email verified by test send.** Rendered from the live template with real
  `data.json`: all placeholders substituted, subscribe link and share line
  present, subject reads `Day 213 · …`. The worry about whether
  `X-Buttondown-Live-Dangerously` renders Django variables turned out to be
  moot — the template uses a literal signup URL, so there are no variables. It
  would matter again only if someone switches to `{{ subscribe_url }}`.

## Immediate, not yet done

1. **Instrument conversion.** Plausible is installed but has no custom events
   and no UTM tags, and the signup form POSTs cross-origin with no confirmation
   page — so signup conversion is invisible and some unknown share of the 450
   monthly uniques is existing subscribers clicking through from email. This is
   now the largest measurement gap left.
2. **YouTube and Amazon.** Both use the same ownership-verification path, which
   now works. Together they are worth ~1–2% of listening against Spotify's
   28.2%, so this is a rainy-day task, not a priority. YouTube RSS ingestion is
   **not** deprecated; Google Podcasts was, in 2024.
3. **Check the OP3 stats page** once real traffic has flowed. OP3 creates a
   show page only after it observes requests. Apple Podcasts Connect is also
   free and apparently still unused.

**Google Search Console already exists** and is verified by DNS TXT
(`google-site-verification=wYUT-z5U9WMv6kd-mXYdmM_saz08sfazn0syJD9fw4w`). An
earlier draft of this plan said there was no property; that was wrong, and came
from checking the repo and page HTML for a meta tag without checking DNS. This
is better than a fresh setup — there is existing history to compare the
reference pages against.

## The Pipa conversation

He is a friend, which makes this a conversation rather than a permission
request. It is also the gate on everything institutional below.

**The correspondence changes the picture substantially.** In April 2022 he
proposed the book himself, unprompted:

> "Is it possible to get a digital copy of Westminster Subscription? It has
> been suggested we put in booklet. **Be under your name and mine.** What do you
> think? Dr. P"

and on the proof texts:

> "I WOULD PREFER TO KEEP PROOF TEXTS AS YOU HAVE THEM. **GREENVILLE COULD
> POSSIBLY PUBLISH IT.** WHAT YOU THINK?"

Tim raised the ESV copyright problem; Pipa replied *"Ok. I will have Andy look
into it,"* and the thread ends there. A follow-up sent 13 July 2026 is still
unanswered.

Three consequences:

- **Permission is not the existential risk this plan originally treated it as.**
  That framing came from reading `tasks/todo.md` alone. He initiated the idea.
- **But what he proposed is not what is being built.** Joint byline, possibly
  published by Greenville, versus a solo KDP paperback under one name. Name that
  difference explicitly rather than treating 2022 as blanket approval.
- **The ESV question is four years old.** Raised in 2022, delegated to "Andy,"
  never resolved, and still the item standing between the book and publication.

**On timing, and this matters more than the schedule.** A June 2025 prayer
request in Tim's inbox reports that Dr. Pipa's wife was diagnosed with
inoperable cancer. The current situation is unknown and may well explain the
unanswered July email. The Sept 15 "send it cold anyway" floor below applies to
the institutional emails; **it does not apply to him.** Send those on schedule
if nothing has come back, and let this conversation happen when it happens.

Ask for, in order of value-to-imposition:

1. **A warm introduction to Danny Olinger** (General Secretary, OPC Committee
   on Christian Education, `danny.olinger@opc.org`). Costs him one email.
2. **A warm introduction into PCA CDM.** Replaces an inbox with a person.
3. **A line for the front matter** of the print book.
4. **The NAPARC Christian Education contacts**, where he has standing.
5. **GPTS rehosting or linking the calendar** — repairs a dead resource.
6. **A foreword.** Highest imposition. Ask last, only if he volunteers.

Do not ask him to approach Ligonier or a publisher, to advocate inside an OPC or
PCA committee, or to confirm permission for the OPC proof-text edition — that is
a separate courtesy note and should not ride on his name.

One thing still worth doing whenever the conversation resumes: he is roughly 80,
and permission that lives in a friendship does not survive into an estate. A
sentence in writing protects the project without asking anything of him.

Also worth mentioning to him, independent of any ask: **GPTS dropped his
Calendar of Readings** when the site was rebuilt. The old URL 404s, there is no
resources section on gpts.edu, and `static/pipa-calendar.pdf` here is
byte-identical to the archived original. That PDF carries no copyright notice,
no rights reservation, and no permission statement. This site is the only place
still publishing it.

## Institutional, September–November

Ranked deliberately with **listings and permission-shaped asks above writing**.
A magazine article is structurally a tweet: broadcast to individuals, no
authority, no date. One session saying yes means 60–300 people starting on the
same day because someone with authority told them to.

| Target | Contact | Note |
|---|---|---|
| **PCA CDM Leader's Ministry** | `cdm.media@pcanet.org`, cc `dbennett@pcanet.org` | Their page says verbatim: "If you have a resource that you would be willing to share, we would love to hear about it!" PCA is 1,959 congregations. |
| **OPC Committee on Christian Education** | `danny.olinger@opc.org` | opc.org **already hosts an outside daily devotional it did not write** (Kuyvenhoven's *Daylight*, copyright Faith Alive). Exact precedent, single decision-maker, and the proof texts here are the OPC's own edition. |
| **PCA children's ministry** | `kflores@pcanet.org` | `children.pcacdm.org/catechism-resources` already lists third-party items. |
| **NAPARC CE contacts** | `naparc.org/ce-contacts` | Christian Education contact and email for every member denomination, on one public page. One afternoon, one template, ten denominations. |
| **The Banner (CRCNA)** | `thebanner.org/contact-us/review` | Submit **Heidelberg Weekly**, not Westminster Daily. CRCNA is 929 churches / 171,380 members. |
| **RPCNA free resources** | `drew@crownandcovenant.com` | One person is the entire gate. Their free-resources page already hosts Bible reading plans. |
| **The Aquila Report** | `daquila@theaquilareport.com` | Self-described "primarily an aggregate publisher." Offer permission to republish an existing post; do not submit a manuscript. |
| **OPC Ruling Elder Podcast** | `repod.opc.org` | Committee-run, officer-facing, host does the endorsing. Pitch as "the guy who built the thing your elders are using," not as a teacher. |

**Best product-market fit found: officer training.** PCA BCO 24-1 requires every
ruling elder and deacon nominee to be examined on the Standards. OPC and ARP
prescribe no curriculum. The PCA's own $99.99 Officer Training Kit ships the
Confession but **not** the Catechisms, and paces nothing.

**Closed doors, do not spend time:** Tabletalk (invitation-only), Great
Commission Publications (input travels through sessions and presbyteries), PCA
CDM's publishing arm (wants finished manuscripts), conference booths (no
published pricing anywhere), *Christian Renewal* (domain now a for-sale lander).

## Calendar

| When | Do |
|---|---|
| **Aug 2026** | ~~`www`, test-send, Spotify, GSC~~ all done 1 Aug. Remaining: instrument signup conversion in Plausible. Pipa conversation when the moment is right, not on a schedule. |
| **Sep 2026** | CDM and OPC CCE — as introductions if Pipa came through. **Hard floor: if nothing by Sept 15, send them cold.** The floor governs the institutional emails, not the Pipa conversation. |
| **Oct 2026** | **Oct 15 is the only published hard deadline anywhere** — *Ordained Servant* runs the 15th of the second month prior, so this is the last chance at a December issue. NAPARC sweep, Banner, Crown & Covenant. |
| **Nov 2026** | **Print book live on KDP by ~Nov 15** or it misses Christmas and the January window. Aquila Report. Bulletin insert finalized. |
| **Dec 2026** | Nothing new. "We start over January 1" to the list and to anyone who listed you. |
| **Jan 2027** | Measure. Attribute by door, or you repeat the mistake of not knowing what failed. |
| **Jun 2027** | PCA GA Jun 14–18 Milwaukee; OPC GA Jun 9–15 Greenville SC. Attend nothing; time follow-ups for the week after. |

## Open decisions

**ESV vs. a public-domain translation.** ESV is 89.5% of site body text against
a 25% cap; the repo stores ~3,476 verses against a 500-verse cap; the free key
is void for any site with ads, sponsorship, *or donations*. Meanwhile Buttondown
prices on subscribers — 5,000 subs is $50–100/month with no permitted way to
offset it, and at ~5,000 daily recipients Gmail's bulk-sender rules bind with a
hard <0.3% complaint ceiling. Swapping the site to KJV/ASV/WEB is a scripted
weekend that removes the exposure and unlocks the only revenue a free devotional
realistically has. **Deferred by decision, 2026-08-01.**

This question is older than it looks. Tim raised ESV copyright with Dr. Pipa in
April 2022; Pipa said he would have "Andy" look into it, and nothing came back.
Four years on it is still the one item genuinely blocking the print book, and it
is now blocking a decision about the site as well. Whatever the answer, it is
worth closing rather than deferring a fifth time.

Worth noting: the podcast audio is built from `data["content"]`, which contains
no ESV. It is the only Crossway-free asset, and therefore the only channel that
could carry sponsorship. The 339 new reference pages are also ESV-free.

**What growth is for.** The research assumed different answers and they imply
different plans. *More people catechized* argues for giving the dataset away and
letting churches run it on their own lists — which reduces your traffic.
*Selling the book* argues for Amazon work and one high-value ask to the existing
500 (reviews at launch); at ~$5/copy it is not a business. *Durability past the
maintainer* argues for succession, not reach. The repo currently pursues several
and has decided none.

## Rejected, with reasons

- **localStorage streaks.** Safari's ITP deletes the data after 7 days without
  interaction, so it dies precisely for the lapsed user. Duolingo's own causal
  streak lift is +1.7% D7, and a *displayed broken* streak cut continuation from
  60.9% to 45.2% versus showing nothing. Dwell ships no streak deliberately.
- **Anki as a distribution channel.** AnkiWeb download counts are admin-only,
  not public; the two existing WSC decks have 10 and 0 thumbs-up. Fine as a side
  artifact, not as a channel.
- **Children's catechism memorization programs.** No PCA/OPC/ARP denominational
  award program exists, and the children's space is crowded (GCP, New City
  Catechism, Songs for Saplings, Truth78). A dense daily reading of the Larger
  Catechism is not a children's product.
- **Day-1-relative URL track** (`/day/1`…). Forks the URL scheme away from the
  contract that RSS, podcast, email, print, and OG images all depend on. The
  mid-year problem is framing, not architecture.

## Not researched

Five seminaries (WTS PA, WSC, RTS, PRTS, Covenant). Reddit and Facebook group
data — both block automated access. Conference booth pricing — nobody publishes
it. KDP vs IngramSpark economics for churches ordering 20+ copies, which matters
only if a whole-church campaign succeeds.

## Repo defects noted in passing

- The README claimed the daily build runs on cron-jobs.org. It runs on a native
  GitHub Actions `schedule`, and `deploy-cloudflare.yml` has no
  `workflow_dispatch`, so the documented manual trigger does not exist.
- `Makefile:2` uses `date -u` while `worker/src/index.js` uses
  `America/New_York`. A push-triggered build between 00:00 and ~05:00 UTC
  publishes tomorrow's homepage to evening Eastern readers.
- The homepage self-canonicalizes to the current day's dated page
  (`Makefile` copies `$(CURRENT_FILE)` to `content/index.md`), so `/` is
  guaranteed to rank for nothing. Fixing it means giving the homepage its own
  `content/index.md` with `canonical_url: /westminster-daily/`.
- GitHub disables scheduled workflows after 60 days of repository inactivity,
  and the commit history has gaps. If the site build stops, the email keeps
  working perfectly while the homepage silently freezes on a stale day. Nothing
  monitors site freshness.
- `twitter:site` in both templates is `@reformedconfessions` — 19 characters,
  longer than X's 15-character limit, so it has never been a real account. The
  live one is `@refconfessions`.
- The Buttondown archive 302s to the signup page, so there is no public
  indexable archive.
