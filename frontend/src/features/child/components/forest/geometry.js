import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';

/** Small seeded RNG so every visit (and every screenshot) builds the same forest. */
export function mulberry32(seed) {
  let a = seed >>> 0;
  return () => {
    a += 0x6d2b79f5;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * Centre line of the dirt path. u is the distance ahead of the avatar
 * (u = -z). The same formula lives in the ground shader (see ground.glsl.js),
 * keep the two in sync.
 */
export function pathX(u) {
  const amp = 0.35 + 0.09 * Math.min(Math.max(u, 0), 40);
  return amp * Math.sin(0.16 * u) + 0.45 * amp * Math.sin(0.41 * u + 1.3) - 0.45 * 0.35 * Math.sin(1.3);
}

export const PATH_HALF_WIDTH = 0.85;

function hash3(x, y, z) {
  const s = Math.sin(x * 127.1 + y * 311.7 + z * 74.7) * 43758.5453;
  return s - Math.floor(s);
}

/**
 * Many thin tapered blades in one geometry (one instance = one tuft). Every vertex carries
 *   aH     0 at the root to 1 at the tip (drives the bend, the colour and the flutter)
 *   aBase  this blade's root, in tuft space: the shader bends the blade by a rotation about it
 *   aSide  half the blade width at this vertex, signed, in tuft space: far blades widen along it
 * `near` blades have 5 triangles (4 rows, a curved arch), far blades 3.
 */
export function makeTuftGeometry(seed = 7, blades = 6, near = false) {
  const rng = mulberry32(seed);
  const pos = [];
  const aH = [];
  const aBase = [];
  const aSide = [];
  const levels = near ? [0, 0.4, 0.75] : [0, 0.55];
  const widths = near ? [1, 0.82, 0.5] : [1, 0.66];
  for (let b = 0; b < blades; b += 1) {
    const yaw = rng() * Math.PI * 2;
    const h = 0.5 + rng() * 0.6;
    const w = 0.06 + rng() * 0.035;
    const lean = 0.1 + rng() * 0.3;
    const ox = (rng() - 0.5) * 0.34;
    const oz = (rng() - 0.5) * 0.34;
    const dx = Math.cos(yaw);
    const dz = Math.sin(yaw);
    const sx = -dz;
    const sz = dx;
    const push = (x, y, z, f, side) => {
      pos.push(x, y, z);
      aH.push(f);
      aBase.push(ox, 0, oz);
      aSide.push(sx * side, 0, sz * side);
    };
    // rows: [left, right] at each level, then the tip
    const row = levels.map((f, i) => {
      const off = lean * h * f * f;
      const hw = (w * widths[i]) / 2;
      const cx = ox + dx * off;
      const cz = oz + dz * off;
      return { f, y: h * f, l: [cx - sx * hw, cz - sz * hw, -hw], r: [cx + sx * hw, cz + sz * hw, hw] };
    });
    const tip = { x: ox + dx * lean * h, y: h, z: oz + dz * lean * h };
    const vL = (r) => push(r.l[0], r.y, r.l[1], r.f, r.l[2]);
    const vR = (r) => push(r.r[0], r.y, r.r[1], r.f, r.r[2]);
    for (let i = 0; i < row.length - 1; i += 1) {
      const lo = row[i];
      const hi = row[i + 1];
      vL(lo); vR(lo); vL(hi);
      vR(lo); vR(hi); vL(hi);
    }
    const top = row[row.length - 1];
    vL(top); vR(top);
    push(tip.x, tip.y, tip.z, 1, 0);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('aH', new THREE.Float32BufferAttribute(aH, 1));
  g.setAttribute('aBase', new THREE.Float32BufferAttribute(aBase, 3));
  g.setAttribute('aSide', new THREE.Float32BufferAttribute(aSide, 3));
  return g;
}

/**
 * A flower: thin stem plus a head that faces the camera (+z). The head is one
 * quad; the material paints the round dandelion or the petals on it, which
 * reads far more like the paintings than a polygon and costs 2 triangles.
 * aHead is 0 on the stem and 1 on the head, aUv spans -1..1 across the head.
 */
export function makeFlowerGeometry(radius, stemHeight = 0.55) {
  const pos = [];
  const aH = [];
  const aHead = [];
  const aUv = [];
  const push = (x, y, z, h, head, u = 0, v = 0) => {
    pos.push(x, y, z);
    aH.push(h);
    aHead.push(head);
    aUv.push(u, v);
  };
  const sw = 0.011;
  const bend = 0.05;
  push(-sw, 0, 0, 0, 0);
  push(sw, 0, 0, 0, 0);
  push(-sw * 0.7 + bend * 0.5, stemHeight * 0.5, 0, 0.5, 0);
  push(sw, 0, 0, 0, 0);
  push(sw * 0.7 + bend * 0.5, stemHeight * 0.5, 0, 0.5, 0);
  push(-sw * 0.7 + bend * 0.5, stemHeight * 0.5, 0, 0.5, 0);
  push(-sw * 0.7 + bend * 0.5, stemHeight * 0.5, 0, 0.5, 0);
  push(sw * 0.7 + bend * 0.5, stemHeight * 0.5, 0, 0.5, 0);
  push(-sw * 0.5 + bend, stemHeight, 0, 1, 0);
  push(sw * 0.7 + bend * 0.5, stemHeight * 0.5, 0, 0.5, 0);
  push(sw * 0.5 + bend, stemHeight, 0, 1, 0);
  push(-sw * 0.5 + bend, stemHeight, 0, 1, 0);
  const tilt = new THREE.Matrix4().makeRotationX(-0.35);
  const c = new THREE.Vector3(bend, stemHeight, 0);
  const corner = (u, v) => {
    const p = new THREE.Vector3(u * radius, v * radius, 0).applyMatrix4(tilt).add(c);
    push(p.x, p.y, p.z, 1, 1, u, v);
  };
  corner(-1, -1);
  corner(1, -1);
  corner(1, 1);
  corner(-1, -1);
  corner(1, 1);
  corner(-1, 1);
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('aH', new THREE.Float32BufferAttribute(aH, 1));
  g.setAttribute('aHead', new THREE.Float32BufferAttribute(aHead, 1));
  g.setAttribute('aUv', new THREE.Float32BufferAttribute(aUv, 2));
  return g;
}

/* ---------- trees (merged, vertex coloured, low poly) ---------- */

function colorize(geo, fn) {
  const p = geo.attributes.position;
  const colors = new Float32Array(p.count * 3);
  const c = new THREE.Color();
  for (let i = 0; i < p.count; i += 1) {
    fn(c, p.getX(i), p.getY(i), p.getZ(i));
    colors[i * 3] = c.r;
    colors[i * 3 + 1] = c.g;
    colors[i * 3 + 2] = c.b;
  }
  geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  return geo;
}

function blob(cx, cy, cz, r, squash, dark, light, lumpAmt = 0.18) {
  let g = new THREE.IcosahedronGeometry(1, 1);
  if (g.index) g = g.toNonIndexed();
  const p = g.attributes.position;
  for (let i = 0; i < p.count; i += 1) {
    const x = p.getX(i);
    const y = p.getY(i);
    const z = p.getZ(i);
    const k = 1 + (hash3(x * 3.1 + cx, y * 3.1 + cy, z * 3.1 + cz) - 0.5) * lumpAmt * 2;
    p.setXYZ(i, x * k * r + cx, y * k * r * squash + cy, z * k * r + cz);
  }
  // Soft, rounded shading like the painted trees: ellipsoid normals instead of faceted ones.
  const nrm = new Float32Array(p.count * 3);
  const n = new THREE.Vector3();
  for (let i = 0; i < p.count; i += 1) {
    n.set((p.getX(i) - cx) / r, (p.getY(i) - cy) / (r * squash * squash), (p.getZ(i) - cz) / r);
    n.y += 0.25; // a little sky light on every blob
    n.normalize();
    nrm[i * 3] = n.x;
    nrm[i * 3 + 1] = n.y;
    nrm[i * 3 + 2] = n.z;
  }
  g.setAttribute('normal', new THREE.BufferAttribute(nrm, 3));
  const d = new THREE.Color(dark);
  const l = new THREE.Color(light);
  colorize(g, (c, x, y) => {
    const t = THREE.MathUtils.clamp(((y - cy) / (r * squash) + 1) * 0.5, 0, 1);
    c.copy(d).lerp(l, t ** 1.3);
  });
  return g;
}

function trunk(height, r0, r1, sides, color, dark) {
  let g = new THREE.CylinderGeometry(r1, r0, height, sides, 1, true);
  g = g.toNonIndexed();
  g.translate(0, height / 2, 0);
  const a = new THREE.Color(color);
  const b = new THREE.Color(dark);
  colorize(g, (c, x, y) => c.copy(b).lerp(a, y / height));
  return g;
}

function cone(r, h, y, sides, dark, light) {
  let g = new THREE.ConeGeometry(r, h, sides, 1, true);
  g = g.toNonIndexed();
  g.translate(0, y + h / 2, 0);
  const a = new THREE.Color(dark);
  const b = new THREE.Color(light);
  colorize(g, (c, x, yy) => c.copy(a).lerp(b, THREE.MathUtils.clamp((yy - y) / h, 0, 1)));
  return g;
}

/**
 * Merge the parts of a tree and give every vertex its sway weights for the wind shader:
 *   aSway  0 at the foot, 1 at the top of the crown, eased (pow 1.6), times `amp`
 *   aLeaf  1 on the leafy parts, 0 on the trunk (branch motion and leaf flutter only act on leaves)
 */
function mergeParts(parts, leafFlags, amp = 1) {
  let maxY = 0.001;
  parts.forEach((g) => {
    const p = g.attributes.position;
    for (let i = 0; i < p.count; i += 1) maxY = Math.max(maxY, p.getY(i));
  });
  parts.forEach((g, k) => {
    if (g.attributes.uv) g.deleteAttribute('uv');
    const p = g.attributes.position;
    const sway = new Float32Array(p.count);
    const leaf = new Float32Array(p.count);
    for (let i = 0; i < p.count; i += 1) {
      sway[i] = amp * Math.pow(Math.max(p.getY(i), 0) / maxY, 1.6);
      leaf[i] = leafFlags[k] ? 1 : 0;
    }
    g.setAttribute('aSway', new THREE.BufferAttribute(sway, 1));
    g.setAttribute('aLeaf', new THREE.BufferAttribute(leaf, 1));
  });
  return mergeGeometries(parts, false);
}

export function makeBroadleafGeometry() {
  // a crown of four round clumps, like the painted trees
  return mergeParts([
    trunk(2.2, 0.22, 0.13, 6, '#7a5a3e', '#3b2c20'),
    blob(0, 2.75, 0.1, 1.3, 0.88, '#2f6a35', '#a6c844', 0.1),
    blob(-0.95, 2.35, 0.35, 0.95, 0.88, '#2a6034', '#8fbd3e', 0.1),
    blob(0.9, 2.5, -0.15, 0.95, 0.88, '#2c6436', '#98c242', 0.1),
    blob(0.05, 3.55, -0.1, 1.0, 0.88, '#356e36', '#bcd64e', 0.1),
  ], [false, true, true, true, true]);
}

export function makePineGeometry() {
  return mergeParts([
    trunk(1.4, 0.16, 0.1, 6, '#5a4230', '#33261b'),
    cone(1.15, 2.3, 1.2, 7, '#133d2c', '#3c7a4c'),
    cone(0.9, 2.0, 2.5, 7, '#164531', '#468658'),
    cone(0.6, 1.8, 3.7, 7, '#1a4d36', '#58986a'),
  ], [false, true, true, true], 0.8);
}

export function makeBushGeometry() {
  return mergeParts([blob(0, 0.45, 0, 0.9, 0.65, '#2d6a34', '#9cc440', 0.12)], [true], 0.45);
}
