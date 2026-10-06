/* The frame loop drives meshes, materials and the runtime object by design. */
/* eslint-disable react-hooks/immutability */
import { useEffect, useMemo, useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import { useForest } from './forestContext';
import { addTriangles } from './runtime';
import { createPointsMaterial } from './materials';

/**
 * Three things to tap in Sadiq's forest: a brass lantern on a post, an open book on a stump and a bulbul.
 * All procedural, vertex-coloured, no textures. Five draw calls in total (static, page, bird, glow, sparks).
 *
 * The 3D objects only react. The tap targets are real DOM buttons placed over `rt.propBox` (see
 * DemoHeroScene), and they tell this component with a `prop-tap` event on `rt.bus`. State flows out through
 * `rt.props` (hover in; lit, asleep, flying out), `rt.propBox` (screen boxes) and `rt.gaze` (Sadiq looks).
 */

// Where the props stand, relative to Sadiq's feet. Wide stages first, portrait phones second.
const LAYOUT = {
  wide: { lantern: [1.0, 0, -0.3], book: [-0.9, 0, 0.12] },
  narrow: { lantern: [0.62, 0, -0.2], book: [-0.6, 0, 0.14] },
};

// The lantern body centre, in post-local coordinates (the post stands at the origin).
const LANTERN_AT = [-0.3, 0.74, 0];
const POST_TOP = 1.0;
const BOOK_PIVOT = 0.4; // book height above the ground
const BOOK_TILT = 0.95; // radians: the page leans toward the camera so it reads from a low view
const SUN_DIR = new THREE.Vector3(-0.35, 0.8, 0.5).normalize();
const BRASS = '#c98208';
const WOOD = '#7d5230';

const V = new THREE.Vector3();
const N = new THREE.Vector3();
const M = new THREE.Matrix4();
const Q = new THREE.Quaternion();
const E = new THREE.Euler();
const ONE = new THREE.Vector3(1, 1, 1);

/** Bakes one primitive into a vertex-coloured, non-indexed piece with a cheap fake light. */
function part(geo, color, o = {}) {
  const { pos = [0, 0, 0], rot = [0, 0, 0], scale = [1, 1, 1], group = null, attr, colorFn } = o;
  const g = geo.index ? geo.toNonIndexed() : geo.clone();
  g.deleteAttribute('uv');
  const m = new THREE.Matrix4().compose(new THREE.Vector3(...pos), new THREE.Quaternion().setFromEuler(new THREE.Euler(...rot)), new THREE.Vector3(...scale));
  if (group) m.premultiply(group);
  g.applyMatrix4(m);
  const count = g.attributes.position.count;
  const col = new Float32Array(count * 3);
  const base = new THREE.Color(color);
  const tmp = new THREE.Color();
  for (let i = 0; i < count; i += 1) {
    N.fromBufferAttribute(g.attributes.normal, i);
    const shade = 0.6 + 0.4 * Math.max(N.dot(SUN_DIR), 0) + 0.08 * Math.max(N.y, 0);
    tmp.copy(colorFn ? colorFn(Math.floor(i / 3), base) : base);
    col[i * 3] = Math.min(tmp.r * shade, 1);
    col[i * 3 + 1] = Math.min(tmp.g * shade, 1);
    col[i * 3 + 2] = Math.min(tmp.b * shade, 1);
  }
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  if (attr) g.setAttribute(attr[0], new THREE.Float32BufferAttribute(new Float32Array(count).fill(attr[1]), 1));
  g.deleteAttribute('normal');
  return g;
}

const box = (w, h, d) => new THREE.BoxGeometry(w, h, d);
const cyl = (rt, rb, h, seg) => new THREE.CylinderGeometry(rt, rb, h, seg);
const ball = (r, w = 7, h = 5) => new THREE.SphereGeometry(r, w, h);

const GLASS_DIM = [new THREE.Color('#b78f31'), new THREE.Color('#4b8c86')];
const GLASS_LIT = [new THREE.Color('#ffd25a'), new THREE.Color('#72e4d2')];

/** The post, the lantern frame, the book stump and the book: one draw call. aProp picks the layout slot. */
function buildStatic() {
  const L = (p) => ({ ...p, attr: ['aProp', 0] });
  const lanternParts = [];
  // post, foot and arm
  lanternParts.push(part(box(0.06, POST_TOP, 0.06), WOOD, L({ pos: [0, POST_TOP / 2, 0] })));
  lanternParts.push(part(cyl(0.07, 0.1, 0.07, 6), '#9b9486', L({ pos: [0, 0.035, 0] })));
  lanternParts.push(part(box(0.1, 0.05, 0.1), WOOD, L({ pos: [0, POST_TOP + 0.02, 0] })));
  lanternParts.push(part(box(0.34, 0.04, 0.04), WOOD, L({ pos: [-0.15, POST_TOP - 0.04, 0] })));
  lanternParts.push(part(box(0.012, 0.09, 0.012), BRASS, L({ pos: [LANTERN_AT[0], LANTERN_AT[1] + 0.3, 0] })));
  // the lantern: dome, ring, hexagon of glass, ribs, base
  const [lx, ly] = LANTERN_AT;
  lanternParts.push(part(new THREE.ConeGeometry(0.1, 0.11, 6), BRASS, L({ pos: [lx, ly + 0.17, 0] })));
  lanternParts.push(part(new THREE.TorusGeometry(0.022, 0.007, 4, 8), BRASS, L({ pos: [lx, ly + 0.245, 0], rot: [Math.PI / 2, 0, 0] })));
  lanternParts.push(part(cyl(0.078, 0.062, 0.22, 6), '#fff', L({
    pos: [lx, ly, 0],
    colorFn: (t, base) => (t < 12 ? GLASS_DIM[Math.floor(t / 2) % 2] : base.set(BRASS)),
  })));
  for (let i = 0; i < 6; i += 1) {
    const a = (i / 6) * Math.PI * 2;
    lanternParts.push(part(box(0.014, 0.23, 0.014), BRASS, L({ pos: [lx + Math.sin(a) * 0.072, ly, Math.cos(a) * 0.072], rot: [0, a, 0] })));
  }
  lanternParts.push(part(cyl(0.075, 0.06, 0.025, 6), BRASS, L({ pos: [lx, ly - 0.122, 0] })));
  lanternParts.push(part(new THREE.ConeGeometry(0.045, 0.07, 6), BRASS, L({ pos: [lx, ly - 0.17, 0], rot: [Math.PI, 0, 0] })));

  // the book: a stump, a wooden rest, a green cover and two cream page blocks, tilted toward the camera
  const B = (p) => ({ ...p, attr: ['aProp', 1] });
  const tilt = new THREE.Matrix4().compose(new THREE.Vector3(0, BOOK_PIVOT, 0), new THREE.Quaternion().setFromEuler(new THREE.Euler(BOOK_TILT, 0, 0)), ONE);
  const bookParts = [];
  bookParts.push(part(cyl(0.2, 0.26, BOOK_PIVOT, 9), '#8b5e3a', B({ pos: [0, BOOK_PIVOT / 2, 0] })));
  bookParts.push(part(cyl(0.19, 0.19, 0.012, 9), '#d2a56a', B({ pos: [0, BOOK_PIVOT + 0.004, 0] })));
  bookParts.push(part(box(0.58, 0.03, 0.4), WOOD, B({ pos: [0, -0.02, 0], group: tilt })));
  bookParts.push(part(box(0.54, 0.035, 0.36), '#1d6b3c', B({ pos: [0, 0.0125, 0], group: tilt })));
  bookParts.push(part(box(0.5, 0.008, 0.33), '#e0b02a', B({ pos: [0, 0.004, 0], group: tilt })));
  bookParts.push(part(box(0.235, 0.034, 0.31), '#fbf4e2', B({ pos: [-0.122, 0.048, 0], rot: [0, 0, 0.07], group: tilt })));
  bookParts.push(part(box(0.235, 0.034, 0.31), '#f3ead4', B({ pos: [0.122, 0.048, 0], rot: [0, 0, -0.07], group: tilt })));
  bookParts.push(part(box(0.02, 0.045, 0.33), '#14532d', B({ pos: [0, 0.03, 0], group: tilt })));
  return mergeGeometries([...lanternParts, ...bookParts], false);
}

/** The flipping page, hinged on the book's spine (x = 0 is the hinge, the page extends to +x). */
function buildPage() {
  const g = new THREE.PlaneGeometry(0.225, 0.3);
  g.rotateX(-Math.PI / 2);
  g.translate(0.1125 + 0.004, 0, 0);
  return g;
}

/** A white-spectacled bulbul: grey-brown, dark head, white eye rings, a touch of yellow under the tail. aWing marks the wing tips. */
function buildBird() {
  const W = (p) => ({ ...p, attr: ['aWing', 0] });
  const parts = [];
  parts.push(part(ball(0.06), '#8d7761', W({ pos: [0, 0, 0], scale: [0.85, 0.88, 1.35] })));
  parts.push(part(ball(0.05), '#d9d0c0', W({ pos: [0, -0.022, 0.018], scale: [0.78, 0.7, 1.15] })));
  parts.push(part(ball(0.042), '#2c2723', W({ pos: [0, 0.052, 0.072] })));
  parts.push(part(new THREE.ConeGeometry(0.013, 0.036, 4), '#241f1c', W({ pos: [0, 0.046, 0.12], rot: [Math.PI / 2, 0, 0] })));
  parts.push(part(ball(0.011, 5, 4), '#ffffff', W({ pos: [0.03, 0.06, 0.096] })));
  parts.push(part(ball(0.011, 5, 4), '#ffffff', W({ pos: [-0.03, 0.06, 0.096] })));
  parts.push(part(box(0.045, 0.01, 0.1), '#6b5846', W({ pos: [0, 0.0, -0.125], rot: [-0.18, 0, 0] })));
  parts.push(part(ball(0.026, 5, 4), '#f0c92c', W({ pos: [0, -0.02, -0.098], scale: [1, 0.7, 1.1] })));
  // wings: a flat fan on each side, lifted by the vertex shader
  [-1, 1].forEach((s) => {
    const g = new THREE.BufferGeometry();
    const p = [
      s * 0.035, 0.025, 0.045, s * 0.15, 0.02, -0.02, s * 0.05, 0.025, -0.07,
      s * 0.035, 0.025, 0.045, s * 0.05, 0.025, -0.07, s * 0.02, 0.025, -0.04,
    ];
    g.setAttribute('position', new THREE.Float32BufferAttribute(p, 3));
    const c = [];
    for (let i = 0; i < 6; i += 1) {
      const tip = i === 1 || i === 2 ? 0.55 : 0.78;
      c.push(0.43 * tip, 0.36 * tip, 0.3 * tip);
    }
    g.setAttribute('color', new THREE.Float32BufferAttribute(c, 3));
    g.setAttribute('aWing', new THREE.Float32BufferAttribute(new Float32Array(6).fill(1), 1));
    parts.push(g);
  });
  return mergeGeometries(parts, false);
}

const GLOW_VERT = /* glsl */ `
  attribute vec2 aUv;
  attribute float aKind;
  attribute vec3 aCol;
  varying vec2 vUv;
  varying float vKind;
  varying vec3 vCol;
  void main() {
    vUv = aUv;
    vKind = aKind;
    vCol = aCol;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const GLOW_FRAG = /* glsl */ `
  uniform float uGlow;
  varying vec2 vUv;
  varying float vKind;
  varying vec3 vCol;
  void main() {
    float r = length(vUv - 0.5) * 2.0;
    vec3 c;
    float a;
    if (vKind < 0.5) {
      a = pow(smoothstep(1.0, 0.0, r), 2.0) * 0.55 * uGlow;
      c = vec3(1.0, 0.74, 0.32);
    } else if (vKind < 1.5) {
      a = pow(smoothstep(1.0, 0.0, r), 1.5) * 0.5 * uGlow;
      c = vec3(1.0, 0.7, 0.28);
    } else {
      a = 1.0;
      c = vCol * uGlow * 0.8;
    }
    gl_FragColor = vec4(c, a);
    #include <colorspace_fragment>
  }
`;

/** The lantern's glow: lit glass panes, a soft halo and a pool of light on the path. All additive, one draw call. */
function buildGlow() {
  const pieces = [];
  const mk = (positions, uvs, kind, cols) => {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    g.setAttribute('aUv', new THREE.Float32BufferAttribute(uvs, 2));
    const n = positions.length / 3;
    g.setAttribute('aKind', new THREE.Float32BufferAttribute(new Float32Array(n).fill(kind), 1));
    g.setAttribute('aCol', new THREE.Float32BufferAttribute(cols || new Float32Array(n * 3).fill(1), 3));
    return g;
  };
  const quad = (hx, hy, z) => [-hx, -hy, z, hx, -hy, z, hx, hy, z, -hx, -hy, z, hx, hy, z, -hx, hy, z];
  const uv = [0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1];
  pieces.push(mk(quad(0.7, 0.7, 0.05), uv, 0));
  // the pool of light: a flat quad on the ground (the lantern centre is LANTERN_AT[1] above it)
  const gy = -LANTERN_AT[1] + 0.02;
  pieces.push(mk([-0.85, gy, 0.55, 0.85, gy, 0.55, 0.85, gy, -0.55, -0.85, gy, 0.55, 0.85, gy, -0.55, -0.85, gy, -0.55], uv, 1));
  // lit panes
  const hex = new THREE.CylinderGeometry(0.081, 0.065, 0.22, 6, 1, true).toNonIndexed();
  const pos = hex.attributes.position.array;
  const cols = new Float32Array(pos.length);
  for (let i = 0; i < pos.length / 3; i += 1) {
    const c = GLASS_LIT[Math.floor(Math.floor(i / 3) / 2) % 2];
    cols[i * 3] = c.r;
    cols[i * 3 + 1] = c.g;
    cols[i * 3 + 2] = c.b;
  }
  pieces.push(mk(Array.from(pos), new Array((pos.length / 3) * 2).fill(0.5), 2, cols));
  return mergeGeometries(pieces, false);
}

const catmull = (pts) => new THREE.CatmullRomCurve3(pts, false, 'catmullrom', 0.5);
const smooth = (u) => u * u * (3 - 2 * u);
const clamp = (v, a, b) => Math.min(Math.max(v, a), b);
const rand = (a, b) => a + Math.random() * (b - a);

// projectBox works on its own vector: callers pass the shared V as `world`, and transforming V in place
// would turn the world point into view space before it is projected (the buttons then missed the props).
const PB = new THREE.Vector3();
function projectBox(out, world, rW, rH, camera, size, fov) {
  PB.copy(world);
  const depth = -PB.applyMatrix4(camera.matrixWorldInverse).z;
  PB.copy(world).project(camera);
  const pxPerUnit = size.height / (2 * Math.max(depth, 0.2) * Math.tan((fov * Math.PI) / 360));
  out.x = (PB.x * 0.5 + 0.5) * size.width;
  out.y = (-PB.y * 0.5 + 0.5) * size.height;
  out.w = 2 * rW * pxPerUnit;
  out.h = 2 * rH * pxPerUnit;
  out.visible = depth > 0.2 && Math.abs(PB.x) < 1.15 && Math.abs(PB.y) < 1.15;
}

export default function ForestProps() {
  const rt = useForest();
  const { camera, size, gl, setDpr } = useThree();

  const built = useMemo(() => {
    const staticGeo = buildStatic();
    const pageGeo = buildPage();
    const birdGeo = buildBird();
    const glowGeo = buildGlow();

    const uniforms = {
      uOff: { value: [new THREE.Vector3(), new THREE.Vector3()] },
      uScale: { value: [1, 1] },
    };
    const tintMat = (extra) => {
      const m = new THREE.MeshBasicMaterial({ vertexColors: true, fog: false, side: THREE.DoubleSide });
      m.onBeforeCompile = extra;
      return m;
    };
    const staticMat = tintMat((shader) => {
      shader.uniforms.uOff = uniforms.uOff;
      shader.uniforms.uScale = uniforms.uScale;
      shader.vertexShader = shader.vertexShader
        .replace('#include <common>', '#include <common>\nattribute float aProp;\nuniform vec3 uOff[2];\nuniform float uScale[2];')
        .replace('#include <begin_vertex>', 'int slot = int(aProp + 0.5);\nvec3 transformed = position * uScale[slot] + uOff[slot];');
    });
    const flap = { value: 0 };
    const fold = { value: 1 };
    const birdMat = tintMat((shader) => {
      shader.uniforms.uFlap = flap;
      shader.uniforms.uFold = fold;
      shader.vertexShader = shader.vertexShader
        .replace('#include <common>', '#include <common>\nattribute float aWing;\nuniform float uFlap;\nuniform float uFold;')
        .replace(
          '#include <begin_vertex>',
          'vec3 transformed = vec3(position);\nfloat ax = abs(position.x);\ntransformed.y += aWing * ax * uFlap * 2.6;\ntransformed.x = sign(position.x) * mix(ax, ax * 0.32, aWing * uFold);',
        );
    });
    const pageMat = new THREE.MeshBasicMaterial({ color: '#fbf4e2', side: THREE.DoubleSide, fog: false });
    const glowMat = new THREE.ShaderMaterial({
      vertexShader: GLOW_VERT,
      fragmentShader: GLOW_FRAG,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      fog: false,
      uniforms: { uGlow: { value: 0 } },
    });

    // eight to ten sparks that spiral around the lantern when it is tapped
    const SPARKS = 10;
    const sparkGeo = new THREE.BufferGeometry();
    sparkGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(SPARKS * 3), 3));
    const seeds = new Float32Array(SPARKS * 4);
    // fixed seeds (a golden-ratio sequence): the sparks look scattered and the render stays pure
    for (let i = 0; i < SPARKS * 4; i += 1) seeds[i] = (i * 0.6180339887 + 0.137) % 1;
    sparkGeo.setAttribute('aSeed', new THREE.BufferAttribute(seeds, 4));
    const sparkMat = createPointsMaterial(rt.shared, { size: 1.6, color: '#ffe58a', isStatic: true, blink: 3, alpha: 0 });

    const tris = [staticGeo, pageGeo, birdGeo, glowGeo].reduce((a, g) => a + (g.index ? g.index.count : g.attributes.position.count) / 3, 0);
    return { staticGeo, pageGeo, birdGeo, glowGeo, uniforms, staticMat, birdMat, pageMat, glowMat, flap, fold, sparkGeo, sparkMat, SPARKS, tris };
  }, [rt]);

  useEffect(() => {
    addTriangles(rt, 'props', Math.round(built.tris));
    return () => {
      addTriangles(rt, 'props', 0);
      [built.staticGeo, built.pageGeo, built.birdGeo, built.glowGeo, built.sparkGeo].forEach((g) => g.dispose());
      [built.staticMat, built.birdMat, built.pageMat, built.glowMat, built.sparkMat].forEach((m) => m.dispose());
    };
  }, [rt, built]);

  const refs = {
    stat: useRef(),
    page: useRef(),
    bookGroup: useRef(),
    bird: useRef(),
    glow: useRef(),
    sparks: useRef(),
  };

  // Everything the behaviour needs between frames.
  const S = useMemo(
    () => ({
      t: 0,
      hv: { lantern: 0, book: 0, bird: 0 },
      lantern: { glow: 0, litUntil: 0, pulse: 0, burstAt: -99, burstKind: 'day', wasBurst: false },
      book: { flipAt: -99 },
      bird: {
        mode: 'perch', // perch | fly
        flyAt: 0,
        curve: null,
        awakeUntil: 0,
        hopAt: -99,
        nextHop: 2.5,
        tiltAt: -99,
        nextTilt: 1.5,
        tiltDir: 1,
        sleep: 0,
        pos: new THREE.Vector3(),
        heading: -Math.PI / 2,
        flapBeats: 0,
      },
      off: [new THREE.Vector3(), new THREE.Vector3()],
      tint: new THREE.Color(),
      lanternWorld: new THREE.Vector3(),
      bookWorld: new THREE.Vector3(),
      perch: new THREE.Vector3(),
      dprCut: false,
    }),
    [],
  );

  // Taps come from the DOM buttons.
  useEffect(() => {
    const onTap = (e) => {
      const name = e.detail && e.detail.name;
      const t = S.t;
      const calm = rt.reduced;
      if (name === 'lantern') {
        const evening = rt.timeName === 'maghrib' || rt.timeName === 'night';
        if (evening) S.lantern.pulse = 1;
        else S.lantern.litUntil = t + 8;
        if (!calm) {
          S.lantern.burstAt = t;
          S.lantern.burstKind = evening ? 'gather' : 'spiral';
        }
      } else if (name === 'book') {
        if (!calm) S.book.flipAt = t;
      } else if (name === 'bird') {
        const asleep = rt.timeName === 'night' && t > S.bird.awakeUntil;
        if (asleep) {
          S.bird.awakeUntil = t + 3.6;
        } else if (!calm && S.bird.mode === 'perch') {
          S.bird.mode = 'fly';
          S.bird.flyAt = t;
          const hy = (rt.walk.modelHeight || 0.9) * 0.95;
          const H = new THREE.Vector3(rt.feet.x, hy, rt.feet.z);
          S.bird.curve = catmull([
            S.perch.clone(),
            H.clone().add(new THREE.Vector3(0.6, 0.1, 0.1)),
            H.clone().add(new THREE.Vector3(0.25, 0.3, 0.6)),
            H.clone().add(new THREE.Vector3(-0.45, 0.2, 0.4)),
            H.clone().add(new THREE.Vector3(-0.55, 0.05, -0.25)),
            H.clone().add(new THREE.Vector3(0.1, 0.25, -0.5)),
            H.clone().add(new THREE.Vector3(0.65, 0.08, -0.1)),
            S.perch.clone(),
          ]);
        } else {
          S.bird.tiltAt = t;
          S.bird.tiltDir = Math.random() < 0.5 ? -1 : 1;
        }
        S.bird.awakeUntil = Math.max(S.bird.awakeUntil, t + 3.6);
      }
    };
    rt.bus.addEventListener('prop-tap', onTap);
    return () => rt.bus.removeEventListener('prop-tap', onTap);
  }, [rt, S]);

  useFrame((_, dt) => {
    const d = Math.min(dt, 0.1);
    S.t += d;
    const t = S.t;
    const p = rt.palette;
    const aspect = size.width / size.height;
    const nar = clamp((0.95 - aspect) / 0.45, 0, 1);
    const fov = camera.fov;

    // hover blends (the DOM buttons set rt.props[name].hover)
    const hk = 1 - Math.exp(-d * 12);
    ['lantern', 'book', 'bird'].forEach((k) => {
      S.hv[k] += ((rt.props[k].hover ? 1 : 0) - S.hv[k]) * hk;
    });

    // layout
    const wl = LAYOUT.wide.lantern;
    const nl = LAYOUT.narrow.lantern;
    const wb = LAYOUT.wide.book;
    const nb = LAYOUT.narrow.book;
    S.off[0].set(
      rt.feet.x + wl[0] + (nl[0] - wl[0]) * nar,
      rt.feet.y,
      rt.feet.z + wl[2] + (nl[2] - wl[2]) * nar,
    );
    S.off[1].set(
      rt.feet.x + wb[0] + (nb[0] - wb[0]) * nar,
      rt.feet.y,
      rt.feet.z + wb[2] + (nb[2] - wb[2]) * nar,
    );
    const { uniforms } = built;
    uniforms.uOff.value[0].copy(S.off[0]);
    uniforms.uOff.value[1].copy(S.off[1]);
    uniforms.uScale.value[0] = 1 + 0.06 * S.hv.lantern;
    uniforms.uScale.value[1] = 1 + 0.06 * S.hv.book;

    // light from the time of day
    S.tint.copy(p.ambient).multiplyScalar(clamp(p.ambientI / 0.55, 0.6, 1.2));
    S.tint.r = Math.min(S.tint.r + 0.1, 1);
    S.tint.g = Math.min(S.tint.g + 0.1, 1);
    S.tint.b = Math.min(S.tint.b + 0.1, 1);
    built.staticMat.color.copy(S.tint);
    built.birdMat.color.copy(S.tint);
    built.pageMat.color.set('#fbf4e2').multiply(S.tint);

    // ---- lantern ----
    const Ls = S.lantern;
    const evening = rt.timeName === 'maghrib' || rt.timeName === 'night';
    const base = rt.timeName === 'night' ? 1 : rt.timeName === 'maghrib' ? 0.7 : 0;
    let target = base;
    if (t < Ls.litUntil) target = Math.max(target, 1.15);
    const up = rt.reduced ? 5 : 3.3;
    const down = rt.reduced ? 5 : 0.85;
    Ls.glow += clamp(target - Ls.glow, -down * d, up * d);
    Ls.pulse = Math.max(0, Ls.pulse - d / 1.2);
    const flicker = rt.reduced ? 1 : 1 + 0.05 * Math.sin(t * 9) + 0.03 * Math.sin(t * 13.7);
    const glow = (Ls.glow + 0.7 * Ls.pulse + 0.25 * S.hv.lantern) * flicker;
    rt.props.lantern.lit = Ls.glow > 0.5 || t < Ls.litUntil || evening;
    built.glowMat.uniforms.uGlow.value = glow;
    S.lanternWorld.set(S.off[0].x + LANTERN_AT[0], S.off[0].y + LANTERN_AT[1], S.off[0].z + LANTERN_AT[2]);
    if (refs.glow.current) {
      refs.glow.current.visible = glow > 0.01;
      refs.glow.current.position.copy(S.lanternWorld);
    }

    // sparks around the lantern
    const sp = refs.sparks.current;
    if (sp) {
      const age = t - Ls.burstAt;
      const dur = 2.5;
      if (age >= 0 && age < dur && !rt.reduced) {
        const prog = age / dur;
        const arr = built.sparkGeo.attributes.position.array;
        const spiral = Ls.burstKind === 'spiral';
        const n = spiral ? 8 : built.SPARKS;
        for (let i = 0; i < built.SPARKS; i += 1) {
          const a = t * (spiral ? 2.6 : 1.8) + (i / n) * Math.PI * 2 * 1.7;
          const r = spiral ? 0.1 + prog * 0.65 * (0.7 + 0.3 * ((i * 7) % 3) / 2) : 0.28 + 0.12 * Math.sin(t * 2 + i) + 0.12 * (1 - prog);
          const y = spiral ? prog * 0.7 + Math.sin(a * 1.3) * 0.06 : Math.sin(a * 0.8 + i) * 0.18;
          arr[i * 3] = S.lanternWorld.x + Math.cos(a) * r;
          arr[i * 3 + 1] = S.lanternWorld.y + y;
          arr[i * 3 + 2] = S.lanternWorld.z + Math.sin(a) * r * 0.7;
          if (i >= n) arr[i * 3 + 1] = -50;
        }
        built.sparkGeo.attributes.position.needsUpdate = true;
        built.sparkMat.uniforms.uAlpha.value = Math.sin(Math.PI * prog) ** 0.6 * 1.6;
        sp.visible = true;
      } else {
        sp.visible = false;
      }
    }

    // ---- book ----
    const Bk = S.book;
    S.bookWorld.set(S.off[1].x, S.off[1].y + BOOK_PIVOT, S.off[1].z);
    if (refs.bookGroup.current) {
      refs.bookGroup.current.position.copy(S.bookWorld);
      refs.bookGroup.current.rotation.x = BOOK_TILT;
      refs.bookGroup.current.scale.setScalar(1 + 0.06 * S.hv.book);
    }
    if (refs.page.current) {
      // three flips, 160 ms each, 90 ms apart. Between flips (and at rest) the page lies on the right block.
      let phi = -0.07;
      const age = t - Bk.flipAt;
      if (age >= 0 && age < 0.9) {
        for (let i = 0; i < 3; i += 1) {
          const u = (age - i * 0.25) / 0.16;
          if (u > 0 && u < 1) phi = -0.07 + smooth(u) * (Math.PI + 0.14);
        }
      }
      refs.page.current.rotation.z = phi;
      refs.page.current.position.set(0, 0.066, 0);
    }

    // ---- bird ----
    const Bd = S.bird;
    S.perch.set(S.off[0].x, S.off[0].y + POST_TOP + 0.05 + 0.04, S.off[0].z);
    const asleep = rt.timeName === 'night' && t > Bd.awakeUntil;
    rt.props.bird.asleep = asleep && Bd.mode === 'perch';
    rt.props.bird.flying = Bd.mode === 'fly';
    Bd.sleep += ((asleep && Bd.mode === 'perch' ? 1 : 0) - Bd.sleep) * (1 - Math.exp(-d * (asleep ? 3 : 8)));
    const bm = refs.bird.current;
    let flapAmt = 0;
    let fold = 1;
    let hop = 0;
    let roll = 0;
    let pitch = 0;
    let yawOff = 0;
    if (Bd.mode === 'fly' && Bd.curve) {
      const age = t - Bd.flyAt;
      const dur = 2.9;
      const u = clamp(age / dur, 0, 1);
      const e = smooth(u);
      Bd.curve.getPoint(e, Bd.pos);
      Bd.curve.getTangent(e, V);
      const targetHeading = Math.atan2(V.x, V.z);
      let dh = targetHeading - Bd.heading;
      dh = Math.atan2(Math.sin(dh), Math.cos(dh));
      Bd.heading += dh * (1 - Math.exp(-d * 10));
      roll = clamp(-dh * 1.2, -0.6, 0.6);
      pitch = clamp(-V.y * 0.8, -0.5, 0.5);
      flapAmt = Math.sin(t * 46) * (age < 0.45 ? 1 : 0.7);
      fold = 0;
      if (u >= 1) {
        Bd.mode = 'perch';
        Bd.heading = -Math.PI / 2;
      }
    } else {
      Bd.pos.copy(S.perch);
      Bd.heading += (-Math.PI / 2 - Bd.heading) * (1 - Math.exp(-d * 8));
      const awake = 1 - Bd.sleep;
      const slow = rt.timeName === 'maghrib' ? 1.8 : 1;
      if (!rt.reduced && awake > 0.5) {
        if (t > Bd.nextHop) {
          Bd.hopAt = t;
          Bd.nextHop = t + rand(2.6, 5.5) * slow;
        }
        const ha = (t - Bd.hopAt) / 0.28;
        if (ha >= 0 && ha < 1) hop = Math.sin(ha * Math.PI) * 0.045;
      }
      if (awake > 0.5 && t > Bd.nextTilt) {
        Bd.tiltAt = t;
        Bd.tiltDir = Math.random() < 0.5 ? -1 : 1;
        Bd.nextTilt = t + rand(2, 4) * slow;
      }
      const ta = t - Bd.tiltAt;
      if (ta >= 0 && ta < 1.1) {
        const env = ta < 0.2 ? ta / 0.2 : ta > 0.8 ? 1 - (ta - 0.8) / 0.3 : 1;
        yawOff = Bd.tiltDir * 0.55 * env;
        roll = Bd.tiltDir * 0.25 * env;
      }
      // waking after a tap: a few quick wing shivers
      if (!rt.reduced && t < Bd.awakeUntil && rt.timeName === 'night' && Bd.awakeUntil - t > 3.0) flapAmt = Math.sin(t * 40) * 0.5;
      pitch = Bd.sleep * 0.3;
    }
    built.flap.value = flapAmt;
    built.fold.value = fold;
    if (bm) {
      bm.position.copy(Bd.pos);
      bm.position.y += hop - Bd.sleep * 0.012;
      bm.rotation.set(pitch, Bd.heading + yawOff, roll, 'YXZ');
      const s = 1.5 * (1 + 0.06 * S.hv.bird);
      bm.scale.set(s, s * (1 - 0.22 * Bd.sleep), s * (1 - 0.1 * Bd.sleep));
    }

    // ---- screen boxes for the DOM buttons ----
    V.copy(S.lanternWorld);
    projectBox(rt.propBox.lantern, V, 0.3, 0.3, camera, size, fov);
    V.set(S.bookWorld.x, S.bookWorld.y + 0.1, S.bookWorld.z);
    projectBox(rt.propBox.book, V, 0.3, 0.3, camera, size, fov);
    V.copy(Bd.pos);
    projectBox(rt.propBox.bird, V, 0.2, 0.2, camera, size, fov);

    // ---- where Sadiq looks ----
    const f = rt.gazeFocus;
    const g = rt.gaze;
    if (f && performance.now() < f.untilMs && rt.screen.visible) {
      let tx = f.x;
      let ty = f.y;
      if (f.name) {
        const b = rt.propBox[f.name];
        tx = b.x;
        ty = b.y;
      }
      const sc = rt.screen;
      g.x = clamp((tx - sc.headX) / Math.max(sc.heightPx * 1.2, 40), -1, 1);
      g.y = clamp((sc.headY - ty) / Math.max(sc.heightPx * 0.9, 40), -1, 1);
      g.weight = 1;
    } else {
      g.weight = 0;
      if (f && performance.now() >= f.untilMs) rt.gazeFocus = null;
    }

    // ---- adaptive quality: the third step caps the pixel ratio (never goes back up) ----
    if (rt.degrade >= 3 && !S.dprCut) {
      S.dprCut = true;
      setDpr(Math.min(gl.getPixelRatio(), 1.25));
    }
  });

  return (
    <>
      <mesh ref={refs.stat} geometry={built.staticGeo} material={built.staticMat} frustumCulled={false} renderOrder={3} />
      <group ref={refs.bookGroup}>
        <mesh ref={refs.page} geometry={built.pageGeo} material={built.pageMat} frustumCulled={false} renderOrder={4} />
      </group>
      <mesh ref={refs.bird} geometry={built.birdGeo} material={built.birdMat} frustumCulled={false} renderOrder={4} />
      <mesh ref={refs.glow} geometry={built.glowGeo} material={built.glowMat} frustumCulled={false} renderOrder={6} visible={false} />
      <points ref={refs.sparks} geometry={built.sparkGeo} material={built.sparkMat} frustumCulled={false} renderOrder={7} visible={false} />
    </>
  );
}
