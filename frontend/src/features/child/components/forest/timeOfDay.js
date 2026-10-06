/**
 * Time of day comes from the device clock only (no location, no weather).
 *   05:00-09:59 morning, 10:00-16:59 noon, 17:00-19:59 maghrib, otherwise night.
 * Maghrib is a fixed window on purpose: it keeps the scene offline-safe and
 * private. The palette is a mood, not a prayer time.
 */
export const TIMES = ['morning', 'noon', 'maghrib', 'night'];

export function timeOfDayFromDate(date = new Date()) {
  const h = date.getHours();
  if (h >= 5 && h < 10) return 'morning';
  if (h >= 10 && h < 17) return 'noon';
  if (h >= 17 && h < 20) return 'maghrib';
  return 'night';
}

// Boundaries in minutes since midnight: [minute, time before, time after].
const EDGES = [
  [5 * 60, 'night', 'morning'],
  [10 * 60, 'morning', 'noon'],
  [17 * 60, 'noon', 'maghrib'],
  [20 * 60, 'maghrib', 'night'],
];
const SOFT_EDGE_MIN = 30;

/**
 * Soft edges: within 30 minutes of a boundary the scene is already moving to the next palette.
 * Returns the current name, the neighbour it is blending toward (or null) and the weight 0..0.5.
 * Device clock only, like timeOfDayFromDate.
 */
export function timeBlendFromDate(date = new Date()) {
  const name = timeOfDayFromDate(date);
  const m = date.getHours() * 60 + date.getMinutes();
  for (const [at, before, after] of EDGES) {
    const d = Math.abs(((m - at + 720 + 1440) % 1440) - 720); // signed distance to the edge, wrapped
    if (d < SOFT_EDGE_MIN && (name === before || name === after)) {
      const toward = name === before ? after : before;
      const w = 0.5 * (1 - d / SOFT_EDGE_MIN); // 0 at 30 min away, 0.5 on the boundary
      return { name, next: toward, weight: Math.max(0, w) };
    }
  }
  return { name, next: null, weight: 0 };
}

export const TIME_LABELS = {
  morning: 'Morning',
  noon: 'Noon',
  maghrib: 'Maghrib',
  night: 'Night',
};

/**
 * Palettes. Colours are sRGB hex, numbers are plain. Every field is blended
 * smoothly when the time of day changes (see palette.js).
 *  bdTint   multiplies the painted backdrop
 *  bdGlow   additive glow near the horizon (bdGlowAmt is its strength)
 *  fog      distance haze, also the colour the ground fades to
 *  grass    multiplies ground, grass and flowers
 *  dew      extra sparkle strength near the path (morning dew)
 *  avatar   CSS filter applied to the avatar layer (the avatar canvas is separate)
 */
export const PALETTES = {
  morning: {
    night: 0,
    dew: 0.5,
    bdTint: '#ffe9dc',
    bdGlow: '#ffd6b0',
    bdGlowAmt: 0.28,
    cloud: '#fff1ea',
    fog: '#d8e4cf',
    fogNear: 9,
    fogFar: 48,
    grass: '#eef6e4',
    ambient: '#fff0e6',
    ambientI: 0.6,
    hemiSky: '#ffe6d6',
    hemiGround: '#6f8a3c',
    hemiI: 0.6,
    sun: '#ffd9a8',
    sunI: 0.9,
    sunPos: [10, 3, 4],
    avatar: { b: 1.03, s: 1.02, sep: 0.06, hue: 0 },
  },
  noon: {
    night: 0,
    dew: 0,
    bdTint: '#ffffff',
    bdGlow: '#fff0b8',
    bdGlowAmt: 0.0,
    cloud: '#ffffff',
    fog: '#c5cd62',
    fogNear: 18,
    fogFar: 70,
    grass: '#ffffff',
    ambient: '#ffffff',
    ambientI: 0.6,
    hemiSky: '#dff0ff',
    hemiGround: '#7a8f3a',
    hemiI: 0.6,
    sun: '#fff1d0',
    sunI: 1.1,
    sunPos: [-6, 10, 8],
    avatar: { b: 1, s: 1, sep: 0, hue: 0 },
  },
  maghrib: {
    night: 0.1,
    dew: 0,
    bdTint: '#ffb394',
    bdGlow: '#ff8a4a',
    bdGlowAmt: 0.42,
    cloud: '#ff9f8a',
    fog: '#d99a5e',
    fogNear: 14,
    fogFar: 64,
    grass: '#ffc59c',
    ambient: '#ffcba8',
    ambientI: 0.55,
    hemiSky: '#ffb08a',
    hemiGround: '#6b4a2e',
    hemiI: 0.55,
    sun: '#ff9650',
    sunI: 1.05,
    sunPos: [-9, 4, 6],
    avatar: { b: 0.97, s: 1.2, sep: 0.28, hue: -10 },
  },
  night: {
    night: 1,
    dew: 0,
    bdTint: '#2a3a78',
    bdGlow: '#5266b8',
    bdGlowAmt: 0.14,
    cloud: '#6f7fc4',
    fog: '#1c2c55',
    fogNear: 10,
    fogFar: 56,
    grass: '#4660a8',
    ambient: '#6676b8',
    ambientI: 0.45,
    hemiSky: '#3a4c96',
    hemiGround: '#121c38',
    hemiI: 0.5,
    sun: '#9db4ff',
    sunI: 0.5,
    sunPos: [4, 8, 6],
    // darker and greyer, not hue-rotated: a hue shift turned the brown fur teal
    avatar: { b: 0.58, s: 0.58, sep: 0, hue: 0 },
  },
};
