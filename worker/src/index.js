// Daily Westminster Daily → Buttondown email worker.
//
// On the cron schedule defined in wrangler.toml:
//   1. Compute today's date in US/Eastern.
//   2. Fetch the per-day data.json from the deployed site. These files are
//      generated for the full year on every Pages build, so they survive a
//      missed daily deploy — the worker no longer depends on feed.rss being
//      regenerated that morning.
//   3. Wrap data.title + data.feed in the Buttondown HTML template.
//   4. POST it to the Buttondown API for immediate send.
//
// Secrets required (set via `wrangler secret put` or the deploy workflow):
//   BUTTONDOWN_API_KEY

import template from "./template.html";

const SITE_BASE = "https://reformedconfessions.com/westminster-daily";
const BUTTONDOWN_URL = "https://api.buttondown.com/v1/emails";
const HEALTHCHECK_URL =
  "https://hc-ping.com/b0d50eaf-63d4-40db-9f76-f94629f98662";

export default {
  async scheduled(_event, env, ctx) {
    ctx.waitUntil(runWithHealthcheck(env));
  },
};

async function runWithHealthcheck(env) {
  try {
    await sendDailyEmail(env);
    await fetch(HEALTHCHECK_URL, { method: "POST" }).catch((e) =>
      console.error(`healthcheck success ping failed: ${e.message}`),
    );
  } catch (err) {
    const detail = err?.stack || err?.message || String(err);
    console.error(detail);
    await fetch(`${HEALTHCHECK_URL}/fail`, {
      method: "POST",
      body: detail.slice(0, 10000),
    }).catch((e) =>
      console.error(`healthcheck fail ping failed: ${e.message}`),
    );
    throw err;
  }
}

async function sendDailyEmail(env) {
  if (!env.BUTTONDOWN_API_KEY) {
    throw new Error("BUTTONDOWN_API_KEY is not set on the worker");
  }

  const { month, day } = easternMonthDay(new Date());
  const dataUrl = `${SITE_BASE}/${month}/${day}/data.json`;

  let data = await fetchData(dataUrl);
  if (!data) {
    console.log(`data.json missing for ${month}/${day} — retrying in 5 minutes`);
    await new Promise((r) => setTimeout(r, 5 * 60 * 1000));
    data = await fetchData(dataUrl);
    if (!data) {
      throw new Error(`data.json not available for ${month}/${day} after retry`);
    }
  }
  if (!data.title || !data.feed) {
    throw new Error(`data.json for ${month}/${day} missing title or feed`);
  }

  const entryUrl = `${SITE_BASE}/${month}/${day}`;
  const dayNumber = dayOfYear(month, day);
  // Leading with the day number tells someone joining in August where they
  // are, and makes January 1 legible as a shared restart.
  const subject = `Day ${dayNumber} · ${data.title}`;
  const body = template
    .replaceAll("__ENTRY_URL__", entryUrl)
    .replaceAll("__DAY_NUMBER__", String(dayNumber))
    .replace("__ENTRY_CONTENT__", data.feed);

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
    if (resp.status === 400 && text.includes("email_duplicate")) {
      console.log(`Already sent (duplicate): ${subject}`);
      return;
    }
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

// Day of the year on a 365-day calendar. The reading plan has no Feb 29
// entry, so leap years are deliberately not accounted for -- every date
// maps to the same day number every year, which is what the plan means.
const DAYS_BEFORE_MONTH = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334];

function dayOfYear(month, day) {
  return DAYS_BEFORE_MONTH[Number(month) - 1] + Number(day);
}

async function fetchData(url) {
  const resp = await fetch(url, { cf: { cacheTtl: 0 } });
  if (!resp.ok) return null;
  return await resp.json();
}
