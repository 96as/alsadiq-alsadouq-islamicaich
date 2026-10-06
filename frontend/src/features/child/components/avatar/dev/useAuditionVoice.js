// Dev only (imported by the preview pages, which are only mounted when import.meta.env.DEV).
// Plays one of the audition clips in frontend/dev-audio/ (gitignored, never committed) through an
// audio element and gives back getLipsync(), so the avatar's mouth follows it exactly as it follows
// the agent's voice in a session.
//
// The Arabic evaluation clips (dev-audio/eval-ar/) come first. With `timeline` on, the clip's
// ElevenLabs alignment is delivered to the same sink the live session uses (lk.lipsync), so the
// mouth is timed by the text and coloured by the audio; with it off the mouth is audio only.
import { useCallback, useEffect, useRef, useState } from 'react';
import { assetUrl } from '../../../../../utils/assetUrl.js';
import useVisemes from '../lipsync/useVisemes.js';
import { DEFAULT_EVAL_CLIP, EVAL_CLIPS, loadAlignment, newTimelineSink, replayTimeline, stopTimeline } from '../lipsync/dev/evalClips.js';

const CLIP_URLS = import.meta.glob('/dev-audio/*.mp3', { query: '?url', import: 'default', eager: true });
const LINE_FILES = import.meta.glob('/dev-audio/lines.json', { eager: true, import: 'default' });
const LINES = Object.values(LINE_FILES)[0] ?? {};

const MP3_CLIPS = Object.entries(CLIP_URLS)
  .map(([path, url]) => {
    const name = path.split('/').pop().replace(/\.mp3$/, '');
    const lineKey = name.match(/line\d+$/)?.[0];
    return { name, url: assetUrl(url), text: LINES[lineKey]?.text ?? '', kind: LINES[lineKey]?.kind ?? '', lang: /_ar_|abdullah/.test(name) ? 'ar' : 'en' };
  })
  .sort((a, b) => a.name.localeCompare(b.name));

export const AUDITION_CLIPS = [...EVAL_CLIPS, ...MP3_CLIPS];

/** An Arabic clip first: that is what the child hears. */
export const DEFAULT_CLIP =
  DEFAULT_EVAL_CLIP ??
  MP3_CLIPS.find((c) => c.name.startsWith('abdullah_eleven_multilingual_v2_line01')) ??
  AUDITION_CLIPS[0];

const nextFrame = () => new Promise((resolve) => requestAnimationFrame(() => resolve()));

export default function useAuditionVoice({ timeline: timelineStart = true } = {}) {
  const [el] = useState(() => (typeof Audio === 'undefined' ? null : new Audio()));
  const [sink] = useState(newTimelineSink);
  const [lang, setLang] = useState(DEFAULT_CLIP?.lang ?? 'ar');
  const [timelineOn, setTimelineOn] = useState(timelineStart);
  const { getLipsync, resume } = useVisemes(el, { lang, timeline: sink });
  const [playing, setPlaying] = useState('');
  const spRef = useRef('');
  const lastPlayRef = useRef(0);

  useEffect(() => {
    if (!el) return undefined;
    const done = () => {
      setPlaying('');
      sink.agentState(false, performance.now()); // the speech is over once this has held for endStateMs
    };
    el.addEventListener('ended', done);
    el.addEventListener('pause', done);
    return () => {
      el.removeEventListener('ended', done);
      el.removeEventListener('pause', done);
      el.pause();
    };
  }, [el, sink]);

  const speak = useCallback(
    async (clip = DEFAULT_CLIP) => {
      if (!el || !clip) return false;
      const clipLang = clip.lang ?? 'en';
      if (clipLang !== lang) {
        // The vowel mode is chosen when the driver is made: let the new driver exist first.
        setLang(clipLang);
        await nextFrame();
        await nextFrame();
      }
      await resume();
      // eslint-disable-next-line react-hooks/immutability -- a media element is meant to be driven
      el.src = clip.url;
      el.currentTime = 0;
      // Every play is a new speech, as every reply of the agent is.
      sink.clear();
      const sp = `${clip.name}#${++lastPlayRef.current}`;
      spRef.current = sp;
      if (timelineOn && clip.alignPath) {
        const alignment = await loadAlignment(clip);
        // The agent sends the text and `go` as it starts to speak, and the sound follows.
        replayTimeline(sink, alignment, sp, performance.now(), clipLang);
      }
      try {
        sink.agentState(true, performance.now());
        await el.play();
        setPlaying(clip.name);
        return true;
      } catch (err) {
        console.warn('[audition] could not play', clip.name, err);
        return false;
      }
    },
    [el, resume, lang, sink, timelineOn],
  );
  const stop = useCallback(() => {
    if (el) el.pause();
    stopTimeline(sink, spRef.current, performance.now());
  }, [el, sink]);

  return { clips: AUDITION_CLIPS, speak, stop, playing, getLipsync, timelineOn, setTimelineOn, timeline: sink };
}
