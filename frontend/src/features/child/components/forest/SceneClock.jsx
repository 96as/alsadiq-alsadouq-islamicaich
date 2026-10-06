/* The frame loop mutates the runtime object by design (see runtime.js). */
/* eslint-disable react-hooks/immutability */
import { useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { useForest } from './forestContext';
import { makePalette, mixPalette, stepPalette } from './palette';
import { windState } from './wind/windField';
import { packWindUniforms } from './wind/windGlsl';

/**
 * Per-frame housekeeping: wind time, blending toward the current time-of-day
 * palette, and applying it to fog and lights. Everything else reads the
 * blended palette from the runtime.
 */
export default function SceneClock() {
  const rt = useForest();
  const { scene, gl } = useThree();
  const ambient = useRef();
  const hemi = useRef();
  const sun = useRef();

  useFrame((_, dt) => {
    const d = Math.min(dt, 0.1);
    const { palette: p, shared } = rt;
    if (rt.freezeTime != null) shared.uTime.value = rt.freezeTime; // dev: frozen-time pairs for the checks
    else shared.uTime.value += d;
    shared.uSway.value = rt.reduced ? 0.25 : 1;
    shared.uFlutterOn.value = rt.reduced ? 0 : 1;
    // one wind for every material: the CPU state is mirrored into the shader uniforms
    windState(shared.uTime.value, rt.wind);
    packWindUniforms(rt.wind, shared);
    stepFeet(rt, shared);
    shared.uDpr.value = gl.getPixelRatio();

    const k = 1 - Math.exp(-d * (rt.reduced ? 1.4 : 2.2));
    // Soft edges: near a boundary the target is already a mix of two palettes (see timeBlendFromDate).
    let target = rt.targets[rt.timeName];
    if (rt.timeNext && rt.timeW > 0.001 && rt.targets[rt.timeNext]) {
      if (!rt.mixTarget) rt.mixTarget = makePalette(rt.timeName);
      mixPalette(rt.mixTarget, target, rt.targets[rt.timeNext], rt.timeW);
      target = rt.mixTarget;
    }
    stepPalette(p, target, k);

    shared.uGrass.value.copy(p.grass);
    shared.uNight.value = p.night;

    if (scene.fog) {
      scene.fog.color.copy(p.fog);
      scene.fog.near = p.fogNear;
      scene.fog.far = p.fogFar;
    }
    if (scene.background && scene.background.isColor) scene.background.copy(p.fog);

    if (ambient.current) {
      ambient.current.color.copy(p.ambient);
      ambient.current.intensity = p.ambientI;
    }
    if (hemi.current) {
      hemi.current.color.copy(p.hemiSky);
      hemi.current.groundColor.copy(p.hemiGround);
      hemi.current.intensity = p.hemiI;
    }
    if (sun.current) {
      sun.current.color.copy(p.sun);
      sun.current.intensity = p.sunI;
      sun.current.position.set(p.sunPos[0], p.sunPos[1], p.sunPos[2]);
    }
  });

  return (
    <>
      <color attach="background" args={['#c5cd62']} />
      <fog attach="fog" args={['#c5cd62', 18, 70]} />
      <ambientLight ref={ambient} />
      <hemisphereLight ref={hemi} />
      <directionalLight ref={sun} />
    </>
  );
}

const FOOT_EVERY = 0.12; // seconds between prints while the avatar moves
const FOOT_LIFE = 2.4; // seconds a print keeps the grass down
const FOOT_STEP = 0.05; // metres the avatar must have moved to leave a print

/** Record the avatar's footprints and write them to the shared uniforms. No allocation. */
function stepFeet(rt, shared) {
  const tr = rt.trail;
  const now = shared.uTime.value;
  const { x, z } = rt.stand;
  if (now - tr.last >= FOOT_EVERY && (x - tr.lx) ** 2 + (z - tr.lz) ** 2 > FOOT_STEP * FOOT_STEP) {
    tr.last = now;
    tr.lx = x;
    tr.lz = z;
    tr.x[tr.head] = x;
    tr.z[tr.head] = z;
    tr.t[tr.head] = now;
    tr.head = (tr.head + 1) % 8;
  }
  const feet = shared.uFeet.value;
  let best = -1;
  let bestAge = 1e9;
  for (let i = 0; i < 8; i += 1) {
    const age = now - tr.t[i];
    const w = age < FOOT_LIFE ? (1 - age / FOOT_LIFE) ** 1.5 : 0;
    feet[i].set(tr.x[i], tr.z[i], w, 0);
    if (w > 0 && age < bestAge) {
      bestAge = age;
      best = i;
    }
  }
  const dev = rt.devFeet;
  if (dev) {
    for (let i = 0; i < dev.length && i < 8; i += 1) feet[i].set(dev[i][0], dev[i][1], 1, 0);
    shared.uFeetC.value.set(dev[0][0], dev[0][1]);
    return;
  }
  if (best >= 0) shared.uFeetC.value.set(tr.x[best], tr.z[best]);
  else shared.uFeetC.value.set(1e4, 1e4);
}
