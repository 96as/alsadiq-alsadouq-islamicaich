import { useEffect } from 'react';
import { gsap } from 'gsap';

/**
 * Pointer parallax for the landing: the arch tilts a little toward the pointer (at most 2.5 degrees,
 * smoothed over 0.6 s), a soft highlight on its rim follows the pointer, and the headline drifts the
 * other way (at most 4 px). On a phone the same values come from the device tilt instead.
 *
 * Nothing here runs under reduced motion (the caller passes `enabled: false`; a change of that setting
 * re-runs the effect, so it follows the system switch live).
 *
 *   tiltRef   the element that rotates (inside a parent with `perspective: 1200px`)
 *   specRef   the rim highlight (its --sx and --sy are set in percent)
 *   driftRef  the headline
 *   controlRef  the forest stage's control ref ({ rt }); the device tilt feeds the camera parallax through rt.pointer
 *   sceneRef  the element whose first tap asks iOS for motion permission
 */
const MAX_DEG = 2.5;
const MAX_DRIFT = 4;
const clamp = (v, lo, hi) => Math.min(Math.max(v, lo), hi);

export default function useSceneTilt({ enabled, tiltRef, specRef, driftRef, controlRef, sceneRef }) {
  useEffect(() => {
    const tilt = tiltRef.current;
    if (!enabled || !tilt) return undefined;
    const spec = specRef.current;
    const drift = driftRef.current;

    const rx = gsap.quickTo(tilt, 'rotationX', { duration: 0.6, ease: 'power3.out' });
    const ry = gsap.quickTo(tilt, 'rotationY', { duration: 0.6, ease: 'power3.out' });
    const dx = drift ? gsap.quickTo(drift, 'x', { duration: 0.6, ease: 'power3.out' }) : null;
    const dy = drift ? gsap.quickTo(drift, 'y', { duration: 0.6, ease: 'power3.out' }) : null;

    // px and py are -1..1 across the whole window.
    const apply = (px, py) => {
      ry(px * MAX_DEG);
      rx(-py * MAX_DEG);
      if (dx) dx(-px * MAX_DRIFT);
      if (dy) dy(-py * MAX_DRIFT * 0.5);
      if (spec) {
        spec.style.setProperty('--sx', `${((px + 1) * 50).toFixed(1)}%`);
        spec.style.setProperty('--sy', `${((py + 1) * 50).toFixed(1)}%`);
      }
    };

    const fine = window.matchMedia('(pointer: fine)').matches;
    const onMove = (e) => {
      if (e.pointerType === 'touch') return;
      apply(clamp((e.clientX / window.innerWidth) * 2 - 1, -1, 1), clamp((e.clientY / window.innerHeight) * 2 - 1, -1, 1));
    };
    const onLeave = () => apply(0, 0);
    if (fine) {
      window.addEventListener('pointermove', onMove, { passive: true });
      document.documentElement.addEventListener('pointerleave', onLeave);
    }

    // Phone tilt: gamma (left/right) and beta (front/back), eased with a low-pass filter. The resting
    // front/back angle is whatever the phone is held at when the first reading arrives. In landscape the
    // two axes swap.
    let base = null;
    let lastAngle = null;
    const lp = { x: 0, y: 0 };
    const onOrient = (e) => {
      if (e.gamma == null || e.beta == null) return;
      const angle = window.screen.orientation?.angle ?? 0;
      let a;
      let b;
      if (angle === 90) {
        a = e.beta;
        b = -e.gamma;
      } else if (angle === 270) {
        a = -e.beta;
        b = e.gamma;
      } else {
        a = e.gamma;
        b = e.beta;
      }
      if (base === null || angle !== lastAngle) {
        base = b;
        lastAngle = angle;
      }
      const x = clamp(a / 18, -1, 1);
      const y = clamp((b - base) / 18, -1, 1);
      lp.x += (x - lp.x) * 0.08;
      lp.y += (y - lp.y) * 0.08;
      const rt = controlRef.current?.rt;
      if (rt) {
        rt.pointer.x = lp.x;
        rt.pointer.y = -lp.y;
      }
      apply(lp.x, lp.y);
    };
    let listening = false;
    const listen = () => {
      if (listening) return;
      listening = true;
      window.addEventListener('deviceorientation', onOrient, { passive: true });
    };
    const coarse = window.matchMedia('(pointer: coarse)').matches;
    const scene = sceneRef.current;
    const ask = () => {
      const DOE = window.DeviceOrientationEvent;
      if (DOE && typeof DOE.requestPermission === 'function') {
        // iOS: the permission prompt may only open from a tap, so it waits for the first tap on the scene.
        DOE.requestPermission().then((r) => { if (r === 'granted') listen(); }).catch(() => {});
      } else {
        listen();
      }
    };
    if (coarse && 'DeviceOrientationEvent' in window) {
      if (scene) scene.addEventListener('pointerdown', ask, { once: true });
      if (typeof window.DeviceOrientationEvent.requestPermission !== 'function') listen();
    }

    return () => {
      window.removeEventListener('pointermove', onMove);
      document.documentElement.removeEventListener('pointerleave', onLeave);
      window.removeEventListener('deviceorientation', onOrient);
      if (scene) scene.removeEventListener('pointerdown', ask);
      gsap.killTweensOf([tilt, drift].filter(Boolean));
      gsap.set(tilt, { rotationX: 0, rotationY: 0 });
      if (drift) gsap.set(drift, { x: 0, y: 0 });
    };
  }, [enabled, tiltRef, specRef, driftRef, controlRef, sceneRef]);
}
