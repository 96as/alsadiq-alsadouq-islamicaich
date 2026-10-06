import { useEffect, useState } from 'react';

/** 'low' for phones and touch devices, 'high' otherwise. */
export function detectQuality() {
  try {
    const coarse = window.matchMedia('(pointer: coarse)').matches;
    const narrow = Math.min(window.innerWidth, window.innerHeight) < 700;
    return coarse || narrow ? 'low' : 'high';
  } catch {
    return 'high';
  }
}

/**
 * Instance counts per tier. `tufts` is the number of tufts in each depth ring (6 blades per tuft): ring 0 is the
 * ring around the avatar, with 5-triangle blades, the rest are 3-triangle blades. `springs` is how many near flowers
 * run a real second-order spring (the rest lean by the same formula in the shader).
 */
export const COUNTS = {
  high: { tufts: [800, 1400, 2200, 3600], springs: 280, dandelions: 1100, blooms: 1200, broadleaf: 36, pines: 48, bushes: 40, pollen: 160, sparkles: 26, fireflies: 40, stars: 260 },
  low: { tufts: [300, 520, 840, 1400], springs: 140, dandelions: 650, blooms: 700, broadleaf: 22, pines: 30, bushes: 24, pollen: 80, sparkles: 14, fireflies: 24, stars: 160 },
};

export function maxDpr(quality) {
  return quality === 'low' ? 1.5 : 2;
}

export function webglAvailable() {
  try {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
    if (!gl) return false;
    const lose = gl.getExtension('WEBGL_lose_context');
    if (lose) lose.loseContext();
    return true;
  } catch {
    return false;
  }
}

export function useReducedMotion() {
  const [reduced, setReduced] = useState(() => {
    try {
      return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    } catch {
      return false;
    }
  });
  useEffect(() => {
    let mq;
    try {
      mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    } catch {
      return undefined;
    }
    const onChange = () => setReduced(mq.matches);
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, []);
  return reduced;
}

export function usePageVisible() {
  const [visible, setVisible] = useState(() => document.visibilityState !== 'hidden');
  useEffect(() => {
    const onChange = () => setVisible(document.visibilityState !== 'hidden');
    document.addEventListener('visibilitychange', onChange);
    return () => document.removeEventListener('visibilitychange', onChange);
  }, []);
  return visible;
}

/** Depth rings of the grass (u = metres ahead of the avatar). */
export const GRASS_RINGS = [
  [-5, 6],
  [6, 14],
  [14, 26],
  [26, 46],
];
