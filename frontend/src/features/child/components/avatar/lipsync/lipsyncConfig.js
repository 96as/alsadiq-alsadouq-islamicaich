// Every tuning number of the lip-sync driver lives here, so the mouth can be re-tuned without
// reading the DSP. Hz are Hz, times are seconds, rates are 1/s (used with exponential damping).
//
// Nothing here may contain scripture or any other Islamic text; it is pure signal-processing data.

import { VI } from './visemes.js';

export const ANALYSIS = {
  // A formant peak in the LPC envelope must stand this far above its valleys (natural-log power).
  peakMinProm: 0.25,
};

export const CLASSIFIER = {
  // Voice activity on the RMS of the newest 21 ms, with hysteresis.
  gateOpen: 0.012,
  gateClose: 0.007,
  // Loudness is judged against the loudest recent frame, so TTS volume does not matter.
  peakDecay: 0.2, // 1/s, how fast the remembered peak fades
  peakMin: 0.05, // a quiet hiss never counts as a full-volume peak
  levelFloor: 0.008, // RMS that counts as level 0

  // Voicing (autocorrelation peak) mapped to 0..1 between these two values.
  voicedLo: 0.4,
  voicedHi: 0.7,

  // A silence shorter than this inside a phrase is a stop closure (lips press), not a pause.
  closureMax: 0.14,
  closurePP: 0.35, // how far the lips close before the release tells us which stop it was
  phraseGap: 0.3, // a silence longer than this ends the phrase (the mouth relaxes, the eyes may blink)

  // Vowel prototypes (F1, F2 in Hz) for an adult male voice, and how forgiving the match is.
  vowels: {
    [VI.aa]: [780, 1250],
    [VI.E]: [520, 1850],
    [VI.I]: [320, 2250],
    [VI.O]: [500, 900],
    [VI.U]: [340, 850],
  },
  sigmaF1: 0.3, // in natural-log Hz
  sigmaF2: 0.22,
  formantRate: 40, // damp rate of the F1/F2 tracker

  openGain: 1.0, // vowel weight at the loudest recent level
  openCurve: 0.7, // level^curve: below 1 opens the mouth earlier on quiet speech
  confMin: 0.6, // vowel weight when the formants match no prototype well

  // Nasals and murmurs: voiced, almost nothing between 700 and 2500 Hz next to the low band
  // (log10 of the power ratio; a vowel sits around -1 to -2), and not loud.
  nasalTilt: [-2.8, -3.6],
  nasalLevelLo: 0.35,
  nasalLevelHi: 0.7,
  nasalWeight: 0.6,

  // American r: a low third formant with F2 in the middle.
  rrF3: [2500, 2000],
  rrWeight: 0.6,

  // Fricatives and affricates, from the spectral centroid and the high-band share.
  ssCentroid: [4800, 6500],
  ssSib: [0.25, 0.55],
  chCentroid: [2600, 3600],
  chCentroidEnd: [4400, 5400],
  chHigh: [0.5, 0.8],
  ffHigh: [0.2, 0.45],
  ffLevelMax: [0.35, 0.6],
  ffWeight: 0.7,
  noiseGain: 3, // fricatives are quieter than vowels: amp = level * gain, clamped to 1

  // Stop bursts: the first loud frame after a closure picks PP, kk or DD from its centroid.
  burstRise: 2.5, // rms must be this many times the previous frame's
  burstPPMax: 1800,
  burstKKMax: 3500,
  burstVoicingMax: 0.55, // a voiced onset is a vowel, not a stop release
  burstWeight: 0.5,
  burstTau: 0.07,

  // Co-articulation: through a consonant the mouth keeps part of the last vowel's shape.
  carry: 0.4,
  carryTau: 0.2,
  closureCarry: 0.25,

  // Stress, for the blink scheduler: loud voiced syllables.
  stressLevel: [0.6, 0.9],
  stressAttack: 20,
  stressRelease: 4,
};

/**
 * Arabic mode (lang 'ar'): the English five-vowel prototypes do not fit Arabic. Measured on the
 * ElevenLabs voice (PLAN.md section 1 and the eval harness): fatha sits near F1 560, F2 1540
 * (an [ae]-like front vowel, which the English E prototype swallows), kasra near 310/2100 and
 * damma near 370/1080. So the vowel is one of three classes from the raw per-frame formants:
 * a unless the audio clearly says i or u. Fitted on lines ar01-ar20 only.
 */
