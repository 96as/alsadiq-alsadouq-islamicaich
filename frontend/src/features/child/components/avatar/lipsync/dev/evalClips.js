// Dev only (imported by the lab and the avatar preview, which are only mounted when
// import.meta.env.DEV). The evaluation clips in frontend/dev-audio/eval-ar/ and eval-en/ (gitignored,
// never committed) and the replay of their ElevenLabs alignment as the lk.lipsync messages the agent
// would send, so the text-timed mouth can be seen and heard without an agent or a session.
//
//   arNN.plain.wav   the line without short-vowel marks: the form a reply has live
//   arNN.diac.wav    the same line fully voweled
//   enNN.wav         an English line (the timeline then gives the lip closures only)
//   <name>.align.json   {characters, starts, ends} in seconds from the first sample
import { TimelineSync } from '../timelineSync.js';
import { alignmentToItems, goMessage, stopMessage, timelineMessages } from '../timelineMessages.js';

const WAV_URLS = import.meta.glob(['/dev-audio/eval-ar/*.wav', '/dev-audio/eval-en/*.wav'], {
  query: '?url',
  import: 'default',
  eager: true,
});
const ALIGN_LOADERS = import.meta.glob(['/dev-audio/eval-ar/*.align.json', '/dev-audio/eval-en/*.align.json'], {
  import: 'default',
});

/** Arabic first, plain before voweled, in line order, then English. `id` is "ar21.plain" or "en01". */
export const EVAL_CLIPS = Object.entries(WAV_URLS)
  .map(([path, url]) => {
    const id = path.split('/').pop().replace(/\.wav$/, '');
    const lang = path.includes('/eval-en/') ? 'en' : 'ar';
    return {
      name: id,
      url,
      text: '',
      kind: `eval-${lang}`,
      lang,
      alignPath: path.replace(/\.wav$/, '.align.json'),
    };
  })
  .sort((a, b) => {
    const rank = (c) => (c.lang === 'en' ? 2 : c.name.endsWith('.plain') ? 0 : 1);
    return rank(a) - rank(b) || a.name.localeCompare(b.name, 'en', { numeric: true });
  });

/** The clip to start on: line 21 (a held-out line), plain. */
export const DEFAULT_EVAL_CLIP = EVAL_CLIPS.find((c) => c.name === 'ar21.plain') ?? EVAL_CLIPS[0] ?? null;

/** The alignment of a clip, or null (a clip with no alignment plays audio only). */
export async function loadAlignment(clip) {
  const load = clip && ALIGN_LOADERS[clip.alignPath];
  if (!load) return null;
  try {
    return await load();
  } catch {
    return null;
  }
}

/** The text of the clip (what the alignment says), for the page to show. */
export function alignmentText(alignment) {
  return alignment ? (alignment.text ?? (alignment.characters ?? alignment.chars ?? []).join('')) : '';
}

/**
 * Deliver one speech to `sync` the way the agent does: the characters, then `go`. Call it just
 * before the audio starts (the agent sends `go` as it starts to speak; the sound follows).
 * @param {TimelineSync} sync
 * @param {object} alignment from loadAlignment
 * @param {string} sp speech id
 * @param {number} [nowMs]
 * @param {'ar'|'en'} [lang] the language the agent would tag the speech with
 */
export function replayTimeline(sync, alignment, sp, nowMs = performance.now(), lang = 'ar') {
  if (!sync || !alignment) return false;
  const items = alignmentToItems(alignment, { dropMarks: true });
  for (const msg of timelineMessages(items, sp, { lang })) sync.push(msg, nowMs);
  sync.push(goMessage(sp), nowMs);
  return true;
}

/**
 * The same delivery as events for the offline analysis (analyseBuffer): the characters 300 ms before
 * the first sample and `go` at it, as the evaluation does (scripts/lipsync-eval/timelines.mjs).
 */
export function replayEvents(alignment, sp, lang = 'ar') {
  if (!alignment) return null;
  const items = alignmentToItems(alignment, { dropMarks: true });
  const events = timelineMessages(items, sp, { lang }).map((msg) => ({ t: -0.3, msg }));
  events.push({ t: 0, msg: goMessage(sp) });
  return events;
}

/** Tell `sync` the speech was cut off. */
export function stopTimeline(sync, sp, nowMs = performance.now()) {
  if (sync) sync.push(stopMessage(sp), nowMs);
}

export const newTimelineSink = () => new TimelineSync();
