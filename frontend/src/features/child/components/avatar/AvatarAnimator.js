// One AnimationMixer for the whole avatar, used as a blender and nothing more.
//
// Layers, in the order they are mixed:
//   1. body loops (Idle, Listen*, Think, SearchHold, Talk*, Walk): exactly one is the base, the others
//      fade to 0. Their weights always add up to 1, so the bind pose (a T-pose) never shows through.
//      The base can be shown only partly against Idle (the talk energy underlay, setUnderlay).
//   2. one-shots and transitions (Wave, Happy, LookAround, Greet, Goodbye, Celebrate, SearchStart,
//      SearchSwipe, Found): fade over the base, play once, fade out. Every one of them ends on the first
//      frame of its home loop (the clip's `to` or `home`), so just before it fades out the base loops
//      are put back to their first frame and the hand-back is seamless. Two can overlap: one that was
//      cut fades out under the one that replaced it.
//   2b. walk transition (Walk_Start, Walk_Stop_R, Walk_Stop_L): a clip the walk-in timeline places
//      frame by frame (`setTransitionTime`). Start blends in over the Idle base; a stop cuts in on a
//      contact; both end exactly on the first frame of the next loop (Walk f0 or Idle f0), where the
//      loop takes over without a fade (`endTransition`).
//   3. additive clips (Nod, later Beat_*): made additive against their first frame, two slots per
//      clip so a double nod overlaps itself smoothly, played on top of everything.
//   4. Blink: its own layer. It keys only the two eyelid bones, so it never fights the body.
// The jaw, the visemes, the expression and the look-at are not here: code owns those (ClipAvatar.jsx).
//
// Action clocks are driven by hand (every action is paused and gets `action.time` each frame), so a
// loop's speed can change smoothly (the walk follows the ground speed) and nothing depends on
// mixer events. Nothing is allocated per frame.
//
// 06-avatar-context: the clip set, markers and hand-back rules come from CLIP_META (avatarConfig.js).

import { AdditiveAnimationBlendMode, AnimationMixer, AnimationUtils } from 'three';
import { ANIM, CLIP, CLIP_META } from './avatarConfig.js';

const smooth = (x) => {
  const c = x < 0 ? 0 : x > 1 ? 1 : x;
  return c * c * (3 - 2 * c);
};
const between = (range, rng) => range[0] + rng() * (range[1] - range[0]);
const UNDERLAY_RATE = 8; // how fast the shown base share follows setUnderlay (per second)
const ADDITIVE_SLOTS = 2;
const TRANSITION_CLIPS = [CLIP.walkStart, CLIP.walkStopR, CLIP.walkStopL];

class Layer {
  constructor(action, duration, name) {
    this.action = action;
    this.name = name;
    this.e = 0; // eased weight, set each frame
    this.duration = duration;
    this.time = 0;
    this.w = 0; // raw fade 0..1
    this.target = 0;
    this.scale = 1; // playback speed
    this.hold = false; // the clock was placed by hand for the next update
  }
}

/** One one-shot in flight. Two of these exist; they are reused. */
class ShotState {
  constructor() {
    this.layer = null;
    this.name = '';
    this.meta = null;
    this.phase = 0; // 0 in | 1 play | 2 out
    this.a = 0;
    this.elapsed = 0;
    this.fadeIn = ANIM.fadeOneShot;
    this.fadeOut = ANIM.fadeOneShot;
    this.maxWeight = 1;
    this.blinkAt = -1;
    this.rewind = true; // hand the base back to frame 0 when the clip ends
    this.shown = 0; // the weight this frame
  }
}

