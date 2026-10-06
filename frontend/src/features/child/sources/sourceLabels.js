// cards-spec (05) section 1: every label on a source card comes from this file. They are constants in the
// UI and never come from the payload. The parent view (task 04) imports the same file so the wording
// stays identical. Pure functions only (no React), so scripts/check-source-cards.mjs runs them as they are.
import { surahName } from './surahNames';
import { safeSourceUrl, safeTranslationUrl } from './safeUrl';

/** The tier-2 header, exactly as the spec words it. */
export const EXPLANATION_HEADER = {
  en: 'In simple words, for children (our explanation, not the source\'s words):',
  ar: 'بكلمات بسيطة للأطفال (شرحنا، وليس نص المصدر):',
};

/**
 * Shown under a verse's play button (section 1.6, organiser ruling 2026-10-05: everyayah.com is accepted
 * "with the source name and link stated clearly"). A payload `audio_credit` overrides it; this is the fallback
 * for a card that has audio but an empty `audio_credit`. Exact wording, both languages.
 */
export const RECITATION_CREDIT = {
  en: 'Recitation: Mahmoud Khalil Al-Husary, everyayah.com',
  ar: 'التلاوة: محمود خليل الحصري، everyayah.com',
};

/** The recitation credit's fallback link, used when the payload sends no (safe) `audio_source_url`. */
export const RECITATION_AUDIO_SOURCE_URL = 'https://everyayah.com/';

export const SOURCE_LABELS = {
  en: {
    explanationHeader: EXPLANATION_HEADER.en,
    fromQuran: 'From the Quran:',
    fromBook: 'From {book}:',
    says: '{source} says:',
    tafsirEncyclopedia: 'Tafsir encyclopedia (al-Durar al-Saniyya) says:',
    bookSays: '{book} says:',
    fromCreed: 'From the Creed encyclopedia (al-Durar al-Saniyya):',
    fromFiqh: 'From the Fiqh encyclopedia (al-Durar al-Saniyya):',
    fromHistory: 'From the History encyclopedia (al-Durar al-Saniyya):',
    fromFaq: 'From Bayyinat (Questions and Answers about Islam):',
    fromTerm: 'From the Al-Jamhara dictionary:',
    pill: {
      verse: 'Verse', hadith: 'Hadith', tafsir: 'Tafsir', faq: 'Q&A', term: 'Term', aqidah: 'Creed', fiqh: 'Fiqh', sirah: 'Seerah',
    },
    surahLine: 'Surah {surah}:{ayah}',
    translationVia: 'Translation: {name} via Quranpedia',
    translation: 'Translation: {name}',
    translationHadeeth: 'Translation: HadeethEnc.com',
    captionQuranpedia: 'Text: King Fahd Complex (KFGQPC), via Quranpedia',
    captionComplex: 'Text: King Fahd Complex (KFGQPC)',
    reviewed: 'Checked against the source by our team',
    reviewedTitle: 'Not reviewed by a scholar',
    fiqhNote: 'General information, not a ruling. Ask your parents or a scholar.',
    scholarsDiffer: 'Scholars may differ:',
    viewOn: 'View on {site}',
    viewSource: 'View source',
    newTab: ' (opens in a new tab)',
    sources: 'Sources',
    closeCard: 'Close card',
    sessionSources: 'Sources this session ({n})',
    sourcesEmpty: 'Verses and hadith that Al-Sadiq mentions will appear here.',
    audio: {
      listen: 'Listen to the recitation', playing: 'Playing recitation', loading: 'Loading...', unavailable: 'Recitation unavailable',
      play: 'Play recitation', pause: 'Pause recitation',
    },
    cite: {
      graded: 'graded {grade} ({grader})', gradedNoGrader: 'graded {grade}', source: 'source: {site}', sahih: 'sahih',
    },
  },
  ar: {
    explanationHeader: EXPLANATION_HEADER.ar,
    fromQuran: 'من القرآن الكريم:',
    fromBook: 'من {book}:',
    says: '{source} يقول:',
    tafsirEncyclopedia: 'موسوعة التفسير (الدرر السنية) تقول:',
    bookSays: '{book} يقول:',
    fromCreed: 'من الموسوعة العقدية (الدرر السنية):',
    fromFiqh: 'من الموسوعة الفقهية (الدرر السنية):',
    fromHistory: 'من الموسوعة التاريخية (الدرر السنية):',
    fromFaq: 'من «بينات: أسئلة وأجوبة عن الإسلام»:',
    fromTerm: 'من معجم الجمهرة:',
    pill: {
      verse: 'آية', hadith: 'حديث', tafsir: 'تفسير', faq: 'سؤال وجواب', term: 'مصطلح', aqidah: 'عقيدة', fiqh: 'فقه', sirah: 'سيرة',
    },
    surahLine: 'سورة {surah} : {ayah}',
    translationVia: 'الترجمة: {name} عبر Quranpedia',
    translation: 'الترجمة: {name}',
    translationHadeeth: 'الترجمة: HadeethEnc.com',
    captionQuranpedia: 'النص: مجمع الملك فهد (KFGQPC)، عبر Quranpedia',
    captionComplex: 'النص: مجمع الملك فهد (KFGQPC)',
    reviewed: 'طابقه فريقنا مع المصدر',
    reviewedTitle: 'لم يراجعه عالم',
    fiqhNote: 'معلومات عامة وليست فتوى. اسأل والديك أو أحد أهل العلم.',
    scholarsDiffer: 'قد يختلف العلماء:',
    viewOn: 'عرض في {site}',
    viewSource: 'عرض المصدر',
    newTab: ' (يفتح في تبويب جديد)',
    sources: 'المصادر',
    closeCard: 'إغلاق البطاقة',
    sessionSources: 'مصادر الجلسة ({n})',
    sourcesEmpty: 'الآيات والأحاديث التي يذكرها الصديق تظهر هنا.',
    audio: {
      listen: 'استمع إلى التلاوة', playing: 'جارٍ تشغيل التلاوة', loading: 'جارٍ التحميل...', unavailable: 'التلاوة غير متاحة',
      play: 'تشغيل التلاوة', pause: 'إيقاف التلاوة',
    },
    cite: {
      graded: 'الحكم: {grade} ({grader})', gradedNoGrader: 'الحكم: {grade}', source: 'المصدر: {site}', sahih: 'صحيح',
    },
  },
};

