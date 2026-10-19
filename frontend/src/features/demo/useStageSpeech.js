import { useCallback, useEffect, useRef, useState } from 'react';
import { soundBus } from './soundBus';

/**
 * What Sadiq says and what the props do, as state for the stage pieces in stageParts.jsx.
 *
 *   say(text, { hold })   one bubble at a time: it pops (420 ms), its words arrive 80 ms apart, it stays
 *                         `hold` ms (4.5 s), then leaves in 200 ms. Returns how long until the last word is in.
 *   later(fn, ms)         a timer that is cleared on unmount
 *   onTapProp / onHover   handlers for the lantern, book and bulbul buttons
 *   ps, flash, card       prop states, the prop whose verb label shows after a touch, the open value card
 *   lastActive            performance.now() of the last touch (the idle beats wait on it)
 *
 * `live` is true while the forest is drawn (the props only exist then).
 */

export const wordsOf = (text) => text.split(' ');

const WORD_MS = 80; // one word at a time, never one letter (Arabic letters join)
const HOLD_MS = 4500;
const EXIT_MS = 200;
const VALUE_HOLD_MS = 6000;
const VALUE_KEY = 'demo_value_index';

/** The next value to show: the index lives in sessionStorage, so each tap moves on (and a reload continues). */
const nextValueIndex = (count) => {
  try {
    const i = Number(window.sessionStorage.getItem(VALUE_KEY)) || 0;
    window.sessionStorage.setItem(VALUE_KEY, String((i + 1) % count));
    return i % count;
  } catch {
    return 0;
  }
};

export default function useStageSpeech({ controlRef, t, live }) {
  const timers = useRef(new Set());
  const seq = useRef(0);
  const lastActive = useRef(0);
  const interacted = useRef(false);
  const birdGreeted = useRef(false);

  const [speaking, setSpeaking] = useState(false);
  const [bubble, setBubble] = useState(null); // { id, text, leaving }
  const [card, setCard] = useState(null); // { id, idx, leaving }
  const [flash, setFlash] = useState(null);
  const [ps, setPs] = useState({ lit: false, asleep: false });

  const later = useCallback((fn, ms) => {
    const id = window.setTimeout(() => {
      timers.current.delete(id);
      fn();
    }, ms);
    timers.current.add(id);
    return id;
  }, []);
  useEffect(() => {
    const set = timers.current;
    return () => {
      set.forEach((id) => window.clearTimeout(id));
      set.clear();
    };
  }, []);

  const activity = useCallback(() => {
    interacted.current = true;
    lastActive.current = performance.now();
  }, []);

  const say = useCallback((text, { hold = HOLD_MS } = {}) => {
    seq.current += 1;
    const id = seq.current;
    const total = 420 + wordsOf(text).length * WORD_MS;
    setCard(null); // one thing at a time next to him
    setBubble({ id, text, leaving: false });
    setSpeaking(true);
    later(() => setSpeaking(false), Math.min(total + 600, 3200));
    later(() => setBubble((b) => (b && b.id === id ? { ...b, leaving: true } : b)), total + hold);
    later(() => setBubble((b) => (b && b.id === id ? null : b)), total + hold + EXIT_MS);
    return total;
  }, [later]);

  // The prop states that change the verb labels (the lantern is lit, the bulbul sleeps).
  useEffect(() => {
    if (!live) return undefined;
    const id = window.setInterval(() => {
      const rt = controlRef.current?.rt;
      if (!rt) return;
      const lit = Boolean(rt.props.lantern.lit);
      const asleep = Boolean(rt.props.bird.asleep);
      setPs((p) => (p.lit === lit && p.asleep === asleep ? p : { lit, asleep }));
    }, 250);
    return () => window.clearInterval(id);
  }, [live, controlRef]);

  const flashLabel = useCallback((name) => {
    setFlash(name);
    later(() => setFlash((f) => (f === name ? null : f)), 1200);
  }, [later]);

  const showValue = useCallback(() => {
    seq.current += 1;
    const id = seq.current;
    setBubble(null);
    setCard({ id, idx: nextValueIndex(t.values.length), leaving: false });
    later(() => setCard((c) => (c && c.id === id ? { ...c, leaving: true } : c)), VALUE_HOLD_MS);
    later(() => setCard((c) => (c && c.id === id ? null : c)), VALUE_HOLD_MS + EXIT_MS);
  }, [later, t.values.length]);

  const onHover = useCallback((name, on) => {
    const c = controlRef.current;
    if (!c || name === 'sadiq') return;
    c.rt.props[name].hover = on ? 1 : 0;
    if (on && name !== 'book') c.look({ name }, 1.4);
  }, [controlRef]);

  const onTapProp = useCallback((name) => {
    const c = controlRef.current;
    activity();
    flashLabel(name);
    if (c) {
      c.rt.bus.dispatchEvent(new CustomEvent('prop-tap', { detail: { name } }));
      c.look({ name }, 1.8);
    }
    soundBus.play?.(name === 'book' ? 'page' : name === 'lantern' ? 'lantern' : 'tweet');
    if (name === 'book') showValue();
    if (name === 'bird' && !birdGreeted.current && !c?.rt.props.bird.asleep) {
      birdGreeted.current = true;
      say(t.birdHello);
    }
  }, [controlRef, activity, flashLabel, showValue, say, t.birdHello]);

  return { later, say, activity, lastActive, speaking, bubble, card, flash, ps, onHover, onTapProp };
}
