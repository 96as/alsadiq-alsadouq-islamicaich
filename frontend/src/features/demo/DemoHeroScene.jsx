import { Component, Suspense, lazy, useCallback, useEffect, useRef, useState } from 'react';
import { Hand } from 'lucide-react';
import { StageLayer, StaticBubble } from './stageParts';
import useStageSpeech from './useStageSpeech';
import { useReducedMotion } from './hooks';
import { soundBus } from './soundBus';
import { MEADOW_IMAGE, MEADOW_SIZES, MEADOW_SRCSET } from '../child/components/forest/meadowPoster';
import MeadowLife from '../child/components/ambient/MeadowLife';
import { isForestEnabled } from '../child/components/forest/forestFlag'; // avatar-integ
// avatar-integ: the child's Home stage (painted meadow + Sadiq walking up the path). Already in the main bundle via the
// child page; its Avatar (three.js scene + GLB) is lazy inside it.
import MeadowStage from '../child/components/MeadowStage';

/**
 * DemoHeroScene: the live picture on the demo landing page.
 *
 * By default (like the product) it is the painted meadow with Sadiq walking up the path and waving (MeadowStage, the
 * child's Home stage; avatar-integ). With the forest flag on (isForestEnabled:
 * ?forest=1 or VITE_FOREST_SCENE=1) it is the 3D forest (ForestStage) with Sadiq, including the walk-in, plus
 * three small props (a lantern, a book and a bulbul). Everything the visitor can touch is a real
 * DOM button laid over the 3D object (positions come from the stage runtime, see useStageAnchor),
 * so the keyboard and screen readers work and no 3D picking is needed. The pieces live in
 * stageParts.jsx and the speech and prop state in useStageSpeech.js (the child idle screen uses both).
 *
 * What happens here:
 *   - Sadiq walks up the path and waves. When the wave starts, one greeting for the time of day
 *     appears word by word in a bubble that points at his head.
 *   - 1.2 s after the greeting a hint chip says to tap him. Tapping him (or the CTA) starts the demo.
 *   - Lantern, book and bulbul answer a tap. The book shows a value card, the bulbul gets a hello.
 *   - While nobody touches anything he glances around every 12 to 18 s, and once suggests the lantern.
 *
 * Fallbacks, lightest first:
 *   - no WebGL, or the forest chunk fails: the painted meadow with a sun glow and two slow clouds,
 *     the same bubble and hint (no character, no prop buttons). A tap on the scene starts the demo.
 *   - the forest draws but the avatar model fails: the forest alone (ForestStage isolates the avatar).
 *   - reduced motion: the forest is drawn but calm (no walk-in, no parallax). Props still answer.
 *
 * Props
 *   t            the copy for the current language (copy.js)
 *   time         'morning' | 'noon' | 'maghrib' | 'night', picks the greeting
 *   forcedTime   a time to force the forest to (the preview pill), or null for the device clock
 *   onStart      called when the visitor taps Sadiq (the page starts the demo, like the CTA)
 *   busy         true while the demo is starting
 *   controlRef   ref the stage fills with { walk, rt, hop, wave, look }
 *   ctaPoint     () => { x, y } client position of the CTA, so Sadiq can glance at it
 *   className    sizing and radius are the parent's job (the scene fills it)
 */

// Lazy so three.js, the forest and the GLB only download after the page is interactive.
const ForestStage = lazy(() => import('../child/components/forest/ForestStage'));
// The same chunk the stage uses. Fetched early so the model download starts with the forest.
const warmAvatar = () => import('../child/components/avatar/Avatar').catch(() => {});


// walkIn.js STATE values: 3 is WAVE (4 is HOP, 5 is DONE, which reduced motion jumps to).
const WALK_WAVE = 3;
const GREET_FALLBACK_MS = 8000;
const HINT_DELAY_MS = 1200;
const NUDGE_AFTER_MS = 20000;

/** If the forest chunk or WebGL fails, the painted meadow stays and the scene still works. */
class SceneBoundary extends Component {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  componentDidCatch() {
    this.props.onFail?.();
  }
  render() {
    return this.state.failed ? null : this.props.children;
  }
}

const hasWebGL = () => {
  try {
    const canvas = document.createElement('canvas');
    return Boolean(canvas.getContext('webgl2') || canvas.getContext('webgl'));
  } catch {
    return false;
  }
};

