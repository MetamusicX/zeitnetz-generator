#!/usr/bin/env python3
"""
Zeitnetz Generator — Web GUI

Opens a local web interface in your browser.
No extra dependencies — uses only Python's built-in libraries.

Usage: double-click this file, or run:
    python3 zeitnetz_gui.py
"""

import http.server
import json
import os
import sys
import io
import threading
import webbrowser
import subprocess
import urllib.parse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = 8470  # "zeit" on a phone keypad = 9348, but let's use something simpler

# ─── Default inputs ──────────────────────────────────────────────────────────

DEFAULT_PITCHES   = "1 11 0 8 9 3 6 4 2 10 5 7"
DEFAULT_PERM      = "1 5 0 6 2 7 11 8 3 10 4 9"
DEFAULT_DURATIONS = "-11 6 9 7 6 6 4 3 10 6 3 1 10"

# ─── HTML Page ───────────────────────────────────────────────────────────────

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Zeitnetz Generator</title>
<style>
  :root {
    --bg: #1a1a2e;
    --surface: #16213e;
    --surface2: #0f3460;
    --accent: #e94560;
    --accent2: #533483;
    --text: #eee;
    --text2: #aab;
    --input-bg: #0d1b3e;
    --border: #2a3a5e;
    --success: #4ade80;
    --mono: 'SF Mono', 'Menlo', 'Consolas', monospace;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    padding: 0;
  }

  .container {
    max-width: 800px;
    margin: 0 auto;
    padding: 30px 24px;
  }

  header {
    margin-bottom: 32px;
    border-bottom: 2px solid var(--accent);
    padding-bottom: 16px;
  }

  header h1 {
    font-size: 28px;
    font-weight: 700;
    letter-spacing: -0.5px;
  }

  header p {
    color: var(--text2);
    margin-top: 4px;
    font-size: 14px;
  }

  .section {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 18px;
  }

  .section h2 {
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: var(--accent);
    margin-bottom: 16px;
  }

  .field {
    margin-bottom: 14px;
  }

  .field:last-child { margin-bottom: 0; }

  .field label {
    display: block;
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 5px;
    color: var(--text);
  }

  .field .hint {
    font-size: 11px;
    color: var(--text2);
    margin-top: 3px;
  }

  .field input[type="text"] {
    width: 100%;
    padding: 10px 12px;
    font-family: var(--mono);
    font-size: 15px;
    background: var(--input-bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
    outline: none;
    transition: border-color 0.2s;
  }

  .field input[type="text"]:focus {
    border-color: var(--accent);
  }

  .field input[type="text"]:disabled {
    opacity: 0.4;
  }

  .radio-group {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .radio-group label {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    font-weight: 400;
    cursor: pointer;
  }

  .radio-group input[type="radio"] {
    accent-color: var(--accent);
  }

  .ts-custom-row {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .ts-custom-row input[type="text"] {
    flex: 1;
  }

  .buttons {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 18px;
  }

  button {
    padding: 11px 22px;
    border: none;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s;
  }

  button:active { transform: scale(0.97); }

  .btn-generate {
    background: var(--accent);
    color: white;
  }
  .btn-generate:hover { background: #d63a52; }

  .btn-validate {
    background: var(--accent2);
    color: white;
  }
  .btn-validate:hover { background: #6b44a8; }

  .btn-discover {
    background: var(--surface2);
    color: white;
    border: 1px solid var(--border);
  }
  .btn-discover:hover { background: #1a4a7a; }

  .btn-reset {
    margin-left: auto;
    background: transparent;
    color: var(--text2);
    border: 1px solid var(--border);
  }
  .btn-reset:hover { color: var(--text); border-color: var(--text2); }

  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }

  .log-section {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
  }

  .log-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 20px;
    border-bottom: 1px solid var(--border);
  }

  .log-header h2 {
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: var(--accent);
    margin: 0;
  }

  .status {
    font-size: 12px;
    padding: 3px 10px;
    border-radius: 20px;
    font-weight: 600;
  }

  .status-idle { background: var(--border); color: var(--text2); }
  .status-running { background: #854d0e; color: #fbbf24; }
  .status-done { background: #14532d; color: var(--success); }
  .status-error { background: #7f1d1d; color: #fca5a5; }

  #log {
    padding: 16px 20px;
    font-family: var(--mono);
    font-size: 12px;
    line-height: 1.6;
    min-height: 200px;
    max-height: 450px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-break: break-all;
    color: #c8d0e0;
    background: #0a0f1e;
  }

  .discover-overlay {
    display: none;
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.6);
    justify-content: center;
    align-items: center;
    z-index: 100;
  }

  .discover-overlay.active { display: flex; }

  .discover-dialog {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 24px;
    width: 360px;
  }

  .discover-dialog h3 {
    margin-bottom: 16px;
    color: var(--accent);
  }

  .discover-dialog .field { margin-bottom: 12px; }

  .discover-dialog .dialog-buttons {
    display: flex;
    gap: 10px;
    margin-top: 18px;
    justify-content: flex-end;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
  .status-running { animation: pulse 1.5s infinite; }
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>Zeitnetz Generator</h1>
    <p>Algorithmic time-grid generator for music composition</p>
  </header>

  <!-- Input Parameters -->
  <div class="section">
    <h2>Input Parameters</h2>
    <div class="field">
      <label>Pitch Row (12 values)</label>
      <input type="text" id="pitches" value="PITCHES_DEFAULT">
      <div class="hint">Integers 0–11 or German names: c cis d dis e f fis g gis a ais h</div>
    </div>
    <div class="field">
      <label>Permutation (12 values)</label>
      <input type="text" id="perm" value="PERM_DEFAULT">
      <div class="hint">A permutation of 0–11</div>
    </div>
    <div class="field">
      <label>Durations (13 values)</label>
      <input type="text" id="durations" value="DURATIONS_DEFAULT">
      <div class="hint">First value may be negative (initial rest)</div>
    </div>
  </div>

  <!-- Time Signatures -->
  <div class="section">
    <h2>Time Signatures</h2>
    <div class="radio-group">
      <label>
        <input type="radio" name="ts_mode" value="default" checked
               onchange="toggleCustomTS()">
        Default (Mouvement wedge pattern, 105 bars cyclic)
      </label>
      <label>
        <input type="radio" name="ts_mode" value="auto"
               onchange="toggleCustomTS()">
        Auto-generate based on piece length
      </label>
      <label class="ts-custom-row">
        <input type="radio" name="ts_mode" value="custom"
               onchange="toggleCustomTS()">
        Custom sequence:
        <input type="text" id="ts_custom" value="7 6 5 4 3 2 1 1 2 3 4 5 6 7"
               disabled placeholder="values 1–7">
      </label>
    </div>
  </div>

  <!-- Output -->
  <div class="section">
    <h2>Output Directory</h2>
    <div class="field">
      <input type="text" id="outdir" value="OUTPUT_DEFAULT">
      <div class="hint">MusicXML files will be saved here</div>
    </div>
  </div>

  <!-- Buttons -->
  <div class="buttons">
    <button class="btn-generate" onclick="runGenerate()" id="btnGenerate">Generate</button>
    <button class="btn-validate" onclick="runValidate()" id="btnValidate">Validate Only</button>
    <button class="btn-discover" onclick="showDiscover()" id="btnDiscover">Discover</button>
    <button class="btn-reset" onclick="resetDefaults()">Reset to Defaults</button>
  </div>

  <!-- Log -->
  <div class="log-section">
    <div class="log-header">
      <h2>Log</h2>
      <span class="status status-idle" id="status">Ready</span>
    </div>
    <div id="log">Waiting for command...\n</div>
  </div>
</div>

<!-- Discover Dialog -->
<div class="discover-overlay" id="discoverOverlay">
  <div class="discover-dialog">
    <h3>Discovery Settings</h3>
    <div class="field">
      <label>Number of trials</label>
      <input type="text" id="disc_trials" value="100">
    </div>
    <div class="field">
      <label>Random seed (optional)</label>
      <input type="text" id="disc_seed" value="42">
    </div>
    <div class="field">
      <label>Minimum families</label>
      <input type="text" id="disc_minfam" value="30">
    </div>
    <div class="dialog-buttons">
      <button class="btn-reset" onclick="hideDiscover()">Cancel</button>
      <button class="btn-discover" onclick="runDiscover()">Run Discovery</button>
    </div>
  </div>
</div>

<script>
const DEFAULTS = {
  pitches: "PITCHES_DEFAULT",
  perm: "PERM_DEFAULT",
  durations: "DURATIONS_DEFAULT"
};

function toggleCustomTS() {
  const mode = document.querySelector('input[name="ts_mode"]:checked').value;
  document.getElementById('ts_custom').disabled = (mode !== 'custom');
}

function resetDefaults() {
  document.getElementById('pitches').value = DEFAULTS.pitches;
  document.getElementById('perm').value = DEFAULTS.perm;
  document.getElementById('durations').value = DEFAULTS.durations;
  document.querySelector('input[name="ts_mode"][value="default"]').checked = true;
  toggleCustomTS();
}

function setStatus(text, cls) {
  const el = document.getElementById('status');
  el.textContent = text;
  el.className = 'status status-' + cls;
}

function setButtons(disabled) {
  document.getElementById('btnGenerate').disabled = disabled;
  document.getElementById('btnValidate').disabled = disabled;
  document.getElementById('btnDiscover').disabled = disabled;
}

function clearLog() {
  document.getElementById('log').textContent = '';
}

function appendLog(text) {
  const el = document.getElementById('log');
  el.textContent += text;
  el.scrollTop = el.scrollHeight;
}

function getInputs() {
  return {
    pitches: document.getElementById('pitches').value,
    perm: document.getElementById('perm').value,
    durations: document.getElementById('durations').value,
    ts_mode: document.querySelector('input[name="ts_mode"]:checked').value,
    ts_custom: document.getElementById('ts_custom').value,
    outdir: document.getElementById('outdir').value
  };
}

async function runCommand(endpoint, body) {
  clearLog();
  setStatus('Running...', 'running');
  setButtons(true);

  try {
    const resp = await fetch(endpoint, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    });

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const {value, done} = await reader.read();
      if (done) break;
      appendLog(decoder.decode(value));
    }

    setStatus('Done', 'done');
  } catch (e) {
    appendLog('\nError: ' + e.message + '\n');
    setStatus('Error', 'error');
  } finally {
    setButtons(false);
  }
}

function runGenerate() {
  runCommand('/api/generate', getInputs());
}

function runValidate() {
  runCommand('/api/validate', getInputs());
}

function showDiscover() {
  document.getElementById('discoverOverlay').classList.add('active');
}

function hideDiscover() {
  document.getElementById('discoverOverlay').classList.remove('active');
}

function runDiscover() {
  hideDiscover();
  runCommand('/api/discover', {
    trials: document.getElementById('disc_trials').value,
    seed: document.getElementById('disc_seed').value,
    min_families: document.getElementById('disc_minfam').value
  });
}
</script>
</body>
</html>"""

# ─── Server ──────────────────────────────────────────────────────────────────

class ZeitnetzHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler for the Zeitnetz GUI."""

    def log_message(self, format, *args):
        """Suppress default access logging."""
        pass

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            page = HTML_PAGE
            page = page.replace("PITCHES_DEFAULT", DEFAULT_PITCHES)
            page = page.replace("PERM_DEFAULT", DEFAULT_PERM)
            page = page.replace("DURATIONS_DEFAULT", DEFAULT_DURATIONS)
            default_out = os.path.join(SCRIPT_DIR, "output")
            page = page.replace("OUTPUT_DEFAULT", default_out)

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(page.encode())
        else:
            self.send_error(404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        if self.path == "/api/generate":
            self._run_generate(body)
        elif self.path == "/api/validate":
            self._run_validate(body)
        elif self.path == "/api/discover":
            self._run_discover(body)
        else:
            self.send_error(404)

    def _stream_response(self):
        """Set up streaming response headers."""
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Transfer-Encoding", "chunked")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

    def _send_chunk(self, text):
        """Send a chunk of text."""
        data = text.encode("utf-8")
        self.wfile.write(f"{len(data):x}\r\n".encode())
        self.wfile.write(data)
        self.wfile.write(b"\r\n")
        self.wfile.flush()

    def _end_chunks(self):
        """End chunked response."""
        self.wfile.write(b"0\r\n\r\n")
        self.wfile.flush()

    def _run_subprocess(self, cmd):
        """Run a subprocess and stream its output."""
        self._stream_response()
        self._send_chunk(f"$ {' '.join(cmd)}\n\n")

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=SCRIPT_DIR,
            )
            for line in iter(proc.stdout.readline, ""):
                self._send_chunk(line)
            proc.wait()

            if proc.returncode == 0:
                self._send_chunk("\n--- Done ---\n")
            else:
                self._send_chunk(
                    f"\n--- Finished with errors (code {proc.returncode}) ---\n"
                )
        except Exception as e:
            self._send_chunk(f"\nError: {e}\n")

        self._end_chunks()

    def _clean(self, val):
        """Strip commas so users can paste comma-separated values."""
        return val.replace(",", " ")

    def _run_generate(self, body):
        cmd = [sys.executable, "-m", "zeitnetz", "generate"]
        cmd += ["--pitches", self._clean(body.get("pitches", DEFAULT_PITCHES))]
        cmd += ["--perm", self._clean(body.get("perm", DEFAULT_PERM))]
        cmd += ["--durations", self._clean(body.get("durations", DEFAULT_DURATIONS))]
        cmd += ["--output-dir", body.get("outdir", os.path.join(SCRIPT_DIR, "output"))]

        ts_mode = body.get("ts_mode", "default")
        if ts_mode == "auto":
            cmd.append("--auto-ts")
        elif ts_mode == "custom":
            ts_val = body.get("ts_custom", "").strip()
            if ts_val:
                cmd += ["--ts-sequence", ts_val]

        # Ensure output dir exists
        outdir = body.get("outdir", os.path.join(SCRIPT_DIR, "output"))
        os.makedirs(outdir, exist_ok=True)

        self._run_subprocess(cmd)

    def _run_validate(self, body):
        cmd = [sys.executable, "-m", "zeitnetz", "validate"]
        cmd += ["--pitches", self._clean(body.get("pitches", DEFAULT_PITCHES))]
        cmd += ["--perm", self._clean(body.get("perm", DEFAULT_PERM))]
        cmd += ["--durations", self._clean(body.get("durations", DEFAULT_DURATIONS))]
        self._run_subprocess(cmd)

    def _run_discover(self, body):
        cmd = [sys.executable, "-m", "zeitnetz", "discover"]
        cmd += ["--trials", str(body.get("trials", "100"))]
        cmd += ["--min-families", str(body.get("min_families", "30"))]
        seed = body.get("seed", "").strip()
        if seed:
            cmd += ["--seed", seed]
        self._run_subprocess(cmd)


def main():
    server = http.server.HTTPServer(("127.0.0.1", PORT), ZeitnetzHandler)
    url = f"http://127.0.0.1:{PORT}"

    print(f"\n  Zeitnetz Generator — Web GUI")
    print(f"  Running at: {url}")
    print(f"  Press Ctrl+C to stop.\n")

    # Open browser after a short delay
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Shutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
