// Builds the lk.lipsync messages (see timelineSync.js) from a character alignment. The agent does
// the same in Python (backend/conversation/agent/lipsync_timeline.py); this copy serves the lab,
// the avatar preview and the offline evaluation, which replay an alignment without an agent.
// Pure functions, no DOM.

const isMark = (c) => (c >= 'ً' && c <= 'ْ') || c === 'ٰ';

/** At most this many characters in one message (the data channel packet limit is the reason). */
export const MAX_ITEMS_PER_MESSAGE = 120;

/**
 * @param {{characters?: string[], chars?: string[], starts: number[], ends: number[]}} alignment
 *   times in seconds from the first audio sample
 * @param {{dropMarks?: boolean}} [opts] dropMarks removes the short-vowel marks and gives their time
 *   to the letter before them: the form a reply has live, where the text is written without them
 * @returns {Array<[string, number, number]>} [char, startMs, durMs]
 */
export function alignmentToItems(alignment, { dropMarks = false } = {}) {
  const chars = alignment.characters ?? alignment.chars;
  const { starts, ends } = alignment;
  const items = [];
  for (let i = 0; i < chars.length; i++) {
    const ch = chars[i];
    const a = Math.round(starts[i] * 1000);
    const b = Math.round(ends[i] * 1000);
    if (dropMarks && isMark(ch) && items.length) {
      const last = items[items.length - 1];
      last[2] = Math.max(last[2], b - last[1]);
      continue;
    }
    items.push([ch, a, Math.max(0, b - a)]);
  }
  return items;
}

/** One speech as a list of messages: the characters in packets, none of them started yet. */
export function timelineMessages(items, sp, { lang = 'ar', chunk = MAX_ITEMS_PER_MESSAGE } = {}) {
  const out = [];
  for (let k = 0, seq = 0; k < items.length; k += chunk, seq++) {
    out.push({ v: 1, sp, seq, lang, t: items.slice(k, k + chunk) });
  }
  return out;
}

export const goMessage = (sp) => ({ v: 1, sp, go: 1 });
export const stopMessage = (sp) => ({ v: 1, sp, stop: 1 });