const DemoHeroScene = ({
  t,
  time = 'noon',
  forcedTime = null,
  onStart,
  busy = false,
  controlRef,
  ctaPoint,
  className = '',
}) => {
  const rootRef = useRef(null);
  const greeted = useRef(false);
  const starting = useRef(false);
  const reduced = useReducedMotion();

  const [webgl] = useState(hasWebGL);
  // avatar-integ: the 3D forest is opt-in (?forest=1 or VITE_FOREST_SCENE=1), exactly as on the child page.
  // By default the landing shows the painted meadow with Sadiq on it, like the product (no forest chunk).
  const [forestOn] = useState(isForestEnabled);
  const canForest = webgl && forestOn;
  const [stageFailed, setStageFailed] = useState(false);
  const [mountForest, setMountForest] = useState(false);
  const [hintOn, setHintOn] = useState(false);
  const [greetDone, setGreetDone] = useState(false);

  const forest = canForest && !stageFailed;
  const live = forest && mountForest;
  // avatar-integ: without the forest, Sadiq still walks up the meadow path and waves (MeadowStage, as on the child's
  // Home), so the bubble and "tap Sadiq" have someone to point at. Its own ref: the landing's controlRef expects the
  // forest's { rt, look }. If the avatar fails, the plain living meadow below takes over.
  const meadowRef = useRef(null);
  const [meadowFailed, setMeadowFailed] = useState(false);
  const meadowAvatar = webgl && !canForest && !meadowFailed;

  const speech = useStageSpeech({ controlRef, t, live });
  const { later, say, activity, lastActive, speaking, bubble } = speech;

  // Mount the forest only once the page has painted and the device can draw it.
  useEffect(() => {
    if (!canForest) return undefined; // avatar-integ: meadow by default, no forest chunk and no model download
    const arm = () => {
      setMountForest(true);
      warmAvatar();
    };
    const id = 'requestIdleCallback' in window
      ? window.requestIdleCallback(arm, { timeout: 1200 })
      : window.setTimeout(arm, 400);
    return () => {
      if ('cancelIdleCallback' in window) window.cancelIdleCallback(id);
      else window.clearTimeout(id);
    };
  }, [canForest]);

  // He greets once: when the walk-in reaches the wave (at once if there is no walk to wait for).
  useEffect(() => {
    const greet = () => {
      if (greeted.current) return;
      greeted.current = true;
      lastActive.current = performance.now();
      const ms = say(t.greetings[time]);
      later(() => {
        setHintOn(true);
        setGreetDone(true);
      }, ms + HINT_DELAY_MS);
    };
    if (!forest && !meadowAvatar) {
      const id = window.setTimeout(greet, 1700);
      return () => window.clearTimeout(id);
    }
    const walker = forest ? controlRef : meadowRef; // avatar-integ: the meadow walk-in greets at its wave too
    const poll = window.setInterval(() => {
      const w = walker.current?.walk;
      if (w && w.state >= WALK_WAVE) greet();
    }, 150);
    const fallback = window.setTimeout(greet, GREET_FALLBACK_MS);
    return () => {
      window.clearInterval(poll);
      window.clearTimeout(fallback);
    };
    // The greeting is said once; a language or time change later does not repeat it.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [forest, meadowAvatar]);

  const stagePoint = useCallback((client) => {
    const r = rootRef.current?.getBoundingClientRect();
    return r && client ? { x: client.x - r.left, y: client.y - r.top } : null;
  }, []);

  // Idle life: a glance (and sometimes a small wave) every 12 to 18 s while nobody touches anything,
  // and one nudge toward the lantern after 20 s.
  useEffect(() => {
    if (!live || !greetDone) return undefined;
    let timer = 0;
    const beat = () => {
      const c = controlRef.current;
      const idleFor = performance.now() - lastActive.current;
      if (c && !document.hidden && idleFor > 6000) {
        const cta = Math.random() < 0.5 ? stagePoint(ctaPoint?.()) : null;
        c.look(cta || { name: 'bird' }, 1.6);
        if (Math.random() < 0.6) later(() => controlRef.current?.wave(), 500);
      }
      timer = window.setTimeout(beat, 12000 + Math.random() * 6000);
    };
    timer = window.setTimeout(beat, 12000 + Math.random() * 6000);
    const nudge = window.setTimeout(() => {
      if (performance.now() - lastActive.current < NUDGE_AFTER_MS - 1000) return;
      say(t.nudge, { hold: 3500 });
      controlRef.current?.look({ name: 'lantern' }, 2.2);
    }, NUDGE_AFTER_MS);
    return () => {
      window.clearTimeout(timer);
      window.clearTimeout(nudge);
    };
    // t is read when the nudge fires; a language switch just changes its text.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [live, greetDone]);

  // Tap Sadiq: he hops and says it, then the page starts the demo (a beat later, so the hop is seen).
  const startFromScene = useCallback(() => {
    activity();
    setHintOn(false);
    if (starting.current || busy) return;
    starting.current = true;
    if (forest) controlRef.current?.hop();
    else meadowRef.current?.hop?.(); // avatar-integ
    soundBus.play?.('hop');
    say(t.letsTalk, { hold: 1500 });
    later(() => {
      starting.current = false;
      onStart?.();
    }, reduced ? 150 : 450);
  }, [activity, busy, controlRef, forest, say, t.letsTalk, later, reduced, onStart]);

  const hint = (
    <span className="demo-hint" data-show={hintOn ? 'true' : 'false'} aria-hidden="true">
      <Hand className="demo-hint-hand" strokeWidth={2} aria-hidden="true" />
      {t.hint}
    </span>
  );

  return (
    <div
      ref={rootRef}
      className={`demo-scene ${className}`}
      data-demo-scene={forest ? 'forest' : 'meadow'}
      data-arch=""
      onPointerDown={activity}
    >
      {/* Base layer: the painted meadow. It is the poster while the forest loads and the fallback. */}
      {forest ? (
        <img
          src={MEADOW_IMAGE}
          srcSet={MEADOW_SRCSET}
          sizes={MEADOW_SIZES}
          fetchPriority="high"
          alt=""
          aria-hidden="true"
          draggable="false"
          className="pointer-events-none absolute inset-0 h-full w-full select-none object-cover object-[47.5%_center]"
        />
      ) : meadowAvatar ? (
        /* avatar-integ: the child's Home stage, Sadiq walking up the meadow path (its own living meadow under him) */
        <SceneBoundary onFail={() => setMeadowFailed(true)}>
          {/* z-0 + no pointer events: the stage's own z-10 content layer must not cover the scene's tap button */}
          <div className="pointer-events-none absolute inset-0 z-0 flex">
            <MeadowStage phase="home" walkControlRef={meadowRef} />
          </div>
        </SceneBoundary>
      ) : (
        <MeadowLife anchored={false} /> /* the living meadow, with the still image under it as poster and fallback */
      )}

      {!forest ? (
        <>
          {/* Warm sun glow and two slow clouds give the flat painting some depth. */}
          <div
            aria-hidden="true"
            className="pointer-events-none absolute -top-10 -end-10 h-56 w-56 rounded-full"
            style={{ background: 'radial-gradient(circle, rgba(255,226,140,0.85), rgba(255,226,140,0) 68%)' }}
          />
          <div aria-hidden="true" className="pointer-events-none absolute inset-x-0 top-6 h-24">
            <div className="demo-cloud absolute start-[8%] top-2 h-8 w-32 rounded-full bg-white/70 blur-md" />
            <div
              className="demo-cloud absolute end-[14%] top-10 h-6 w-24 rounded-full bg-white/60 blur-md"
              style={{ animationDelay: '-6s' }}
            />
          </div>
          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-x-0 bottom-0 z-[2] h-1/3"
            style={{ background: 'linear-gradient(0deg, rgba(15,45,28,0.28), transparent)' }}
          />
          <button type="button" className="demo-scene-tap" onClick={startFromScene} aria-label={t.labels.sadiq} />
        </>
      ) : null}

      {/* Not drawn yet, or no forest: the same bubble and hint, placed by CSS instead of by Sadiq's head. */}
      {!live ? (
        <>
          {bubble ? <StaticBubble bubble={bubble} /> : null}
          {hint}
        </>
      ) : null}

      {live ? (
        <SceneBoundary onFail={() => setStageFailed(true)}>
          <Suspense fallback={null}>
            <div className="absolute inset-0 flex">
              <ForestStage
                phase="wide"
                timeOfDay={forcedTime || undefined}
                avatarSpeaking={speaking}
                walkControlRef={controlRef}
                walkPreset="landing"
                interactive
              >
                <StageLayer controlRef={controlRef} t={t} speech={speech} onTapSadiq={startFromScene} />
                {hint}
              </ForestStage>
            </div>
          </Suspense>
        </SceneBoundary>
      ) : null}
    </div>
  );
};

export default DemoHeroScene;
