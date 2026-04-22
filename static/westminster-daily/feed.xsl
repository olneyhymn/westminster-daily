<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:atom="http://www.w3.org/2005/Atom"
  xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <xsl:output method="html" encoding="UTF-8" indent="yes"
    doctype-system="about:legacy-compat"/>

  <xsl:template match="/">
    <html lang="en">
      <head>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1"/>
        <title><xsl:value-of select="/rss/channel/title"/> &#8212; RSS Feed</title>
        <meta name="robots" content="noindex"/>
        <style>
          :root {
            --parchment: #E8E0D2;
            --cream: #FFFDF7;
            --burgundy: #5C1A2A;
            --gold: #C4A265;
            --brown-muted: #8B7355;
            --brown-light: #A0937D;
            --dark-brown: #2C1810;
            --border-light: #D6CBAF;
          }
          * { box-sizing: border-box; }
          html, body {
            margin: 0;
            padding: 0;
            background: var(--parchment);
            color: var(--dark-brown);
            font-family: Georgia, "Times New Roman", serif;
            font-size: 16px;
            line-height: 1.78;
          }
          a { color: var(--burgundy); text-decoration: none; }
          a:hover { text-decoration: underline; color: #3d1019; }
          .page {
            max-width: 720px;
            margin: 0 auto;
            padding: 24px 16px 64px 16px;
          }
          .card {
            background: var(--cream);
            border: 1px solid var(--border-light);
            border-radius: 4px;
            box-shadow: 0 2px 6px rgba(44, 24, 16, 0.06);
          }
          .masthead {
            text-align: center;
            padding: 28px 24px 20px 24px;
          }
          .masthead .label {
            font-size: 10px;
            letter-spacing: 3px;
            text-transform: uppercase;
            color: var(--brown-light);
            margin-bottom: 6px;
          }
          .masthead h1 {
            margin: 0;
            font-size: 22px;
            letter-spacing: 3px;
            color: var(--dark-brown);
            font-weight: normal;
          }
          .masthead .subtitle {
            margin-top: 8px;
            color: var(--brown-muted);
            font-size: 14px;
            font-style: italic;
          }
          hr.gold {
            border: none;
            border-top: 2px solid var(--gold);
            margin: 0 24px;
          }
          hr.thin {
            border: none;
            border-top: 1px solid var(--border-light);
            margin: 0 24px;
          }
          .notice {
            margin: 0 24px;
            padding: 18px 20px;
            border: 1px solid var(--border-light);
            background: #faf7f0;
            border-radius: 4px;
            color: var(--dark-brown);
            font-size: 14px;
          }
          .notice strong { color: var(--burgundy); }
          .notice code {
            background: #f1ead8;
            padding: 1px 5px;
            border-radius: 3px;
            font-size: 13px;
            word-break: break-all;
          }
          .notice .readers {
            margin-top: 8px;
            color: var(--brown-muted);
            font-size: 13px;
          }
          .section-label {
            text-align: center;
            font-size: 10px;
            letter-spacing: 3px;
            text-transform: uppercase;
            color: var(--brown-light);
            padding: 20px 24px 8px 24px;
          }
          article.entry {
            padding: 20px 24px 8px 24px;
          }
          article.entry + article.entry {
            border-top: 1px solid var(--border-light);
          }
          article.entry h2 {
            margin: 0 0 4px 0;
            font-size: 20px;
            font-style: italic;
            color: var(--burgundy);
            font-weight: normal;
          }
          article.entry h2 a { color: var(--burgundy); }
          article.entry .date {
            font-size: 11px;
            letter-spacing: 2px;
            text-transform: uppercase;
            color: var(--brown-muted);
            margin-bottom: 12px;
          }
          article.entry .body {
            font-size: 15px;
            line-height: 1.78;
            color: var(--dark-brown);
          }
          article.entry .body p { margin: 0 0 12px 0; }
          article.entry .permalink {
            display: inline-block;
            margin: 8px 0 16px 0;
            font-size: 12px;
            letter-spacing: 2px;
            text-transform: uppercase;
            color: var(--brown-muted);
          }
          article.entry .permalink:hover { color: var(--burgundy); }
          footer.page-footer {
            text-align: center;
            padding: 20px 24px 28px 24px;
            color: var(--brown-muted);
            font-size: 12px;
          }
          footer.page-footer a { color: var(--brown-muted); }
        </style>
      </head>
      <body>
        <div class="page">
          <div class="card">
            <header class="masthead">
              <div class="label">RSS Feed</div>
              <h1><xsl:value-of select="/rss/channel/title"/></h1>
              <div class="subtitle"><xsl:value-of select="/rss/channel/description"/></div>
            </header>

            <hr class="gold"/>

            <div class="notice" style="margin-top: 20px;">
              <p style="margin: 0 0 8px 0;">
                <strong>This is a web feed.</strong>
                Paste the address below into a feed reader to subscribe and get new readings automatically.
              </p>
              <code><xsl:value-of select="/rss/channel/atom:link/@href"/></code>
              <div class="readers">
                Popular readers: Feedly, Inoreader, NetNewsWire, Reeder, The Old Reader.
              </div>
            </div>

            <div class="section-label">Recent Readings</div>
            <hr class="thin"/>

            <xsl:for-each select="/rss/channel/item">
              <article class="entry">
                <h2>
                  <a>
                    <xsl:attribute name="href"><xsl:value-of select="link"/></xsl:attribute>
                    <xsl:value-of select="title"/>
                  </a>
                </h2>
                <div class="date">
                  <xsl:value-of select="substring(pubDate, 1, 16)"/>
                </div>
                <div class="body">
                  <xsl:value-of select="description" disable-output-escaping="yes"/>
                </div>
                <a class="permalink">
                  <xsl:attribute name="href"><xsl:value-of select="link"/></xsl:attribute>
                  Read on the web &#8594;
                </a>
              </article>
            </xsl:for-each>

            <hr class="thin"/>
            <footer class="page-footer">
              <a href="/westminster-daily/">reformedconfessions.com/westminster-daily</a>
            </footer>
          </div>
        </div>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
