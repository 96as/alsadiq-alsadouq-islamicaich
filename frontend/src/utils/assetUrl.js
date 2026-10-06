/**
 * Base-path helpers. The app is served at "/" in production; the showcase build
 * is served under a sub-path (vite build --base /page/). import.meta.env.BASE_URL
 * always ends with a slash. With the default base "/", every helper here returns
 * its input unchanged.
 */
// integrate-1: optional chaining so the node tests and the lip-sync eval can import avatarConfig.js
export const BASE_URL = import.meta.env?.BASE_URL || '/';

/** Showcase build (VITE_SHOWCASE=1): preview pages only, no backend. Off by default. */
export const SHOWCASE = import.meta.env?.VITE_SHOWCASE === '1';

/** Router basename: "/" or "/page" (no trailing slash). */
export const ROUTER_BASENAME = BASE_URL === '/' ? '/' : BASE_URL.replace(/\/+$/, '');

/** Turns an absolute public path ("/models/x.glb") into one that honours the base. */
export function assetUrl(path) {
  if (BASE_URL === '/' || typeof path !== 'string' || !path.startsWith('/')) return path;
  if (path.startsWith(BASE_URL)) return path; // already prefixed
  return BASE_URL + path.replace(/^\/+/, '');
}
