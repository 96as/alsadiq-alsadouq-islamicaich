// Every tuning number of the mouth shaping and face acting layers (WP4 of the motion bible).
// Plain data: no three.js, no audio. Angles are radians, times are seconds, rates are 1/s (used
// with exponential damping). Source tags: [MB x.y] is MOTION-BIBLE section x.y, [M] is
// M-mouth-acting.md, [EST-D] is the studio director's estimate (a starting value to tune by eye).
//
// Nothing here may contain scripture or any other Islamic text; it is pure animation data.

import { VISEMES } from '../lipsync/visemes.js';

/** Jaw constants [MB 6.1]. `open` is how much each viseme opens the jaw, 0..1. */
export const JAW_STUDIO = {
  max: 0.55, // rad at jaw-open = 1 (tune range 0.42-0.55, top of it for the V2 bars); 3.64 cm of chin per rad on V1, 4.87 on V2 (measured)
  attack: 40, // the jaw leads and the lips follow (bible 6.4: 36-40/s)
  release: 28, // 16-20/s in the bible; 28/s gives 82 ms to 10%, inside its 120 ms cap, and lets the chew dip show
  levelCouple: 0.15, // jaw x ((1 - c) + c x level)
  levelRate: 50, // 1/s smoothing of the level before it scales the jaw
  open: {
    aa: 1, O: 0.7, E: 0.5, U: 0.35, I: 0.35, kk: 0.35, CH: 0.3, DD: 0.3, RR: 0.25, nn: 0.12, SS: 0.12, FF: 0.05, PP: 0,
  },
  ffBite: 0.6, // jaw x (1 - ffBite x FF)
  chewDepth: 0.4, // [MB 6.4] consonant bridge: a consonant between vowels cuts the jaw by up to this share
  chewFrom: 0.1, // consonant mass (over half the vowel mass) at which the cut begins...
  chewFull: 0.4, // ...and at which it is complete
  ppGateAt: 0.3, // while PP is at least this, the jaw is clamped
  ppGateLead: 0.22, // the clamp fades in from ppGateAt - this, so a PP that jumps 0.2 to 0.67 does not pop the chin
  ppJawV1: 0.03, // rad: any more tears the lower lip on today's mesh [M 4]
  ppJawV2: 0.08, // rad: after the WP5 mesh fix
  ppJawMorphRef: 0.2, // rad: PP_jaw = PP * min(jaw, ref) / ref (V2 GLB with a PP_jaw morph)
  speechFloor: 0.07, // rad while speech is active (gaps shorter than speechGap) and PP is low
  speechGap: 0.3,
  openSpeed: 6.0, // rad/s: the jaw never opens faster than this (about 0.1 rad on a 60 fps frame; a mouth that goes 0.23 rad in one frame after a closure reads as a pop)
  closeSpeed: 6.5, // rad/s: nor closes faster, except through the PP gate (the lips must seal on the frame PP arrives)
  budgetRef: 0.55, // rad: the open budget is written against this jaw angle (= max, so a full jaw leaves the same aa as at 0.5 before)
};

/**
 * Morph gain and hard cap per viseme, by mesh version [MB 6.2]. `gain` multiplies the shown weight;
 * `cap` is the highest influence ever written. Closures (PP, FF, SS) are never amplified.
 * V1 is today's mesh, V2 the WP5 mesh (picked by the browUp morph or the sidecar).
 */
export const MORPH_GAIN = {
  1: {
    sil: [1, 1], PP: [1, 1], FF: [1, 1], DD: [1.5, 2.0], kk: [1.5, 2.0], CH: [1.3, 1.5], SS: [1, 1], nn: [2.0, 3.0],
    RR: [1.3, 1.5], aa: [0.8, 0.9], E: [1.8, 2.0], I: [1.5, 2.5], O: [0.8, 0.9], U: [0.8, 0.9],
  },
  2: {
    sil: [1, 1], PP: [1, 1], FF: [1, 1], DD: [1, 1.2], kk: [1, 1.2], CH: [1, 1.2], SS: [1, 1], nn: [1.0, 1.2],
    RR: [1, 1.2], aa: [1, 1], E: [1, 1.2], I: [1, 1.2], O: [1, 1], U: [1, 1],
  },
};

/**
 * Open budget [MB 6.1]: the aa and O morph may not exceed `base - jaw / budgetRef`, so a wide jaw
 * and a wide aa never stack into a black slot. V2 bases are the bible's 1.6 for aa and an
 * equivalent +0.3 step for O [EST-D].
 */
