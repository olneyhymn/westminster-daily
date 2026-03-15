interface Env {
  BUTTONDOWN_API_KEY: string;
}

interface DataJson {
  title: string;
  feed: string;
}

function getTodayEastern(): { mm: string; dd: string } {
  const now = new Date(
    new Date().toLocaleString("en-US", { timeZone: "America/New_York" })
  );
  const mm = String(now.getMonth() + 1).padStart(2, "0");
  const dd = String(now.getDate()).padStart(2, "0");
  return { mm, dd };
}

function buildEmailHtml(title: string, feedHtml: string, link: string): string {
  return `<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin: 0; padding: 0;">
<!-- Outer parchment background -->
<table cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #E8E0D2;">
  <tr>
    <td align="center" style="padding: 28px 10px;">

      <!-- Page container — fluid width, capped at 580px -->
      <table cellpadding="0" cellspacing="0" border="0" width="100%" style="max-width: 580px; background-color: #FFFDF7; border: 1px solid #C4B697;">

        <!-- Inner border frame (book-page effect) -->
        <tr>
          <td style="padding: 4px;">
            <table cellpadding="0" cellspacing="0" border="0" width="100%" style="border: 1px solid #D6CBAF;">

              <!-- Masthead -->
              <tr>
                <td align="center" style="padding: 30px 24px 10px 24px;">
                  <span style="font-family: Georgia, 'Times New Roman', serif; font-size: 10px; letter-spacing: 3px; text-transform: uppercase; color: #A0937D;">
                    A Daily Reading from the
                  </span>
                </td>
              </tr>
              <tr>
                <td align="center" style="padding: 0 24px 22px 24px;">
                  <a href="https://reformedconfessions.com/westminster-daily/" target="_blank" style="font-family: Georgia, 'Times New Roman', serif; font-size: 20px; color: #2C1810; letter-spacing: 3px; text-decoration: none;">
                    WESTMINSTER STANDARDS
                  </a>
                </td>
              </tr>

              <!-- Gold rule under masthead -->
              <tr>
                <td style="padding: 0 24px;">
                  <table cellpadding="0" cellspacing="0" border="0" width="100%">
                    <tr>
                      <td style="border-bottom: 2px solid #C4A265; font-size: 0; line-height: 0; height: 1px;"> </td>
                    </tr>
                  </table>
                </td>
              </tr>

              <!-- Reading title -->
              <tr>
                <td align="center" style="padding: 26px 24px 0 24px;">
                  <a href="${link}" target="_blank"
                     style="font-family: Georgia, 'Times New Roman', serif; font-size: 22px; font-weight: normal; font-style: italic; color: #5C1A2A; text-decoration: none; line-height: 1.4;">
                    ${title}
                  </a>
                </td>
              </tr>

              <!-- Short centered rule under title -->
              <tr>
                <td align="center" style="padding: 20px 0 6px 0;">
                  <table cellpadding="0" cellspacing="0" border="0" width="60">
                    <tr>
                      <td style="border-bottom: 1px solid #C4A265; font-size: 0; line-height: 0; height: 1px;"> </td>
                    </tr>
                  </table>
                </td>
              </tr>

              <!-- Listen button -->
              <tr>
                <td align="center" style="padding: 10px 24px 20px 24px;">
                  <a href="${link}" target="_blank"
                     style="font-family: Georgia, 'Times New Roman', serif; font-size: 12px; letter-spacing: 2px; text-transform: uppercase; color: #5C1A2A; text-decoration: none; border: 1px solid #D6CBAF; padding: 10px 24px; display: inline-block;">
                    &#9654; Listen to Today&#39;s Reading
                  </a>
                </td>
              </tr>

              <!-- Thin rule before content -->
              <tr>
                <td style="padding: 0 24px;">
                  <table cellpadding="0" cellspacing="0" border="0" width="100%">
                    <tr>
                      <td style="border-bottom: 1px solid #E8E0D2; font-size: 0; line-height: 0; height: 1px;"> </td>
                    </tr>
                  </table>
                </td>
              </tr>

              <!-- Reading content -->
              <tr>
                <td style="padding: 22px 24px 30px 24px; font-family: Georgia, 'Times New Roman', serif; font-size: 16px; line-height: 1.78; color: #2C1810;">
                  ${feedHtml}
                </td>
              </tr>

              <!-- Bottom ornament -->
              <tr>
                <td align="center" style="padding: 0 24px 24px 24px;">
                  <span style="font-family: Georgia, serif; font-size: 11px; color: #C4A265; letter-spacing: 8px;">&#8729; &#8729; &#8729;</span>
                </td>
              </tr>

              <!-- Site links -->
              <tr>
                <td align="center" style="border-top: 1px solid #D6CBAF; background-color: #F5F0E6; padding: 18px 24px 10px 24px;">
                  <a href="https://reformeddeacon.com" style="font-family: Georgia, 'Times New Roman', serif; font-size: 11px; color: #8B7355; text-decoration: none;">reformeddeacon.com</a>
                  <span style="color: #C4A265; padding: 0 6px;">&middot;</span>
                  <a href="https://ulsterworldly.com/" style="font-family: Georgia, 'Times New Roman', serif; font-size: 11px; color: #8B7355; text-decoration: none;">ulsterworldly.com</a>
                  <span style="color: #C4A265; padding: 0 6px;">&middot;</span>
                  <a href="https://readmachen.com/" style="font-family: Georgia, 'Times New Roman', serif; font-size: 11px; color: #8B7355; text-decoration: none;">readmachen.com</a>
                </td>
              </tr>

              <!-- Unsubscribe footer -->
              <tr>
                <td align="center" style="background-color: #F5F0E6; padding: 6px 24px 20px 24px;">
                  <span style="font-family: Georgia, 'Times New Roman', serif; font-size: 10px; color: #A0937D; line-height: 1.6;">
                    Subscribed to
                    <a href="https://reformedconfessions.com/westminster-daily/" target="_blank" style="color: #5C1A2A; text-decoration: none;">Westminster Daily</a>
                     &middot;
                    <a href="{{ unsubscribe_url }}" target="_blank" style="color: #A0937D; text-decoration: underline;">Unsubscribe</a>
                  </span>
                </td>
              </tr>

            </table>
            <!-- /inner border -->
          </td>
        </tr>

      </table>
      <!-- /page container -->

    </td>
  </tr>
</table>
</body>
</html>`;
}