export class AvatarAnimator {
  /**
   * @param {object} root the cloned scene the clips animate
   * @param {Array} clips THREE.AnimationClip list from the GLB
   * @param {{rng?: () => number}} [opts]
   */
  constructor(root, clips, { rng = Math.random } = {}) {
    this.rng = rng;
    this.mixer = new AnimationMixer(root);
    this.loops = new Map(); // body loops by clip name
    this.shots = new Map(); // one-shots and transitions by clip name
    this.additives = new Map(); // additive clips by name: an array of ADDITIVE_SLOTS slots
    this.trans = new Map(); // walk transitions by clip name (studio GLB only)
    this.blinkLayer = null;
    this.onMarker = null; // optional (clipName, markerName) hook, fired as a shot's clock crosses a marker

    for (const clip of clips) {
      const isTrans = TRANSITION_CLIPS.includes(clip.name);
      const kind = isTrans ? 'walktransition' : (CLIP_META[clip.name]?.kind ?? 'loop');
      if (kind === 'additive') {
        this.addAdditive(clip);
        continue;
      }
      const action = this.mixer.clipAction(clip);
      action.paused = true; // the clock is driven by hand
      action.weight = 0;
      action.play();
      const layer = new Layer(action, clip.duration, clip.name);
      if (clip.name === CLIP.blink) this.blinkLayer = layer;
      else if (isTrans) this.trans.set(clip.name, layer);
      else if (kind === 'oneshot' || kind === 'transition') this.shots.set(clip.name, layer);
      else this.loops.set(clip.name, layer);
    }
    this.loopList = [...this.loops.values()]; // arrays for allocation-free iteration
    this.additiveList = [...this.additives.values()].flat();

    this.base = this.loops.has(CLIP.idle) ? CLIP.idle : [...this.loops.keys()][0];
    this.baseLayer = this.loops.get(this.base) ?? null;
    this.idleLayer = this.loops.get(CLIP.idle) ?? null;
    this.reduced = false;
    this.fade = ANIM.fade;
    this.underlay = 1; // shown share of the base (the rest is Idle), eased toward underlayTarget
    this.underlayTarget = 1;
    this.setTargets();
    if (this.baseLayer) this.baseLayer.w = 1;

    this.slots = [new ShotState(), new ShotState()];
    this.blinkT = -1; // seconds into the Blink clip, -1 when idle
    // The active walk transition: { layer, name, a: blend 0..1, blendIn: seconds, time: clip seconds }
    this.tr = { layer: null, name: '', a: 0, blendIn: 0, time: 0 };
    this.glanceTimer = between(ANIM.lookAroundFirst, rng);
    this.glanceEnabled = true; // idle glances (LookAround every 12 to 20 s) while the base is Idle
    this.walkScale = 1;
    this.onBlinkStart = null; // optional hook, e.g. to hold the lip-sync scheduler off for a moment
  }

  addAdditive(clip) {
    const slots = [];
    for (let i = 0; i < ADDITIVE_SLOTS; i++) {
      const c = clip.clone(); // its own clip per slot: an action is cached per clip and root
      c.name = `${clip.name}#${i}`;
      AnimationUtils.makeClipAdditive(c, 0);
      const action = this.mixer.clipAction(c);
      action.blendMode = AdditiveAnimationBlendMode;
      action.paused = true;
      action.weight = 0;
      action.play();
      slots.push({ action, duration: c.duration, time: 0, w: 0, scale: 1, active: false });
    }
    this.additives.set(clip.name, slots);
  }

  has(name) {
    return (
      this.loops.has(name) || this.shots.has(name) || this.additives.has(name) || this.trans.has(name) || this.blinkLayer?.name === name
    );
  }

  /** The GLB carries Walk_Start and both stops (the studio walk-in can play). */
  get hasStudioWalk() {
    return this.trans.has(CLIP.walkStart) && this.trans.has(CLIP.walkStopR) && this.trans.has(CLIP.walkStopL) && this.loops.has(CLIP.walk);
  }

  /** Name of the walk transition that is playing, or ''. */
  get transitionName() {
    return this.tr.layer ? this.tr.name : '';
  }

  /** Clip seconds the active transition is at (-1 when none plays). */
  get transitionTime() {
    return this.tr.layer ? this.tr.time : -1;
  }

  /** Clip time a loop is at (the walk-in measures the stop's phase from this). */
  loopTime(name) {
    const l = this.loops.get(name);
    return l ? l.time : -1;
  }

  /** Start a walk transition over the base. `blendIn` 0 cuts in at once (a stop starts on a contact). */
  startTransition(name, { blendIn = 0 } = {}) {
    const layer = this.trans.get(name);
    if (!layer) return false;
    this.cancelTransition();
    const t = this.tr;
    t.layer = layer;
    t.name = name;
    t.blendIn = blendIn;
    t.a = blendIn > 0 ? 0 : 1;
    t.time = 0;
    layer.action.time = 0;
    return true;
  }

  /** Place the transition at `time` clip seconds (the walk-in's clock; nothing is advanced by hand). */
  setTransitionTime(time) {
    if (this.tr.layer) this.tr.time = Math.min(Math.max(time, 0), this.tr.layer.duration);
  }

