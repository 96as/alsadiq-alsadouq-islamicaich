// Turns the features of one audio frame into raw, un-smoothed target weights for the 14 visemes.
// Stateful (it remembers the loudest recent level, the last vowel and the last silence) but pure:
// no DOM, no audio, nothing allocated per frame.
//
// What a lip-sync from sound alone can and cannot see:
//   vowels        good: F1 and F2 place the vowel, loudness sets how wide the mouth opens
//   s, sh, ch     good: a hissing high band
//   p, b, m       fair: a short silence inside a phrase (lips pressed), then a low-pitched burst
//   t, d, k, g    fair: the same silence, then a mid or high burst
//   f, v, th      weak: quiet broadband noise
//   n, l, r       weak: heuristics on a quiet voiced sound
// It never reads the text. The mouth follows what is heard, a few milliseconds late.
//
// Language: `lang` 'en' (the default) keeps the five-vowel logic and the English r. 'ar' replaces
// the vowels with the three-class Arabic rule (arabicVowels.js), turns the r detector off (the
// Arabic r is a tap, not the Oculus RR pucker) and uses the fuller vowel amplitude of ARABIC.

import { ArabicVowelRule, VOWEL_A, VOWEL_I } from './arabicVowels.js';
import { ARABIC, CLASSIFIER } from './lipsyncConfig.js';
import { VISEME_COUNT, VI, VOWEL_INDEX } from './visemes.js';

const clamp01 = (x) => (x < 0 ? 0 : x > 1 ? 1 : x);
/** 0 at or below `lo`, 1 at or above `hi`, smooth in between (works for lo > hi too). */
function smooth(x, lo, hi) {
  const t = clamp01((x - lo) / (hi - lo));
  return t * t * (3 - 2 * t);
}
/** Vowel weights (aa, E, I, O, U) when no formants were found: a loose open mouth. */
const OPEN_GUESS = [0.6, 0.2, 0, 0.2, 0];
const damp = (a, b, rate, dt) => b + (a - b) * Math.exp(-rate * dt);

export class VisemeClassifier {
  /**
   * @param {object} [cfg] CLASSIFIER numbers
   * @param {'en'|'ar'} [lang] 'ar' selects the Arabic vowel rule
   */
  constructor(cfg = CLASSIFIER, lang = 'en') {
    this.cfg = cfg;
    this.lang = lang === 'ar' ? 'ar' : 'en';
    this.arabic = new ArabicVowelRule(ARABIC);
    this.raw = new Float32Array(VISEME_COUNT);
    this.vw = new Float32Array(5); // vowel weights, reused every frame
    this.vowelMem = new Float32Array(VISEME_COUNT);
    this.state = {
      level: 0, // loudness 0..1 against the recent peak
      active: false, // the voice is above the gate right now
      speaking: false, // active, or paused for less than phraseGap
      stress: 0, // 0..1, loud voiced syllable (blinks wait for this to pass)
      voiced: 0, // 0..1
      phraseEnds: 0, // counts finished phrases
    };
    this.reset();
  }

  reset() {
    this.peak = 0;
    this.active = false;
    this.sinceSpeech = 99;
    this.inPhrase = false;
    this.prevRms = 0;
    this.lf1 = Math.log(500);
    this.lf2 = Math.log(1500);
    this.event = 0; // viseme index of the stop release being shown, or 0
    this.eventAge = 99;
    this.arabic.reset();
    this.raw.fill(0);
    this.vowelMem.fill(0);
    const s = this.state;
    s.level = 0;
    s.active = false;
    s.speaking = false;
    s.stress = 0;
    s.voiced = 0;
  }

