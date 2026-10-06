import { Component, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Box3, Vector3 } from 'three'; // avatar-integ: forest speech-bubble height (walk.modelHeight)
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { useGLTF } from '@react-three/drei';
import * as SkeletonUtils from 'three/examples/jsm/utils/SkeletonUtils.js';
import useAvatarMotion from './useAvatarMotion';
import { resolveMotionState } from './motionConfig';
import ClipAvatar from './ClipAvatar';
import { FALLBACK_MODEL_URL, FALLBACK_SHIPPED, REQUIRED_CLIPS, configuredModelUrl } from './avatarConfig';
import { WALK, pinWalkDistance } from './walkIn';
import { computeFraming } from '../meadowFraming';
import { HOLO } from './hologram/hologramConfig'; // 06-avatar-context
// LOOKDEV: the look-dev rig (camera, light, grade, grounding) and its URL switches. "?look=before" restores the old look.
import AvatarLookdev from './lookdev/AvatarLookdev';
import { lookdevAvatarX } from './lookdev/lookdevRuntime';
import { LOOKDEV } from './lookdev/lookdevConfig';
import { lookParams, lookdevActive } from './lookdev/lookFlag';
import { detectQuality } from '../forest/quality';
import { avatarCamPose } from './avatarCam';

// Two models. The animated one (avatar-animated.glb, 27 bones, 14 viseme morphs, 9 clips) plays its
// clips. The web build of the Tripo avatar (about 0.7 MB, meshopt; rebuild with
// `npm run avatar:optimize`) has no clips and keeps today's procedural motion. The animated one is
// the default (VITE_AVATAR_MODEL_URL changes it); if it fails to load or lacks a clip the Avatar
// falls back to the web build, but only when FALLBACK_SHIPPED (avatar-integ perf: the web build is no longer published).
const MODEL_URL = FALLBACK_MODEL_URL;
const BACKDROP_MATERIAL_NAME = 'BackdropMat';

/**
 * Loads the Blender-exported GLB scene and:
 * - Hides the legacy backdrop plane so VoiceMode can supply a responsive image.
 * - Hands the clone to useAvatarMotion, which drives idle life, the agent states and the jaw.
 *
 * Lighting comes from R3F JSX (ambient + two directional lights) so the
 * avatar PBR material is lit correctly.
 */
function SceneRig({ state, getAudioLevel, walk, gaze, getLipsync, morphNames, modelUrl, controlRef, framing, getAvatarContext, lang, lowTier, onStatus, lookOn, stage, productStage = false }) {
  const { size } = useThree();
  const gltf = useGLTF(modelUrl, false);
  // With framing="meadow" Sadiq stands on the path of the painted meadow (meadowFraming.js).
  // LOOKDEV: with the rig on, Sadiq's x comes from the stage framing (stageFraming.js); otherwise today's value.
  const avatarX = lookOn
    ? lookdevAvatarX(framing, size)
    : framing === 'meadow'
      ? computeFraming(size.width, size.height).avatarX
      : size.width / size.height < 0.8
        ? -0.02
        : -0.13;
  const names = gltf.animations.map((c) => c.name);
  const hasClips = REQUIRED_CLIPS.every((n) => names.includes(n));
  // A model that is not the web build must bring the clips; otherwise try the next URL.
  if (!hasClips && modelUrl !== FALLBACK_MODEL_URL) {
    throw new Error(`[Avatar] ${modelUrl} lacks the clips ${REQUIRED_CLIPS.filter((n) => !names.includes(n)).join(', ')}`);
  }
  if (hasClips) {
    return (
      <ClipAvatar
        gltf={gltf}
        state={state}
        getAudioLevel={getAudioLevel}
        walk={walk}
        getLipsync={getLipsync}
        morphNames={morphNames}
        avatarX={avatarX}
        controlRef={controlRef}
        getAvatarContext={getAvatarContext} // 06-avatar-context
        lang={lang} // 06-avatar-context
        lowTier={lowTier} // 06-avatar-context
        onStatus={onStatus} // 06-avatar-context
        shot={framing === 'meadow' && !stage && !productStage} // hotfix-2: the conversation shot on the meadow page; avatar-integ: never in the product (one camera move, then steady), even with ?look=before
        lookdevShot={lookOn && framing === 'meadow' && !stage && !productStage} // step 2: the shot starts from look-dev's grounded stage camera
        stage={stage} // avatar-integ: the meadow stage (meadowStage.js)
      />
    );
  }
  return (
    <ProceduralAvatar
      gaze={gaze}
      sourceScene={gltf.scene}
      state={state}
      getAudioLevel={getAudioLevel}
      walk={walk}
      getLipsync={getLipsync}
      morphNames={morphNames}
      avatarX={avatarX}
      controlRef={controlRef}
    />
  );
}

