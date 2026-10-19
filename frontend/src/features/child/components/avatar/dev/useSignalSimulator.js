// Dev only (06-avatar-context): a fake agent for the avatar's session signals. It feeds the SAME store
// functions useLiveKitRoom feeds from LiveKit (applySnapshot, applyChanged, onAgentText, onGamification,
// setChildSpeaking, onSessionLimit), so what the dev pages show is what a live session would do.
//
// Everything is scriptable from the console as window.__sim (Playwright uses it too):
//   __sim.connect()                      al.sig_v=1 and a (re)connect
//   __sim.listen('curious')              al.listen_style + al.turn
//   __sim.talk('story')                  al.talk_style + al.reply (a new reply)
//   __sim.search('library', 'found', 3500)   searching now, found (or none) after 3.5 s
//   __sim.searchWeb('sky', {outcome, lang})  the held web page: fixture results, then found (w3)
//   __sim.interrupt()                 activity idle + the host's onInterrupt (agent state back to listening)
//   __sim.gam('celebrate')               a gamification event
//   __sim.say('As-salamu alaykum!')      one agent transcript message
//   __sim.child(true)                    the child is speaking
//   __sim.limit()                        the session_ending warning
//   __sim.lang('ar')                     the hologram mirrors for Arabic
//   __sim.newSession()                   reset + a long-break reconnect (Greet and Goodbye can play again)

import { useEffect, useMemo, useRef, useState } from 'react';
import { createAvatarContextStore } from '../context/avatarSignals.js';
import { fixtureMessage, flaggedMessage, metaWordMessage } from '../hologram/webPage/fixtures.js'; // w3

export const SIM_LISTEN = ['neutral', 'curious', 'sad', 'excited'];
export const SIM_TALK = ['explain', 'story', 'praise', 'question', 'gentle'];
export const SIM_KINDS = ['library', 'folders', 'web'];

const GAM_EVENTS = {
  happy: { type: 'points', delta: 5 },
  celebrate: { type: 'quest_completed' },
};

export default function useSignalSimulator({ initialLang = 'en', onInterrupt } = {}) {
  const store = useMemo(() => createAvatarContextStore(), []);
  // The child cutting in is the agent going back to 'listening', not an al.* signal: the host page flips its state picker.
  const interruptRef = useRef(onInterrupt);
  useEffect(() => {
    interruptRef.current = onInterrupt;
  }, [onInterrupt]);
  const timers = useRef(new Set());
  const counters = useRef({ turn: 0, reply: 0, msg: 0 });
  const [lang, setLangState] = useState(initialLang);

  const sim = useMemo(() => {
    const later = (fn, ms) => {
      const id = window.setTimeout(() => {
        timers.current.delete(id);
        fn();
      }, ms);
      timers.current.add(id);
      return id;
    };
    const clearTimers = () => {
      for (const id of timers.current) window.clearTimeout(id);
      timers.current.clear();
    };
    const set = (attrs) => store.applyChanged(attrs);
    const api = {
      store,
      getContext: store.getContext,
      connect() {
        store.applySnapshot({ 'al.sig_v': '1' });
        store.markConnected();
      },
      disconnect() {
        clearTimers();
        store.markDisconnected();
      },
      attrs: set,
      listen(style = 'neutral') {
        counters.current.turn += 1;
        set({ 'al.listen_style': style, 'al.turn': String(counters.current.turn) });
      },
      talk(style = 'explain') {
        counters.current.reply += 1;
        set({ 'al.talk_style': style, 'al.reply': String(counters.current.reply) });
      },
      /** searching now; found or none after `delayMs`; then idle again 4 s later (so the next one is a change). */
      search(kind = 'web', outcome = 'found', delayMs = 3500) {
        clearTimers();
        set({ 'al.search_kind': kind, 'al.activity': 'searching' });
        later(() => set({ 'al.activity': outcome }), delayMs);
        later(() => set({ 'al.activity': 'idle' }), delayMs + 4500);
      },
      /**
       * w3: a web search the way the agent publishes it: al.search "searching" with al.activity, the results
       * `resultsMs` later, then found (or none) at `foundMs`, then idle. FIXTURE text only (fixtures.js).
       * @param {string} name 'sky' | 'bees'
       * @param {{outcome?: 'found'|'none'|'grownup'|'meta', lang?: string, resultsMs?: number, foundMs?: number}} [opts]
       */
      searchWeb(name = 'sky', { outcome = 'found', lang: l = 'en', resultsMs = 1600, foundMs = 9000 } = {}) {
        clearTimers();
        counters.current.search = (counters.current.search || 0) + 1;
        const id = `fx${counters.current.search}`;
        const lg = l === 'ar' ? 'ar' : 'en';
        const searching = fixtureMessage(name, lg, 'searching', id);
        let results;
        if (outcome === 'none') results = fixtureMessage(name, lg, 'none', id);
        else if (outcome === 'grownup') results = flaggedMessage(lg, id);
        else if (outcome === 'meta') results = metaWordMessage(lg, id);
        else results = fixtureMessage(name, lg, 'results', id);
        store.onSearchMessage(searching);
        set({ 'al.search_kind': 'web', 'al.activity': 'searching' });
        later(() => store.onSearchMessage(results), resultsMs);
        later(() => set({ 'al.activity': outcome === 'none' ? 'none' : 'found' }), foundMs);
        later(() => set({ 'al.activity': 'idle' }), foundMs + 6500);
      },
      interrupt() {
        clearTimers();
        set({ 'al.activity': 'idle' });
        if (interruptRef.current) interruptRef.current();
      },
      gam(kind = 'happy') {
        store.onGamification(GAM_EVENTS[kind] ?? GAM_EVENTS.happy);
      },
      say(text, final = true) {
        counters.current.msg += 1;
        store.onAgentText(text, { id: `sim-${counters.current.msg}`, final });
      },
      child(on) {
        store.setChildSpeaking(on);
      },
      limit() {
        store.onSessionLimit({ type: 'session_ending', seconds_left: 30 });
      },
      lang(next) {
        store.setLang(next);
        setLangState(next === 'ar' ? 'ar' : 'en');
      },
      reset() {
        clearTimers();
        counters.current = { turn: 0, reply: 0, msg: 0 };
        store.reset();
        api.connect();
      },
      /**
       * integrate-1: a brand new session that the director treats as a reconnect after a long break,
       * so Greet and Goodbye (once per session) can play again. The showcase buttons use it.
       */
      newSession() {
        api.reset();
        store.getContext().awaySec = 999;
      },
      clearTimers,
    };
    return api;
  }, [store]);

  useEffect(() => {
    store.setLang(initialLang);
    sim.connect();
    window.__sim = sim;
    window.__simStore = store;
    return () => {
      sim.clearTimers();
      if (window.__sim === sim) {
        delete window.__sim;
        delete window.__simStore;
      }
    };
  }, [sim, store, initialLang]);

  return { sim, getContext: store.getContext, lang };
}
