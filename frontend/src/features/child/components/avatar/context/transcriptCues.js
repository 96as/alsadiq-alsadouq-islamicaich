// Free cues from the agent's streaming transcript (SPEC-EXPERIENCE 5.7), plus the text
// normalisation of section 8.3 that the backend classifiers share. Pure: no DOM, no three.js.
//
//   greet     the salam in the first 40 characters of the first agent message of the session
//   goodbye   a farewell phrase anywhere in an agent message
//   question  a finished agent message that ends with ? or the Arabic question mark
//
// Nothing here is scripture; the phrases are everyday greetings and farewells.

const DIACRITICS = /[ؗ-ًؚ-ْٰـ]/g; // diacritics and tatweel
const LETTER_MAP = { 'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ٱ': 'ا', 'ى': 'ي', 'ة': 'ه', 'ؤ': 'و', 'ئ': 'ي' };
const LETTERS = /[أإآٱىةؤئ]/g;
const TOKEN = /[\p{L}\p{N}_']+/gu;

/** Section 8.3: strip diacritics and tatweel, fold letter forms, straighten quotes, lowercase. */
export function normalizeText(text) {
  return String(text ?? '')
    .replace(DIACRITICS, '')
    .replace(LETTERS, (c) => LETTER_MAP[c])
    .replace(/[‘’]/g, "'")
    .toLowerCase()
    .replace(/\s+/g, ' ')
    .trim();
}

/** Tokens (runs of letters, digits and apostrophes) of already-normalised text. */
export function tokens(normalized) {
  return normalized.match(TOKEN) ?? [];
}

/** The normalised text with every punctuation run turned into one space, padded for phrase matching. */
function padded(normalized) {
  return ` ${tokens(normalized).join(' ')} `;
}

const isArabicPhrase = (p) => /[؀-ۿ]/.test(p);

const SALAM = ['السلام عليكم', 'سلام عليكم', 'assalam', 'salam', 'peace be upon you'].map(normalizeText);
const GOODBYE = [
  'مع السلامة', 'في أمان الله', 'إلى اللقاء', 'نشوفك',
  'bye', 'goodbye', 'see you later', 'see you soon', 'see you tomorrow', 'see you next', 'take care',
].map(normalizeText);

/** A phrase matches on token boundaries; an Arabic phrase also matches after the clitic و. */
function hasPhrase(pad, phrase) {
  if (pad.includes(` ${phrase} `)) return true;
  return isArabicPhrase(phrase) && pad.includes(` و${phrase} `);
}

/** True if the first `within` characters of the message carry a salam. */
export function hasGreeting(text, within = 40) {
  const head = normalizeText(text).slice(0, within);
  for (const s of SALAM) if (head.includes(s)) return true;
  return false;
}

/** True if the message carries a farewell. "I see you're trying" and "take care of it" do not count. */
export function hasFarewell(text) {
  const pad = padded(normalizeText(text));
  for (const g of GOODBYE) {
    if (!hasPhrase(pad, g)) continue;
    if (g === 'take care' && pad.includes(' take care of ')) continue;
    return true;
  }
  return false;
}

/** True if the message ends with a question mark (Latin or Arabic), ignoring closing quotes. */
export function endsWithQuestion(text) {
  return /[?؟]["'”»)\]\s]*$/.test(String(text ?? '').trim());
}

/**
 * Tracks the agent's messages and counts the cues. The director compares the counters with what
 * it has already seen, so a cue is never lost between frames and never fires twice.
 *   msgCount     agent messages that have started (0 until the first transcript chunk)
 *   greetSeq     +1 when the FIRST message of the session carries a salam
 *   goodbyeSeq   +1 for each message that carries a farewell (once per message)
 *   question     the latest finished agent message ended with a question mark
 */
export function createCueTracker() {
  const state = { msgCount: 0, greetSeq: 0, goodbyeSeq: 0, question: false };
  let currentId = null;
  let greetChecked = false;
  let goodbyeFor = null;
  return {
    state,
    /**
     * @param {string} text the message so far (or final)
     * @param {{id?: string, final?: boolean}} [info] id identifies the stream so chunks of one
     *   message are not counted twice
     */
    onAgentText(text, { id = 'm', final = false } = {}) {
      if (id !== currentId) {
        currentId = id;
        state.msgCount += 1;
        state.question = false; // a new message started: the old question is no longer pending
      }
      if (!greetChecked && state.msgCount === 1 && text.length > 0) {
        // The first 40 characters decide, so wait until there are enough (or the message ends).
        if (text.length >= 40 || final || hasGreeting(text)) {
          greetChecked = true;
          if (hasGreeting(text)) state.greetSeq += 1;
        }
      }
      if (goodbyeFor !== id && hasFarewell(text)) {
        goodbyeFor = id;
        state.goodbyeSeq += 1;
      }
      if (final) state.question = endsWithQuestion(text);
    },
    reset() {
      state.msgCount = 0;
      state.greetSeq = 0;
      state.goodbyeSeq = 0;
      state.question = false;
      currentId = null;
      greetChecked = false;
      goodbyeFor = null;
    },
  };
}
