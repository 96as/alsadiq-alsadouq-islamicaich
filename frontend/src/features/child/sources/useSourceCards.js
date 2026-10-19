// cards-spec (05): normalizeReference follows the section 2 payload contract (rewritten from the verse/hadith-only version).
import { useCallback, useMemo, useReducer } from 'react';
import { EMPTY_SESSION, sessionCardsReducer } from './sessionCards';
import { safeSourceUrl, safeTranslationUrl, sourceHostForType } from './safeUrl';
import { HAFS_AYAH_COUNTS } from './ayahCounts';
import { hasBrokenMarker, verseMarkerRefs } from './quranText';
import { normalizeGrade, sourceHeader } from './sourceLabels';

export const MAX_SOURCE_CARDS = 3; // hk-14: the same number as sessionCards MAX_VISIBLE (a test keeps them equal)

// cards-spec (05) section 2: exactly these keys survive; everything else is dropped.
const KEYS = [
  'id', 'type', 'kind', 'arabic_text', 'english_text', 'translation_name', 'translation_source_url',
  'surah', 'ayah', 'surah_name', 'audio_url', 'audio_credit', 'audio_source_url', 'book', 'number', 'grade', 'grader',
  'source_site', 'source_url', 'content_level', 'value', 'title', 'explanation', 'explanation_lang',
  'explanation_origin', 'disagreement_note', 'verification_status', 'verse_refs',
];

// Text that is shown verbatim: never trimmed, re-cased or otherwise touched (HadeethEnc terms, r1 section 2.7).
const VERBATIM_KEYS = ['arabic_text', 'english_text'];
const NUMERIC_KEYS = ['id', 'surah', 'ayah', 'number'];

export const CARD_TYPES = ['verse', 'hadith', 'tafsir', 'faq', 'term', 'aqidah', 'fiqh', 'sirah'];
const SCRIPTURE_TYPES = ['verse', 'hadith'];

const isPosInt = (s) => /^\d+$/.test(s) && Number.isSafeInteger(Number(s)) && Number(s) >= 1;
const validAyah = (surah, ayah) => (
  Number.isInteger(surah) && Number.isInteger(ayah) && surah >= 1 && surah <= HAFS_AYAH_COUNTS.length
  && ayah >= 1 && ayah <= HAFS_AYAH_COUNTS[surah - 1]
);

/**
 * hk/01 resolves the {{verse:S:A}} markers of a FAQ item on the server: `arabic_text` is the plain-text fallback and
 * `segments` is the ordered rendering ({type:'text', text} | {type:'verse', surah, ayah, audio_url}). Returns the
 * segments in the card's shape, [] when there are none, or null when any piece is invalid (the card is then dropped,
 * like a broken marker). A text piece may never hold a brace, a verse piece must be a real verse (Hafs counts).
 */
