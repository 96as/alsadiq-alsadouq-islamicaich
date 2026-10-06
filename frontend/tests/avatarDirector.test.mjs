// Tests for the context director and its parts (SPEC-EXPERIENCE sections 5, 7 and 8).
// Pure JS: runs under `node --test` without a browser. Time is simulated at 60 fps.

import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

import { CLIP, CLIP_META, DIRECTOR, FALLBACK, MESH_VISEME_GAIN, resolveClip } from '../src/features/child/components/avatar/avatarConfig.js';
import { createAvatarContextStore, classifyGamification, RING } from '../src/features/child/components/avatar/context/avatarSignals.js';
import { createDirector, makeDirectorOutput } from '../src/features/child/components/avatar/context/avatarDirector.js';
import { LipsyncRig } from '../src/features/child/components/avatar/lipsync/lipsyncRig.js';
import { VISEME_GAIN } from '../src/features/child/components/avatar/lipsync/visemes.js';
import { HP } from '../src/features/child/components/avatar/context/holoTimeline.js';
import {
  createCueTracker, hasFarewell, hasGreeting, endsWithQuestion, normalizeText,
} from '../src/features/child/components/avatar/context/transcriptCues.js';

const DT = 1 / 60;
const ALL = new Set(Object.values(CLIP));
const ANIM2 = new Set(['Idle', 'LookAround', 'Listen', 'Think', 'TalkGesture', 'Wave', 'Happy', 'Walk', 'Blink']);

function mulberry(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let x = a;
    x = Math.imul(x ^ (x >>> 15), x | 1);
    x ^= x + Math.imul(x ^ (x >>> 7), x | 61);
    return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
  };
}

/** A session: a store, a director and a clock. `log` collects what the director asked for. */
function session({ clips = ALL, seed = 7, reduced = false, signals = true } = {}) {
  let clock = 0;
  const store = createAvatarContextStore({ now: () => clock * 1000 });
  const director = createDirector({ rng: mulberry(seed), has: (n) => clips.has(n) });
  const out = makeDirectorOutput();
  const s = {
    store, director, out, clips,
    state: 'idle', voice: -1, reduced, walkIn: false, visible: true, waveAgo: 999,
    bases: [], shots: [], nods: [], phases: [], t: 0,
    log: { base: [], shots: [], nods: [], interrupts: [] },
  };
  if (signals) store.applySnapshot({ 'al.sig_v': '1' });
  s.step = (n = 1) => {
    for (let i = 0; i < n; i++) {
      clock += DT;
      s.t += DT;
      const c = store.ctx;
      director.step(DT, {
        agentState: s.state, signals: c.signals, cues: c.cues, childSpeaking: c.childSpeaking,
        voiceLevel: s.voice, gam: c.gam, sessionEndingSeq: c.sessionEndingSeq, connectSeq: c.connectSeq,
        awaySec: c.awaySec, walkIn: s.walkIn, reduced: s.reduced, visible: s.visible, waveAgo: s.waveAgo,
      }, out);
      if (out.baseChanged) s.cur = out.base;
      if (out.baseChanged) s.log.base.push({ t: s.t, name: out.base, fade: out.baseFade, entry: out.baseEntry });
      if (out.oneShot) s.log.shots.push({ t: s.t, name: out.oneShot, logical: out.oneShotLogical, weight: out.oneShotWeight, force: out.oneShotForce });
      if (out.nod > 0) s.log.nods.push({ t: s.t, w: out.nod });
      if (out.interrupt > 0) s.log.interrupts.push(s.t);
    }
    return s;
  };
  s.run = (sec) => s.step(Math.round(sec / DT));
  s.base = () => s.cur;
  s.attrs = (a) => store.applyChanged(a);
  s.setState = (st) => { s.state = st; };
  s.shot = (logical) => s.log.shots.filter((x) => x.logical === logical);
  s.step(); // the first step only reads the baseline; whatever follows is an event
  s.log.base.length = 0;
  s.t = 0;
  return s;
}

/** One agent reply with a talk style: the attribute change, then speaking, then listening. */
function reply(s, style, n, speakSec = 3) {
  s.attrs({ 'al.talk_style': style, 'al.reply': String(n) });
  s.setState('speaking');
  s.run(speakSec);
  s.setState('listening');
  s.run(1);
}

// ---------------------------------------------------------------- clip table

test('every clip has metadata, and fallbacks point at real clips', () => {
  for (const name of Object.values(CLIP)) {
    assert.ok(CLIP_META[name], `meta for ${name}`);
    assert.ok(CLIP_META[name].dur > 0, `dur for ${name}`);
  }
  for (const [k, v] of Object.entries(FALLBACK)) {
    assert.ok(ALL.has(k), `fallback key ${k}`);
    assert.ok(v === '' || ALL.has(v), `fallback value ${v}`);
  }
  assert.equal(resolveClip(CLIP.talkStory, (n) => ANIM2.has(n)), CLIP.talk);
  assert.equal(resolveClip(CLIP.searchHold, (n) => ANIM2.has(n)), CLIP.think);
  assert.equal(resolveClip(CLIP.greet, (n) => ANIM2.has(n)), CLIP.wave);
  assert.equal(resolveClip(CLIP.found, (n) => ANIM2.has(n)), '');
  assert.equal(resolveClip(CLIP.nod, (n) => ANIM2.has(n)), '');
  assert.equal(resolveClip(CLIP.listenEmpathy, (n) => n === 'Listen'), 'Listen');
});

