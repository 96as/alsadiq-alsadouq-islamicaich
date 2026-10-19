/**
 * The veil between the landing and the child screen: a plain full-screen layer in the time-of-day wall
 * colour that fades in over the arch (which scales up and blurs a little under it), stays while the
 * route changes and the forest warms up, then fades out. No React: it has to outlive the landing.
 *
 *   showVeil(color)          fades the veil in (450 ms) and resolves when it is solid
 *   hideVeilWhen(ready)      fades it out once ready() is true (checked every 100 ms), or after 2.5 s
 *   hideVeil()               fades it out now
 *
 * It always goes away within 4 s of showVeil, whatever happens.
 */
const IN_MS = 450;
const OUT_MS = 500;
const MAX_MS = 4000;

let veil = null;
let killTimer = 0;
let pollTimer = 0;

const reduced = () => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

export function hideVeil() {
  window.clearTimeout(killTimer);
  window.clearInterval(pollTimer);
  const v = veil;
  veil = null;
  if (!v) return;
  v.style.transition = `opacity ${reduced() ? 120 : OUT_MS}ms ease`;
  v.style.opacity = '0';
  window.setTimeout(() => v.remove(), OUT_MS + 80);
}

export function hideVeilWhen(ready) {
  if (!veil) return;
  window.clearInterval(pollTimer);
  const t0 = performance.now();
  pollTimer = window.setInterval(() => {
    let ok = false;
    try {
      ok = Boolean(ready());
    } catch {
      ok = true;
    }
    if (ok || performance.now() - t0 > 2500) hideVeil();
  }, 100);
}

export function showVeil(color) {
  hideVeil();
  const v = document.createElement('div');
  v.setAttribute('aria-hidden', 'true');
  v.setAttribute('data-demo-veil', '');
  Object.assign(v.style, {
    position: 'fixed',
    inset: '0',
    zIndex: '9999',
    pointerEvents: 'none',
    background: color || '#dcefe2',
    opacity: '0',
    transition: `opacity ${reduced() ? 120 : IN_MS}ms ease`,
  });
  document.body.appendChild(v);
  veil = v;
  // Next frame, so the fade runs.
  requestAnimationFrame(() => {
    v.style.opacity = '1';
  });
  killTimer = window.setTimeout(hideVeil, MAX_MS);
  return new Promise((resolve) => window.setTimeout(resolve, reduced() ? 120 : IN_MS));
}