/** The old avatar: no clips, so every bone is driven by code (useAvatarMotion). */
function ProceduralAvatar({ sourceScene, state, getAudioLevel, walk, gaze, getLipsync, morphNames, avatarX, controlRef }) {
  const scene = useMemo(() => {
    const clonedScene = SkeletonUtils.clone(sourceScene);
    clonedScene.traverse((obj) => {
      if (!obj.isMesh) return;
      const materials = Array.isArray(obj.material) ? obj.material : [obj.material];
      if (materials.some((material) => material?.name === BACKDROP_MATERIAL_NAME)) {
        obj.visible = false;
      }
    });
    // The forest stage needs the model's height to anchor the speech bubble to the head.
    if (walk) {
      // Precise (per vertex, with the skeleton applied): the bind-pose box alone came out at a third of the real height.
      clonedScene.updateMatrixWorld(true);
      clonedScene.traverse((obj) => {
        if (obj.isSkinnedMesh) obj.skeleton.update();
      });
      const box = new Box3().setFromObject(clonedScene, true);
      const h = box.getSize(new Vector3()).y;
      // eslint-disable-next-line react-hooks/immutability -- the walk state is a shared mutable object by design
      if (h > 0.1 && h < 5) walk.modelHeight = h;
    }
    return clonedScene;
  }, [sourceScene, walk]);

  useAvatarMotion(scene, { state, getAudioLevel, walk, gaze, getLipsync, morphNames }); // avatar-integ: gaze (forest stage)
  useEffect(() => {
    pinWalkDistance(walk, WALK.distance);
  }, [walk]);
  useEffect(() => {
    if (!controlRef) return undefined;
    controlRef.current = { mode: 'procedural', clips: [], play: () => false, hold: () => {}, look: () => {}, jaw: () => {} };
    return () => {
      controlRef.current = null;
    };
  }, [controlRef]);

  return (
    <group position={[avatarX, 0, 0]}>
      <primitive object={scene} />
    </group>
  );
}

const camPose = { pos: [0, 0, 0], look: [0, 0, 0] };

/**
 * The camera. On the meadow (framing 'meadow') it is placed by stage height (Sadiq about 57% of it, feet above the mic
 * row, on any window shape; ClipAvatar's conversation shot then takes over while he speaks or listens).
 * In the forest it is the default camera, orbited about the feet to the forest camera's elevation while the avatar walks
 * in (`walk.camElev` and `walk.camAz`, published by the forest's CameraRig; null otherwise, which is exactly the default).
 * The feet stay on the same pixel at the same scale, so the forest's CSS placement is unaffected.
 */