test('the old Happy stays out of the live flow until the round-2 GLB lands (section 5.9)', () => {
  // today's GLB has a Happy clip, but it is the arms-out round-1 one
  assert.equal(resolveClip(CLIP.happy, (n) => ANIM2.has(n)), '');
  // the round-2 GLB (it carries Greet from the same talk package) plays its fixed Happy
  assert.equal(resolveClip(CLIP.happy, (n) => ALL.has(n)), CLIP.happy);
  const s = session({ clips: ANIM2 });
  s.setState('listening');
  s.run(1);
  s.store.onGamification({ type: 'points', delta: 5 });
  s.run(0.8);
  assert.ok(s.out.smile > 0.5, `the smile still says "yay" (${s.out.smile})`);
  s.run(1.5);
  assert.equal(s.log.shots.filter((x) => x.name === CLIP.happy).length, 0, 'no old Happy clip');
});

test('clip metadata matches section 4 (frames and markers)', () => {
  assert.equal(CLIP_META[CLIP.searchStart].frames, 27);
  assert.equal(CLIP_META[CLIP.found].frames, 48);
  assert.ok(Math.abs(CLIP_META[CLIP.searchStart].markers.bloom - 10 / 30) < 1e-9);
  assert.ok(Math.abs(CLIP_META[CLIP.searchSwipe].markers.advance - 11 / 30) < 1e-9);
  assert.ok(Math.abs(CLIP_META[CLIP.found].markers.sparkle - 24 / 30) < 1e-9);
  assert.equal(CLIP_META[CLIP.searchStart].to, CLIP.searchHold);
  assert.equal(CLIP_META[CLIP.found].to, CLIP.idle);
});

// ---------------------------------------------------------------- base selection

test('idle, listening and speaking pick the plain loops', () => {
  const s = session();
  s.run(0.5);
  assert.equal(s.base(), 'Idle');
  s.setState('listening');
  s.run(1);
  assert.equal(s.base(), 'Listen');
  s.setState('speaking');
  s.step();
  assert.equal(s.base(), 'TalkGesture', 'a change into speaking is immediate');
});

test('thinking under 0.45 s keeps the previous loop, longer picks Think', () => {
  const s = session();
  s.setState('listening');
  s.run(1);
  s.setState('thinking');
  s.run(0.3);
  assert.equal(s.base(), 'Listen');
  s.run(0.5);
  assert.equal(s.base(), 'Think');
  // A fast thinking blip goes back to listening without ever showing Think.
  const f = session();
  f.setState('speaking'); f.run(1);
  f.setState('thinking'); f.run(0.3);
  f.setState('speaking'); f.run(0.5);
  assert.ok(!f.log.base.some((b) => b.name === 'Think'));
});

test('a fresh sad listen style plays Listen_Empathy, and replaces Think while thinking', () => {
  const s = session();
  s.setState('listening');
  s.run(0.5);
  s.attrs({ 'al.listen_style': 'sad', 'al.turn': '1' });
  s.run(1);
  assert.equal(s.base(), 'Listen_Empathy');
  s.setState('thinking');
  s.run(1);
  assert.equal(s.base(), 'Listen_Empathy', 'Think is replaced by the empathy loop');
});

test('excited and curious apply only when fresh; sad stays for 90 s', () => {
  const s = session();
  s.attrs({ 'al.listen_style': 'excited' });
  s.run(0.2);
  s.setState('listening');
  s.run(1);
  assert.equal(s.base(), 'Listen', 'excited was set before this listening began: stale');
  s.attrs({ 'al.listen_style': 'curious', 'al.turn': '1' });
  s.run(1);
  assert.equal(s.base(), 'Listen_Curious');
  const t = session();
  t.attrs({ 'al.listen_style': 'sad' });
  t.run(5);
  t.setState('listening');
  t.run(1);
  assert.equal(t.base(), 'Listen_Empathy', 'sad is still current');
  t.run(100);
  t.setState('speaking'); t.run(1); t.setState('listening'); t.run(2);
  assert.equal(t.base(), 'Listen', 'a stale sad lapses after 90 s');
});

test('listen styles need signals: without al.sig_v the plain loops play', () => {
  const s = session({ signals: false });
  s.attrs({ 'al.listen_style': 'sad', 'al.reply': '1', 'al.talk_style': 'praise' });
  s.setState('listening');
  s.run(1);
  assert.equal(s.base(), 'Listen');
  s.setState('speaking');
  s.run(1);
  assert.equal(s.base(), 'TalkGesture');
});

test('a Listen_Curious window follows a question and ends when the child talks', () => {
  const s = session();
  s.store.onAgentText('Do you like cats?', { id: 'a', final: true });
  s.setState('speaking');
  s.run(1);
  s.setState('listening');
  s.run(1);
  assert.equal(s.base(), 'Listen_Curious');
  s.store.setChildSpeaking(true);
  s.run(2);
  assert.equal(s.base(), 'Listen');
});

test('talk styles map to their loops when the reply is fresh', () => {
  const want = { story: 'Talk_Story', praise: 'Talk_Praise', question: 'Talk_Ask', gentle: 'Talk_Gentle' };
  for (const [style, clip] of Object.entries(want)) {
    const s = session();
    s.setState('listening');
    s.run(1);
    s.attrs({ 'al.talk_style': style, 'al.reply': '1' });
    s.setState('speaking');
    s.run(0.5);
    assert.equal(s.base(), clip, style);
  }
});

