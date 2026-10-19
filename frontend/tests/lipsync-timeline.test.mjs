// Run with: npm run test:lipsync   (node's built-in test runner, no extra dependency)
// The text-timed hybrid of the Arabic lip-sync: the text to mouth rules (arabicText.js), the
// sampler (timelineTrack.js), the clock that follows the audio (timelineSync.js), the message
// helpers, and requirement R2 (no timeline: the output is the audio-only output, unchanged).
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { CLS, KIND, buildTrack } from '../src/features/child/components/avatar/lipsync/arabicText.js';
import { HybridLipsync } from '../src/features/child/components/avatar/lipsync/hybridLipsync.js';
import { LipsyncEngine, analyseBuffer } from '../src/features/child/components/avatar/lipsync/lipsyncEngine.js';
import { TIMELINE } from '../src/features/child/components/avatar/lipsync/lipsyncConfig.js';
import {
  MAX_ITEMS_PER_MESSAGE,
  alignmentToItems,
  goMessage,
  stopMessage,
  timelineMessages,
} from '../src/features/child/components/avatar/lipsync/timelineMessages.js';
import { PHASE, TimelineSync } from '../src/features/child/components/avatar/lipsync/timelineSync.js';
import { TrackSampler } from '../src/features/child/components/avatar/lipsync/timelineTrack.js';
import { VI, VISEME_COUNT } from '../src/features/child/components/avatar/lipsync/visemes.js';
import {
  VOWEL_FORMANTS,
  concat,
  silence,
  vowel,
} from '../src/features/child/components/avatar/lipsync/testSignals.js';

const SR = 48000;

/** One item per character, `d` ms each, from t = 0. */
const items = (text, d = 100) => [...text].map((c, i) => [c, i * d, d]);
const track = (text, d = 100, o) => buildTrack(items(text, d), o);
const closures = (tr) => tr.segs.filter((s) => s.bilab);
const vowels = (tr) => tr.segs.filter((s) => s.kind === KIND.VOWEL);

const FATHA = 'َ';
const KASRA = 'ِ';
const DAMMA = 'ُ';
const SHADDA = 'ّ';
const SUKUN = 'ْ';
const FATHATAN = 'ً';

// --- arabicText: the text to mouth rules ------------------------------------------------------

test('text: every meem and baa is a lip closure, nothing else is', () => {
  const tr = track('مرحبا'); // m r H b aa
  const c = closures(tr);
  assert.equal(c.length, 2);
  assert.deepEqual(c.map((s) => s.ch), ['م', 'ب']);
  assert.equal(tr.startsClosed, true, 'a reply that starts with a closure');
  assert.equal(track('كتاب').startsClosed, false);
});

test('text: a long vowel letter after a consonant is a fixed a-class vowel, not a slot', () => {
  const tr = track('بابا'); // baaba
  const v = vowels(tr);
  assert.ok(v.length >= 2);
  assert.ok(v.every((s) => !s.slot && s.cls === CLS.A));
  assert.ok(v.some((s) => s.base >= 1.0), 'the long vowel is at full weight');
});

test('text: waw and yaa without a mark after a consonant are long u and i', () => {
  const u = vowels(track('نور')).find((s) => s.cls === CLS.U);
  assert.ok(u && !u.slot, 'nuur has a long u');
  const i = vowels(track('كبير')).find((s) => s.cls === CLS.I);
  assert.ok(i && !i.slot, 'kabiir has a long i');
});

test('text: an unwritten short vowel is a slot that the audio decides, a marked one is fixed', () => {
  const bare = vowels(track('كتب')); // ktb
  assert.ok(bare.some((s) => s.slot), 'ktb has slots');
  for (const s of bare.filter((x) => x.slot)) assert.ok(Array.isArray(s.votes) || s.votes instanceof Float32Array || s.votes);
  const marked = vowels(track(`ك${FATHA}ت${KASRA}ب${DAMMA}`));
  assert.deepEqual(marked.map((s) => [s.slot, s.cls]), [[false, CLS.A], [false, CLS.I], [false, CLS.U]]);
});

