const APPROVED_SOURCE_HOSTS = [
  'quranpedia.net',
  'qurancomplex.gov.sa',
  'dorar.net',
  'shamela.ws',
  'dawa.center',
  'islamic-content.com',
  // cards-spec (05) section 1.6, organiser ruling 2026-10-05: the recitation credit's own link (audio_source_url),
  // never a card's source_url (SOURCE_HOSTS_BY_TYPE below does not list it for any type).
  'everyayah.com',
];

// cards-spec (05) section 2: the hosts a `source_url` may use, by card type. hadeethenc.com is
// deliberately absent: it is a translation link only, never a hadith source.
const SOURCE_HOSTS_BY_TYPE = {
  verse: ['quranpedia.net', 'qurancomplex.gov.sa'],
  hadith: ['dorar.net', 'shamela.ws'],
  tafsir: ['dorar.net', 'shamela.ws', 'quranpedia.net'],
  aqidah: ['dorar.net', 'shamela.ws'],
  fiqh: ['dorar.net', 'shamela.ws'],
  sirah: ['dorar.net', 'shamela.ws'],
  faq: ['dawa.center'],
  term: ['islamic-content.com'],
};

// cards-spec (05) section 1.5: where a translation's own page may live.
const TRANSLATION_HOSTS = ['hadeethenc.com', 'quranenc.com', 'quranpedia.net'];

function parse(u) {
  if (typeof u !== 'string' || !u.trim()) return null;
  try {
    return new URL(u, window.location.origin);
  } catch {
    return null;
  }
}

const hostMatches = (host, allowed) => allowed.some((h) => host === h || host.endsWith(`.${h}`));

/**
 * Returns a safe href for a source link, or null. Only http(s) URLs on the
 * approved content hosts (or their subdomains) are allowed.
 */
export function safeSourceUrl(u) {
  const url = parse(u);
  if (!url) return null;
  if (url.protocol !== 'https:' && url.protocol !== 'http:') return null;
  return hostMatches(url.hostname.toLowerCase(), APPROVED_SOURCE_HOSTS) ? url.href : null;
}

/**
 * cards-spec (05): the approved host (dorar.net, ...) that `u` belongs to for this card type,
 * or null. This is the "source_site" the card is allowed to name.
 */
export function sourceHostForType(type, u) {
  const href = safeSourceUrl(u);
  if (!href) return null;
  const host = new URL(href).hostname.toLowerCase();
  return (SOURCE_HOSTS_BY_TYPE[type] || []).find((h) => host === h || host.endsWith(`.${h}`)) || null;
}

/** cards-spec (05): a safe href for a translation's own page (hadeethenc.com, quranenc.com, quranpedia.net), or null. */
export function safeTranslationUrl(u) {
  const url = parse(u);
  if (!url || url.protocol !== 'https:') return null;
  return hostMatches(url.hostname.toLowerCase(), TRANSLATION_HOSTS) ? url.href : null;
}

/** Returns a safe audio src (same-origin or https), or null. */
export function safeAudioUrl(u) {
  const url = parse(u);
  if (!url) return null;
  if (url.origin === window.location.origin) return url.href;
  return url.protocol === 'https:' ? url.href : null;
}

/** @deprecated name kept generic: use safeSourceUrl / safeAudioUrl. */
export const safeHttpUrl = safeSourceUrl;