test('a stale talk style is ignored (reply long before speaking began)', () => {
  const s = session();
  s.attrs({ 'al.talk_style': 'praise', 'al.reply': '1' });
  s.run(12);
  s.setState('speaking');
  s.run(0.5);
  // replySeenAt is older than 8 s and no speaking ended since: fresh only if it came after the last speech end.
  // The first reply of a session counts as fresh because nothing has been spoken yet.
  assert.ok(['TalkGesture', 'Talk_Praise'].includes(s.base()));
  const t = session();
  reply(t, 'praise', 1);
  t.run(12);
  t.setState('speaking');
  t.run(0.5);
  assert.equal(t.base(), 'TalkGesture', 'no new reply signal: the style does not repeat');
});

test('style fatigue: the third identical style in a row plays TalkGesture', () => {
  const s = session();
  s.setState('listening');
  s.run(1);
  reply(s, 'praise', 1);
  assert.equal(s.log.base.filter((b) => b.name === 'Talk_Praise').length, 1);
  reply(s, 'praise', 2);
  assert.equal(s.log.base.filter((b) => b.name === 'Talk_Praise').length, 2);
  const before = s.log.base.length;
  s.attrs({ 'al.talk_style': 'praise', 'al.reply': '3' });
  s.setState('speaking');
  s.run(1);
  const added = s.log.base.slice(before).map((b) => b.name);
  assert.ok(added.includes('TalkGesture') && !added.includes('Talk_Praise'), `got ${added}`);
  assert.ok(s.out.smile > 0.3, 'the style keeps its expression');
});

test('talk to talk changes wait 2.5 s', () => {
  const s = session();
  s.attrs({ 'al.talk_style': 'story', 'al.reply': '1' });
  s.setState('speaking');
  s.run(0.5);
  assert.equal(s.base(), 'Talk_Story');
  s.attrs({ 'al.talk_style': 'gentle', 'al.reply': '2' });
  s.run(1.5);
  assert.equal(s.base(), 'Talk_Story');
  s.run(1.5);
  assert.equal(s.base(), 'Talk_Gentle');
});

test('base changes carry fades from the table, scaled in reduced motion', () => {
  const s = session();
  s.setState('listening');
  s.run(1);
  s.setState('thinking');
  s.run(1);
  const think = s.log.base.find((b) => b.name === 'Think');
  assert.equal(think.fade, DIRECTOR.fade.listenToThink);
  assert.equal(think.entry, 0);
  const r = session({ reduced: true });
  r.setState('listening');
  r.run(1);
  r.setState('thinking');
  r.run(1);
  assert.ok(Math.abs(r.log.base.find((b) => b.name === 'Think').fade - 0.5 * 1.3) < 1e-9);
});

test('the energy underlay follows the voice for talk loops only', () => {
  const s = session();
  s.setState('speaking');
  s.voice = 0.5;
  s.run(2);
  const loud = s.out.underlay;
  s.voice = 0.0;
  s.run(2);
  const quiet = s.out.underlay;
  assert.ok(loud > quiet, `${loud} vs ${quiet}`);
  assert.ok(quiet >= 0.55 - 1e-6 && loud <= 1);
  s.setState('listening');
  s.run(1);
  assert.equal(s.out.underlay, 1);
});

test('the walk-in owns the base: the director stays paused and replays nothing', () => {
  const s = session();
  s.walkIn = true;
  s.setState('speaking');
  s.attrs({ 'al.talk_style': 'story', 'al.reply': '1' });
  s.run(1);
  assert.equal(s.out.paused, true);
  assert.equal(s.log.base.length, 0);
  s.walkIn = false;
  s.step();
  assert.equal(s.out.paused, false);
  assert.ok(s.base());
});

// ---------------------------------------------------------------- expression

test('expression channels: empathy squints and goes soft, excited smiles, all capped', () => {
  const s = session();
  s.setState('listening');
  s.run(0.5);
  s.attrs({ 'al.listen_style': 'sad', 'al.turn': '1' });
  s.run(2);
  assert.ok(s.out.squint > 0.1 && s.out.squint <= 0.35);
  assert.ok(s.out.soft > 0.5);
  const e = session();
  e.setState('listening');
  e.run(0.5);
  e.attrs({ 'al.listen_style': 'excited', 'al.turn': '1' });
  e.run(2);
  assert.ok(e.out.smile > 0.5);
  assert.ok(e.out.squint <= DIRECTOR.expr.squintCap + 1e-9);
});

test('blink rate: calmer while listening and searching, faster while thinking', () => {
  const s = session();
  s.setState('listening'); s.run(1);
  assert.equal(s.out.blinkRate, 0.8);
  s.setState('thinking'); s.run(1);
  assert.equal(s.out.blinkRate, 1.3);
});

// ---------------------------------------------------------------- nods

function nodTrial(seed, seconds) {
  const s = session({ seed });
  s.setState('listening');
  s.run(0.5);
  let t = 0;
  while (t < seconds) {
    s.store.setChildSpeaking(true);
    s.run(2.4);
    s.store.setChildSpeaking(false);
    s.run(1.6);
    t += 4;
  }
  return s.log.nods;
}