  /** Drop the transition now (reduced motion, a replay). The base loop keeps whatever it had. */
  cancelTransition() {
    const t = this.tr;
    if (t.layer) t.layer.action.weight = 0;
    t.layer = null;
    t.a = 0;
  }

  /**
   * The transition is over: it is on the first frame of `name`, so `name` takes over at once, at
   * `time` clip seconds, with every other loop at 0 (no crossfade, the poses are equal).
   */
  endTransition(name, time = 0) {
    this.cancelTransition();
    this.snapBase(name, time);
  }

  /** Make `name` the base now: weight 1 at `time`, every other loop 0 (no fade). */
  snapBase(name, time = 0) {
    const l = this.loops.get(name);
    if (!l) return false;
    for (const o of this.loopList) {
      o.w = o === l ? 1 : 0;
      o.target = o.w;
    }
    this.base = name;
    this.baseLayer = l;
    this.setTargets();
    l.time = time % l.duration;
    l.hold = true;
    return true;
  }

  /** Put a loop at `time` clip seconds for the next update (the walk-in drives the Walk clock). */
  setLoopTime(name, time) {
    const l = this.loops.get(name);
    if (!l) return;
    l.time = time % l.duration;
    l.hold = true;
  }

  /** Name of the loop that is the base right now. */
  get baseName() {
    return this.base;
  }

  /** The newest one-shot that is playing (not fading out because it was cut), or ''. */
  get shotName() {
    const s = this.slots;
    for (let i = s.length - 1; i >= 0; i--) if (s[i].layer && s[i].phase < 2) return s[i].name;
    for (let i = 0; i < s.length; i++) if (s[i].layer) return s[i].name;
    return '';
  }

  /** 0..1, how far the one-shots cover the base (0 when none plays). */
  get shotAmount() {
    let a = 0;
    for (let i = 0; i < this.slots.length; i++) if (this.slots[i].layer) a += this.slots[i].shown;
    return a > 1 ? 1 : a;
  }

  /** True while a one-shot that has not been cut is playing (or fading in or out normally). */
  get shotBusy() {
    for (let i = 0; i < this.slots.length; i++) if (this.slots[i].layer) return true;
    return false;
  }

  setReduced(reduced) {
    if (reduced === this.reduced) return;
    this.reduced = reduced;
    this.setTargets();
  }

  /**
   * Make `name` the base loop; the old one crossfades out.
   * `entry` (seconds, optional): where the new loop's clock starts. `scale`: its playback speed
   * (a small random jitter, so no loop repeats in lockstep). Both apply only on a real change, and
   * the Walk is never jittered (the walk-in sets its speed).
   */
  setBase(name, fade = ANIM.fade, entry = -1, scale = 1) {
    const layer = this.loops.get(name);
    if (!layer) return false;
    this.fade = fade;
    if (name === this.base) return true;
    this.base = name;
    this.baseLayer = layer;
    if (entry >= 0 && name !== CLIP.walk) {
      layer.time = entry % layer.duration;
      layer.action.time = layer.time;
    }
    if (name !== CLIP.walk) layer.scale = scale;
    this.setTargets();
    return true;
  }

  /** How much of the base shows against Idle (1 = all). Ignored in reduced motion. */
  setUnderlay(amount) {
    this.underlayTarget = amount < 0 ? 0 : amount > 1 ? 1 : amount;
  }

  /** The weight a loop was mixed with on the last update (0 when it is not in the GLB). */
  weightOf(name) {
    const l = this.loops.get(name);
    return l ? l.action.weight : 0;
  }

  /** Playback speed of one loop (the walk uses this to follow the ground speed). */
  setLoopScale(name, scale) {
    const l = this.loops.get(name);
    if (l) l.scale = scale;
  }

  setTargets() {
    const reduced = this.reduced && this.base !== CLIP.walk;
    const idle = this.loops.get(CLIP.idle);
    for (const [name, l] of this.loops) {
      if (name === this.base) l.target = reduced && idle && name !== CLIP.idle ? ANIM.reducedIdleWeight : 1;
      else l.target = reduced && idle && name === CLIP.idle ? 1 - ANIM.reducedIdleWeight : 0;
    }
  }

