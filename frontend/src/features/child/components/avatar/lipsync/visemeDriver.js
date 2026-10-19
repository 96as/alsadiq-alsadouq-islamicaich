// Live lip-sync driver: taps an audio source with a Web Audio AnalyserNode and, each time read()
// is called, runs the LipsyncEngine on the newest samples. Nothing is allocated per read.
//
// The analyser only listens. It is never connected to the speakers (a media element is the one
// exception: Web Audio takes it over, so it is routed to the speakers once, apart from the
// driver), so playback is unaffected.
// hotfix-2: that route goes through a GainNode placed AFTER the analyser's tap, so setMuted() can
// silence what is heard while the analyser (and so the lips) still gets the full signal.
//
// iOS and Safari: an AudioContext starts suspended unless it is created or resumed inside a user
// gesture. The driver resumes its context on the next tap, key press or return to the tab, and
// read() returns null until the context runs, so the avatar uses its jaw fallback meanwhile.

import { FFT_SIZE, bytesToFloat } from './dsp.js';
import { HybridLipsync } from './hybridLipsync.js';
import { LipsyncEngine } from './lipsyncEngine.js';

const MAX_DT = 0.1;
const MIN_DT = 1 / 240;
const RESET_GAP_MS = 500; // reads further apart than this start from a clean state
const GESTURE_EVENTS = ['pointerdown', 'touchend', 'keydown', 'click'];

// A media element can feed Web Audio only once for its lifetime, so remember what it fed.
const elementTaps = new WeakMap();

/** How long the speakers take to play what the browser has decoded, in ms (0 when unknown). */
function outputLatencyMs(ctx) {
  const sec = ctx.outputLatency || 0;
  return Number.isFinite(sec) && sec > 0 ? sec * 1000 : 0;
}

function getAudioContextCtor() {
  if (typeof window === 'undefined') return null;
  return window.AudioContext || window.webkitAudioContext || null;
}

/**
 * Resume `ctx` as soon as the browser allows: on a user gesture, or when the tab becomes visible
 * again. Returns a function that removes the listeners.
 */
export function resumeOnGesture(ctx) {
  if (typeof window === 'undefined') return () => {};
  const tryResume = () => {
    if (ctx.state === 'running' || ctx.state === 'closed') return;
    ctx.resume().catch(() => {});
  };
  const onVisible = () => {
    if (document.visibilityState === 'visible') tryResume();
  };
  // A context can fall back to suspended or interrupted later (a call, a locked phone), so the
  // listeners stay for the life of the driver; they cost nothing while the context runs.
  // Options objects, not a bare `true`: some EventTarget implementations ignore the boolean on
  // removal, which would leave the listeners behind.
  const opts = { capture: true, passive: true };
  for (const e of GESTURE_EVENTS) window.addEventListener(e, tryResume, opts);
  document.addEventListener('visibilitychange', onVisible);
  return () => {
    for (const e of GESTURE_EVENTS) window.removeEventListener(e, tryResume, opts);
    document.removeEventListener('visibilitychange', onVisible);
  };
}

/** Accepts a MediaStream, MediaStreamTrack, a LiveKit audio track, or an HTMLMediaElement. */
function sourceKind(source) {
  if (!source) return null;
  if (typeof HTMLMediaElement !== 'undefined' && source instanceof HTMLMediaElement) return 'element';
  if (typeof MediaStream !== 'undefined' && source instanceof MediaStream) return 'stream';
  if (typeof MediaStreamTrack !== 'undefined' && source instanceof MediaStreamTrack) return 'track';
  if (source.mediaStream || source.mediaStreamTrack) return 'livekit';
  return null;
}

/**
 * @param {object} opts
 * @param {MediaStream|MediaStreamTrack|HTMLMediaElement|object} [opts.source] what to listen to
 * @param {AudioContext} [opts.context] with `input`: tap an AudioNode of a context you own instead
 * @param {AudioNode} [opts.input] the node to tap (needs `context`)
 * @param {'en'|'ar'} [opts.lang] 'ar' selects the Arabic vowel mode (default 'en')
 * @param {import('./timelineSync.js').TimelineSync|null} [opts.timeline] the sink for the text
 *   timelines of the replies (lk.lipsync). While one is latched to the voice the mouth follows the
 *   text, coloured by the audio; without one (or without a timeline) it is audio only.
 * @returns {null | {read, resume, dispose, context}} null when Web Audio is unavailable
 */
export function createVisemeDriver({ source, context, input, lang = 'en', timeline = null } = {}) {
  let ctx = context ?? null;
  let ownsContext = false;
  let tap = input ?? null;
  let gain = null; // hotfix-2: the speaker route of a media element (see setMuted)
  const kind = tap && ctx ? 'node' : sourceKind(source);
  if (!kind) return null;

  try {
    if (kind !== 'node') {
      const known = kind === 'element' ? elementTaps.get(source) : null;
      if (known) {
        ctx = known.ctx;
        tap = known.node;
        gain = known.gain ?? null;
      } else {
        const Ctor = getAudioContextCtor();
        if (!Ctor) return null;
        ctx = new Ctor();
        ownsContext = kind !== 'element';
        if (kind === 'element') {
          tap = ctx.createMediaElementSource(source);
          // Web Audio takes the element over: keep it audible, independent of this driver.
          // hotfix-2: through a gain (1 = heard, 0 = muted); the analyser taps `tap`, before it.
          gain = ctx.createGain();
          tap.connect(gain);
          gain.connect(ctx.destination);
          elementTaps.set(source, { ctx, node: tap, gain });
        } else {
          let stream = source;
          if (kind === 'track') stream = new MediaStream([source]);
          if (kind === 'livekit') stream = source.mediaStream ?? new MediaStream([source.mediaStreamTrack]);
          tap = ctx.createMediaStreamSource(stream);
        }
      }
    }
    const analyser = ctx.createAnalyser();
    analyser.fftSize = FFT_SIZE;
    analyser.smoothingTimeConstant = 0;
    tap.connect(analyser);
    return new VisemeDriver({ ctx, tap, analyser, ownsContext, lang, timeline, gain });
  } catch {
    // No Web Audio, or the element is already tapped by someone else: no lip-sync.
    if (ownsContext && ctx) ctx.close().catch(() => {});
    return null;
  }
}