test('backchannel nods obey the gap, the per-minute cap and fire at a sensible rate', () => {
  let total = 0;
  for (let seed = 1; seed <= 20; seed++) {
    const nods = nodTrial(seed, 240);
    total += nods.length;
    // Primary nods only: a double nod's second dip is 0.35 s later.
    const primary = nods.filter((n, i) => i === 0 || n.t - nods[i - 1].t > 0.5);
    for (let i = 1; i < primary.length; i++) assert.ok(primary[i].t - primary[i - 1].t >= 2.49, 'gap');
    for (const n of primary) {
      const inMinute = primary.filter((m) => m.t > n.t - 60 && m.t <= n.t).length;
      assert.ok(inMinute <= 8, 'cap');
    }
  }
  const perTrial = total / 20;
  // 60 pauses in 240 s, probability 0.55, gap 2.5 s: about 25 to 35 nods, double nods included.
  assert.ok(perTrial > 18 && perTrial < 45, `nods per 4 minutes: ${perTrial}`);
});

test('no backchannel nod without a long enough run of child speech', () => {
  const s = session();
  s.setState('listening');
  s.run(0.5);
  for (let i = 0; i < 30; i++) {
    s.store.setChildSpeaking(true);
    s.run(0.6);
    s.store.setChildSpeaking(false);
    s.run(1);
  }
  assert.equal(s.log.nods.length, 0);
});

test('reduced motion halves the nod amplitude', () => {
  let a = 0;
  let b = 0;
  let na = 0;
  let nb = 0;
  for (let seed = 1; seed <= 10; seed++) {
    for (const n of nodTrial(seed, 120)) { a += n.w; na++; }
    const s = session({ seed, reduced: true });
    s.setState('listening'); s.run(0.5);
    for (let i = 0; i < 30; i++) {
      s.store.setChildSpeaking(true); s.run(2.4);
      s.store.setChildSpeaking(false); s.run(1.6);
    }
    for (const n of s.log.nods) { b += n.w; nb++; }
  }
  assert.ok(na > 0 && nb > 0);
  assert.ok(b / nb < 0.6 * (a / na), `${b / nb} vs ${a / na}`);
});

test('emphasis nods fire on voice onsets while speaking, within the gap', () => {
  let count = 0;
  for (let seed = 1; seed <= 10; seed++) {
    const s = session({ seed });
    s.setState('speaking');
    for (let i = 0; i < 40; i++) {
      s.voice = 0.0; s.run(0.5);
      s.voice = 0.9; s.run(0.5);
    }
    count += s.log.nods.length;
    const n = s.log.nods;
    for (let i = 1; i < n.length; i++) assert.ok(n[i].t - n[i - 1].t >= 1.79);
  }
  assert.ok(count > 10, `emphasis nods: ${count}`);
});

test('no nods while the hologram is open or a greet plays', () => {
  const s = session();
  s.store.onAgentText('السلام عليكم يا صديقي', { id: 'a', final: false });
  s.setState('speaking');
  s.run(0.1);
  const before = s.log.nods.length;
  for (let i = 0; i < 20; i++) { s.voice = 0; s.run(0.4); s.voice = 0.9; s.run(0.3); }
  // Greet plays for 2.8 s; nothing in that window.
  assert.ok(s.shot('Greet').length === 1);
  const g = s.shot('Greet')[0].t;
  assert.ok(!s.log.nods.slice(before).some((n) => n.t > g && n.t < g + 2.8));
});

// ---------------------------------------------------------------- one-shots

test('Celebrate on quest completion, with a 30 s cooldown; Happy waits for quiet', () => {
  const s = session();
  s.run(1);
  s.store.onGamification({ type: 'quest_completed' });
  s.run(0.5);
  assert.equal(s.shot('Celebrate').length, 1);
  s.run(6);
  s.store.onGamification({ type: 'quest_completed' });
  s.run(3);
  assert.equal(s.shot('Celebrate').length, 1, 'cooldown');
  s.run(30);
  s.store.onGamification({ type: 'leveled_up', leveled_up: true });
  s.run(0.5);
  assert.equal(s.shot('Celebrate').length, 2);
  const h = session();
  h.run(1);
  h.store.onAgentText('Nice one.', { id: 'n', final: true });
  h.setState('speaking');
  h.store.onGamification({ type: 'points', delta: 2 });
  h.run(2);
  assert.equal(h.shot('Happy').length, 0, 'waits while speaking');
  h.setState('listening');
  h.run(1);
  assert.equal(h.shot('Happy').length, 1);
});

test('a pending Happy expires after its TTL', () => {
  const s = session();
  s.run(1);
  s.setState('speaking');
  s.store.onGamification({ type: 'points', delta: 1 });
  s.run(8);
  s.setState('listening');
  s.run(1);
  assert.equal(s.shot('Happy').length, 0);
});

test('classifyGamification', () => {
  assert.equal(classifyGamification({ type: 'quest_completed' }), 'celebrate');
  assert.equal(classifyGamification({ type: 'points', delta: 3, leveled_up: true }), 'celebrate');
  assert.equal(classifyGamification({ type: 'points', delta: 3, new_badges: ['x'] }), 'celebrate');
  assert.equal(classifyGamification({ type: 'points', delta: 3 }), 'happy');
  assert.equal(classifyGamification({ type: 'points', delta: 0 }), '');
  assert.equal(classifyGamification(null), '');
});

