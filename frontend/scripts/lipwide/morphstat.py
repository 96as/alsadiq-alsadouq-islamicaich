from pathlib import Path
from playwright.sync_api import sync_playwright
HERE = Path(__file__).parent
with sync_playwright() as pw:
    b = pw.chromium.launch(channel='msedge', headless=True)
    ctx = b.new_context(viewport={'width': 1440, 'height': 900})
    ctx.add_init_script(path=str(HERE / 'helpers.js'))
    page = ctx.new_page()
    page.goto('http://127.0.0.1:5386/avatar-component-preview.html?framing=meadow&state=idle&bars=0&sim=0')
    page.wait_for_function('() => window.__voice && window.__control && window.__control.current', timeout=60000)
    page.wait_for_timeout(2000)
    print(page.evaluate('''() => {
      const c = window.__control.current; let root = c.bones.head; while (root.parent) root = root.parent;
      const out = [];
      root.traverse((o) => { if (o.morphTargetDictionary) { const g = o.geometry; const ma = g.morphAttributes.position;
        for (const [n, i] of Object.entries(o.morphTargetDictionary)) { let s = 0, mx = 0, cnt = 0; const a = ma[i];
          for (let v = 0; v < a.count; v++) { const d = Math.abs(a.getX(v)) + Math.abs(a.getY(v)) + Math.abs(a.getZ(v)); s += d; if (d > 1e-7) cnt++; mx = Math.max(mx, d); }
          out.push(n + ' verts ' + cnt + ' max ' + mx.toFixed(4)); } } });
      return out; }'''))
    b.close()
