// The search hologram's timeline (SPEC-EXPERIENCE 7.5). Pure: no three.js, no allocations per step.
// The web owns the timing; the backend only says searching, found or none.
//
//   closed -> start (SearchStart, panel opens at its `bloom` marker) -> hold (swipes, page turns)
//          -> found:  grace, then the Found clip: glow, collapse into the palm, sparkle burst
//          -> none:   dim, squash to a line, gone
//          -> interrupt: the child barged in, a quick reverse materialise
//
// The timeline runs on its own clock with the same times as the clips' markers, so it behaves the
// same whether or not the GLB has the clips yet. The director plays the clips it asks for.

export const HP = {
  CLOSED: 0,
  START: 1, // SearchStart plays, the panel is not open yet
  OPENING: 2, // the classic materialise
  HOLD: 3,
  GLOW: 4, // Found: the panel flashes gold
  COLLAPSE: 5, // ... shrinks into the palm
  BURST: 6, // ... a sparkle
  NONE_DIM: 7,
  NONE_CLOSE: 8,
  INT_CLOSE: 9,
  ICON: 10, // reduced motion: the static icon
  ICON_CHECK: 11,
};

const between = (range, rng) => range[0] + rng() * (range[1] - range[0]);

export function makeHoloOutput() {
  return {
    phase: HP.CLOSED,
    t: 0, // seconds in this phase
    kind: 'web',
    prevKind: 'web',
    kindMix: 1, // 0..1 cross-dissolve from prevKind to kind
    page: 0, // content pages turned so far
    pageT: 9, // seconds since the last page turn
    total: 0, // seconds since the panel started to open
    foundT: -1, // seconds since Found began (-1: not found)
    swipeT: -1, // seconds since a swipe began (-1: none)
    icon: 0, // reduced motion: 0 none, 1 search, 2 check
    iconA: 0,
    holdBase: false, // the hologram wants the SearchHold base loop
    thinkBase: false, // reduced motion: keep Think for the whole search
    active: false,
    quick: false,
    statusSeq: 0,
    statusKind: '', // library | folders | web | found
    // w3: the held web page
    reduced: false, // a web page in reduced motion: a 0.15 s fade in, the page jumps to the card, a 0.15 s fade out
    hero: 0, // 0..1 the window travelling out to the child (min-jerk), 1 while it is held
    shift: 0, // seconds the collapse and the sparkle are pushed back by the hero hold
    web: false, // this search shows the page model (the rig swaps the procedural skin for the held page)
  };
}

const minJerk = (x) => {
  const t = x < 0 ? 0 : x > 1 ? 1 : x;
  return t * t * t * (t * (t * 6 - 15) + 10);
};

