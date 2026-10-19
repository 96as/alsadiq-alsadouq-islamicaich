// Settings for the animated avatar (avatar-animated.glb). Plain data, no three.js, so the numbers
// can be tuned in one place. Angles are radians, times are seconds.
//
// Nothing here may contain scripture or any other Islamic text; it is pure animation data.

import { assetUrl } from '../../../../utils/assetUrl.js';
import { JAW_STUDIO } from './acting/actingConfig.js'; // WP4

/** The animated avatar: 32 joints, 20 head morphs (14 visemes, 5 face, PP_jaw), no MouthBag mesh, and 30 clips (see avatar-animated.json). */
export const ANIMATED_MODEL_URL = assetUrl('/models/avatar/avatar-animated.glb') + '?v=studio3';
/** The old web avatar: no clips, driven by the procedural motion in useAvatarMotion.js. */
export const FALLBACK_MODEL_URL = assetUrl('/models/avatar/avatar-web.glb') + '?v=web1';
/**
 * avatar-integ perf: avatar-web.glb (0.7 MB) is no longer shipped, so it is not in the fallback chain: a 404 on it would be a second
 * failed request for nothing. To bring the fallback back, run `npm run avatar:optimize` (it writes avatar-src/avatar-web.glb),
 * copy that file to public/models/avatar/ and set this to true.
 */
export const FALLBACK_SHIPPED = false;

/**
 * The model the Avatar loads first. Set VITE_AVATAR_MODEL_URL (a path or URL to a GLB) to use
 * another one. If it fails to load, or lacks the clips below, the Avatar falls back to
 * FALLBACK_MODEL_URL and the procedural motion (only when FALLBACK_SHIPPED; otherwise it renders nothing).
 */
export function configuredModelUrl() {
  const fromEnv = import.meta.env?.VITE_AVATAR_MODEL_URL;
  return typeof fromEnv === 'string' && fromEnv.trim() ? assetUrl(fromEnv.trim()) : ANIMATED_MODEL_URL;
}

/**
 * The V2 mesh (WP5) bakes no gain in: sidecar `viseme_mesh_gain.applied` is {} (the R2 mesh multiplied E, I, kk, DD and nn by 1.5).
 * The V2 gains and caps come from acting/actingConfig.js (MORPH_GAIN, picked by the browUp morph). Kept for the R2-era mechanism:
 * The web gains (lipsync/visemes.js VISEME_GAIN) were tuned for the round-1 mesh, so for a GLB that carries the
 * R2 socket (prop_L) each gain is divided by this value; otherwise the mouth would be driven 1.5x too hard.
 * A test keeps this equal to the sidecar.
 */
export const MESH_VISEME_GAIN = Object.freeze({});

/** avatar-integ: the P6 clip that scrolls the held web page (BEHAVIOUR-SPEC 6.3). It is not in CLIP (and not in CLIP_META)
 * because the GLB does not carry it yet; ClipAvatar asks the animator whether it exists. */
export const SEARCH_SCROLL_W = 'SearchScroll_W';

/** Clip names in the GLB: the 24 of SPEC-EXPERIENCE section 4 plus the studio walk transitions and the Beat_* additives (the V2 studio GLB carries all 30). */
export const CLIP = {
  idle: 'Idle',
  lookAround: 'LookAround',
  listen: 'Listen',
  listenCurious: 'Listen_Curious',
  listenEmpathy: 'Listen_Empathy',
  listenExcited: 'Listen_Excited',
  nod: 'Nod',
  think: 'Think',
  searchStart: 'SearchStart',
  searchHold: 'SearchHold',
  searchSwipe: 'SearchSwipe',
  found: 'Found',
  talk: 'TalkGesture',
  talkStory: 'Talk_Story',
  talkPraise: 'Talk_Praise',
  talkAsk: 'Talk_Ask',
  talkGentle: 'Talk_Gentle',
  greet: 'Greet',
  goodbye: 'Goodbye',
  wave: 'Wave',
  beatR: 'Beat_R',
  beatL: 'Beat_L',
  beatBoth: 'Beat_Both',
  walkStart: 'Walk_Start',
  walkStopR: 'Walk_Stop_R',
  walkStopL: 'Walk_Stop_L',
  happy: 'Happy',
  celebrate: 'Celebrate',
  walk: 'Walk',
  blink: 'Blink',
};