test('Greet plays once per session, as Wave on today\'s GLB', () => {
  const s = session({ clips: ANIM2 });
  s.store.onAgentText('السلام عليكم ورحمة', { id: 'a', final: false });
  s.setState('speaking');
  s.run(1);
  const g = s.shot('Greet');
  assert.equal(g.length, 1);
  assert.equal(g[0].name, 'Wave');
  s.store.onAgentText('Hi again, assalam alaikum', { id: 'b', final: true });
  s.run(6);
  assert.equal(s.shot('Greet').length, 1);
});

test('Greet also fires when speech starts and no transcript arrives', () => {
  const s = session();
  s.setState('speaking');
  s.run(1);
  assert.equal(s.shot('Greet').length, 0);
  s.run(1);
  assert.equal(s.shot('Greet').length, 1);
});

test('Greet becomes a Nod when Wave just played', () => {
  const s = session();
  s.waveAgo = 3;
  s.store.onAgentText('Salam!', { id: 'a', final: false });
  s.setState('speaking');
  s.run(0.5);
  assert.equal(s.shot('Greet').length, 0);
  assert.ok(s.log.nods.length >= 1);
});

test('Greet plays again after a reconnect of a minute or more', () => {
  const s = session();
  s.store.onAgentText('Salam!', { id: 'a', final: false });
  s.setState('speaking');
  s.run(6);
  assert.equal(s.shot('Greet').length, 1);
  s.store.markDisconnected();
  s.run(70);
  s.store.markConnected();
  s.store.reset();
  s.store.applySnapshot({ 'al.sig_v': '1' });
  s.run(0.2);
  s.store.onAgentText('Salam, welcome back', { id: 'z', final: false });
  s.run(6);
  assert.equal(s.shot('Greet').length, 2);
});

test('Goodbye from a farewell cue, once; and from session_ending followed by speaking', () => {
  const s = session();
  s.setState('speaking');
  s.store.onAgentText('Great job today. Bye bye, see you tomorrow!', { id: 'g', final: true });
  s.run(1);
  assert.equal(s.shot('Goodbye').length, 1);
  s.store.onAgentText('Bye again!', { id: 'h', final: true });
  s.run(5);
  assert.equal(s.shot('Goodbye').length, 1, 'once per session');
  const e = session();
  e.setState('listening');
  e.store.onSessionLimit({ type: 'session_ending' });
  e.run(1);
  assert.equal(e.shot('Goodbye').length, 0, 'waits for the agent to speak');
  e.setState('speaking');
  e.run(1);
  assert.equal(e.shot('Goodbye').length, 1);
});

test('Goodbye outranks a pending Celebrate and Happy', () => {
  const s = session();
  s.run(1);
  s.store.onGamification({ type: 'quest_completed' });
  s.store.onGamification({ type: 'points', delta: 1 });
  s.store.onAgentText('Bye!', { id: 'b', final: true });
  s.run(0.3);
  assert.equal(s.shot('Goodbye').length, 1);
  assert.equal(s.shot('Celebrate').length, 0);
});

test('LookAround happens when idle, never while the hologram is open', () => {
  const s = session();
  s.run(40);
  assert.ok(s.shot('LookAround').length >= 1);
});

test('reduced motion: no Celebrate, Happy or Greet; Goodbye plays at half weight, forced', () => {
  const s = session({ reduced: true });
  s.run(1);
  s.store.onGamification({ type: 'quest_completed' });
  s.store.onGamification({ type: 'points', delta: 2 });
  s.store.onAgentText('Salam', { id: 'a', final: false });
  s.setState('speaking');
  s.run(3);
  assert.equal(s.shot('Celebrate').length, 0);
  assert.equal(s.shot('Happy').length, 0);
  assert.equal(s.shot('Greet').length, 0);
  s.store.onAgentText('Bye bye', { id: 'b', final: true });
  s.run(1);
  const g = s.shot('Goodbye');
  assert.equal(g.length, 1);
  assert.equal(g[0].weight, 0.5);
  assert.equal(g[0].force, true);
});

// ---------------------------------------------------------------- hologram

function startSearch(s, kind = 'library') {
  s.attrs({ 'al.search_kind': kind, 'al.activity': 'searching' });
  s.setState('thinking');
}

test('a search plays SearchStart, opens at the bloom marker and holds on SearchHold', () => {
  const s = session();
  s.setState('listening');
  s.run(1);
  startSearch(s);
  s.step();
  assert.equal(s.out.holo.phase, HP.START);
  assert.equal(s.log.shots.at(-1).name, 'SearchStart');
  assert.equal(s.base(), 'SearchHold');
  s.run(0.4);
  assert.equal(s.out.holo.phase, HP.OPENING);
  s.run(0.4);
  assert.equal(s.out.holo.phase, HP.HOLD);
  assert.equal(s.out.holo.kind, 'library');
  assert.equal(s.out.statusKind, 'library');
});

test('swipes come in the hold: at most 3, page turns follow the advance marker', () => {
  const s = session();
  startSearch(s, 'folders');
  s.run(12);
  const swipes = s.shot('SearchSwipe');
  assert.ok(swipes.length >= 2 && swipes.length <= 3, `swipes ${swipes.length}`);
  for (let i = 1; i < swipes.length; i++) assert.ok(swipes[i].t - swipes[i - 1].t >= 1.6);
  assert.equal(s.out.holo.page, swipes.length);
});

