// Stress detector [MB 6.7]: finds the moments a speaker leans on a word, from the loudness
// envelope alone, so nods and brow flashes land on emphasis rather than on a metronome.
//
// Events (each true for exactly one update call):
//   onset      speech begins after a quiet gap
//   accent     a local loudness peak well above the running mean
//   phraseEnd  speech has stopped for long enough to count as the end of a phrase
// The timeline path may feed `announce()` with a stressed vowel it knows is coming
// (STRESS.lookAhead seconds ahead); the same event fields are then raised early.

import { STRESS } from './actingConfig.js';
import { clamp } from './dynamics.js';

export class StressDetector {
  constructor(config) {
    this.cfg = { ...STRESS, ...config };
    this.events = { onset: false, accent: false, phraseEnd: false, strength: 0 };
    this.reset();
  }

  reset() {
    this.level = 0; // lightly smoothed level
    this.peak = this.cfg.peakMin;
    this.mean = 0;
    this.quietFor = 99; // seconds spent below onsetQuiet x peak
    this.sinceEvent = 99;
    this.armed = true;
    this.speechActive = false;
    this.endArmed = false;
    this.quietSinceSpeech = 0;
    this.announced = 0;
    this.events.onset = this.events.accent = this.events.phraseEnd = false;
    this.events.strength = 0;
  }

  /** The text timeline knows a stressed vowel is coming: raise an accent with this strength. */
  announce(strength = 1) {
    this.announced = Math.max(this.announced, clamp(strength, 0, 1));
  }

  /**
   * @param {number} dt seconds
   * @param {number} level 0..1 loudness
   * @param {boolean} [speaking] false when no clip is playing (resets the end-of-phrase state)
   * @returns {{onset: boolean, accent: boolean, phraseEnd: boolean, strength: number}} reused object
   */
  update(dt, level, speaking = true) {
    const c = this.cfg;
    const ev = this.events;
    ev.onset = ev.accent = ev.phraseEnd = false;
    ev.strength = 0;

    if (!speaking) {
      // Outside a clip: decay, fire a phrase end once if speech had been going.
      if (this.speechActive || this.endArmed) {
        this.quietSinceSpeech += dt;
        if (this.endArmed && this.quietSinceSpeech >= c.phraseQuietFor) {
          ev.phraseEnd = true;
          this.endArmed = false;
        }
        this.speechActive = false;
      }
      this.level = 0;
      this.peak = Math.max(c.peakMin, this.peak * Math.exp(-c.peakDecay * dt));
      this.quietFor += dt;
      this.sinceEvent += dt;
      this.announced = 0;
      return ev;
    }

    // Light smoothing so single-frame spikes do not count.
    const k = 1 - Math.exp(-dt / c.smoothTau);
    this.level += (level - this.level) * k;
    const L = this.level;

    // Peak follower with slow decay, running mean.
    this.peak = Math.max(c.peakMin, L > this.peak ? L : this.peak * Math.exp(-c.peakDecay * dt));
    const km = 1 - Math.exp(-dt / c.meanTau);
    this.mean += (L - this.mean) * km;
    this.sinceEvent += dt;

    const rel = L / this.peak;
    if (rel < c.onsetQuiet) this.quietFor += dt;

    // Onset: rising above onsetRise x peak after a long enough quiet.
    if (rel >= c.onsetRise && this.quietFor >= c.onsetQuietFor) {
      ev.onset = true;
      this.quietFor = 0;
      this.speechActive = true;
      this.endArmed = true;
      this.quietSinceSpeech = 0;
    } else if (rel >= c.onsetRise) {
      this.quietFor = 0;
    }

    // Accent: local peak above the running mean and half the peak; re-arms after falling away.
    const threshold = Math.max(this.mean * c.accentRatio, this.peak * c.accentOfPeak);
    if (L < threshold * c.rearm) this.armed = true;
    if (this.armed && L >= threshold && this.sinceEvent >= c.minGap && this.mean > c.peakMin * 0.4) {
      ev.accent = true;
      ev.strength = clamp((L - this.mean) / Math.max(1e-3, this.peak - this.mean), 0.2, 1);
      this.armed = false;
      this.sinceEvent = 0;
    }
    if (this.announced > 0) {
      if (!ev.accent && this.sinceEvent >= c.minGap) {
        ev.accent = true;
        ev.strength = this.announced;
        this.sinceEvent = 0;
      }
      this.announced = 0;
    }

    // Phrase end: quiet for long enough after speech had been going.
    if (rel < c.phraseQuiet) {
      if (this.endArmed) {
        this.quietSinceSpeech += dt;
        if (this.quietSinceSpeech >= c.phraseQuietFor) {
          ev.phraseEnd = true;
          this.endArmed = false;
          this.speechActive = false;
        }
      }
    } else {
      this.quietSinceSpeech = 0;
    }
    return ev;
  }
}
