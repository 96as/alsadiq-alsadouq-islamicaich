// w3: what the held web page may show (BEHAVIOUR-SPEC 6.8 and 6.11). Pure: no DOM, no three.js, so it is unit tested.
//
// Only real text from the search tool (or a clearly marked dev fixture) is ever drawn. Everything is escaped
// and truncated here, once, before the renderer sees it. Nothing here contains scripture: the lists below are
// the META WORDS that mark a result as religious text, so the page can refuse to show it and show the
// neutral "read this with a grown-up" card instead. Nothing on the page is clickable and only the domain of a
// result is ever shown, never a full URL.

export const LIMITS = { title: 70, snippet: 140, query: 70, results: 5, domain: 40, raw: 400 };

export const GROWNUP = {
  en: { title: "Let's read this with a grown-up", body: 'Some things are best read together.' },
  ar: { title: 'نقرأها مع أحد الكبار', body: 'بعض الأشياء الأفضل أن نقرأها معا.' },
};

export const NONE_TEXT = {
  en: { title: 'No pages found', body: 'Let us try asking in a different way.' },
  ar: { title: 'لم نجد صفحات', body: 'لنجرب السؤال بطريقة أخرى.' },
};

export const FOOTER_TEXT = { en: 'Pages chosen for kids', ar: 'صفحات مختارة للأطفال' };

// Arabic combining marks (tashkeel) and the dagger alef, tatweel, and the bidi control characters that can spoof text.
const DIACRITICS = /[\u064B-\u065F\u0670\u06D6-\u06ED]/g;
const BIDI_CONTROLS = /[\u200E\u200F\u202A-\u202E\u2066-\u2069\u061C]/g;
// eslint-disable-next-line no-control-regex -- stripping control characters is the point
const CONTROLS = /[\u0000-\u001F\u007F-\u009F]/g;
const ARABIC_LETTER = /[\u0621-\u064A]/g;

/** Arabic comparison form: no marks, no tatweel, alef variants merged, ya and ta marbuta folded. */
export function foldArabic(text) {
  return String(text)
    .replace(DIACRITICS, '')
    .replace(/ـ/g, '')
    .replace(/[آأإٱ]/g, 'ا')
    .replace(/ى/g, 'ي')
    .replace(/ة/g, 'ه');
}

