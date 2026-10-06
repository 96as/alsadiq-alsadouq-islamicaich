// The timeline replay of the evaluation (--mode hybrid): turns a clip's own alignment into the
// lk.lipsync messages the agent would send, and applies the stress runs.
//
//   none   data at t = -300 ms, go at t = 0 (the clip's first sample)
//   late   go arrives 150 ms after the first letter starts
//   stall  150 ms of silence is cut into the audio in the middle of a word; the timeline does not
//          know (the clip's labels move with the audio, the messages are the original ones)
//   stale  another line's timeline is delivered first, with no go; it must never be shown
//
// The hybrid is fed the alignment in its live form: the short-vowel marks are dropped and their
// time goes to the letter (the text a reply has live is written without them).

import {
  alignmentToItems,
  goMessage,
  timelineMessages,
} from '../../src/features/child/components/avatar/lipsync/timelineMessages.js';
import { loadTestset } from './gt.mjs';

const isMark = (c) => (c >= 'ً' && c <= 'ْ') || c === 'ٰ';
const isSpace = (c) => c === ' ' || c === ' ';

export const STALL_MS = 150;

function firstLetterStart(clip) {
  for (let i = 0; i < clip.chars.length; i++) {
    if (!isSpace(clip.chars[i]) && !isMark(clip.chars[i])) return clip.starts[i];
  }
  return 0;
}

/** Cut STALL_MS of silence into the middle of a word of the clip (audio and labels move together). */
function insertStall(clip) {
  const n = clip.chars.length;
  const isLetter = (i) => i >= 0 && i < n && !isSpace(clip.chars[i]) && !isMark(clip.chars[i]) && !/[.,!?،؛؟]/.test(clip.chars[i]);
  const mid = Math.floor(n / 2);
  let at = -1;
  for (let d = 0; d < n && at < 0; d++) {
    for (const m of [mid + d, mid - d]) {
      if (m > 1 && m < n - 2 && isLetter(m - 1) && isLetter(m) && isLetter(m + 1) && !isMark(clip.chars[m])) {
        at = m;
        break;
      }
    }
  }
  if (at < 0) return;
  const T = clip.starts[at];
  const cut = Math.round(T * clip.sr);
  const gap = Math.round((STALL_MS / 1000) * clip.sr);
  const pcm = new Float32Array(clip.pcm.length + gap);
  pcm.set(clip.pcm.subarray(0, cut), 0);
  pcm.set(clip.pcm.subarray(cut), cut + gap);
  clip.pcm = pcm;
  for (let i = 0; i < n; i++) {
    if (clip.starts[i] >= T) clip.starts[i] += STALL_MS / 1000;
    if (clip.ends[i] > T) clip.ends[i] += STALL_MS / 1000;
  }
}

/**
 * @param {object} clip from gt.mjs loadClip (the stall run changes its audio and labels)
 * @param {{stress?: string}} args
 * @returns {Array<{t: number, msg: object}>} the events for analyseBuffer
 */
export function makeTimeline(clip, args = {}) {
  const stress = args.stress || 'none';
  const items = alignmentToItems(clip, { dropMarks: true });
  const sp = clip.name;
  const events = [];
  if (stress === 'stale') {
    const lines = loadTestset().lines;
    const k = lines.findIndex((l) => l.id === clip.id);
    const other = lines[(k + 3) % lines.length];
    // Any other line's text will do; it only has to differ from this one.
    const fake = timelineMessages(
      [...other.text].reduce((acc, ch, i) => (acc.push([ch, i * 60, 60]), acc), []),
      `stale-${other.id}`,
    );
    for (const msg of fake) events.push({ t: -0.5, msg });
  }
  if (stress === 'stall') insertStall(clip);
  for (const msg of timelineMessages(items, sp)) events.push({ t: -0.3, msg });
  const goAt = stress === 'late' ? firstLetterStart(clip) + 0.15 : 0;
  events.push({ t: goAt, msg: goMessage(sp) });
  return events;
}