export const ARABIC = {
  // i: second formant above f2i and first formant below f1i.
  f2i: 1700,
  f1i: 450,
  // u: second formant below f2u and first formant below f1u.
  f2u: 1300,
  f1u: 450,
  // The rule looks at the median of the last few raw frames. 1 is the raw frame: on the tune set a
  // window of 3 cost 6 points of vowel accuracy (it lags a frame at every vowel change), and the
  // rig's own smoothing already hides a one-frame flip.
  medianFrames: 1,
  // Vowel weight = ampBase + ampSpan * level^ampCurve, so a quiet syllable still shows its shape
  // and a normal one reaches a full pose (the jaw, not this weight, carries the loudness: JAW.levelCouple).
  // Where the voicing measure counts as a vowel (the English gate is voicedLo/voicedHi above).
  voicedLo: 0.2,
  voicedHi: 0.5,
  ampBase: 0.8,
  ampSpan: 0.2,
  ampCurve: 0.4,
};

export const SMOOTHING = {
  // Stage 1: removes single-frame jitter from the classifier. With LIVE_RATE in lipsyncRig.js it
  // sets the lag: 60 gives about 60 ms mean and under 80 ms worst on the 13 audition clips (40
  // gave 78 and 104 ms), and motion above 10 Hz stays under 1 percent.
  preRate: 60,
  // Stage 2: attack (opening toward a target) and release (closing), per viseme.
  attack: {
    [VI.PP]: 42, [VI.FF]: 28, [VI.DD]: 36, [VI.kk]: 30, [VI.CH]: 26, [VI.SS]: 24, [VI.nn]: 22,
    [VI.RR]: 20, [VI.aa]: 60, [VI.E]: 22, [VI.I]: 22, [VI.O]: 20, [VI.U]: 20,
  },
  release: {
    [VI.PP]: 22, [VI.FF]: 16, [VI.DD]: 20, [VI.kk]: 18, [VI.CH]: 14, [VI.SS]: 14, [VI.nn]: 14,
    [VI.RR]: 12, [VI.aa]: 12, [VI.E]: 12, [VI.I]: 12, [VI.O]: 10, [VI.U]: 10,
  },
  maxSum: 1.0, // non-sil weights are scaled down when they add up to more than this
};

/**
 * Text-timed mouth (PLAN.md sections 3 to 5): the TTS says when each character is spoken, the
 * audio says which short vowel it was and how loud. Times are ms, rates 1/s.
 */