test('text: shadda holds a closure longer, sukun leaves no vowel after the letter', () => {
  const plain = closures(track('أم'))[0];
  const doubled = closures(track(`أم${SHADDA}`))[0];
  assert.ok(doubled.t1 - doubled.t0 > plain.t1 - plain.t0, 'the doubled meem is held longer');
  // m a n(sukun) z: no vowel segment between the noon and the zayn
  const tr = track(`م${FATHA}ن${SUKUN}ز${KASRA}`);
  const noon = tr.segs.find((s) => s.ch === 'ن');
  const zay = tr.segs.find((s) => s.ch === 'ز');
  const between = vowels(tr).filter((s) => s.t0 >= noon.t1 - 1 && s.t1 <= zay.t0 + 1);
  assert.equal(between.length, 0);
});

test('text: tanween gives a vowel and a short n', () => {
  const tr = track(`كتاب${FATHATAN}ا`);
  assert.ok(tr.segs.some((s) => s.kind === KIND.CONS && s.ch === ''), 'the tanween n is a consonant part');
  assert.ok(vowels(tr).some((s) => s.cls === CLS.A && !s.slot));
});

test('text: taa marbuta is silent before a pause, a soft t inside', () => {
  const end = track('مدرسة'); // madrasa(h), final
  assert.ok(!end.segs.some((s) => s.ch === 'ة'), 'no segment for the final ta marbuta');
  const mid = buildTrack([...items('مدرسة', 100), [' ', 500, 100], ...items('كبير', 100).map(([c, t, d]) => [c, t + 600, d])]);
  assert.ok(mid.segs.some((s) => s.kind === KIND.SIL || s.kind === KIND.VOWEL));
});

test('text: hamza seats give a dip and the vowel of the seat', () => {
  const tr = track('سؤال'); // su'aal
  assert.ok(tr.segs.some((s) => s.kind === KIND.DIP), 'hamza dip');
  assert.ok(vowels(tr).some((s) => s.cls === CLS.U), 'the waw seat: u');
  const kasra = track('إيمان'); // iimaan, kasra seat
  assert.equal(vowels(kasra)[0].cls, CLS.I);
});

test('text: the first alef takes the vowel its mark says, a without one', () => {
  assert.equal(vowels(track(`ا${KASRA}ب${SUKUN}ن`))[0].cls, CLS.I);
  assert.equal(vowels(track(`ا${DAMMA}ب`))[0].cls, CLS.U);
  assert.equal(vowels(track('ٱبن'))[0].cls, CLS.A);
});

test('text: the article lam is not skipped before a sun letter, and the wasla alef is silent mid-reply', () => {
  const sun = track('الشمس'); // ash-shams
  assert.ok(sun.segs.some((s) => s.ch === 'ش'));
  assert.ok(closures(sun).length === 1, 'the meem');
  const mid = buildTrack([
    ...items('هذا', 100),
    [' ', 300, 60],
    ['ا', 360, 80],
    ['ل', 440, 80],
    ['ق', 520, 80],
    ['م', 600, 80],
  ]);
  const wasla = mid.segs.filter((s) => s.kind === KIND.VOWEL && s.t0 >= 360 && s.t1 <= 440 + 1 && !s.slot);
  assert.equal(wasla.length, 0, 'no vowel shape on the wasla alef');
});

test('text: spaces shorter than a pause leave no silence, longer ones do', () => {
  const short = buildTrack([['ب', 0, 100], ['ا', 100, 100], [' ', 200, 50], ['ب', 250, 100]]);
  assert.ok(!short.segs.some((s) => s.kind === KIND.SIL));
  const long = buildTrack([['ب', 0, 100], ['ا', 100, 100], [' ', 200, 200], ['ب', 400, 100]]);
  const sil = long.segs.filter((s) => s.kind === KIND.SIL);
  assert.equal(sil.length, 1);
  assert.ok(sil[0].t0 >= 190 && sil[0].t1 <= 410);
});

test('text: emphatic letters mark the vowels next to them', () => {
  const tr = track('صاد'); // saad
  assert.ok(vowels(tr).some((s) => s.emph));
  assert.ok(!vowels(track('باب')).some((s) => s.emph));
});

test('text: onsets, start and end are in the reply clock', () => {
  const tr = buildTrack(items('كتاب', 100).map(([c, t, d]) => [c, t + 250, d]));
  assert.equal(tr.startMs, 250);
  assert.ok(tr.endMs >= 650 - 1);
  assert.ok(tr.onsets.length >= 1 && tr.onsets[0] >= 250);
});

