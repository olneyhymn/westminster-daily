// Daily Westminster Daily → Buttondown email worker.
//
// On the cron schedule defined in wrangler.toml:
//   1. Compute today's date in US/Eastern.
//   2. Fetch the site's RSS feed (which is regenerated an hour earlier
//      by the Cloudflare Pages deploy workflow).
//   3. Find the <item> whose <link> matches today's MM/DD path.
//   4. Wrap its content in the Buttondown HTML template.
//   5. POST it to the Buttondown API for immediate send.
//
// Secrets required (set via `wrangler secret put` or the deploy workflow):
//   BUTTONDOWN_API_KEY

import template from "./template.html";

const FEED_URL =
  "https://reformedconfessions.com/westminster-daily/feed.rss";
const BUTTONDOWN_URL = "https://api.buttondown.com/v1/emails";

export default {
  async scheduled(_event, env, ctx) {
    ctx.waitUntil(sendDailyEmail(env));
  },
};

async function sendDailyEmail(env) {
  if (!env.BUTTONDOWN_API_KEY) {
    throw new Error("BUTTONDOWN_API_KEY is not set on the worker");
  }

  const { month, day } = easternMonthDay(new Date());

  const feedResp = await fetch(FEED_URL, { cf: { cacheTtl: 0 } });
  if (!feedResp.ok) {
    throw new Error(`Feed fetch failed: ${feedResp.status}`);
  }
  const feed = await feedResp.text();

  const entry = findEntry(feed, month, day);
  if (!entry) {
    throw new Error(`No feed entry found for ${month}/${day}`);
  }

  const entryUrl = `https://reformedconfessions.com/westminster-daily/${month}/${day}/`;
  const subject = `Westminster Daily : ${entry.title}`;
  const body = template
    .replace("__ENTRY_URL__", entryUrl)
    .replace("__ENTRY_CONTENT__", entry.content);

  const resp = await fetch(BUTTONDOWN_URL, {
    method: "POST",
    headers: {
      Authorization: `Token ${env.BUTTONDOWN_API_KEY}`,
      "Content-Type": "application/json",
      "X-Buttondown-Live-Dangerously": "true",
    },
    body: JSON.stringify({
      subject,
      body,
      email_type: "public",
      status: "about_to_send",
    }),
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Buttondown API ${resp.status}: ${text}`);
  }
  console.log(`Sent: ${subject}`);
}

// --- helpers ---

function easternMonthDay(date) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(date);
  return {
    month: parts.find((p) => p.type === "month").value,
    day: parts.find((p) => p.type === "day").value,
  };
}

function findEntry(feed, month, day) {
  const needle = `/${month}/${day}/`;
  const itemRegex = /<item>([\s\S]*?)<\/item>/g;
  let m;
  while ((m = itemRegex.exec(feed)) !== null) {
    const chunk = m[1];
    if (!chunk.includes(needle)) continue;
    const title = extractTag(chunk, "title");
    const content =
      extractTag(chunk, "content:encoded") ?? extractTag(chunk, "description");
    if (!title || !content) return null;
    return { title: decodeXml(title), content };
  }
  return null;
}

function extractTag(chunk, tag) {
  const re = new RegExp(`<${tag}>([\\s\\S]*?)<\\/${tag}>`);
  const m = chunk.match(re);
  if (!m) return null;
  let v = m[1];
  const cdata = v.match(/^\s*<!\[CDATA\[([\s\S]*?)\]\]>\s*$/);
  if (cdata) v = cdata[1];
  return v;
}

function decodeXml(s) {
  return s
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'");
}
