import fs from "fs/promises";
import path from "path";
import { fileURLToPath, pathToFileURL } from "url";
import { chromium } from "playwright";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, "..");
const DEFAULT_OUTPUT_DIR = path.join(ROOT, "static", "images", "docs");
const PARchment_IMAGE = path.join(ROOT, "static", "images", "parchment.jpg");

const MONTHS = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

function parseArgs(argv) {
  const options = {
    all: false,
    date: null,
    week: null,
    defaultOnly: false,
    heidelbergDefaultOnly: false,
    outputDir: DEFAULT_OUTPUT_DIR,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];

    if (arg === "--all") {
      options.all = true;
      continue;
    }

    if (arg === "--date") {
      options.date = normalizeDateArg(argv[index + 1]);
      index += 1;
      continue;
    }

    if (arg === "--week") {
      options.week = normalizeWeekArg(argv[index + 1]);
      index += 1;
      continue;
    }

    if (arg === "--default") {
      options.defaultOnly = true;
      continue;
    }

    if (arg === "--heidelberg-default") {
      options.heidelbergDefaultOnly = true;
      continue;
    }

    if (arg === "--out-dir") {
      options.outputDir = path.resolve(ROOT, argv[index + 1]);
      index += 1;
      continue;
    }

    if (arg === "--help" || arg === "-h") {
      printHelp();
      process.exit(0);
    }

    throw new Error(`Unknown argument: ${arg}`);
  }

  if (
    !options.all &&
    !options.date &&
    !options.week &&
    !options.defaultOnly &&
    !options.heidelbergDefaultOnly
  ) {
    options.all = true;
  }

  return options;
}

function printHelp() {
  console.log(`Generate Open Graph images for Westminster Daily.

Usage:
  node scripts/generate-og-images.mjs --all
  node scripts/generate-og-images.mjs --date 03/25
  node scripts/generate-og-images.mjs --week 01
  node scripts/generate-og-images.mjs --default
  node scripts/generate-og-images.mjs --heidelberg-default

Options:
  --all                 Generate all Westminster and Heidelberg images.
  --date MM/DD          Generate one Westminster Daily image.
  --week WW             Generate one Heidelberg Weekly image.
  --default             Generate the default Westminster image only.
  --heidelberg-default  Generate the default Heidelberg image only.
  --out-dir PATH        Override the output directory.
`);
}

function normalizeDateArg(value) {
  if (!value) {
    throw new Error("Missing value for --date");
  }

  const normalized = value.replace(/-/g, "/");
  if (!/^\d{2}\/\d{2}$/.test(normalized)) {
    throw new Error(`Invalid --date value: ${value}`);
  }

  return normalized;
}

function normalizeWeekArg(value) {
  if (!value) {
    throw new Error("Missing value for --week");
  }

  if (!/^\d{1,2}$/.test(value)) {
    throw new Error(`Invalid --week value: ${value}`);
  }

  return value.padStart(2, "0");
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

function stripHtml(value) {
  return decodeEntities(
    String(value || "")
      .replace(/<br\s*\/?>/gi, " ")
      .replace(/<[^>]*>/g, " ")
      .replace(/\s+/g, " ")
      .trim()
  );
}

function decodeEntities(value) {
  return value
    .replace(/&#(\d+);/g, (_, code) => String.fromCharCode(Number(code)))
    .replace(/&nbsp;/g, " ")
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">");
}

function clampText(value, maxLength) {
  const text = String(value || "").trim();
  if (text.length <= maxLength) {
    return text;
  }

  return `${text.slice(0, maxLength - 1).trimEnd()}...`;
}

function normalizeComparable(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function formatMonthDay(shortDate) {
  if (!/^\d{4}$/.test(shortDate || "")) {
    return "";
  }

  const month = Number(shortDate.slice(0, 2));
  const day = Number(shortDate.slice(2, 4));
  return `${MONTHS[month - 1]} ${day}`;
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
      /^Answer$/i.test(trimmed)
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
      if (/^Introduction$/i.test(cleaned)) {
        continue;
      }

      return clampText(cleaned, 170);
    }
  }

  return "";
}

async function readJson(filePath) {
  const raw = await fs.readFile(filePath, "utf8");
  return JSON.parse(raw);
}