/** Display names of the approved hosts, both languages (the spec fixes the first two). */
export const SITE_NAMES = {
  'dorar.net': { en: 'الدرر السنية', ar: 'الدرر السنية' },
  'shamela.ws': { en: 'المكتبة الشاملة', ar: 'المكتبة الشاملة' },
  'quranpedia.net': { en: 'Quranpedia', ar: 'Quranpedia' },
  'qurancomplex.gov.sa': { en: 'King Fahd Complex', ar: 'مجمع الملك فهد' },
  'dawa.center': { en: 'Bayyinat', ar: 'بينات' },
  'islamic-content.com': { en: 'Al-Jamhara', ar: 'الجمهرة' },
};

// cards-spec (05) review: exact names only. A substring match would relabel another book that merely contains
// "Muslim" or "al-Bukhari" (Hisn al-Muslim, al-Adab al-Mufrad of al-Bukhari, a sharh of Sahih Muslim) as the Sahih,
// which is attributing a text to a reference that does not hold it. Anything else is shown as stored.
const BOOK_NAMES = {
  bukhari: { en: 'Sahih al-Bukhari', ar: 'صحيح البخاري', aliases: ['sahih al-bukhari', 'sahih bukhari', 'صحيح البخاري'] },
  muslim: { en: 'Sahih Muslim', ar: 'صحيح مسلم', aliases: ['sahih muslim', 'صحيح مسلم'] },
};

const GRADER_NAMES = {
  bukhari: { en: 'al-Bukhari', ar: 'البخاري', aliases: ['al-bukhari', 'bukhari', 'البخاري', 'الإمام البخاري'] },
  muslim: { en: 'Muslim', ar: 'مسلم', aliases: ['muslim', 'مسلم', 'الإمام مسلم'] },
};

const pickLang = (lang) => (lang === 'ar' ? 'ar' : 'en');
const fill = (template, values) => template.replace(/\{(\w+)\}/g, (m, k) => (k in values ? String(values[k]) : m));

// Compared without case, extra spaces, tatweel or Arabic short vowels, so a vowelled spelling still matches.
const nameKey = (raw) => String(raw || '').replace(/[ً-ْٰـ]/g, '').replace(/\s+/g, ' ').trim().toLowerCase();

function knownName(table, raw) {
  const s = nameKey(raw);
  if (!s) return null;
  return Object.values(table).find((entry) => entry.aliases.includes(s)) || null;
}

