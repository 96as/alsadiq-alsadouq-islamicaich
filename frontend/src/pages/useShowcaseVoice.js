// integrate-1: the meadow page's REAL voice. It plays one of the few clips the showcase build ships
// (showcase-audio/manifest.json, made by scripts/showcase-audio.mjs from the gitignored dev-audio
// folder) and gives back getLipsync() / getLevel(), so Sadiq's mouth follows it the way it follows
// the agent in a session: the clip's text timing (the lk.lipsync messages, replayed here) coloured
// by the audio. With no manifest (no clips in this build) `clips` is empty and the page keeps its
// made-up voice.
//
// hotfix-2: SAFARI-SAFE PLAY. Safari and iOS only start sound inside the user's tap, and they drop
// that permission at the first await. The old speak() awaited resume(), a fetch and (on a language
// switch) two animation frames BEFORE el.play(), so play() threw NotAllowedError there, the catch only
// warned, and the child saw nothing at all. Now:
//   - on load the page prefetches the manifest and EVERY clip's alignment and audio (the alignment
//     is parsed into timeline items, the audio becomes a blob URL), so a tap has nothing to wait for;
//   - speak() calls el.play() (source already set) and audioContext.resume() in the same tick, as its
//     FIRST statements, with no await before them; everything else (the lip-sync timeline, the
//     language switch, the state callbacks) happens after play() has been called;
//   - the first tap, touch or key press anywhere unlocks the audio context (resume + one silent
//     sample), so a later tap always works;
//   - if play() still rejects, or the context stays suspended, `blocked` is set and the page shows a
//     "Tap to turn on sound" button whose own tap retries (retry()); it is logged, never silent.
// tests/showcase-voice-order.test.mjs keeps the "play before any await" rule.
import { useCallback, useEffect, useRef, useState } from 'react';
import { assetUrl } from '../utils/assetUrl.js';
import useVisemes from '../features/child/components/avatar/lipsync/useVisemes.js';
import { TimelineSync } from '../features/child/components/avatar/lipsync/timelineSync.js';
import { alignmentToItems, goMessage, stopMessage, timelineMessages } from '../features/child/components/avatar/lipsync/timelineMessages.js';

const nextFrame = () => new Promise((resolve) => requestAnimationFrame(() => resolve()));
const base = (name) => assetUrl(`/showcase-audio/${name}`);
const UNLOCK_EVENTS = ['pointerdown', 'touchend', 'click', 'keydown'];

/** One line per tap, for the tests and for anyone debugging a phone (window.__voiceLog). */
function record(entry) {
  try {
    const log = (window.__voiceLog ||= []);
    log.push(entry);
    if (log.length > 60) log.shift();
  } catch {
    /* no window */
  }
}

/**
 * @param {{ onStart?: (clip: object) => void, onEnd?: (clip: object, why: 'ended'|'stopped') => void }} [cb]
 */
