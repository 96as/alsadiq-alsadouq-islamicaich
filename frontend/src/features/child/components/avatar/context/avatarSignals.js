// The avatar's view of the session, kept outside React so reading it never re-renders anything
// (SPEC-EXPERIENCE 8.6). useLiveKitRoom feeds it from LiveKit; the dev simulator feeds the very
// same functions, so what the simulator shows is what a live session would do.
//
// The director reads it through one getter, `getContext()`. The object it returns is the same
// every time; its fields change in place.

import { createCueTracker } from './transcriptCues.js';

export const RING = 16;
export const SIGNAL_PREFIX = 'al.';
const ACTIVITIES = new Set(['idle', 'searching', 'found', 'none']);
const KINDS = new Set(['library', 'folders', 'web']);
const TALK_STYLES = new Set(['explain', 'story', 'praise', 'question', 'gentle']);
const LISTEN_STYLES = new Set(['neutral', 'curious', 'sad', 'excited']);

/** Gamification payloads that mean a big celebration, and the small one (a point or two). */
export function classifyGamification(ev) {
  if (!ev || typeof ev !== 'object') return '';
  const big =
    ev.type === 'quest_completed' ||
    ev.leveled_up === true ||
    (Array.isArray(ev.new_badges) && ev.new_badges.length > 0);
  if (big) return 'celebrate';
  if (ev.type === 'points' && Number(ev.delta) > 0) return 'happy';
  return '';
}