/** A GLB is used in clip mode only if it carries all of these. */
export const REQUIRED_CLIPS = [CLIP.idle, CLIP.listen, CLIP.think, CLIP.talk, CLIP.walk, CLIP.blink];

const FPS = 30;
const f = (frames) => frames / FPS;

/**
 * What the director and the animator know about each clip (mirrors section 4 and the sidecar's
 * `kind`, `home`, `entry_s` and `markers`; tests/avatarDirector.test.mjs checks it against avatar-animated.json).
 *   kind      loop | oneshot | transition | additive | lids
 *   home      the loop a one-shot ends on (frame 0). Only Idle and SearchHold are homes.
 *   to        a transition ends on this loop's frame 0 (and the base switches when it starts)
 *   entry     seconds: where the clock starts when the loop becomes the base (null = keeps running)
 *   markers   seconds into the clip
 *   fadeIn / fadeOut  one-shot fades (default ANIM.fadeOneShot)
 *   interruptible     the director may cut it with a 0.25 s fade
 */
export const CLIP_META = {
  [CLIP.idle]: { frames: 240, kind: 'loop', entry: null },
  [CLIP.lookAround]: { frames: 180, kind: 'oneshot', home: CLIP.idle, interruptible: true },
  [CLIP.listen]: { frames: 180, kind: 'loop', entry: null },
  [CLIP.listenCurious]: { frames: 150, kind: 'loop', entry: 0 },
  [CLIP.listenEmpathy]: { frames: 240, kind: 'loop', entry: 0 },
  [CLIP.listenExcited]: { frames: 120, kind: 'loop', entry: null },
  [CLIP.nod]: { frames: 24, kind: 'additive' },
  [CLIP.think]: { frames: 180, kind: 'loop', entry: 0 },
  [CLIP.searchStart]: {
    frames: 27, kind: 'transition', to: CLIP.searchHold, fadeIn: 0.2,
    markers: { bloom: f(10), look: f(14) },
  },
  [CLIP.searchHold]: { frames: 120, kind: 'loop', entry: null },
  [CLIP.searchSwipe]: {
    frames: 30, kind: 'oneshot', home: CLIP.searchHold, fadeIn: 0.2,
    markers: { contact: f(8), advance: f(11), release: f(16) },
  },
  [CLIP.found]: {
    frames: 48, kind: 'transition', from: CLIP.searchHold, to: CLIP.idle, fadeIn: 0.2,
    markers: { pop: f(3), glow: f(6), collapse: f(16), sparkle: f(24) },
  },
  [CLIP.talk]: { frames: 240, kind: 'loop', entry: null },
  [CLIP.talkStory]: { frames: 300, kind: 'loop', entry: null },
  [CLIP.talkPraise]: { frames: 180, kind: 'loop', entry: null },
  [CLIP.talkAsk]: { frames: 180, kind: 'loop', entry: null },
  [CLIP.talkGentle]: { frames: 240, kind: 'loop', entry: null },
  [CLIP.greet]: { frames: 84, kind: 'oneshot', home: CLIP.idle, markers: { heart: f(22), bow: f(30), offer: f(48) } },
  [CLIP.goodbye]: { frames: 90, kind: 'oneshot', home: CLIP.idle, markers: { heart: f(60) } },
  [CLIP.wave]: { frames: 84, kind: 'oneshot', home: CLIP.idle },
  [CLIP.happy]: {
    frames: 48, kind: 'oneshot', home: CLIP.idle, interruptible: true,
    markers: { takeoff: f(8), apex: f(15), land: f(21) },
  },
  [CLIP.celebrate]: {
    frames: 72, kind: 'oneshot', home: CLIP.idle,
    markers: { takeoff: f(8), apex: f(19), land: f(26) },
  },
  [CLIP.walk]: { frames: 16, kind: 'loop', entry: null },
  // The studio walk's transitions: placed frame by frame by the walk-in (AvatarAnimator.startTransition), not by the director.
  [CLIP.walkStart]: { frames: 15, kind: 'transition', to: CLIP.walk, markers: { liftoff: f(4), heelstrike: f(15) } },
  [CLIP.walkStopR]: { frames: 21, kind: 'transition', to: CLIP.idle },
  [CLIP.walkStopL]: { frames: 21, kind: 'transition', to: CLIP.idle },
  // Gesture beats on top of the talk loops (additive, like Nod). Nothing plays them yet.
  [CLIP.beatR]: { frames: 18, kind: 'additive' },
  [CLIP.beatL]: { frames: 18, kind: 'additive' },
  [CLIP.beatBoth]: { frames: 21, kind: 'additive' },
  [CLIP.blink]: { frames: 9, kind: 'lids' },
};
for (const meta of Object.values(CLIP_META)) meta.dur = f(meta.frames);

