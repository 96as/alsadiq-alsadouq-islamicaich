// Dev helper: prints the node tree, morph targets and animation channels of a GLB.
// Usage: node scripts/inspect-avatar-glb.mjs public/models/avatar/avatar-animated.glb [tracks]
import { NodeIO } from '@gltf-transform/core';
import { EXTMeshoptCompression, EXTTextureWebP, KHRMeshQuantization } from '@gltf-transform/extensions';
import { MeshoptDecoder } from 'meshoptimizer';

const [file, mode] = process.argv.slice(2);
await MeshoptDecoder.ready;
const io = new NodeIO()
  .registerExtensions([EXTMeshoptCompression, EXTTextureWebP, KHRMeshQuantization])
  .registerDependencies({ 'meshopt.decoder': MeshoptDecoder });
const doc = await io.read(file);
const root = doc.getRoot();

const fmt = (a) => a.map((v) => +v.toFixed(4)).join(', ');
function walk(node, depth) {
  const t = node.getTranslation();
  const r = node.getRotation();
  const s = node.getScale();
  const mesh = node.getMesh();
  console.log(
    `${'  '.repeat(depth)}${node.getName()}  T[${fmt(t)}] R[${fmt(r)}] S[${fmt(s)}]${mesh ? ` mesh=${mesh.getName()}` : ''}`,
  );
  node.listChildren().forEach((c) => walk(c, depth + 1));
}
for (const scene of root.listScenes()) scene.listChildren().forEach((n) => walk(n, 0));

for (const mesh of root.listMeshes()) {
  console.log('MESH', mesh.getName(), 'targets', mesh.listPrimitives()[0].listTargets().length, 'extras', JSON.stringify(mesh.getExtras()));
  mesh.listPrimitives().forEach((p, i) => {
    console.log(' prim', i, 'mat', p.getMaterial()?.getName(), 'tris', (p.getIndices()?.getCount() ?? 0) / 3);
  });
}
for (const skin of root.listSkins()) console.log('SKIN joints', skin.listJoints().length, 'skeleton', skin.getSkeleton()?.getName());
for (const anim of root.listAnimations()) {
  const chans = anim.listChannels();
  console.log('ANIM', anim.getName(), 'channels', chans.length);
  if (mode === 'tracks') {
    for (const c of chans) {
      const s = c.getSampler();
      console.log('   ', c.getTargetNode()?.getName(), c.getTargetPath(), s.getInterpolation(), s.getInput().getCount());
    }
  }
}
