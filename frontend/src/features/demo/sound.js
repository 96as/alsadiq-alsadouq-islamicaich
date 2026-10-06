/**
 * Forest sounds, all made with WebAudio (no files, nothing to download): a soft day bed (a breeze and
 * the odd far bird) and a night bed (crickets and a low breeze), plus small UI sounds. No music, no
 * bells, no instruments. Fetched lazily by SoundPill; the AudioContext is created from a press.
 *
 * Rules: the bed fades in over 1.5 s at volume 0.25; sunset plays the day bed at 60% through a
 * lowpass; it pauses while the tab is hidden and resumes when it is visible; kill() ends it for good
 * (a voice session started).
 */
import { soundBus } from './soundBus';

const BED_VOL = 0.25;
const FADE = 1.5;

let ctx = null;
let master = null;
let day = null;
let night = null;
let tone = null; // lowpass: the warm, muffled sunset
let noise = null;
let period = 'noon';
let running = false;
let dead = false;
let chirpTimer = 0;

const rand = (a, b) => a + Math.random() * (b - a);

function noiseBuffer(c) {
  const len = Math.floor(c.sampleRate * 3);
  const buf = c.createBuffer(1, len, c.sampleRate);
  const d = buf.getChannelData(0);
  let b0 = 0;
  for (let i = 0; i < len; i += 1) {
    b0 = 0.97 * b0 + 0.03 * (Math.random() * 2 - 1);
    d[i] = b0 * 5;
  }
  return buf;
}

function breeze(c, out, vol, freq) {
  const src = c.createBufferSource();
  src.buffer = noise;
  src.loop = true;
  const lp = c.createBiquadFilter();
  lp.type = 'lowpass';
  lp.frequency.value = freq;
  const g = c.createGain();
  g.gain.value = vol;
  const lfo = c.createOscillator();
  lfo.frequency.value = 0.11;
  const depth = c.createGain();
  depth.gain.value = vol * 0.6;
  lfo.connect(depth).connect(g.gain);
  src.connect(lp).connect(g).connect(out);
  src.start();
  lfo.start();
}

function cricket(c, out, f0, rate) {
  const o = c.createOscillator();
  o.frequency.value = f0;
  const g = c.createGain();
  g.gain.value = 0;
  const lfo = c.createOscillator();
  lfo.type = 'square';
  lfo.frequency.value = rate;
  const d = c.createGain();
  d.gain.value = 0.012;
  const bias = c.createConstantSource();
  bias.offset.value = 0.012;
  lfo.connect(d).connect(g.gain);
  bias.connect(g.gain);
  o.connect(g).connect(out);
  o.start();
  lfo.start();
  bias.start();
}

function chirp(c, out, at) {
  const o = c.createOscillator();
  const g = c.createGain();
  const f = rand(2600, 4200);
  o.frequency.setValueAtTime(f, at);
  o.frequency.exponentialRampToValueAtTime(f * rand(0.8, 1.35), at + 0.09);
  g.gain.setValueAtTime(0.0001, at);
  g.gain.exponentialRampToValueAtTime(0.03, at + 0.015);
  g.gain.exponentialRampToValueAtTime(0.0001, at + 0.11);
  o.connect(g).connect(out);
  o.start(at);
  o.stop(at + 0.13);
}

function scheduleChirps() {
  window.clearTimeout(chirpTimer);
  if (!ctx || dead || !running) return;
  if (period !== 'night' && !document.hidden) {
    const n = 2 + Math.floor(Math.random() * 3);
    for (let i = 0; i < n; i += 1) chirp(ctx, day, ctx.currentTime + i * rand(0.12, 0.2));
  }
  chirpTimer = window.setTimeout(scheduleChirps, rand(2500, 6500));
}

function applyPeriod(instant) {
  if (!ctx) return;
  const t = ctx.currentTime;
  const isNight = period === 'night';
  const dayVol = period === 'maghrib' ? 0.6 : 1;
  const ramp = instant ? 0.01 : 1.2;
  [day.gain, night.gain, tone.frequency].forEach((p) => {
    p.cancelScheduledValues(t);
    p.setValueAtTime(p.value, t);
  });
  day.gain.linearRampToValueAtTime(isNight ? 0 : dayVol, t + ramp);
  night.gain.linearRampToValueAtTime(isNight ? 1 : 0, t + ramp);
  tone.frequency.linearRampToValueAtTime(period === 'maghrib' ? 2400 : 18000, t + ramp);
}

