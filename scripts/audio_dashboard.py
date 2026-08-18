# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "elevenlabs>=2.5.0",
#     "inflect>=7.4.0",
# ]
# ///

"""
Serve the voice bake-off as a page you can work through on any machine here.

Picking a cast is a listening job, and listening happens wherever the good
speakers are -- not necessarily at the machine holding the repo. This binds to
every interface so the audition can be done from the couch, and writes the
result straight back to audio/cast.json.

The page also drives a preview: choose a cast, hear those three mockup days
re-rendered in the voices actually chosen, adjust, repeat. That loop is the
only way to judge a handoff between two specific voices, which is the thing a
solo audition structurally cannot show.

Usage:
    uv run scripts/audio_dashboard.py
    uv run scripts/audio_dashboard.py --port 8765
"""

import argparse
import json
import mimetypes
import re
import socket
import subprocess
import sys
import threading
from collections import Counter
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))

from generate_audio import (  # noqa: E402
    CAST_FILE,
    resolve_days,
    respondent_for,
)

BAKEOFF = REPO / "audio" / "bakeoff"

# One preview render at a time. The button is easy to press twice and each run
# spends credits, so a second request while one is in flight is refused rather
# than queued.
PREVIEW_LOCK = threading.Lock()
PREVIEW_STATE = {"status": "idle", "log": ""}


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Voice Bake-off — Westminster Daily</title>
<style>
  :root {
    --ink: #2C1810; --accent: #5C1A2A; --ink-muted: #6B5D45;
    --ornament: #C4A265; --edge: #D6CBAF;
    --surface: #FFFDF7; --recessed: #E8E0D2;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--recessed); color: var(--ink);
    font: 16px/1.78 Georgia, 'Times New Roman', serif;
  }
  .wrap { max-width: 1180px; margin: 0 auto; padding: 0 24px 96px; }
  header { padding: 40px 0 24px; border-bottom: 2px solid var(--ornament); }
  h1 { font-size: 27px; margin: 0 0 6px; color: var(--accent); font-weight: normal; }
  h2 { font-size: 22px; font-style: italic; margin: 40px 0 4px; color: var(--accent); }
  .label {
    font-size: 10px; text-transform: uppercase; letter-spacing: 3px;
    color: var(--ink-muted); margin: 0;
  }
  .lede { color: var(--ink-muted); margin: 6px 0 0; max-width: 62ch; }
  .layout { display: grid; grid-template-columns: 1fr 340px; gap: 40px; align-items: start; }
  @media (max-width: 900px) { .layout { grid-template-columns: 1fr; } }

  .card {
    background: var(--surface); border: 1px solid var(--edge);
    padding: 18px 20px; margin-bottom: 14px;
  }
  .card.mockup { display: block; }
  .card h3 { margin: 0 0 2px; font-size: 18px; font-style: italic; font-weight: normal; }
  .meta { font-size: 13px; color: var(--ink-muted); margin: 0 0 12px; }
  audio { width: 100%; height: 36px; margin-top: 6px; }

  .voice-head { display: flex; justify-content: space-between; align-items: baseline; gap: 16px; }
  .roles { display: flex; gap: 0; margin-top: 12px; flex-wrap: wrap; }
  .roles button {
    font: 11px/1 Georgia, serif; text-transform: uppercase; letter-spacing: 1.5px;
    padding: 9px 13px; background: var(--surface); color: var(--ink-muted);
    border: 1px solid var(--edge); margin-right: -1px; cursor: pointer;
  }
  .roles button:hover { background: var(--recessed); color: var(--ink); }
  .roles button[aria-pressed="true"] {
    background: var(--accent); border-color: var(--accent); color: #FFFDF7;
  }

  aside { position: sticky; top: 24px; }
  aside .card { margin-bottom: 0; }
  .slot { display: flex; justify-content: space-between; gap: 12px; padding: 7px 0;
          border-bottom: 1px solid var(--edge); font-size: 15px; }
  .slot:last-of-type { border-bottom: 0; }
  .slot .who { color: var(--ink-muted); text-align: right; }
  .slot .who.filled { color: var(--ink); }
  ul.picks { margin: 4px 0 0; padding-left: 18px; font-size: 15px; }
  ul.picks li { margin: 2px 0; }
  .empty { color: var(--ink-muted); font-style: italic; }

  .note { font-size: 13px; line-height: 1.6; padding: 10px 12px; margin: 12px 0 0;
          border-left: 3px solid var(--ornament); background: var(--recessed);
          color: var(--ink-muted); }
  .note.bad { border-left-color: var(--accent); color: var(--accent); }

  .actions { display: flex; gap: 8px; margin-top: 16px; }
  .actions button {
    flex: 1; font: 12px/1 Georgia, serif; text-transform: uppercase;
    letter-spacing: 1.5px; padding: 13px 10px; cursor: pointer;
    border: 1px solid var(--accent); background: var(--accent); color: #FFFDF7;
  }
  .actions button.ghost { background: var(--surface); color: var(--accent); }
  .actions button[disabled] { opacity: .45; cursor: default; }

  fieldset { border: 0; border-top: 1px solid var(--edge); margin: 18px 0 0; padding: 14px 0 0; }
  .knob { display: grid; grid-template-columns: 74px 1fr 42px; align-items: center;
          gap: 10px; margin-bottom: 8px; font-size: 13px; color: var(--ink-muted); }
  .knob input { width: 100%; accent-color: var(--accent); }
  .knob output { text-align: right; font-variant-numeric: tabular-nums; color: var(--ink); }
  hr { border: 0; border-top: 1px solid var(--ornament); margin: 30px 0 0; }
  table.rot { width: 100%; border-collapse: collapse; font-size: 14px; margin-top: 8px; }
  table.rot td { padding: 3px 0; border-bottom: 1px solid var(--edge); }
  table.rot td:last-child { text-align: right; font-variant-numeric: tabular-nums; }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <p class="label">Westminster Daily</p>
    <h1>Voice bake-off</h1>
    <p class="lede">Assign a role to each candidate, then preview the cast on three
      real days. The mockups below re-render in whatever you have selected.</p>
  </header>

  <div class="layout">
    <main>
      <h2>Mockups</h2>
      <p class="label">The architecture, not the casting</p>
      <div id="mockups"></div>

      <h2>Candidates</h2>
      <p class="label">Identical text — Larger Catechism 39</p>
      <div id="candidates"></div>
    </main>

    <aside>
      <div class="card">
        <p class="label">Selected cast</p>
        <div class="slot"><span>Catechist</span><span class="who" id="s-cat">—</span></div>
        <div class="slot"><span>Confessor</span><span class="who" id="s-con">—</span></div>
        <div class="slot"><span>Respondents</span><span class="who" id="s-rescount">0</span></div>
        <ul class="picks" id="s-res"></ul>

        <div id="validation"></div>

        <fieldset>
          <p class="label" style="margin-bottom:10px">Delivery</p>
          <div class="knob"><label for="k-stab">Stability</label>
            <input type="range" id="k-stab" min="0" max="1" step="0.05">
            <output id="o-stab"></output></div>
          <div class="knob"><label for="k-style">Style</label>
            <input type="range" id="k-style" min="0" max="1" step="0.05">
            <output id="o-style"></output></div>
          <div class="knob"><label for="k-speed">Speed</label>
            <input type="range" id="k-speed" min="0.7" max="1.2" step="0.01">
            <output id="o-speed"></output></div>
        </fieldset>

        <div class="actions">
          <button id="save">Save cast</button>
          <button id="preview" class="ghost">Preview</button>
        </div>
        <div id="status"></div>
        <div id="rotation"></div>
      </div>
    </aside>
  </div>
