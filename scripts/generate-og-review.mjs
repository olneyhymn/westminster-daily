import fs from "fs/promises";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, "..");

function parseArgs(argv) {
  const options = {
    output: path.join(ROOT, "build", "og-review", "index.html"),
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--output") {
      options.output = path.resolve(ROOT, argv[index + 1]);
      index += 1;
      continue;
    }

    if (arg === "--help" || arg === "-h") {
      console.log("Usage: node scripts/generate-og-review.mjs --output build/og-review/index.html");
      process.exit(0);
    }

    throw new Error(`Unknown argument: ${arg}`);
  }

  return options;
}

async function walkFiles(directory, matcher) {
  const results = [];
  const entries = await fs.readdir(directory, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      results.push(...(await walkFiles(fullPath, matcher)));
      continue;
    }

    if (matcher(fullPath)) {
      results.push(fullPath);
    }
  }

  results.sort();
  return results;
}

function splitFrontmatter(raw) {
  const match = raw.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/);
  if (!match) {
    return { attributes: {}, body: raw };
  }

  const attributes = {};
  for (const line of match[1].split(/\r?\n/)) {
    if (!line.trim()) {
      continue;
    }

    const separatorIndex = line.indexOf(":");
    if (separatorIndex === -1) {
      continue;
    }

    const key = line.slice(0, separatorIndex).trim();
    let value = line.slice(separatorIndex + 1).trim();
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }

    attributes[key] = value;
  }

  return { attributes, body: match[2] };
}

function decodeEntities(value) {
  return String(value || "")
    .replace(/&#(\d+);/g, (_, code) => String.fromCharCode(Number(code)))
    .replace(/&nbsp;/g, " ")
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">");
}

function stripHtml(value) {
  return decodeEntities(
    String(value || "")
      .replace(/<br\s*\/?>/gi, " ")
      .replace(/<[^>]*>/g, " ")
      .replace(/\s+/g, " ")
      .trim()
  );
}

function clampText(value, maxLength) {
  const text = String(value || "").trim();
  if (text.length <= maxLength) {
    return text;
  }

  return `${text.slice(0, maxLength - 1).trimEnd()}...`;
}

function extractMarkdownPreview(body) {
  const lines = body.split(/\r?\n/);

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) {
      continue;
    }

    if (
      trimmed.startsWith("#") ||
      trimmed.startsWith("---") ||
      trimmed.startsWith("[^") ||
      /^Question\s+\d+$/i.test(trimmed) ||
      /^Answer$/i.test(trimmed) ||
      /^Introduction$/i.test(trimmed)
    ) {
      continue;
    }

    const cleaned = decodeEntities(
      trimmed
        .replace(/[*_`]/g, "")
        .replace(/\[(.*?)\]\([^)]*\)/g, "$1")
        .replace(/\s+/g, " ")
        .trim()
    );

    if (cleaned) {
      return clampText(cleaned, 180);
    }
  }

  return "";
}

function uniqueBy(records, keyFn) {
  const seen = new Set();
  return records.filter((record) => {
    const key = keyFn(record);
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}

async function loadWestminsterRecords() {
  const markdownFiles = await walkFiles(path.join(ROOT, "content"), (filePath) =>
    /content\/\d{2}\/\d{2}\.md$/.test(filePath)
  );

  const records = [];
  for (const markdownPath of markdownFiles) {
    const raw = await fs.readFile(markdownPath, "utf8");
    const { attributes } = splitFrontmatter(raw);
    if (!attributes.short_date) {
      continue;
    }

    const month = markdownPath.split(path.sep).slice(-2)[0];
    const dayFile = path.basename(markdownPath, ".md");
    const jsonPath = path.join(ROOT, "content", month, dayFile, "data.json");
    const data = JSON.parse(await fs.readFile(jsonPath, "utf8"));
    const firstEntry = data.content?.[0] || {};
    const excerpt = clampText(
      firstEntry.answer || stripHtml(firstEntry.body) || firstEntry.question || "",
      180
    );

    records.push({
      id: `westminster-${attributes.short_date}`,
      series: "westminster",
      filename: `${attributes.short_date}-full.png`,
      pagePath: `../westminster-daily/${month}/${dayFile}.html`,
      title: attributes.pagetitle || data.title || "Westminster Daily",
      detail: firstEntry.long_citation || firstEntry.citation || "",
      context: attributes.this_date || `${month}/${dayFile}`,
      excerpt,
      titleLength: (attributes.pagetitle || "").length,
      excerptLength: excerpt.length,
    });
  }

  return records;
}

async function loadHeidelbergRecords() {
  const markdownFiles = await walkFiles(
    path.join(ROOT, "content-heidelberg"),
    (filePath) => /content-heidelberg\/week-\d{2}\/index\.md$/.test(filePath)
  );

  const records = [];
  for (const markdownPath of markdownFiles) {
    const raw = await fs.readFile(markdownPath, "utf8");
    const { attributes, body } = splitFrontmatter(raw);
    if (!attributes.week_number) {
      continue;
    }

    const excerpt = extractMarkdownPreview(body);
    records.push({
      id: `heidelberg-${attributes.week_number}`,
      series: "heidelberg",
      filename: `heidelberg-week-${attributes.week_number}-full.png`,
      pagePath: `../heidelberg-weekly/week-${attributes.week_number}/index.html`,
      title: attributes.pagetitle || "Heidelberg Weekly",
      detail: attributes.lords_day ? `Lord's Day ${attributes.lords_day}` : "",
      context: attributes.this_week || `Week ${Number(attributes.week_number)}`,
      excerpt,
      titleLength: (attributes.pagetitle || "").length,
      excerptLength: excerpt.length,
    });
  }

  return records;
}