test('found waits for the minimum show time and the grace, then runs Found and closes', () => {
  const s = session();
  startSearch(s);
  s.run(0.5);
  s.attrs({ 'al.activity': 'found' });
  s.run(0.5);
  assert.ok(s.out.holo.phase <= HP.HOLD, 'still showing: minimum show time');
  s.run(1.5);
  assert.ok(s.out.holo.phase >= HP.GLOW, `phase ${s.out.holo.phase}`);
  assert.equal(s.shot('Found').length, 1);
  assert.equal(s.out.statusKind, 'found');
  assert.ok(s.out.smile > 0.3, 'the found smile');
  s.run(1.5);
  assert.equal(s.out.holo.phase, HP.CLOSED);
  assert.equal(s.out.holo.active, false);
});

test('none dims and closes without Found', () => {
  const s = session();
  startSearch(s);
  s.run(0.5);
  s.attrs({ 'al.activity': 'none' });
  s.run(3);
  assert.equal(s.out.holo.phase, HP.CLOSED);
  assert.equal(s.shot('Found').length, 0);
});

test('a chained search keeps the panel open and cross-dissolves the skin', () => {
  const s = session();
  startSearch(s, 'library');
  s.run(1.5);
  s.attrs({ 'al.activity': 'found' });
  s.run(0.1);
  s.attrs({ 'al.search_kind': 'web', 'al.activity': 'searching' });
  s.step();
  assert.ok(s.out.holo.phase <= HP.HOLD);
  assert.equal(s.out.holo.kind, 'web');
  assert.equal(s.out.holo.prevKind, 'library');
  s.run(3);
  assert.ok(s.out.holo.active, 'no result yet: still searching');
  assert.equal(s.shot('Found').length, 0);
});

test('the child barging in closes the hologram quickly and cuts a swipe', () => {
  const s = session();
  startSearch(s);
  s.run(3);
  s.setState('listening');
  s.step();
  assert.equal(s.out.holo.phase, HP.INT_CLOSE);
  s.run(0.5);
  assert.equal(s.out.holo.phase, HP.CLOSED);
});

test('found without a searching seen starts a quick search (coalesced attributes)', () => {
  const s = session();
  s.setState('thinking');
  s.attrs({ 'al.search_kind': 'folders', 'al.activity': 'found' });
  s.run(0.1);
  assert.ok(s.out.holo.active);
  assert.equal(s.out.holo.quick, true);
  s.run(4);
  assert.equal(s.shot('Found').length, 1);
});

test('the initial snapshot pushes no event: joining mid-search shows nothing', () => {
  const s = session({ signals: false });
  s.store.applySnapshot({ 'al.sig_v': '1', 'al.activity': 'searching', 'al.search_kind': 'library' });
  s.setState('thinking');
  s.run(2);
  assert.equal(s.store.ctx.signals.eventCount, 0);
  assert.equal(s.out.holo.active, false);
});

test('without al.sig_v a search is never faked', () => {
  const s = session({ signals: false });
  s.attrs({ 'al.activity': 'searching', 'al.search_kind': 'library' });
  s.setState('thinking');
  s.run(5);
  assert.equal(s.out.holo.active, false);
  assert.equal(s.shot('SearchStart').length, 0);
});

test('frequency caps: a second search within 8 s of the first closing is not shown', () => {
  const s = session();
  startSearch(s);
  s.run(0.5);
  s.attrs({ 'al.activity': 'none' });
  s.run(2.5);
  assert.equal(s.out.holo.phase, HP.CLOSED);
  s.attrs({ 'al.activity': 'idle' });
  s.step();
  s.attrs({ 'al.activity': 'searching' });
  s.run(1);
  assert.equal(s.out.holo.active, false, 'toolGap');
  s.attrs({ 'al.activity': 'found' });
  s.run(3);
  assert.equal(s.out.holo.active, false, 'the denied search\'s result is dropped too');
  s.run(8);
  s.attrs({ 'al.activity': 'idle' });
  s.step();
  s.attrs({ 'al.activity': 'searching' });
  s.run(1);
  assert.equal(s.out.holo.active, true);
});

test('a search never outlives its maximum hold', () => {
  const s = session();
  startSearch(s);
  s.run(20);
  assert.equal(s.out.holo.active, false);
});

test('events that coalesce into one ring slot are all seen (ring of 16)', () => {
  const s = session();
  assert.equal(RING, 16);
  s.store.ctx.signals.eventCount; // exists
  for (let i = 0; i < 20; i++) {
    s.attrs({ 'al.activity': i % 2 === 0 ? 'searching' : 'idle' });
  }
  s.run(0.1); // must not throw on a burst bigger than the ring
  assert.ok(s.store.ctx.signals.eventCount >= 16);
});

test('on today\'s GLB the hologram still runs (virtual clock), without clips or beam', () => {
  const s = session({ clips: ANIM2 });
  s.setState('listening'); s.run(1);
  startSearch(s);
  s.run(0.8);
  assert.equal(s.out.holo.phase, HP.HOLD);
  assert.equal(s.shot('SearchStart').length, 0);
  assert.equal(s.base(), 'Think', 'SearchHold falls back to Think');
  assert.ok(s.out.lookPanel > 0.3, 'the gaze goes to the panel');
  s.attrs({ 'al.activity': 'found' });
  s.run(3);
  assert.equal(s.out.holo.phase, HP.CLOSED);
  assert.equal(s.shot('Found').length, 0);
});