  /**
   * @param {object} f features from FeatureExtractor.analyse()
   * @param {number} dt seconds since the previous call
   * @returns {Float32Array} raw targets, index = VI.*; entry 0 (sil) is left to the smoother
   */
  update(f, dt) {
    const c = this.cfg;
    const raw = this.raw;
    const s = this.state;
    raw.fill(0);

    // Loudness against the recent peak.
    this.peak = Math.max(f.rms, this.peak * Math.exp(-c.peakDecay * dt));
    const full = Math.max(this.peak, c.peakMin);
    const level = clamp01((f.rms - c.levelFloor) / (full - c.levelFloor));
    s.level = level;

    // Voice gate with hysteresis.
    if (this.active) this.active = f.rms > c.gateClose;
    else this.active = f.rms > c.gateOpen;
    if (this.active) {
      this.sinceSpeech = 0;
      this.inPhrase = true;
    } else {
      this.sinceSpeech += dt;
      if (this.inPhrase && this.sinceSpeech > c.phraseGap) {
        this.inPhrase = false;
        s.phraseEnds++;
      }
    }
    s.active = this.active;
    s.speaking = this.inPhrase;

    // Decay the vowel memory (the shape the mouth keeps through consonants).
    const memDecay = Math.exp(-dt / c.carryTau);
    for (const i of VOWEL_INDEX) this.vowelMem[i] *= memDecay;

    if (this.active) {
      // A sudden, unvoiced rise in loudness is a stop release: the first frame after a closure
      // or a quiet gap, or a burst inside running speech. Its spectral centre picks the place.
      const risen = this.prevRms < 0.25 * f.rms || f.rms > c.burstRise * this.prevRms;
      if (risen && f.voicing < c.burstVoicingMax) {
        this.event = f.centroid < c.burstPPMax ? VI.PP : f.centroid < c.burstKKMax ? VI.kk : VI.DD;
        this.eventAge = 0;
      }
    }
    this.prevRms = f.rms;
    this.eventAge += dt;

    if (this.active) {
      this.speech(f, level, dt);
    } else if (this.inPhrase && this.sinceSpeech < c.closureMax) {
      // A short silence inside a phrase: the lips press, still holding some of the last vowel.
      raw[VI.PP] = c.closurePP * (1 - 0.4 * (this.sinceSpeech / c.closureMax));
      for (const i of VOWEL_INDEX) raw[i] = this.vowelMem[i] * c.closureCarry;
      s.voiced = 0;
    } else {
      s.voiced = 0;
    }

    // The stop release that was just heard fades out over a few tens of milliseconds.
    if (this.event) {
      const strength = c.burstWeight * Math.exp(-this.eventAge / c.burstTau);
      if (strength > 0.03) raw[this.event] = Math.max(raw[this.event], strength);
      else this.event = 0;
    }

    // Stress for the blink scheduler.
    const stressRaw = s.voiced * smooth(level, c.stressLevel[0], c.stressLevel[1]);
    s.stress = damp(s.stress, stressRaw, stressRaw > s.stress ? c.stressAttack : c.stressRelease, dt);
    return raw;
  }