</div>

<script>
const state = { catechist: null, confessor: null, respondents: [],
                settings: { stability: 0.45, style: 0.3, speed: 0.95 } };
let manifest = null;

const byId = id => (manifest.candidates.find(c => c.id === id) || {}).name || id;
const shortName = id => byId(id).split(' - ')[0];

function roleOf(id) {
  if (state.catechist === id) return 'catechist';
  if (state.confessor === id) return 'confessor';
  if (state.respondents.includes(id)) return 'respondent';
  return 'none';
}

function setRole(id, role) {
  // A voice holds one job at a time, so clear it from everywhere first.
  if (state.catechist === id) state.catechist = null;
  if (state.confessor === id) state.confessor = null;
  state.respondents = state.respondents.filter(r => r !== id);
  if (role === 'catechist') state.catechist = id;
  if (role === 'confessor') state.confessor = id;
  if (role === 'respondent') state.respondents.push(id);
  render();
}

function renderMockups() {
  document.getElementById('mockups').innerHTML = manifest.mockups.map(m => `
    <div class="card mockup">
      <h3>${m.day}</h3>
      <p class="meta">${m.shape}</p>
      <audio controls preload="metadata" src="/audio/${m.file}?v=${manifest.stamp}"></audio>
    </div>`).join('');
}