/**
 * Missing clips (section 5.9): the substitute for each, '' meaning "nothing". `has(name)` decides.
 * Nod has no clip substitute: the head code plays a procedural nod instead.
 */
export const FALLBACK = {
  [CLIP.listenCurious]: CLIP.listen,
  [CLIP.listenEmpathy]: CLIP.listen,
  [CLIP.listenExcited]: CLIP.listen,
  [CLIP.talkStory]: CLIP.talk,
  [CLIP.talkPraise]: CLIP.talk,
  [CLIP.talkAsk]: CLIP.talk,
  [CLIP.talkGentle]: CLIP.talk,
  [CLIP.searchHold]: CLIP.think,
  [CLIP.searchStart]: '',
  [CLIP.searchSwipe]: '',
  [CLIP.found]: '',
  [CLIP.nod]: '',
  [CLIP.greet]: CLIP.wave,
  [CLIP.goodbye]: CLIP.wave,
  [CLIP.celebrate]: '',
  [CLIP.happy]: '',
  [CLIP.walkStart]: '',
  [CLIP.walkStopR]: '',
  [CLIP.walkStopL]: '',
  [CLIP.beatR]: '',
  [CLIP.beatL]: '',
  [CLIP.beatBoth]: '',
};

/**
 * Round-1 clips the live flow must not play until the round-2 GLB lands (section 5.9: "Happy: nothing until
 * the fixed GLB lands"; today's Happy has the arms-out T-pose look). Such a clip counts as present only when
 * the GLB also carries the round-2 clip named here (Greet ships in the same talk package as the Happy fix and
 * is on its never-cut list). The dev pages still play the old clip directly.
 */
export const LEGACY_GATE = {
  [CLIP.happy]: CLIP.greet,
};

/** The clip to actually play for `name` given what the GLB has ('' = nothing). */
export function resolveClip(name, has) {
  const gate = LEGACY_GATE[name];
  if (has(name) && (!gate || has(gate))) return name;
  const sub = FALLBACK[name];
  return sub && has(sub) ? sub : '';
}

