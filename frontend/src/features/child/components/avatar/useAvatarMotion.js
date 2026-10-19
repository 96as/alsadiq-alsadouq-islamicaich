import { useEffect, useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { MathUtils, Quaternion } from 'three';
import {
  ARM_POSE_Z,
  ARM_SWAY,
  BREATH_HZ,
  BREATH_NECK,
  BREATH_PEC,
  BREATH_SPINE,
  EMPHASIS_NOD,
  EMPHASIS_SWAY,
  GLANCE_DAMP,
  GLANCE_HOLD,
  GLANCE_PITCH,
  GLANCE_REST,
  GLANCE_YAW,
  HAND_SWAY,
  JAW_ATTACK,
  JAW_LEVEL_FLOOR,
  JAW_PEAK_DECAY,
  JAW_PEAK_MIN,
  JAW_MAX,
  JAW_RELEASE,
  JAW_SYNTH_HZ_A,
  JAW_SYNTH_HZ_B,
  P,
  POSE_DAMP,
  REDUCED_OSC,
  REDUCED_POSE,
  SHIFT_HZ,
  SHIFT_ROLL,
  SHIFT_YAW,
  STATE_TARGETS,
} from './motionConfig';
import { STATE, applyWalk, buildLegRig, stepWalk } from './walkIn';
import { LipsyncRig } from './lipsync/lipsyncRig.js';

const TAU = Math.PI * 2;
// Gaze (runtime.js rt.gaze): how far the head may turn toward a target on screen, in radians.
const GAZE_YAW = 0.35;
const GAZE_PITCH = 0.2;
const GAZE_DAMP = 5;
const MAX_DT = 0.1; // a stalled tab must not make the avatar snap
const { damp, clamp } = MathUtils;
const headDelta = new Quaternion(); // per-frame scratch, reused (frames run one at a time)

/** A rig entry keeps the bone and its rest rotation as plain numbers (no Euler clones per frame). */
function entry(bone) {
  return bone ? { bone, x: bone.rotation.x, y: bone.rotation.y, z: bone.rotation.z } : null;
}

/**
 * In avatar-web.glb the jaw hangs off neck > Bone.008, a sibling of the head on the same pivot,
 * so turning the head bone leaves the lower face behind (the mouth gapes and shears). Return the
 * jaw's ancestor that sits beside the head, so it can copy the head's turn each frame.
 */
function findJawCarrier(head, jaw) {
  if (!head || !jaw) return null;
  for (let node = jaw.bone.parent; node?.parent; node = node.parent) {
    if (node === head.bone) return null; // the jaw already follows the head
    if (node.parent === head.bone.parent) {
      return {
        bone: node,
        restQ: node.quaternion.clone(),
        restP: node.position.clone(),
        headRestInv: head.bone.quaternion.clone().invert(),
        headP: head.bone.position.clone(),
      };
    }
  }
  return null;
}

/**
 * Finds the bones once, when the scene is cloned and before any frame has moved them, and
 * records their rest rotations. GLTFLoader strips dots from node names, so `pec.l` is `pecl`.
 */
export function buildRig(scene) {
  const byName = new Map();
  scene.traverse((obj) => {
    if (!obj.name) return;
    byName.set(obj.name, obj);
    byName.set(obj.name.replaceAll('.', ''), obj);
  });
  const get = (name) => entry(byName.get(name) || byName.get(name.replaceAll('.', '')));
  const rig = {
    head: get('head'),
    neck: get('neck'),
    jaw: get('jaw'),
    spine: get('Bone'),
    pecL: get('pec.l'),
    pecR: get('pec.l.001'),
    armL: get('arm.l'),
    armR: get('arm.r'),
    handL: get('hand.l'),
    handR: get('hand.r'),
  };
  for (const [name, value] of Object.entries(rig)) {
    if (!value) console.warn(`[Avatar] Bone "${name}" not found in the GLB; that motion is skipped.`);
  }
  rig.jawCarrier = findJawCarrier(rig.head, rig.jaw);
  rig.legs = buildLegRig(byName);
  return rig;
}

/** The model's root transform at rest, as plain numbers, for the walk-in to offset. */
function rootBase(scene) {
  const { position: p, rotation: r } = scene;
  return { root: scene, x: p.x, y: p.y, z: p.z, rx: r.x, ry: r.y, rz: r.z };
}

export function useReducedMotion() {
  const ref = useRef(false);
  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return undefined;
    const query = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => {
      ref.current = query.matches;
    };
    update();
    query.addEventListener('change', update);
    return () => query.removeEventListener('change', update);
  }, []);
  return ref;
}