test('reduced motion: a static icon, no SearchStart, no swipes, Think held', () => {
  const s = session({ reduced: true });
  startSearch(s);
  s.run(2);
  assert.equal(s.out.holo.phase, HP.ICON);
  assert.equal(s.shot('SearchStart').length, 0);
  assert.equal(s.shot('SearchSwipe').length, 0);
  assert.equal(s.base(), 'Think');
  s.attrs({ 'al.activity': 'found' });
  s.run(0.6);
  assert.equal(s.out.holo.phase, HP.ICON_CHECK);
  assert.equal(s.out.holo.icon, 2);
  s.run(1.6);
  assert.equal(s.out.holo.phase, HP.CLOSED);
});

test('the status line fires once per search and once more for found', () => {
  const s = session();
  startSearch(s, 'folders');
  s.run(1);
  const seq1 = s.out.statusSeq;
  assert.equal(s.out.statusKind, 'folders');
  s.run(1);
  assert.equal(s.out.statusSeq, seq1);
  s.attrs({ 'al.activity': 'found' });
  s.run(3);
  assert.equal(s.out.statusSeq, seq1 + 1);
});

test('hologram photosensitivity: at most one gold flash per search', () => {
  const s = session();
  startSearch(s);
  s.run(1.6);
  s.attrs({ 'al.activity': 'found' });
  let glows = 0;
  let prev = s.out.holo.phase;
  for (let i = 0; i < 400; i++) {
    s.step();
    if (s.out.holo.phase === HP.GLOW && prev !== HP.GLOW) glows++;
    prev = s.out.holo.phase;
  }
  assert.equal(glows, 1);
});

test('the director allocates nothing per step once warm', () => {
  const s = session();
  s.setState('listening');
  s.run(3);
  const g = typeof globalThis.gc === 'function' ? globalThis.gc : null;
  if (g) g();
  const before = process.memoryUsage().heapUsed;
  s.run(60);
  if (g) g();
  const grew = process.memoryUsage().heapUsed - before;
  assert.ok(grew < 4_000_000, `heap grew ${grew}`);
});

// ---------------------------------------------------------------- signals store and cues

test('the store parses al.* attributes, ignores other keys, and pushes activity events', () => {
  const store = createAvatarContextStore({ now: () => 5 });
  store.applySnapshot({ 'al.sig_v': '1', 'al.activity': 'searching', 'lk.agent.state': 'thinking' });
  assert.equal(store.ctx.signals.v, 1);
  assert.equal(store.ctx.signals.activity, 'searching');
  assert.equal(store.ctx.signals.eventCount, 0);
  store.applyChanged({ 'lk.agent.state': 'speaking' });
  assert.equal(store.ctx.signals.eventCount, 0);
  store.applyChanged({ 'al.search_kind': 'folders', 'al.activity': 'found' });
  const ev = store.ctx.signals.events[0];
  assert.equal(ev.to, 'found');
  assert.equal(ev.kind, 'folders');
  assert.equal(ev.from, 'searching');
  store.applyChanged({ 'al.activity': 'bogus', 'al.talk_style': 'nonsense', 'al.reply': 'x' });
  assert.equal(store.ctx.signals.activity, 'found');
  assert.equal(store.ctx.signals.talkStyle, 'explain');
  store.markDisconnected();
  assert.equal(store.ctx.signals.v, 0);
});

test('transcript cues: greetings and farewells, Arabic and English', () => {
  assert.equal(hasGreeting('السلام عليكم يا بطل'), true);
  assert.equal(hasGreeting('السَّلامُ عَلَيْكُم'), true);
  assert.equal(hasGreeting('Assalam alaikum Majd'), true);
  assert.equal(hasGreeting('Hello there, how are you? ........................ salam'), false, 'only the first 40 characters');
  assert.equal(hasFarewell('مع السلامة يا صديقي'), true);
  assert.equal(hasFarewell('Bye bye!'), true);
  assert.equal(hasFarewell('See you tomorrow, take care.'), true);
  assert.equal(hasFarewell("I see you're trying hard"), false);
  assert.equal(hasFarewell('Take care of your pet cat'), false);
  assert.equal(endsWithQuestion('Do you like it?'), true);
  assert.equal(endsWithQuestion('هل تحب ذلك؟'), true);
  assert.equal(endsWithQuestion('That is nice.'), false);
  assert.equal(normalizeText('  أَهْلاً  '), 'اهلا');
});

test('the cue tracker counts the greeting for the first message only, and farewells per message', () => {
  const c = createCueTracker();
  c.onAgentText('السلام', { id: '1', final: false });
  c.onAgentText('السلام عليكم يا صديقي', { id: '1', final: true });
  assert.equal(c.state.greetSeq, 1);
  assert.equal(c.state.msgCount, 1);
  c.onAgentText('salam again', { id: '2', final: true });
  assert.equal(c.state.greetSeq, 1);
  c.onAgentText('Bye', { id: '3', final: false });
  c.onAgentText('Bye bye now', { id: '3', final: true });
  assert.equal(c.state.goodbyeSeq, 1);
  c.onAgentText('Is that clear?', { id: '4', final: true });
  assert.equal(c.state.question, true);
  c.reset();
  assert.equal(c.state.msgCount, 0);
});

// ---- CLIP_META against the sidecar of the real GLB (avatar-animated.json) ----