/** Every number of section 5 (the director) and section 6 (the expression layer). */
export const DIRECTOR = {
  thinkHold: 0.45, // thinking shorter than this keeps the previous loop
  expectantWindow: 4, // Listen_Curious after Sadiq asked a question
  expectantChildSpeech: 1.5, // ...or until the child has spoken this long
  minDwell: 0.35, // minimum time on a base before it may change (a change into speaking is immediate)
  talkDwell: 2.5, // one talk variant to another
  fatigue: 3, // the same non-default talk style for a 3rd reply in a row plays TalkGesture
  reducedFadeScale: 1.3,
  fade: {
    listenToListen: 0.6,
    listenToThink: 0.5,
    toTalk: 0.3,
    talkToTalk: 0.6,
    talkToListen: 0.5,
    holdToState: 0.5,
    interruptToListen: 0.4,
    toIdle: 0.6,
    other: 0.4,
    cut: 0.25, // an interruptible one-shot cut by a higher priority
  },
  jitter: { voice: [0.94, 1.06], other: [0.97, 1.03] },
  fresh: { talkWithin: 8, sadStale: 90 },
  nod: {
    minSpeech: 1.2, // child speech before a pause counts
    minPause: 0.3,
    prob: 0.55,
    minGap: 2.5,
    perMinute: 8,
    weight: [0.55, 1.0],
    scale: [0.85, 1.15],
    double: 0.2,
    doubleAmp: 0.7,
    doubleDelay: 0.35,
    empathyWeight: [0.4, 0.6],
    empathyScale: 0.8,
    excitedWeight: [0.8, 1.0],
    reducedAmp: 0.5,
    emphasis: {
      // MOTION-BIBLE section 10: when the stress-timed accent nod (hk/06-mouth-acting) lands, set
      // this to false so only one system nods while Sadiq speaks.
      enabled: true,
      prob: 0.4,
      weight: [0.35, 0.6],
      byStyle: { praise: 0.6, gentle: 0.3, story: 0.5 },
      minGap: 1.8,
      high: 0.6, // voice level (of its peak) that starts an onset
      low: 0.25,
      lowFor: 0.25,
    },
  },
  energy: {
    base: 0.55, gain: 0.45, attack: 0.12, release: 0.45,
    storyMin: 0.7, gentle: 0.85, reduced: 0.6,
    peakFloor: 0.05, peakDecay: 20, // the running peak forgets with this time constant (s)
  },
  // One-shot priority (higher wins), queue TTL (s) and cooldown (s). Search is atomic.
  shots: {
    priority: { Goodbye: 7, search: 6, Celebrate: 5, Greet: 4, Happy: 3, LookAround: 1 },
    ttl: { Celebrate: 4, Greet: 3, Happy: 6, Goodbye: 3 },
    cooldown: { Happy: 60, Celebrate: 30, SearchSwipe: 1.6 },
    lookAroundEvery: [12, 20],
    lookAroundFirst: [6, 10],
    lookAroundListenSilence: 10,
    goodbyeReducedWeight: 0.5,
  },
  greet: { speechWait: 1.5, waveWindow: 6, reconnectAway: 60 },
  holo: {
    minShow: 1.4, foundGrace: 0.3, maxHold: 15,
    toolGap: 8, quickGap: 20,
    swipeFirst: [0.9, 1.3], swipeEvery: [1.6, 2.4], swipeMax: 3,
    open: 0.35, glow: 0.25, collapse: 0.3, burst: 0.6,
    noneDim: 0.25, noneSquash: 0.15, noneGone: 0.2,
    interruptClose: 0.25,
    iconIn: 0.15, iconCheck: 1.0, iconOut: 0.2,
    // The virtual timeline used when the clip is missing (same times as the clips' markers).
    bloomAt: f(10), swipeAdvanceAt: f(11), swipeDur: f(30), foundDur: f(48),
    glowAt: f(6), collapseAt: f(16), sparkleAt: f(24),
    pageSpring: 0.25,
    // w3: the held web page (BEHAVIOUR-SPEC 6): flicks start once the results show, Found waits until one was
    // readable, the hero hold (window out to the child) shifts the collapse and the sparkle by out+hold+back, and
    // reduced motion has no motion but the fade.
    webSwipeMax: 6, webReadMin: 1.8, webWait: 2.5,
    hero: { out: 0.45, hold: 2.0, back: 0.45 },
    reducedOpen: 0.15, reducedHold: 1.5, reducedFade: 0.15,
  },
  expr: {
    attack: 6, release: 3,
    squint: { praise: 0.22, found: 0.3, celebrate: 0.3, excited: 0.12, empathy: 0.18, gentle: 0.15, curious: 0 },
    squintCap: 0.35,
    blinkRate: { listening: 0.8, curious: 0.7, thinking: 1.3, searching: 0.6, other: 1 },
    ooh: 0.3, // seconds
    foundSquintFrom: f(8), foundSquintTo: f(40),
  },
  // Viseme bias (index names of lipsync/visemes.js) for the expression channels.
  // softSil is the spec value; sil is already 1 at rest, so it only matters mid-phrase. softI is what
  // the soft (empathy, gentle) mouth actually shows at rest: a faint closed-lip curve.
  bias: { smileE: 0.18, smileI: 0.1, smileSpeaking: 0.3, softSil: 0.35, softI: 0.08, oohO: 0.25, oohU: 0.12 },
  // The procedural nod when the GLB has no Nod clip.
  proceduralNod: { peak: 0.08, attack: 0.12, release: 0.35 },
};