function renderCandidates() {
  const roles = [['none','—'],['catechist','Catechist'],
                 ['confessor','Confessor'],['respondent','Respondent']];
  document.getElementById('candidates').innerHTML = manifest.candidates.map(c => `
    <div class="card">
      <div class="voice-head">
        <h3>${c.name}</h3>
        <span class="meta" style="margin:0">${roleOf(c.id) !== 'none' ? '● ' + roleOf(c.id) : ''}</span>
      </div>
      <p class="meta">${[c.age, c.accent, c.use_case].filter(Boolean).join(' · ').replace(/_/g,' ')}</p>
      <audio controls preload="metadata" src="/audio/${c.solo}"></audio>
      <div class="roles">
        ${roles.map(([r,txt]) => `<button data-id="${c.id}" data-role="${r}"
            aria-pressed="${roleOf(c.id)===r}">${txt}</button>`).join('')}
      </div>
    </div>`).join('');
  document.querySelectorAll('.roles button').forEach(b =>
    b.onclick = () => setRole(b.dataset.id, b.dataset.role));
}

function validate() {
  const problems = [];
  if (!state.catechist) problems.push('No catechist chosen — nobody asks the questions.');
  if (!state.confessor) problems.push('No confessor chosen — 171 Confession days have no reader.');
  if (state.respondents.length < 2)
    problems.push('Pick at least two respondents, or the rotation does nothing.');
  const notes = [];
  if (state.respondents.length > 0 && state.respondents.length < 4)
    notes.push(`${state.respondents.length} respondents means each reads about ` +
               `${Math.round(366/state.respondents.length)} days of the year.`);
  if (state.respondents.length > 6)
    notes.push('More than six respondents is hard to tell apart from random.');
  return { problems, notes };
}

function render() {
  renderCandidates();
  document.getElementById('s-cat').textContent = state.catechist ? shortName(state.catechist) : '—';
  document.getElementById('s-cat').className = 'who' + (state.catechist ? ' filled' : '');
  document.getElementById('s-con').textContent = state.confessor ? shortName(state.confessor) : '—';
  document.getElementById('s-con').className = 'who' + (state.confessor ? ' filled' : '');
  document.getElementById('s-rescount').textContent = state.respondents.length;
  document.getElementById('s-res').innerHTML = state.respondents.length
    ? state.respondents.map(r => `<li>${shortName(r)}</li>`).join('')
    : '<li class="empty">none chosen</li>';

  const { problems, notes } = validate();
  document.getElementById('validation').innerHTML =
    problems.map(p => `<p class="note bad">${p}</p>`).join('') +
    notes.map(n => `<p class="note">${n}</p>`).join('');
  const ok = problems.length === 0;
  document.getElementById('save').disabled = !ok;
  document.getElementById('preview').disabled = !ok;
}

function bindKnob(key, input, out, fmt) {
  const i = document.getElementById(input), o = document.getElementById(out);
  i.value = state.settings[key];
  o.textContent = fmt(i.value);
  i.oninput = () => { state.settings[key] = parseFloat(i.value); o.textContent = fmt(i.value); };
}

function say(html, bad) {
  document.getElementById('status').innerHTML = `<p class="note${bad ? ' bad' : ''}">${html}</p>`;
}

async function save() {
  const r = await fetch('/api/save', { method: 'POST',
    headers: {'Content-Type':'application/json'}, body: JSON.stringify(state) });
  const data = await r.json();
  if (!r.ok) { say(data.error, true); return null; }
  say('Saved to <code>audio/cast.json</code>.');
  document.getElementById('rotation').innerHTML =
    `<p class="label" style="margin-top:18px">Rotation across the year</p>
     <table class="rot">${data.rotation.map(([n,d]) =>
       `<tr><td>${n}</td><td>${d} days</td></tr>`).join('')}</table>
     <p class="note">Longest run of the same answering voice: ${data.streak} days.</p>`;
  return data;
}

