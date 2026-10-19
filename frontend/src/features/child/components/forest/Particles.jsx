/* The frame loop updates shader uniforms by design. */
/* eslint-disable react-hooks/immutability */
import { useEffect, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { useForest } from './forestContext';
import { createPointsMaterial } from './materials';
import { mulberry32 } from './geometry';

function makePoints(rt, count, seed, box, matOpts) {
  const rng = mulberry32(seed);
  const pos = new Float32Array(count * 3);
  const sd = new Float32Array(count * 4);
  for (let i = 0; i < count; i += 1) {
    pos[i * 3] = box.min[0] + rng() * box.size[0];
    pos[i * 3 + 1] = box.min[1] + rng() * box.size[1];
    pos[i * 3 + 2] = box.min[2] + rng() * box.size[2];
    sd.set([rng(), rng(), rng(), rng()], i * 4);
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  geometry.setAttribute('aSeed', new THREE.BufferAttribute(sd, 4));
  const material = createPointsMaterial(rt.shared, { boxMin: box.min, boxSize: box.size, ...matOpts });
  return { geometry, material };
}

/**
 * Floating pollen (day), sparkles near the avatar, and fireflies (night).
 * All are GPU points: one draw call each, motion done in the vertex shader.
 */
export default function Particles({ counts }) {
  const rt = useForest();

  const layers = useMemo(() => {
    const pollen = makePoints(rt, counts.pollen, 11, { min: [-7, 0.2, -16], size: [14, 4.5, 22] }, {
      size: 0.8, color: '#fff3c0', drift: [0.18, 0.06, 0.08], wander: 0.5, blink: 1.1, windPush: 1,
    });
    const sparkles = makePoints(rt, counts.sparkles, 12, { min: [-2.4, 0.3, -3.5], size: [4.8, 2.4, 6.5] }, {
      size: 1.1, color: '#fffbe0', drift: [0.02, 0.05, 0], wander: 0.35, blink: 2.4, star: true, windPush: 0.35,
    });
    const fireflies = makePoints(rt, counts.fireflies, 13, { min: [-6, 0.4, -14], size: [12, 2.8, 17] }, {
      size: 1.5, color: '#d4ff6a', drift: [0.02, 0.01, 0], wander: 0.9, move: 0.6, blink: 1.3,
    });
    return { pollen, sparkles, fireflies };
  }, [counts, rt]);

  useEffect(
    () => () => {
      Object.values(layers).forEach((l) => {
        l.geometry.dispose();
        l.material.dispose();
      });
    },
    [layers],
  );

  useFrame(() => {
    const n = rt.palette.night;
    const calm = rt.reduced ? 0.4 : 1;
    const thin = rt.degrade >= 2 ? 0 : 1; // second step of the quality ladder: no pollen or sparkles
    layers.pollen.material.uniforms.uAlpha.value = (1 - n) * 0.85 * calm * thin;
    layers.sparkles.material.uniforms.uAlpha.value = ((0.55 + rt.palette.dew) * calm + n * 0.25) * thin;
    layers.fireflies.material.uniforms.uAlpha.value = n * 1.54 * calm * (rt.degrade >= 1 ? 0.6 : 1);
    layers.pollen.material.uniforms.uMove.value = rt.reduced ? 0.25 : 1;
    layers.sparkles.material.uniforms.uMove.value = rt.reduced ? 0.25 : 1;
    layers.fireflies.material.uniforms.uMove.value = rt.reduced ? 0.15 : 0.6;
  });

  return (
    <>
      <points geometry={layers.pollen.geometry} material={layers.pollen.material} frustumCulled={false} renderOrder={5} />
      <points geometry={layers.sparkles.geometry} material={layers.sparkles.material} frustumCulled={false} renderOrder={5} />
      <points geometry={layers.fireflies.geometry} material={layers.fireflies.material} frustumCulled={false} renderOrder={5} />
    </>
  );
}
