// Tuning for the avatar's procedural motion. Angles are radians, rates are Hz.
//
// Bone axes (checked against avatar-web.glb, bones run along local +Y):
//   rotation.x  positive = pitch forward (nod down, lean in)
//   rotation.y  positive = turn toward the viewer's right
//   rotation.z  positive = roll, top of the head toward the viewer's left
//
// Nothing here may contain scripture or any other Islamic text; it is pure animation data.

export const MOTION_STATES = ['idle', 'listening', 'thinking', 'speaking'];

/**
 * Map the agent's real state (lk.agent.state) and the audio-level boolean to a motion state.
 * The real state wins; the boolean is only the fallback while the agent has not published one.
 */
export function resolveMotionState(agentState, isSpeaking) {
  if (agentState === 'listening' || agentState === 'thinking' || agentState === 'speaking') {
    return agentState;
  }
  return isSpeaking ? 'speaking' : 'idle';
}

// Order of the smoothed pose parameters. Each state has one target value per parameter.
export const P = {
  YAW: 0, // head turn bias
  PITCH: 1, // head nod bias (negative looks up)
  ROLL: 2, // head tilt bias
  SWAY: 3, // head sway amplitude
  SWAY_HZ: 4, // head sway rate
  GLANCE: 5, // 0..1, how often the avatar looks around
  LEAN: 6, // spine pitch (lean toward the camera)
  EMPHASIS: 7, // 0..1, head emphasis while talking
  BREATH: 8, // breathing amplitude multiplier
  ARMS: 9, // arm and hand life multiplier
  COUNT: 10,
};

//                      yaw    pitch  roll   sway   hz    glance lean   emph breath arms
export const STATE_TARGETS = {
  idle: [0.0, 0.0, 0.0, 0.05, 0.16, 1.0, 0.0, 0.0, 1.0, 1.0],
  // Tilt toward the camera and lean in a little, steady gaze.
  listening: [0.0, 0.035, 0.12, 0.018, 0.1, 0.2, 0.04, 0.0, 0.9, 0.7],
  // Head up and a little to the side, slower sway, no glancing around. No roll, and a modest
  // yaw: more (0.22 yaw, -0.05 roll) pushed the left cheek through the jacket collar.
  thinking: [0.15, -0.12, 0.0, 0.03, 0.07, 0.0, -0.012, 0.0, 0.8, 0.5],
  speaking: [0.0, 0.0, 0.0, 0.035, 0.22, 0.3, 0.012, 1.0, 1.15, 1.25],
};

// How fast each parameter eases toward its target (1/s, used by MathUtils.damp).
export const POSE_DAMP = 3.2;

// Breathing: 0.25 Hz, as the task file asks.
export const BREATH_HZ = 0.25;
export const BREATH_PEC = 0.016; // shoulder raise, rad
export const BREATH_SPINE = 0.007; // upper body leans back on inhale, rad
export const BREATH_NECK = 0.009; // head lifts a touch on inhale, rad

// Weight shift: a slow lean from one side to the other.
export const SHIFT_HZ = 0.085;
export const SHIFT_ROLL = 0.014;
export const SHIFT_YAW = 0.012;

// Glances: how long the avatar holds a look and how long it rests between looks.
export const GLANCE_YAW = 0.2;
export const GLANCE_PITCH = 0.06;
export const GLANCE_HOLD = [0.9, 1.8];
export const GLANCE_REST = [2.8, 6.5];
export const GLANCE_DAMP = 5;

// Speaking jaw.
export const JAW_MAX = 0.26; // rad, a small open and close, not a gape
export const JAW_LEVEL_FLOOR = 0.012; // RMS below this reads as silence
// Auto gain: the jaw is fully open at the loudest recent level, so it uses its whole range
// whatever the TTS volume (a fixed 0.13 left it open on most frames of real speech).
export const JAW_PEAK_DECAY = 0.2; // 1/s, how fast the remembered peak level fades
export const JAW_PEAK_MIN = 0.05; // RMS; quiet noise never counts as a full-open peak
export const JAW_ATTACK = 32; // damp rates for opening and closing
export const JAW_RELEASE = 14;
// Fallback only (no analyser): two sines so it does not look like a metronome.
export const JAW_SYNTH_HZ_A = 5.5;
export const JAW_SYNTH_HZ_B = 3.1;

// Head emphasis while talking: nods follow the voice envelope.
export const EMPHASIS_NOD = 0.055;
export const EMPHASIS_SWAY = 0.022;

// Arms. The extra z values pull the arms in from the original A-pose.
export const ARM_POSE_Z = {
  pecl: -0.489, // -28 deg
  pecl001: 0.489, // 28 deg
  arml: -0.69, // -39.5 deg
  armr: 0.69, // 39.5 deg
};
export const ARM_SWAY = 0.016;
export const HAND_SWAY = 0.05;

// prefers-reduced-motion: ripple-type motion shrinks hard; static state poses shrink less so
// listening, thinking and speaking still read as different. The jaw is never reduced.
export const REDUCED_OSC = 0.2;
export const REDUCED_POSE = 0.5;