export const OPEN_BUDGET = {
  1: { aa: 1.25, O: 1.45 }, // aa base 1.30 -> 1.25 (review): keeps the V1 chin max under 4.0 cm (M1)
  2: { aa: 1.6, O: 1.75 },
};

/** Options for the audio-only path [MB 6.3-6.5]. The text timeline path leaves these off. */
export const AUDIO_PATH = {
  massLift: false, // enable only if the lip-sync vowel poses stay weak (LS bar K1)
  massMin: 0.05, // non-sil mass below this is not lifted
  massMax: 4,
  vowelSumMax: 1.3, // vowels may add up to this when lifted (maxSum relaxation)
  vowelHold: 0.4, // floor of the previous dominant vowel...
  vowelHoldTime: 0.1, // ...for this long after it fades
  vowelHoldAt: 0.45, // a vowel counts as dominant from this weight
  stressHoldTime: 0.12, // a stressed vowel holds this long...
  stressHoldFrac: 0.85, // ...at this fraction of its peak or more
  ppHoldAt: 0.9,
  ppHoldTime: 0.07, // [MB 6.4] 70 ms: two frames at 24 fps, cartoon readability
};

/**
 * Frame-to-frame limits on the written mouth (lip-sync glitch test, 2026-10-05): no viseme weight rises by more than
 * `riseRate` per second (0.32 on a 60 fps frame), and a released closure lets go over about 55 ms instead of one frame.
 * A closure itself still snaps on (the lips must seal on the frame the lip-sync asks).
 */
export const MOUTH_SLEW = {
  riseRate: 19,
  ppFall: 14,
  maxStep: 0.3, // no viseme moves by more than this on one frame, however long the frame (a 25 ms hitch must not become a pop)
  jawMaxStep: 0.1, // rad: nor the jaw, except through the PP gate
  gateRate: 32, // 1/s: the chin settles onto the PP gate over about 25 ms
  gateSlack: 0.12, // rad: and is never more than this above the gate
};

/**
 * Closure sharpening for the text timeline path [MB 6.4]. The timeline's closures arrive through the
 * viseme smoother, so PP rises slowly and peaks at 0.93-0.95: on screen the seal is a blur of two
 * frames. Once PP passes `snapAt` it is pushed to `snapTo` and kept there until the seal has lasted
 * `minMs` in total, so every b and m reads as a seal of at least 110 ms (7 frames at 60 fps).
 */
export const TIMED_PATH = {
  snapAt: 0.6,
  snapTo: 0.97,
  minMs: 110,
  // Spans the text does not know (English letters other than b, p, m, f) are drawn from the audio, whose vowel weights are
  // weak: the mass of the non-closure weights is lifted towards massTarget (never by more than massMax) so "Mama" opens.
  massMin: 0.04,
  massTarget: 0.7,
  massMax: 3,
};

/** Stress detector [MB 6.7]. */
export const STRESS = {
  peakDecay: 0.2, // 1/s, how fast the remembered peak fades
  peakMin: 0.05, // a quiet hiss never counts as a full-volume peak
  meanTau: 1.5, // s, running mean of the level
  smoothTau: 0.03, // s, light smoothing of the level before edge detection
  onsetRise: 0.6, // onset: the level rises above this fraction of the peak...
  onsetQuiet: 0.25, // ...after at least onsetQuietFor seconds below this fraction
  onsetQuietFor: 0.25,
  accentRatio: 1.25, // accent: level at least this x the running mean...
  accentOfPeak: 0.5, // ...and at least this fraction of the peak
  rearm: 0.8, // the level must fall under this x the threshold before the next accent
  minGap: 0.6, // s between events
  phraseQuiet: 0.25, // phrase end: under this fraction of the peak...
  phraseQuietFor: 0.3, // ...for this long after speech
  lookAhead: 0.17, // timeline path: announced this long before the stressed vowel
};

