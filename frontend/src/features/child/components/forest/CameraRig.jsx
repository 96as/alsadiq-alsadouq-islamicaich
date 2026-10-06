/* The frame loop mutates the camera, the runtime and one DOM layer by design. */
/* eslint-disable react-hooks/immutability */
import { useEffect, useMemo, useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { useForest } from './forestContext';
import { avatarFilterCss } from './palette';
import { avatarFeetX } from './runtime';
import { walkRemaining } from '../avatar/walkIn';
import { AVATAR_CAM, avatarCamPose, bearingOver, elevationOver, walkCamAz, walkCamElev } from '../avatar/avatarCam';
import { pathX } from './geometry';
import { AVATAR_HEIGHT } from '../meadowFraming';

// The avatar's height in its own canvas units when the model has not been measured yet, and how far up
// that height the bubble's tail points (the top of the head sits a little below the full height).
const DEFAULT_AVATAR_HEIGHT = 0.85;
const HEAD_FRACTION = 1;

const WIDE_DIR = new THREE.Vector3();
const FAR = new THREE.Vector3();
const NEAR = new THREE.Vector3();

/** Writes the ground point `rem` units up the path from the avatar's spot into `out`. */
function standAt(rt, spot, rem, out) {
  out.copy(spot);
  if (rt.modelFeet || rt.stats.triangles.model) {
    WIDE_DIR.set(spot.x - rt.poses.wide.pos.x, 0, spot.z - rt.poses.wide.pos.z).normalize();
    out.addScaledVector(WIDE_DIR, rem);
  } else {
    out.x += pathX(rem);
    out.z -= rem;
  }
  return out;
}

/**
 * Sets rt.stand, the avatar's ground point. Normally that is its spot. While the walk-in plays
 * it is a point further up the path: the built-in forest has a known path curve, a Blender
 * forest gets a straight line away from the wide camera (its path is not known to the code).
 * Also reports, for the avatar's gait:
 * - `walk.heading`, -1..1: which way the avatar moves across the screen, so the procedural gait
 *   can turn three quarters toward that side (its legs read badly head-on);
 * - `walk.travelYaw`, radians: the direction it really travels as the camera `eye` sees it
 *   (0 = straight at the camera, + = toward screen right). The Walk clip faces exactly this way,
 *   because its feet only stay planted when they push straight back along the path.
 */
function updateStand(rt, eye) {
  const spot = rt.modelFeet || rt.feet;
  const w = rt.walk;
  const rem = walkRemaining(w);
  if (rem <= 0) {
    rt.stand.copy(spot);
    w.heading = 0;
    return;
  }
  standAt(rt, spot, rem, rt.stand);
  const cam = rt.poses.wide.pos;
  standAt(rt, spot, rem + 0.15, FAR);
  standAt(rt, spot, Math.max(rem - 0.15, 0), NEAR);
  const bFar = (FAR.x - cam.x) / Math.max(cam.z - FAR.z, 0.5);
  const bNear = (NEAR.x - cam.x) / Math.max(cam.z - NEAR.z, 0.5);
  w.heading = Math.tanh(300 * (bNear - bFar));
  // Travel direction split into "toward the eye" and "across the view", on the ground plane.
  const dx = NEAR.x - FAR.x;
  const dz = NEAR.z - FAR.z;
  let tx = eye.x - rt.stand.x;
  let tz = eye.z - rt.stand.z;
  const tl = Math.hypot(tx, tz);
  if (tl > 1e-6 && dx * dx + dz * dz > 1e-10) {
    tx /= tl;
    tz /= tl;
    w.travelYaw = Math.atan2(dx * tz - dz * tx, dx * tx + dz * tz);
  }
}

const smoother = (t) => t * t * t * (t * (t * 6 - 15) + 10);

/**
 * Drives the forest camera and keeps the Avatar layer glued to the ground.
 * - glides from the wide shot to the talking shot when the session starts
 * - gentle breathing and a tiny pointer parallax (the painted backdrop only
 *   holds up while the camera stays near the centre, so everything is clamped)
 * - projects the avatar's feet and scales/translates the avatar layer to match
 */
export default function CameraRig() {
  const rt = useForest();
  const { camera, size } = useThree();

  const tmp = useMemo(
    () => ({
      avCam: new THREE.PerspectiveCamera(AVATAR_CAM.fov, 1, 0.1, 100),
      avPose: { pos: [0, 0, 0], look: [0, 0, 0] },
      v: new THREE.Vector3(),
      pos: new THREE.Vector3(),
      dirA: new THREE.Vector3(),
      dirB: new THREE.Vector3(),
      dir: new THREE.Vector3(),
      look: new THREE.Vector3(),
      lastFilter: '',
      wPos: new THREE.Vector3(),
      wLook: new THREE.Vector3(),
      canvas: null,
      lastOpacity: -1,
    }),
    [],
  );

  useEffect(() => {
    const el = rt.layerEl;
    return () => {
      if (el) el.style.filter = '';
      if (tmp.canvas) {
        tmp.canvas.style.transform = '';
        tmp.canvas.style.transformOrigin = '';
        tmp.canvas.style.opacity = '';
      }
    };
  }, [rt, tmp]);

  useFrame((state, dt) => {
    const d = Math.min(dt, 0.1);
    const { poses } = rt;
    const target = rt.phase === 'talk' ? 1 : 0;
    if (rt.reduced) rt.glide = target;
    else rt.glide += Math.sign(target - rt.glide) * Math.min(Math.abs(target - rt.glide), d / 2.6);
    const e = smoother(rt.glide);

    const t = rt.shared.uTime.value;
    const calm = rt.reduced ? 0 : 1;
    // pointer parallax, smoothed and clamped
    const pk = 1 - Math.exp(-d * 3);
    rt.pointer.sx += (rt.pointer.x - rt.pointer.sx) * pk;
    rt.pointer.sy += (rt.pointer.y - rt.pointer.sy) * pk;
    const wideAmt = 1 - e;

    // Portrait phones: centre the avatar on the path and tilt down so it stands
    // in the middle of the screen, clear of the card at the bottom. Only for the
    // built-in framing; a Blender model brings its own CamStart.
    const aspectNow = size.width / size.height;
    // The built-in scene stands the avatar where Avatar.jsx draws it for this
    // aspect (it moves to the centre on narrow screens); a Blender AvatarSpot wins.
    if (!rt.modelFeet) rt.feet.x = avatarFeetX(aspectNow);
    const narrow = rt.stats.triangles.model ? 0 : THREE.MathUtils.clamp((0.95 - aspectNow) / 0.45, 0, 1);
    updateStand(rt, camera.position);

    tmp.wPos.copy(poses.wide.pos);
    tmp.wLook.copy(poses.wide.look);
    tmp.wPos.x = THREE.MathUtils.lerp(tmp.wPos.x, rt.feet.x, narrow);
    tmp.wLook.x = THREE.MathUtils.lerp(tmp.wLook.x, rt.feet.x, narrow);
    tmp.wLook.y = THREE.MathUtils.lerp(tmp.wLook.y, -1.4, narrow);

    tmp.pos.lerpVectors(tmp.wPos, poses.talk.pos, e);
    tmp.pos.x += (Math.sin(t * 0.37) * 0.05 + rt.pointer.sx * 0.36 * wideAmt) * calm;
    tmp.pos.y += (Math.sin(t * 0.52) * 0.03 + rt.pointer.sy * 0.12 * wideAmt) * calm;
    tmp.pos.z += Math.sin(t * 0.29) * 0.04 * calm;

    tmp.dirA.copy(tmp.wLook).sub(tmp.wPos).normalize();
    tmp.dirB.copy(poses.talk.look).sub(poses.talk.pos).normalize();
    tmp.dir.lerpVectors(tmp.dirA, tmp.dirB, e).normalize();
    tmp.look.copy(tmp.pos).addScaledVector(tmp.dir, 10);

    camera.position.copy(tmp.pos);
    camera.lookAt(tmp.look);
    const fov = THREE.MathUtils.lerp(poses.wide.fov, poses.talk.fov, e);
    if (Math.abs(camera.fov - fov) > 0.001 || camera.aspect !== size.width / size.height) {
      camera.fov = fov;
      camera.aspect = size.width / size.height;
      camera.updateProjectionMatrix();
    }
    camera.updateMatrixWorld();

    // The avatar canvas looks at its ground from the forest camera's elevation while it walks in, so a
    // step back covers the same ground on screen as in the forest (see avatar/avatarCam.js).
    const cp = camera.position;
    const st = rt.stand;
    rt.walk.camElev = walkCamElev(rt.walk, elevationOver(cp.x, cp.y, cp.z, st.x, st.y, st.z));
    rt.walk.camAz = walkCamAz(rt.walk, bearingOver(cp.x, cp.z, st.x, st.z));

    // Keep the avatar layer's feet on the forest ground.
    const el = rt.layerEl;
    if (!el) return;
    const aspect = size.width / size.height;
    const feet = rt.stand;
    const av = tmp.avCam;
    av.aspect = aspect;
    const avFeetX = avatarFeetX(aspect);
    const pose = avatarCamPose(rt.walk.camElev, avFeetX, tmp.avPose, rt.walk.camAz);
    av.position.set(...pose.pos);
    av.lookAt(...pose.look);
    av.updateProjectionMatrix();
    av.updateMatrixWorld();
    tmp.v.set(avFeetX, 0, 0).project(av);
    const ax = (tmp.v.x * 0.5 + 0.5) * size.width;
    const ay = (-tmp.v.y * 0.5 + 0.5) * size.height;
    const avDepth = tmp.v.set(avFeetX, 0, 0).applyMatrix4(av.matrixWorldInverse).z * -1;

    tmp.v.copy(feet).applyMatrix4(camera.matrixWorldInverse);
    const fDepth = -tmp.v.z;
    tmp.v.copy(feet).project(camera);
    const fx = (tmp.v.x * 0.5 + 0.5) * size.width;
    const fy = (-tmp.v.y * 0.5 + 0.5) * size.height;
    const scale = (avDepth * Math.tan((AVATAR_CAM.fov * Math.PI) / 360)) / (Math.max(fDepth, 0.2) * Math.tan((fov * Math.PI) / 360));
    // publish the feet and the avatar's height on screen (the foreground strip limits itself to the legs with it)
    rt.screen.x = fx;
    rt.screen.y = fy;
    rt.screen.avatarPx =
      scale * (AVATAR_HEIGHT / (2 * avDepth * Math.tan((AVATAR_CAM.fov * Math.PI) / 360))) * size.height;
    // Transform the avatar's <canvas> itself, never an ancestor: R3F sizes its
    // canvas from getBoundingClientRect() of the wrapper, which includes ancestor
    // transforms, so a scaled layer made the avatar shrink again on every resize
    // or scroll (phone URL bar, rotation). The canvas sits at the layer origin.
    if (!tmp.canvas || !tmp.canvas.isConnected) tmp.canvas = el.querySelector('canvas');
    // Publish where Sadiq's feet and head are on screen (CSS px inside the stage), for the HTML overlay.
    // The model's height comes from the avatar canvas (walk.modelHeight, measured once from its bounds).
    const sc = rt.screen;
    const pxPerUnit = size.height / (2 * Math.max(avDepth, 0.2) * Math.tan((AVATAR_CAM.fov * Math.PI) / 360));
    const heightPx = (rt.walk.modelHeight || DEFAULT_AVATAR_HEIGHT) * pxPerUnit * scale;
    sc.feetX = fx;
    sc.feetY = fy;
    sc.headX = fx;
    sc.headY = fy - heightPx * HEAD_FRACTION;
    sc.heightPx = heightPx;
    sc.width = size.width;
    sc.height = size.height;
    sc.visible = rt.walk.fade > 0.05;
    const cv = tmp.canvas;
    if (cv) {
      cv.style.transformOrigin = `${ax.toFixed(3)}px ${ay.toFixed(3)}px`;
      cv.style.transform = `translate(${(fx - ax).toFixed(3)}px, ${(fy - ay).toFixed(3)}px) scale(${scale.toFixed(6)})`;
      // fades in at the far end of the path while the walk-in starts
      const fade = Math.round(rt.walk.fade * 100) / 100;
      if (fade !== tmp.lastOpacity) {
        tmp.lastOpacity = fade;
        cv.style.opacity = fade >= 1 ? '' : String(fade);
      }
    }
    // tint the avatar with the time of day (only touches the DOM when the value changes)
    const filter = avatarFilterCss(rt.palette.avatar);
    if (filter !== tmp.lastFilter) {
      tmp.lastFilter = filter;
      el.style.filter = filter;
    }
  });

  return null;
}

const SHADOW_FRAG = /* glsl */ `
  varying vec2 vUv;
  uniform float uFade;
  void main() {
    float r = length(vUv - 0.5) * 2.0;
    float a = smoothstep(1.0, 0.1, r) * 0.55 * uFade;
    gl_FragColor = vec4(0.04, 0.1, 0.03, a);
  }
`;

/** Soft contact shadow under the avatar's feet (the avatar layer has none of its own on this ground). */
export function AvatarShadow() {
  const rt = useForest();
  const mesh = useRef();
  const material = useMemo(
    () =>
      new THREE.ShaderMaterial({
        transparent: true,
        depthWrite: false,
        fog: false,
        uniforms: { uFade: { value: 1 } },
        vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
        fragmentShader: SHADOW_FRAG,
      }),
    [],
  );
  useEffect(() => () => material.dispose(), [material]);
  // follows the feet, which change with the screen aspect (see CameraRig)
  useFrame(() => {
    const f = rt.stand;
    if (!mesh.current) return;
    mesh.current.position.set(f.x, f.y + 0.015, f.z);
    mesh.current.visible = rt.walk.fade > 0.01;
    material.uniforms.uFade.value = rt.walk.fade;
  });
  return (
    <mesh ref={mesh} rotation={[-Math.PI / 2, 0, 0]} material={material} renderOrder={2}>
      <planeGeometry args={[1.5, 0.9]} />
    </mesh>
  );
}