function CameraSetup({ framing, walk }) {
  const { camera, size } = useThree();
  const last = useRef({ e: -1, a: -1 });
  const feetX = size.width / size.height < 0.8 ? -0.02 : -0.13;
  const meadow = framing === 'meadow';

  const place = (elev, az) => {
    avatarCamPose(elev, feetX, camPose, az);
    camera.position.set(...camPose.pos);
    camera.lookAt(...camPose.look);
    camera.updateProjectionMatrix();
  };

  useEffect(() => {
    last.current.e = -1;
    last.current.a = -1;
    if (meadow) {
      const f = computeFraming(size.width, size.height);
      camera.position.set(0, f.targetY, f.distance);
      camera.lookAt(0, f.targetY, 0);
      camera.updateProjectionMatrix();
    } else {
      place(null, null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [camera, feetX, meadow, size.width, size.height]);

  useFrame(() => {
    if (meadow) return;
    const elev = walk?.camElev ?? null;
    const az = walk?.camAz ?? null;
    const ke = elev == null ? -1 : elev;
    const ka = az == null ? -1 : az;
    if (ke === last.current.e && ka === last.current.a) return;
    last.current.e = ke;
    last.current.a = ka;
    place(elev, az);
  });

  return null;
}

/**
 * The URLs to try, in order: the one asked for (the prop, else the configured default), then the web
 * avatar. A model that fails to download or parse, or lacks the clips, moves on to the next URL; if
 * the last one fails too, render nothing (the page background stays) instead of crashing the session
 * screen. suspend-react caches a failed load, including one started by the idle-screen preload, so
 * clear it to let the next session retry.
 */
function modelChain(requested) {
  const first = requested || configuredModelUrl();
  return first === FALLBACK_MODEL_URL || !FALLBACK_SHIPPED ? [first] : [first, FALLBACK_MODEL_URL]; // avatar-integ perf: avatar-web.glb is not shipped (avatarConfig.js FALLBACK_SHIPPED)
}

class AvatarErrorBoundary extends Component {
  state = { attempt: 0, failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch(error) {
    const chain = modelChain(this.props.modelUrl);
    const url = chain[this.state.attempt];
    console.warn(`[Avatar] Could not use ${url}; ${this.state.attempt + 1 < chain.length ? 'trying the fallback' : 'continuing without it'}.`, error);
    useGLTF.clear(url);
    if (this.state.attempt + 1 < chain.length) this.setState({ attempt: this.state.attempt + 1, failed: false });
  }

  render() {
    if (this.state.failed) return null;
    const chain = modelChain(this.props.modelUrl);
    return this.props.children(chain[Math.min(this.state.attempt, chain.length - 1)]);
  }
}

/**
 * Renders the voice-mode avatar from a Blender GLB.
 * The Canvas fills 100% of its parent container (controlled by VoiceMode.jsx).
 *
 * Camera: positioned at chest height and aimed at the avatar's chest so the
 * face stays clear of the floating header in taller/fullscreen layouts.
 *
 * @param {boolean} isSpeaking — fallback speaking flag (audio-level boolean), used only while
 *   `agentState` is not listening, thinking or speaking.
 * @param {string} agentState — the agent's lk.agent.state: initializing, listening, thinking or speaking.
 * @param {() => number} getAudioLevel — RMS level of the agent's voice (negative when unavailable);
 *   drives the jaw of the procedural avatar. Without it the jaw uses a synthetic wave while speaking.
 * @param {object} walk — optional shared walk-in state (walkIn.js). Only the forest stage passes it.
 * @param {object} gaze — optional { x, y, weight } head-turn target in -1..1 (runtime.js). Only the forest stage passes it.
 * @param {boolean} paused — stop drawing (the forest stage pauses it while scrolled out of view).
 * @param {() => object|null} getLipsync — the agent's live viseme state (lipsync/useVisemes.js).
 *   Drives the viseme morph targets (animated avatar) or the jaw (web avatar).
 * @param {object} morphNames — optional { viseme: morphName } overrides for the GLB's names.
 * @param {string} modelUrl — optional GLB to load instead of the configured one (see avatarConfig.js).
 * @param {object} controlRef — optional ref that receives a dev handle ({ play, hold, look, clips, ... }).
 * @param {string} framing — "meadow" frames Sadiq by stage height and stands him on the path of the painted
 *   meadow (see meadowFraming.js); anything else keeps the fixed camera.
 */
export default function Avatar(props) {
  return (
    <AvatarErrorBoundary modelUrl={props.modelUrl}>
      {(url) => <AvatarCanvas key={url} {...props} modelUrl={url} />}
    </AvatarErrorBoundary>
  );
}

function AvatarCanvas({
  isSpeaking = false,
  agentState,
  getAudioLevel,
  walk,
  gaze, // avatar-integ: forest stage head-turn target
  paused = false, // avatar-integ: forest stage pauses drawing off-screen
  getLipsync,
  morphNames,
  modelUrl,
  controlRef,
  framing,
  getAvatarContext, // 06-avatar-context: () => the signal store's context (useLiveKitRoom)
  lang, // 06-avatar-context: 'ar' | 'en'
  lowTier, // 06-avatar-context: force the hologram tier (dev)
  stage: stageProp = null, // avatar-integ: the meadow stage (meadowStage.js); only used with the look-dev rig on the meadow
}) {
  const state = resolveMotionState(agentState, isSpeaking);
  // 06-avatar-context: the hologram's status line (aria-live, also shown as a small caption).
  const [status, setStatus] = useState({ kind: '', seq: 0 });
  const onStatus = useCallback((kind, seq) => {
    setStatus((s) => (s.seq === seq ? s : { kind, seq }));
  }, []);
  const caption = HOLO.status[status.kind]?.[lang === 'ar' ? 'ar' : 'en'] || '';
  // LOOKDEV: tier, DPR range (an adaptive drop lowers the top once, if frames stay slow) and the rig switch.
  const lookOn = lookdevActive(framing);
  const stage = lookOn && framing === 'meadow' ? stageProp : null; // avatar-integ
  const { tier: tierOverride, adaptive } = lookParams();
  const tier = tierOverride || detectQuality();
  const dprCfg = LOOKDEV.dpr[tier];
  const [dprTop, setDprTop] = useState(dprCfg.range[1]);
  const onSlow = useCallback(() => setDprTop((cur) => Math.min(cur, dprCfg.adaptiveMin)), [dprCfg.adaptiveMin]);
  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
    <Canvas
      camera={{ position: [0, 0.9, 3.2], fov: 32, near: 0.1, far: 50 }}
      dpr={lookOn ? [dprCfg.range[0], dprTop] : [1, 2]} // LOOKDEV
      frameloop={paused ? 'never' : 'always'} // avatar-integ
      shadows={lookOn && tier === 'high' ? 'percentage' : false} // LOOKDEV: R3F resets shadowMap.enabled on configure, so it is declared here
      gl={{ antialias: true, powerPreference: 'high-performance' }}
      onCreated={({ gl }) => {
        // LOOKDEV: the grade (CustomToneMapping, exposure 1.0) is selected by AvatarLookdev; today's ACES 1.12 otherwise.
        if (!lookOn) gl.toneMappingExposure = 1.12;
      }}
      style={{ width: '100%', height: '100%' }}
    >
      {(!lookOn || framing !== 'meadow') && <CameraSetup framing={framing} walk={walk} />}
      {lookOn ? (
        <AvatarLookdev framing={framing} tier={tier} onSlow={onSlow} adaptive={adaptive} stage={stage} />
      ) : (
        <>
          <ambientLight intensity={0.45} color="#fff4e8" />
          <hemisphereLight color="#dcefff" groundColor="#75512f" intensity={0.65} />
          <directionalLight position={[-2, 3, 2]} intensity={1.35} color="#ffd9a3" />
          <directionalLight position={[3, 2, -2]} intensity={0.65} color="#9fc4ff" />
          <directionalLight position={[0, 1, 4]} intensity={0.25} color="#fff6e8" />
        </>
      )}
      <SceneRig
        gaze={gaze}
        lookOn={lookOn}
        stage={stage}
        productStage={Boolean(stageProp)} // avatar-integ: the product's meadow stage owns the camera, so no speak-time shot
        framing={framing}
        state={state}
        getAudioLevel={getAudioLevel}
        walk={walk}
        getLipsync={getLipsync}
        morphNames={morphNames}
        modelUrl={modelUrl}
        controlRef={controlRef}
        getAvatarContext={getAvatarContext} // 06-avatar-context
        lang={lang} // 06-avatar-context
        lowTier={lowTier} // 06-avatar-context
        onStatus={onStatus} // 06-avatar-context
      />
    </Canvas>
    {/* 06-avatar-context: the search status for screen readers; sighted children see the hologram. */}
    <p
      role="status"
      aria-live="polite"
      dir={lang === 'ar' ? 'rtl' : 'ltr'}
      className="sr-only"
      data-avatar-status={status.kind}
    >
      {caption}
    </p>
    </div>
  );
}

// Draco is off (it would fetch its decoder from a CDN); meshopt is on by default in drei.
useGLTF.preload(configuredModelUrl(), false);
