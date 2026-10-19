// Synthetic speech-like signals with known content, for the node tests and for tuning. A vowel is
// a glottal pulse train through formant resonators; a fricative is band-shaped noise. No audio
// files are needed, so the tests run anywhere with `npm test`.

const TAU = Math.PI * 2;

/** Small seeded random generator (mulberry32), so every run sees the same noise. */
export function seeded(seed = 1) {
  let a = seed >>> 0;
  return () => {
    a += 0x6d2b79f5;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function resonate(x, freq, bw, sr) {
  const r = Math.exp((-Math.PI * bw) / sr);
  const b1 = 2 * r * Math.cos((TAU * freq) / sr);
  const b2 = -r * r;
  const a0 = 1 - b1 - b2;
  const y = new Float32Array(x.length);
  let y1 = 0;
  let y2 = 0;
  for (let i = 0; i < x.length; i++) {
    const v = a0 * x[i] + b1 * y1 + b2 * y2;
    y[i] = v;
    y2 = y1;
    y1 = v;
  }
  return y;
}

function scaleToRms(x, rms) {
  let s = 0;
  for (let i = 0; i < x.length; i++) s += x[i] * x[i];
  const k = rms / Math.sqrt(s / x.length + 1e-20);
  for (let i = 0; i < x.length; i++) x[i] *= k;
  return x;
}

/** A voiced vowel with formants f1..f3 (Hz), pitch f0, lasting `dur` seconds. */
export function vowel({ f1, f2, f3 = 2600, f0 = 120, dur = 0.3, sr = 48000, rms = 0.1 }) {
  const n = Math.round(dur * sr);
  const x = new Float32Array(n);
  const period = sr / f0;
  for (let t = 0; t < n; t += period) x[Math.floor(t)] = 1;
  let y = resonate(x, 90, 100, sr); // glottal pulse shaping
  y = resonate(y, f1, 70, sr);
  y = resonate(y, f2, 100, sr);
  y = resonate(y, f3, 160, sr);
  y = resonate(y, 3500, 300, sr);
  // lip radiation: +6 dB per octave, which cancels most of the glottal tilt
  for (let i = n - 1; i > 0; i--) y[i] -= y[i - 1];
  // 12 ms raised-cosine fade at both ends
  const fade = Math.round(0.012 * sr);
  for (let i = 0; i < fade && i < n; i++) {
    const g = 0.5 - 0.5 * Math.cos((Math.PI * i) / fade);
    y[i] *= g;
    y[n - 1 - i] *= g;
  }
  return scaleToRms(y, rms);
}

/** Noise shaped around `centre` Hz with bandwidth `bw`, for fricatives. */
export function noise({ centre, bw, dur = 0.2, sr = 48000, rms = 0.03, rng = seeded(7) }) {
  const n = Math.round(dur * sr);
  const x = new Float32Array(n);
  for (let i = 0; i < n; i++) x[i] = rng() * 2 - 1;
  let y = resonate(x, centre, bw, sr);
  y = resonate(y, centre, bw, sr);
  const fade = Math.round(0.01 * sr);
  for (let i = 0; i < fade && i < n; i++) {
    const g = 0.5 - 0.5 * Math.cos((Math.PI * i) / fade);
    y[i] *= g;
    y[n - 1 - i] *= g;
  }
  return scaleToRms(y, rms);
}

export function silence(dur, sr = 48000) {
  return new Float32Array(Math.round(dur * sr));
}

export function concat(...parts) {
  const total = parts.reduce((s, p) => s + p.length, 0);
  const out = new Float32Array(total);
  let o = 0;
  for (const p of parts) {
    out.set(p, o);
    o += p.length;
  }
  return out;
}

/** Adult male formant targets for the five vowels the avatar can show. */
export const VOWEL_FORMANTS = {
  aa: { f1: 780, f2: 1250, f3: 2600 },
  E: { f1: 520, f2: 1850, f3: 2600 },
  I: { f1: 300, f2: 2300, f3: 3000 },
  O: { f1: 480, f2: 850, f3: 2500 },
  U: { f1: 330, f2: 800, f3: 2400 },
};