function buildDefaults() {
  return [
    {
      id: "westminster-default",
      series: "westminster",
      filename: "westminster-default-full.png",
      pagePath: "../westminster-daily/index.html",
      title: "Westminster Daily",
      detail: "Default image",
      context: "Homepage",
      excerpt: "Default Open Graph image used when a page-level date is not set.",
      titleLength: "Westminster Daily".length,
      excerptLength: 63,
    },
    {
      id: "heidelberg-default",
      series: "heidelberg",
      filename: "heidelberg-default-full.png",
      pagePath: "../heidelberg-weekly/index.html",
      title: "Heidelberg Weekly",
      detail: "Default image",
      context: "Homepage",
      excerpt: "Default Open Graph image used when a week-specific image is not set.",
      titleLength: "Heidelberg Weekly".length,
      excerptLength: 67,
    },
  ];
}

function addFlags(records, currentIds) {
  for (const record of records) {
    record.flags = [];
    if (currentIds.has(record.id)) {
      record.flags.push("current");
    }
  }

  for (const series of ["westminster", "heidelberg"]) {
    const scoped = records.filter((record) => record.series === series && !record.id.endsWith("default"));
    if (scoped.length === 0) {
      continue;
    }

    const longestTitle = [...scoped].sort((a, b) => b.titleLength - a.titleLength)[0];
    const shortestTitle = [...scoped].sort((a, b) => a.titleLength - b.titleLength)[0];
    const longestExcerpt = [...scoped].sort((a, b) => b.excerptLength - a.excerptLength)[0];

    longestTitle.flags.push("long-title");
    shortestTitle.flags.push("short-title");
    if (longestExcerpt.excerptLength > 0) {
      longestExcerpt.flags.push("long-excerpt");
    }
  }

  for (const record of records) {
    if (record.id.endsWith("default")) {
      record.flags.push("default");
    }
  }

  return records;
}

function getCurrentIds() {
  const now = new Date(
    new Date().toLocaleString("en-US", { timeZone: "America/New_York" })
  );
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");

  const jan1 = new Date(2024, 0, 1);
  const daysUntilSunday = (7 - jan1.getDay()) % 7;
  const firstSunday = new Date(jan1);
  firstSunday.setDate(jan1.getDate() + daysUntilSunday);
  const weeksDiff = Math.floor((now - firstSunday) / (1000 * 60 * 60 * 24 * 7));
  const week = String((((weeksDiff % 52) + 52) % 52) + 1).padStart(2, "0");

  return new Set([`westminster-${month}${day}`, `heidelberg-${week}`]);
}