// Whole words, folded with foldArabic (so these are written in plain letters). Whole words only: "ايه" inside
// "نهايه" (an ending) must not trip. A leading ال, و, ب, ل or ف is allowed on the word.
const META_AR_WORDS = new Set(['سوره', 'ايه', 'ايات', 'حديث', 'رواه', 'القران', 'قران']);
const META_AR_PREFIX = ['', 'ال', 'وال', 'بال', 'فال', 'لل', 'و', 'ب', 'ل', 'ف'];
const META_EN = [/\bqur'?an\b/i, /\bkoran\b/i, /\bsurah?\b/i, /\bayah\b/i, /\bayat\b/i, /\bhadith\b/i, /\bverses?\b/i];

function arabicMeta(token) {
  for (const pre of META_AR_PREFIX) {
    if (token.length > pre.length && token.startsWith(pre) && META_AR_WORDS.has(token.slice(pre.length))) return true;
  }
  return false;
}

/** True when `text` carries a scripture marker (a meta word) in Arabic or English. */
export function hasMetaWord(text) {
  if (!text) return false;
  const s = String(text);
  for (const re of META_EN) if (re.test(s)) return true;
  const tokens = foldArabic(s).split(/[^ء-ي]+/).filter(Boolean);
  for (let i = 0; i < tokens.length; i++) {
    if (arabicMeta(tokens[i])) return true;
    if (tokens[i] === 'قال' && tokens[i + 1] === 'رسول') return true;
  }
  return false;
}

/** The share of Arabic letters that carry a diacritic. Fully voweled text is how scripture is typeset. */
export function diacriticShare(text) {
  const s = String(text ?? '');
  const letters = (s.match(ARABIC_LETTER) || []).length;
  if (letters === 0) return 0;
  const marks = (s.match(DIACRITICS) || []).length;
  return marks / letters;
}

/** One line of display text: controls and bidi overrides out, tags out, spaces collapsed. Never longer than `max`. */
export function cleanText(value, max) {
  if (typeof value !== 'string') return '';
  let s = value.slice(0, LIMITS.raw);
  s = s.replace(CONTROLS, ' ').replace(BIDI_CONTROLS, '');
  s = s.replace(/<[^>]*>/g, ' ').replace(/[<>]/g, '');
  s = s.replace(/&(?:[a-z]+|#\d+);/gi, ' ');
  s = s.replace(/\s+/g, ' ').trim();
  if (s.length > max) {
    // cut at a word boundary when one is close, and never inside a surrogate pair
    let cut = s.slice(0, max - 1);
    const sp = cut.lastIndexOf(' ');
    if (sp > max * 0.6) cut = cut.slice(0, sp);
    if (/[\uD800-\uDBFF]$/.test(cut)) cut = cut.slice(0, -1);
    s = cut.replace(/[\s.,;:!?-]+$/, '') + '…';
  }
  return s;
}

/** Only the host of a URL or domain: lower case, no scheme, credentials, port, path or query. '' when it is not a plain host. */
export function cleanDomain(value) {
  if (typeof value !== 'string') return '';
  let s = value.trim().toLowerCase().slice(0, 200);
  s = s.replace(/^[a-z][a-z0-9+.-]*:\/\//, '');
  s = s.replace(/^[^/@]*@/, '');
  s = s.split(/[/?#]/)[0].replace(/:\d+$/, '').replace(/^www\./, '');
  if (!/^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$/.test(s)) return '';
  return s.length > LIMITS.domain ? s.slice(0, LIMITS.domain - 1) + '…' : s;
}

const TOPICS = [
  ['space', /\b(space|star|stars|moon|sun|planet|planets|galaxy|rocket|orbit|astronaut|comet|universe)\b|فضاء|نجم|نجوم|قمر|شمس|كوكب|مجره|صاروخ/i],
  ['weather', /\b(sky|rain|cloud|clouds|weather|wind|storm|snow|rainbow|thunder|lightning|season)\b|سماء|السماء|مطر|غيم|سحاب|طقس|رياح|عاصفه|ثلج|رعد|برق|قوس قزح/i],
  ['animals', /\b(bee|bees|honey|animal|animals|bird|birds|fish|cat|dog|camel|horse|butterfly|ant|ants|insect|whale|lion|elephant)\b|نحل|عسل|حيوان|طير|طائر|سمك|قط|كلب|جمل|حصان|فراش|نمل|حشر|حوت|اسد|فيل/i],
  ['body', /\b(body|heart|bone|bones|brain|teeth|tooth|eyes?|ear|sleep|blood|muscle|lungs?|breath|hungry)\b|جسم|قلب|عظم|عظام|دماغ|اسنان|عين|نوم|دم|عضل|رئه|تنفس/i],
  ['values', /\b(kind|kindness|honest|honesty|share|sharing|friend|friends|help|helping|patience|polite|respect|truth)\b|لطف|صدق|امانه|مشاركه|صديق|مساعده|صبر|ادب|احترام/i],
  ['nature', /\b(tree|trees|plant|plants|flower|flowers|river|sea|ocean|mountain|forest|grow|seed|leaf|leaves|water|earth|desert|rock)\b|شجر|نبات|زهر|نهر|بحر|محيط|جبل|غابه|بذر|ورق|ماء|ارض|صحراء|صخر/i],
];

/** The picture category for a query (nature, animals, space, weather, body, values, generic). */
export function topicOf(query) {
  const q = foldArabic(String(query ?? ''));
  for (const [name, re] of TOPICS) if (re.test(q)) return name;
  return 'generic';
}

/** Whether a result trips a scripture rule. */
function resultTrips(r) {
  const text = `${r.t} ${r.s}`;
  return hasMetaWord(text) || diacriticShare(text) > 0.2;
}

/**
 * One result from the tool, cleaned. Returns null for something unusable (no title).
 * @param {{t?: unknown, d?: unknown, s?: unknown}} r
 */
export function cleanResult(r) {
  if (!r || typeof r !== 'object') return null;
  const t = cleanText(r.t, LIMITS.title);
  if (!t) return null;
  return { t, d: cleanDomain(r.d), s: cleanText(r.s, LIMITS.snippet) };
}

/**
 * What the page shows, from the `al.search` state the avatar store keeps.
 *
 * @param {{id?: string, st?: string, q?: string, lang?: string, r?: unknown[], hl?: number, sf?: unknown, fixture?: boolean}|null} s
 * @param {string} [uiLang] fallback language
 * @returns {null | {
 *   id: string, state: 'skeleton'|'results'|'none'|'grownup', lang: 'ar'|'en', rtl: boolean, query: string, topic: string,
 *   results: {t: string, d: string, s: string}[], hl: number, hero: boolean, foundTitle: string, fixture: boolean, key: string
 * }}
 */
export function buildPageModel(s, uiLang = 'en') {
  if (!s || typeof s !== 'object') return null;
  const lang = s.lang === 'ar' || s.lang === 'en' ? s.lang : uiLang === 'ar' ? 'ar' : 'en';
  const query = cleanText(s.q, LIMITS.query);
  const flagged = !!s.sf || hasMetaWord(s.q) || diacriticShare(s.q) > 0.2;
  const base = {
    id: typeof s.id === 'string' ? s.id.slice(0, 24) : '',
    state: 'skeleton',
    lang,
    rtl: lang === 'ar',
    query,
    topic: topicOf(query),
    results: [],
    hl: -1,
    hero: false,
    foundTitle: '',
    fixture: !!s.fixture,
    key: '',
  };
  if (flagged) {
    base.state = 'grownup';
    base.topic = 'generic';
    base.query = '';
  } else if (s.st === 'none') {
    base.state = 'none';
  } else if (s.st === 'results') {
    const raw = Array.isArray(s.r) ? s.r.slice(0, LIMITS.results) : [];
    const results = [];
    let tripped = false;
    for (const item of raw) {
      const r = cleanResult(item);
      if (!r) continue;
      if (resultTrips(r)) {
        tripped = true;
        break;
      }
      results.push(r);
    }
    if (tripped) {
      base.state = 'grownup';
      base.topic = 'generic';
      base.query = '';
    } else if (results.length === 0) {
      base.state = 'none';
    } else {
      base.state = 'results';
      base.results = results;
      const hl = Number.isInteger(s.hl) && s.hl >= 0 && s.hl < results.length ? s.hl : 0;
      base.hl = hl;
      base.foundTitle = results[hl].t;
      base.hero = true; // only a page with real result text earns the hero hold
    }
  }
  base.key = `${base.state}|${base.lang}|${base.query}|${base.results.map((r) => r.t).join('~')}|${base.hl}`;
  return base;
}

/** The text a screen reader gets for the page (the aria-live status keeps running in reduced motion). */
export function spokenSummary(model) {
  if (!model) return '';
  if (model.state === 'grownup') return GROWNUP[model.lang].title;
  if (model.state === 'none') return NONE_TEXT[model.lang].title;
  if (model.state === 'results') return model.foundTitle;
  return '';
}
