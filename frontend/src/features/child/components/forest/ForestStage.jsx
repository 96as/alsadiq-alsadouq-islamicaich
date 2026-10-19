/* The stage hands the runtime object (plain mutable state, see runtime.js) to the frame loop. */
/* eslint-disable react-hooks/immutability */
import { Suspense, lazy, useCallback, useEffect, useRef, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import ForestBoundary from './ForestBoundary';
import ForestWorld from './ForestWorld';
import MeadowLife from '../ambient/MeadowLife';
import ForegroundStrip from './ForegroundStrip';
import { createRuntime, lookAt } from './runtime';
import { briefWave, replayWalk, tapHop } from '../avatar/walkIn';
import { timeBlendFromDate } from './timeOfDay';
import { detectQuality, maxDpr, usePageVisible, useReducedMotion, webglAvailable } from './quality';
import { clickLabel, useForestManifest } from './useForestManifest';
import { MEADOW_IMAGE, MEADOW_SIZES, MEADOW_SRCSET } from './meadowPoster';

// The Avatar owns its own canvas (and a large model), so it loads on demand.
const Avatar = lazy(() => import('../avatar/Avatar'));

/** Test and preview switch: ?walk=off skips the walk-in, ?walk=hop plays the fallback (a hop and a wave). */
function walkModeFromUrl() {
  try {
    const v = new URLSearchParams(window.location.search).get('walk');
    return v === 'off' || v === 'hop' ? v : 'walk';
  } catch {
    return 'walk';
  }
}

/** The device clock, checked every minute: the period, plus the neighbour it is blending toward near a boundary. */
function useClockTime() {
  const [t, setT] = useState(() => timeBlendFromDate(new Date()));
  useEffect(() => {
    const id = window.setInterval(() => {
      const next = timeBlendFromDate(new Date());
      setT((cur) => (cur.name === next.name && cur.next === next.next && Math.abs(cur.weight - next.weight) < 0.01 ? cur : next));
    }, 60000);
    return () => window.clearInterval(id);
  }, []);
  return t;
}

/** True while at least 5% of the element is on screen (the stage pauses its two canvases when it is not). */
function useOnScreen(ref) {
  const [on, setOn] = useState(true);
  useEffect(() => {
    const el = ref.current;
    if (!el || typeof IntersectionObserver === 'undefined') return undefined;
    const io = new IntersectionObserver(([entry]) => setOn(entry.isIntersecting), { threshold: [0, 0.05] });
    io.observe(el);
    return () => io.disconnect();
  }, [ref]);
  return on;
}

/**
 * The forest scene as a full-size stage.
 *
 * Layers, back to front: meadow image (poster and WebGL fallback), the 3D
 * canvas, the Avatar (its own transparent canvas, pinned to the ground by the
 * camera rig), then `children` (all HTML, so text stays Arabic/RTL safe).
 *
 * Props
 *   phase          'wide' (idle shot) or 'talk' (close shot). Changing it glides the camera.
 *   timeOfDay      force 'morning' | 'noon' | 'maghrib' | 'night'. Default: the device clock.
 *   hidden         keep mounted but pause drawing and fade out (for the chat view).
 *   avatarSpeaking forwarded to Avatar (fallback speaking flag).
 *   agentState     lk.agent.state, forwarded to Avatar (listening, thinking, speaking poses).
 *   getAudioLevel  () => level of the agent's voice, forwarded to Avatar (audio-driven jaw).
 *   getLipsync     () => live viseme state of the agent's voice, forwarded to Avatar (lip-sync).
 *   onClickTarget  called with the node name when a Click_* object is clicked.
 *   avatarControlRef optional ref; gets the avatar's dev handle ({ play, hold, look, clips, ... }), preview page only.
 *   getAvatarContext () => the avatar signal store's context, forwarded to Avatar (06-avatar-context).
 *   lang           'ar' | 'en', forwarded to Avatar (06-avatar-context).
 *   walkControlRef optional ref; gets `{ replay(mode), walk, rt }`: replay plays the walk-in again (preview page),
 *                  walk is the shared walk state (read-only for callers, e.g. the demo landing greets when it waves),
 *                  rt is the shared runtime (screen positions of Sadiq and the props, gaze, pointer),
 *                  hop() / wave() / look(target, seconds) make Sadiq hop, wave briefly, or turn his head;
 *                  setTime(name | null) forces the time of day (the time pill) or returns to the device clock.
 *   walkPreset     'default' (child screen) or 'landing' (a shorter walk-in for the demo landing).
 *   interactive    draw the lantern, book and bulbul (the DOM buttons for them live in the caller's children).
 *
 * The stage pauses both canvases while less than 5% of it is on screen, and walks the quality down
 * (rt.degrade) when frames stay slow.
 *
 * Walk-in: once per page load, when the avatar first appears, it starts up the path, waddles to its
 * spot, turns to face the child and waves. It is skipped for reduced motion. Only this stage passes
 * a walk to the Avatar, so the meadow mode never walks.
 */
export default function ForestStage({
  phase = 'wide',
  timeOfDay,
  hidden = false,
  avatarSpeaking = false,
  agentState,
  getAudioLevel,
  getLipsync,
  getAvatarContext, // 06-avatar-context: the signal store getter, forwarded to Avatar
  lang, // 06-avatar-context: 'ar' | 'en'
  onClickTarget,
  walkControlRef,
  walkPreset = 'default',
  interactive = false,
  avatarControlRef,
  children,
  className = '',
}) {
  const rootRef = useRef(null);
  const [quality] = useState(detectQuality);
  const reduced = useReducedMotion();
  const visible = usePageVisible();
  const clock = useClockTime();
  const [picked, setPicked] = useState(null); // a time chosen through control.setTime (the time pill)
  const forcedTime = timeOfDay || picked;
  const timeName = forcedTime || clock.name;
  const onScreen = useOnScreen(rootRef);
  const paused = !onScreen;
  const [failed, setFailed] = useState(() => !webglAvailable());
  const [ready, setReady] = useState(false);
  const [clicks, setClicks] = useState([]);
  const [rt] = useState(() => createRuntime({ quality, reduced, timeName, walkMode: walkModeFromUrl(), walkPreset }));
  const manifest = useForestManifest(!failed);

  useEffect(() => {
    rt.timeName = timeName;
    // Near a boundary the scene is already moving toward the next palette (only when following the clock).
    rt.timeNext = forcedTime ? null : clock.next;
    rt.timeW = forcedTime ? 0 : clock.weight;
  }, [rt, timeName, forcedTime, clock.next, clock.weight]);
  useEffect(() => {
    rt.paused = paused;
  }, [rt, paused]);
  useEffect(() => {
    rt.phase = phase;
  }, [rt, phase]);
  useEffect(() => {
    rt.reduced = reduced;
  }, [rt, reduced]);

  // The walk may start once the forest is drawn and the avatar can be seen. If the child starts the
  // session first, the rest of the walk plays fast so the avatar is at its spot for the close shot.
  useEffect(() => {
    rt.walk.armed = rt.walk.armed || (ready && !failed && !hidden);
  }, [rt, ready, failed, hidden]);
  useEffect(() => {
    rt.walk.rush = phase === 'talk';
  }, [rt, phase]);
  useEffect(() => {
    if (!walkControlRef) return undefined;
    walkControlRef.current = {
      replay: (mode) => replayWalk(rt.walk, mode),
      walk: rt.walk,
      rt,
      // for the landing's overlay (kept here so the landing page never imports three.js)
      hop: () => tapHop(rt.walk),
      wave: () => briefWave(rt.walk),
      look: (target, seconds) => lookAt(rt, target, seconds),
      setTime: setPicked, // 'morning' | 'noon' | 'maghrib' | 'night', or null for the device clock
    };
    return () => {
      walkControlRef.current = null;
    };
  }, [rt, walkControlRef]);

  useEffect(() => {
    const onClick = (e) => {
      if (onClickTarget) onClickTarget(e.detail);
    };
    rt.bus.addEventListener('click-target', onClick);
    return () => rt.bus.removeEventListener('click-target', onClick);
  }, [rt, onClickTarget]);

  useEffect(() => {
    if (!import.meta.env.DEV) return undefined;
    window.__forest = { rt };
    return () => {
      delete window.__forest;
    };
  }, [rt]);

  const setLayer = useCallback(
    (el) => {
      rt.layerEl = el;
    },
    [rt],
  );

  const onPointerMove = (e) => {
    if (reduced || e.pointerType === 'touch') return;
    const r = e.currentTarget.getBoundingClientRect();
    rt.pointer.x = ((e.clientX - r.left) / r.width) * 2 - 1;
    rt.pointer.y = -(((e.clientY - r.top) / r.height) * 2 - 1);
  };

  const onCreated = useCallback(({ gl }) => {
    gl.domElement.addEventListener('webglcontextlost', (ev) => {
      ev.preventDefault();
      setFailed(true);
    });
    setReady(true);
  }, []);

  const fadeMs = reduced ? 350 : 800;

  return (
    <div
      ref={rootRef}
      onPointerMove={onPointerMove}
      data-forest-stage=""
      data-time={timeName}
      data-phase={phase}
      data-quality={quality}
      data-state={failed ? 'fallback' : ready ? 'ready' : 'loading'}
      className={`relative flex min-h-0 flex-1 flex-col overflow-hidden bg-[#b7d9dc] ${className}`}
    >
      {/* Poster while the 3D loads, and the whole background if WebGL is not available. */}
      {failed ? (
        <MeadowLife anchored={false} /> /* the fallback is the living painted meadow (it keeps the still image under it) */
      ) : (
        <img
          src={MEADOW_IMAGE}
          srcSet={MEADOW_SRCSET}
          sizes={MEADOW_SIZES}
          alt=""
          aria-hidden="true"
          draggable="false"
          className="pointer-events-none absolute inset-0 h-full w-full translate-x-[1%] scale-[1.03] select-none object-cover object-[47.5%_center]"
        />
      )}

      {!failed && (
        <ForestBoundary onError={() => setFailed(true)}>
          <div
            className="absolute inset-0"
            style={{
              opacity: ready && !hidden ? 1 : 0,
              transition: `opacity ${fadeMs}ms ease`,
              visibility: hidden && ready ? 'hidden' : 'visible',
            }}
          >
            <Canvas
              flat
              resize={{ offsetSize: true, scroll: false }}
              dpr={[1, maxDpr(quality)]}
              frameloop={visible && !hidden && !paused ? 'always' : 'never'}
              gl={{ antialias: quality === 'high', alpha: false, powerPreference: 'high-performance' }}
              camera={{ fov: 44, near: 0.1, far: 200, position: [0.7, 1.55, 5.6] }}
              eventSource={rootRef}
              eventPrefix="client"
              onCreated={onCreated}
              style={{ position: 'absolute', inset: 0 }}
              aria-hidden="true"
            >
              <ForestWorld
                rt={rt}
                manifest={manifest.status === 'ready' ? manifest.manifest : null}
                onClicks={setClicks}
                interactive={interactive}
              />
            </Canvas>
          </div>
        </ForestBoundary>
      )}

      {/* The Avatar (same component and avatar-web.glb as the meadow mode), pinned to the forest floor by the camera rig. */}
      <div
        ref={setLayer}
        className="pointer-events-none absolute inset-0"
        style={{ visibility: hidden ? 'hidden' : 'visible', opacity: failed || ready ? 1 : 0, transition: `opacity ${fadeMs}ms ease` }}
      >
        {/* Unmounted while hidden (chat view), as before the forest: its canvas would keep drawing. */}
        {!hidden && (
          <ForestBoundary>
            <Suspense fallback={null}>
              <Avatar
                isSpeaking={avatarSpeaking}
                agentState={agentState}
                getAudioLevel={getAudioLevel}
                getLipsync={getLipsync}
                getAvatarContext={getAvatarContext} // 06-avatar-context
                lang={lang} // 06-avatar-context
                walk={rt.walk}
                gaze={rt.gaze}
                paused={paused || !visible}
                controlRef={avatarControlRef}
              />
            </Suspense>
          </ForestBoundary>
        )}
      </div>

      {/* Blades and flowers in front of the avatar's feet (a 2D layer: the avatar is a separate canvas). */}
      {!hidden && <ForegroundStrip mode="forest" rt={rt} />}

      {/* Real buttons for every 3D click target (keyboard and screen reader users). */}
      {clicks.length > 0 && !hidden && (
        <ul className="absolute left-3 top-3 z-30 m-0 list-none p-0">
          {clicks.map((name) => (
            <li key={name}>
              <button
                type="button"
                onClick={() => onClickTarget && onClickTarget(name)}
                className="sr-only focus:not-sr-only focus:rounded-xl focus:bg-black/60 focus:px-3 focus:py-2 focus:text-sm focus:text-white"
              >
                {clickLabel(name)}
              </button>
            </li>
          ))}
        </ul>
      )}

      <div className="relative z-10 flex min-h-0 flex-1 flex-col">{children}</div>
    </div>
  );
}