document.getElementById('save').onclick = save;

document.getElementById('preview').onclick = async () => {
  const btn = document.getElementById('preview');
  if (!await save()) return;
  btn.disabled = true;
  say('Rendering three days in the selected cast — about a minute.');
  const start = await fetch('/api/preview', { method: 'POST' });
  if (!start.ok) { say((await start.json()).error, true); btn.disabled = false; return; }
  const poll = setInterval(async () => {
    const s = await (await fetch('/api/preview')).json();
    if (s.status === 'running') return;
    clearInterval(poll);
    btn.disabled = false;
    if (s.status === 'done') {
      manifest.stamp = Date.now();
      renderMockups();
      say('Mockups re-rendered. Play them above.');
    } else {
      say('Preview failed: <code>' + (s.log || '').slice(-300) + '</code>', true);
    }
  }, 2000);
};

(async () => {
  manifest = await (await fetch('/manifest.json')).json();
  manifest.stamp = Date.now();
  const saved = await (await fetch('/cast.json')).json();
  const known = new Set(manifest.candidates.map(c => c.id));
  const v = saved.voices || {};
  if (known.has(v.catechist)) state.catechist = v.catechist;
  if (known.has(v.confessor)) state.confessor = v.confessor;
  state.respondents = (saved.respondents || [])
    .map(k => v[k]).filter(id => known.has(id));
  if (saved.settings) Object.assign(state.settings, {
    stability: saved.settings.stability, style: saved.settings.style,
    speed: saved.settings.speed });
  bindKnob('stability','k-stab','o-stab', x => (+x).toFixed(2));
  bindKnob('style','k-style','o-style', x => (+x).toFixed(2));
  bindKnob('speed','k-speed','o-speed', x => (+x).toFixed(2) + '×');
  renderMockups();
  render();
})();
</script>
</body>
</html>
"""


def rotation_for(respondent_keys):
    """Day counts per respondent, plus the longest identical-voice streak."""
    days = resolve_days("all")
    sequence = [respondent_for(m, d, respondent_keys) for m, d in days]
    counts = Counter(sequence)
    streak = longest = 1
    for previous, current in zip(sequence, sequence[1:]):
        streak = streak + 1 if previous == current else 1
        longest = max(longest, streak)
    return counts, longest


def save_cast(payload):
    """
    Fold the page's selections into the shape generate_audio.py expects:
    named role slots, and a respondents list naming which slots rotate.
    """
    cast = json.loads(CAST_FILE.read_text())
    voices = {
        "catechist": payload["catechist"],
        "confessor": payload["confessor"],
    }
    keys = []
    for i, voice_id in enumerate(payload["respondents"]):
        key = f"respondent_{chr(ord('a') + i)}"
        voices[key] = voice_id
        keys.append(key)
    cast["voices"] = voices
    cast["respondents"] = keys
    cast["settings"].update(
        {k: payload["settings"][k] for k in ("stability", "style", "speed")}
    )
    CAST_FILE.write_text(json.dumps(cast, indent=2) + "\n")
    return cast, keys


def run_preview(cast):
    """Re-render the mockup days with the saved cast, reusing the bake-off."""
    trio = ",".join([
        cast["voices"]["catechist"],
        cast["voices"][cast["respondents"][0]],
        cast["voices"]["confessor"],
    ])
    try:
        done = subprocess.run(
            ["uv", "run", "scripts/audio_bakeoff.py", "mockup", "--cast", trio],
            cwd=REPO, capture_output=True, text=True, timeout=600,
        )
        PREVIEW_STATE["log"] = (done.stdout + done.stderr)[-2000:]
        PREVIEW_STATE["status"] = "done" if done.returncode == 0 else "failed"
    except Exception as exc:
        PREVIEW_STATE["log"] = str(exc)
        PREVIEW_STATE["status"] = "failed"
    finally:
        PREVIEW_LOCK.release()


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def handle_one_request(self):
        """
        A browser probing an audio file opens a range request, reads the
        header it wanted and hangs up, which surfaces here as a reset or a
        broken pipe. That is the client behaving normally, not an error worth
        a traceback, and fifteen players make it happen fifteen times a load.
        """
        try:
            super().handle_one_request()
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True

    def log_message(self, fmt, *args):
        if "/api/" in (self.path or ""):
            sys.stderr.write(f"  {self.command} {self.path}\n")

    def reply(self, body, content_type="application/json", status=200, extra=None):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def serve_audio(self, relative):
        """
        Stream an mp3, honouring Range. Safari will not play an audio element
        the server cannot seek in, so partial content is not optional here.
        """
        path = (BAKEOFF / relative).resolve()
        if not path.is_file() or BAKEOFF.resolve() not in path.parents:
            self.reply({"error": "not found"}, status=404)
            return
        data = path.read_bytes()
        mime = mimetypes.guess_type(path.name)[0] or "audio/mpeg"
        match = re.match(r"bytes=(\d*)-(\d*)", self.headers.get("Range", "") or "")
        if match:
            start = int(match.group(1) or 0)
            end = int(match.group(2)) if match.group(2) else len(data) - 1
            end = min(end, len(data) - 1)
            chunk = data[start:end + 1]
            self.send_response(206)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Range", f"bytes {start}-{end}/{len(data)}")
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(len(chunk)))
            self.end_headers()
            self.wfile.write(chunk)
            return
        self.reply(data, mime, extra={"Accept-Ranges": "bytes"})

    def do_GET(self):
        route = self.path.split("?")[0]
        if route == "/":
            self.reply(PAGE, "text/html; charset=utf-8")
        elif route == "/manifest.json":
            self.reply((BAKEOFF / "manifest.json").read_text(), "application/json")
        elif route == "/cast.json":
            self.reply(CAST_FILE.read_text(), "application/json")
        elif route == "/api/preview":
            self.reply(dict(PREVIEW_STATE))
        elif route.startswith("/audio/"):
            self.serve_audio(route[len("/audio/"):])
        else:
            self.reply({"error": "not found"}, status=404)

    def do_POST(self):
        route = self.path.split("?")[0]
        if route == "/api/save":
            payload = json.loads(
                self.rfile.read(int(self.headers.get("Content-Length", 0)))
            )
            if not payload.get("catechist") or not payload.get("confessor"):
                self.reply({"error": "Cast is incomplete."}, status=400)
                return
            cast, keys = save_cast(payload)
            counts, streak = rotation_for(keys)
            names = {
                c["id"]: c["name"].split(" - ")[0]
                for c in json.loads(
                    (BAKEOFF / "manifest.json").read_text()
                )["candidates"]
            }
            rotation = [
                (names.get(cast["voices"][k], k), counts.get(k, 0)) for k in keys
            ]
            print(f"  saved cast: {len(keys)} respondents, streak {streak}")
            self.reply({"rotation": rotation, "streak": streak})
        elif route == "/api/preview":
            if not PREVIEW_LOCK.acquire(blocking=False):
                self.reply({"error": "A preview is already running."}, status=409)
                return
            PREVIEW_STATE.update({"status": "running", "log": ""})
            cast = json.loads(CAST_FILE.read_text())
            threading.Thread(target=run_preview, args=(cast,), daemon=True).start()
            self.reply({"status": "running"})
        else:
            self.reply({"error": "not found"}, status=404)


def lan_address():
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("8.8.8.8", 80))
        return probe.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        probe.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()

    if not (BAKEOFF / "manifest.json").exists():
        sys.exit("No manifest. Run: uv run scripts/audio_bakeoff.py solo --day 03/25")

    server = ThreadingHTTPServer((args.host, args.port), partial(Handler))
    # flush: piping the server into a log buffers stdout, and the network
    # address is the one thing the operator needs before anything happens.
    print("  Voice bake-off — Westminster Daily", flush=True)
    print(f"  this machine   http://localhost:{args.port}", flush=True)
    print(f"  on the network http://{lan_address()}:{args.port}", flush=True)
    print(f"  writes to      {CAST_FILE.relative_to(REPO)}\n", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  stopped")


if __name__ == "__main__":
    main()
