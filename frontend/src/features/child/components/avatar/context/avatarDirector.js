// The context director (SPEC-EXPERIENCE section 5): decides, every frame, which base loop plays,
// which one-shots and nods fire, the expression, the hologram phase and the gaze target.
// Pure JS: no three.js, no DOM, and nothing is allocated per step. ClipAvatar applies the output.
//
//   const director = createDirector({ rng, has });   // has(name): does the GLB carry this clip?
//   director.step(dt, input, out);                   // out = makeDirectorOutput(), reused
//
// All numbers live in avatarConfig.js (DIRECTOR, CLIP_META, FALLBACK).

import { CLIP, CLIP_META, DIRECTOR, resolveClip } from '../avatarConfig.js';
import { createHoloTimeline, HP } from './holoTimeline.js';
import { createNodder } from './nodRules.js';
import { createShotQueue } from './shotQueue.js';

const D = DIRECTOR;
const between = (range, rng) => range[0] + rng() * (range[1] - range[0]);
const clamp01 = (x) => (x < 0 ? 0 : x > 1 ? 1 : x);

const isTalk = (n) => n === CLIP.talk || n.startsWith('Talk_');
const isListen = (n) => n === CLIP.listen || n.startsWith('Listen_');

const TALK_BY_STYLE = {
  explain: CLIP.talk,
  story: CLIP.talkStory,
  praise: CLIP.talkPraise,
  question: CLIP.talkAsk,
  gentle: CLIP.talkGentle,
};
const SEARCH_SHOTS = { SearchStart: 1, SearchSwipe: 1, Found: 1 };
const BLOCKS_HOLO = { Greet: 1, Goodbye: 1, Celebrate: 1 };

export function makeDirectorOutput() {
  return {
    paused: false, // the walk-in owns the base; nothing below applies
    // base loop
    base: '', // the clip to be the base (a name the GLB has), only meaningful when baseChanged
    baseChanged: false,
    baseFade: 0.4,
    baseEntry: -1, // seconds, -1 keeps the running clock
    baseScale: 1,
    underlay: 1, // how much of the base shows against Idle (the talk energy underlay)
    // one-shot (this frame only)
    oneShot: '', // clip to play ('' none)
    oneShotLogical: '', // the director's name for it (it may be a substitute clip)
    oneShotFade: 0, // 0: the animator's default
    oneShotForce: false,
    oneShotWeight: 1,
    interrupt: 0, // >0: cut the playing one-shot with this fade, this frame
    // additive nod (this frame only)
    nod: 0, // weight, 0 none
    nodScale: 1,
    // code-owned expression layer (damped)
    squint: 0,
    smile: 0,
    soft: 0,
    ooh: 0,
    blinkRate: 1,
    blinkNow: false,
    // the hologram
    holo: null, // the timeline's output object (set by the director)
    lookPanel: 0, // 0..1 how much the gaze aims at the panel
    statusSeq: 0,
    statusKind: '',
    // for the dev overlay and tests
    logicalBase: '',
    talkStyle: 'explain',
    shotPlaying: '',
  };
}

/**
 * @param {{rng?: () => number, has?: (name: string) => boolean, meta?: object}} [opts]
 */