test('text: unknown characters become audio-driven spans', () => {
  const tr = track('با€با');
  assert.ok(tr.segs.some((s) => s.kind === KIND.UNK));
});

test('text: Latin letters give the labial closures only, in both languages', () => {
  for (const lang of ['ar', 'en']) {
    const tr = track('mab', 100, { lang });
    assert.deepEqual(closures(tr).map((s) => s.ch), ['m', 'b']);
    assert.ok(tr.segs.filter((s) => !s.bilab).every((s) => s.kind === KIND.UNK), 'the rest is left to the audio');
  }
});

test('text: empty and junk input give an empty, valid track', () => {
  const tr = buildTrack([]);
  assert.deepEqual(tr.segs, []);
  assert.equal(tr.onsets.length, 0);
  assert.doesNotThrow(() => buildTrack([['x', NaN, undefined], [5, 0, 1]]));
});

// --- the sampler ------------------------------------------------------------------------------

function sampler(text, d = 100) {
  const s = new TrackSampler(track(text, d));
  s.leadMs = 0;
  return s;
}

test('sampler: inside a closure PP is at the floor and the rest is squeezed out', () => {
  const s = sampler('بابا', 200);
  const out = new Float32Array(VISEME_COUNT);
  // the first baa is ~0..90 ms: sample at 40
  s.sample(40, -1, 0.5, out);
  assert.ok(out[VI.PP] >= TIMELINE.ppFloor - 1e-6, `PP ${out[VI.PP]}`);
  let sum = 0;
  for (let i = 1; i < VISEME_COUNT; i++) sum += out[i];
  assert.ok(sum <= 1.0001);
});

test('sampler: a long a opens the mouth, and louder opens it more', () => {
  const s = sampler('بابا', 200);
  const quiet = new Float32Array(VISEME_COUNT);
  const loud = new Float32Array(VISEME_COUNT);
  s.sample(290, -1, 0.05, quiet);
  s.sample(290, -1, 1.0, loud);
  assert.ok(quiet[VI.aa] > 0.4, `aa ${quiet[VI.aa]}`);
  assert.ok(loud[VI.aa] > quiet[VI.aa]);
});

test('sampler: a slot takes the vowel class the audio shows', () => {
  const tr = track('كتب', 200);
  const slot = tr.segs.find((s) => s.slot);
  const s = new TrackSampler(tr);
  s.leadMs = 0;
  const out = new Float32Array(VISEME_COUNT);
  const mid = (slot.t0 + slot.t1) / 2;
  for (let k = 0; k < 6; k++) s.sample(mid, CLS.I, 0.8, out);
  assert.equal(slot.cls, CLS.I);
  assert.ok(out[VI.I] > out[VI.aa]);
  const s2 = new TrackSampler(track('كتب', 200));
  s2.leadMs = 0;
  const slot2 = s2.track.segs.find((x) => x.slot);
  for (let k = 0; k < 6; k++) s2.sample((slot2.t0 + slot2.t1) / 2, CLS.U, 0.8, out);
  assert.equal(slot2.cls, CLS.U);
  assert.ok(out[VI.U] > out[VI.aa]);
});

test('sampler: the mouth leads the sound by leadMs', () => {
  const tr = track('كبب', 200);
  const a = new TrackSampler(tr);
  a.leadMs = 0;
  const b = new TrackSampler(tr);
  b.leadMs = 100;
  const oa = new Float32Array(VISEME_COUNT);
  const ob = new Float32Array(VISEME_COUNT);
  const bab = tr.segs.find((s) => s.bilab);
  a.sample(bab.t0 - 80, -1, 0.5, oa);
  b.sample(bab.t0 - 80, -1, 0.5, ob);
  assert.ok(ob[VI.PP] > oa[VI.PP], 'with the lead the closure shows earlier');
});

test('sampler: an unknown span reports how much the audio should be used', () => {
  const s = sampler('با€با', 200);
  const out = new Float32Array(VISEME_COUNT);
  s.sample(450, -1, 0.5, out);
  assert.ok(s.unk > 0.9);
  s.sample(50, -1, 0.5, out);
  assert.ok(s.unk < 0.5);
});