export default function useShowcaseVoice({ onStart, onEnd } = {}) {
  const [el] = useState(() => {
    if (typeof Audio === 'undefined') return null;
    const a = new Audio();
    a.preload = 'auto';
    return a;
  });
  const [sink] = useState(() => new TimelineSync());
  const [lang, setLang] = useState('ar');
  const { getLipsync, resume, unlock, setMuted: muteGain, contextState, gainValue } = useVisemes(el, { lang, timeline: sink });
  const [clips, setClips] = useState([]);
  const [loaded, setLoaded] = useState(false);
  const [ready, setReady] = useState(false); // every clip prefetched
  const [playing, setPlaying] = useState('');
  const [blocked, setBlocked] = useState(null); // { clip, reason } when the browser refused the sound
  const cur = useRef({ clip: null, sp: '', n: 0 });
  const live = useRef(false); // true from the tap until the clip ends
  const langRef = useRef('ar'); // the vowel model of the current driver (read in the tap, not rendered)
  const prepared = useRef(new Map()); // clip id -> { items, url }
  const srcId = useRef(''); // the clip whose source the element holds
  const mutedRef = useRef(false);
  const blockedRef = useRef(null);
  const cb = useRef({ onStart, onEnd });
  useEffect(() => {
    cb.current = { onStart, onEnd };
  }, [onStart, onEnd]);
  useEffect(() => {
    blockedRef.current = blocked;
  }, [blocked]);

  // Prefetch the manifest, then every clip's alignment (parsed) and audio (a blob URL, so a tap sets a
  // source that is already in memory and play() has nothing to download).
  useEffect(() => {
    let off = false;
    const urls = [];
    const map = prepared.current;
    (async () => {
      let list = [];
      try {
        const r = await fetch(base('manifest.json'));
        const m = r.ok ? await r.json() : { clips: [] };
        list = Array.isArray(m.clips) ? m.clips : [];
      } catch {
        list = [];
      }
      if (off) return;
      setClips(list);
      setLoaded(true);
      await Promise.all(
        list.map(async (c) => {
          try {
            const [align, blob] = await Promise.all([
              fetch(base(c.align)).then((r) => r.json()),
              fetch(base(c.audio)).then((r) => r.blob()),
            ]);
            if (off) return;
            const url = URL.createObjectURL(blob);
            urls.push(url);
            prepared.current.set(c.id, { items: alignmentToItems(align, { dropMarks: true }), url });
          } catch (err) {
            console.warn('[showcase] could not prefetch', c.id, err);
          }
        }),
      );
      if (off) return;
      // Load the most likely first tap now, so its media is decoded when the child taps.
      const first = list.find((c) => c.lang === 'ar') ?? list[0];
      const pre = first && prepared.current.get(first.id);
      if (pre && el && !live.current && !srcId.current) {
        el.src = pre.url;
        srcId.current = first.id;
      }
      setReady(true);
    })();
    return () => {
      off = true;
      for (const u of urls) URL.revokeObjectURL(u);
      map.clear();
      srcId.current = '';
    };
  }, [el]);

  // iOS/Safari unlock: the first tap, touch or key anywhere resumes the audio context and plays one
  // silent sample, so the tap that follows can always make sound. Stays until the context runs.
  useEffect(() => {
    if (typeof window === 'undefined') return undefined;
    const opts = { capture: true, passive: true };
    const off = () => {
      for (const e of UNLOCK_EVENTS) window.removeEventListener(e, onGesture, opts);
    };
    function onGesture() {
      if (unlock()) off();
    }
    for (const e of UNLOCK_EVENTS) window.addEventListener(e, onGesture, opts);
    return off;
  }, [unlock]);

  // hotfix-2 (checker): iPhone. The voice is routed through Web Audio (for the lips), and iOS can mute
  // Web Audio with the ring/silent switch. Ask for a 'playback' audio session (Safari 16.4+) while this
  // page is open, like a video would; put it back on leave. Other browsers have no navigator.audioSession.
  useEffect(() => {
    let s = null;
    try {
      s = typeof navigator !== 'undefined' ? navigator.audioSession ?? null : null;
      if (s && s.type === 'auto') s.type = 'playback';
      else s = null;
    } catch {
      s = null;
    }
    return () => {
      try {
        if (s && s.type === 'playback') s.type = 'auto';
      } catch {
        /* not supported */
      }
    };
  }, []);

  const finish = useCallback(
    (why) => {
      const clip = cur.current.clip;
      if (!live.current || !clip) return;
      live.current = false;
      cur.current.clip = null;
      setPlaying('');
      cb.current.onEnd?.(clip, why);
    },
    [],
  );

  useEffect(() => {
    if (!el) return undefined;
    const ended = () => finish('ended');
    el.addEventListener('ended', ended);
    return () => {
      el.removeEventListener('ended', ended);
      el.pause();
    };
  }, [el, finish]);

  const stop = useCallback(() => {
    if (!el || !live.current) return;
    el.pause();
    sink.push(stopMessage(cur.current.sp), performance.now());
    finish('stopped');
  }, [el, sink, finish]);

  // Not async on purpose: nothing may sit between the tap and el.play(). Do not add an await, a
  // fetch or a state update above the "SOUND FIRST" block (tests/showcase-voice-order.test.mjs).
  const speak = useCallback(
    (clip, opts = {}) => {
      if (!el || !clip) return Promise.resolve(false);
      // ---- SOUND FIRST: the tap's permission is still alive ----
      const n = ++cur.current.n;
      const tCall = performance.now();
      const ctxReady = resume(); // resume() the audio context in the same tick, not awaited before play
      const prep = prepared.current.get(clip.id);
      if (srcId.current !== clip.id) {
        el.src = prep ? prep.url : base(clip.audio);
        srcId.current = clip.id;
      } else {
        try {
          el.currentTime = 0;
        } catch {
          /* not seekable yet: it starts from the top anyway */
        }
      }
      let playPromise = null;
      let threw = null;
      try {
        playPromise = el.play();
      } catch (err) {
        threw = err;
      }
      const tPlay = performance.now();
      // ---- everything else, after play() has been called ----
      if (live.current) {
        sink.push(stopMessage(cur.current.sp), tPlay);
        finish('stopped'); // the previous clip: its element source was just replaced
      }
      live.current = true;
      cur.current.clip = clip;
      const sp = `${clip.id}#${n}`;
      cur.current.sp = sp;
      setBlocked(null);
      cb.current.onStart?.(clip);
      setPlaying(clip.id);

      // The lip-sync timeline: the text and `go` the agent sends as it starts to speak. They carry the
      // time of the tap, so a late arrival (a language switch, a slow fetch) still lines up.
      const feed = (items) => {
        if (cur.current.n !== n) return; // another tap came in
        sink.clear();
        for (const msg of timelineMessages(items, sp, { lang: clip.lang })) sink.push(msg, tPlay);
        sink.push(goMessage(sp), tPlay);
      };
      (async () => {
        // The vowel model is chosen when the driver is made: let a new driver exist first. The sound
        // is already playing; the first frames of a language switch are mouth-only by a hair.
        if (clip.lang !== langRef.current) {
          langRef.current = clip.lang;
          setLang(clip.lang);
          await nextFrame();
          await nextFrame();
        }
        let items = prep?.items;
        if (!items) {
          items = alignmentToItems(await fetch(base(clip.align)).then((r) => r.json()), { dropMarks: true });
        }
        feed(items);
      })().catch((err) => console.warn('[showcase] no lip-sync timeline for', clip.id, err));

      return (async () => {
        try {
          if (threw) throw threw;
          if (playPromise && typeof playPromise.then === 'function') await playPromise;
          const tDone = performance.now();
          await ctxReady;
          const state = contextState();
          record({
            id: clip.id, n, ok: true, tap: opts.at ?? tCall, called: tCall, resolved: tDone,
            playMs: tDone - (opts.at ?? tCall), ctx: state, prefetched: !!prep,
          });
          // Safari plays into a suspended context in silence: do not let that pass for success.
          if (cur.current.n === n && state !== 'running' && state !== 'none') {
            console.warn('[showcase] the audio context is', state, 'so there is no sound; asking for a tap');
            setBlocked({ clip, reason: `context-${state}` });
          }
          return true;
        } catch (err) {
          if (cur.current.n !== n) return false; // replaced by a newer tap (AbortError)
          record({ id: clip.id, n, ok: false, tap: opts.at ?? tCall, called: tCall, error: String(err?.name || err), ctx: contextState() });
          console.warn('[showcase] could not play', clip.id, err);
          finish('stopped');
          setBlocked({ clip, reason: String(err?.name || 'error') });
          return false;
        }
      })();
    },
    [el, resume, contextState, sink, finish],
  );

  // The "Tap to turn on sound" button: its own tap runs speak() again, play() first.
  const retry = useCallback(
    (opts = {}) => {
      const b = blockedRef.current;
      unlock(); // synchronous, still inside this tap
      return b ? speak(b.clip, opts) : Promise.resolve(false);
    },
    [speak, unlock],
  );

  // The speaker button: silence what is heard, the lips keep moving (a gain after the analyser).
  const setMuted = useCallback(
    (muted) => {
      mutedRef.current = !!muted;
      if (!muteGain(!!muted) && el) el.muted = !!muted; // no Web Audio: the element's own mute
    },
    [muteGain, el],
  );
  useEffect(() => {
    // A new driver (a language switch) finds the gain where the last one left it; re-apply anyway.
    if (mutedRef.current) muteGain(true);
  }, [lang, muteGain]);

  // For the tests and for debugging a phone: what the audio route looks like right now.
  useEffect(() => {
    window.__voiceState = () => ({ ctx: contextState(), gain: gainValue(), muted: mutedRef.current, src: srcId.current, live: live.current });
    return () => {
      delete window.__voiceState;
    };
  }, [contextState, gainValue]);

  const read = useCallback(() => (live.current ? getLipsync() : null), [getLipsync]);
  const getLevel = useCallback(() => read()?.level ?? 0, [read]);

  return { clips, loaded, ready, playing, blocked, speak, retry, stop, setMuted, getLipsync: read, getLevel, isLive: () => live.current };
}