  speech(f, level, dt) {
    const c = this.cfg;
    const raw = this.raw;
    const s = this.state;
    // The Arabic voice reads weaker on the voicing measure (the lab clips sit near 0.4 on many
    // fatha frames), so 'ar' has its own, lower gate; the noise branch below uses the same value.
    const voiced =
      this.lang === 'ar'
        ? smooth(f.voicing, ARABIC.voicedLo, ARABIC.voicedHi)
        : smooth(f.voicing, c.voicedLo, c.voicedHi);
    s.voiced = voiced;

    if (this.lang === 'ar') {
      this.arabicVowel(f, level, voiced);
    } else if (voiced > 0.05) {
      // Vowels, from F1 and F2.
      // Track the formants in the log domain, so one noisy frame cannot flip the vowel. A frame
      // with no clear formants keeps the last estimate instead of guessing.
      if (f.f1 > 0 && f.f2 > 0 && level > 0.05) {
        this.lf1 = damp(this.lf1, Math.log(f.f1), c.formantRate, dt);
        this.lf2 = damp(this.lf2, Math.log(f.f2), c.formantRate, dt);
      }
      const hasFormants = f.f1 > 0 && f.f2 > 0;
      const w = this.vw;
      let sum = 0;
      let max = 0;
      for (let k = 0; k < VOWEL_INDEX.length; k++) {
        const proto = c.vowels[VOWEL_INDEX[k]];
        const d1 = (this.lf1 - Math.log(proto[0])) / c.sigmaF1;
        const d2 = (this.lf2 - Math.log(proto[1])) / c.sigmaF2;
        const v = Math.exp(-0.5 * (d1 * d1 + d2 * d2));
        w[k] = v;
        sum += v;
        if (v > max) max = v;
      }
      let conf = hasFormants ? clamp01(max * 1.5) : 0.5;
      if (sum > 1e-6) for (let k = 0; k < 5; k++) w[k] /= sum;
      else w.set(OPEN_GUESS);
      const open = c.openGain * Math.pow(level, c.openCurve) * (c.confMin + (1 - c.confMin) * conf);
      // Nasals and murmurs: almost all energy is low and the sound is quiet.
      const tilt = Math.log10((f.mid + 1e-9) / (f.low + 1e-9)); // about -1 for a vowel, below -3 for a murmur
      const nasal =
        voiced * smooth(tilt, c.nasalTilt[0], c.nasalTilt[1]) * (1 - smooth(level, c.nasalLevelLo, c.nasalLevelHi));
      const vowelAmp = voiced * open * (1 - 0.8 * nasal);
      for (let k = 0; k < VOWEL_INDEX.length; k++) {
        const vi = VOWEL_INDEX[k];
        raw[vi] = w[k] * vowelAmp;
        if (raw[vi] > this.vowelMem[vi]) this.vowelMem[vi] = raw[vi];
      }
      raw[VI.nn] = nasal * c.nasalWeight;
      // American r.
      if (f.f3 > 0 && f.f1 < 700) {
        const rr = smooth(f.f3, c.rrF3[0], c.rrF3[1]) * smooth(f.f2, 700, 1100) * (1 - smooth(f.f2, 1700, 2100));
        raw[VI.RR] = voiced * rr * c.rrWeight * Math.min(1, level * 2);
      }
    }

    // Noise: s, sh, ch, f, th.
    const noise = 1 - voiced;
    if (noise > 0.05) {
      const amp = noise * clamp01(level * c.noiseGain);
      const ss = smooth(f.centroid, c.ssCentroid[0], c.ssCentroid[1]) * smooth(f.sib, c.ssSib[0], c.ssSib[1]);
      const ch =
        smooth(f.centroid, c.chCentroid[0], c.chCentroid[1]) *
        (1 - smooth(f.centroid, c.chCentroidEnd[0], c.chCentroidEnd[1])) *
        smooth(f.high + f.sib, c.chHigh[0], c.chHigh[1]);
      const ff =
        Math.max(0, 1 - ss - ch) *
        smooth(f.high + f.sib, c.ffHigh[0], c.ffHigh[1]) *
        (1 - smooth(level, c.ffLevelMax[0], c.ffLevelMax[1]));
      raw[VI.SS] = amp * ss;
      raw[VI.CH] = amp * ch;
      raw[VI.FF] = amp * ff * c.ffWeight;
    }

    // Through a consonant the mouth keeps part of the last vowel (not through a lip press).
    let consonant = 0;
    for (let i = 1; i < VISEME_COUNT; i++) {
      if (i === VI.PP || VOWEL_INDEX.includes(i)) continue;
      if (raw[i] > consonant) consonant = raw[i];
    }
    if (consonant > 0) {
      for (const i of VOWEL_INDEX) {
        raw[i] = Math.max(raw[i], this.vowelMem[i] * c.carry * consonant);
      }
    }
  }

  /**
   * Arabic vowels and nasals: one of a, i, u from the raw formants; the amplitude follows the
   * loudness but never drops below ARABIC.ampBase, so even a quiet syllable shows its shape.
   */
  arabicVowel(f, level, voiced) {
    const c = this.cfg;
    const a = ARABIC;
    const raw = this.raw;
    if (voiced <= 0.05) return;
    const cls = this.arabic.push(f.f1, f.f2);
    const tilt = Math.log10((f.mid + 1e-9) / (f.low + 1e-9));
    const nasal =
      voiced * smooth(tilt, c.nasalTilt[0], c.nasalTilt[1]) * (1 - smooth(level, c.nasalLevelLo, c.nasalLevelHi));
    const amp = voiced * (a.ampBase + a.ampSpan * Math.pow(level, a.ampCurve)) * (1 - 0.8 * nasal);
    const vi = cls === VOWEL_A ? VI.aa : cls === VOWEL_I ? VI.I : VI.U;
    raw[vi] = amp;
    if (amp > this.vowelMem[vi]) this.vowelMem[vi] = amp;
    raw[VI.nn] = nasal * c.nasalWeight;
  }
}
