// Builds the narrow-viewport meadow tier: public/backgrounds/hq/meadow-narrow-<w>.webp from meadow-<w>.webp.
//
//   node scripts/make-narrow-meadow.mjs [--quality=84] [--dry]
//
// A phone in portrait shows a thin vertical slice of the 16:9 painting (object-fit: cover), so most of the bytes of
// meadow-3840.webp are columns nobody sees. The narrow file is the same picture at the same size (so every piece of
// framing and GL maths stays as it is) with only the visible band kept sharp: the columns outside BAND are a smooth
// colour wash of the painting itself, which WebP codes in a few kilobytes.
//
// BAND is in painting u (0..1). It covers a portrait viewport up to 3:4 (the media query MEADOW_NARROW_MEDIA in
// meadowFraming.js) with object-position 47.5% (look-dev, u 0.2755..0.6955 at 3:4) and the anchored fit centred on the
// path at u 0.455 (0.245..0.665), plus a margin for a viewport that is resized.
// The tier must keep PAINTING/PATH_X in step: tests/meadowNarrow.test.mjs checks the band against both fits.
import { existsSync, statSync } from 'node:fs';
import { resolve } from 'node:path';
import sharp from 'sharp';

export const BAND = [0.19, 0.75];
export const WIDTHS = [900, 1600, 2560, 3840, 5120];

const quality = Number((process.argv.find((a) => a.startsWith('--quality=')) ?? '--quality=84').split('=')[1]);
const dry = process.argv.includes('--dry');
const dir = resolve(import.meta.dirname, '../public/backgrounds/hq');

async function build(w) {
  const src = resolve(dir, `meadow-${w}.webp`);
  if (!existsSync(src)) throw new Error(`missing ${src}`);
  const meta = await sharp(src).metadata();
  const left = Math.floor(BAND[0] * meta.width);
  const right = Math.ceil(BAND[1] * meta.width);
  const band = await sharp(src).extract({ left, top: 0, width: right - left, height: meta.height }).toBuffer();
  const wash = await sharp(src)
    .resize(48, 27, { fit: 'fill', kernel: 'lanczos3' })
    .resize(meta.width, meta.height, { fit: 'fill', kernel: 'cubic' })
    .blur(6)
    .toBuffer();
  const out = await sharp(wash)
    .composite([{ input: band, left, top: 0 }])
    .webp({ quality, effort: 6, smartSubsample: true })
    .toBuffer();
  const dest = resolve(dir, `meadow-narrow-${w}.webp`);
  if (!dry) await sharp(out).toFile(dest);
  console.log(`meadow-narrow-${w}.webp ${meta.width}x${meta.height} band ${left}..${right}: ${statSync(src).size} -> ${out.length} bytes`);
}

for (const w of WIDTHS) await build(w);
