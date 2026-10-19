// Tiny synthesised UI sounds for the child's Home (no audio files, nothing recorded or downloaded).
// Off until the child turns it on; the choice is remembered in localStorage. Everything is wrapped in
// try/catch so a blocked AudioContext or storage never breaks the page.
const KEY = 'child_sound_fx';
let ctx = null;

export function readSoundOn() {
  try {
    return localStorage.getItem(KEY) === '1';
  } catch {
    return false;
  }
}

export function writeSoundOn(on) {
  try {
    localStorage.setItem(KEY, on ? '1' : '0');
  } catch {
    /* storage blocked: the toggle still works for this visit */
  }
}

function audio() {
  if (ctx) return ctx;
  const AC = typeof window !== 'undefined' && (window.AudioContext || window.webkitAudioContext);
  if (!AC) return null;
  try {
    ctx = new AC();
  } catch {
    ctx = null;
  }
  return ctx;
}

function tone(c, freq, start, dur, gain = 0.07) {
  const o = c.createOscillator();
  const g = c.createGain();
  o.type = 'sine';
  o.frequency.setValueAtTime(freq, start);
  g.gain.setValueAtTime(0.0001, start);
  g.gain.exponentialRampToValueAtTime(gain, start + 0.015);
  g.gain.exponentialRampToValueAtTime(0.0001, start + dur);
  o.connect(g).connect(c.destination);
  o.start(start);
  o.stop(start + dur + 0.02);
}

const SOUNDS = {
  tap: [[660, 0, 0.09]],
  chime: [[784, 0, 0.14], [1046, 0.09, 0.2]],
  cheer: [[523, 0, 0.12], [659, 0.1, 0.12], [784, 0.2, 0.12], [1046, 0.3, 0.3]],
};

/** Play one of 'tap' | 'chime' | 'cheer' when the child has sound on; otherwise nothing. */
export function playFx(name) {
  if (!readSoundOn()) return;
  const c = audio();
  if (!c) return;
  try {
    if (c.state === 'suspended') c.resume();
    const t0 = c.currentTime + 0.01;
    for (const [f, at, d] of SOUNDS[name] || SOUNDS.tap) tone(c, f, t0 + at, d);
  } catch {
    /* ignore */
  }
}
