// Features, classifier and smoother chained into one object that turns audio frames into
// 14 smoothed viseme weights. No DOM and no Web Audio, so it runs live (visemeDriver.js),
// offline on a decoded clip (analyseBuffer below) and in node tests, with the same result.

import { FFT_SIZE, FeatureExtractor, createFeatures } from './dsp.js';
import { HybridLipsync } from './hybridLipsync.js';
import { TimelineSync } from './timelineSync.js';
import { VisemeClassifier } from './visemeClassifier.js';
import { VisemeSmoother } from './visemeSmoother.js';

export class LipsyncEngine {
  /**
   * @param {number} sampleRate of the audio frames given to process(), in Hz
   * @param {{lang?: 'en'|'ar'}} [opts] 'ar' selects the Arabic vowel mode (default 'en')
   */
  constructor(sampleRate, { lang = 'en' } = {}) {
    this.lang = lang === 'ar' ? 'ar' : 'en';
    this.extractor = new FeatureExtractor(sampleRate);
    this.classifier = new VisemeClassifier(undefined, this.lang);
    this.smoother = new VisemeSmoother();
    this.features = createFeatures();
    this.weights = this.smoother.out;
  }

  reset() {
    this.extractor.reset();
    this.classifier.reset();
    this.smoother.reset();
  }

  /**
   * @param {Float32Array} samples newest audio, newest last, at least FFT_SIZE (2048) long
   * @param {number} dt seconds since the previous call
   * @returns {Float32Array} the 14 weights (reused between calls)
   */
  process(samples, dt) {
    this.extractor.analyse(samples, this.features);
    const raw = this.classifier.update(this.features, dt);
    return this.smoother.step(raw, dt);
  }
}

/**
 * Run the whole pipeline over a decoded clip at a fixed frame rate (default 60). Used by the dev
 * page for the timeline and by the tests. The frames are copies, safe to keep.
 * @param {Float32Array} pcm mono samples
 * @param {number} sampleRate
 * @param {{fps?: number, lang?: 'en'|'ar', timeline?: Array<{t: number, msg: object}>,
 *   outputLatencyMs?: number}} [opts] timeline replays lk.lipsync messages: each `msg` (see
 *   timelineSync.js) is delivered at `t` seconds (negative: before the audio starts)
 */
export function analyseBuffer(pcm, sampleRate, { fps = 60, lang = 'en', timeline = null, outputLatencyMs = 0 } = {}) {
  const base = new LipsyncEngine(sampleRate, { lang });
  const sync = timeline ? new TimelineSync() : null;
  const events = timeline ? [...timeline].sort((a, b) => a.t - b.t) : [];
  let nextEvent = 0;
  const engine = new HybridLipsync(base, { sync, outputLatencyMs });
  const dt = 1 / fps;
  const hop = sampleRate / fps;
  const window = new Float32Array(FFT_SIZE);
  const frames = [];
  const count = Math.ceil(pcm.length / hop);
  for (let n = 0; n < count; n++) {
    const end = Math.min(pcm.length, Math.round((n + 1) * hop));
    const begin = end - FFT_SIZE;
    if (begin >= 0) window.set(pcm.subarray(begin, end));
    else {
      window.fill(0);
      window.set(pcm.subarray(0, end), FFT_SIZE - end);
    }
    const t = (n + 1) * dt;
    while (nextEvent < events.length && events[nextEvent].t <= t) {
      sync.push(events[nextEvent].msg, events[nextEvent].t * 1000);
      nextEvent++;
    }
    const weights = engine.process(window, dt, t * 1000);
    const f = engine.features;
    const s = engine.classifier.state;
    frames.push({
      t,
      weights: Float32Array.from(weights),
      timed: engine.timed,
      rms: f.rms,
      level: s.level,
      voicing: f.voicing,
      centroid: f.centroid,
      f1: f.f1,
      f2: f.f2,
      f3: f.f3,
      low: f.low,
      mid: f.mid,
      high: f.high,
      sib: f.sib,
      stress: s.stress,
      active: s.active,
      speaking: s.speaking,
      phraseEnds: s.phraseEnds,
    });
  }
  return { frames, duration: pcm.length / sampleRate, fps };
}