async function loadWestminsterRecords() {
  const markdownFiles = await walkFiles(path.join(ROOT, "content"), (filePath) =>
    /content\/\d{2}\/\d{2}\.md$/.test(filePath)
  );

  const records = [];
  for (const markdownPath of markdownFiles) {
    const raw = await fs.readFile(markdownPath, "utf8");
    const { attributes } = splitFrontmatter(raw);
    const shortDate = attributes.short_date;
    if (!shortDate) {
      continue;
    }

    const month = markdownPath.split(path.sep).slice(-2)[0];
    const dayFile = path.basename(markdownPath, ".md");
    const jsonPath = path.join(ROOT, "content", month, dayFile, "data.json");
    const data = await readJson(jsonPath);
    const firstEntry = data.content?.[0] || {};

    const excerptCandidates = [
      firstEntry.answer,
      stripHtml(firstEntry.body),
      firstEntry.question,
    ];

    let excerpt = "";
    for (const candidate of excerptCandidates) {
      if (!candidate) {
        continue;
      }

      const cleaned = clampText(candidate, 180);
      if (normalizeComparable(cleaned) !== normalizeComparable(attributes.pagetitle)) {
        excerpt = cleaned;
        break;
      }
    }

    records.push({
      filename: `${shortDate}-full.png`,
      seriesLabel: "A Daily Reading from the",
      brandTitle: "WESTMINSTER STANDARDS",
      contextLabel: attributes.this_date || formatMonthDay(shortDate),
      title: attributes.pagetitle || data.title || "Westminster Daily",
      detail: firstEntry.long_citation || firstEntry.citation || "",
      excerpt,
      theme: "westminster",
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

    records.push({
      filename: `heidelberg-week-${attributes.week_number}-full.png`,
      seriesLabel: "A Weekly Reading from the",
      brandTitle: "HEIDELBERG CATECHISM",
      contextLabel: attributes.this_week || `Week ${Number(attributes.week_number)}`,
      title: attributes.pagetitle || "Heidelberg Weekly",
      detail: attributes.lords_day
        ? `Lord's Day ${attributes.lords_day}`
        : "",
      excerpt: extractMarkdownPreview(body),
      theme: "heidelberg",
    });
  }

  return records;
}

function buildDefaultWestminsterRecord() {
  return {
    filename: "westminster-default-full.png",
    seriesLabel: "A Daily Reading from the",
    brandTitle: "WESTMINSTER STANDARDS",
    contextLabel: "365-Day Reading Plan",
    title: "Westminster Daily",
    detail: "A daily reading from the Confession and Catechisms",
    excerpt: "Read through the Westminster Standards in a year with a small, steady daily portion.",
    theme: "westminster",
    isDefault: true,
  };
}

function buildDefaultHeidelbergRecord() {
  return {
    filename: "heidelberg-default-full.png",
    seriesLabel: "A Weekly Reading from the",
    brandTitle: "HEIDELBERG CATECHISM",
    contextLabel: "52-Week Reading Plan",
    title: "Heidelberg Weekly",
    detail: "A weekly reading from the Heidelberg Catechism",
    excerpt: "Move through one Lord's Day each week in the same bookish style as the refreshed site.",
    theme: "heidelberg",
    isDefault: true,
  };
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function buildHtml(record) {
  const parchmentUrl = pathToFileURL(PARchment_IMAGE).href;
  const titleLength = record.title.length;
  const titleClass =
    titleLength > 95
      ? "title title-small"
      : titleLength > 68
        ? "title title-medium"
        : "title";
  const excerptClass =
    record.excerpt && record.excerpt.length > 135
      ? "excerpt excerpt-tight"
      : "excerpt";

  return `<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
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

      * {
        box-sizing: border-box;
      }

      html,
      body {
        margin: 0;
        width: 1200px;
        height: 630px;
        overflow: hidden;
      }

      body {
        font-family: Georgia, "Times New Roman", serif;
        color: var(--dark-brown);
        background:
          linear-gradient(rgba(232, 224, 210, 0.9), rgba(232, 224, 210, 0.92)),
          radial-gradient(circle at top left, rgba(255, 255, 255, 0.48), transparent 38%),
          radial-gradient(circle at bottom right, rgba(196, 162, 101, 0.14), transparent 28%),
          url("${parchmentUrl}");
        background-size: cover;
      }

      .canvas {
        width: 1200px;
        height: 630px;
        padding: 48px;
      }

      .card {
        position: relative;
        width: 100%;
        height: 100%;
        background: linear-gradient(180deg, rgba(255, 253, 247, 0.99), rgba(252, 248, 240, 0.98));
        border: 1px solid #c4b697;
        box-shadow:
          0 18px 60px rgba(44, 24, 16, 0.14),
          inset 0 0 0 4px rgba(255, 253, 247, 0.85);
      }

      .card::before {
        content: "";
        position: absolute;
        inset: 12px;
        border: 1px solid var(--border-light);
        pointer-events: none;
      }

      .inner {
        position: absolute;
        inset: 0;
        padding: 52px 74px 46px;
        display: flex;
        flex-direction: column;
      }

      .series-label {
        text-align: center;
        font-size: 12px;
        line-height: 1;
        letter-spacing: 4px;
        text-transform: uppercase;
        color: var(--brown-light);
      }

      .brand {
        margin-top: 14px;
        text-align: center;
        font-size: 28px;
        line-height: 1.1;
        letter-spacing: 4px;
        color: var(--dark-brown);
      }

      .rule {
        width: 100%;
        height: 2px;
        margin: 26px 0 26px;
        background: linear-gradient(90deg, transparent, var(--gold) 12%, var(--gold) 88%, transparent);
      }

      .context {
        align-self: center;
        border: 1px solid var(--border-light);
        padding: 10px 18px 9px;
        font-size: 14px;
        line-height: 1;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: var(--burgundy);
        background: rgba(255, 253, 247, 0.72);
      }

      .title-block {
        flex: 1;
        display: flex;
        flex-direction: column;
        justify-content: center;
        text-align: center;
      }

      .title {
        margin: 24px 0 0;
        font-size: 60px;
        line-height: 1.08;
        font-weight: normal;
        font-style: italic;
        color: var(--burgundy);
        text-wrap: balance;
      }

      .title-medium {
        font-size: 52px;
      }

      .title-small {
        font-size: 45px;
      }

      .detail {
        margin: 18px 0 0;
        font-size: 24px;
        line-height: 1.25;
        color: var(--brown-muted);
      }

      .excerpt {
        width: 82%;
        margin: 20px auto 0;
        font-size: 25px;
        line-height: 1.38;
        color: var(--dark-brown);
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }

      .excerpt-tight {
        font-size: 23px;
      }

      .footer {
        margin-top: 24px;
        text-align: center;
      }

      .ornament {
        color: var(--gold);
        font-size: 14px;
        letter-spacing: 10px;
      }

      .site {
        margin-top: 16px;
        font-size: 13px;
        line-height: 1;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: var(--brown-light);
      }

      .heidelberg .context {
        color: var(--dark-brown);
      }

      .heidelberg .detail {
        color: var(--burgundy);
      }

      .default .title {
        font-size: 66px;
      }

      .default .title-medium {
        font-size: 58px;
      }

      .default .title-small {
        font-size: 50px;
      }

      .default .excerpt {
        width: 74%;
      }
    </style>
  </head>
  <body>
    <div class="canvas ${record.theme} ${record.isDefault ? "default" : ""}">
      <div class="card">
        <div class="inner">
          <div class="series-label">${escapeHtml(record.seriesLabel)}</div>
          <div class="brand">${escapeHtml(record.brandTitle)}</div>
          <div class="rule"></div>
          <div class="context">${escapeHtml(record.contextLabel)}</div>
          <div class="title-block">
            <div class="${titleClass}">${escapeHtml(record.title)}</div>
            ${
              record.detail
                ? `<div class="detail">${escapeHtml(record.detail)}</div>`
                : ""
            }
            ${
              record.excerpt
                ? `<div class="${excerptClass}">${escapeHtml(record.excerpt)}</div>`
                : ""
            }
          </div>
          <div class="footer">
            <div class="ornament">&middot; &middot; &middot;</div>
            <div class="site">reformedconfessions.com</div>
          </div>
        </div>
      </div>
    </div>
  </body>
</html>`;
}

async function renderRecords(records, outputDir) {
  await fs.mkdir(outputDir, { recursive: true });

  const browser = await chromium.launch();
  const page = await browser.newPage({
    viewport: { width: 1200, height: 630 },
    deviceScaleFactor: 1,
  });

  for (const record of records) {
    const outputPath = path.join(outputDir, record.filename);
    await page.setContent(buildHtml(record), { waitUntil: "load" });
    await page.screenshot({
      path: outputPath,
      type: "png",
    });
    console.log(`wrote ${path.relative(ROOT, outputPath)}`);
  }

  await browser.close();
}

function filterRecords(records, predicate) {
  return records.filter(predicate);
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const allWestminsterRecords = await loadWestminsterRecords();
  const allHeidelbergRecords = await loadHeidelbergRecords();

  let records = [];

  if (options.all) {
    records = [
      buildDefaultWestminsterRecord(),
      buildDefaultHeidelbergRecord(),
      ...allWestminsterRecords,
      ...allHeidelbergRecords,
    ];
  } else {
    if (options.defaultOnly) {
      records.push(buildDefaultWestminsterRecord());
    }

    if (options.heidelbergDefaultOnly) {
      records.push(buildDefaultHeidelbergRecord());
    }

    if (options.date) {
      records.push(
        ...filterRecords(
          allWestminsterRecords,
          (record) =>
            `${record.filename.slice(0, 2)}/${record.filename.slice(2, 4)}` === options.date
        )
      );
    }

    if (options.week) {
      records.push(
        ...filterRecords(
          allHeidelbergRecords,
          (record) => record.filename.includes(`week-${options.week}-`)
        )
      );
    }
  }

  if (records.length === 0) {
    throw new Error("No records matched the requested image selection.");
  }

  await renderRecords(records, options.outputDir);
  console.log(`generated ${records.length} image(s)`);
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exit(1);
});