export function normalizeSegments(raw) {
  if (raw === undefined || raw === null) return [];
  if (!Array.isArray(raw)) return null;
  const out = [];
  for (const s of raw) {
    if (!s || typeof s !== 'object') return null;
    if (s.type === 'text') {
      if (typeof s.text !== 'string' || /\{\{|\}\}/.test(s.text)) return null;
      if (s.text) out.push({ type: 'text', value: s.text });
    } else if (s.type === 'verse') {
      const surah = Number(s.surah);
      const ayah = Number(s.ayah);
      if (!validAyah(surah, ayah)) return null;
      const seg = { type: 'verse', surah, ayah, ref: `${surah}:${ayah}` };
      if (typeof s.audio_url === 'string' && /^https?:\/\//i.test(s.audio_url.trim())) seg.audio_url = s.audio_url.trim();
      out.push(seg);
    } else {
      return null;
    }
  }
  return out;
}

/**
 * Whitelists a `reference` payload (cards-spec (05) section 2) and returns the card, or null when it must not
 * render. Rules, in order:
 *  - only the whitelisted keys, only strings (numbers only for id, surah, ayah, number);
 *  - `type` is one of the eight card types and `kind` matches it (scripture for verse and hadith, else source_excerpt);
 *  - `arabic_text` and `source_url` are required, and the `source_url` host must be approved for the type;
 *    `source_site` is set to that host (a payload `source_site` that disagrees drops the card);
 *  - verse: a valid surah and ayah (bounded by the Hafs counts); hadith: book, number, grader, and grade sahih;
 *  - `english_text` only survives with a `translation_name` (a translation link only on an approved host);
 *  - a {{verse:S:A}} marker must be valid, a broken one drops the card; content level C needs a disagreement note;
 *  - the type and site pair must have a header (sourceLabels.sourceHeader), otherwise nothing is shown.
 * The text fields are copied verbatim (no trimming) so the card never alters scripture or a translation.
 */
export function normalizeReference(raw) {
  if (!raw || typeof raw !== 'object') return null;
  const out = {};
  for (const k of KEYS) {
    const v = raw[k];
    if (k === 'verse_refs') continue;
    if (typeof v === 'string' || (NUMERIC_KEYS.includes(k) && typeof v === 'number' && Number.isFinite(v))) {
      const s = String(v);
      if (!s.trim()) continue;
      out[k] = VERBATIM_KEYS.includes(k) ? s : s.trim();
    }
  }
  if (!CARD_TYPES.includes(out.type)) return null;
  if (out.kind !== (SCRIPTURE_TYPES.includes(out.type) ? 'scripture' : 'source_excerpt')) return null;
  if (!out.id || !out.arabic_text || !out.source_url) return null;

  // Source site: derived from the URL host for this type, never taken on trust from the payload.
  const site = sourceHostForType(out.type, out.source_url);
  if (!site) return null;
  if (out.source_site && out.source_site.toLowerCase() !== site) return null;
  out.source_site = site;

  if (out.type === 'verse') {
    if (!out.surah || !out.ayah || !isPosInt(out.surah) || !isPosInt(out.ayah)) return null;
    if (!validAyah(Number(out.surah), Number(out.ayah))) return null;
  } else {
    delete out.surah;
    delete out.ayah;
    delete out.audio_url; // audio_url is verse-only; audio_credit/audio_source_url stay (section 1.6: a card whose
    // verse `segments` carry audio still needs the credit, once per card, even when it is not itself a verse)
  }
  if (out.type === 'hadith') {
    if (!out.book || !out.number || !out.grader) return null;
    if (normalizeGrade(out.grade) !== 'sahih') return null; // the backend serves only sahih; this is the second guard
  }

  // Translation rule: no translation_name means no English text at all.
  if (!out.translation_name) delete out.english_text;
  if (out.translation_source_url) {
    const link = safeTranslationUrl(out.translation_source_url);
    if (link) out.translation_source_url = link;
    else delete out.translation_source_url;
  }

  // cards-spec (05) section 1.6: the recitation credit's own link. An unsafe/unapproved host is dropped here, not
  // passed through as a trusted href; recitationCreditParts (sourceLabels.js) falls back to the fixed
  // everyayah.com URL only when this field is absent.
  if (out.audio_source_url) {
    const link = safeSourceUrl(out.audio_source_url);
    if (link) out.audio_source_url = link;
    else delete out.audio_source_url;
  }

  // {{verse:S:A}} markers: every one must be a real verse, and no half-broken marker may remain.
  if (hasBrokenMarker(out.arabic_text)) return null;
  const refs = verseMarkerRefs(out.arabic_text);
  if (refs.some((r) => !validAyah(r.surah, r.ayah))) return null;
  if (refs.length) out.marker_refs = refs.map((r) => r.ref);
  // The server-resolved form of the same markers (the payload no longer carries a raw marker).
  const segs = normalizeSegments(raw.segments);
  if (segs === null) return null;
  if (segs.length) {
    out.segments = segs;
    if (!out.marker_refs) out.marker_refs = [...new Set(segs.filter((s) => s.type === 'verse').map((s) => s.ref))];
  }
  // `verse_refs` is accepted only as strings "S:A" that are valid; it never adds anything the markers do not show.
  if (Array.isArray(raw.verse_refs)) {
    const ok = raw.verse_refs.filter((r) => typeof r === 'string' && /^\d{1,3}:\d{1,3}$/.test(r.trim())
      && validAyah(...r.trim().split(':').map(Number)));
    if (ok.length) out.verse_refs = ok.map((r) => r.trim());
  }

  if (out.content_level && !['A', 'B', 'C'].includes(out.content_level.toUpperCase())) delete out.content_level;
  if (out.content_level) out.content_level = out.content_level.toUpperCase();
  if (out.content_level === 'C' && !out.disagreement_note) return null;
  if (out.content_level !== 'C') delete out.disagreement_note;

  if (out.explanation_lang && !['ar', 'en'].includes(out.explanation_lang)) delete out.explanation_lang;
  if (out.verification_status && !['seeded', 'reviewed'].includes(out.verification_status)) delete out.verification_status;
  delete out.explanation_origin; // never read: the card always labels an explanation as our own words, not the source's

  if (!sourceHeader(out, 'en')) return null; // a type and site pair with no label is not rendered
  return out;
}

/**
 * Source cards pushed by the agent over the LiveKit `reference` topic. `cards` = the visible ones (max 3, newest
 * first, de-duplicated by id); `history` = every valid card of this session (newest first, cap 20). Invalid payloads
 * are dropped silently (console.warn in DEV only). hk-14: dismiss(id) closes one card, reopen() shows the whole
 * history again (those cards stay until closed, see `pinned`), clearReferences() resets everything.
 *
 * @returns {{ cards: object[], history: object[], pinned: string[], addReference: Function, dismiss: Function,
 *   reopen: Function, clearReferences: Function }}
 */
export default function useSourceCards() {
  const [state, dispatch] = useReducer(sessionCardsReducer, EMPTY_SESSION);

  const addReference = useCallback((payload) => {
    const card = normalizeReference(payload);
    if (!card) {
      if (import.meta.env.DEV) console.warn('Dropped invalid reference payload', payload);
      return;
    }
    dispatch({ type: 'add', card });
  }, []);
  const dismiss = useCallback((id) => dispatch({ type: 'dismiss', id }), []);
  const reopen = useCallback(() => dispatch({ type: 'reopen' }), []);
  const clearReferences = useCallback(() => dispatch({ type: 'clear' }), []);

  const cards = useMemo(
    () => state.visible.map((id) => state.history.find((c) => c.id === id)).filter(Boolean),
    [state.visible, state.history],
  );
  return { cards, history: state.history, pinned: state.pinned, addReference, dismiss, reopen, clearReferences };
}