function createMotionState() {
  const pose = new Float32Array(P.COUNT);
  pose.set(STATE_TARGETS.idle);
  return {
    pose,
    jaw: 0, // smoothed jaw opening, 0..1
    env: 0, // smoothed voice envelope for head emphasis
    glanceYaw: 0,
    glancePitch: 0,
    glanceTargetYaw: 0,
    glanceTargetPitch: 0,
    glanceActive: false,
    nextGlanceAt: 3,
    osc: 1, // eased oscillation scale (reduced motion lowers it)
    posek: 1, // eased pose-bias scale
    swayPhase: 0, // integrated, so changing the sway rate between states never jumps
    gazeX: 0, // smoothed head turn toward rt.gaze, -1..1
    gazeY: 0,
    gazeW: 0,
    levelPeak: 0, // loudest recent voice level, fading at JAW_PEAK_DECAY (auto gain for the jaw)
  };
}

function randomBetween(range) {
  return range[0] + Math.random() * (range[1] - range[0]);
}

/**
 * Drives every bone of the avatar each frame: idle life (breathing, sway, glances, weight
 * shift, relaxed arms), the three agent states, and the speaking jaw.
 *
 * Nothing is allocated per frame: all working values live in `s`, and bones are rewritten
 * from their recorded rest rotation, so the animation never drifts.
 *
 * @param scene            the cloned avatar scene
 * @param state            'idle' | 'listening' | 'thinking' | 'speaking' (see resolveMotionState)
 * @param getAudioLevel    optional () => RMS level of the agent's voice, or a negative number when unavailable
 * @param walk             optional shared walk-in object (see walkIn.js). Without it there is no walk.
 * @param gaze             optional { x, y, weight } head-turn target, -1..1 (see runtime.js). Without it no turn.
 * @param getLipsync       optional () => the agent's live viseme state (see lipsync/useVisemes.js), or
 *                         null. Drives viseme morph targets and the blink when the GLB has them.
 * @param morphNames       optional { viseme: morphName } overrides (see lipsync/morphTargets.js)
 */
