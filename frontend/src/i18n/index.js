/**
 * Small i18n layer for the web app (Arabic first).
 *
 * There is no library: the app already keeps one language switch (`demo_lang`, read by
 * `useDemoLang`) and per-surface copy objects (`COPY`, `VOICE_COPY`). This module adds:
 *   - `useLang()`       the active language as React state ('ar' | 'en')
 *   - `useStrings()`    the dictionary for it (see strings.js)
 *   - `useDocumentLang` sets <html lang> and dir from the active language
 *   - number / percent / date / relative-time formatters that give Arabic-Indic digits
 *
 * No Quran or hadith text lives here, only plain interface wording.
 */
import { useEffect } from 'react';
import { readDemoLang, useDemoLang } from '../services/demoService';
import { STRINGS } from './strings';
import { shortDate } from './format';
import { normalizeLang, stringsFor } from './stringsFor';

export { num, pct, arCount, shortDate, clockTime } from './format';

export const LANGS = ['ar', 'en'];

export { normalizeLang, stringsFor };
export const dirOf = (lang) => (lang === 'en' ? 'ltr' : 'rtl');

/** The active UI language. Follows the demo toggle and the child's profile (see LangSync). */
export const useLang = () => useDemoLang();

/** The dictionary for the active language. */
export const useStrings = () => STRINGS[useLang()];

/** The language right now, outside React. */
export const currentLang = () => readDemoLang();

/** `<html lang dir>` follows the language: Arabic reads right to left. */
export const applyDocumentLang = (lang, root = typeof document !== 'undefined' ? document.documentElement : null) => {
  if (!root) return;
  root.setAttribute('lang', lang);
  root.setAttribute('dir', dirOf(lang));
};

/**
 * Mount this in a shell that is fully localised (the child and parent apps, the demo landing page).
 * It sets <html lang dir> from the language and puts the old values back when the shell unmounts,
 * so the English-only sign-in pages never inherit a right-to-left page.
 */
export const useDocumentLang = () => {
  const lang = useLang();
  useEffect(() => {
    const root = document.documentElement;
    const before = { lang: root.getAttribute('lang'), dir: root.getAttribute('dir') };
    applyDocumentLang(lang, root);
    return () => {
      if (before.lang) root.setAttribute('lang', before.lang); else root.removeAttribute('lang');
      if (before.dir) root.setAttribute('dir', before.dir); else root.removeAttribute('dir');
    };
  }, [lang]);
  return lang;
};

/** "5m ago" in either language. `now` is injectable for tests. */
export const timeAgo = (iso, lang, now = new Date()) => {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  const diffMin = Math.round(Math.max(0, now - d) / 60000);
  const diffH = Math.round(diffMin / 60);
  const diffD = Math.round(diffH / 24);
  const s = STRINGS[lang].time;
  if (diffMin < 1) return s.now;
  if (diffMin < 60) return s.minutesAgo(diffMin);
  if (diffH < 24) return s.hoursAgo(diffH);
  if (diffD === 1) return s.yesterday;
  if (diffD < 7) return s.daysAgo(diffD);
  return shortDate(iso, lang);
};

/** English backend names (levels, badges) in the active language. Falls back to the original. */
export const localName = (map, name) => (name && map && map[name]) || name;
