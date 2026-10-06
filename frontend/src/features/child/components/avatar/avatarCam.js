// The avatar canvas camera, shared by the avatar canvas (Avatar.jsx) and the forest rig (CameraRig.jsx).
//
// The avatar is drawn in its own canvas and laid over the forest by CSS (scale and translate of the
// canvas). The ground in that canvas is seen from the default camera at about 15.7 degrees; the
// forest camera sees the far end of the path at about 9 degrees. A foot that steps back by 0.1 m
// therefore moves 1.78 times further across the forest ground than across the avatar ground, so the
// planted foot slides on screen (moonwalking) although the clip itself is slip free.
//
// The fix: while the avatar walks in, the avatar camera orbits about the avatar's feet to the
// forest camera's elevation over the stand point. The orbit keeps the distance, so the feet stay on
// the same screen pixel with the same scale, and the CSS placement in CameraRig does not change.
// `walk.camElev` carries the elevation (radians), published by CameraRig; it is null (default
// camera, exactly the talk shot) whenever the walk is not running.
//
// Plain numbers apart from walkIn's state constants, so node can test it.
import { STATE, walkRemaining } from './walkIn.js';

/** The camera the Avatar canvas has always used (and the talking shot of the forest). */
export const AVATAR_CAM = { pos: [0, 0.9, 3.2], look: [0, 0.7, 0], fov: 32 };
/** The default camera's elevation over the ground below the look point, 15.7 degrees. */
export const DEFAULT_ELEV = Math.atan2(AVATAR_CAM.pos[1], AVATAR_CAM.pos[2]);
const MIN_ELEV = 0.05;
const MAX_ELEV = 0.6;
const MAX_AZ = 0.6;
/** Seconds over which the elevation returns to the default camera once the avatar has stopped. */
export const TURN_BLEND = 0.6;

const smooth = (x) => {
  const c = x < 0 ? 0 : x > 1 ? 1 : x;
  return c * c * (3 - 2 * c);
};

/**
 * Writes the avatar camera for the camera elevation `elev` (radians) into `out` and returns it.
 * The default camera is orbited about the feet point (feetX, 0, 0) in the vertical plane that holds
 * the camera, so the distance, the screen position of the feet and the framing are kept.
 * An elevation equal to DEFAULT_ELEV (or null) gives the default pose exactly.
 */
export function avatarCamPose(elev, feetX = -0.13, out = { pos: [0, 0, 0], look: [0, 0, 0] }, az = 0) {
  const [px, py, pz] = AVATAR_CAM.pos;
  const [lx, ly, lz] = AVATAR_CAM.look;
  const noAz = az == null || Math.abs(az) < 1e-9;
  if ((elev == null || Math.abs(elev - DEFAULT_ELEV) < 1e-9) && noAz) {
    out.pos[0] = px;
    out.pos[1] = py;
    out.pos[2] = pz;
    out.look[0] = lx;
    out.look[1] = ly;
    out.look[2] = lz;
    return out;
  }
  const e = elev == null ? DEFAULT_ELEV : Math.min(Math.max(elev, MIN_ELEV), MAX_ELEV);
  const delta = e - DEFAULT_ELEV;
  const c = Math.cos(delta);
  const s = Math.sin(delta);
  // h: the horizontal direction from the feet to the camera; the rotation turns (along h, up) about the feet
  let hx = px - feetX;
  let hz = pz;
  const hl = Math.hypot(hx, hz);
  hx /= hl;
  hz /= hl;
  const orbit = (x, y, z, dst) => {
    const rx = x - feetX;
    const u = rx * hx + z * hz; // along h
    const w = -rx * hz + z * hx; // across h, unchanged
    const u2 = u * c - y * s;
    const y2 = u * s + y * c;
    dst[0] = feetX + u2 * hx - w * hz;
    dst[1] = y2;
    dst[2] = u2 * hz + w * hx;
  };
  orbit(px, py, pz, out.pos);
  orbit(lx, ly, lz, out.look);
  if (!noAz) {
    // then turn both about the vertical through the feet by the bearing the forest camera sees the stand point
    // from, so the avatar's yaw (which the rig measures against the eye ray) and its ground direction agree:
    // the sense is the mirror of the forest's bearing because the yaw is measured the other way round
    const a = Math.min(Math.max(az, -MAX_AZ), MAX_AZ);
    const ca = Math.cos(a);
    const sa = Math.sin(a);
    for (const v of [out.pos, out.look]) {
      const rx = v[0] - feetX;
      const rz = v[2];
      v[0] = feetX + rx * ca - rz * sa;
      v[2] = rx * sa + rz * ca;
    }
  }
  return out;
}

/** Bearing of the forest camera as seen from the stand point (radians, 0 = on the +z side, + = toward +x). */
export function bearingOver(camX, camZ, standX, standZ) {
  return Math.atan2(camX - standX, camZ - standZ);
}

/** The azimuth the avatar camera should take this frame: the same rule as walkCamElev, blending back to 0. */
export function walkCamAz(w, raw) {
  if (walkRemaining(w) > 0) return raw;
  if (w.state === STATE.TURN) return raw * (1 - smooth(w.t / TURN_BLEND));
  return null;
}

/** Elevation of the forest camera over the avatar's ground point: atan2(height above it, distance along the ground). */
export function elevationOver(camX, camY, camZ, standX, standY, standZ) {
  return Math.atan2(camY - standY, Math.hypot(camX - standX, camZ - standZ));
}

/**
 * The elevation the avatar camera should take this frame. `raw` is the forest camera's elevation over
 * the stand point. While the avatar is waiting or walking it is `raw`; in TURN it blends back to the
 * default camera; afterwards (wave, done, hop) it is exactly the default, so the talk shot is untouched.
 */
export function walkCamElev(w, raw) {
  if (walkRemaining(w) > 0) return raw;
  if (w.state === STATE.TURN) {
    const b = smooth(w.t / TURN_BLEND);
    return raw + (DEFAULT_ELEV - raw) * b;
  }
  return null;
}