  /**
   * Play a one-shot over the base. Returns false if one is already playing (cut it first with
   * interrupt), the clip is missing, or reduced motion is on and it is not forced.
   * A transition (SearchStart, Found) also makes its `to` loop the base if it is not already.
   */
  playOnce(name, { force = false, maxWeight = 1, fadeIn = 0, switchBase = true } = {}) {
    const layer = this.shots.get(name);
    if (!layer) return false;
    if (this.reduced && !force) return false;
    const slots = this.slots;
    let free = null;
    for (let i = 0; i < slots.length; i++) {
      const s = slots[i];
      if (s.layer && s.phase < 2) return false;
      if (s.layer && s.layer === layer) {
        s.layer.action.weight = 0; // the same clip is still fading out: it ends now
        s.layer = null;
        s.a = 0;
      }
    }
    for (let i = 0; i < slots.length; i++) if (!slots[i].layer) free = slots[i];
    if (!free) {
      // Both are busy fading out: drop the one that is further along.
      free = slots[0].a <= slots[1].a ? slots[0] : slots[1];
      free.layer.action.weight = 0;
    }
    const meta = CLIP_META[name] ?? null;
    free.layer = layer;
    free.name = name;
    free.meta = meta;
    free.phase = 0;
    free.a = 0;
    free.elapsed = 0;
    free.shown = 0;
    free.maxWeight = maxWeight;
    free.fadeIn = fadeIn > 0 ? fadeIn : (meta?.fadeIn ?? ANIM.fadeOneShot);
    free.fadeOut = meta?.fadeOut ?? ANIM.fadeOneShot;
    free.blinkAt = name === CLIP.lookAround ? ANIM.lookAroundBlinkAt : -1;
    free.rewind = true;
    layer.time = 0;
    if (switchBase && meta?.kind === 'transition' && meta.to && this.base !== meta.to && this.loops.has(meta.to)) {
      this.setBase(meta.to, free.fadeIn);
    }
    return true;
  }

  /** Cut the one-shots that are playing: they fade out over `fade` seconds and do not hand back. */
  interrupt(fade = 0.25) {
    for (let i = 0; i < this.slots.length; i++) {
      const s = this.slots[i];
      if (!s.layer || s.phase >= 2) continue;
      s.phase = 2;
      s.fadeOut = fade;
      s.rewind = false;
    }
  }

  /**
   * Play an additive clip (Nod, Beat_*) on top of everything. `weight` scales it, `timeScale` is its
   * speed. Two can overlap (a double nod). Returns false if the GLB has no such clip.
   */
  playAdditive(name, weight = 1, timeScale = 1) {
    const slots = this.additives.get(name);
    if (!slots) return false;
    let pick = slots[0];
    for (let i = 0; i < slots.length; i++) {
      if (!slots[i].active) {
        pick = slots[i];
        break;
      }
      if (slots[i].time > pick.time) pick = slots[i];
    }
    pick.active = true;
    pick.time = 0;
    pick.w = weight;
    pick.scale = timeScale;
    return true;
  }

  /** Start one Blink (restarts a blink in progress). Returns false if the GLB has no Blink clip. */
  blink() {
    if (!this.blinkLayer) return false;
    this.blinkT = 0;
    if (this.onBlinkStart) this.onBlinkStart();
    return true;
  }

  fireMarkers(s, before, after) {
    const hook = this.onMarker;
    const markers = s.meta?.markers;
    if (!hook || !markers) return;
    for (const key in markers) {
      const at = markers[key];
      if (before < at && at <= after) hook(s.name, key);
    }
  }

