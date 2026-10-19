/**
 * Pure helpers for Arabic source text on a card (cards-spec (05) sections 1 and 3).
 * No React and no scripture in this file: the code points below are written as escapes.
 */

// The KFGQPC font draws these three legacy open-tanween code points; Amiri Quran does not.
// At display time only they are mapped to the new Unicode code points the fallback font draws.
// cards-spec (05) review: the KFGQPC v18 encoding reuses three marks for open tanween. The pairing is the spec's
// (r4 section 2.6: same counts and same glyph as the v3.0 font), even though the old names suggest otherwise.
const FALLBACK_MARK_MAP = {
  '\u0657': '\u08F0', // inverted damma (v18) -> ARABIC OPEN FATHATAN
  '\u065E': '\u08F1', // fatha with two dots (v18) -> ARABIC OPEN DAMMATAN
  '\u0656': '\u08F2', // subscript alef (v18) -> ARABIC OPEN KASRATAN
};

/**
 * What to put on screen for stored Arabic `text`. With the unmodified KFGQPC font it is the text as is. While
 * the fallback font (Amiri Quran) is in use the three legacy marks are mapped. Returns a new string; the
 * stored and received text is never changed, so never use this for copy or for anything sent to the server.
 */
export function toDisplayArabic(text, usingFallbackFont) {
  const s = typeof text === 'string' ? text : '';
  if (!usingFallbackFont) return s;
  return s.replace(/[\u0656\u0657\u065E]/g, (ch) => FALLBACK_MARK_MAP[ch]);
}

// Same shape the agent's retrieval.py uses: {{verse:S:A}} (spaces tolerated).
const VERSE_MARKER = /\{\{\s*verse\s*:\s*(\d{1,3})\s*:\s*(\d{1,3})\s*\}\}/g;

/**
 * Splits `text` into [{ type: 'text', value }, { type: 'verse', surah, ayah, ref }] so a card can render each
 * {{verse:S:A}} marker as a reference chip. The raw marker never appears in any segment.
 */
export function splitVerseMarkers(text) {
  const s = typeof text === 'string' ? text : '';
  const out = [];
  let last = 0;
  for (const m of s.matchAll(VERSE_MARKER)) {
    if (m.index > last) out.push({ type: 'text', value: s.slice(last, m.index) });
    const surah = Number(m[1]);
    const ayah = Number(m[2]);
    out.push({ type: 'verse', surah, ayah, ref: `${surah}:${ayah}` });
    last = m.index + m[0].length;
  }
  if (last < s.length) out.push({ type: 'text', value: s.slice(last) });
  return out;
}

/** True when `text` still holds a (possibly malformed) marker-looking piece after the valid ones are removed. */
export function hasBrokenMarker(text) {
  return /\{\{|\}\}/.test(String(text ?? '').replace(VERSE_MARKER, ''));
}

/** Every distinct { surah, ayah } marker in `text`, in order. */
export function verseMarkerRefs(text) {
  const seen = new Set();
  return splitVerseMarkers(text).filter((p) => {
    if (p.type !== 'verse' || seen.has(p.ref)) return false;
    seen.add(p.ref);
    return true;
  });
}

const pad3 = (n) => String(n).padStart(3, '0');

/** `<base>/SSSAAA.mp3`, the file name the knowledge bank uses for a verse recitation (static/quran/SSSAAA.mp3). */
export function quranAudioUrl(base, surah, ayah) {
  return `${String(base).replace(/\/+$/, '')}/${pad3(surah)}${pad3(ayah)}.mp3`;
}