/** Speech head, drift, ear flicks [MB 5.1, 4, 6.7]. */
export const HEAD = {
  // Continuous speech motion scaled by the voice envelope E.
  pitch: 0.045, // rad amplitude (the bible's +-0.03-0.05)
  yaw: 0.055, // +-0.04-0.06
  roll: 0.028, // +-0.025
  pitchHz: [0.41, 0.67, 0.31], // three sines per axis; irrational ratios so it never repeats
  yawHz: [0.33, 0.52, 0.77],
  rollHz: [0.58, 0.37, 0.71],
  mix: [1, 0.55, 0.35], // weights of the three sines
  floor: 0.7, // amplitude = base x (floor + (1 - floor) x E): the head keeps moving in gaps
  energyAttack: 0.12, // s, E envelope
  energyRelease: 0.45,
  neckShare: 0.35, // the neck takes this share of every offset; the head the rest
  speakBlend: 6, // 1/s, how fast the speech layer fades in and out
  jawDampAt: 0.35, // rad: above this jaw, the speech noise is damped...
  jawDampBy: 0.3, // ...by this fraction...
  jawDampFor: 0.08, // ...for this long
  // Accent nod (speaking only).
  nodMin: 0.035, // rad (2 deg)
  nodMax: 0.07, // rad (4 deg)
  nodDown: [0.1, 0.14], // s, head goes down
  nodBack: [0.22, 0.3], // s, and back
  nodOvershoot: 0.1,
  nodNeckLead: 0.016, // s, the neck is one frame ahead
  nodGap: [0.6, 1.2], // s between nods
  // Micro-drift (the procedural layer after the mixer): idle wander.
  driftYaw: 0.021, // rad (1.2 deg)
  driftPitch: 0.014, // rad (0.8 deg)
  driftHz: [0.11, 0.19, 0.27],
  driftMix: [1, 0.7, 0.45],
  // Multiplier by motion state: idle 1 (B4 idle was measured with glances off and was the same at 1, 0.6 and 0: it is the Idle clip, not the drift), listening 0.6, speaking 0.6 (the speech head takes over),
  // thinking 0.4, one-shots and the walk 0.
  driftMult: { idle: 1, listening: 0.6, speaking: 0.6, thinking: 0.4, oneshot: 0, walk: 0 },
  // Ear flicks.
  earEvery: [4, 9], // s
  earAmp: [0.052, 0.087], // rad (3-5 deg)
  earOut: 0.12, // s
  earSpring: { f: 4.0, z: 0.35, r: 0 }, // [MB 2.2]
  reducedScale: 0.4, // prefers-reduced-motion: speech head at 0.4 x
};

/** Face accents [MB 6.7]. Brows and cheeks need the WP5 morphs; the caller binds only what exists. */
export const FACE = {
  browMin: 0.35,
  browMax: 0.6,
  browUp: 0.09, // s
  browDown: 0.25,
  browChance: 0.6, // per accent
  browGap: [1.5, 2.5],
  browLead: 0.1, // s before the stressed vowel (timeline path)
  innerQuestion: 0.3, // browInnerUp on the last 0.6 s of a question
  innerEmpathy: 0.25, // empathy and gentle: held
  innerRate: 8,
  // Lids follow the jaw: over 0.30 rad, lids close 6-10% x (jaw - 0.30) / 0.20.
  lidJawAt: 0.3,
  lidJawSpan: 0.2,
  lidJawAmount: 0.08,
  lidLookDown: 0.15, // looking down drops the lids 10-20%
  lidRate: 10,
  lidMax: 0.35, // the squint cap of SPEC 6
  // Cheeks (chipmunk cheeks are the big acting surface).
  cheekPP: 0.2, // x PP on bilabials
  cheekAa: 0.1, // x aa on loud open vowels
  cheekRate: 14,
};

/** Studio blinks [MB 5.3]. */
export const BLINK_STUDIO = {
  shape: 2.5, // gamma shape k [MB 5.3]
  minGap: 1.2, // s between natural blinks (start to start)
  meanIdle: 3.5, // s mean interval when idle and listening
  meanSpeaking: 2.6,
  meanByState: { idle: 3.5, listening: 3.5, thinking: 3.5, speaking: 2.35 },
  doubleChance: 0.1,
  doubleGap: [0.06, 0.2], // s after the first blink ends; start to start is at least 0.36 s
  closeTime: 0.067, // timeScale 1.0: close 67 ms, hold 33 ms, open 200 ms
  holdTime: 0.033,
  openTime: 0.2,
  phraseEndChance: 0.6,
  glanceChance: 1,
  glanceDelay: [0.02, 0.1],
};

/** The order of VISEMES, re-exported so the pure modules need only this file. */
export const VISEME_ORDER = VISEMES;