test('sampler: no track gives zeros, and an empty track does not throw', () => {
  const out = new Float32Array(VISEME_COUNT).fill(0.3);
  new TrackSampler().sample(10, -1, 0.5, out);
  assert.ok(out.every((v) => v === 0));
  const s = new TrackSampler(buildTrack([]));
  assert.doesNotThrow(() => s.sample(10, -1, 0.5, out));
});

test('sampler: an English closure next to letters left to the audio stays closed', () => {
  // Between b, m, p the English letters are unknown spans (the audio's shapes). Their audio share
  // must not pull the lips apart inside the closure (reviewer fix: closures 0 -> 23 of 23 in English).
  const s = new TrackSampler(track('amab', 100, { lang: 'en' }));
  s.leadMs = 0;
  const m = s.track.segs.find((x) => x.bilab);
  const out = new Float32Array(VISEME_COUNT);
  s.sample(m.t0 + 25, -1, 0.5, out);
  assert.ok(out[VI.PP] >= TIMELINE.ppFloor - 1e-6, `PP ${out[VI.PP]}`);
  assert.equal(s.unk, 0, 'no audio share inside the closure');
});

test('sampler: vowels lead the sound by vowelLeadMs, consonants by leadMs', () => {
  const tr = track('كتب', 200);
  const slot = tr.segs.find((x) => x.slot);
  const at = (vowelLeadMs) => {
    const saved = TIMELINE.vowelLeadMs;
    TIMELINE.vowelLeadMs = vowelLeadMs;
    try {
      const s = new TrackSampler(tr);
      s.leadMs = TIMELINE.leadMs;
      const out = new Float32Array(VISEME_COUNT);
      s.sample(slot.t0 - 35, -1, 0.5, out); // 35 ms before the vowel is heard
      return out[VI.aa];
    } finally {
      TIMELINE.vowelLeadMs = saved;
    }
  };
  assert.ok(TIMELINE.vowelLeadMs < TIMELINE.leadMs);
  assert.ok(at(TIMELINE.vowelLeadMs) < at(TIMELINE.leadMs), 'the vowel opens later than with the full lead');
});

// --- timelineMessages -------------------------------------------------------------------------

test('messages: items from an alignment in ms, short-vowel marks folded into the letter', () => {
  const al = { characters: ['ك', FATHA, 'ت'], starts: [0, 0.05, 0.1], ends: [0.05, 0.1, 0.2] };
  assert.deepEqual(alignmentToItems(al), [['ك', 0, 50], [FATHA, 50, 50], ['ت', 100, 100]]);
  assert.deepEqual(alignmentToItems(al, { dropMarks: true }), [['ك', 0, 100], ['ت', 100, 100]]);
});

test('messages: at most 120 characters in a packet, in order, with a sequence number', () => {
  const it = Array.from({ length: 300 }, (_, i) => ['ب', i * 10, 10]);
  const msgs = timelineMessages(it, 's1');
  assert.equal(MAX_ITEMS_PER_MESSAGE, 120);
  assert.deepEqual(msgs.map((m) => m.t.length), [120, 120, 60]);
  assert.deepEqual(msgs.map((m) => m.seq), [0, 1, 2]);
  assert.ok(msgs.every((m) => m.v === 1 && m.sp === 's1' && m.lang === 'ar'));
  assert.deepEqual(goMessage('s1'), { v: 1, sp: 's1', go: 1 });
  assert.deepEqual(stopMessage('s1'), { v: 1, sp: 's1', stop: 1 });
});

// --- timelineSync -----------------------------------------------------------------------------

const LINE = items('بابا كتاب مدرسة', 100);

/** Feed `gate(t)` to the sync every 10 ms from `from` to `to`. */
function drive(sync, from, to, gate, rms = 0) {
  for (let t = from; t <= to; t += 10) sync.onFrame(gate(t), t, rms);
}

function started(sync, sp = 'a', { dataAt = -300, goAt = 0 } = {}) {
  for (const m of timelineMessages(LINE, sp)) sync.push(m, dataAt);
  sync.push(goMessage(sp), goAt);
}