export default {
  async scheduled(
    _controller: ScheduledController,
    env: Env,
    ctx: ExecutionContext
  ): Promise<void> {
    ctx.waitUntil(sendDailyEmail(env));
  },

  async fetch(
    request: Request,
    env: Env,
    ctx: ExecutionContext
  ): Promise<Response> {
    const url = new URL(request.url);
    if (url.pathname === "/__scheduled") {
      ctx.waitUntil(sendDailyEmail(env));
      return new Response("Triggered daily email send", { status: 200 });
    }
    return new Response("Westminster Daily Email Worker", { status: 200 });
  },
};

async function sendDailyEmail(env: Env): Promise<void> {
  const { mm, dd } = getTodayEastern();
  const dataUrl = `https://reformedconfessions.com/westminster-daily/${mm}/${dd}/data.json`;

  const dataResp = await fetch(dataUrl);
  if (!dataResp.ok) {
    console.error(`Failed to fetch ${dataUrl}: ${dataResp.status}`);
    return;
  }

  const data: DataJson = await dataResp.json();
  const link = `https://reformedconfessions.com/westminster-daily/${mm}/${dd}/`;
  const html = buildEmailHtml(data.title, data.feed, link);
  const subject = `Westminster Daily: ${data.title}`;

  const resp = await fetch("https://api.buttondown.com/v1/emails", {
    method: "POST",
    headers: {
      Authorization: `Token ${env.BUTTONDOWN_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      subject,
      body: `<!-- buttondown-editor-mode: plaintext -->\n${html}`,
      status: "about_to_send",
    }),
  });

  if (!resp.ok) {
    const err = await resp.text();
    console.error(`Failed to send email via Buttondown: ${resp.status} ${err}`);
    return;
  }

  const result = (await resp.json()) as { id: string };
  console.log(`Sent Buttondown email ${result.id} for ${mm}/${dd}`);
}
