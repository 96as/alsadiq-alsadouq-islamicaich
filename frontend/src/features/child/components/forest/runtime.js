import * as THREE from 'three';
import { createSharedUniforms } from './materials';
import { makePalette, makeTargets } from './palette';
import { STATE, createWalk } from '../avatar/walkIn';
import { makeWindState } from './wind/windField';

/**
 * The mutable state the frame loop reads and writes. It is a plain object on
 * purpose: React state would re-render the whole scene on every change.
 * `poses` hold the camera framing for the wide idle shot and the talking shot,
 * the Blender model may replace them (CamStart/CamTalk empties).
 */
export function createRuntime({ quality, reduced, timeName, walkMode = 'walk', walkPreset = 'default' }) {
  const walk = createWalk(walkMode, walkPreset);
  if (walkMode === 'off') {
    walk.state = STATE.DONE;
    walk.fade = 1;
  }
  return {
    // The avatar's walk-in, shared with the Avatar canvas (see avatar/walkIn.js).
    walk,
    // Where the avatar stands this frame: its spot, or a point up the path while it walks in.
    stand: new THREE.Vector3(-0.13, 0, 0),
    // The CPU mirror of the wind (windField.js), refreshed every frame by SceneClock. Flowers, butterflies and seeds read it.
    wind: makeWindState(),
    // The avatar's last footprints (8), for the grass that leans away from them.
    trail: { x: new Float32Array(8), z: new Float32Array(8), t: new Float32Array(8).fill(-1e3), head: 0, last: -1, lx: 1e4, lz: 1e4 },
    // dev only: extra prints to check the foot push in the grass (set by the /dev/forest panel)
    devFeet: null,
    // dev only: when a number, the scene clock stays at that time (frozen-time pairs for the checks)
    freezeTime: null,
    quality,
    reduced,
    timeName,
    phase: 'wide',
    glide: 0,
    shared: createSharedUniforms(),
    palette: makePalette(timeName),
    targets: makeTargets(),
    // Where the avatar's feet stand in the forest. The procedural scene keeps
    // x tied to the avatar layout, a Blender AvatarSpot overrides all of it.
    feet: new THREE.Vector3(-0.13, 0, 0),
    modelFeet: null,
    poses: {
      wide: {
        pos: new THREE.Vector3(0.7, 1.55, 5.6),
        look: new THREE.Vector3(-0.1, 1.0, -14),
        fov: 44,
      },
      talk: {
        pos: new THREE.Vector3(0, 0.9, 3.2),
        look: new THREE.Vector3(0, 0.7, 0),
        fov: 32,
      },
    },
    pointer: { x: 0, y: 0, sx: 0, sy: 0 },
    // Where things are on screen, in CSS px inside the stage. CameraRig writes `screen` (the avatar)
    // and ForestProps writes `propBox`. The HTML overlay reads them (useStageAnchor), so the bubble and
    // the tap targets sit on the 3D objects without any React state per frame.
    // avatar-integ: x, y and avatarPx are the feet and on-screen height the foreground strip reads (avatar-studio).
    screen: { x: 0, y: 0, avatarPx: 0, feetX: 0, feetY: 0, headX: 0, headY: 0, heightPx: 0, width: 0, height: 0, visible: false },
    propBox: {
      lantern: { x: 0, y: 0, w: 0, h: 0, visible: false },
      book: { x: 0, y: 0, w: 0, h: 0, visible: false },
      bird: { x: 0, y: 0, w: 0, h: 0, visible: false },
    },
    // Head turn target for Sadiq: x and y are -1..1 from his head toward what he looks at, weight 0..1.
    gaze: { x: 0, y: 0, weight: 0 },
    // What he is looking at: { name: 'lantern'|'book'|'bird' } or { x, y } in stage px, until a time. See lookAt().
    gazeFocus: null,
    // Hover state of the tap targets (the DOM buttons set it, the 3D objects read it).
    props: { lantern: { hover: 0 }, book: { hover: 0 }, bird: { hover: 0 } },
    // Set by the landing's time pill to preview another time of day; null follows the device clock.
    timeOverride: null,
    // Quality ladder that PerformanceMonitor walks down when frames are slow. Never goes back up.
    degrade: 0,
    paused: false,
    layerEl: null,
    bus: new EventTarget(),
    stats: { triangles: {}, total: 0 },
  };
}

export function addTriangles(rt, name, count) {
  rt.stats.triangles[name] = count;
  rt.stats.total = Object.values(rt.stats.triangles).reduce((a, b) => a + b, 0);
}

/** Where the Avatar places itself on x: -0.13 on wide screens, -0.02 on narrow ones. */
export function avatarFeetX(aspect) {
  return aspect >= 0.8 ? -0.13 : -0.02;
}

/** Ask Sadiq to turn his head toward a prop ({ name }) or a point in the stage ({ x, y }, CSS px) for a moment. */
export function lookAt(rt, target, seconds = 1.6) {
  rt.gazeFocus = { ...target, untilMs: performance.now() + seconds * 1000 };
}