export function createDirector({ rng = Math.random, has = () => true, meta = CLIP_META } = {}) {
  const R = (name) => resolveClip(name, has);
  const queue = createShotQueue(D.shots);
  const nodder = createNodder({ rng, cfg: D.nod });
  const holoTl = createHoloTimeline({ rng, cfg: D.holo });
  const take = { cut: false };
  const takeEnv = { speaking: false, holoActive: false }; // reused: no object literal per step
  const holoEnv = { state: 'idle', reduced: false, visible: true, blocked: false, swipePlaying: false };
  const nodEnv = {
    childSpeaking: false, listening: false, speaking: false, blocked: false,
    mood: '', talkStyle: 'explain', voice: -1, reduced: false,
  };

  // All the numbers that change every step live in one object: a closure variable that holds a double
  // is boxed again on each assignment, an object field is updated in place (no steady allocation).
  const S = {
    t: 0,
    stateT: 0,
    lastSpeakEnd: 0,
    cycleStart: 0,
    firstSpeakAt: -1,
    replySeenAt: -999,
    listenSeenAt: -999,
    expectUntil: -1,
    childSpeechInListen: 0,
    baseSince: 0,
    peak: 0.05,
    energy: 0.7,
    curShotStart: 0,
    lookTimer: between(D.shots.lookAroundFirst, rng),
    lookCooldown: 0,
    silentT: 0,
    oohUntil: -1,
    gamSmileUntil: -1,
    greetNod: 0,
  };
  let started = false;
  let wasPaused = false;

  // agent state tracking
  let prevState = 'initializing';

  // signals baselines and freshness
  let seenEvent = 0;
  let seenReply = 0;
  let seenTurn = 0;
  let seenListen = 'neutral';
  let styleStreak = 0;
  let lastStyle = '';
  let fatigued = false;

  // cues, gamification
  let seenGreet = 0;
  let seenGoodbye = 0;
  let seenGam = 0;
  let seenEnding = 0;
  let seenConnect = 0;
  let greeted = false;
  let goodbyeDone = false;
  let endingPending = false;
  let wasQuestion = false;

  // base
  let curBase = ''; // the resolved clip the animator was told to play
  let curLogical = '';
  let prevHold = false;
  let holdFlip = false;
  let interruptBase = false;

  // energy

  // one-shot bookkeeping

  // expression state
  const ex = { squint: 0, smile: 0, soft: 0, ooh: 0, look: 0 };

  const damp = (cur, target, dt) => {
    const rate = target > cur ? D.expr.attack : D.expr.release;
    return cur + (target - cur) * (1 - Math.exp(-rate * dt));
  };

  function fadeFor(from, to, reduced) {
    const F = D.fade;
    let f = F.other;
    if (interruptBase) f = F.interruptToListen;
    else if (from === CLIP.searchHold || (from === CLIP.think && holdFlip)) f = F.holdToState;
    else if (to === CLIP.idle) f = F.toIdle;
    else if (isTalk(to)) f = isTalk(from) ? F.talkToTalk : F.toTalk;
    else if (isTalk(from) && isListen(to)) f = F.talkToListen;
    else if (isListen(from) && isListen(to)) f = F.listenToListen;
    else if (to === CLIP.think || from === CLIP.think) f = F.listenToThink;
    return reduced ? f * D.reducedFadeScale : f;
  }

  function wantBase(state, sig, live, reduced, holo, ctxIn) {
    if (holo.holdBase) return CLIP.searchHold;
    if (holo.thinkBase) return CLIP.think;
    const listenFresh = live && S.listenSeenAt >= S.cycleStart;
    const sad = live && sig.listenStyle === 'sad' && (listenFresh || S.t - S.listenSeenAt <= D.fresh.sadStale);
    switch (state) {
      case 'listening': {
        if (sad) return CLIP.listenEmpathy;
        if (listenFresh && sig.listenStyle === 'excited') return CLIP.listenExcited;
        if (listenFresh && sig.listenStyle === 'curious') return CLIP.listenCurious;
        if (S.t < S.expectUntil && S.childSpeechInListen < D.expectantChildSpeech) return CLIP.listenCurious;
        return CLIP.listen;
      }
      case 'thinking': {
        if (S.stateT < D.thinkHold) return curLogical || CLIP.idle;
        if (live && listenFresh && sig.listenStyle === 'sad') return CLIP.listenEmpathy;
        return CLIP.think;
      }
      case 'speaking': {
        const style = fatigued ? 'explain' : ctxIn.talkStyle;
        return TALK_BY_STYLE[style] ?? CLIP.talk;
      }
      default:
        return CLIP.idle;
    }
  }

  function startShot(logical, resolved, out, fadeIn, force, weight) {
    out.oneShot = resolved;
    out.oneShotLogical = logical;
    out.oneShotFade = fadeIn;
    out.oneShotForce = force;
    out.oneShotWeight = weight;
    S.curShotStart = S.t;
  }

  function metaOf(name) {
    return meta[name] ?? meta[CLIP.idle];
  }

  function step(dt, input, out) {
    const sig = input.signals;
    const cues = input.cues;
    const reduced = !!input.reduced;
    const state = input.agentState;
    const live = !!sig && sig.v === 1;
    S.t += dt;

    // Defaults for this frame's one-shot outputs.
    out.baseChanged = false;
    out.oneShot = '';
    out.oneShotLogical = '';
    out.oneShotFade = 0;
    out.oneShotForce = false;
    out.oneShotWeight = 1;
    out.interrupt = 0;
    out.nod = 0;
    out.nodScale = 1;
    out.blinkNow = false;
    out.holo = holoTl.out;
    holoTl.beginFrame();

    // First step: whatever is already true is not an event.
    if (!started) {
      started = true;
      if (sig) {
        seenEvent = sig.eventCount;
        seenReply = sig.reply;
        seenTurn = sig.turn;
        seenListen = sig.listenStyle;
      }
      if (cues) {
        seenGreet = cues.greetSeq;
        seenGoodbye = cues.goodbyeSeq;
        wasQuestion = cues.question;
      }
      if (input.gam) seenGam = input.gam.seq;
      seenEnding = input.sessionEndingSeq ?? 0;
      seenConnect = input.connectSeq ?? 0;
      prevState = state;
    }

    // ---- agent state bookkeeping
    if (state !== prevState) {
      if (prevState === 'speaking') S.lastSpeakEnd = S.t;
      if (state === 'speaking') {
        if (S.firstSpeakAt < 0) S.firstSpeakAt = S.t;
      }
      if (state === 'listening') {
        S.cycleStart = S.t;
        S.childSpeechInListen = 0;
        S.silentT = 0;
        if (cues && cues.question) S.expectUntil = S.t + D.expectantWindow;
      }
      S.stateT = 0;
      prevState = state;
    } else S.stateT += dt;
    if (state === 'listening') {
      if (input.childSpeaking) {
        S.childSpeechInListen += dt;
        S.silentT = 0;
      } else S.silentT += dt;
    }
    if (cues) {
      if (cues.question && !wasQuestion && state === 'listening') S.expectUntil = S.t + D.expectantWindow;
      wasQuestion = cues.question;
    }

    // ---- signals
    if (live) {
      if (sig.reply !== seenReply) {
        seenReply = sig.reply;
        S.replySeenAt = S.t;
        const style = sig.talkStyle;
        if (style !== 'explain' && style === lastStyle) styleStreak += 1;
        else styleStreak = 1;
        lastStyle = style;
        fatigued = style !== 'explain' && styleStreak >= D.fatigue;
      }
      if (sig.turn !== seenTurn) {
        seenTurn = sig.turn;
        S.listenSeenAt = S.t;
      }
      if (sig.listenStyle !== seenListen) {
        seenListen = sig.listenStyle;
        S.listenSeenAt = S.t;
      }
    } else {
      seenReply = sig ? sig.reply : 0;
      seenTurn = sig ? sig.turn : 0;
    }
    const talkFresh = live && S.replySeenAt > -999 && (S.replySeenAt >= S.lastSpeakEnd || S.t - S.replySeenAt <= D.fresh.talkWithin);
    const talkStyle = talkFresh ? sig.talkStyle : 'explain';
    out.talkStyle = talkStyle;

    // ---- walk-in: the walk-in owns the base. Keep reading events so none replay later.
    if (input.walkIn) {
      out.paused = true;
      wasPaused = true;
      if (sig) seenEvent = sig.eventCount;
      holoTl.reset();
      queue.reset();
      nodder.reset();
      if (cues) {
        seenGreet = cues.greetSeq;
        seenGoodbye = cues.goodbyeSeq;
      }
      if (input.gam) seenGam = input.gam.seq;
      out.underlay = 1;
      out.nod = 0;
      out.lookPanel = 0;
      return out;
    }
    if (wasPaused) {
      wasPaused = false;
      curBase = '';
      curLogical = '';
      S.baseSince = -999;
    }
    out.paused = false;

    queue.update(S.t);
    const playing = queue.playing(S.t);

    // ---- hologram timeline
    holoEnv.state = state;
    holoEnv.reduced = reduced;
    holoEnv.visible = input.visible !== false;
    holoEnv.blocked = BLOCKS_HOLO[playing] === 1;
    holoEnv.swipePlaying = false;
    // w3: the held web page's model (null when there is none): it decides flicks, the Found wait and the hero hold
    const web = input.web || null;
    holoEnv.webHas = !!web;
    holoEnv.webResults = !!web && web.state !== 'skeleton';
    holoEnv.webHero = !!web && web.hero === true;
    holoEnv.webScroll = !!web && web.state === 'results' && web.results.length >= 2;
    if (live && sig.eventCount > seenEvent) {
      let from = seenEvent;
      if (sig.eventCount - from > sig.events.length) from = sig.eventCount - sig.events.length;
      for (let i = from; i < sig.eventCount; i++) {
        const ev = sig.events[i % sig.events.length];
        if (ev) holoTl.onActivity(ev.to, ev.kind, S.t, holoEnv);
      }
    }
    if (sig) seenEvent = sig.eventCount;
    const holo = holoTl.step(dt, S.t, holoEnv);
    const hq = holoTl.q;
    if (hq.blink) out.blinkNow = true;
    if (hq.interruptShots && playing === 'search') {
      out.interrupt = D.fade.cut;
      queue.cut();
    }
    holdFlip = prevHold !== holo.holdBase;
    prevHold = holo.holdBase;
    interruptBase = holo.phase === HP.INT_CLOSE;

    // The search sequence is atomic and plays as the timeline asks.
    let searchStarted = false;
    if (hq.req !== '') {
      const logical = hq.req;
      const m = metaOf(logical);
      const resolved = R(logical);
      const cut = queue.playSearch(m.dur, S.t);
      if (cut) out.interrupt = D.fade.cut;
      if (resolved !== '') startShot(logical, resolved, out, m.fadeIn ?? 0, false, 1);
      searchStarted = true;
    }

    // ---- triggers for the other one-shots
    if (cues) {
      if (cues.greetSeq > seenGreet) {
        seenGreet = cues.greetSeq;
        greetCue(input, reduced, out);
      } else if (cues.greetSeq < seenGreet) seenGreet = cues.greetSeq;
      if (cues.goodbyeSeq > seenGoodbye) {
        seenGoodbye = cues.goodbyeSeq;
        goodbyeRequest(reduced);
      } else if (cues.goodbyeSeq < seenGoodbye) seenGoodbye = cues.goodbyeSeq;
    }
    if (input.connectSeq !== undefined && input.connectSeq !== seenConnect) {
      seenConnect = input.connectSeq;
      if ((input.awaySec ?? 0) >= D.greet.reconnectAway) {
        greeted = false;
        goodbyeDone = false; // integrate-1: a session back after a long break may say goodbye again
        S.firstSpeakAt = -1;
      }
    }
    if ((input.sessionEndingSeq ?? 0) > seenEnding) {
      seenEnding = input.sessionEndingSeq;
      endingPending = true;
    }
    if (endingPending && state === 'speaking') {
      endingPending = false;
      goodbyeRequest(reduced);
    }
    // Greet when speech starts and no transcript has arrived to say otherwise.
    if (!greeted && S.firstSpeakAt >= 0 && state === 'speaking' && S.t - S.firstSpeakAt >= D.greet.speechWait && cues && cues.msgCount === 0) {
      greetCue(input, reduced, out);
    }
    if (input.gam && input.gam.seq > seenGam) {
      seenGam = input.gam.seq;
      if (!reduced) {
        if (input.gam.kind === 'celebrate') queue.request('Celebrate', S.t);
        else if (input.gam.kind === 'happy') queue.request('Happy', S.t);
      }
      S.gamSmileUntil = S.t + (input.gam.kind === 'celebrate' ? 2.4 : 1.6);
    } else if (input.gam && input.gam.seq < seenGam) seenGam = input.gam.seq;

    // LookAround: idle glances, and after a long silence while listening.
    if (!reduced && !holo.active && !playing && queue.state.pend === '') {
      S.lookTimer -= dt;
      if (curBase === CLIP.idle && S.lookTimer <= 0) {
        S.lookTimer = between(D.shots.lookAroundEvery, rng);
        queue.request('LookAround', S.t);
      } else if (
        curBase === CLIP.listen && state === 'listening' && S.silentT >= D.shots.lookAroundListenSilence &&
        S.t >= S.lookCooldown && S.t >= S.expectUntil
      ) {
        S.lookCooldown = S.t + between(D.shots.lookAroundEvery, rng);
        S.silentT = 0;
        queue.request('LookAround', S.t);
      }
    }

    // Take the pending one-shot when it is allowed.
    if (!searchStarted) {
      takeEnv.speaking = state === 'speaking';
      takeEnv.holoActive = holo.active;
      const name = queue.take(S.t, takeEnv, take);
      if (name !== '') {
        const m = metaOf(name);
        queue.begin(name, m.dur, S.t, !!m.interruptible);
        if (take.cut) out.interrupt = D.fade.cut;
        const resolved = R(name);
        const force = reduced && name === 'Goodbye';
        if (resolved !== '') {
          startShot(name, resolved, out, 0, force, force ? D.shots.goodbyeReducedWeight : 1);
        } else {
          S.curShotStart = S.t;
        }
      }
    }
    out.shotPlaying = queue.playing(S.t);

    // ---- the base loop
    const want = wantBase(state, sig, live, reduced, holo, out);
    const resolved = R(want) || R(CLIP.idle) || curBase;
    const forced = holdFlip || interruptBase || holo.phase === HP.START;
    if (resolved !== curBase) {
      const dwell = S.t - S.baseSince;
      const intoSpeaking = isTalk(resolved) && !isTalk(curBase);
      let ok = curBase === '' || intoSpeaking || forced || dwell >= D.minDwell;
      if (ok && isTalk(resolved) && isTalk(curBase) && !forced && dwell < D.talkDwell) ok = false;
      if (ok) {
        const m = metaOf(resolved);
        out.base = resolved;
        out.baseChanged = true;
        out.baseFade = curBase === '' ? 0 : fadeFor(curBase, resolved, reduced);
        out.baseEntry = m.entry == null ? -1 : m.entry;
        const j = isListen(resolved) || isTalk(resolved) ? D.jitter.voice : D.jitter.other;
        out.baseScale = between(j, rng);
        curBase = resolved;
        curLogical = want;
        S.baseSince = S.t;
        if (want === CLIP.listenCurious) S.oohUntil = S.t + D.expr.ooh;
      }
    } else if (curLogical !== want) {
      curLogical = want;
    }
    out.logicalBase = curLogical;

    // ---- the voice: energy underlay
    const voice = input.voiceLevel ?? -1;
    let norm = -1;
    if (voice >= 0) {
      S.peak = Math.max(voice, S.peak * Math.exp(-dt / D.energy.peakDecay), D.energy.peakFloor);
      norm = clamp01(voice / S.peak);
    }
    if (state === 'speaking') {
      const target = norm < 0 ? 0.7 : norm;
      const rate = target > S.energy ? D.energy.attack : D.energy.release;
      S.energy += (target - S.energy) * (1 - Math.exp(-dt / rate));
    } else S.energy += (0.5 - S.energy) * (1 - Math.exp(-dt / 0.5));
    let under = 1;
    if (isTalk(curBase)) {
      under = D.energy.base + D.energy.gain * S.energy;
      if (curLogical === CLIP.talkStory) under = Math.max(under, D.energy.storyMin);
      else if (curLogical === CLIP.talkGentle) under = D.energy.gentle;
      if (reduced) under = D.energy.reduced;
    }
    out.underlay = clamp01(under);

    // ---- nods
    const blockedNod = playing !== '' && (playing === 'search' || playing === 'Celebrate' || playing === 'Greet' || playing === 'Goodbye');
    nodEnv.childSpeaking = !!input.childSpeaking;
    nodEnv.listening = state === 'listening' && isListen(curBase);
    nodEnv.speaking = state === 'speaking';
    nodEnv.blocked = blockedNod || holo.active;
    nodEnv.mood = curLogical === CLIP.listenEmpathy ? 'empathy' : curLogical === CLIP.listenExcited ? 'excited' : '';
    nodEnv.talkStyle = talkStyle;
    nodEnv.voice = norm;
    nodEnv.reduced = reduced;
    nodder.update(dt, S.t, nodEnv, out);
    if (S.greetNod > 0) {
      out.nod = Math.max(out.nod, S.greetNod);
      S.greetNod = 0;
    }

    // ---- expression layer
    expression(dt, state, holo, reduced, out);

    // ---- gaze and blink rate
    const reading = (holo.phase === HP.OPENING || holo.phase === HP.HOLD) && holo.foundT < 0;
    // w3: with a page the head reads it (0.35 while reading, 0.6 on Found; the reading line is the rig's gaze)
    const webLook = holoEnv.webHas && holo.kind === 'web';
    const onFound = holo.foundT >= 0 && holo.phase >= HP.GLOW && holo.phase <= HP.COLLAPSE && !holo.reduced;
    const lookTarget = reading ? (webLook ? 0.35 : has(CLIP.searchHold) ? 0.25 : 0.8) : webLook && onFound ? 0.6 : 0;
    ex.look = damp(ex.look, lookTarget, dt);
    out.lookPanel = ex.look;
    let rate = D.expr.blinkRate.other;
    if (holo.active) rate = D.expr.blinkRate.searching;
    else if (curLogical === CLIP.listenCurious) rate = D.expr.blinkRate.curious;
    else if (state === 'listening') rate = D.expr.blinkRate.listening;
    else if (state === 'thinking') rate = D.expr.blinkRate.thinking;
    out.blinkRate = rate;
    out.statusSeq = holo.statusSeq;
    out.statusKind = holo.statusKind;
    return out;
  }


  function greetCue(input, reduced, out) {
    if (greeted) return;
    greeted = true;
    if (reduced) return;
    if ((input.waveAgo ?? 999) < D.greet.waveWindow) {
      S.greetNod = 0.7; // Wave just played: one greeting gesture is enough
      return;
    }
    queue.request('Greet', S.t);
    void out;
  }

  function goodbyeRequest(reduced) {
    if (goodbyeDone) return;
    goodbyeDone = true;
    queue.request('Goodbye', S.t); // reduced motion still plays it, at half weight
    void reduced;
  }

  function expression(dt, state, holo, reduced, out) {
    const E = D.expr;
    const speaking = state === 'speaking';
    let squint = 0;
    let smile = 0;
    let soft = 0;
    let ooh = 0;
    const logical = curLogical;
    if (logical === CLIP.listenEmpathy) {
      squint = E.squint.empathy;
      if (!speaking) soft = 1;
    } else if (logical === CLIP.listenExcited) {
      squint = E.squint.excited;
      smile = 1;
    } else if (isTalk(logical) || speaking) {
      const style = fatigued ? lastStyle : out.talkStyle;
      if (style === 'praise') {
        squint = E.squint.praise;
        smile = 1;
      } else if (style === 'gentle') {
        squint = E.squint.gentle;
        if (!speaking) soft = 1;
      }
    }
    // Found: the "oh!", then a smile and a squint.
    if (holo.foundT >= 0) {
      smile = 1;
      if (holo.foundT < 0.2) ooh = 1;
      if (holo.foundT >= E.foundSquintFrom && holo.foundT <= E.foundSquintTo) squint = Math.max(squint, E.squint.found);
    }
    const shot = queue.playing(S.t);
    if (shot === 'Happy') smile = 1;
    else if (shot === 'Celebrate') {
      smile = 1;
      if (S.t - S.curShotStart >= metaOf(CLIP.celebrate).markers.land) squint = Math.max(squint, E.squint.celebrate);
    }
    if (S.t < S.gamSmileUntil) smile = 1;
    if (S.t < S.oohUntil) ooh = 1;
    if (squint > E.squintCap) squint = E.squintCap;
    ex.squint = damp(ex.squint, squint, dt);
    ex.smile = damp(ex.smile, smile, dt);
    ex.soft = damp(ex.soft, soft, dt);
    ex.ooh = damp(ex.ooh, ooh, dt);
    out.squint = ex.squint;
    out.smile = ex.smile;
    out.soft = ex.soft;
    out.ooh = ex.ooh;
    void reduced;
  }

  function reset() {
    S.t = 0;
    started = false;
    wasPaused = false;
    curBase = '';
    curLogical = '';
    S.baseSince = 0;
    greeted = false;
    goodbyeDone = false;
    endingPending = false;
    S.firstSpeakAt = -1;
    S.replySeenAt = -999;
    S.listenSeenAt = -999;
    styleStreak = 0;
    lastStyle = '';
    fatigued = false;
    queue.reset();
    nodder.reset();
    holoTl.reset();
  }

  return {
    step,
    reset,
    get time() {
      return S.t;
    },
    /** For tests and the dev overlay. */
    debug: () => ({ curBase, curLogical, fatigued, styleStreak, greeted, goodbyeDone, shot: queue.state.cur, pend: queue.state.pend, nods: nodder.state.total }),
  };
}
