/* The frame loop mutates the model, the animator and the shared walk state by design. */
import { useEffect, useMemo, useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { MathUtils, Quaternion, Vector3 } from 'three';
import * as SkeletonUtils from 'three/examples/jsm/utils/SkeletonUtils.js';
import { AvatarAnimator } from './AvatarAnimator.js';
import { ANIM, CLIP, DIRECTOR, JAW, LOOK, MESH_VISEME_GAIN, MODEL_SCALE, SEARCH_SCROLL_W, STATE_CLIP, WALK_CLIP, WALK_CLIP_LEGACY } from './avatarConfig.js';
import { LookAt } from './lookAt.js';
import { LipsyncRig } from './lipsync/lipsyncRig.js';
import { VI, VISEMES, VISEME_COUNT } from './lipsync/visemes.js';
// 06-avatar-context: the director, the head and eyelid layers, and the search hologram.
import { createDirector, makeDirectorOutput } from './context/avatarDirector.js';
import { ExpressionLayer } from './context/expressionLayer.js';
import { HeadLayer } from './context/headLayer.js';
import { createProceduralNod } from './context/proceduralNod.js';
import { HOLO, isLowTier } from './hologram/hologramConfig.js';
import { HP } from './context/holoTimeline.js'; // hotfix-2
import { ConversationShot } from './conversationShot.js'; // hotfix-2
import { computeFraming } from '../meadowFraming.js'; // hotfix-2
import { lookdevShotFraming } from './lookdev/shotFraming.js'; // step 2: the shot on top of look-dev's stage camera
import { HologramRig } from './hologram/HologramRig.js';
import { ActingRig } from './acting/actingRig.js'; // WP4
import { buildPageModel } from './hologram/webPage/contentFilter.js'; // w3
import {
  JAW_LEVEL_FLOOR,
  JAW_PEAK_DECAY,
  JAW_PEAK_MIN,
  JAW_SYNTH_HZ_A,
  JAW_SYNTH_HZ_B,
} from './motionConfig';
import { STATE, WALK, pinWalkDistance, stepWalk } from './walkIn';
import { LEG } from './studioWalk.js';
import { placeStage, stepStage } from './meadowStage.js'; // avatar-integ: the meadow stage (Home walk, one camera move)
import { useReducedMotion } from './useAvatarMotion';

const { clamp } = MathUtils;
const MAX_DT = 0.1; // a stalled tab must not make the avatar snap
const BACKDROP_MATERIAL_NAME = 'BackdropMat';

// The jaw bone's local axis it opens about. Checked in the dev preview (see the README).
const JAW_AXIS = new Vector3(1, 0, 0);
// The walk-in turn (head lead, chest and neck carrying the turn at the stop) turns the bones about
// their own long axis (local Y), like the look-at does.
const TURN_AXIS = new Vector3(0, 1, 0);
const boneTurn = new Quaternion();
// How the turn at the stop is shared (Bible 3.3: chest and neck), and how much of the head lead is the head alone.
const TWIST_SHARE = { chest: 0.3, neck: 0.3, head: 0.4 };
const LEAD_SHARE = { neck: 0.3, head: 0.7 };

/** Nodes by name. GLTFLoader strips dots from node names, so look both spellings up. */
function findBones(scene) {
  const byName = new Map();
  scene.traverse((obj) => {
    if (obj.name) byName.set(obj.name, obj);
  });
  const get = (n) => byName.get(n) || byName.get(n.replaceAll('.', '')) || null;
  const jaw = get('jaw');
  return {
    head: get('head'),
    neck: get('neck'),
    chest: get('chest'),
    jaw,
    jawRest: jaw ? jaw.quaternion.clone() : null,
    chestBase: get('chest') ? get('chest').quaternion.clone() : null, // what the mixer left, before the walk-in turn
  };
}

/**
 * Where the child is looking, so the avatar can look back: the pointer on desktop (after it has
 * moved), the camera otherwise. Plain numbers in a ref, so no React render per move.
 */
function usePointerGaze() {
  const gaze = useRef({ x: 0, y: 0, last: -1e9 });
  useEffect(() => {
    const onMove = (e) => {
      if (e.pointerType === 'touch') return;
      const g = gaze.current;
      g.x = (e.clientX / window.innerWidth) * 2 - 1;
      g.y = -((e.clientY / window.innerHeight) * 2 - 1);
      g.last = performance.now() / 1000;
    };
    window.addEventListener('pointermove', onMove, { passive: true });
    return () => window.removeEventListener('pointermove', onMove);
  }, []);
  return gaze;
}

/**
 * The avatar driven by the clips of avatar-animated.glb:
 *   state loops (Idle, Listen, Think, TalkGesture) crossfaded by the agent state; Idle glances
 *   (LookAround) every 12 to 20 s; the Walk clip and the Wave for the forest walk-in; the Blink
 *   clip on its own layer, timed by the lip-sync blink scheduler; viseme morphs from the agent's
 *   voice; a subtle jaw that agrees with them; a look-at on top.
 * Order each frame: clips, then lip-sync and jaw, then look-at, so code always has the last word.
 */
export default function ClipAvatar({
  gltf,
  state,
  getAudioLevel,
  walk,
  getLipsync,
  morphNames,
  avatarX,
  controlRef,
  // 06-avatar-context: the session's signals (a stable getter, see context/avatarSignals.js), the
  // language (Arabic mirrors the hologram), a tier override for the dev pages and the status caption.
  getAvatarContext,
  lang,
  lowTier: lowTierProp,
  onStatus,
  shot: shotProp = false, // hotfix-2: ease in to the conversation shot while speaking or listening (the meadow page)
  lookdevShot = false, // step 2: the meadow page runs the look-dev rig, so the shot's full-body end is its stage camera
  stage = null, // avatar-integ: the meadow stage (meadowStage.js): it places Sadiq on the path and owns the camera
}) {
  const scene = useMemo(() => {
    const clone = SkeletonUtils.clone(gltf.scene);
    clone.traverse((obj) => {
      if (!obj.isMesh) return;
      obj.frustumCulled = false; // skinned and morphed: the bounds do not follow the pose
      const materials = Array.isArray(obj.material) ? obj.material : [obj.material];
      if (materials.some((m) => m?.name === BACKDROP_MATERIAL_NAME)) obj.visible = false;
    });
    return clone;
  }, [gltf]);

  // The studio GLB carries Walk_Start and both stops; the older one walks with the ramp gait.
  const studio = useMemo(() => {
    const names = new Set(gltf.animations.map((c) => c.name));
    return names.has(CLIP.walkStart) && names.has(CLIP.walkStopR) && names.has(CLIP.walkStopL);
  }, [gltf]);
  const walkParams = studio ? STUDIO_PARAMS : LEGACY_PARAMS;

  const animator = useMemo(() => {
    const a = new AvatarAnimator(scene, gltf.animations);
    a.update(0); // pose the bones before the first render: the bind pose is a T-pose
    return a;
  }, [scene, gltf]);
  const bones = useMemo(() => findBones(scene), [scene]);
  const lookAt = useMemo(() => new LookAt(bones), [bones]);
  // The R2 mesh (the one with the prop_L socket) has the gain of five visemes baked in: divide it out.
  const lipRig = useMemo(
    () => new LipsyncRig(scene, { morphNames, meshGain: scene.getObjectByName(HOLO.socketBone) ? MESH_VISEME_GAIN : undefined }),
    [scene, morphNames],
  );
  const acting = useMemo(() => new ActingRig({ scene, bones, lipRig }), [scene, bones, lipRig]); // WP4

  // 06-avatar-context
  const headLayer = useMemo(() => new HeadLayer(bones.head), [bones]);
  const exprLayer = useMemo(() => new ExpressionLayer(scene, gltf.animations), [scene, gltf]);
  const proceduralNod = useMemo(() => createProceduralNod(DIRECTOR.proceduralNod), []);
  const director = useMemo(() => {
    animator.glanceEnabled = false; // the director schedules LookAround itself
    return createDirector({ has: (n) => animator.has(n) });
  }, [animator]);
  const dirOut = useMemo(() => makeDirectorOutput(), []);
  const tier = useMemo(() => resolveTier(lowTierProp), [lowTierProp]);
  const rig = useMemo(() => new HologramRig(scene, { lowTier: tier }), [scene, tier]);
  // hotfix-2: the conversation shot (camera easing and the measured face-size floor, conversationShot.js).
  const shotRig = useMemo(() => (shotProp && bones.head ? new ConversationShot(scene, bones.head) : null), [shotProp, scene, bones]);
  useEffect(
    () => () => {
      try {
        document.documentElement.style.removeProperty('--sadiq-shot');
      } catch {
        /* no document */
      }
    },
    [],
  );
  const gl = useThree((s) => s.gl);
  const glScene = useThree((s) => s.scene);
  const glCamera = useThree((s) => s.camera);
  useEffect(() => {
    let live = true;
    rig.warmUp(gl, glScene, glCamera).then(() => {
      if (!live) rig.root.visible = false;
    });
    return () => {
      live = false;
      rig.dispose();
    };
  }, [rig, gl, glScene, glCamera]);
  const contextFnRef = useRef(getAvatarContext);
  const statusFnRef = useRef(onStatus);
  const langRef = useRef(lang);
  useEffect(() => {
    contextFnRef.current = getAvatarContext;
    statusFnRef.current = onStatus;
    langRef.current = lang;
  }, [getAvatarContext, onStatus, lang]);

  const reducedRef = useReducedMotion();
  const gaze = usePointerGaze();
  const stateRef = useRef(state);
  const levelFnRef = useRef(getAudioLevel);
  const lipsyncFnRef = useRef(getLipsync);
  const groupRef = useRef(null);
  const outerRef = useRef(null); // avatar-integ: the stage moves this group along the path
  useEffect(() => {
    stateRef.current = state;
    levelFnRef.current = getAudioLevel;
    lipsyncFnRef.current = getLipsync;
  }, [state, getAudioLevel, getLipsync]);

  // Per-frame working values, mutated in place.
  const m = useRef({
    jaw: 0,
    levelPeak: 0,
    lastBlinks: 0,
    lastWalkState: -1,
    appliedBase: '',
    override: null, // dev: hold this loop whatever the agent state is
    lookOverride: null, // dev: { x, y } to look at
    jawDebug: -1, // dev: force the jaw to this opening (0..1), -1 = off
    walkWasPlaying: false,
    walkStopping: false,
    lastLeg: -1,
    twistApplied: false,
    lipCtx: { lipsync: null, open: 0, speaking: false, reduced: false }, // reused, no per-frame object
    // 06-avatar-context
    dirIn: {
      agentState: 'idle', signals: null, cues: null, childSpeaking: false, voiceLevel: -1, gam: null,
      sessionEndingSeq: 0, connectSeq: 0, awaySec: 0, walkIn: false, reduced: false, visible: true, waveAgo: 999,
    },
    holoCtx: { camera: null, hasHold: false, reduced: false, viewW: 1, viewH: 1, pxPerUnit: 600, web: null, jaw: null }, // w3: web, jaw
    webRev: -1, // w3: the al.search revision the page model was built from
    webModel: null,
    waveAt: -999,
    afterWalk: false,
    rtl: null,
    statusSeq: 0,
    gl: null,
    perf: { n: 0, sum: 0, max: 0 }, // dev only: JS ms per frame spent in the director, layers and hologram
  }).current;

  // Wire the blink scheduler to the animator: a LookAround blink also holds the scheduler off.
  useEffect(() => {
    animator.onBlinkStart = () => {
      const b = lipRig.blinker;
      b.sinceBlink = 0;
      if (b.timer < 1.2) b.timer = 1.2;
    };
    return () => {
      animator.onBlinkStart = null;
    };
  }, [animator, lipRig]);

  // Dev and preview handle.
  useEffect(() => {
    if (!controlRef) return undefined;
    const control = {
      mode: 'clips',
      animator,
      lookAt,
      lipRig,
      acting, // WP4
      clips: gltf.animations.map((c) => c.name),
      play: (name) => (name === CLIP.blink ? animator.blink() : animator.playOnce(name, { force: true })),
      hold: (name) => {
        m.override = name || null;
      },
      look: (x, y) => {
        m.lookOverride = x == null ? null : { x, y };
      },
      jaw: (v) => {
        m.jawDebug = v;
      },
      jawAxis: JAW_AXIS,
      // Dev measurement: turn the idle LookAround glances off, so the B4 head-motion share of the
      // procedural layer can be read without the glance clip in it.
      glances: (on) => {
        animator.glanceEnabled = Boolean(on);
      },
      // WP4: the dev measurement hook (chin vertex, jaw, closures, head angles). Loaded on demand.
      metrics: async () => {
        if (!control.metricsObj) {
          const { MouthMetrics } = await import('./acting/mouthMetrics.js');
          control.metricsObj = new MouthMetrics(scene, acting, lipRig);
          acting.onFrame = () => control.metricsObj.sample();
        }
        return control.metricsObj;
      },
      bones,
      shot: shotRig, // hotfix-2: .metrics() = the measured face, .exactFace(camera, h) = from the real vertices
      faceExact: () => (shotRig && shotRig.enabled ? shotRig.exactFace(glCamera, gl.domElement.clientHeight) : null), // hotfix-2: from the real skinned vertices, stage px
      camera: glCamera, // hotfix-2: for the tests
      // 06-avatar-context
      director,
      dirOut,
      rig,
      exprLayer,
      nod: (w = 1) => (animator.has(CLIP.nod) ? animator.playAdditive(CLIP.nod, w, 1) : proceduralNod.fire(w, 1)),
      perfReset: () => {
        m.perf.n = 0;
        m.perf.sum = 0;
        m.perf.max = 0;
      },
      get info() {
        return {
          base: animator.baseName,
          shot: animator.shotName,
          logical: dirOut.logicalBase,
          talkStyle: dirOut.talkStyle,
          holoPhase: dirOut.holo ? dirOut.holo.phase : 0,
          lookPanel: dirOut.lookPanel,
          squint: dirOut.squint,
          jaw: m.jaw,
          walkState: walk ? walk.state : -1,
          tier: tier ? 'low' : 'high',
          drawCalls: m.gl ? m.gl.info.render.calls : -1,
          triangles: m.gl ? m.gl.info.render.triangles : -1,
          directorMs: m.perf.n ? m.perf.sum / m.perf.n : 0,
          directorMaxMs: m.perf.max,
          frames: m.perf.n,
          studio,
          transition: animator.transitionName,
        };
      },
    };
    controlRef.current = control;
    return () => {
      acting.onFrame = null;
      controlRef.current = null;
    };
  }, [controlRef, animator, lookAt, lipRig, acting, gltf, bones, m, walk, scene, director, dirOut, rig, exprLayer, proceduralNod, tier, shotRig, gl, glCamera, studio]);

  // The walk-in's distance is this gait's, unless a preview pinned it.
  useEffect(() => {
    pinWalkDistance(walk, WALK_CLIP.distance);
  }, [walk]);

  // avatar-integ: the meadow stage's camera and idle beats run first (priority -2), so the camera and the avatar read the same pose.
  useFrame((frame, delta) => {
    if (stage) {
      stage.reduced = reducedRef.current;
      stepStage(stage, Math.min(delta, MAX_DT), frame.size.width, frame.size.height);
    }
  }, -2);

  useFrame((frame, delta) => {
    const dt = Math.min(delta, MAX_DT);
    const t = frame.clock.elapsedTime;
    const reduced = reducedRef.current;
    animator.setReduced(reduced);

    // ---- which body clip is the base ----
    const motionState = stateRef.current;
    const walking = walk && walk.state !== STATE.DONE;
    const perfOn = !!controlRef;
    const p0 = perfOn ? performance.now() : 0;
    if (walking) {
      stepWalkClip(walk, dt, reduced, animator, m, t, walkParams);
    } else if (m.walkWasPlaying) {
      m.walkWasPlaying = false;
      m.lastLeg = -1;
      animator.cancelTransition();
      m.afterWalk = true; // hand the base back to the director (with a fade, not a pop)
    }

    // 06-avatar-context: the context director decides base, one-shots, nods, expression and hologram.
    const ctx = contextFnRef.current ? contextFnRef.current() : null;
    const din = m.dirIn;
    const levelNow = motionState === 'speaking' && levelFnRef.current ? levelFnRef.current() : -1;
    din.agentState = motionState;
    din.signals = ctx ? ctx.signals : null;
    din.cues = ctx ? ctx.cues : null;
    din.childSpeaking = ctx ? ctx.childSpeaking : false;
    din.gam = ctx ? ctx.gam : null;
    din.sessionEndingSeq = ctx ? ctx.sessionEndingSeq : 0;
    din.connectSeq = ctx ? ctx.connectSeq : 0;
    din.awaySec = ctx ? ctx.awaySec : 0;
    din.voiceLevel = levelNow;
    din.walkIn = !!walking;
    din.reduced = reduced;
    din.waveAgo = t - m.waveAt;
    // w3: the page model of the held web window, rebuilt only when a new al.search arrives
    const sw = din.signals ? din.signals.web : null;
    if (!sw || sw.used) {
      m.webModel = null;
      m.webRev = -1;
    } else if (sw.rev !== m.webRev) {
      m.webRev = sw.rev;
      m.webModel = buildPageModel(sw, (langRef.current || (ctx ? ctx.lang : 'en')) === 'ar' ? 'ar' : 'en');
    }
    din.web = m.webModel;
    director.step(dt, din, dirOut);
    if (!walking) applyDirector(dirOut, animator, proceduralNod, m);
    // A blink request (the hologram's bloom and glow) and the blink rate for the mood.
    if (dirOut.blinkNow) animator.blink();
    const blinker = lipRig.blinker;
    if (blinker.phase === 0 && dirOut.blinkRate !== 1) blinker.timer -= dt * (dirOut.blinkRate - 1);
    const perfDir = perfOn ? performance.now() - p0 : 0;

    // The mixer only writes a bone whose blended value changed, so every offset layered on top of
    // it is taken back first, last one applied first (the look-at saw the nod, so it goes before it).
    acting.restore(); // WP4: ears
    lookAt.restore();
    if (m.twistApplied && bones.chest) bones.chest.quaternion.copy(bones.chestBase); // same for the walk-in chest turn
    m.twistApplied = false;
    headLayer.restore();
    exprLayer.restore();
    animator.update(dt);
    headLayer.pitch = proceduralNod.step(dt);
    headLayer.apply();
    exprLayer.apply(dirOut.squint);
    // The walk-in moves the body by what the Walk clip shows, so it needs the clip's real weight.
    if (walking) walk.clipWeight = animator.weightOf(CLIP.walk);

    // ---- voice: lip-sync morphs, blink timing, subtle jaw ----
    const speaking = motionState === 'speaking';
    let open = 0;
    if (speaking) {
      const level = levelNow; // read once above, for the director too
      if (level >= 0) {
        m.levelPeak = Math.max(level, m.levelPeak * Math.exp(-JAW_PEAK_DECAY * dt));
        const full = Math.max(m.levelPeak, JAW_PEAK_MIN);
        open = clamp((level - JAW_LEVEL_FLOOR) / (full - JAW_LEVEL_FLOOR), 0, 1);
      } else {
        const a = (Math.sin(t * JAW_SYNTH_HZ_A) + 1) * 0.5;
        const b = (Math.sin(t * JAW_SYNTH_HZ_B + 1.3) + 1) * 0.5;
        open = 0.35 + 0.65 * a * (0.5 + 0.5 * b);
      }
    }
    // Analyse the voice only while speaking (phones do not pay for it otherwise).
    const lipsync = speaking && lipRig.hasVisemes && lipsyncFnRef.current ? lipsyncFnRef.current() : null;
    const lipCtx = m.lipCtx;
    lipCtx.lipsync = lipsync;
    lipCtx.open = open;
    lipCtx.speaking = speaking;
    lipCtx.reduced = reduced;
    applyVisemeBias(lipRig.bias, dirOut, speaking); // 06-avatar-context: smile, soft mouth, "ooh"
    lipRig.update(dt, lipCtx);
    // The scheduler decides when; the Blink clip is what the child sees.
    const blinks = lipRig.blinker.blinks;
    if (blinks !== m.lastBlinks) {
      m.lastBlinks = blinks;
      animator.blink();
    }

    // WP4: the jaw comes from the mouth shaper (it follows the shown visemes, with the PP gate and
    // the open budget); stress, speech head and face accents run off the same frame.
    const motionStateNow = walking ? 'walk' : animator.shotAmount > 0.3 ? 'oneshot' : motionState;
    acting.update(dt, { lipsync, open, speaking, reduced, state: motionStateNow });
    acting.applyJaw(m.jawDebug);
    m.jaw = m.jawDebug >= 0 ? m.jawDebug : acting.shaper.jawOpen;

    // 06-avatar-context: the hologram, placed in the model's space after the pose is final.
    const hc = m.holoCtx;
    const rtl = (langRef.current || (ctx ? ctx.lang : 'en')) === 'ar';
    if (rtl !== m.rtl) {
      m.rtl = rtl;
      rig.setRtl(rtl);
    }
    hc.camera = frame.camera;
    hc.hasHold = animator.has(CLIP.searchHold);
    hc.webClips = animator.has(SEARCH_SCROLL_W); // avatar-integ: the P6 W clips exist (BEHAVIOUR-SPEC 6.3)
    hc.scrollW = hc.webClips && animator.shotName === SEARCH_SCROLL_W && animator.shotAmount > 0.01; // avatar-integ: webSafety is frozen while it plays
    hc.reduced = reduced;
    hc.viewW = frame.size.width;
    hc.viewH = frame.size.height;
    hc.pxPerUnit = frame.camera.projectionMatrix.elements[5] * frame.gl.domElement.height * 0.5 * MODEL_SCALE;
    hc.web = m.webModel; // w3
    hc.jaw = bones.jaw;
    const q0 = perfOn ? performance.now() : 0;
    rig.update(dt, dirOut.holo, hc);
    if (rig.webBlink) {
      rig.webBlink = false; // w3: a blink as the page flicks
      animator.blink();
    }
    if (perfOn) {
      const ms = perfDir + (performance.now() - q0);
      const pf = m.perf;
      pf.n += 1;
      pf.sum += ms;
      if (ms > pf.max) pf.max = ms;
    }
    if (dirOut.statusSeq !== m.statusSeq) {
      m.statusSeq = dirOut.statusSeq;
      if (statusFnRef.current && dirOut.statusSeq > 0) statusFnRef.current(dirOut.statusKind, dirOut.statusSeq);
    }
    m.gl = frame.gl;

    // ---- look-at, last ----
    let gx = 0;
    let gy = 0;
    if (m.lookOverride) {
      gx = m.lookOverride.x;
      gy = m.lookOverride.y;
    } else if (!reduced) {
      const g = gaze.current;
      if (t - g.last < LOOK.pointerIdle) {
        gx = g.x;
        gy = g.y;
      }
    }
    const a = animator.shotAmount;
    const onWalk = animator.baseName === CLIP.walk || animator.transitionName !== '';
    const baseAllow = onWalk ? 0.5 : (LOOK.stateWeight[motionState] ?? 1);
    const shotAllow = LOOK.oneShotWeight[animator.shotName] ?? 1;
    let weight = baseAllow * (1 - a) + shotAllow * a;
    // 06-avatar-context: while the panel is up the gaze goes to it (no SearchHold clip: mostly; with the clip: a little).
    const lp = dirOut.lookPanel;
    if (lp > 0.001 && rig.root.visible && !m.lookOverride) {
      panelNdc.copy(rig.gazeOn ? rig.gazePt : rig.center); // w3: the line he is reading, when there is a page
      rig.root.localToWorld(panelNdc);
      panelNdc.project(frame.camera);
      const ga = 1 - rig.glance; // w3: a glance at the child pulls the target to the camera
      gx += (panelNdc.x * ga - gx) * lp;
      gy += (panelNdc.y * ga - gy) * lp;
      weight += (Math.max(weight, LOOK.panelWeight) - weight) * lp;
    }
    if (reduced) weight = Math.min(weight, LOOK.reducedWeight);
    lookAt.update(dt, gx, gy, weight);
    if (walking && walk.sw) applyWalkTurn(walk.sw, bones, m);
    acting.applyHead(); // WP4: speech head, neck and ears on top of the look-at

    // ---- the model's place: heading, hop ----
    const g = groupRef.current;
    const face = stage ? stage.facing : 0; // avatar-integ: the idle pivot on the meadow stage
    if (g) {
      if (walking) {
        g.rotation.y = walk.yaw + face;
        g.position.y = WALK.hopHeight * walk.hop;
      } else if (g.rotation.y !== face || g.position.y !== 0) {
        g.rotation.y = face;
        g.position.y = 0;
      }
    }
    if (stage && outerRef.current) {
      // avatar-integ: where on the path he stands (after this frame's walk step), and his fade-in on arrival
      placeStage(stage);
      outerRef.current.position.set(stage.px, 0, stage.pz);
      const fade = walk && walk.state !== STATE.DONE ? walk.fade : 1;
      if (m.stageFade !== fade) {
        m.stageFade = fade;
        gl.domElement.style.opacity = fade >= 0.999 ? '' : String(fade);
      }
    }

    // ---- hotfix-2: the conversation shot, last: the pose is final, so the face is measured where it is drawn ----
    if (shotRig && shotRig.enabled) {
      const holoPhase = dirOut.holo ? dirOut.holo.phase : HP.CLOSED;
      const block = !!walking || motionState === 'thinking' || holoPhase !== HP.CLOSED;
      const want = motionState === 'speaking' || motionState === 'listening';
      const sw = frame.size.width;
      const sh = frame.size.height;
      if (m.fr?.w !== sw || m.fr?.h !== sh || m.fr?.look !== lookdevShot) {
        m.fr = { w: sw, h: sh, look: lookdevShot, v: lookdevShot ? lookdevShotFraming(sw, sh) : computeFraming(sw, sh) };
      }
      const e = shotRig.update({
        dt, want, block, reduced, camera: frame.camera, fr: m.fr.v, w: sw, h: sh,
        viewH: typeof window !== 'undefined' ? window.innerHeight : sh, avatarX,
      });
      if (Math.abs(e - m.shotCss) > 0.01 || m.shotCss === undefined) {
        m.shotCss = e;
        document.documentElement.style.setProperty('--sadiq-shot', e.toFixed(2));
      }
    }
    if (acting.onFrame) acting.onFrame(); // WP4 dev: measurement sample
  });

  return (
    <group ref={outerRef} position={[avatarX, 0, 0]}>
      <group ref={groupRef} scale={MODEL_SCALE}>
        <primitive object={scene} />
        <primitive object={rig.root} />
      </group>
    </group>
  );
}

// 06-avatar-context ---------------------------------------------------------------------------

const panelNdc = new Vector3(); // scratch for the look-at

/** The hologram tier: a prop wins, then ?holotier=low|high (dev pages), then the device. */
function resolveTier(prop) {
  if (typeof prop === 'boolean') return prop;
  try {
    const q = new URLSearchParams(globalThis.location?.search ?? '').get('holotier');
    if (q === 'low') return true;
    if (q === 'high') return false;
  } catch {
    /* no location: use the device */
  }
  return isLowTier();
}

/** Apply what the director decided this frame to the animator. Allocates nothing. */
function applyDirector(d, animator, nod, m) {
  if (m.override) {
    // Dev: hold one loop whatever the director wants.
    if (m.override !== m.appliedBase) {
      m.appliedBase = m.override;
      animator.setBase(m.override);
    }
  } else if (d.baseChanged) {
    m.appliedBase = d.base;
    const fade = m.afterWalk ? Math.max(d.baseFade, 0.4) : d.baseFade;
    m.afterWalk = false;
    animator.setBase(d.base, fade, d.baseEntry, d.baseScale);
  } else if (m.afterWalk) {
    m.afterWalk = false;
  }
  animator.setUnderlay(d.underlay);
  if (d.interrupt > 0) animator.interrupt(d.interrupt);
  if (d.oneShot !== '') {
    // switchBase false: the director has already chosen the base for this frame (SearchHold under SearchStart,
    // the current state loop under Found, spec 7.5). Letting the transition switch it to its `to` loop (Idle for
    // Found) would leave the animator on Idle while the director believes the talk or think loop is playing.
    const played = animator.playOnce(d.oneShot, {
      force: d.oneShotForce, maxWeight: d.oneShotWeight, fadeIn: d.oneShotFade || undefined, switchBase: false,
    });
    // The director believes the shot is playing; if the animator refused it the two are out of step (a shot already
    // in flight, reduced motion, a clip the GLB lacks). Say so in dev, once per refusal.
    if (!played && import.meta.env?.DEV) {
      console.warn(`[avatar] the animator refused the director's shot "${d.oneShot}" (${d.oneShotLogical || 'no logical name'})`);
    }
  }
  if (d.nod > 0) {
    if (animator.has(CLIP.nod)) animator.playAdditive(CLIP.nod, d.nod, d.nodScale);
    else nod.fire(d.nod, d.nodScale);
  }
}

/** The expression layer's viseme offsets: smile (less while speaking), soft mouth (only at rest), "ooh". */
function applyVisemeBias(bias, d, speaking) {
  const B = DIRECTOR.bias;
  const smile = d.smile * (speaking ? B.smileSpeaking : 1);
  const soft = speaking ? 0 : d.soft;
  bias[VI.E] = B.smileE * smile;
  bias[VI.I] = B.smileI * smile + B.softI * soft;
  bias[VI.sil] = B.softSil * soft;
  bias[VI.O] = B.oohO * d.ooh;
  bias[VI.U] = B.oohU * d.ooh;
}

/**
 * The walk-in turn on top of the look-at: the head leads the root turn, and at the stop the chest,
 * neck and head carry the remaining turn (the root turns slowly afterwards). Same discipline as the
 * look-at: the head and neck are put back by lookAt.restore(), the chest by the frame loop.
 */
function applyWalkTurn(sw, bones, m) {
  const twist = sw.twist;
  const lead = sw.lead;
  if (Math.abs(twist) < 1e-5 && Math.abs(lead) < 1e-5) return;
  if (bones.chest && Math.abs(twist) > 1e-5) {
    bones.chestBase.copy(bones.chest.quaternion);
    bones.chest.quaternion.multiply(boneTurn.setFromAxisAngle(TURN_AXIS, twist * TWIST_SHARE.chest));
    m.twistApplied = true;
  }
  if (bones.neck) bones.neck.quaternion.multiply(boneTurn.setFromAxisAngle(TURN_AXIS, twist * TWIST_SHARE.neck + lead * LEAD_SHARE.neck));
  if (bones.head) bones.head.quaternion.multiply(boneTurn.setFromAxisAngle(TURN_AXIS, twist * TWIST_SHARE.head + lead * LEAD_SHARE.head));
}

/** Steps the walk-in timeline and plays the matching clips. Allocates nothing. */
function stepWalkClip(walk, dt, reduced, animator, m, t, params) {
  stepWalkImpl(walk, dt, reduced, params);
  m.walkWasPlaying = true;
  const sw = walk.sw;
  if (params.studio && sw) {
    syncStudio(walk, sw, animator, m, t);
    return;
  }
  if (walk.state !== m.lastWalkState) {
    m.lastWalkState = walk.state;
    m.walkStopping = false;
    if (walk.state === STATE.WALK) animator.setBase(CLIP.walk, ANIM.fade);
    else if (walk.state === STATE.TURN || walk.state === STATE.HOP) animator.setBase(CLIP.idle, 0.3);
    else if (walk.state === STATE.WAVE) {
      animator.playOnce(CLIP.wave, { force: true });
      m.waveAt = t; // 06-avatar-context: the director skips Greet when Wave just played
    }
  }
  // The stop at the spot: Walk fades to Idle over exactly the time the timeline brakes in.
  if (walk.stopping && !m.walkStopping) {
    m.walkStopping = true;
    animator.setBase(CLIP.idle, WALK_CLIP_LEGACY.stopTime);
  }
  if (walk.state === STATE.WALK) animator.setLoopScale(CLIP.walk, walk.timeScale);
}

/**
 * The studio walk: the timeline (studioWalk.js) says which leg plays and how far into it, and the
 * clip times are set from that, so the pose and the root motion are one clock. Start blends in over
 * Idle, hands over to Walk at f0 without a fade, a stop cuts in on a heel strike and hands over to
 * Idle at f0.
 */
function syncStudio(walk, sw, animator, m, t) {
  const first = m.lastWalkState !== walk.state;
  m.lastWalkState = walk.state;
  if (walk.state === STATE.WALK) {
    if (sw.leg !== m.lastLeg) {
      const from = m.lastLeg;
      m.lastLeg = sw.leg;
      if (from === LEG.START) animator.endTransition(CLIP.walk, sw.walkClock);
      if (sw.leg === LEG.START) animator.startTransition(CLIP.walkStart, { blendIn: STUDIO_BLEND_IN });
      else if (sw.leg === LEG.STOP) {
        animator.startTransition(sw.side === 'R' ? CLIP.walkStopR : CLIP.walkStopL, { blendIn: 0 });
      }
    }
    if (sw.leg === LEG.CRUISE) animator.setLoopTime(CLIP.walk, sw.walkClock);
    else animator.setTransitionTime(sw.legT);
    return;
  }
  if (first) {
    m.lastLeg = -1;
    if (animator.transitionName) animator.endTransition(CLIP.idle, 0); // the stop is on Idle f0
    if (walk.state === STATE.WAVE) {
      animator.playOnce(CLIP.wave, { force: true });
      m.waveAt = t; // 06-avatar-context: the director skips Greet when Wave just played
    }
  }
}

const STUDIO_BLEND_IN = 0.1; // seconds Walk_Start takes to fade in over Idle (both start on Idle f0)
const LEGACY_PARAMS = {
  ...WALK_CLIP_LEGACY,
  modelScale: MODEL_SCALE,
  waveTime: 2.8,
  fadeIn: WALK.fadeIn,
  studio: false,
};
const STUDIO_PARAMS = {
  ...WALK_CLIP, // fadeIn and holdIn come from here: the studio walk fades in on Idle f0 before Walk_Start plays
  modelScale: MODEL_SCALE,
  waveTime: 2.8,
  studio: true,
};
const stepArgs = { reduced: false, clip: LEGACY_PARAMS };
function stepWalkImpl(walk, dt, reduced, params) {
  stepArgs.reduced = reduced;
  stepArgs.clip = params;
  stepWalk(walk, dt, stepArgs);
}
