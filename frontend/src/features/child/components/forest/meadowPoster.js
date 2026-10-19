/**
 * The painted meadow that shows while the 3D forest loads (and when WebGL is missing). One place for
 * the file names so the page preload (index.html), the landing and the stage all ask for the same URL:
 * a 900 px file for phones (47 KB), 1600 px, and the 2560 px original.
 */
export const MEADOW_IMAGE = '/backgrounds/fantasy-meadow.webp';
export const MEADOW_SRCSET = [
  '/backgrounds/fantasy-meadow-900.webp 900w',
  '/backgrounds/fantasy-meadow-1600.webp 1600w',
  '/backgrounds/fantasy-meadow.webp 2560w',
].join(', ');
// The picture fills the arch (about 560 px wide on desktop) or the phone's width.
export const MEADOW_SIZES = '(min-width: 1024px) 560px, 100vw';
