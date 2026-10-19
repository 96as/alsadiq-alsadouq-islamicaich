/* The frame loop mutates uniforms by design. */
/* eslint-disable react-hooks/immutability */
import { useEffect, useMemo } from 'react';
import { assetUrl } from '../../../../utils/assetUrl';
import { useFrame } from '@react-three/fiber';
import { useTexture } from '@react-three/drei';
import * as THREE from 'three';
import { useForest } from './forestContext';
import { BACKDROP_EXT, createBackdropMaterial, createPointsMaterial } from './materials';
import { mulberry32 } from './geometry';

export const BACKDROP_URL = assetUrl('/backgrounds/fantasy-meadow-1600.webp');

const R = 70; // radius of the painted curtain
const ARC = (100 * Math.PI) / 180; // 100 degrees of horizon
const IMG_ASPECT = 16 / 9;
const HEIGHT = (R * ARC) / IMG_ASPECT;
const HORIZON_ROW = 0.47; // fraction from the top of the painting where the horizon sits
const CENTER_COL = 0.535; // painting column that sits straight ahead (where the path vanishes)
const HORIZON_Y = 0.9; // world height of the painted horizon

/**
 * The painted meadow image as a distant curved curtain, so mountains, sky and
 * the far tree line match the reference pictures exactly. The camera is kept
 * close to the centre (see CameraRig), so the curtain never shows its edge.
 */
export function Backdrop() {
  const rt = useForest();
  const tex = useTexture(BACKDROP_URL, (t) => {
    t.colorSpace = THREE.SRGBColorSpace;
    t.anisotropy = 4;
  });
  const geometry = useMemo(() => {
    // The curtain is wider than the painting (BACKDROP_EXT x) and the shader mirrors the painting past its edges,
    // so a very wide window never shows the bare edge of the curtain.
    const thetaStart = Math.PI - (1 - CENTER_COL) * ARC - (ARC * (BACKDROP_EXT - 1)) / 2;
    const g = new THREE.CylinderGeometry(R, R, HEIGHT, 72, 1, true, thetaStart, ARC * BACKDROP_EXT);
    g.translate(0, HORIZON_Y - (HORIZON_ROW - 0.5) * -HEIGHT - HEIGHT * 0, 0);
    return g;
  }, []);
  const material = useMemo(() => createBackdropMaterial(tex, rt.shared), [tex, rt]);

  useEffect(() => () => {
    geometry.dispose();
    material.dispose();
  }, [geometry, material]);

  useFrame(() => {
    const p = rt.palette;
    const u = material.uniforms;
    u.uTint.value.copy(p.bdTint);
    u.uGlow.value.copy(p.bdGlow);
    u.uGlowAmt.value = p.bdGlowAmt;
    u.uCloud.value.copy(p.cloud);
    u.uDrift.value = rt.reduced ? 0.15 : 1;
    u.uWarp.value = rt.reduced ? 0.25 : 1;
  });

  return <mesh geometry={geometry} material={material} renderOrder={-10} frustumCulled={false} />;
}

/** Twinkling stars, only visible at night. */
export function Stars({ count }) {
  const rt = useForest();
  const { geometry, material } = useMemo(() => {
    const rng = mulberry32(42);
    const pos = new Float32Array(count * 3);
    const seed = new Float32Array(count * 4);
    for (let i = 0; i < count; i += 1) {
      const az = (rng() - 0.5) * 2 * ((62 * Math.PI) / 180);
      const el = ((2 + 38 * rng() ** 1.5) * Math.PI) / 180;
      const r = 66;
      pos[i * 3] = Math.sin(az) * Math.cos(el) * r;
      pos[i * 3 + 1] = HORIZON_Y + Math.sin(el) * r;
      pos[i * 3 + 2] = -Math.cos(az) * Math.cos(el) * r;
      seed.set([rng(), rng(), rng(), rng()], i * 4);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    g.setAttribute('aSeed', new THREE.BufferAttribute(seed, 4));
    const m = createPointsMaterial(rt.shared, {
      size: 1.7,
      color: '#e6ecff',
      isStatic: true,
      blink: 1.3,
      star: true,
    });
    return { geometry: g, material: m };
  }, [count, rt]);

  useEffect(() => () => {
    geometry.dispose();
    material.dispose();
  }, [geometry, material]);

  useFrame(() => {
    material.uniforms.uAlpha.value = rt.palette.night * 0.95;
  });

  return <points geometry={geometry} material={material} frustumCulled={false} />;
}

const MOON_FRAG = /* glsl */ `
  uniform float uAlpha;
  varying vec2 vUv;
  void main() {
    vec2 p = vUv - 0.5;
    float r = length(p) * 2.0;
    float disc = smoothstep(0.22, 0.2, r);
    float glow = exp(-r * r * 9.0) * 0.55;
    float crater = 0.08 * smoothstep(0.07, 0.0, length(p - vec2(-0.05, 0.04))) + 0.06 * smoothstep(0.05, 0.0, length(p - vec2(0.05, -0.06)));
    vec3 col = mix(vec3(0.62, 0.7, 1.0), vec3(1.0, 0.97, 0.86), disc);
    col -= crater * disc;
    float a = max(disc, glow) * uAlpha;
    gl_FragColor = vec4(col, a);
    #include <colorspace_fragment>
  }
`;

/** A soft moon with a glow, only visible at night. */
export function Moon() {
  const rt = useForest();
  const material = useMemo(
    () =>
      new THREE.ShaderMaterial({
        transparent: true,
        depthWrite: false,
        fog: false,
        uniforms: { uAlpha: { value: 0 } },
        vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
        fragmentShader: MOON_FRAG,
      }),
    [],
  );
  useEffect(() => () => material.dispose(), [material]);
  useFrame(() => {
    material.uniforms.uAlpha.value = THREE.MathUtils.smoothstep(rt.palette.night, 0.35, 1);
  });
  const pos = [7, HORIZON_Y + 14, -63];
  return (
    <mesh position={pos} material={material} renderOrder={-5} frustumCulled={false}>
      <planeGeometry args={[16, 16]} />
    </mesh>
  );
}