test('sync: data then go arms the clock, the first sound latches it', () => {
  const sync = new TimelineSync();
  started(sync);
  assert.equal(sync.phase, PHASE.ARMED);
  assert.equal(sync.position(100), -1, 'not timed before the sound');
  drive(sync, 0, 190, () => false);
  drive(sync, 200, 300, () => true);
  assert.equal(sync.phase, PHASE.LOCKED);
  const first = sync.track.onsets[0];
  assert.ok(Math.abs(sync.position(200) - (first + TIMELINE.latchOffsetMs)) < 1e-6);
  assert.ok(Math.abs(sync.position(300) - sync.position(200) - 100) < 1e-6, 'the clock runs with real time');
});

test('sync: a go that arrives late still latches to the onset that has just happened', () => {
  const sync = new TimelineSync();
  for (const m of timelineMessages(LINE, 'a')) sync.push(m, -300);
  drive(sync, 0, 90, () => false);
  drive(sync, 100, 240, () => true); // the sound began at 100, no go yet
  assert.equal(sync.phase, PHASE.IDLE);
  sync.push(goMessage('a'), 250);
  assert.equal(sync.phase, PHASE.LOCKED);
  assert.ok(Math.abs(sync.position(100) - (sync.track.onsets[0] + TIMELINE.latchOffsetMs)) < 1e-6);
});

test('sync: a go much later than the sound falls back to audio-only until the next pause', () => {
  const sync = new TimelineSync();
  for (const m of timelineMessages(LINE, 'a')) sync.push(m, -300);
  drive(sync, 0, 90, () => false);
  drive(sync, 100, 800, () => true);
  sync.push(goMessage('a'), 800);
  assert.equal(sync.phase, PHASE.AUDIO);
  assert.equal(sync.position(800), -1);
});

test('sync: a timeline without its go is never shown, however the audio sounds', () => {
  const sync = new TimelineSync();
  for (const m of timelineMessages(LINE, 'stale')) sync.push(m, -500);
  drive(sync, 0, 90, () => false);
  drive(sync, 100, 900, () => true);
  assert.equal(sync.phase, PHASE.IDLE);
  assert.equal(sync.position(500), -1);
  assert.equal(sync.track, null);
});

test('sync: a newer go drops the timelines that never got one', () => {
  const sync = new TimelineSync();
  for (const m of timelineMessages(LINE, 'stale')) sync.push(m, -500);
  started(sync, 'now', { dataAt: -300, goAt: 0 });
  assert.ok(!sync.lines.has('stale'));
  assert.equal(sync.cur.sp, 'now');
});

test('sync: a stall (sound stops mid-word, text says speech) holds the clock and resumes from there', () => {
  const sync = new TimelineSync();
  started(sync);
  drive(sync, 0, 90, () => false);
  drive(sync, 100, 500, () => true); // sound from 100 to 500: in the text, 'baaba kitaab' still speaking
  const posAtStop = sync.position(500);
  drive(sync, 510, 900, () => false); // 400 ms of nothing while the text has a vowel
  assert.equal(sync.phase, PHASE.STALLED);
  assert.equal(sync.position(900), -1, 'no text timing while stalled');
  drive(sync, 910, 1000, () => true);
  assert.equal(sync.phase, PHASE.LOCKED);
  const resumed = sync.position(910);
  assert.ok(Math.abs(resumed - posAtStop) < 30, `resumed ${resumed} from ${posAtStop}`);
});

test('sync: a short gate dropout inside a word (a quiet vowel, a voiceless consonant) does not hold the clock', () => {
  // At 48 kHz the voice gate drops out for 100 to 170 ms in places the text calls speech. That is
  // shorter than stallMs, so the clock keeps running; holding it would shift every later mouth.
  const sync = new TimelineSync();
  started(sync);
  drive(sync, 0, 90, () => false);
  drive(sync, 100, 400, () => true);
  const before = sync.offset;
  drive(sync, 410, 540, () => false, 1e-3); // 130 ms dropout, below stallMs, the voice still faintly there
  assert.equal(sync.phase, PHASE.LOCKED);
  drive(sync, 550, 700, () => true);
  assert.equal(sync.phase, PHASE.LOCKED);
  assert.ok(Math.abs(sync.offset - before) <= TIMELINE.reanchorMaxStepMs + 1e-6, `offset ${sync.offset} from ${before}`);
});