/** 'sahih' when `grade` is صحيح or sahih (the only grade a card may show), else null. The second guard behind the backend. */
export function normalizeGrade(grade) {
  const s = String(grade ?? '').trim().toLowerCase();
  return s === 'صحيح' || s === 'sahih' ? 'sahih' : null;
}

/** The hadith book in the page language: the two canonical books are translated, any other book stays as stored. */
export function bookName(book, lang) {
  return knownName(BOOK_NAMES, book)?.[pickLang(lang)] ?? String(book ?? '');
}

/** The grader in the page language: al-Bukhari and Muslim are mapped, any other grader is shown as stored. */
export function graderName(grader, lang) {
  return knownName(GRADER_NAMES, grader)?.[pickLang(lang)] ?? String(grader ?? '');
}

/** Display name of an approved host in the page language ("الدرر السنية" for dorar.net). */
export function siteName(site, lang) {
  return SITE_NAMES[site]?.[pickLang(lang)] ?? String(site ?? '');
}

const isDorar = (site) => site === 'dorar.net';

/**
 * The header of a card (section 1.2) as { template, book }, or null when the type and site pair has no label
 * (the card is then not rendered). `card.source_site` must already be the approved host (normalizeReference does that).
 * `template` may hold {book}; fillHeader() substitutes it. The UI wraps the book in <bdi>.
 */
export function sourceHeader(card, lang) {
  const L = SOURCE_LABELS[pickLang(lang)];
  const site = card?.source_site;
  const book = card?.book ? bookName(card.book, lang) : '';
  switch (card?.type) {
    case 'verse':
      return site === 'quranpedia.net' || site === 'qurancomplex.gov.sa' ? { template: L.fromQuran, book: '' } : null;
    case 'hadith':
      return (site === 'dorar.net' || site === 'shamela.ws') && book ? { template: L.fromBook, book } : null;
    case 'tafsir':
      if (isDorar(site)) return { template: L.tafsirEncyclopedia, book: '' };
      return book ? { template: L.bookSays, book } : null;
    case 'aqidah':
      return isDorar(site) ? { template: L.fromCreed, book: '' } : null;
    case 'fiqh':
      return isDorar(site) ? { template: L.fromFiqh, book: '' } : null;
    case 'sirah':
      return isDorar(site) ? { template: L.fromHistory, book: '' } : null;
    case 'faq':
      return site === 'dawa.center' ? { template: L.fromFaq, book: '' } : null;
    case 'term':
      return site === 'islamic-content.com' ? { template: L.fromTerm, book: '' } : null;
    default:
      return null;
  }
}

/** The header as one plain string, e.g. "From Sahih al-Bukhari:". */
export function fillHeader(header) {
  return header ? fill(header.template, { book: header.book }) : '';
}

/**
 * The hadith citation line pieces (section 1.4). Joined with " · " they read, for a dorar payload:
 *   en: Sahih al-Bukhari <n> · graded sahih (al-Bukhari) · source: الدرر السنية
 *   ar: صحيح البخاري <n> · الحكم: صحيح (البخاري) · المصدر: الدرر السنية
 * Returns null when the grade is not sahih (the card must not render).
 */
export function hadithCitationPieces(card, lang) {
  const L = SOURCE_LABELS[pickLang(lang)];
  if (normalizeGrade(card?.grade) !== 'sahih') return null;
  const grader = card.grader ? graderName(card.grader, lang) : '';
  const grade = L.cite.sahih;
  return [
    `${bookName(card.book, lang)} ${card.number}`,
    grader ? fill(L.cite.graded, { grade, grader }) : fill(L.cite.gradedNoGrader, { grade }),
    fill(L.cite.source, { site: siteName(card.source_site, lang) }),
  ];
}

export const CITATION_SEPARATOR = ' · ';

/** The tafsir citation line: the book and the "S:A-B" number. */
export function tafsirCitationPieces(card) {
  return [card.book, card.number].filter(Boolean);
}

/** The numeric id at the end of a HadeethEnc page path (hadeethenc.com/<lang>/browse/hadith/<id>), or ''. */
export function hadeethId(url) {
  try {
    const parts = new URL(url).pathname.split('/').filter(Boolean);
    const last = parts[parts.length - 1] || '';
    return /^\d+$/.test(last) ? last : '';
  } catch {
    return '';
  }
}

