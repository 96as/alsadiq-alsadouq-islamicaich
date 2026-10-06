// Hybrid lip-sync: the audio-only LipsyncEngine, plus, while a text timeline of the reply is
// latched to the audio (timelineSync.js), mouth shapes timed by the text and coloured by the audio
// (timelineTrack.js). With no timeline, process() returns exactly what the engine returns
// (requirement R2: the same Float32Array), so the feature costs nothing when it is off.
//
// The engine always runs: it supplies the voice gate, the loudness, the short-vowel class of the
// slots and the shapes of spans the text knows nothing about (digits, symbols).

import { TIMELINE, TIMELINE_SMOOTHING } from './lipsyncConfig.js';
import { PHASE } from './timelineSync.js';
import { TrackSampler } from './timelineTrack.js';
import { VisemeSmoother } from './visemeSmoother.js';
import { VI, VISEME_COUNT } from './visemes.js';

export class HybridLipsync {
  /**
   * @param {import('./lipsyncEngine.js').LipsyncEngine} engine the audio-only engine to wrap
   * @param {{sync?: import('./timelineSync.js').TimelineSync|null, outputLatencyMs?: number}} [opts]
   *   without `sync` this is the plain engine
   */
  constructor(engine, { sync = null, outputLatencyMs = 0 } = {}) {
    this.engine = engine;
    this.sync = sync;
    this.sampler = new TrackSampler();
    this.smoother = new VisemeSmoother(TIMELINE_SMOOTHING);
    this.raw = new Float32Array(VISEME_COUNT);
    this.mixed = new Float32Array(VISEME_COUNT);
    this.mixed[VI.sil] = 1;
    this.outputLatencyMs = outputLatencyMs;
    this.mix = 0; // 0 audio-only .. 1 text-timed
    this.seeded = false;
    this.track = null;
  }

  get features() {
    return this.engine.features;
  }

  get classifier() {
    return this.engine.classifier;
  }

  /** The browser's output latency in ms (AudioContext.outputLatency); the mouth leads by less. */
  setOutputLatency(ms) {
    this.outputLatencyMs = Number.isFinite(ms) && ms > 0 ? ms : 0;
  }

  /** True while the shown mouth comes (at least partly) from a text timeline. */
  get timed() {
    return this.mix > 0;
  }

  reset() {
    this.engine.reset();
    this.smoother.reset();
    this.mix = 0;
    this.seeded = false;
    this.mixed.fill(0);
    this.mixed[VI.sil] = 1;
  }

  /**
   * @param {Float32Array} samples newest audio, newest last, at least FFT_SIZE long
   * @param {number} dt seconds since the previous call
   * @param {number} nowMs a clock in ms shared with the timeline messages
   * @returns {Float32Array} the 14 weights (reused between calls)
   */
  process(samples, dt, nowMs) {
    const eng = this.engine.process(samples, dt);
    const sync = this.sync;
    if (!sync) return eng;
    const st = this.engine.classifier.state;
    sync.onFrame(st.active, nowMs, this.engine.features.rms);
    const pos = sync.position(nowMs);
    // A reply that starts with b or m: the lips wait pressed together until the first sound.
    const waitClosed = pos < 0 && sync.phase === PHASE.ARMED && sync.track !== null && sync.track.startsClosed;
    if (pos < 0 && !waitClosed && this.mix <= 0.001) {
      this.mix = 0;
      this.seeded = false;
      return eng;
    }
    const smoother = this.smoother;
    if (!this.seeded) {
      // Start from what the audio-only mouth shows, so the hand-over does not jump.
      smoother.pre.set(this.engine.smoother.pre);
      smoother.out.set(eng);
      this.seeded = true;
    }
    const raw = this.raw;
    if (pos >= 0) {
      const track = sync.track;
      if (track !== this.track) {
        this.track = track;
        this.sampler.setTrack(track);
      }
      const lead = TIMELINE.leadMs - this.outputLatencyMs;
      this.sampler.leadMs = lead < TIMELINE.leadMinMs ? TIMELINE.leadMinMs : lead > TIMELINE.leadMaxMs ? TIMELINE.leadMaxMs : lead;
      const cls = st.voiced > 0.3 ? this.engine.classifier.arabic.cls : -1;
      this.sampler.sample(pos, cls, st.level, raw);
      const u = this.sampler.unk;
      if (u > 0) {
        // An English text track names every b, p and m, so a closure the audio finds in a span the text left open
        // (a t before a th, a k) is a false one: the lips stay as the other letters say.
        const noPP = track && track.lang === 'en';
        for (let i = 1; i < VISEME_COUNT; i++) if (!(noPP && i === VI.PP)) raw[i] += (eng[i] - raw[i]) * u;
      }
      this.mix += (1 - this.mix) * (1 - Math.exp(-TIMELINE.mixInRate * dt));
    } else if (waitClosed) {
      raw.fill(0);
      raw[VI.PP] = TIMELINE.ppFloor;
      this.mix += (1 - this.mix) * (1 - Math.exp(-TIMELINE.mixInRate * dt));
    } else {
      for (let i = 1; i < VISEME_COUNT; i++) raw[i] = eng[i];
      this.mix -= this.mix * (1 - Math.exp(-TIMELINE.mixOutRate * dt));
    }
    const tl = smoother.step(raw, dt);
    const m = this.mix;
    const out = this.mixed;
    let sum = 0;
    for (let i = 1; i < VISEME_COUNT; i++) {
      out[i] = eng[i] + (tl[i] - eng[i]) * m;
      sum += out[i];
    }
    out[VI.sil] = sum < 1 ? 1 - sum : 0;
    return out;
  }
}
