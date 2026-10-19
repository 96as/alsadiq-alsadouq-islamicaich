// The narrow meadow tier (perf): meadow-narrow-<w>.webp keeps only the columns a portrait viewport can show.
// Run with `npm run test:meadowstage`. The band in meadowFraming.js must cover the visible slice under both fits:
// the look-dev fit (object-position 47.5%, stageFraming.js paintingFit) and the anchored fit (computeFraming).
import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import sharp from 'sharp';
import { paintingFit } from '../src/features/child/components/avatar/lookdev/stageFraming.js';
import {
  MEADOW_IMAGE,
  MEADOW_NARROW,
  MEADOW_NARROW_SRCSET,
  MEADOW_SRCSET,
  PATH_X,
  computeFraming,
  meadowCap,
  meadowFile,
  meadowNarrowSrcset,
} from '../src/features/child/components/meadowFraming.js';

const root = resolve(import.meta.dirname, '..');
// every portrait phone up to the 3:4 the media query allows
const VIEWPORTS = [[320, 568], [360, 640], [375, 667], [390, 844], [412, 915], [430, 932], [600, 800], [768, 1024], [360, 1200]];

test('the media query is max-aspect-ratio 3/4', () => {
  assert.equal(MEADOW_NARROW.media, '(max-aspect-ratio: 3/4)');
});

for (const [W, H] of VIEWPORTS) {
  test(`the band covers the visible slice at ${W}x${H} under both fits`, () => {
    assert.ok(W / H <= 0.75 + 1e-9);
    const [lo, hi] = MEADOW_NARROW.band;
    // look-dev fit
    const f = paintingFit(W, H);
    const l1 = -f.ox / f.dw;
    const r1 = (W - f.ox) / f.dw;
    assert.ok(l1 >= lo && r1 <= hi, `look-dev slice ${l1.toFixed(3)}..${r1.toFixed(3)} vs band ${lo}..${hi}`);
    // anchored fit
    const fr = computeFraming(W, H);
    const imgW = Math.max(W / MEADOW_IMAGE.aspect, H) * MEADOW_IMAGE.aspect;
    const l2 = (fr.objectX * (imgW - W)) / imgW;
    const r2 = l2 + W / imgW;
    assert.ok(l2 >= lo && r2 <= hi, `anchored slice ${l2.toFixed(3)}..${r2.toFixed(3)} vs band ${lo}..${hi}`);
    assert.ok(PATH_X > lo && PATH_X < hi);
  });
}

test('the narrow srcset mirrors the full srcset width for width', () => {
  const widths = (s) => s.split(',').map((x) => x.trim().split(' ')[1]);
  assert.deepEqual(widths(MEADOW_NARROW_SRCSET), widths(MEADOW_SRCSET));
  assert.match(MEADOW_NARROW_SRCSET, /meadow-narrow-900\.webp 900w/);
  assert.equal(meadowFile(2560, true), 'meadow-narrow-2560.webp');
  assert.equal(meadowFile(2560, false), 'meadow-2560.webp');
});

test('MeadowImage serves the narrow tier through a <picture> source, and MeadowLife loads the same files', () => {
  const image = readFileSync(resolve(root, 'src/features/child/components/MeadowImage.jsx'), 'utf8');
  assert.match(image, /<source media=\{MEADOW_NARROW\.media\} srcSet=\{narrowSrcset\}/);
  assert.match(image, /meadowNarrowSrcset\(meadowCap\(detectQuality\(\)\)\)/);
  const life = readFileSync(resolve(root, 'src/features/child/components/ambient/MeadowLife.jsx'), 'utf8');
  assert.match(life, /meadowFile\(width, narrow\)/);
  assert.match(life, /const cap = meadowCap\(quality\)/);
});

// perf review: the GL layer (which covers the <img>) and the narrow <img> must pick the same file, or a phone downloads two.
test('the narrow <img> stops at the GL cap, so a phone takes one meadow file', () => {
  const widths = (s) => s.split(',').map((x) => Number(x.trim().split(' ')[1].replace('w', '')));
  assert.deepEqual(widths(meadowNarrowSrcset(meadowCap('low'))), [900, 1600, 2560]);
  assert.deepEqual(widths(meadowNarrowSrcset(meadowCap('high'))), [900, 1600, 2560, 3840]);
  // smallest candidate that covers the need, else the largest: the browser's srcset pick and meadowLifeGL pickWidth
  const pick = (ws, need) => ws.find((w) => w >= need) ?? ws[ws.length - 1];
  for (const [W, H] of VIEWPORTS) {
    const imgW = Math.max(W / MEADOW_IMAGE.aspect, H) * MEADOW_IMAGE.aspect;
    for (const dpr of [1, 1.5, 2, 2.625, 3]) {
      for (const q of ['low', 'high']) {
        const ws = widths(meadowNarrowSrcset(meadowCap(q)));
        const img = pick(ws, imgW * dpr);
        const gl = pick(ws, imgW * Math.min(dpr, 2)); // MeadowLife caps the GL DPR at 2
        // the same need below DPR 2; above it both land on the top width once the GL's need passes the one below it
        const agree = dpr <= 2 || imgW * 2 > ws[ws.length - 2];
        if (agree) assert.equal(gl, img, `${W}x${H} @${dpr} ${q}: GL ${gl} vs <img> ${img}`);
        if (q === 'low') assert.ok(agree, `${W}x${H} @${dpr}: a phone's GL and <img> take the same file`);
      }
    }
  }
});

for (const w of MEADOW_IMAGE.widths) {
  test(`meadow-narrow-${w}.webp has the same size as meadow-${w}.webp and fewer bytes`, async () => {
    const dir = resolve(root, 'public/backgrounds/hq');
    const full = resolve(dir, MEADOW_IMAGE.file(w));
    const narrow = resolve(dir, MEADOW_NARROW.file(w));
    assert.ok(existsSync(narrow), `${narrow} exists (npm run meadow:narrow)`);
    const [a, b] = await Promise.all([sharp(full).metadata(), sharp(narrow).metadata()]);
    assert.equal(b.width, a.width);
    assert.equal(b.height, a.height);
    assert.ok(readFileSync(narrow).length < readFileSync(full).length * 0.7, 'at least 30% smaller');
  });
}