/** The looping body clip for each agent state (see resolveMotionState). */
export const STATE_CLIP = {
  idle: CLIP.idle,
  listening: CLIP.listen,
  thinking: CLIP.think,
  speaking: CLIP.talk,
};

/** Clips the dev pages can play as one-shots, and the loops they can hold. */
// 06-avatar-context: the list now covers all 24 names; the dev page shows only those the GLB has.
export const ONE_SHOTS = [
  CLIP.wave, CLIP.happy, CLIP.lookAround, CLIP.greet, CLIP.goodbye, CLIP.celebrate,
  CLIP.searchStart, CLIP.searchSwipe, CLIP.found,
];
export const LOOPS = [
  CLIP.idle, CLIP.listen, CLIP.listenCurious, CLIP.listenEmpathy, CLIP.listenExcited, CLIP.think,
  CLIP.searchHold, CLIP.talk, CLIP.talkStory, CLIP.talkPraise, CLIP.talkAsk, CLIP.talkGentle, CLIP.walk,
];

export const ANIM = {
  fade: 0.4, // crossfade between body loops (0.3 to 0.5 s)
  fadeOneShot: 0.35, // fade into and out of a one-shot
  lookAroundEvery: [12, 20], // seconds between idle glances, random in this range (first one is sooner)
  lookAroundFirst: [6, 10],
  blinkTimeScale: 1.0, // MOTION-BIBLE 5.3: close 67 ms, hold 33, open 200; the studio scheduler starts a double blink at least 0.36 s after the first
  lookAroundBlinkAt: 0.3, // seconds into LookAround: blink as the head turns
  reducedIdleScale: 0.5, // reduced motion: Idle at half speed
  reducedIdleWeight: 0.6, // ...and the other loops blended in only this far (calmer poses)
};

/**
 * Walk-in with the studio Walk (avatar-animated.glb, WP1). The clip is in place: 16 frames (0.5333 s),
 * 0.28 m per cycle (two steps), 0.525 m per second at timeScale 1, heel strike R at f0 and L at f8, on a
 * 0.977 m avatar. The model is scaled by MODEL_SCALE to the height the forest expects, so ground speed in
 * forest units per second is timeScale * 0.525 * MODEL_SCALE: the feet stay planted as long as the avatar
 * moves at exactly that speed and faces the way it travels (see studioWalk.js). Walk_Start, Walk_Stop_R
 * and Walk_Stop_L are the transitions; their own ground speed is the sidecar's `root_speed_m_s`.
 */
export const MODEL_HEIGHT = 0.977;
/** The old avatar was about 0.85 tall in forest units; the camera rig is calibrated to it. */
export const MODEL_SCALE = 0.87;
export const WALK_CLIP = {
  speedPerScale: 0.525, // metres per second at timeScale 1
  stridePerCycle: 0.28, // metres per 16 f cycle (two steps)
  cycle: 16 / 30, // seconds per cycle at timeScale 1 (0.5333)
  cruiseScale: 1.0, // timeScale while cruising (0.525 m/s is a relaxed kid's pace)
  rushScale: 1.35, // the child started the session before the walk was over (5 steps/s, never 2.0)
  rampUp: 0.8, // legacy gait only
  stopTime: 0.9, // legacy gait only
  distance: 4.2, // how far up the path it starts, in forest units (the walk re-plans it to whole steps)
  turnTime: 0.8, // legacy gait only
  turnRate: 3.0, // rad/s at most while walking (Bible 3.3)
  headLead: 0.12, // seconds the head leads the root's turn (0.10 to 0.15)
  residualMax: 0.2618, // 15 deg: the most turn the chest and neck take over at the stop
  residualTime: 0.6, // seconds the chest and neck take to carry that turn
  residualRate: 0.6, // rad/s the root turns afterwards
  // The avatar fades in standing still on Walk_Start f0 (= Idle f0) for holdIn seconds, and only then steps off, so the toe-off
  // of Walk_Start is never hidden under the fade (the fade used to run for 0.7 s while Walk_Start plays 0.5 s).
  fadeIn: 0.3,
  holdIn: 0.3,
};