export function createHoloTimeline({ rng = Math.random, cfg }) {
  const H = cfg;
  const out = makeHoloOutput();
  const q = {
    // requests for the director, set during step and cleared by the director
    req: '', // '' | 'SearchStart' | 'SearchSwipe' | 'Found'
    blink: false, // one blink at bloom and at glow
    interruptShots: false, // cut a swipe that is playing
  };
  let result = ''; // '' | found | none
  let graceT = 0;
  let searchSeen = false;
  let pendingKind = '';
  let lastCloseT = -999;
  let nextSwipeAt = 0;
  let swipes = 0;
  let sawNonListening = false;
  let bloomed = false;
  let iconNone = false;
  let glowed = false;
  let reduced = false;
  // w3: the held web page
  let webMode = false; // this search shows the page model (not the procedural skin)
  let resultsAt = -1; // out.total when the results first showed
  let resultWait = 0; // seconds Found waited for results that never came
  let heroOn = false;
  let clipSent = false;

  function setStatus(kind) {
    out.statusKind = kind;
    out.statusSeq += 1;
  }

  function reset() {
    out.phase = HP.CLOSED;
    out.t = 0;
    out.active = false;
    out.holdBase = false;
    out.thinkBase = false;
    out.foundT = -1;
    out.swipeT = -1;
    out.icon = 0;
    out.iconA = 0;
    out.reduced = false; // w3
    out.hero = 0;
    out.shift = 0;
    heroOn = false;
    clipSent = false;
    webMode = false;
    out.web = false;
    resultsAt = -1;
    resultWait = 0;
    result = '';
    graceT = 0;
  }

  function close(t) {
    reset();
    lastCloseT = t;
  }

  function start(kind, t, quick, env) {
    reduced = env.reduced;
    out.kind = kind;
    out.prevKind = kind;
    out.kindMix = 1;
    out.page = 0;
    out.pageT = 9;
    out.total = 0;
    out.foundT = -1;
    out.swipeT = -1;
    out.quick = quick;
    out.active = true;
    out.t = 0;
    result = '';
    graceT = 0;
    swipes = 0;
    bloomed = false;
    glowed = false;
    sawNonListening = env.state !== 'listening';
    nextSwipeAt = H.bloomAt + between(H.swipeFirst, rng);
    webMode = kind === 'web' && !!env.webHas; // w3
    out.web = webMode;
    resultsAt = -1;
    resultWait = 0;
    heroOn = false;
    clipSent = false;
    out.reduced = false;
    out.hero = 0;
    out.shift = 0;
    if (reduced && webMode) {
      // w3: reduced motion with a page: no icon, no clips; a 0.15 s fade in, the page, a 0.15 s fade out
      out.phase = HP.OPENING;
      out.reduced = true;
      out.thinkBase = true;
      out.holdBase = false;
      bloomed = true;
      out.t = 0;
      setStatus(kind);
    } else if (reduced) {
      out.phase = HP.ICON;
      out.icon = 1;
      out.iconA = 0;
      out.thinkBase = true;
      setStatus(kind);
    } else {
      out.phase = HP.START;
      out.holdBase = true;
      q.req = 'SearchStart';
    }
  }

  function allowed(env) {
    return env.visible && !env.blocked;
  }

  /** An al.activity transition. `kind` is the search kind that was current for it. */
  function onActivity(to, kind, t, env) {
    if (to === 'searching') {
      searchSeen = true;
      if (out.phase === HP.CLOSED) {
        if (t - lastCloseT >= H.toolGap && allowed(env)) start(kind, t, false, env);
      } else if (out.phase <= HP.HOLD || out.phase >= HP.ICON) {
        // A new search while one is open: keep the panel, cross-dissolve the skin.
        result = '';
        graceT = 0;
        if (kind !== out.kind) {
          out.prevKind = out.kind;
          out.kind = kind;
          out.kindMix = 0;
        }
      } else {
        pendingKind = kind; // it is closing: open again once it is closed
      }
      return;
    }
    if (to !== 'found' && to !== 'none') return;
    pendingKind = ''; // integrate-1: a search waiting to reopen the panel has already ended
    if (out.phase === HP.CLOSED) {
      if (searchSeen) {
        searchSeen = false; // the search was denied or already ended: nothing to show
        return;
      }
      // Found or none without a searching seen (coalesced, or a late join): a quick search.
      if (t - lastCloseT >= H.quickGap && allowed(env)) {
        start(kind, t, true, env);
        result = to;
      }
      return;
    }
    searchSeen = false;
    if (out.phase <= HP.HOLD || out.phase >= HP.ICON) result = to;
  }

  /** Advance the timeline. `env`: {state, reduced, visible, blocked, swipePlaying}. */
  function step(dt, t, env) {
    out.t += dt;
    if (out.kindMix < 1) out.kindMix = Math.min(1, out.kindMix + dt / 0.3);
    if (out.pageT < 9) out.pageT += dt;
    if (env.state !== 'listening') sawNonListening = true;
    const p = out.phase;

    if (p === HP.CLOSED) {
      if (pendingKind && allowed(env)) {
        // integrate-1: wait out the 0.2 s gap. Checking it on the first closed frame (always under
        // 0.2 s) dropped every search that came in while the panel was closing.
        if (t - lastCloseT >= 0.2) {
          const k = pendingKind;
          pendingKind = '';
          start(k, t, false, env);
        }
      } else if (pendingKind) pendingKind = '';
      return out;
    }

    out.total += dt;

    // Reduced motion: a static icon, no panel.
    if (p === HP.ICON || p === HP.ICON_CHECK) {
      stepIcon(dt, t, env);
      return out;
    }

    // w3: the held page: it may join late (the skeleton arrives after the activity), and flicks start with the results
    if (!webMode && out.kind === 'web' && env.webHas && !out.reduced && p <= HP.HOLD && out.foundT < 0 && p !== HP.CLOSED) {
      webMode = true;
      out.web = true;
    }
    if (webMode && env.webResults && resultsAt < 0 && out.foundT < 0) {
      resultsAt = out.total;
      nextSwipeAt = out.total + between(H.swipeFirst, rng);
    }

    // The child barged in: a quick reverse materialise (only before Found has begun).
    if (p <= HP.HOLD && env.state === 'listening' && sawNonListening) {
      out.phase = HP.INT_CLOSE;
      out.t = 0;
      out.holdBase = false;
      q.interruptShots = true;
      return out;
    }

    if (p === HP.START) {
      if (out.t >= H.bloomAt) {
        out.phase = HP.OPENING;
        out.t = out.t - H.bloomAt;
        bloomed = true;
        q.blink = true;
        setStatus(out.kind);
      }
    } else if (p === HP.OPENING) {
      const openFor = out.reduced ? H.reducedOpen : H.open; // w3
      if (out.t >= openFor) {
        out.phase = HP.HOLD;
        out.t -= openFor;
      }
    }

    if (out.phase === HP.OPENING || out.phase === HP.HOLD) {
      stepHold(dt, env);
    } else if (out.phase >= HP.GLOW && out.phase <= HP.BURST) {
      stepFound(dt, t);
    } else if (out.phase === HP.NONE_DIM) {
      if (out.t >= H.noneDim) {
        out.phase = HP.NONE_CLOSE;
        out.t = 0;
      }
    } else if (out.phase === HP.NONE_CLOSE) {
      if (out.t >= H.noneSquash + H.noneGone) close(t);
    } else if (out.phase === HP.INT_CLOSE) {
      if (out.t >= H.interruptClose) close(t);
    }
    return out;
  }

  function sinceBloom() {
    return out.total - H.bloomAt;
  }

  function stepHold(dt, env) {
    // Swipes and page turns while holding.
    if (out.swipeT >= 0) {
      const before = out.swipeT;
      out.swipeT += dt;
      if (before < H.swipeAdvanceAt && out.swipeT >= H.swipeAdvanceAt) {
        out.page += 1;
        out.pageT = 0;
      }
      if (out.swipeT >= H.swipeDur) out.swipeT = -1;
    }
    const swipePlaying = out.swipeT >= 0 || env.swipePlaying;
    // w3: with a page, flicks start once the results show, only when the page can scroll, up to six, never in reduced motion
    const swipeOk = !webMode || (!out.reduced && resultsAt >= 0 && !!env.webScroll);
    const swipeCap = webMode ? H.webSwipeMax : H.swipeMax;
    if (out.foundT < 0 && result === '' && swipeOk && swipes < swipeCap && out.total >= nextSwipeAt && !swipePlaying && bloomed) {
      swipes += 1;
      out.swipeT = 0;
      q.req = 'SearchSwipe';
      nextSwipeAt = out.total + between(H.swipeEvery, rng);
    }

    // The search took too long: close it as none.
    if (result === '' && sinceBloom() >= H.maxHold) result = 'none';

    if (result !== '' && sinceBloom() >= H.minShow && !swipePlaying && out.phase === HP.HOLD && webReady(dt)) {
      if (result === 'found') {
        graceT += dt;
        if (graceT >= H.foundGrace) {
          out.foundT = 0;
          out.phase = HP.GLOW;
          out.t = 0;
          glowed = false;
          // w3: with a page, Found is the hero hold: the window goes out to the child, and the Found clip waits for
          // the end of it (its collapse marker lands on the collapse). Reduced motion plays no clip at all.
          heroOn = webMode && !out.reduced && !!env.webHero;
          out.shift = heroOn ? H.hero.out + H.hero.hold + H.hero.back : 0;
          clipSent = false;
          if (out.reduced) {
            out.holdBase = false;
          } else if (heroOn) {
            out.holdBase = true; // the hand stays up, holding the window out
          } else {
            out.holdBase = false;
            q.req = 'Found';
            clipSent = true;
          }
          // The panel keeps its look until the glow marker; the phase is GLOW from the start
          // of Found so the component can read foundT for the "!" beat.
        }
      } else {
        out.phase = HP.NONE_DIM;
        out.t = 0;
        out.holdBase = false;
      }
    } else if (result === '') graceT = 0;
  }

  /** w3: may Found begin? With a page it waits until the results were on show long enough for one flick to be read. */
  function webReady(dt) {
    if (!webMode || result !== 'found') return true;
    if (resultsAt >= 0) return out.reduced || out.total - resultsAt >= H.webReadMin;
    resultWait += dt; // no results page came: do not hold Found up for ever
    return resultWait >= H.webWait;
  }

  function stepFound(dt, t) {
    out.foundT += dt;
    const ft = out.foundT;
    if (!glowed && ft >= H.glowAt) {
      glowed = true;
      q.blink = !out.reduced;
      setStatus('found');
    }
    if (out.reduced) {
      // w3: the page stays up, gold, for reducedHold, then fades out
      if (ft >= H.reducedHold + H.reducedFade) close(t);
      return;
    }
    const sh = out.shift;
    if (heroOn) {
      const he = H.hero;
      const u = ft - (H.glowAt + H.glow);
      out.hero = u <= 0 ? 0 : u < he.out ? minJerk(u / he.out) : u < he.out + he.hold ? 1 : 1 - minJerk((u - he.out - he.hold) / he.back);
      if (!clipSent && ft >= sh) {
        clipSent = true;
        out.holdBase = false;
        q.req = 'Found';
      }
    }
    if (ft >= H.sparkleAt + sh) {
      if (out.phase !== HP.BURST) {
        out.phase = HP.BURST;
        out.t = 0;
        out.hero = 0;
      }
      if (out.t >= H.burst) close(t);
    } else if (ft >= H.collapseAt + sh) {
      if (out.phase !== HP.COLLAPSE) {
        out.phase = HP.COLLAPSE;
        out.t = 0;
      }
    }
  }

  function stepIcon(dt, t, env) {
    const fin = out.foundT >= 0;
    if (out.phase === HP.ICON) {
      out.iconA = Math.min(1, out.iconA + dt / H.iconIn);
      if (result === '' && out.total >= H.maxHold) result = 'none';
      if (result !== '' && out.total >= H.minShow) {
        if (result === 'found') {
          out.phase = HP.ICON_CHECK;
          out.icon = 2;
          out.foundT = 0;
          out.t = 0;
          iconNone = false;
          setStatus('found');
        } else {
          out.phase = HP.ICON_CHECK;
          out.icon = 1;
          out.foundT = -1;
          out.t = 0;
          iconNone = true;
        }
      }
      if (env.state === 'listening' && sawNonListening && !fin) close(t);
    } else {
      if (out.foundT >= 0) out.foundT += dt;
      const hold = iconNone ? 0 : H.iconCheck;
      if (out.t >= hold) {
        out.iconA = Math.max(0, out.iconA - dt / H.iconOut);
        if (out.iconA <= 0) close(t);
      }
    }
  }

  /** The director calls this once a frame, before onActivity and step. */
  function beginFrame() {
    q.req = '';
    q.blink = false;
    q.interruptShots = false;
  }

  return { out, q, step, beginFrame, onActivity, reset, close, lastClose: () => lastCloseT };
}
