"""Records the avatar preview speaking one clip (Playwright video in Edge) plus a JSON with the timing
needed to mux the original audio and to pick frames at the same audio timestamps.

  PYTHONUTF8=1 python scripts/mouth-capture.py --url http://127.0.0.1:5341 --clip abdullah_eleven_multilingual_v2_line01 \
      --width 1000 --height 640 --out ../tmp-out/cap-after-1000

Writes <out>.webm and <out>.json. Never clicks mailto: or tel:.

Sync marker: the screencast starts late and by an unknown amount, so the audio start cannot be worked
out from clocks. Instead a 28 px white square is lit in the top-left corner (a black frame the rest of
the time) from the media element's `playing` event for 600 ms. scripts/mouth-mux.py finds the first
bright frame in the video and puts the audio there (plus the browser's output latency, which is
written to the json as outputLatencyS), then paints the square out. The json keeps the clock-based
guess as audioStartInVideoS for reference only.
"""
import argparse
import json
import os
import shutil
import tempfile
import time

from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument('--url', default='http://127.0.0.1:5341')
ap.add_argument('--clip', default='abdullah_eleven_multilingual_v2_line01')
ap.add_argument('--width', type=int, default=1000)
ap.add_argument('--height', type=int, default=640)
ap.add_argument('--out', required=True)
ap.add_argument('--query', default='state=idle')
ap.add_argument('--zoom', type=float, default=2.7)
ap.add_argument('--dy', type=float, default=-0.02)
ap.add_argument('--shot', default='', help='also save a still of the idle page to this png path')
args = ap.parse_args()

INIT = """
(() => {
  const orig = HTMLMediaElement.prototype.play;
  HTMLMediaElement.prototype.play = function () {
    window.__aud = this;
    window.__audPlayPerf = performance.now();
    if (!this.__markerHooked) {
      this.__markerHooked = true;
      this.addEventListener('playing', () => {
        window.__playingPerf = performance.now();
        const m = document.getElementById('__syncmark');
        if (m) {
          m.style.background = '#fff';
          setTimeout(() => { m.style.background = '#000'; }, 600);
        }
      });
    }
    return orig.apply(this, arguments);
  };
})();
"""


def main():
    tmp = tempfile.mkdtemp()
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True, args=['--autoplay-policy=no-user-gesture-required', '--disable-background-timer-throttling', '--disable-renderer-backgrounding'])
        ctx = browser.new_context(viewport={'width': args.width, 'height': args.height}, record_video_dir=tmp, record_video_size={'width': args.width, 'height': args.height})
        ctx.add_init_script(INIT)
        t_page = time.time()
        page = ctx.new_page()
        page.goto(args.url.rstrip('/') + '/avatar-component-preview.html?' + args.query)
        page.wait_for_function('() => window.__voice && window.__control && window.__control.current', timeout=60000)
        page.wait_for_timeout(2500)
        if args.zoom > 1:
            page.evaluate('''([z, dy]) => {
              const c = window.__control.current, cam = c.camera;
              const p = c.bones.head.getWorldPosition(cam.position.clone());
              cam.position.set(p.x, p.y + dy, cam.position.z);
              cam.lookAt(p.x, p.y + dy, 0);
              cam.zoom = z; cam.updateProjectionMatrix();
            }''', [args.zoom, args.dy])
            page.wait_for_timeout(500)
        # hide the preview chrome (buttons, select, debug line) so the footage shows the avatar only
        page.evaluate("() => document.querySelectorAll('button, select, body *').forEach((e) => { if (e.matches('button, select') || (e.children.length === 0 && (e.textContent || '').startsWith('{'))) e.style.visibility = 'hidden'; })")
        page.evaluate("""() => {
          const m = document.createElement('div');
          m.id = '__syncmark';
          m.style.cssText = 'position:fixed;left:4px;top:4px;width:28px;height:28px;background:#000;z-index:2147483647;pointer-events:none';
          document.body.appendChild(m);
        }""")
        if args.shot:
            page.screenshot(path=args.shot)
        origin = page.evaluate('() => performance.timeOrigin')
        clip = next(c for c in page.evaluate('() => window.__voice.clips') if c['name'] == args.clip)
        page.evaluate('(c) => window.__voice.speak(c)', clip)
        t0 = time.time()
        while time.time() - t0 < 5 and not page.evaluate('() => Boolean(window.__voice.playing)'):
            page.wait_for_timeout(30)
        while time.time() - t0 < 60 and page.evaluate('() => Boolean(window.__voice.playing)'):
            page.wait_for_timeout(100)
        page.wait_for_timeout(900)
        play_perf = page.evaluate('() => window.__playingPerf || window.__audPlayPerf')
        out_latency = page.evaluate("""async () => {
          const c = new AudioContext();
          await c.resume();
          await new Promise((r) => setTimeout(r, 400));
          const v = c.outputLatency || 0;
          c.close();
          return v;
        }""")
        audio_dur = page.evaluate('() => window.__aud ? window.__aud.duration : 0')
        vpath = page.video.path()
        ctx.close()
        browser.close()
    start = (origin + play_perf) / 1000 - t_page
    shutil.copy(vpath, args.out + '.webm')
    shutil.rmtree(tmp, ignore_errors=True)
    with open(args.out + '.json', 'w', encoding='utf8') as f:
        json.dump({'audioStartInVideoS': round(start, 3), 'audioDurationS': audio_dur, 'clip': args.clip, 'url': clip['url'], 'outputLatencyS': round(out_latency, 3)}, f)
    print(json.dumps({'audioStartInVideoS': round(start, 3), 'audioDurationS': audio_dur}))


main()