export function createAvatarContextStore({ now = () => performance.now() } = {}) {
  const signals = {
    v: 0, // 1 when the agent has published al.sig_v = "1"
    activity: 'idle',
    searchKind: 'web',
    talkStyle: 'explain',
    reply: 0,
    listenStyle: 'neutral',
    turn: 0,
    changedAt: { activity: 0, searchKind: 0, talkStyle: 0, reply: 0, listenStyle: 0, turn: 0 },
    events: new Array(RING).fill(null), // al.activity transitions, a ring
    eventCount: 0, // how many have ever been pushed; event i lives at events[i % RING]
    web: null, // w3: the latest al.search message (see onSearchMessage), the held web page's content
  };
  const cues = createCueTracker();
  const ctx = {
    signals,
    cues: cues.state,
    childSpeaking: false,
    lang: 'en',
    gam: { seq: 0, kind: '' }, // the latest gamification moment: 'happy' | 'celebrate'
    sessionEndingSeq: 0,
    connectSeq: 0, // +1 on every (re)connect
    awaySec: 0, // seconds the previous connection had been gone when this one began
  };
  let disconnectedAt = 0;

  function pushEvent(from, to, kind) {
    const t = now();
    signals.events[signals.eventCount % RING] = { seq: signals.eventCount + 1, from, to, kind, t };
    signals.eventCount += 1;
    // w3: a new search starts: the page of the one before is spent (a new al.search replaces it anyway)
    if (to === 'searching' && signals.web && signals.web.st !== 'searching') signals.web.used = true;
  }

  // w3: al.search is a data topic (JSON), see BEHAVIOUR-SPEC 6.8. Only the fields the page can show are kept, the
  // rest is dropped here; contentFilter.js escapes and truncates what is left.
  const WEB_STATES = new Set(['searching', 'results', 'none']);
  function onSearchMessage(data) {
    if (!data || typeof data !== 'object') return false;
    if (!WEB_STATES.has(data.st)) return false;
    if (data.kind !== undefined && data.kind !== 'web') return false; // the library and folder searches are unchanged
    const r = [];
    if (Array.isArray(data.r)) {
      for (let i = 0; i < data.r.length && r.length < 5; i++) {
        const x = data.r[i];
        if (x && typeof x === 'object') r.push({ t: x.t, d: x.d, s: x.s });
      }
    }
    const prev = signals.web;
    signals.web = {
      rev: (prev ? prev.rev : 0) + 1,
      id: typeof data.id === 'string' ? data.id.slice(0, 24) : '',
      st: data.st,
      q: typeof data.q === 'string' ? data.q.slice(0, 400) : '',
      lang: data.lang === 'ar' ? 'ar' : data.lang === 'en' ? 'en' : '',
      r,
      hl: Number.isInteger(data.hl) ? data.hl : 0,
      sf: data.sf ? 1 : 0,
      fixture: data.fixture === true,
      at: now(),
      used: false,
    };
    return true;
  }

  function setActivity(value, asEvent) {
    if (!ACTIVITIES.has(value) || value === signals.activity) return;
    const from = signals.activity;
    signals.activity = value;
    signals.changedAt.activity = now();
    if (asEvent) pushEvent(from, value, signals.searchKind);
  }

  /**
   * Read the al.* keys of an attribute map. `asEvent` is false for the initial snapshot, which
   * sets values but never counts as an activity transition. An empty string means "deleted".
   */
  function apply(attrs, asEvent) {
    if (!attrs) return;
    const t = now();
    // Order matters: the search kind is read before the activity it belongs to.
    if (attrs['al.search_kind'] && KINDS.has(attrs['al.search_kind'])) {
      signals.searchKind = attrs['al.search_kind'];
      signals.changedAt.searchKind = t;
    }
    if (attrs['al.sig_v'] !== undefined) signals.v = attrs['al.sig_v'] === '1' ? 1 : 0;
    if (attrs['al.talk_style'] && TALK_STYLES.has(attrs['al.talk_style'])) {
      signals.talkStyle = attrs['al.talk_style'];
      signals.changedAt.talkStyle = t;
    }
    if (attrs['al.reply'] !== undefined && attrs['al.reply'] !== '') {
      const n = Number.parseInt(attrs['al.reply'], 10);
      if (Number.isFinite(n) && n !== signals.reply) {
        signals.reply = n;
        signals.changedAt.reply = t;
      }
    }
    if (attrs['al.listen_style'] && LISTEN_STYLES.has(attrs['al.listen_style'])) {
      if (attrs['al.listen_style'] !== signals.listenStyle) signals.changedAt.listenStyle = t;
      signals.listenStyle = attrs['al.listen_style'];
    }
    if (attrs['al.turn'] !== undefined && attrs['al.turn'] !== '') {
      const n = Number.parseInt(attrs['al.turn'], 10);
      if (Number.isFinite(n) && n !== signals.turn) {
        signals.turn = n;
        signals.changedAt.turn = t;
      }
    }
    if (attrs['al.activity']) setActivity(attrs['al.activity'], asEvent);
  }

  return {
    ctx,
    /** The stable getter prop the avatar components receive. */
    getContext: () => ctx,
    /** The initial attributes of the agent (ParticipantConnected). No events. */
    applySnapshot: (attrs) => apply(attrs, false),
    /** ParticipantAttributesChanged for the agent: only keys starting with al. matter. */
    applyChanged(changed) {
      if (!changed) return;
      let any = false;
      for (const key in changed) {
        if (key.startsWith(SIGNAL_PREFIX)) {
          any = true;
          break;
        }
      }
      if (any) apply(changed, true);
    },
    setChildSpeaking(on) {
      ctx.childSpeaking = !!on;
    },
    setLang(lang) {
      ctx.lang = lang === 'ar' ? 'ar' : 'en';
    },
    onAgentText: (text, info) => cues.onAgentText(text, info),
    onSearchMessage, // w3
    onGamification(ev) {
      const kind = classifyGamification(ev);
      if (!kind) return;
      ctx.gam.kind = kind;
      ctx.gam.seq += 1;
    },
    onSessionLimit(ev) {
      if (ev && ev.type === 'session_ending') ctx.sessionEndingSeq += 1;
    },
    markConnected() {
      ctx.connectSeq += 1;
      ctx.awaySec = disconnectedAt ? (now() - disconnectedAt) / 1000 : 0;
      disconnectedAt = 0;
    },
    markDisconnected() {
      disconnectedAt = now();
      // The agent is gone: nothing it published is current any more.
      signals.v = 0;
      signals.activity = 'idle';
      signals.web = null; // w3
      ctx.childSpeaking = false;
    },
    /** Back to a fresh session (used by the simulator's reset). */
    reset() {
      signals.v = 0;
      signals.activity = 'idle';
      signals.searchKind = 'web';
      signals.talkStyle = 'explain';
      signals.reply = 0;
      signals.listenStyle = 'neutral';
      signals.turn = 0;
      signals.events.fill(null);
      signals.eventCount = 0;
      signals.web = null; // w3
      cues.reset();
      ctx.childSpeaking = false;
      ctx.gam.kind = '';
    },
  };
}
