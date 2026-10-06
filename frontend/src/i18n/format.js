import { localDigits } from '../features/demo/copy.js';

/** Pure formatters (no dictionary), shared by strings.js and index.js. */

/** A number as text: Arabic-Indic digits in Arabic, plain digits in English. */
export const num = (n, lang) => localDigits(n ?? '', lang);

/** 60 -> "٦٠٪" in Arabic, "60%" in English. */
export const pct = (n, lang) => (lang === 'ar' ? `${num(n, lang)}٪` : `${n}%`);

/** Arabic count phrase. `one` and `two` are whole phrases, `few` (3-10) and `many` (11+) are nouns. */
export const arCount = (n, one, two, few, many) => {
  const v = Math.abs(Number(n));
  if (v === 1) return one;
  if (v === 2) return two;
  return `${num(n, 'ar')} ${v >= 3 && v <= 10 ? few : many}`;
};

// Gregorian months with Latin digits first, then mapped by hand, so a device with an Islamic default
// calendar or Eastern digits can never change what a child sees.
const AR_DATE = 'ar-u-ca-gregory-nu-latn';

/** "٥ أكتوبر" or "Oct 5". */
export const shortDate = (iso, lang) => {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  if (lang === 'ar') {
    return localDigits(new Intl.DateTimeFormat(AR_DATE, { month: 'long', day: 'numeric' }).format(d), 'ar');
  }
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
};

/** Time of day, "٣:٠٥ م" or "3:05 PM". */
export const clockTime = (value, lang) => {
  const d = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(d.getTime())) return '';
  if (lang === 'ar') {
    return localDigits(new Intl.DateTimeFormat(AR_DATE, { hour: 'numeric', minute: '2-digit', hour12: true }).format(d), 'ar');
  }
  return d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
};