test('sync: 150 ms of digital silence inside a word is a stall and holds the clock', () => {
  const sync = new TimelineSync();
  started(sync);
  drive(sync, 0, 90, () => false);
  drive(sync, 100, 250, () => true); // the first word is 'baaba', speech until about 400 in the text
  const posAtStop = sync.position(250);
  drive(sync, 260, 400, () => false, 0); // 140 ms of exact zeros: below stallMs but not a dropout
  drive(sync, 410, 550, () => true);
  assert.equal(sync.phase, PHASE.LOCKED);
  assert.ok(Math.abs(sync.position(410) - posAtStop) < 30, `resumed ${sync.position(410)} from ${posAtStop}`);
});

test('sync: a re-anchor moves the clock by at most reanchorMaxStepMs', () => {
  const sync = new TimelineSync();
  const it = [...items('بابا', 100), [' ', 400, 400], ...items('بابا', 100).map(([c, t, d]) => [c, t + 800, d])];
  for (const m of timelineMessages(it, 'p')) sync.push(m, -300);
  sync.push(goMessage('p'), 0);
  drive(sync, 0, 90, () => false);
  drive(sync, 100, 450, () => true);
  const before = sync.offset;
  drive(sync, 460, 1010, () => false); // the pause, but the sound comes back 100 ms after the text says
  drive(sync, 1020, 1200, () => true);
  assert.equal(sync.phase, PHASE.LOCKED);
  const step = sync.offset - before;
  assert.ok(Math.abs(step) <= TIMELINE.reanchorMaxStepMs + 1e-6, `step ${step}`);
  assert.ok(step > 0, 'it still moves toward the sound');
});

test('sync: a silence that the text explains (a pause) is not a stall and re-anchors at the next onset', () => {
  const sync = new TimelineSync();
  const it = [...items('بابا', 100), [' ', 400, 400], ...items('بابا', 100).map(([c, t, d]) => [c, t + 800, d])];
  for (const m of timelineMessages(it, 'p')) sync.push(m, -300);
  sync.push(goMessage('p'), 0);
  drive(sync, 0, 90, () => false);
  drive(sync, 100, 450, () => true);
  drive(sync, 460, 900, () => false); // the pause of the text, 440 ms
  assert.equal(sync.phase, PHASE.LOCKED, 'the pause is explained by the text');
  drive(sync, 910, 1000, () => true);
  assert.equal(sync.phase, PHASE.LOCKED);
  const second = sync.track.segs.filter((s) => s.kind !== KIND.SIL && s.t0 >= 800)[0];
  assert.ok(Math.abs(sync.position(910) - (800 + TIMELINE.latchOffsetMs)) < 60, `pos ${sync.position(910)} for ${second.t0}`);
});

const PAUSED = [...items('بابا', 100), [' ', 400, 400], ...items('بابا', 100).map(([c, t, d]) => [c, t + 800, d])];

test('sync: the voice stopping a little before the pause of the text is that pause, not a stall', () => {
  // A silent final letter (an English silent e, a taa marbuta) or a fading consonant ends the sound
  // up to pauseAheadMs before the alignment's pause. Holding the clock there put English replies
  // 0.6 to 1.2 s behind (reviewer finding); the clock must run on and re-anchor after the pause.
  const sync = new TimelineSync();
  for (const m of timelineMessages(PAUSED, 'e')) sync.push(m, -300);
  sync.push(goMessage('e'), 0);
  drive(sync, 0, 90, () => false);
  drive(sync, 100, 250, () => true); // the sound ends 175 ms before the text's pause at 400
  for (let t = 260; t <= 880; t += 10) {
    sync.onFrame(false, t, 1e-3); // quiet, not digital silence
    assert.notEqual(sync.phase, PHASE.STALLED, `stalled at ${t}`);
  }
  drive(sync, 890, 1000, () => true);
  assert.equal(sync.phase, PHASE.LOCKED);
  const onset = sync.track.onsets[1];
  assert.ok(Math.abs(sync.position(890) - (onset + TIMELINE.latchOffsetMs)) < 20, `pos ${sync.position(890)} for ${onset}`);
});

test('sync: a pause that runs far past the text is a stall held at the end of the pause', () => {
  const sync = new TimelineSync();
  for (const m of timelineMessages(PAUSED, 'q')) sync.push(m, -300);
  sync.push(goMessage('q'), 0);
  drive(sync, 0, 90, () => false);
  drive(sync, 100, 450, () => true);
  drive(sync, 460, 1400, () => false, 1e-3); // the text's pause is 400 ms, the audio's is 950 ms
  assert.equal(sync.phase, PHASE.STALLED);
  drive(sync, 1410, 1500, () => true);
  assert.equal(sync.phase, PHASE.LOCKED);
  const onset = sync.track.onsets[1];
  assert.ok(Math.abs(sync.position(1410) - (onset + TIMELINE.latchOffsetMs)) < 1e-6, `pos ${sync.position(1410)}`);
});