export const TIMELINE = {
  // The mouth is shown this much before the sound, minus the output latency (a lip closure is seen
  // ahead of its burst). Clamped to [leadMinMs, leadMaxMs] after the latency is subtracted.
  leadMs: 50,
  vowelLeadMs: 25, // vowels lead the sound by this much instead (the same output latency is taken off)
  leadMinMs: 0,
  leadMaxMs: 250,

  // --- Track building (arabicText.js) ---
  pauseMs: 100, // a space shorter than this is not a pause
  // Mouth weight of each vowel before the loudness law (ARABIC.ampBase..ampCurve).
  longA: 1.0,
  longU: 0.9,
  longI: 0.85,
  markA: 0.75, // fatha, wasla and the other vowels the text marks itself
  markI: 0.7,
  markU: 0.7,
  leadVowelWeight: 0.85, // the part of a letter before a long vowel that already takes its shape
  slotWeight: 0.95, // a short vowel the text does not write; which one comes from the audio
  slotMinMs: 35, // a letter shorter than consonant part + this has no vowel slot
  finalSlotMinMs: 90, // a word-final letter before a space gets a slot only if at least this long
  slotConsFrac: 0.45, // share of a letter's time for the consonant, the rest is the vowel
  slotConsMinMs: 30,
  slotConsMaxMs: 70,
  bilabMaxMs: 120, // the longest closure part of a b or m
  hamzaMinMs: 40,
  hamzaMaxMs: 60,
  bMinMs: 50, // a closure is held at least this long (a lip closure under 40 ms is not seen)
  mMinMs: 60,
  shaddaHold: 1.5, // a doubled letter holds longer
  ffMinMs: 50,
  // Natural undershoot (a short vowel, fast speech) is off: at 0.8 and 0.85 the open vowels missed
  // the readability bars (K1, K2) and the mouth looked small; full poses read better on the avatar.
  undershootMs: 70, // a vowel shorter than this is scaled by `undershoot`
  undershoot: 1.0,
  fastCount: 6, // more vowels than this in one second are scaled by `fast`
  fast: 1.0,
  stopOnsetMaxMs: 60, // a stop is heard after its closure: the expected onset is later by up to this
  emphA: 1.1, // a vowel next to an emphatic letter: aa times this, plus emphO on the rounded shape
  emphO: 0.1,

  // --- Sampling (timelineTrack.js) ---
  windowMs: 220, // segments farther than this from the time of the frame are ignored
  background: 0.02, // the weight of "nothing", so a far-off segment fades out
  closureHoldMs: 120, // PP stays at the floor at least this long from the start of a b or m (the vowel is then pushed aside)
  labioHoldMs: 70,
  ppFloor: 0.95, // inside a closure (shrunk by closureShrinkMs each side) PP is at least this
  closureShrinkMs: 5,
  ffFloor: 0.8,
  slotListenMs: 0, // a slot takes the audio's vowel class once the voice has been heard this long in it
  slotListenEndMs: 0, // the audio is listened to until this long after the end of the slot
  unknownFadeMs: 25, // how fast the blend moves from the text shapes to the audio's inside an unknown span
  // Dominance by role (index = ROLE in arabicText.js: dom, dom-u, semi, rec, vowel, sil, unk):
  // alpha is the strength, before and after the span the dominance falls as exp(-distance / theta).
  // The unknown role (an English letter other than b, p, m, f; a digit) has a dominance of its own: without it the
  // lone closure next to it has nothing to compete with and PP starts to rise 70-100 ms ahead of the letter, which
  // eats the whole vowel of "Mama" (lip-sync glitch test, 2026-10-05). Its shape is still drawn from the audio.
  alpha: [1.0, 1.0, 3.0, 0.1, 2.0, 0.5, 2.0],
  thetaBefore: [25, 100, 30, 20, 45, 60, 20],
  thetaAfter: [20, 60, 30, 20, 45, 80, 20],

  // --- Sync (timelineSync.js) ---
  latchOffsetMs: 40, // added to the first expected onset: the gate opens about this long after a sound begins
  gateSilenceMs: 60, // the gate must have been shut this long for its opening to count as an onset
  retroMs: 400, // a late go or late data still latches onto an onset this recent
  reanchorSilenceMs: 90, // after this much silence the clock may be re-set at the next onset
  reanchorWindowMs: 250, // ... to an expected onset within this distance
  reanchorMaxStepMs: 60, // a re-anchor moves the clock by at most this much (the gate onset jitters)
  stallMs: 180, // the gate shut this long while the text says speech: the audio has stalled
  pauseAheadMs: 200, // a silence that starts at most this long before a pause of the text is that pause
  pauseOverrunMs: 300, // ... until it outlasts the pause by this much: then it is a stall after all
  reanchorPausesOnly: 1, // 1: re-anchor only at the onset after a pause of the text, not after a gap inside a word
  hardSilenceRms: 2e-5, // a gap whose quietest frame is below this is digital silence: a shorter stall is real
  pauseOverlapMs: 50, // a silence in the audio is a pause of the text if they overlap this much
  stallVowelMs: 0, // ...meaning the text has at least this much vowel in the silence
  endStateMs: 400, // the agent left "speaking" this long ago: the timeline is over
  endAfterMs: 300, // the track ended this long ago: the timeline is over
  mixInRate: 60, // 1/s, how fast the shown mouth moves from the audio-only one to the text-timed one
  mixOutRate: 12,
};

/** The smoother of the text-timed weights: the targets are exact, so it is quicker than SMOOTHING. */
export const TIMELINE_SMOOTHING = {
  preRate: 250,
  attack: {
    [VI.PP]: 200, [VI.FF]: 50, [VI.DD]: 50, [VI.kk]: 50, [VI.CH]: 50, [VI.SS]: 50, [VI.nn]: 40,
    [VI.RR]: 50, [VI.aa]: 50, [VI.E]: 50, [VI.I]: 50, [VI.O]: 50, [VI.U]: 50,
  },
  release: {
    [VI.PP]: 80, [VI.FF]: 30, [VI.DD]: 30, [VI.kk]: 30, [VI.CH]: 30, [VI.SS]: 30, [VI.nn]: 30,
    // The vowels let go a little faster (38, not 30) so a full vowel does not hold the lips apart at
    // the next closure (K3).
    [VI.RR]: 30, [VI.aa]: 38, [VI.E]: 38, [VI.I]: 38, [VI.O]: 38, [VI.U]: 38,
  },
  maxSum: 1.0,
};

export const BLINK = {
  minInterval: 2,
  maxInterval: 6,
  doubleChance: 0.18, // chance that a blink is followed at once by a second one
  doubleGap: [0.09, 0.2], // seconds between the two blinks of a double blink
  closeTime: 0.07,
  holdTime: 0.03,
  openTime: 0.13,
  stressBlock: 0.5, // no blink starts while the stress value is above this
  maxDefer: 3, // but never wait longer than this
  phraseEndChance: 0.6, // blink at the end of a phrase this often (when it has been a while)
  phraseEndMinSince: 1.2, // only if the last blink was at least this long ago
  phraseEndDelay: [0.05, 0.22],
};

/**
 * How much of the old jaw-bone motion to keep when the avatar has viseme morphs (0 = none, 1 = all).
 * The morphs already open the mouth, so the default is 0; raise it a little if the GLB's visemes
 * are mouth shapes only and the chin should drop with them.
 */
export const JAW_WITH_VISEMES = 0;
