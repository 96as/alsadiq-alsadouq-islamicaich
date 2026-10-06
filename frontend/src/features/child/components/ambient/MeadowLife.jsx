import { useEffect, useRef, useState } from 'react';
import MeadowImage from '../MeadowImage';
import { MEADOW_IMAGE, meadowCap, meadowFile, isNarrowMeadow } from '../meadowFraming';
import { detectQuality, usePageVisible, useReducedMotion } from '../forest/quality';
import { createMeadowGL, pickWidth } from './meadowLifeGL';
import { windNow } from '../forest/wind/windClock';

/**
 * The lead's painted meadow, alive: a WebGL2 layer over the picture (masked warp of the grass and trees, a gust
 * colour wave, cloud shadows and wisps, light shafts, painted blades, pollen and seeds), all driven by the one wind
 * field the forest and the foreground strip use. The painting itself is never replaced.
 *
 * MeadowImage stays underneath as the poster and the fallback: if WebGL2 is missing, a shader fails or the
 * context is lost, the canvas is hidden and the child sees exactly what they saw before.
 *
 * Drop-in for <MeadowImage anchored />: same props.
 */
export default function MeadowLife({ anchored = true, className = '' }) {
  const rootRef = useRef(null);
  const canvasRef = useRef(null); // the canvas is made per effect run: a force-lost context cannot be reused (StrictMode remounts)
  const apiRef = useRef(null);
  const reduced = useReducedMotion();
  const visible = usePageVisible();
  const [live, setLive] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const reducedRef = useRef(reduced);
  const visibleRef = useRef(visible);

  useEffect(() => {
    reducedRef.current = reduced;
    apiRef.current?.setMotion(reduced);
  }, [reduced]);
  useEffect(() => {
    visibleRef.current = visible;
  }, [visible]);
  useEffect(() => {
    if (canvasRef.current) canvasRef.current.style.opacity = live ? '1' : '0';
  }, [live]);

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return undefined;
    const canvas = document.createElement('canvas');
    canvas.setAttribute('aria-hidden', 'true');
    canvas.className = 'absolute inset-0 h-full w-full';
    canvas.style.opacity = '0';
    canvas.style.transition = 'opacity 350ms ease-out';
    const quality = detectQuality();
    const api = createMeadowGL(canvas, { quality, anchored });
    if (!api) return undefined;
    root.appendChild(canvas);
    canvasRef.current = canvas;
    apiRef.current = api;
    api.setMotion(reducedRef.current);

    let raf = 0;
    let disposed = false;
    // DPR 2 on both tiers: this canvas covers the sharp <img>, so a lower cap blurs the painting on every
    // phone and HiDPI laptop (reviewer measured 7x less detail at DPR 1 on a DPR-3 phone). The base pass is one
    // full-screen triangle, so the cost is small; the adaptive step-down below still protects slow GPUs.
    let dprCap = 2;
    let slowMs = 0;
    let lastFrame = 0;
    let firstDrawn = false;
    let loadedWidth = 0;
    let timeOverride = null;
    let paused = false;

    const measure = () => {
      const r = root.getBoundingClientRect();
      if (r.width < 1 || r.height < 1) return;
      const dpr = Math.min(window.devicePixelRatio || 1, dprCap);
      api.resize(r.width, r.height, dpr);
      maybeLoadBetterImage(r.width, r.height, dpr);
    };

    const loadImage = (width, narrow) => {
      const url = `${MEADOW_IMAGE.dir}${meadowFile(width, narrow)}`; // cards-spec (05) perf: the same file the <picture> took, so it is one download
      const img = new Image();
      img.decoding = 'async';
      img.onload = () => {
        if (disposed) return;
        try {
          api.setImage(img);
          loadedWidth = width;
        } catch (e) {
          console.warn('MeadowLife image upload failed', e);
        }
      };
      img.src = url;
    };

    let requested = 0;
    let requestedNarrow = false;
    function maybeLoadBetterImage(w, h, dpr) {
      const narrow = isNarrowMeadow(); // cards-spec (05) perf: a portrait phone takes the narrow tier (meadowFraming.js); a rotation re-requests
      if (narrow !== requestedNarrow) {
        requestedNarrow = narrow;
        requested = 0;
      }
      const imgW = Math.max(w / MEADOW_IMAGE.aspect, h) * MEADOW_IMAGE.aspect;
      const cap = meadowCap(quality); // cards-spec (05) perf review: the same cap the narrow <img> uses (MeadowImage.jsx), so both take one file
      const want = pickWidth(imgW * dpr, cap);
      if (want > requested) {
        requested = want;
        loadImage(want, narrow);
      }
    }

    const frame = (now) => {
      raf = requestAnimationFrame(frame);
      if (paused || !visibleRef.current || !api.isReady()) return;
      const t = timeOverride != null ? timeOverride : windNow(now); // the one painted-meadow clock, shared with the foreground strip
      api.render(t);
      if (!firstDrawn) {
        firstDrawn = true;
        setLive(true);
      }
      // adaptive resolution: 2 -> 1.5 -> 1.25 -> 1.0 when the mean frame time stays above 24 ms for 2 s
      if (lastFrame) {
        const dt = now - lastFrame;
        if (dt > 24 && dt < 200) slowMs += dt;
        else slowMs = Math.max(0, slowMs - dt);
        if (slowMs > 2000 && dprCap > 1) {
          dprCap = dprCap > 1.5 ? 1.5 : dprCap > 1.25 ? 1.25 : 1;
          slowMs = 0;
          measure();
        }
      }
      lastFrame = now;
    };

    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(root);
    raf = requestAnimationFrame(frame);

    const onLost = (e) => {
      e.preventDefault();
      setLive(false);
      cancelAnimationFrame(raf);
    };
    const onRestored = () => setAttempt((n) => n + 1);
    canvas.addEventListener('webglcontextlost', onLost);
    canvas.addEventListener('webglcontextrestored', onRestored);

    // A dev handle for the checks (gust sync, frozen-time pairs, switching layers). Not shipped.
    if (import.meta.env.DEV) {
      window.__meadowLife = {
        api,
        setTime: (t) => {
          timeOverride = t;
        },
        pause: (p) => {
          paused = p;
        },
        render: (t) => api.render(t),
        readGust: (x, y, t) => api.readGust(x, y, t),
        state: api.state,
        get loadedWidth() {
          return loadedWidth;
        },
      };
    }

    return () => {
      disposed = true;
      cancelAnimationFrame(raf);
      ro.disconnect();
      canvas.removeEventListener('webglcontextlost', onLost);
      canvas.removeEventListener('webglcontextrestored', onRestored);
      api.dispose();
      canvas.remove();
      canvasRef.current = null;
      apiRef.current = null;
      setLive(false);
      if (import.meta.env.DEV) delete window.__meadowLife;
    };
  }, [anchored, attempt]);

  return (
    <div ref={rootRef} className={`pointer-events-none absolute inset-0 overflow-hidden ${className}`} data-meadow-life={live ? 'live' : 'poster'}>
      <MeadowImage anchored={anchored} />
    </div>
  );
}
