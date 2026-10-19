/* eslint-disable react-hooks/immutability -- the frame loop mutates three.js objects and the stats object by design (as in forest/) */
import { useEffect, useLayoutEffect, useMemo, useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import {
  CanvasTexture,
  Color,
  DirectionalLight,
  Mesh,
  MeshBasicMaterial,
  PCFShadowMap,
  PlaneGeometry,
  PMREMGenerator,
  SRGBColorSpace,
  ShadowMaterial,
  TextureLoader,
  Vector3,
  EquirectangularReflectionMapping,
  MathUtils,
} from 'three';
import { LOOKDEV } from './lookdevConfig.js';
import { assetUrl } from '../../../../../utils/assetUrl.js';
import { solveFraming } from './stageFraming.js';
import { lookdevAvatarX, lookdevStats } from './lookdevRuntime.js';
import { refreshSceneMaterials, upgradeSceneMaterials } from './materialUpgrade.js';
import { selectGradeToneMapping } from './gradeToneMapping.js';

const { smoothstep } = MathUtils;

/** A radial alpha gradient drawn once (no asset file): white, alpha from the stops in the config. */
function makeBlobTexture() {
  const n = LOOKDEV.ao.texSize;
  const cv = document.createElement('canvas');
  cv.width = n;
  cv.height = n;
  const g = cv.getContext('2d');
  const gr = g.createRadialGradient(n / 2, n / 2, 0, n / 2, n / 2, n / 2);
  for (const [stop, alpha] of LOOKDEV.ao.stops) gr.addColorStop(stop, `rgba(255,255,255,${alpha})`);
  g.fillStyle = gr;
  g.fillRect(0, 0, n, n);
  const tex = new CanvasTexture(cv);
  tex.colorSpace = SRGBColorSpace;
  return tex;
}

/** The deepest first-child descendant: the foot end of a leg chain. */
function chainEnd(bone) {
  let b = bone;
  while (b.children.length && b.children[0].isBone) b = b.children[0];
  return b;
}

/** The hips and the two feet of whatever skeleton is in the scene (this rig's names, then the R2 rig's). */
function findRig(root) {
  const byName = new Map();
  root.traverse((o) => {
    if (o.name) byName.set(o.name.toLowerCase().replaceAll('.', '').replaceAll('_', ''), o);
  });
  const get = (...names) => {
    for (const n of names) {
      const o = byName.get(n);
      if (o) return o;
    }
    return null;
  };
  const hips = get('hips', 'pelvis', 'root');
  let footL = get('footl', 'toel', 'ballL');
  let footR = get('footr', 'toer', 'ballR');
  if (!footL) footL = get('legl') ? chainEnd(get('legl')) : null;
  if (!footR) footR = get('legr') ? chainEnd(get('legr')) : null;
  return { hips, footL, footR };
}

function StageCamera() {
  const { camera, size } = useThree();
  useLayoutEffect(() => {
    const fr = solveFraming(size.width, size.height);
    camera.fov = fr.fov;
    camera.aspect = size.width / size.height;
    camera.near = 0.1;
    camera.far = 50;
    camera.position.set(0, fr.eye, fr.dist);
    camera.rotation.set(0, 0, 0); // level: verticals stay vertical, like the painting
    // The lens shift puts the 3D horizon (the principal row of a level camera) on the painted one.
    camera.setViewOffset(size.width, size.height, 0, fr.viewOffsetY, size.width, size.height);
    camera.updateProjectionMatrix();
    return () => camera.clearViewOffset();
  }, [camera, size.width, size.height]);
  return null;
}

/**
 * avatar-integ: the meadow stage's camera (meadowStage.js). Same level lens and horizon shift as StageCamera; only the
 * distance and the sideways shift move, once, when the talk starts. Runs after the stage tick (priority -2).
 */
function StagedCamera({ stage }) {
  const { camera, size } = useThree();
  useFrame(() => {
    if (!stage.W) return;
    const p = stage.pose;
    camera.fov = p.fov;
    camera.aspect = size.width / size.height;
    camera.near = 0.1;
    camera.far = 50;
    camera.position.set(p.cx, p.eye, p.dist);
    camera.rotation.set(0, 0, 0);
    camera.setViewOffset(size.width, size.height, 0, p.viewOffsetY, size.width, size.height);
    camera.updateProjectionMatrix();
  }, -1);
  useEffect(() => () => camera.clearViewOffset(), [camera]);
  return null;
}

function MeadowEnvironment() {
  const { gl, scene } = useThree();
  useEffect(() => {
    let cancelled = false;
    let target = null;
    new TextureLoader().load(
      assetUrl(LOOKDEV.env.url), // honours the showcase base (/page/)
      (src) => {
        if (cancelled) {
          src.dispose();
          return;
        }
        src.mapping = EquirectangularReflectionMapping;
        src.colorSpace = SRGBColorSpace;
        const pmrem = new PMREMGenerator(gl);
        target = pmrem.fromEquirectangular(src);
        scene.environment = target.texture;
        scene.environmentIntensity = LOOKDEV.env.intensity;
        src.dispose(); // the source and the generator are only needed once
        pmrem.dispose();
      },
      undefined,
      () => console.warn('[lookdev] the meadow environment map did not load; the lights alone will do.'),
    );
    return () => {
      cancelled = true;
      scene.environment = null;
      if (target) target.dispose();
    };
  }, [gl, scene]);
  return null;
}

/**
 * The look-dev rig for the avatar canvas (LOOKDEV-SPEC S3 to S8): the stage camera, the meadow light, the colour
 * grade, the upgraded avatar materials and the grounding (contact blobs on every tier, a cast shadow on the high one).
 */
export default function AvatarLookdev({ framing, tier, onSlow, adaptive = true, stage = null }) {
  const { gl, scene, size, camera } = useThree();
  const high = tier === 'high';
  const avatarX = lookdevAvatarX(framing, size);
  const cfg = LOOKDEV;

  // ---- the grade and the shadow map are renderer state: set them before the avatar first compiles ----
  useLayoutEffect(() => {
    const restoreTone = selectGradeToneMapping(gl, () => refreshSceneMaterials(scene));
    const prevShadow = { enabled: gl.shadowMap.enabled, type: gl.shadowMap.type };
    gl.shadowMap.enabled = high;
    gl.shadowMap.type = PCFShadowMap; // PCFSoft is deprecated in r184
    return () => {
      restoreTone();
      gl.shadowMap.enabled = prevShadow.enabled;
      gl.shadowMap.type = prevShadow.type;
    };
  }, [gl, scene, high]);

  // measurement hook for the gate scripts (window.__lookdev.scene / gl / camera)
  useLayoutEffect(() => {
    lookdevStats.scene = scene;
    lookdevStats.gl = gl;
    lookdevStats.camera = camera;
  }, [scene, gl, camera]);

  // ---- the lights ----
  const rig = useMemo(() => {
    const dist = cfg.lightDistance;
    const key = new DirectionalLight(cfg.key.color, cfg.key.intensity);
    const rim = new DirectionalLight(cfg.rim.color, cfg.rim.intensity);
    const sun = new DirectionalLight(cfg.shadowSun.color, cfg.shadowSun.intensity);
    sun.castShadow = true;
    const s = cfg.shadowSun;
    sun.shadow.mapSize.set(s.mapSize, s.mapSize);
    Object.assign(sun.shadow.camera, { left: -s.bounds, right: s.bounds, top: s.bounds, bottom: -s.bounds, near: s.near, far: s.far });
    sun.shadow.camera.updateProjectionMatrix();
    sun.shadow.bias = s.bias;
    sun.shadow.normalBias = s.normalBias;
    return { dist, key, rim, sun };
  }, [cfg]);
  useLayoutEffect(() => {
    const { dist, key, rim, sun } = rig;
    key.position.set(...cfg.key.dir).multiplyScalar(dist).add(new Vector3(avatarX, 0, 0));
    key.target.position.set(avatarX, cfg.keyTargetY, 0);
    rim.position.set(...cfg.rim.pos).add(new Vector3(avatarX, 0, 0));
    rim.target.position.set(avatarX, cfg.rim.targetY, 0);
    sun.position.set(...cfg.shadowSun.dir).multiplyScalar(dist).add(new Vector3(avatarX, 0, 0));
    sun.target.position.set(avatarX, 0, 0);
    for (const l of [key, rim, sun]) {
      l.target.updateMatrixWorld();
      l.updateMatrixWorld();
    }
  }, [rig, cfg, avatarX]);

  // ---- grounding: blobs on every tier, the faded shadow catcher on the high tier ----
  const ground = useMemo(() => {
    const tex = makeBlobTexture();
    const blobMat = (color, opacity) =>
      new MeshBasicMaterial({ map: tex, color, transparent: true, opacity, depthWrite: false, toneMapped: false, polygonOffset: true, polygonOffsetFactor: -1 });
    const plane = new PlaneGeometry(1, 1);
    const mk = (mat, w, d, y) => {
      const m = new Mesh(plane, mat);
      m.rotation.x = -Math.PI / 2;
      m.position.y = y;
      m.scale.set(w, d, 1);
      m.renderOrder = 2;
      m.frustumCulled = false;
      m.userData.lookdevMaterial = true; // the avatar material pass must leave these alone
      return m;
    };
    const ao = mk(blobMat(cfg.ao.color, cfg.ao.opacity), cfg.ao.size[0], cfg.ao.size[1], cfg.ao.y);
    const feet = [0, 1].map(() => mk(blobMat(cfg.ao.color, cfg.foot.opacity), cfg.foot.size[0], cfg.foot.size[1], cfg.ao.y + 0.001));

    let catcher = null;
    let feetUniform = null;
    if (high) {
      const mat = new ShadowMaterial({ color: new Color(cfg.catcher.color), opacity: cfg.catcher.opacity, toneMapped: false, transparent: true, depthWrite: false });
      feetUniform = { value: new Vector3(0, 0, 0) };
      mat.onBeforeCompile = (shader) => {
        shader.uniforms.uFeetXZ = feetUniform;
        shader.vertexShader = shader.vertexShader
          .replace('#include <common>', '#include <common>\nvarying vec2 vLookXZ;')
          .replace('#include <begin_vertex>', '#include <begin_vertex>\nvLookXZ = ( modelMatrix * vec4( position, 1.0 ) ).xz;');
        shader.fragmentShader = shader.fragmentShader
          .replace('#include <common>', '#include <common>\nvarying vec2 vLookXZ;\nuniform vec3 uFeetXZ;')
          .replace(
            '#include <tonemapping_fragment>',
            `gl_FragColor.a *= 1.0 - smoothstep( ${cfg.catcher.fade[0].toFixed(2)}, ${cfg.catcher.fade[1].toFixed(2)}, distance( vLookXZ, uFeetXZ.xz ) );\n#include <tonemapping_fragment>`,
          );
      };
      mat.customProgramCacheKey = () => 'lookdev-catcher';
      catcher = new Mesh(new PlaneGeometry(cfg.catcher.size, cfg.catcher.size), mat);
      catcher.rotation.x = -Math.PI / 2;
      catcher.receiveShadow = true;
      catcher.renderOrder = 1;
      catcher.frustumCulled = false;
      catcher.userData.lookdevMaterial = true;
    }
    return { tex, plane, ao, feet, catcher, feetUniform };
  }, [cfg, high]);
  useEffect(
    () => () => {
      ground.tex.dispose();
      ground.plane.dispose();
      for (const m of [ground.ao, ...ground.feet]) m.material.dispose();
      if (ground.catcher) {
        ground.catcher.geometry.dispose();
        ground.catcher.material.dispose();
      }
    },
    [ground],
  );
  useLayoutEffect(() => {
    if (ground.catcher) ground.catcher.position.set(avatarX, 0, 0);
  }, [ground, avatarX]);

  // avatar-integ: on the meadow stage the lights, the sun's shadow box and the catcher travel with him along the path
  useFrame(() => {
    if (!stage || !stage.W) return;
    const { dist, key, rim, sun } = rig;
    const x = stage.px;
    const z = stage.pz;
    key.position.set(cfg.key.dir[0] * dist + x, cfg.key.dir[1] * dist, cfg.key.dir[2] * dist + z);
    key.target.position.set(x, cfg.keyTargetY, z);
    rim.position.set(cfg.rim.pos[0] + x, cfg.rim.pos[1], cfg.rim.pos[2] + z);
    rim.target.position.set(x, cfg.rim.targetY, z);
    sun.position.set(cfg.shadowSun.dir[0] * dist + x, cfg.shadowSun.dir[1] * dist, cfg.shadowSun.dir[2] * dist + z);
    sun.target.position.set(x, 0, z);
    for (const l of [key, rim, sun]) {
      l.target.updateMatrixWorld();
      l.updateMatrixWorld();
    }
    if (ground.catcher) ground.catcher.position.set(x, 0, z);
  }, -1);

  // ---- per frame: find the avatar, upgrade its materials, steer the blobs, watch the frame time ----
  const st = useRef({
    sig: [],
    sigLen: -1,
    hips: null,
    foot: [null, null],
    restY: [Infinity, Infinity],
    acc: 0,
    n: 0,
    windowStart: 0,
    lastScan: -1,
    scratch: new Vector3(),
  }).current;

  useFrame((frame, delta) => {
    const t0 = performance.now();

    // New avatar in the scene (first load, or a model swap)? Upgrade its materials before it first compiles.
    const kids = scene.children;
    let changed = kids.length !== st.sigLen;
    if (!changed) for (let i = 0; i < kids.length; i++) if (kids[i].id !== st.sig[i]) changed = true;
    // A model that mounts its meshes a frame after its group would be missed by the top-level check: rescan twice a
    // second while it settles (first 6 s), then every 2 s.
    const nowS = frame.clock.elapsedTime;
    if (!changed && nowS - st.lastScan > (nowS < 6 ? 0.5 : 2)) changed = true;
    if (changed) {
      st.lastScan = nowS;
      st.sigLen = kids.length;
      for (let i = 0; i < kids.length; i++) st.sig[i] = kids[i].id;
      const count = upgradeSceneMaterials(scene, gl.capabilities.getMaxAnisotropy(), high);
      if (count > 0) {
        const r = findRig(scene);
        st.hips = r.hips;
        st.foot[0] = r.footL;
        st.foot[1] = r.footR;
        st.restY[0] = Infinity;
        st.restY[1] = Infinity;
        lookdevStats.scans += 1;
      }
    }

    // Blobs: the AO follows the hips on the ground, the foot blobs follow the feet.
    const v = st.scratch;
    let hop = 0;
    for (let i = 0; i < 2; i++) {
      const fb = ground.feet[i];
      const bone = st.foot[i];
      if (!bone) {
        fb.visible = false;
        continue;
      }
      const e = bone.matrixWorld.elements; // the renderer updated it last frame: no walk up the parents, no allocation
      v.set(e[12], e[13], e[14]);
      if (v.y < st.restY[i]) st.restY[i] = v.y;
      const h = Math.max(0, v.y - st.restY[i]);
      fb.visible = true;
      fb.position.x = v.x;
      fb.position.z = v.z + 0.03; // the toes are in front of the ankle
      fb.material.opacity = cfg.foot.opacity * (1 - smoothstep(h, 0, cfg.foot.fadeHeight));
      hop = i === 0 ? h : Math.min(hop, h);
    }
    if (st.hips) {
      const e = st.hips.matrixWorld.elements;
      v.set(e[12], e[13], e[14]);
      ground.ao.position.x = v.x;
      ground.ao.position.z = v.z;
      if (ground.feetUniform) ground.feetUniform.value.set(v.x, 0, v.z);
    } else {
      ground.ao.position.x = avatarX;
      ground.ao.position.z = 0;
    }
    const lift = 1 - smoothstep(hop, 0, cfg.ao.hopFade);
    ground.ao.material.opacity = cfg.ao.opacity * lift;
    const grow = 1 + cfg.ao.hopGrow * hop;
    ground.ao.scale.set(cfg.ao.size[0] * grow, cfg.ao.size[1] * grow, 1);

    // Adaptive DPR: a mean frame time over the limit for the window drops the cap one step.
    if (onSlow && adaptive && delta < 0.5) {
      st.acc += delta;
      st.n += 1;
      const now = frame.clock.elapsedTime;
      if (st.windowStart === 0) st.windowStart = now;
      if (now - st.windowStart >= cfg.dpr.slowSeconds) {
        if ((st.acc / st.n) * 1000 > cfg.dpr.slowFrameMs) onSlow();
        st.acc = 0;
        st.n = 0;
        st.windowStart = now;
      }
    }

    const ms = performance.now() - t0;
    lookdevStats.frames += 1;
    lookdevStats.totalMs += ms;
    if (ms > lookdevStats.maxMs) lookdevStats.maxMs = ms;
    lookdevStats.dpr = frame.viewport.dpr;
  });

  return (
    <>
      {framing === 'meadow' && (stage ? <StagedCamera stage={stage} /> : <StageCamera />)}
      <MeadowEnvironment />
      <hemisphereLight args={[cfg.hemi.sky, cfg.hemi.ground, cfg.hemi.intensity]} />
      <primitive object={rig.key} />
      <primitive object={rig.key.target} />
      <primitive object={rig.rim} />
      <primitive object={rig.rim.target} />
      {high && <primitive object={rig.sun} />}
      {high && <primitive object={rig.sun.target} />}
      {ground.catcher && <primitive object={ground.catcher} />}
      <primitive object={ground.ao} />
      <primitive object={ground.feet[0]} />
      <primitive object={ground.feet[1]} />
    </>
  );
}
