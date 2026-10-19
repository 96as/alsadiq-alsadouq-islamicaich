/**
 * Build the web avatar: a ~2 MB meshopt-compressed GLB from the 43 MB Tripo source.
 *
 * Source: the 43 MB Tripo export avatar-round7.glb. It is NOT in public/ any more (it was copied into
 * every build); it lives in git history. Restore it once, then run this script:
 *   git log --diff-filter=D --format=%H -1 -- frontend/public/models/avatar/avatar-round7.glb   (the deleting commit, call it D)
 *   mkdir -p avatar-src && git show D~1:frontend/public/models/avatar/avatar-round7.glb > avatar-src/avatar-round7.glb
 * or point AVATAR_SRC at a copy. The avatar-src folder is git-ignored.
 * Output: avatar-src/avatar-web.glb (gitignored; copy it to public/models/avatar/ and set FALLBACK_SHIPPED to ship it again)
 *
 * Steps: drop the unused backdrop plane and its 2400 px PNG, weld, decimate to
 * about TARGET_TRIANGLES (meshoptimizer keeps the original vertices, so the
 * skin weights and the head, neck and jaw bones survive), quantise, resize the
 * colour texture to 1024 px WebP, then compress with meshopt.
 *
 * Meshopt only: the three.js GLTFLoader (used by drei useGLTF) bundles a meshopt
 * decoder, whereas Draco would download its decoder from a CDN at runtime.
 *
 * Run: npm run avatar:optimize   (from frontend/)
 * Options: --triangles=80000  --texture=1024  --quality=85
 */
import { statSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS, EXTMeshoptCompression } from '@gltf-transform/extensions';
import {
  dedup,
  meshopt,
  prune,
  quantize,
  simplify,
  textureCompress,
  weld,
} from '@gltf-transform/functions';
import { MeshoptEncoder, MeshoptSimplifier } from 'meshoptimizer';
import sharp from 'sharp';

const arg = (name, fallback) => {
  const hit = process.argv.find((a) => a.startsWith(`--${name}=`));
  return hit ? Number(hit.split('=')[1]) : fallback;
};
const TARGET_TRIANGLES = arg('triangles', 80000);
const TEXTURE_SIZE = arg('texture', 1024);
const TEXTURE_QUALITY = arg('quality', 85);
const MAX_BYTES = 3 * 1024 * 1024;

const here = dirname(fileURLToPath(import.meta.url));
const SRC = process.env.AVATAR_SRC
  ? resolve(process.env.AVATAR_SRC)
  : resolve(here, '../avatar-src/avatar-round7.glb');
const OUT = resolve(here, '../avatar-src/avatar-web.glb'); // perf: not written into public/ any more (it is no longer shipped)

const mb = (bytes) => `${(bytes / 1024 / 1024).toFixed(2)} MB`;
const triangleCount = (doc) =>
  doc
    .getRoot()
    .listMeshes()
    .flatMap((m) => m.listPrimitives())
    .reduce((sum, p) => sum + (p.getIndices()?.getCount() ?? 0) / 3, 0);

await MeshoptEncoder.ready;
await MeshoptSimplifier.ready;

const io = new NodeIO()
  .registerExtensions(ALL_EXTENSIONS)
  .registerDependencies({ 'meshopt.encoder': MeshoptEncoder });

const before = statSync(SRC).size;
const document = await io.read(SRC);
const sourceTriangles = triangleCount(document);
console.log(`Source: ${mb(before)}, ${Math.round(sourceTriangles)} triangles`);

// The page supplies its own background image, so the baked-in backdrop plane
// (and its 2400 px PNG) is dead weight.
for (const node of document.getRoot().listNodes()) {
  if (node.getName() === 'Backdrop') {
    node.setMesh(null);
    node.dispose();
  }
}

await document.transform(
  dedup(),
  prune(),
  weld(),
  simplify({
    simplifier: MeshoptSimplifier,
    ratio: TARGET_TRIANGLES / sourceTriangles,
    // High error ceiling so the triangle target is what decides when to stop.
    error: 0.05,
  }),
  prune(),
  quantize(),
  textureCompress({
    encoder: sharp,
    targetFormat: 'webp',
    quality: TEXTURE_QUALITY,
    resize: [TEXTURE_SIZE, TEXTURE_SIZE],
  }),
  meshopt({ encoder: MeshoptEncoder, level: 'high' }),
);

// Avatar.jsx drives these bones by name. Fail loudly if the rig did not survive.
const nodeNames = new Set(document.getRoot().listNodes().map((n) => n.getName()));
for (const required of ['head', 'neck', 'jaw', 'arm.l', 'arm.r']) {
  if (!nodeNames.has(required)) {
    console.error(`FAIL: required bone "${required}" is missing.`);
    process.exit(1);
  }
}
if (document.getRoot().listSkins().length === 0) {
  console.error('FAIL: no skin left, the mesh would not deform.');
  process.exit(1);
}
if (!document.getRoot().listExtensionsUsed().some((e) => e instanceof EXTMeshoptCompression)) {
  console.error('FAIL: meshopt compression was not applied.');
  process.exit(1);
}

await io.write(OUT, document);

const after = statSync(OUT).size;
console.log(`Wrote ${OUT}`);
console.log(
  `Output: ${mb(after)} (${Math.round((1 - after / before) * 100)}% smaller), ` +
    `${Math.round(triangleCount(document))} triangles, ` +
    `${document.getRoot().listTextures().length} texture(s)`,
);
if (after > MAX_BYTES) {
  console.error(`FAIL: output is over ${mb(MAX_BYTES)}. Lower --triangles or --texture.`);
  process.exit(1);
}
console.log('OK: within the 3 MB web budget.');
