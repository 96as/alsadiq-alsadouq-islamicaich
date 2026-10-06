"""Records the speaking close-up for several items in one take (Playwright video, 1440x900) and muxes the real
audio of every item at its start. Same sync marker idea as scripts/mouth-capture.py + mouth-mux.py, one flash
per item: a 28 px square top-left turns white for 250 ms on each `playing` event, its rising edges in the
video give the start of every clip, the square is painted out afterwards with a copy of the neighbouring sky patch (this ffmpeg has no delogo).

  PYTHONUTF8=1 python scripts/lipwide/video.py --items wa28.plain,wa32.plain,... --out <mp4> [--headed]
"""
import argparse
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import numpy as np
from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
FRONT = HERE.parent.parent
URL = 'http://127.0.0.1:5386/avatar-component-preview.html?framing=meadow&state=speaking&bars=0&sim=0'
FFMPEG = os.environ.get('FFMPEG', os.path.expanduser(r'~\.conda\envs\anaconda-ml\Library\bin\ffmpeg.exe'))

ap = argparse.ArgumentParser()
ap.add_argument('--items', required=True)
ap.add_argument('--out', required=True)
ap.add_argument('--gap', type=float, default=0.8)
ap.add_argument('--headed', action='store_true')
args = ap.parse_args()
items = args.items.split(',')

INIT = """
(() => {
  const orig = HTMLMediaElement.prototype.play;
  window.__plays = [];
  HTMLMediaElement.prototype.play = function () {
    window.__aud = this;
    if (!this.__hooked) {
      this.__hooked = true;
      this.addEventListener('playing', () => {
        window.__plays.push(performance.now());
        const m = document.getElementById('__syncmark');
        if (m) { m.style.background = '#fff'; setTimeout(() => { m.style.background = '#000'; }, 250); }
      });
    }
    return orig.apply(this, arguments);
  };
})();
"""


def main():
    tmp = tempfile.mkdtemp()
    cargs = ['--autoplay-policy=no-user-gesture-required', '--disable-background-timer-throttling', '--disable-renderer-backgrounding']
    if args.headed:
        cargs += ['--window-position=-3000,0', '--mute-audio']
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel='msedge', headless=not args.headed, args=cargs)
        ctx = b.new_context(viewport={'width': 1440, 'height': 900}, record_video_dir=tmp, record_video_size={'width': 1440, 'height': 900})
        page = ctx.new_page()
        ctx.add_init_script(INIT)
        page.goto(URL)
        page.wait_for_function('() => window.__voice && window.__control && window.__control.current', timeout=60000)
        page.wait_for_timeout(1500)
        page.evaluate("""() => { const m = document.createElement('div'); m.id = '__syncmark';
          m.style.cssText = 'position:fixed;left:4px;top:4px;width:28px;height:28px;background:#000;z-index:2147483647;pointer-events:none';
          document.body.appendChild(m); }""")
        clips = {c['name']: c for c in page.evaluate('() => window.__voice.clips')}
        page.wait_for_timeout(1500)
        info = []
        for name in items:
            clip = clips[name]
            page.evaluate('(c) => window.__voice.speak(c)', clip)
            t0 = time.time()
            while time.time() - t0 < 6 and not page.evaluate('() => Boolean(window.__voice.playing)'):
                page.wait_for_timeout(30)
            while time.time() - t0 < 60 and page.evaluate('() => Boolean(window.__voice.playing)'):
                page.wait_for_timeout(60)
            dur = page.evaluate('() => window.__aud ? window.__aud.duration : 0')
            info.append({'name': name, 'url': clip['url'], 'dur': dur})
            page.wait_for_timeout(int(args.gap * 1000))
        page.wait_for_timeout(600)
        out_latency = page.evaluate("""async () => { const c = new AudioContext(); await c.resume();
          await new Promise((r) => setTimeout(r, 400)); const v = c.outputLatency || 0; c.close(); return v; }""")
        vpath = page.video.path()
        ctx.close()
        b.close()
    webm = Path(args.out).with_suffix('.webm')
    shutil.copy(vpath, webm)
    shutil.rmtree(tmp, ignore_errors=True)

    RATE = 100
    raw = subprocess.run([FFMPEG, '-hide_banner', '-loglevel', 'error', '-i', str(webm), '-vf', f'fps={RATE},crop=20:20:8:8,format=gray', '-f', 'rawvideo', '-'], capture_output=True).stdout
    fr = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 20, 20)
    bright = fr.mean(axis=(1, 2)) > 128
    edges = [int(e) + 1 for e in np.where(bright[1:] & ~bright[:-1])[0]]
    # merge edges closer than 200 ms
    marks = []
    for e in edges:
        if not marks or e - marks[-1] > 20:
            marks.append(e)
    print('markers', len(marks), 'items', len(items))
    if len(marks) != len(items):
        raise SystemExit('marker count mismatch')
    lat = out_latency
    start = max(0.0, marks[0] / RATE - 1.0)
    cmd = [FFMPEG, '-hide_banner', '-loglevel', 'error', '-y', '-ss', f'{start:.3f}', '-i', str(webm)]
    parts = []
    for i, it in enumerate(info):
        wav = FRONT / 'dev-audio' / ('eval-ar' if it['name'].startswith('wa') else 'eval-en') / Path(it['url']).name
        if not wav.exists():
            raise SystemExit(f'audio not found: {wav}')
        cmd += ['-i', str(wav)]
        d = int(round((marks[i] / RATE + lat - start) * 1000))
        parts.append(f'[{i + 1}:a]adelay={d}|{d}[a{i}]')
    mix = ''.join(f'[a{i}]' for i in range(len(info))) + f'amix=inputs={len(info)}:normalize=0:dropout_transition=0,apad[a]'
    fc = ';'.join(['[0:v]split[v0][v1];[v1]crop=40:40:44:0[patch];[v0][patch]overlay=0:0,fps=30,format=yuv420p[v]'] + parts + [mix])
    cmd += ['-filter_complex', fc, '-map', '[v]', '-map', '[a]', '-c:v', os.environ.get('VCODEC', 'libopenh264'), '-b:v', '6M', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-shortest', args.out]
    subprocess.run(cmd, check=True)
    print(json.dumps({'out': args.out, 'items': info, 'markers_s': [round(m / RATE, 2) for m in marks], 'latency': lat}))


main()