  /**
   * @param {number} dt seconds
   */
  update(dt) {
    const reducedScale = this.reduced ? ANIM.reducedIdleScale : 1;
    const step = this.fade > 0 ? dt / this.fade : 1;

    // 1. body loops: advance clocks and fades
    let sum = 0;
    const loops = this.loopList;
    for (let i = 0; i < loops.length; i++) {
      const l = loops[i];
      if (l.w < l.target) l.w = Math.min(l.target, l.w + step);
      else if (l.w > l.target) l.w = Math.max(l.target, l.w - step);
      const walking = l.name === CLIP.walk;
      if (l.hold) l.hold = false; // the walk-in placed this loop's clock itself
      else l.time = (l.time + dt * l.scale * (walking ? 1 : reducedScale)) % l.duration;
      l.action.time = l.time;
      l.e = smooth(l.w);
      sum += l.e;
    }

    // 2. one-shots
    const slots = this.slots;
    let total = 0;
    for (let k = 0; k < slots.length; k++) {
      const s = slots[k];
      s.shown = 0;
      if (!s.layer) continue;
      const L = s.layer;
      if (s.phase === 0) {
        s.a = Math.min(1, s.a + dt / s.fadeIn);
        if (s.a >= 1) s.phase = 1;
      }
      if (s.phase < 2) {
        const before = s.elapsed;
        s.elapsed += dt;
        const t = Math.min(s.elapsed, L.duration);
        L.action.time = t;
        this.fireMarkers(s, before, t);
        if (s.blinkAt >= 0 && s.elapsed >= s.blinkAt) {
          s.blinkAt = -1;
          this.blink();
        }
        if (s.elapsed >= L.duration) {
          // The clip is on its last frame (its home loop's first frame). Rewind the base under it,
          // but only when that loop is what the base is now.
          const home = s.meta ? (s.meta.to ?? s.meta.home ?? CLIP.idle) : CLIP.idle;
          if (s.rewind && this.base === home) {
            for (let i = 0; i < loops.length; i++) {
              loops[i].time = 0;
              loops[i].action.time = 0;
            }
          }
          s.phase = 2;
        }
      } else {
        s.a = Math.max(0, s.a - dt / s.fadeOut);
        if (s.rewind) L.action.time = L.duration;
        if (s.a <= 0) {
          L.action.weight = 0;
          s.layer = null;
          continue;
        }
      }
      s.shown = smooth(s.a) * s.maxWeight;
      total += s.shown;
    }
    // Two shots overlapping (one cut, one new) may not weigh more than 1 together.
    const norm = total > 1 ? 1 / total : 1;
    for (let k = 0; k < slots.length; k++) {
      const s = slots[k];
      if (!s.layer) continue;
      s.shown *= norm;
      s.layer.action.weight = s.shown;
    }
    // 2b. walk transition
    const tr = this.tr;
    let at = 0;
    if (tr.layer) {
      if (tr.a < 1) tr.a = tr.blendIn > 0 ? Math.min(1, tr.a + dt / tr.blendIn) : 1;
      at = smooth(tr.a);
      tr.layer.action.time = tr.time;
      tr.layer.action.weight = at;
    }
    const room = (1 - (total > 1 ? 1 : total)) * (1 - at);

    // 3. weights: the base loops share what the one-shots and the transition leave
    for (let i = 0; i < loops.length; i++) {
      const l = loops[i];
      l.action.weight = sum > 0 ? (l.e / sum) * room : 0;
    }
    // The underlay: only part of the base shows, the rest is Idle (talk loops follow the voice).
    const idleL = this.idleLayer;
    const baseL = this.baseLayer;
    if (this.reduced) this.underlay = 1;
    else this.underlay += (this.underlayTarget - this.underlay) * Math.min(1, UNDERLAY_RATE * dt);
    if (idleL && baseL && baseL !== idleL && this.underlay < 0.999 && !this.reduced) {
      const moved = baseL.action.weight * (1 - this.underlay);
      baseL.action.weight -= moved;
      idleL.action.weight += moved;
    }

    // 4. additive clips (nods)
    const adds = this.additiveList;
    for (let i = 0; i < adds.length; i++) {
      const a = adds[i];
      if (!a.active) {
        a.action.weight = 0;
        continue;
      }
      a.time += dt * a.scale;
      if (a.time >= a.duration) {
        a.active = false;
        a.action.weight = 0;
        continue;
      }
      a.action.time = a.time;
      a.action.weight = a.w;
    }

    // 5. blink layer
    const b = this.blinkLayer;
    if (b) {
      if (this.blinkT >= 0) {
        this.blinkT += dt * ANIM.blinkTimeScale;
        if (this.blinkT >= b.duration) {
          this.blinkT = -1;
          b.action.weight = 0;
        } else {
          b.action.time = this.blinkT;
          b.action.weight = 1;
        }
      } else b.action.weight = 0;
    }

    // 6. idle glances: only while idling, never in reduced motion (the director owns them when it runs)
    if (this.glanceEnabled && !this.reduced && this.base === CLIP.idle && !this.shotBusy && !tr.layer) {
      this.glanceTimer -= dt;
      if (this.glanceTimer <= 0) {
        this.glanceTimer = between(ANIM.lookAroundEvery, this.rng);
        this.playOnce(CLIP.lookAround);
      }
    }

    this.mixer.update(dt);
  }

  dispose() {
    this.mixer.stopAllAction();
    const root = this.mixer.getRoot();
    this.mixer.uncacheRoot(root);
  }
}
