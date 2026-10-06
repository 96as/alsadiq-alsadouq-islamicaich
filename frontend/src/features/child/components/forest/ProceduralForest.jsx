/* The frame loop writes instance attributes by design. */
/* eslint-disable react-hooks/immutability */
import { useEffect, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { useForest } from './forestContext';
import { COUNTS, GRASS_RINGS } from './quality';
import { addTriangles } from './runtime';
import {
  PATH_HALF_WIDTH,
  makeBroadleafGeometry,
  makeBushGeometry,
  makeFlowerGeometry,
  makePineGeometry,
  makeTuftGeometry,
  mulberry32,
  pathX,
} from './geometry';
import { createGroundMaterial, createTreeMaterial, createVegetationMaterial } from './materials';
import { FLOWER_SPRING, TAU, gustWith, springStep } from './wind/windField';

const tmpObj = new THREE.Object3D();

function triCount(geometry, instances) {
  const per = geometry.index ? geometry.index.count / 3 : geometry.attributes.position.count / 3;
  return Math.round(per * instances);
}

/**
 * Builds an InstancedMesh from a list of [x, y, z, yaw, scale, r, g, b] rows. With a cullMargin the mesh is a chunk
 * that is culled as one: its sphere covers the instances plus the tallest blade and the widest bend.
 */
function buildInstanced(geometry, material, rows, tinted, cullMargin = 0) {
  const mesh = new THREE.InstancedMesh(geometry, material, rows.length);
  if (tinted) {
    const tint = new Float32Array(rows.length * 3);
    rows.forEach((r, i) => {
      tint[i * 3] = r[5];
      tint[i * 3 + 1] = r[6];
      tint[i * 3 + 2] = r[7];
    });
    geometry.setAttribute('aTint', new THREE.InstancedBufferAttribute(tint, 3));
  }
  rows.forEach((r, i) => {
    tmpObj.position.set(r[0], r[1], r[2]);
    tmpObj.rotation.set(0, r[3], 0);
    tmpObj.scale.setScalar(r[4]);
    tmpObj.updateMatrix();
    mesh.setMatrixAt(i, tmpObj.matrix);
  });
  mesh.instanceMatrix.needsUpdate = true;
  mesh.frustumCulled = false;
  if (cullMargin > 0) {
    mesh.computeBoundingSphere();
    mesh.boundingSphere.radius += cullMargin;
    mesh.frustumCulled = true;
  }
  return mesh;
}

/** Scatter points over the meadow, thicker near the camera, clear of the dirt path. */
function scatter(count, seed, { clearPath = 0.3, uMin = -5, uMax = 46, spread = 0.7, bias = 1.5, base = 2.5, xBias = 1 } = {}) {
  const rng = mulberry32(seed);
  const pts = [];
  let guard = 0;
  while (pts.length < count && guard < count * 12) {
    guard += 1;
    const u = uMin + (uMax - uMin) * rng() ** bias;
    const r = (rng() - 0.5) * 2;
    const x = Math.sign(r) * Math.abs(r) ** xBias * (base + Math.max(u, 0) * spread);
    if (Math.abs(x - pathX(u)) < PATH_HALF_WIDTH + clearPath) continue;
    pts.push({ x, z: -u, u, rng });
  }
  return pts;
}

const GREEN_TINTS = ['#ffffff', '#e6f4c8', '#cfe9a2', '#f6ffd2', '#b9dc86'];
const DANDELION_TINTS = ['#ffd21f', '#ffd21f', '#ffdc3c', '#ffc928', '#ffe766', '#fff6d6'];
const BLOOM_TINTS = ['#ffb3d4', '#ffc2dc', '#ffffff', '#fff4f8', '#ffffff', '#e9c8ff'];

const c = (hex) => new THREE.Color(hex);

/**
 * The grass: 4 depth rings x 3 sectors (left of the path, the path, right of it) = 12 chunks, each its own
 * InstancedMesh so the ones outside the view are culled. The ring around the avatar has 5-triangle arched blades,
 * the rest 3-triangle blades that widen with distance in the shader. 6 blades per tuft.
 */
function buildGrass(tuftsPerRing, shared) {
  const near = makeTuftGeometry(11, 6, true);
  const far = makeTuftGeometry(11, 6, false);
  const mat = createVegetationMaterial(shared);
  const meshes = [];
  let tris = 0;
  let blades = 0;
  tuftsPerRing.forEach((count, ring) => {
    const [uMin, uMax] = GRASS_RINGS[ring];
    const geo = ring === 0 ? near : far;
    const sectors = [[], [], []];
    scatter(count, 101 + ring * 13, { clearPath: 0.05, uMin, uMax, bias: 1, base: 3, spread: 1.0, xBias: 1.5 }).forEach((p) => {
      const t = c(GREEN_TINTS[Math.floor(p.rng() * GREEN_TINTS.length)]);
      // a low carpet like the paintings, so the flowers stand above it; lowest
      // between the avatar and the camera, where tufts would loom over the view
      const r = p.rng();
      const sc = (0.38 + r * r * 0.6) * (p.u < 0 ? 0.8 : 1 + Math.min(p.u, 40) * 0.006);
      const dx = p.x - pathX(p.u);
      sectors[dx < -3 ? 0 : dx > 3 ? 2 : 1].push([p.x, 0, p.z, p.rng() * 6.283, sc, t.r, t.g, t.b]);
    });
    sectors.forEach((rows) => {
      if (!rows.length) return;
      meshes.push(buildInstanced(geo, mat, rows, true, 2));
      tris += triCount(geo, rows.length);
      blades += rows.length * 6;
    });
  });
  return { meshes, geos: [near, far], mat, tris, blades };
}

function buildFlowers(count, shared, seed, { radius, tints, hScale, kind, smoothEdges }) {
  const geo = makeFlowerGeometry(radius, 0.55);
  const mat = createVegetationMaterial(shared, { flower: true, kind, smoothEdges });
  const rows = scatter(count, seed, { clearPath: 0.1, uMax: 34 }).map((p) => {
    const t = c(tints[Math.floor(p.rng() * tints.length)]);
    const s = (0.75 + p.rng() * 0.6) * hScale;
    return [p.x, 0, p.z, (p.rng() - 0.5) * 0.9, s, t.r, t.g, t.b];
  });
  const mesh = buildInstanced(geo, mat, rows, true);
  // the head lean of the flowers that run a real spring (x: radians, y: 1 when valid); the others use the shader formula
  const lean = new Float32Array(rows.length * 2);
  const attr = new THREE.InstancedBufferAttribute(lean, 2);
  attr.setUsage(THREE.DynamicDrawUsage);
  geo.setAttribute('aLean', attr);
  return { mesh, geo, mat, tris: triCount(geo, rows.length), rows, lean, attr, kind };
}

const DEG = Math.PI / 180;
const HIST_BUCKETS = 96;
const HIST_STEP = 0.25; // metres per bucket

/**
 * Second-order springs on the heads of the flowers nearest the avatar (Motion Bible 7.4): they overshoot and settle
 * after a gust, which no formula in the shader can do. Everything is preallocated, nothing allocates per frame.
 * The ring is re-picked every 0.25 s with a distance histogram; flowers that leave it fall back to the formula in
 * the shader, which is the same target the spring chases.
 */
function makeSprings(sets, maxActive) {
  const per = Math.max(1, Math.floor(maxActive / sets.length));
  return sets.map((set) => {
    const n = set.rows.length;
    const px = new Float32Array(n);
    const pz = new Float32Array(n);
    const ph = new Float32Array(n);
    set.rows.forEach((r, i) => {
      px[i] = r[0];
      pz[i] = r[2];
      const k = r[0] * 7.31 + r[2] * 3.17;
      ph[i] = (k - Math.floor(k)) * TAU;
    });
    return {
      set,
      n,
      cap: per,
      px,
      pz,
      ph,
      dist: new Float32Array(n),
      act: new Uint8Array(n),
      list: new Int32Array(Math.ceil(per * 1.3)),
      count: 0,
      hist: new Int32Array(HIST_BUCKETS),
      states: Array.from({ length: n }, () => ({ y: 0, yd: 0, xp: 0, init: false })),
      preset: set.kind === 0 ? FLOWER_SPRING.dandelion : FLOWER_SPRING.bloom,
    };
  });
}

function repick(sp, fx, fz) {
  const { n, px, pz, dist, act, list, hist, cap, states } = sp;
  hist.fill(0);
  for (let i = 0; i < n; i += 1) {
    const dx = px[i] - fx;
    const dz = pz[i] - fz;
    const d = Math.sqrt(dx * dx + dz * dz);
    dist[i] = d;
    hist[Math.min(HIST_BUCKETS - 1, Math.floor(d / HIST_STEP))] += 1;
  }
  let cum = 0;
  let thr = HIST_BUCKETS * HIST_STEP;
  for (let b = 0; b < HIST_BUCKETS; b += 1) {
    cum += hist[b];
    if (cum >= cap) {
      thr = (b + 1) * HIST_STEP;
      break;
    }
  }
  const keep = thr * 1.2; // hysteresis: a flower already springing stays until it is clearly outside
  let m = 0;
  const lean = sp.set.lean;
  for (let i = 0; i < n; i += 1) {
    const d = dist[i];
    const on = d <= thr || (act[i] === 1 && d <= keep);
    if (on && m < list.length) {
      if (!act[i]) {
        act[i] = 1;
        states[i].init = false;
      }
      list[m] = i;
      m += 1;
    } else if (act[i]) {
      act[i] = 0;
      lean[i * 2 + 1] = 0;
    }
  }
  sp.count = m;
  sp.set.attr.needsUpdate = true;
}

function FlowerSprings({ sets, maxActive }) {
  const rt = useForest();
  const springs = useMemo(() => makeSprings(sets, maxActive), [sets, maxActive]);
  const clock = useMemo(() => ({ pick: -1 }), []);

  useFrame((_, dt) => {
    const d = Math.min(dt, 0.05);
    if (d <= 0) return;
    const t = rt.shared.uTime.value;
    const st = rt.wind;
    const gain = rt.shared.uWindGain.value;
    const mix = rt.shared.uWindMix.value.x;
    if (t - clock.pick > 0.25 || t < clock.pick) {
      clock.pick = t;
      springs.forEach((sp) => repick(sp, rt.stand.x, rt.stand.z));
    }
    springs.forEach((sp) => {
      const { px, pz, ph, list, states, preset } = sp;
      const lean = sp.set.lean;
      for (let j = 0; j < sp.count; j += 1) {
        const i = list[j];
        const s = gustWith(st, px[i], pz[i], 0.12) * gain;
        const target = (28 * s + 4 * Math.sin(TAU * 0.6 * t + ph[i])) * DEG * mix;
        lean[i * 2] = springStep(states[i], target, d, preset.f, preset.z, preset.r);
        lean[i * 2 + 1] = 1;
      }
      if (sp.count) sp.set.attr.needsUpdate = true;
    });
  });
  return null;
}

function buildTrees(counts, treeMat) {
  const out = [];
  const make = (geo, n, seed, place) => {
    const rng = mulberry32(seed);
    const rows = [];
    let guard = 0;
    while (rows.length < n && guard < n * 20) {
      guard += 1;
      const r = place(rng);
      if (r) rows.push(r);
    }
    const mesh = new THREE.InstancedMesh(geo, treeMat, rows.length);
    const col = new THREE.Color();
    rows.forEach((r, i) => {
      tmpObj.position.set(r.x, 0, r.z);
      tmpObj.rotation.set(0, r.yaw, 0);
      tmpObj.scale.set(r.s * r.sx, r.s, r.s * r.sx);
      tmpObj.updateMatrix();
      mesh.setMatrixAt(i, tmpObj.matrix);
      col.setHSL(r.h, r.sat, r.l);
      mesh.setColorAt(i, col);
    });
    mesh.instanceMatrix.needsUpdate = true;
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
    mesh.frustumCulled = false;
    out.push({ mesh, geo, tris: triCount(geo, rows.length) });
  };

  // Like the paintings: a forest edge on the left that recedes toward the
  // horizon, and open meadow on the right so the painted mountains stay in view.
  const broadGeo = makeBroadleafGeometry();
  make(broadGeo, counts.broadleaf, 301, (rng) => {
    const right = rng() < 0.1;
    const u = right ? 18 + rng() * 14 : 6 + rng() * 46;
    const x = right ? 7 + rng() * 6 + u * 0.12 : -(5.6 + rng() * 6.5 + u * 0.08);
    if (Math.abs(x - pathX(u)) < 4) return null;
    const s = right ? 0.6 + rng() * 0.4 : 0.8 + rng() * 0.55 + u * 0.008;
    return { x, z: -u, yaw: rng() * 6.283, s, sx: 0.9 + rng() * 0.3, h: 0.24 + rng() * 0.1, sat: 0.75, l: 0.8 + rng() * 0.2 };
  });

  const pineGeo = makePineGeometry();
  make(pineGeo, counts.pines, 302, (rng) => {
    // left side only: the painted backdrop already has the small pines under the mountains
    const u = 10 + rng() * 46;
    const x = -(8.5 + rng() * 9 + u * 0.1);
    if (Math.abs(x - pathX(u)) < 3) return null;
    const s = 1.0 + rng() * 1.0 + u * 0.01;
    return { x, z: -u, yaw: rng() * 6.283, s, sx: 0.85 + rng() * 0.25, h: 0.4 + rng() * 0.05, sat: 0.7, l: 0.8 + rng() * 0.2 };
  });

  // round bushes on both sides of the path, as at the vanishing point of the paintings
  const bushGeo = makeBushGeometry();
  make(bushGeo, counts.bushes, 303, (rng) => {
    const side = rng() < 0.6 ? -1 : 1;
    const u = 6 + rng() * 30;
    const x = pathX(u) + side * (2.6 + rng() * 4 + u * 0.1);
    return { x, z: -u, yaw: rng() * 6.283, s: 0.5 + rng() * 0.55, sx: 0.9 + rng() * 0.4, h: 0.24 + rng() * 0.08, sat: 0.75, l: 0.85 + rng() * 0.15 };
  });
  return out;
}

/** Ground with a winding path, wind-bent grass and flowers, round trees and pines. */
export default function ProceduralForest() {
  const rt = useForest();
  const counts = COUNTS[rt.quality];

  const world = useMemo(() => {
    const ground = createGroundMaterial(rt.shared);
    const grass = buildGrass(counts.tufts, rt.shared);
    const smoothEdges = rt.quality === 'high'; // the high tier has MSAA on
    const dandelions = buildFlowers(counts.dandelions, rt.shared, 202, { radius: 0.075, tints: DANDELION_TINTS, hScale: 1, kind: 0, smoothEdges });
    const blooms = buildFlowers(counts.blooms, rt.shared, 203, { radius: 0.065, tints: BLOOM_TINTS, hScale: 0.85, kind: 1, smoothEdges });
    const treeMat = createTreeMaterial(rt.shared);
    const trees = buildTrees(counts, treeMat);
    return { ground, grass, dandelions, blooms, treeMat, trees };
  }, [counts, rt]);

  const flowerSets = useMemo(() => [world.dandelions, world.blooms], [world]);

  useEffect(() => {
    addTriangles(rt, 'ground', 2);
    addTriangles(rt, 'grass', world.grass.tris);
    addTriangles(rt, 'dandelions', world.dandelions.tris);
    addTriangles(rt, 'blooms', world.blooms.tris);
    addTriangles(rt, 'trees', world.trees.reduce((a, t) => a + t.tris, 0));
    rt.stats.blades = world.grass.blades;
    return () => {
      ['ground', 'grass', 'dandelions', 'blooms', 'trees'].forEach((k) => addTriangles(rt, k, 0));
      world.ground.dispose();
      [world.dandelions, world.blooms].forEach((p) => {
        p.geo.dispose();
        p.mat.dispose();
        p.mesh.dispose();
      });
      world.grass.meshes.forEach((m) => m.dispose());
      world.grass.geos.forEach((g) => g.dispose());
      world.grass.mat.dispose();
      world.trees.forEach((t) => {
        t.geo.dispose();
        t.mesh.dispose();
      });
      world.treeMat.dispose();
    };
  }, [rt, world]);

  return (
    <group>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, -30]} material={world.ground}>
        <planeGeometry args={[150, 150]} />
      </mesh>
      {world.grass.meshes.map((m) => (
        <primitive key={m.uuid} object={m} />
      ))}
      <primitive object={world.dandelions.mesh} />
      <primitive object={world.blooms.mesh} />
      {world.trees.map((t) => (
        <primitive key={t.mesh.uuid} object={t.mesh} />
      ))}
      <FlowerSprings sets={flowerSets} maxActive={counts.springs} />
    </group>
  );
}