function build() {
  ctx = new (window.AudioContext || window.webkitAudioContext)();
  noise = noiseBuffer(ctx);
  master = ctx.createGain();
  master.gain.value = 0;
  tone = ctx.createBiquadFilter();
  tone.type = 'lowpass';
  tone.frequency.value = 18000;
  master.connect(tone).connect(ctx.destination);
  day = ctx.createGain();
  night = ctx.createGain();
  day.connect(master);
  night.connect(master);
  breeze(ctx, day, 0.05, 700);
  breeze(ctx, night, 0.03, 380);
  cricket(ctx, night, 4400, 13);
  cricket(ctx, night, 4900, 11);
  applyPeriod(true);
}

function fadeTo(v, secs) {
  const t = ctx.currentTime;
  master.gain.cancelScheduledValues(t);
  master.gain.setValueAtTime(master.gain.value, t);
  master.gain.linearRampToValueAtTime(v, t + secs);
}

/** Starts the bed (call it from a press). Resolves false if it cannot play. */
export async function start() {
  if (dead) return false;
  try {
    if (!ctx) build();
    if (ctx.state === 'suspended') await ctx.resume();
    running = true;
    fadeTo(BED_VOL, FADE);
    scheduleChirps();
    return true;
  } catch {
    return false;
  }
}

/** Fades the bed out and keeps the context for the next press. */
export function pause() {
  running = false;
  window.clearTimeout(chirpTimer);
  if (ctx) fadeTo(0, 0.4);
}

/** Ends everything for this page load (a voice session started). */
export function kill() {
  dead = true;
  running = false;
  window.clearTimeout(chirpTimer);
  if (!ctx) return;
  const c = ctx;
  ctx = null;
  try {
    const t = c.currentTime;
    master.gain.cancelScheduledValues(t);
    master.gain.setValueAtTime(master.gain.value, t);
    master.gain.linearRampToValueAtTime(0, t + 0.25);
  } catch {
    // already closing
  }
  window.setTimeout(() => c.close().catch(() => {}), 350);
}

export function setPeriod(name) {
  period = name;
  applyPeriod(false);
}

/** A soft UI sound. Quiet, short, and only while the sounds are on. */
function ui(name) {
  if (!ctx || dead || !running) return;
  const c = ctx;
  const t = c.currentTime;
  const out = c.createGain();
  out.gain.value = 0.5;
  out.connect(c.destination);
  const blip = (f0, f1, dur, vol, at = 0) => {
    const o = c.createOscillator();
    const g = c.createGain();
    o.frequency.setValueAtTime(f0, t + at);
    o.frequency.exponentialRampToValueAtTime(f1, t + at + dur);
    g.gain.setValueAtTime(0.0001, t + at);
    g.gain.exponentialRampToValueAtTime(vol, t + at + 0.012);
    g.gain.exponentialRampToValueAtTime(0.0001, t + at + dur);
    o.connect(g).connect(out);
    o.start(t + at);
    o.stop(t + at + dur + 0.02);
  };
  if (name === 'pop') blip(520, 760, 0.12, 0.12);
  else if (name === 'hop') blip(300, 620, 0.16, 0.14);
  else if (name === 'lantern') {
    blip(330, 495, 0.35, 0.07);
    blip(495, 660, 0.35, 0.05, 0.06);
  } else if (name === 'tweet') {
    blip(3000, 3900, 0.07, 0.09);
    blip(3400, 2800, 0.09, 0.08, 0.1);
  } else if (name === 'page') {
    const src = c.createBufferSource();
    src.buffer = noise;
    const bp = c.createBiquadFilter();
    bp.type = 'bandpass';
    bp.frequency.setValueAtTime(1800, t);
    bp.frequency.exponentialRampToValueAtTime(600, t + 0.22);
    const g = c.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(0.25, t + 0.03);
    g.gain.exponentialRampToValueAtTime(0.0001, t + 0.24);
    src.connect(bp).connect(g).connect(out);
    src.start(t);
    src.stop(t + 0.26);
  }
}

// Wire up the bus, and follow the tab: quiet while it is hidden, back when it is visible.
soundBus.play = ui;
soundBus.stop = kill;
soundBus.setTime = setPeriod;
document.addEventListener('visibilitychange', () => {
  if (!ctx || dead) return;
  if (document.hidden) ctx.suspend().catch(() => {});
  else if (running) ctx.resume().then(scheduleChirps).catch(() => {});
});