function buildSuggested(records) {
  const byFlag = (flag) => records.filter((record) => record.flags.includes(flag));
  return uniqueBy(
    [
      ...byFlag("default"),
      ...byFlag("current"),
      ...byFlag("long-title"),
      ...byFlag("short-title"),
      ...byFlag("long-excerpt"),
    ],
    (record) => record.id
  );
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function renderBadge(flag) {
  const labels = {
    default: "Default",
    current: "Current",
    "long-title": "Long Title",
    "short-title": "Short Title",
    "long-excerpt": "Long Excerpt",
  };

  return `<span class="badge badge-${flag}">${labels[flag] || flag}</span>`;
}

function renderCard(record) {
  const badges = record.flags.map(renderBadge).join("");
  const searchText = [
    record.series,
    record.context,
    record.title,
    record.detail,
    record.excerpt,
    record.flags.join(" "),
  ]
    .join(" ")
    .toLowerCase();

  return `<article class="card" data-series="${escapeHtml(record.series)}" data-search="${escapeHtml(searchText)}">
    <div class="card-top">
      <div class="meta-row">
        <span class="series">${escapeHtml(record.series)}</span>
        <span class="context">${escapeHtml(record.context)}</span>
      </div>
      <h3>${escapeHtml(record.title)}</h3>
      <p class="detail">${escapeHtml(record.detail || " ")}</p>
      <div class="badges">${badges}</div>
    </div>
    <a class="image-link" href="${escapeHtml(record.pagePath)}" target="_blank" rel="noreferrer">
      <img loading="lazy" src="../images/docs/${escapeHtml(record.filename)}" alt="${escapeHtml(record.title)}" />
    </a>
    <div class="card-bottom">
      <p class="excerpt">${escapeHtml(record.excerpt || "No excerpt captured for this entry.")}</p>
      <div class="stats">
        <span>Title ${record.titleLength} chars</span>
        <span>Excerpt ${record.excerptLength} chars</span>
      </div>
      <div class="links">
        <a href="${escapeHtml(record.pagePath)}" target="_blank" rel="noreferrer">Open page</a>
        <a href="../images/docs/${escapeHtml(record.filename)}" target="_blank" rel="noreferrer">Open image</a>
      </div>
    </div>
  </article>`;
}

function buildHtml(suggested, allRecords) {
  const total = allRecords.length;
  const westminsterCount = allRecords.filter((record) => record.series === "westminster").length;
  const heidelbergCount = allRecords.filter((record) => record.series === "heidelberg").length;

  return `<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>OG Review Dashboard</title>
    <style>
      :root {
        --parchment: #e8e0d2;
        --cream: #fffdf7;
        --burgundy: #5c1a2a;
        --gold: #c4a265;
        --brown-muted: #8b7355;
        --brown-light: #a0937d;
        --dark-brown: #2c1810;
        --footer-bg: #f5f0e6;
        --border-light: #d6cbaf;
      }

      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: Georgia, "Times New Roman", serif;
        color: var(--dark-brown);
        background:
          radial-gradient(circle at top left, rgba(255,255,255,0.35), transparent 30%),
          linear-gradient(180deg, rgba(232,224,210,0.92), rgba(245,240,230,0.95));
      }

      .shell {
        max-width: 1440px;
        margin: 0 auto;
        padding: 28px 18px 40px;
      }

      .hero {
        background: rgba(255,253,247,0.9);
        border: 1px solid rgba(196,162,101,0.5);
        box-shadow: 0 14px 40px rgba(44,24,16,0.08);
        padding: 26px 24px 22px;
      }

      .eyebrow {
        text-transform: uppercase;
        letter-spacing: 3px;
        font-size: 11px;
        color: var(--brown-light);
      }

      h1 {
        margin: 8px 0 10px;
        font-size: 42px;
        line-height: 1.05;
        color: var(--burgundy);
        font-style: italic;
        font-weight: normal;
      }

      .hero p {
        max-width: 860px;
        margin: 0;
        font-size: 18px;
        line-height: 1.55;
      }

      .summary {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 18px;
      }

      .pill {
        border: 1px solid var(--border-light);
        background: var(--footer-bg);
        padding: 8px 12px;
        font-size: 13px;
        color: var(--brown-muted);
      }

      .toolbar {
        position: sticky;
        top: 0;
        z-index: 20;
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 18px;
        padding: 14px;
        background: rgba(245,240,230,0.93);
        border: 1px solid rgba(214,203,175,0.9);
        backdrop-filter: blur(8px);
      }

      .toolbar input,
      .toolbar select {
        padding: 10px 12px;
        border: 1px solid var(--border-light);
        background: var(--cream);
        color: var(--dark-brown);
        font-family: Georgia, "Times New Roman", serif;
        font-size: 15px;
      }

      .toolbar input { min-width: 260px; flex: 1; }

      section {
        margin-top: 24px;
      }

      section h2 {
        margin: 0 0 10px;
        font-size: 24px;
        color: var(--burgundy);
        font-style: italic;
        font-weight: normal;
      }

      .section-note {
        margin: 0 0 16px;
        color: var(--brown-muted);
        font-size: 16px;
      }

      .grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 18px;
      }

      .card {
        display: flex;
        flex-direction: column;
        min-height: 100%;
        background: rgba(255,253,247,0.92);
        border: 1px solid rgba(214,203,175,0.9);
        box-shadow: 0 10px 28px rgba(44,24,16,0.06);
      }

      .card-top,
      .card-bottom {
        padding: 14px 15px;
      }

      .meta-row,
      .stats,
      .links {
        display: flex;
        justify-content: space-between;
        gap: 10px;
        flex-wrap: wrap;
      }

      .series,
      .context,
      .stats span {
        text-transform: uppercase;
        letter-spacing: 1.4px;
        font-size: 11px;
        color: var(--brown-light);
      }

      .card h3 {
        margin: 8px 0 4px;
        font-size: 28px;
        line-height: 1.15;
        font-weight: normal;
        color: var(--burgundy);
      }

      .detail {
        min-height: 22px;
        margin: 0;
        font-size: 18px;
        color: var(--brown-muted);
      }

      .badges {
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
        margin-top: 10px;
      }

      .badge {
        border: 1px solid var(--border-light);
        padding: 4px 8px;
        font-size: 11px;
        letter-spacing: 1px;
        text-transform: uppercase;
        background: var(--cream);
      }

      .badge-current,
      .badge-long-title { color: var(--burgundy); }
      .badge-default { color: var(--dark-brown); }
      .badge-short-title,
      .badge-long-excerpt { color: var(--brown-muted); }

      .image-link {
        display: block;
        padding: 0 15px;
      }

      .image-link img {
        width: 100%;
        display: block;
        border: 1px solid rgba(214,203,175,0.9);
        background: white;
      }

      .excerpt {
        margin: 0 0 12px;
        font-size: 16px;
        line-height: 1.45;
      }

      .links a {
        color: var(--burgundy);
        text-decoration: none;
      }

      .links a:hover {
        text-decoration: underline;
      }

      .muted {
        color: var(--brown-muted);
      }

      @media (max-width: 720px) {
        h1 { font-size: 34px; }
        .shell { padding: 18px 12px 28px; }
      }
    </style>
  </head>
  <body>
    <main class="shell">
      <header class="hero">
        <div class="eyebrow">Open Graph QA</div>
        <h1>OG Review Dashboard</h1>
        <p>Use this page to spot-check edge cases before shipping the regenerated social images. The suggested section pulls in defaults, current pages, longest titles, shortest titles, and the entries with the most excerpt content.</p>
        <div class="summary">
          <div class="pill">${total} images in review set</div>
          <div class="pill">${westminsterCount} Westminster</div>
          <div class="pill">${heidelbergCount} Heidelberg</div>
          <div class="pill">Open any card to compare page and image</div>
        </div>
      </header>

      <div class="toolbar">
        <input id="search" type="search" placeholder="Search title, date, citation, excerpt, or flags" />
        <select id="series-filter">
          <option value="all">All series</option>
          <option value="westminster">Westminster</option>
          <option value="heidelberg">Heidelberg</option>
        </select>
      </div>

      <section>
        <h2>Suggested Checks</h2>
        <p class="section-note">This is the fast pass for layout failures and awkward truncation.</p>
        <div class="grid" id="suggested-grid">
          ${suggested.map(renderCard).join("")}
        </div>
      </section>

      <section>
        <h2>All Images</h2>
        <p class="section-note"><span id="visible-count">${allRecords.length}</span> cards visible. Filter by series or search text to narrow the list.</p>
        <div class="grid" id="all-grid">
          ${allRecords.map(renderCard).join("")}
        </div>
      </section>
    </main>

    <script>
      const searchInput = document.getElementById("search");
      const seriesFilter = document.getElementById("series-filter");
      const visibleCount = document.getElementById("visible-count");
      const allCards = Array.from(document.querySelectorAll("#all-grid .card"));
      const suggestedCards = Array.from(document.querySelectorAll("#suggested-grid .card"));

      function applyFilters() {
        const needle = searchInput.value.trim().toLowerCase();
        const series = seriesFilter.value;
        let visible = 0;

        for (const card of allCards) {
          const matchesSeries = series === "all" || card.dataset.series === series;
          const matchesSearch = !needle || card.dataset.search.includes(needle);
          const show = matchesSeries && matchesSearch;
          card.style.display = show ? "" : "none";
          if (show) visible += 1;
        }

        for (const card of suggestedCards) {
          const matchesSeries = series === "all" || card.dataset.series === series;
          const matchesSearch = !needle || card.dataset.search.includes(needle);
          card.style.display = matchesSeries && matchesSearch ? "" : "none";
        }

        visibleCount.textContent = String(visible);
      }

      searchInput.addEventListener("input", applyFilters);
      seriesFilter.addEventListener("change", applyFilters);
      applyFilters();
    </script>
  </body>
</html>`;
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const currentIds = getCurrentIds();
  const westminster = await loadWestminsterRecords();
  const heidelberg = await loadHeidelbergRecords();
  const allRecords = addFlags([...buildDefaults(), ...westminster, ...heidelberg], currentIds);
  const suggested = buildSuggested(allRecords);
  const html = buildHtml(suggested, allRecords);

  await fs.mkdir(path.dirname(options.output), { recursive: true });
  await fs.writeFile(options.output, html);
  console.log(`wrote ${path.relative(ROOT, options.output)}`);
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exit(1);
});
