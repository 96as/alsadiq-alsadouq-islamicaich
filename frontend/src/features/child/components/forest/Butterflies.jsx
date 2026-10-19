import { useEffect, useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { useForest } from './forestContext';

// Rim of one wing in the horizontal plane: a round forewing (+z, the flight
// direction) and a smaller hindwing, so the flap around the body axis reads
// as a butterfly from the side instead of a spinning kite.
const WING_RIM = [
  [0.04, 0.06], [0.16, 0.17], [0.29, 0.17], [0.33, 0.06], [0.22, -0.01],
  [0.24, -0.11], [0.14, -0.19], [0.04, -0.12],
];

/** One wing, hinged on the body axis (local z), lighter toward the edge. */
function wingGeometry(side) {
  const pos = [];
  const col = [];
  for (let i = 0; i < WING_RIM.length - 1; i += 1) {
    const [x0, z0] = WING_RIM[i];
    const [x1, z1] = WING_RIM[i + 1];
    pos.push(0, 0, 0, side * x0, 0, z0, side * x1, 0, z1);
    col.push(0.7, 0.7, 0.7, 1, 1, 1, 1, 1, 1);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  return g;
}

// Small next to the avatar, as a real butterfly would be (wingspan about a third of its height).
const BUTTERFLY_SCALE = 0.5;

const SPECS = [
  { color: '#ff9fcb', center: [0.9, 1.5, -2.6], radius: [1.6, 0.35, 1.2], speed: 0.45, phase: 0 },
  { color: '#ffd45a', center: [-1.6, 1.1, -5.5], radius: [2.1, 0.4, 1.6], speed: 0.36, phase: 2.1 },
  { color: '#8fd3ff', center: [2.4, 1.7, -8.5], radius: [2.4, 0.5, 1.8], speed: 0.3, phase: 4.2 },
];

function Butterfly({ spec }) {
  const rt = useForest();
  const root = useRef();
  const left = useRef();
  const right = useRef();
  const geos = useMemo(() => ({ l: wingGeometry(-1), r: wingGeometry(1) }), []);
  const mat = useMemo(
    () => new THREE.MeshBasicMaterial({ color: spec.color, vertexColors: true, side: THREE.DoubleSide, fog: false, transparent: true, opacity: 0.95 }),
    [spec.color],
  );
  const base = useMemo(() => new THREE.Color(spec.color), [spec.color]);
  const prev = useMemo(() => new THREE.Vector3(), []);
  const next = useMemo(() => new THREE.Vector3(), []);

  useEffect(
    () => () => {
      geos.l.dispose();
      geos.r.dispose();
      mat.dispose();
    },
    [geos, mat],
  );

  useFrame(() => {
    const t = rt.shared.uTime.value * spec.speed * (rt.reduced ? 0.35 : 1) + spec.phase;
    const at = (tt, out) =>
      out.set(
        spec.center[0] + Math.sin(tt) * spec.radius[0] + Math.sin(tt * 2.3) * 0.25,
        spec.center[1] + Math.sin(tt * 1.7) * spec.radius[1],
        spec.center[2] + Math.cos(tt * 0.8) * spec.radius[2],
      );
    at(t, next);
    at(t - 0.05, prev);
    if (root.current) {
      root.current.position.copy(next);
      root.current.rotation.y = Math.atan2(next.x - prev.x, next.z - prev.z);
      root.current.visible = rt.palette.night < 0.6 && rt.degrade < 1;
    }
    // take the time-of-day light like the grass does (warm at Maghrib)
    mat.color.copy(base).multiply(rt.palette.grass);
    const flap = rt.reduced ? 0.3 : 1;
    const a = Math.sin(rt.shared.uTime.value * 11 + spec.phase * 3) * 0.75 * flap + 0.45;
    // positive a lifts both wings (they meet above the body at the top of the beat)
    if (left.current) left.current.rotation.z = -a;
    if (right.current) right.current.rotation.z = a;
  });

  return (
    <group ref={root} scale={BUTTERFLY_SCALE}>
      <group ref={left}>
        <mesh geometry={geos.l} material={mat} />
      </group>
      <group ref={right}>
        <mesh geometry={geos.r} material={mat} />
      </group>
    </group>
  );
}

/** A few butterflies drifting over the meadow, hidden at night. */
export default function Butterflies() {
  return (
    <>
      {SPECS.map((s) => (
        <Butterfly key={s.color} spec={s} />
      ))}
    </>
  );
}