class VisemeDriver {
  constructor({ ctx, tap, analyser, ownsContext, lang, timeline, gain }) {
    this.context = ctx;
    this.gain = gain ?? null; // hotfix-2
    this.tap = tap;
    this.analyser = analyser;
    this.ownsContext = ownsContext;
    this.engine = new HybridLipsync(new LipsyncEngine(ctx.sampleRate, { lang }), { sync: timeline });
    this.timeline = timeline;
    this.buf = new Float32Array(FFT_SIZE);
    this.bytes = typeof analyser.getFloatTimeDomainData === 'function' ? null : new Uint8Array(FFT_SIZE);
    this.lastMs = -1;
    this.wasRunning = false;
    this.stopGesture = resumeOnGesture(ctx);
    if (ctx.state !== 'running') ctx.resume().catch(() => {});
    // What read() returns: one stable object, updated in place.
    this.result = {
      weights: this.engine.engine.weights,
      stress: 0,
      level: 0,
      speaking: false,
      active: false,
      phraseEnds: 0,
      timed: 0, // 0..1: how much of the shown mouth comes from a text timeline (bible 6.3)
      features: this.engine.features,
    };
  }

  /** Resume the audio context now. Call it from a click or tap handler. */
  resume() {
    return this.context.state === 'running' ? Promise.resolve() : this.context.resume().catch(() => {});
  }

  /**
   * hotfix-2: call SYNCHRONOUSLY from a tap (not after an await), and again from any later tap.
   * Resumes the context and plays one silent sample through it, which is what iOS and Safari want
   * before they let a context (and a media element routed through it) make sound. The element is
   * not touched here, so a real clip started by the same tap is never interrupted.
   * @returns {boolean} true once the context is running
   */
  unlock() {
    const ctx = this.context;
    try {
      if (ctx.state !== 'running') ctx.resume().catch(() => {});
      const src = ctx.createBufferSource();
      src.buffer = ctx.createBuffer(1, 1, 22050);
      src.connect(ctx.destination);
      src.start(0);
    } catch {
      // No Web Audio buffer support: resume() above is all there is.
    }
    return ctx.state === 'running';
  }

  /** hotfix-2: silence the speakers; the lips keep moving (the analyser taps before the gain). */
  setMuted(muted) {
    if (!this.gain) return false;
    const t = this.context.currentTime;
    this.gain.gain.cancelScheduledValues(t);
    this.gain.gain.setTargetAtTime(muted ? 0 : 1, t, 0.015);
    return true;
  }

  /** hotfix-2: the speaker gain right now (1 heard, 0 muted), -1 when there is no gain stage. For the tests. */
  get gainValue() {
    return this.gain ? this.gain.gain.value : -1;
  }

  /** hotfix-2: 'running', 'suspended', 'interrupted' (iOS) or 'closed'. */
  get contextState() {
    return this.context.state;
  }

  /**
   * Analyse the newest audio and return the viseme state, or null while the audio context is not
   * running (the caller should then use its fallback). Calls less than 4 ms apart (two
   * consumers in one frame) return the same result without analysing again.
   * @param {number} [nowMs] performance.now()
   */
  read(nowMs = performance.now()) {
    if (this.context.state !== 'running') {
      this.wasRunning = false;
      return null;
    }
    if (this.lastMs >= 0 && nowMs - this.lastMs < 4) return this.result; // already analysed this frame
    let dt = (nowMs - this.lastMs) / 1000;
    if (!this.wasRunning || this.lastMs < 0 || nowMs - this.lastMs > RESET_GAP_MS) {
      this.engine.reset();
      dt = 1 / 60;
    }
    this.wasRunning = true;
    this.lastMs = nowMs;
    dt = Math.min(MAX_DT, Math.max(MIN_DT, dt));

    if (this.bytes) {
      this.analyser.getByteTimeDomainData(this.bytes);
      bytesToFloat(this.bytes, this.buf);
    } else {
      this.analyser.getFloatTimeDomainData(this.buf);
    }
    this.engine.setOutputLatency(outputLatencyMs(this.context));
    const r = this.result;
    r.weights = this.engine.process(this.buf, dt, nowMs);
    const s = this.engine.classifier.state;
    r.stress = s.stress;
    r.level = s.level;
    r.speaking = s.speaking;
    r.active = s.active;
    r.phraseEnds = s.phraseEnds;
    r.timed = this.engine.mix;
    return r;
  }

  dispose() {
    this.stopGesture();
    try {
      this.tap.disconnect(this.analyser);
      this.analyser.disconnect();
    } catch {
      // Already disconnected.
    }
    if (this.ownsContext) this.context.close().catch(() => {});
  }
}