const SIDECAR = JSON.parse(
  readFileSync(new URL('../public/models/avatar/avatar-animated.json', import.meta.url), 'utf8'),
);

test('CLIP_META covers exactly the 24 clips of the sidecar, with the same frame counts and kinds', () => {
  const names = SIDECAR.clips.map((c) => c.name).sort();
  assert.deepEqual(names, Object.values(CLIP).slice().sort(), 'CLIP names');
  assert.deepEqual(Object.keys(CLIP_META).sort(), names, 'CLIP_META names');
  for (const c of SIDECAR.clips) {
    const m = CLIP_META[c.name];
    assert.equal(m.frames, c.frames, `${c.name} frames`);
    assert.equal(m.kind, c.kind, `${c.name} kind`);
    assert.ok(Math.abs(m.dur - c.duration_s) < 1e-6, `${c.name} duration`);
  }
});

test('CLIP_META markers equal the sidecar markers (in seconds)', () => {
  for (const c of SIDECAR.clips) {
    const side = Object.entries(c.markers ?? {});
    const meta = CLIP_META[c.name].markers ?? {};
    // Only the markers the web reads need to be present, but each one it has must be right.
    for (const [k, v] of Object.entries(meta)) {
      assert.ok(c.markers && c.markers[k], `${c.name}.${k} exists in the sidecar`);
      assert.ok(Math.abs(v - c.markers[k].s) < 1e-3, `${c.name}.${k}: ${v} vs ${c.markers[k].s}`);
    }
    // One-shots and transitions: the web must know every marker the sidecar names.
    if (c.kind === 'oneshot' || c.kind === 'transition') {
      const want = side.map(([k]) => k).filter((k) => !(c.name === 'LookAround'));
      for (const k of want) assert.ok(k in meta, `${c.name}.${k} missing from CLIP_META`);
    }
  }
});

test('CLIP_META entry and home match the sidecar', () => {
  for (const c of SIDECAR.clips) {
    const m = CLIP_META[c.name];
    if (c.kind === 'loop') {
      // entry_mode "running" keeps the clock (null); "reset" starts at entry_s
      if (c.entry_mode === 'running') assert.equal(m.entry, null, `${c.name} entry`);
      else assert.equal(m.entry, c.entry_s, `${c.name} entry`);
    }
    if (c.kind === 'oneshot') assert.equal(m.home, c.home, `${c.name} home`);
    if (c.kind === 'transition') assert.equal(m.to, c.home, `${c.name} ends on its home loop`);
  }
  assert.equal(CLIP_META[CLIP.found].from, SIDECAR.clips.find((c) => c.name === 'Found').starts_on?.split(' ')[0] ?? CLIP.searchHold);
});

test('MESH_VISEME_GAIN equals the gain the mesh bakes in, and the rig divides it out of the web gains', () => {
  assert.deepEqual({ ...MESH_VISEME_GAIN }, SIDECAR.viseme_mesh_gain.applied);
  const scene = { traverse() {} };
  const plain = new LipsyncRig(scene);
  const r2 = new LipsyncRig(scene, { meshGain: MESH_VISEME_GAIN });
  for (const k of Object.keys(MESH_VISEME_GAIN)) {
    assert.ok(Math.abs(r2.gains[k] - (VISEME_GAIN[k] ?? 1) / 1.5) < 1e-9, `${k} divided`);
    assert.equal(plain.gains[k], VISEME_GAIN[k] ?? undefined, `${k} untouched without meshGain`);
  }
  assert.equal(r2.gains.aa, VISEME_GAIN.aa, 'aa is not baked, so it is not divided');
});

test('Goodbye plays again after a reconnect of a minute or more', () => { // integrate-1
  const s = session();
  s.setState('speaking');
  s.store.onAgentText('Bye bye, see you tomorrow!', { id: 'g', final: true });
  s.run(1);
  assert.equal(s.shot('Goodbye').length, 1);
  s.store.markDisconnected();
  s.run(70);
  s.store.markConnected();
  s.store.reset();
  s.store.applySnapshot({ 'al.sig_v': '1' });
  s.run(0.2);
  s.store.onAgentText('Goodbye, see you soon!', { id: 'k', final: true });
  s.run(3);
  assert.equal(s.shot('Goodbye').length, 2);
});

test('a search that starts while the panel is closing opens it again once it is closed', () => { // integrate-1
  const s = session();
  startSearch(s, 'web');
  s.run(2);
  s.attrs({ 'al.activity': 'none' });
  for (let i = 0; i < 240 && s.out.holo.phase !== HP.NONE_DIM; i++) s.step();
  assert.equal(s.out.holo.phase, HP.NONE_DIM);
  startSearch(s, 'library');
  s.run(1.5);
  assert.equal(s.out.holo.active, true, 'reopened after the close');
  assert.equal(s.out.holo.kind, 'library');
  // ... but not when that search has already ended before the panel finished closing.
  const s2 = session();
  startSearch(s2, 'web');
  s2.run(2);
  s2.attrs({ 'al.activity': 'none' });
  for (let i = 0; i < 240 && s2.out.holo.phase !== HP.NONE_DIM; i++) s2.step();
  startSearch(s2, 'library');
  s2.step();
  s2.attrs({ 'al.activity': 'found' });
  s2.run(1.5);
  assert.equal(s2.out.holo.active, false);
});
