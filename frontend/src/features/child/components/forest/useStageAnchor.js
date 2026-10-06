import { useEffect } from 'react';

/**
 * Pins an HTML element to something in the 3D stage (Sadiq's head, a prop) without React state per frame.
 *
 * `controlRef` is the ref ForestStage fills with { rt, ... }. `place(rt, size, out)` writes where the
 * element's top-left corner goes (`out.x`, `out.y`, CSS px inside the stage) and may set `out.tail`
 * (a number written to the CSS variable --tail), `out.show` (false hides it) and `out.w` / `out.h`
 * (a size in px, for tap targets that follow an object; 0 leaves the CSS size alone). The hook measures the
 * element only when it resizes, and writes the DOM only when a value moved by 0.5px or more.
 *
 * The element must be absolutely positioned at the stage's top-left (top: 0; left: 0). It is moved with
 * transform, so the element's own animations belong on a child, not on the anchor.
 */
export default function useStageAnchor(controlRef, elRef, place, deps = []) {
  useEffect(() => {
    const el = elRef.current;
    if (!el) return undefined;
    const size = { w: 0, h: 0, radius: 0, stageW: 0, stageH: 0 };
    const out = { x: 0, y: 0, tail: 0, show: true, w: 0, h: 0 };
    const last = { x: -9999, y: -9999, tail: -9999, show: null, w: -1, h: -1 };
    let raf = 0;
    let host = null;

    const measure = () => {
      size.w = el.offsetWidth;
      size.h = el.offsetHeight;
      host = el.closest('[data-arch]');
      size.radius = host ? parseFloat(getComputedStyle(host).borderTopLeftRadius) || 0 : 0;
    };
    measure();
    const ro = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(measure) : null;
    if (ro) {
      ro.observe(el);
      if (host) ro.observe(host);
    }

    const tick = () => {
      raf = window.requestAnimationFrame(tick);
      const rt = controlRef.current?.rt;
      if (!rt) return;
      size.stageW = rt.screen.width;
      size.stageH = rt.screen.height;
      out.show = true;
      out.tail = 0;
      out.w = 0;
      out.h = 0;
      place(rt, size, out);
      if (out.show !== last.show) {
        last.show = out.show;
        el.style.visibility = out.show ? 'visible' : 'hidden';
      }
      if (!out.show) return;
      if (Math.abs(out.x - last.x) >= 0.5 || Math.abs(out.y - last.y) >= 0.5) {
        last.x = out.x;
        last.y = out.y;
        el.style.transform = `translate3d(${out.x.toFixed(1)}px, ${out.y.toFixed(1)}px, 0)`;
      }
      if (out.w > 0 && (Math.abs(out.w - last.w) >= 1 || Math.abs(out.h - last.h) >= 1)) {
        last.w = out.w;
        last.h = out.h;
        el.style.width = `${Math.round(out.w)}px`;
        el.style.height = `${Math.round(out.h)}px`;
      }
      if (Math.abs(out.tail - last.tail) >= 0.5) {
        last.tail = out.tail;
        el.style.setProperty('--tail', `${out.tail.toFixed(1)}px`);
      }
    };
    raf = window.requestAnimationFrame(tick);
    return () => {
      window.cancelAnimationFrame(raf);
      if (ro) ro.disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- `place` is a plain function the caller keeps stable through `deps`
  }, [controlRef, elRef, ...deps]);
}

/** How far the arch's rounded top pushes the usable width in from the side at depth `y` (CSS px). */
export function archInset(radius, y) {
  if (!radius || y >= radius) return 0;
  const dy = radius - Math.max(y, 0);
  return radius - Math.sqrt(Math.max(radius * radius - dy * dy, 0));
}