/**
 * The translation line under `english_text` (section 1.5): { text, href } (href null for plain text), or null when
 * there is no translation_name (then no English text is shown at all).
 */
export function translationLine(card, lang) {
  const L = SOURCE_LABELS[pickLang(lang)];
  const name = String(card?.translation_name || '').trim();
  if (!name) return null;
  const href = safeTranslationUrl(card.translation_source_url);
  let text;
  if (/hadeethenc/i.test(name) || (href && new URL(href).hostname.endsWith('hadeethenc.com'))) {
    const id = hadeethId(card.translation_source_url);
    text = id ? `${L.translationHadeeth} #${id}` : L.translationHadeeth;
  } else if (card.type === 'verse' && card.source_site === 'quranpedia.net') {
    text = fill(L.translationVia, { name });
  } else {
    text = fill(L.translation, { name });
  }
  return { text, href };
}

/** The small caption under a verse (section 1.3 item 6). */
export function verseCaption(card, lang) {
  const L = SOURCE_LABELS[pickLang(lang)];
  if (card?.source_site === 'quranpedia.net') return L.captionQuranpedia;
  if (card?.source_site === 'qurancomplex.gov.sa') return L.captionComplex;
  return '';
}

/** "سورة {name} : {ayah}" in Arabic, "Surah {surah}:{ayah}" in English (the number, as the spec words it). */
export function surahLine(card, lang) {
  const L = SOURCE_LABELS[pickLang(lang)];
  const surah = pickLang(lang) === 'ar' ? (card.surah_name || surahName(card.surah, 'ar') || card.surah) : card.surah;
  return fill(L.surahLine, { surah, ayah: card.ayah });
}

/** The short reference that replaces a {{verse:S:A}} marker in running text, from the surah list (no verse text). */
export function verseRefLabel(surah, ayah, lang) {
  if (pickLang(lang) === 'ar') return `سورة ${surahName(surah, 'ar')} ${surah}:${ayah}`;
  return `Surah ${surahName(surah, 'en')} ${surah}:${ayah}`;
}

/** The recitation credit line: the payload override when there is one, else the constant. */
export function recitationCredit(card, lang) {
  const own = String(card?.audio_credit || '').trim();
  return own || RECITATION_CREDIT[pickLang(lang)];
}

// The literal substring every credit string (payload or fallback) carries, in both languages, per the spec strings.
const EVERYAYAH_HOST = 'everyayah.com';

/**
 * The recitation credit line (section 1.6), split so only "everyayah.com" becomes a link: { before, linkText,
 * after, href }. `linkText` is '' and `href` is null when the credit text does not mention everyayah.com at all
 * (nothing to link to — e.g. a different, unapproved reciter site some day). Otherwise `href` is a safe link: the
 * payload `audio_source_url` when it is present (normalizeReference already dropped it if its host was not
 * approved, so by the time it gets here it is either a safe URL or absent), else the fallback constant. So an
 * unsafe `audio_source_url` never becomes a link to the unsafe host — it falls back to the known-good URL instead
 * of showing plain text, because the credit text itself is still the (trusted, UI-owned) everyayah.com wording.
 */
export function recitationCreditParts(card, lang) {
  const text = recitationCredit(card, lang);
  const idx = text.indexOf(EVERYAYAH_HOST);
  if (idx < 0) return { before: text, linkText: '', after: '', href: null };
  const own = String(card?.audio_source_url || '').trim();
  const href = own ? safeSourceUrl(own) : safeSourceUrl(RECITATION_AUDIO_SOURCE_URL);
  return { before: text.slice(0, idx), linkText: EVERYAYAH_HOST, after: text.slice(idx + EVERYAYAH_HOST.length), href };
}

/** Whether `segments` (section 2.1) holds at least one verse segment: its play button always has an audio
 * fallback (quranAudioUrl + QURAN_AUDIO_BASE), so any verse segment means the card shows the credit (once). */
export function segmentsHaveAudio(segments) {
  return Array.isArray(segments) && segments.some((s) => s?.type === 'verse');
}

/** "View on الدرر السنية (dorar.net)" / "عرض في الدرر السنية (dorar.net)", or the generic "View source". */
export function openSourceLabel(card, lang) {
  const L = SOURCE_LABELS[pickLang(lang)];
  const site = card?.source_site;
  if (!site) return L.viewSource;
  return fill(L.viewOn, { site: `${siteName(site, lang)} (${site})` });
}
