// A made-up voice for pages that have no audio (the showcase). It gives the avatar the same two
// things the agent's real voice gives it: a level (getAudioLevel, drives the jaw fallback) and a
// viseme state (getLipsync, drives the 14 viseme morphs), both from one syllable clock, so the
// mouth shapes and the opening agree. Nothing here is audio; no Web Audio, no network.

import { VISEME_COUNT, VI } from '../lipsync/visemes.js';

const SYLLABLE_HZ = 5.6; // syllables per second
const PHRASE_SECONDS = 3.4; // a short pause between phrases, which also triggers a blink
const CONSONANTS = [VI.PP, VI.DD, VI.kk, VI.SS, VI.nn, VI.FF, VI.CH, VI.RR];
const VOWELS = [VI.aa, VI.E, VI.aa, VI.O, VI.I, VI.aa, VI.U, VI.E];

// Cheap deterministic hash, so each syllable gets its own shape and the sequence never repeats
// in an obvious loop.
const hash = (n) => {
  let x = (n + 1) * 2654435761;
  x ^= x >>> 15;
  x = Math.imul(x, 2246822519);
  x ^= x >>> 13;
  return (x >>> 0) / 4294967296;
};

/**
 * @param {{ now?: () => number }} [opts] clock in seconds (defaults to performance.now)
 * @returns {{ getLevel: () => number, getLipsync: () => object }}
 */
export function createFakeSpeech({ now = () => performance.now() / 1000 } = {}) {
  const weights = new Float32Array(VISEME_COUNT); // reused every call: no per-frame allocation
  const result = { weights, stress: 0, level: 0, speaking: true, active: true, phraseEnds: 0 };

  // 0..1 loudness of the made-up speech at time t.
  const envelope = (t) => {
    const p = t * SYLLABLE_HZ;
    const frac = p - Math.floor(p);
    const syllable = Math.sin(Math.PI * frac) ** 0.8;
    const inPhrase = (t % PHRASE_SECONDS) / PHRASE_SECONDS;
    const gate = inPhrase < 0.86 ? 1 : 0.04; // the pause at the end of each phrase
    const wobble = 0.7 + 0.3 * Math.sin(t * 2.3 + 1);
    return syllable * gate * wobble;
  };

  return {
    /** RMS-like level, 0 to about 0.13, like the real analyser. */
    getLevel() {
      return 0.13 * envelope(now());
    },
    getLipsync() {
      const t = now();
      const env = envelope(t);
      const p = t * SYLLABLE_HZ;
      const idx = Math.floor(p);
      const frac = p - idx;
      weights.fill(0);
      if (frac < 0.3) {
        weights[CONSONANTS[Math.floor(hash(idx) * CONSONANTS.length)]] = env * 0.8;
      } else {
        weights[VOWELS[Math.floor(hash(idx + 977) * VOWELS.length)]] = env * 0.95;
      }
      let sum = 0;
      for (let i = 1; i < VISEME_COUNT; i++) sum += weights[i];
      weights[VI.sil] = Math.max(0, 1 - sum);
      result.level = 0.13 * env;
      result.stress = env > 0.8 ? 1 : 0;
      result.phraseEnds = Math.floor(t / PHRASE_SECONDS);
      return result;
    },
  };
}