export default function useAvatarMotion(scene, { state, getAudioLevel, walk, gaze, getLipsync, morphNames }) { // avatar-integ: gaze + lipsync
  const rig = useMemo(() => buildRig(scene), [scene]);
  const base = useMemo(() => rootBase(scene), [scene]);
  const reducedRef = useReducedMotion();
  const stateRef = useRef(state);
  const levelFnRef = useRef(getAudioLevel);
  const lipsyncFnRef = useRef(getLipsync);
  const lipRig = useMemo(() => new LipsyncRig(scene, { morphNames }), [scene, morphNames]);
  // Refs are refreshed after each commit, never during render.
  useEffect(() => {
    stateRef.current = state;
    levelFnRef.current = getAudioLevel;
    lipsyncFnRef.current = getLipsync;
  }, [state, getAudioLevel, getLipsync]);

  const motionRef = useRef(null); // created on the first frame, then mutated in place

  useFrame((frame, delta) => {
    if (motionRef.current === null) motionRef.current = createMotionState();
    const m = motionRef.current;
    const dt = Math.min(delta, MAX_DT);
    const t = frame.clock.elapsedTime;
    const motionState = stateRef.current;
    const reduced = reducedRef.current;

    // Ease the scales, so toggling reduced motion does not pop.
    m.osc = damp(m.osc, reduced ? REDUCED_OSC : 1, 4, dt);
    m.posek = damp(m.posek, reduced ? REDUCED_POSE : 1, 4, dt);
    const osc = m.osc;

    // Ease every pose parameter toward the active state's target.
    const target = STATE_TARGETS[motionState] || STATE_TARGETS.idle;
    const pose = m.pose;
    for (let i = 0; i < P.COUNT; i++) pose[i] = damp(pose[i], target[i], POSE_DAMP, dt);

    // Voice: jaw openness and the envelope used for head emphasis.
    const speaking = motionState === 'speaking';
    let openTarget = 0;
    if (speaking) {
      const level = levelFnRef.current ? levelFnRef.current() : -1;
      if (level >= 0) {
        m.levelPeak = Math.max(level, m.levelPeak * Math.exp(-JAW_PEAK_DECAY * dt));
        const full = Math.max(m.levelPeak, JAW_PEAK_MIN);
        openTarget = clamp((level - JAW_LEVEL_FLOOR) / (full - JAW_LEVEL_FLOOR), 0, 1);
      } else {
        const a = (Math.sin(t * JAW_SYNTH_HZ_A) + 1) * 0.5;
        const b = (Math.sin(t * JAW_SYNTH_HZ_B + 1.3) + 1) * 0.5;
        openTarget = 0.35 + 0.65 * a * (0.5 + 0.5 * b);
      }
    }
    m.jaw = damp(m.jaw, openTarget, openTarget > m.jaw ? JAW_ATTACK : JAW_RELEASE, dt);
    m.env = damp(m.env, openTarget, 6, dt);

    // Glances: look somewhere for a moment, then come back. Weighted by the state.
    if (t > m.nextGlanceAt) {
      if (m.glanceActive) {
        m.glanceActive = false;
        m.glanceTargetYaw = 0;
        m.glanceTargetPitch = 0;
        m.nextGlanceAt = t + randomBetween(GLANCE_REST);
      } else {
        m.glanceActive = true;
        m.glanceTargetYaw = (Math.random() * 2 - 1) * GLANCE_YAW;
        m.glanceTargetPitch = (Math.random() * 2 - 1) * GLANCE_PITCH;
        m.nextGlanceAt = t + randomBetween(GLANCE_HOLD);
      }
    }
    m.glanceYaw = damp(m.glanceYaw, m.glanceTargetYaw, GLANCE_DAMP, dt);
    m.glancePitch = damp(m.glancePitch, m.glanceTargetPitch, GLANCE_DAMP, dt);
    // Gaze: turn the head toward something on screen (the CTA, the lantern, the bird), damped.
    const gw = gaze ? gaze.weight : 0;
    m.gazeX = damp(m.gazeX, gaze ? gaze.x : 0, GAZE_DAMP, dt);
    m.gazeY = damp(m.gazeY, gaze ? gaze.y : 0, GAZE_DAMP, dt);
    m.gazeW = damp(m.gazeW, gw, GAZE_DAMP, dt);
    const gazeAmt = m.gazeW * (reduced ? 0.7 : 1);
    const gazeYaw = clamp(m.gazeX * GAZE_YAW * gazeAmt, -GAZE_YAW, GAZE_YAW);
    const gazePitch = clamp(m.gazeY * GAZE_PITCH * gazeAmt, -GAZE_PITCH, GAZE_PITCH);
    // while he looks at something on purpose, the random glance steps aside
    const glance = pose[P.GLANCE] * osc * (1 - Math.min(m.gazeW, 1));

    // Breathing and weight shift.
    const breath = Math.sin(t * TAU * BREATH_HZ);
    const breathAmp = pose[P.BREATH] * osc;
    const shift = Math.sin(t * TAU * SHIFT_HZ);
    const shiftYaw = Math.sin(t * TAU * SHIFT_HZ * 0.7 + 1.1);

    // Head: state bias + sway + glance + speaking emphasis. Split 60/40 between head and neck.
    m.swayPhase += pose[P.SWAY_HZ] * TAU * dt;
    const sp = m.swayPhase;
    const sway = pose[P.SWAY] * osc;
    const emphasis = pose[P.EMPHASIS] * osc;
    const headYaw =
      pose[P.YAW] * m.posek +
      Math.sin(sp) * sway +
      gazeYaw +
      m.glanceYaw * glance +
      Math.sin(sp * 0.61 + 2) * EMPHASIS_SWAY * emphasis;
    const headPitch =
      pose[P.PITCH] * m.posek +
      Math.sin(sp * 0.73 + 0.7) * sway * 0.45 +
      m.glancePitch * glance -
      gazePitch +
      m.env * EMPHASIS_NOD * emphasis;
    const headRoll =
      pose[P.ROLL] * m.posek +
      Math.sin(sp * 0.47 + 1.9) * sway * 0.5 +
      Math.sin(sp * 1.1) * EMPHASIS_SWAY * emphasis;
    // Cancel part of the weight-shift roll at the head so the gaze stays level.
    const headShiftRoll = shift * SHIFT_ROLL * osc;

    const r = rig;
    if (r.head) {
      r.head.bone.rotation.set(
        r.head.x + headPitch * 0.6,
        r.head.y + headYaw * 0.6,
        r.head.z + headRoll * 0.6 - headShiftRoll * 0.5,
      );
      // Carry the jaw with the head: apply the head's change from rest (in the neck's space)
      // to the jaw's carrier bone, rotating it about the head's pivot.
      const c = r.jawCarrier;
      if (c) {
        headDelta.copy(r.head.bone.quaternion).multiply(c.headRestInv);
        c.bone.quaternion.copy(headDelta).multiply(c.restQ);
        c.bone.position.copy(c.restP).sub(c.headP).applyQuaternion(headDelta).add(c.headP);
      }
    }
    if (r.neck) {
      r.neck.bone.rotation.set(
        r.neck.x + headPitch * 0.4 - breath * BREATH_NECK * breathAmp,
        r.neck.y + headYaw * 0.4,
        r.neck.z + headRoll * 0.4,
      );
    }

    // Mouth and eyelids: viseme and blink morphs when the GLB has them (lip-sync from the voice),
    // otherwise only the jaw bone below, as before. A GLB with neither (today's avatar-web.glb)
    // skips the voice analysis, so phones do not pay for it.
    const wantsLipsync = speaking && (lipRig.hasVisemes || lipRig.hasBlink) && lipsyncFnRef.current;
    const lipsync = wantsLipsync ? lipsyncFnRef.current() : null;
    lipRig.update(dt, { lipsync, open: m.jaw, speaking, reduced });

    // Jaw (scaled down to nothing when the viseme morphs open the mouth).
    if (r.jaw) r.jaw.bone.rotation.set(r.jaw.x + m.jaw * JAW_MAX * lipRig.jawScale, r.jaw.y, r.jaw.z);

    // Spine: lean toward the camera, breathe, shift weight. The torso is skinned to the static
    // neutral_bone, so this only carries the shoulders, arms and head; there is no chest scale.
    if (r.spine) {
      r.spine.bone.rotation.set(
        r.spine.x + pose[P.LEAN] * m.posek - breath * BREATH_SPINE * breathAmp,
        r.spine.y + shiftYaw * SHIFT_YAW * osc,
        r.spine.z + headShiftRoll,
      );
    }

    // Shoulders rise on the inhale. Arms hang relaxed, with a slow independent sway.
    const arms = pose[P.ARMS] * osc;
    const raise = breath * BREATH_PEC * breathAmp;
    if (r.pecL) r.pecL.bone.rotation.set(r.pecL.x, r.pecL.y, r.pecL.z + ARM_POSE_Z.pecl + raise);
    if (r.pecR) r.pecR.bone.rotation.set(r.pecR.x, r.pecR.y, r.pecR.z + ARM_POSE_Z.pecl001 - raise);
    if (r.armL) {
      r.armL.bone.rotation.set(
        r.armL.x + Math.sin(t * 0.83 + 0.4) * ARM_SWAY * 0.5 * arms,
        r.armL.y,
        r.armL.z + ARM_POSE_Z.arml + Math.sin(t * 0.71) * ARM_SWAY * arms - breath * 0.004 * breathAmp,
      );
    }
    if (r.armR) {
      r.armR.bone.rotation.set(
        r.armR.x + Math.sin(t * 0.79 + 2.1) * ARM_SWAY * 0.5 * arms,
        r.armR.y,
        r.armR.z + ARM_POSE_Z.armr - Math.sin(t * 0.67 + 1.3) * ARM_SWAY * arms + breath * 0.004 * breathAmp,
      );
    }
    if (r.handL) {
      r.handL.bone.rotation.set(
        r.handL.x + Math.sin(t * 1.07 + 0.9) * HAND_SWAY * arms,
        r.handL.y,
        r.handL.z + Math.sin(t * 0.91 + 0.2) * HAND_SWAY * 0.6 * arms,
      );
    }
    if (r.handR) {
      r.handR.bone.rotation.set(
        r.handR.x + Math.sin(t * 1.03 + 2.6) * HAND_SWAY * arms,
        r.handR.y,
        r.handR.z - Math.sin(t * 0.87 + 1.5) * HAND_SWAY * 0.6 * arms,
      );
    }

    // Walk-in: gait, waddle and wave on top of the idle pose. Skipped once it is over.
    if (walk && walk.state !== STATE.DONE) {
      stepWalk(walk, dt, { reduced });
      applyWalk(r, walk, base);
    }
  });
}
