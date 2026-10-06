/**
 * Feature flag for the forest scene. Default OFF.
 *
 *   ?forest=1            turn on (remembered in localStorage)
 *   ?forest=0            turn off and forget
 *   VITE_FOREST_SCENE=1  turn on at build time
 *   (avatar-integ: the painted meadow, alive, is the default stage for the child. The 3D forest is opt-in only:
 *   VITE_DEMO_MODE no longer turns it on.)
 */
const STORAGE_KEY = 'sadiq_forest_scene';

export function isForestEnabled() {
  try {
    const q = new URLSearchParams(window.location.search).get('forest');
    if (q === '1') {
      window.localStorage.setItem(STORAGE_KEY, '1');
      return true;
    }
    if (q === '0') {
      window.localStorage.removeItem(STORAGE_KEY);
      return false;
    }
    if (window.localStorage.getItem(STORAGE_KEY) === '1') return true;
  } catch {
    // storage or location blocked: fall through to the build flag
  }
  return import.meta.env.VITE_FOREST_SCENE === '1'; // avatar-integ: no VITE_DEMO_MODE default any more
}
