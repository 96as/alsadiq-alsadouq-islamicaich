import { useSyncExternalStore } from 'react';

/**
 * cards-spec (05) section 3: is the KFGQPC Hafs font usable?
 * The unmodified TTF is requested through the @font-face in sourceCards.css. If it fails to load, or does not load
 * within 3 seconds, the verse falls back to Amiri Quran and the display-time mark mapping (toDisplayArabic) is used.
 * One shared check for the whole page: every verse card reads the same answer.
 */
const TIMEOUT_MS = 3000;
export const QURAN_FONT = '28px "KFGQPC Hafs"';

let status = 'pending'; // 'pending' | 'ok' | 'fallback'
let started = false;
const listeners = new Set();

function settle(next) {
  if (status !== 'pending') return;
  status = next;
  listeners.forEach((fn) => fn());
}

function startCheck() {
  if (started) return;
  started = true;
  if (typeof document === 'undefined' || !document.fonts || typeof document.fonts.load !== 'function') {
    settle('fallback');
    return;
  }
  const timer = setTimeout(() => settle('fallback'), TIMEOUT_MS);
  document.fonts.load(QURAN_FONT).then(
    (faces) => {
      clearTimeout(timer);
      settle(faces && faces.length ? 'ok' : 'fallback'); // no matching face loaded: the file is missing
    },
    () => {
      clearTimeout(timer);
      settle('fallback');
    },
  );
}

const subscribe = (fn) => {
  listeners.add(fn);
  startCheck();
  return () => listeners.delete(fn);
};

/** 'pending' | 'ok' | 'fallback'. */
export function useQuranFontStatus() {
  return useSyncExternalStore(subscribe, () => status, () => 'pending');
}

/** True once the check has settled on the fallback font (the mapping must then be applied at display time). */
export default function useQuranFontFallback() {
  return useQuranFontStatus() === 'fallback';
}