test('sync: a timeline the agent could not name (?) is taken by the next go, later packets too', () => {
  const sync = new TimelineSync();
  const msgs = timelineMessages(LINE, '?', { chunk: 6 });
  assert.ok(msgs.length >= 2);
  sync.push(msgs[0], -300);
  sync.push(goMessage('s7'), 0);
  for (const m of msgs.slice(1)) sync.push(m, 20);
  assert.equal(sync.cur.sp, 's7');
  assert.equal(sync.cur.items.length, LINE.length);
  assert.equal(sync.phase, PHASE.ARMED);
  assert.ok(!sync.lines.has('?'));
});

test('sync: stop, a long end of speaking and the end of the track each clear the timeline', () => {
  let sync = new TimelineSync();
  started(sync);
  sync.push(stopMessage('a'), 50);
  assert.equal(sync.phase, PHASE.IDLE);
  assert.equal(sync.track, null);

  sync = new TimelineSync();
  started(sync);
  drive(sync, 0, 90, () => false);
  drive(sync, 100, 200, () => true);
  sync.agentState(false, 200);
  drive(sync, 210, 500, () => true);
  assert.equal(sync.phase, PHASE.LOCKED, 'under endStateMs it still holds');
  drive(sync, 510, 700, () => true);
  assert.equal(sync.phase, PHASE.IDLE, 'cleared after endStateMs');

  sync = new TimelineSync();
  started(sync);
  drive(sync, 0, 90, () => false);
  drive(sync, 100, 2500, () => true);
  assert.equal(sync.phase, PHASE.IDLE, 'cleared after the track ended');
});

test('sync: bad messages are ignored and a JSON string is accepted', () => {
  const sync = new TimelineSync();
  for (const m of [null, 5, 'not json', { v: 2, sp: 'a', go: 1 }, { v: 1, sp: 'a', t: 'x' }, { v: 1, sp: 'a', t: [[1, 2, 3], ['x', 'y', 1]] }]) {
    assert.doesNotThrow(() => sync.push(m, 0));
  }
  assert.equal(sync.phase, PHASE.IDLE);
  for (const m of timelineMessages(LINE, 'j')) sync.push(JSON.stringify(m), 0);
  sync.push(JSON.stringify(goMessage('j')), 0);
  assert.equal(sync.phase, PHASE.ARMED);
});

test('sync: a reply that starts with a closure keeps the lips together while armed', () => {
  const eng = new LipsyncEngine(SR, { lang: 'ar' });
  const sync = new TimelineSync();
  const hy = new HybridLipsync(eng, { sync });
  started(sync); // LINE starts with a baa
  assert.equal(sync.track.startsClosed, true);
  const win = new Float32Array(2048);
  let w;
  for (let k = 0; k < 20; k++) w = hy.process(win, 1 / 60, k * 16.7);
  assert.ok(w[VI.PP] > 0.8, `PP ${w[VI.PP]}`);
});

// --- R2 and P1 --------------------------------------------------------------------------------

function signal() {
  return concat(
    silence(0.3),
    vowel({ ...VOWEL_FORMANTS.aa, dur: 0.3 }),
    silence(0.1),
    vowel({ ...VOWEL_FORMANTS.I, dur: 0.3 }),
    vowel({ ...VOWEL_FORMANTS.U, dur: 0.3 }),
    silence(0.4),
  );
}

test('R2: no timeline gives the audio-only engine output, value for value', () => {
  const sig = signal();
  const a = analyseBuffer(sig, SR, { lang: 'ar' });
  const b = analyseBuffer(sig, SR, { lang: 'ar', timeline: [] }); // a sync that never gets a message
  assert.equal(a.frames.length, b.frames.length);
  for (let k = 0; k < a.frames.length; k++) {
    assert.deepEqual(Array.from(b.frames[k].weights), Array.from(a.frames[k].weights), `frame ${k}`);
    assert.equal(b.frames[k].timed, false);
  }
});

