import { STRINGS } from './strings.js';

/** 'ar' | 'en' from any language value ('en-US', 'ar', null...). Arabic is the default. */
export const normalizeLang = (value) => (String(value || '').toLowerCase().startsWith('en') ? 'en' : 'ar');

/** Dictionary for a language, outside React (validators, services, tests). */
export const stringsFor = (lang) => STRINGS[normalizeLang(lang)];