/**
 * The Walk clip of the 2026-10 R2 avatar (24 frames, 0.8 s, stride 0.42 m, no knees) and the ramp
 * gait built for it. Used when the GLB has no Walk_Start / Walk_Stop_R / Walk_Stop_L.
 */
export const WALK_CLIP_LEGACY = {
  speedPerScale: 0.525,
  stridePerCycle: 0.42,
  cycle: 0.8,
  cruiseScale: 1.2,
  minScale: 0.55,
  rushScale: 2.0,
  rampUp: 0.8,
  stopTime: 0.9,
  distance: 4.2,
  turnTime: 0.8,
};

/**
 * The transition clips' ground speed, copied from avatar-animated.json (`clips[].root_speed_m_s`,
 * model metres per second over interval i = frame i to i+1 at 30 fps, the last entry is the speed it
 * hands over to). tests/walkStudio.test.mjs checks these against the sidecar. `duration` is in seconds.
 */
export const WALK_TRANSITIONS = {
  fps: 30,
  steadySpeed: 0.525,
  halfStep: 0.14, // metres between a right and a left heel strike, 8 f of Walk
  start: {
    clip: CLIP.walkStart,
    duration: 0.5,
    root: [0, 0, 0, 0, 0, 0, 0.00203, 0.01478, 0.04055, 0.07935, 0.13117, 0.19601, 0.27388, 0.36478, 0.4687, 0.525],
  },
  stopR: {
    clip: CLIP.walkStopR, // starts on Walk f0 (right heel strike), ends on Idle f0
    duration: 0.7,
    root: [0.48801, 0.41504, 0.34371, 0.27427, 0.20709, 0.14268, 0.082, 0.02734, 0.00019, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  },
  stopL: {
    clip: CLIP.walkStopL, // starts on Walk f8 (left heel strike), ends on Idle f0
    duration: 0.7,
    root: [0.49609, 0.43919, 0.38373, 0.32983, 0.27764, 0.22736, 0.17922, 0.13357, 0.09089, 0.052, 0.01865, 0.00057, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  },
};

/** Look-at. Head and neck only (the model has no eye bones). */
export const LOOK = {
  yaw: 0.2, // total, split HEAD_SHARE between the head and the neck
  pitchUp: 0.12,
  pitchDown: 0.1,
  headShare: 0.65,
  rate: 4.5, // damp rate toward the target
  pointerIdle: 4, // seconds without pointer movement before the gaze returns to the camera
  pointerGain: 1.0, // pointer at the screen edge looks this far (fraction of the limits)
  // How much of the look-at each state lets through (the clips already move the head).
  stateWeight: { idle: 1, listening: 1, thinking: 0.35, speaking: 0.8 },
  oneShotWeight: {
    LookAround: 0.15, Wave: 0.5, Happy: 0.5, // 06-avatar-context: the new shots keep most of the clip's own head
    Greet: 0.3, Goodbye: 0.3, Celebrate: 0.3, SearchStart: 0.3, SearchSwipe: 0.3, Found: 0.3,
  },
  panelWeight: 0.8, // while the hologram is up the gaze aims at the panel with this weight (no SearchHold clip)
  reducedWeight: 0.3,
};

/**
 * The jaw bone agrees with the viseme morphs and adds the loudness: the chin drops with the open
 * vowels (table below) and further with a loud voice, and stays up on a lip closure. The morphs
 * carry the lip shape, the jaw carries how loud, as in JALI.
 */
// WP4: the studio jaw (MOTION-BIBLE 6.1). The mouth shaper in acting/ is the runtime source; these
// values are the same numbers for the older jaw.js path and the lip-sync eval harness.
export const JAW = {
  max: JAW_STUDIO.max, // rad at the widest vowel
  attack: JAW_STUDIO.attack,
  release: JAW_STUDIO.release,
  levelCouple: JAW_STUDIO.levelCouple, // jaw target x (1 - couple + couple * level)
  ppMax: JAW_STUDIO.ppJawV1 / JAW_STUDIO.max, // jaw target ceiling while the lips are closed (0..1 of max)
  ppAt: JAW_STUDIO.ppGateAt, // PP weight at which the lips count as closed
  // How much each viseme opens the jaw, 0..1.
  open: JAW_STUDIO.open,
};