test('R2: without a sync the hybrid returns the engine\'s own array', () => {
  const eng = new LipsyncEngine(SR, { lang: 'ar' });
  const hy = new HybridLipsync(eng);
  const win = new Float32Array(2048);
  const out = hy.process(win, 1 / 60, 0);
  assert.equal(out, eng.weights);
  assert.equal(hy.timed, false);
});

test('R2: a stale timeline (no go) changes nothing in the output', () => {
  const sig = signal();
  const plain = analyseBuffer(sig, SR, { lang: 'ar' });
  const stale = analyseBuffer(sig, SR, {
    lang: 'ar',
    timeline: timelineMessages(LINE, 'stale').map((msg) => ({ t: -0.5, msg })),
  });
  for (let k = 0; k < plain.frames.length; k++) {
    assert.deepEqual(Array.from(stale.frames[k].weights), Array.from(plain.frames[k].weights), `frame ${k}`);
  }
});

test('hybrid: with a timeline and its go the mouth is text-timed and the closures show', () => {
  const sig = concat(silence(0.3), vowel({ ...VOWEL_FORMANTS.aa, dur: 1.2 }), silence(0.3));
  const tl = [
    ...timelineMessages(items('بابابا', 200), 'x').map((msg) => ({ t: -0.3, msg })),
    { t: 0, msg: goMessage('x') },
  ];
  const r = analyseBuffer(sig, SR, { lang: 'ar', timeline: tl });
  assert.ok(r.frames.some((f) => f.timed), 'timed frames');
  const maxPP = Math.max(...r.frames.map((f) => f.weights[VI.PP]));
  assert.ok(maxPP >= 0.9, `PP ${maxPP}`);
});

test('P1: a hybrid step costs under 0.05 ms and allocates no array per frame', () => {
  const eng = new LipsyncEngine(SR, { lang: 'ar' });
  const sync = new TimelineSync();
  const hy = new HybridLipsync(eng, { sync });
  const long = items('بابا كتاب مدرسة الشمس القمر '.repeat(8), 90);
  for (const m of timelineMessages(long, 'p')) sync.push(m, -300);
  sync.push(goMessage('p'), 0);
  const win = vowel({ ...VOWEL_FORMANTS.aa, dur: 0.1, sr: SR }).subarray(0, 2048);
  const buf = new Float32Array(2048);
  buf.set(win.subarray(0, Math.min(2048, win.length)));
  // Warm up, and get the clock locked.
  let now = 0;
  for (let k = 0; k < 120; k++, now += 16.7) hy.process(buf, 1 / 60, now);
  assert.ok(hy.timed, 'locked before measuring');
  // Time only the part the hybrid adds: engine time is measured separately.
  const N = 3000;
  const heap0 = process.memoryUsage().heapUsed;
  let t0 = process.hrtime.bigint();
  for (let k = 0; k < N; k++, now += 16.7) hy.process(buf, 1 / 60, now);
  const full = Number(process.hrtime.bigint() - t0) / 1e6 / N;
  const heap1 = process.memoryUsage().heapUsed;
  const bare = new LipsyncEngine(SR, { lang: 'ar' });
  for (let k = 0; k < 120; k++) bare.process(buf, 1 / 60);
  t0 = process.hrtime.bigint();
  for (let k = 0; k < N; k++) bare.process(buf, 1 / 60);
  const engineOnly = Number(process.hrtime.bigint() - t0) / 1e6 / N;
  const added = full - engineOnly;
  console.log(`P1: hybrid ${full.toFixed(4)} ms, engine ${engineOnly.toFixed(4)} ms, added ${added.toFixed(4)} ms, heap +${((heap1 - heap0) / 1024).toFixed(0)} KiB over ${N} frames`);
  assert.ok(added < 0.05, `the hybrid adds ${added.toFixed(4)} ms per frame`);
  // Measured with --expose-gc: the engine alone leaves about 26 B per frame and the hybrid about 72 B
  // (boxed numbers, no arrays). A 14-float array per frame would be 3000 * 100 B or more, and the
  // limit is 1.5 MiB over 3000 frames, which also leaves room for the runtime itself.
  assert.ok(heap1 - heap0 < 1.5 * 1024 * 1024, `heap grew ${(heap1 - heap0) / 1024} KiB`);
});
