import { Suspense, lazy, useEffect, useState } from 'react';
import MeadowLife from './ambient/MeadowLife'; // the living meadow; it keeps ./MeadowImage as poster and fallback
import { lookdevEnabled } from './avatar/lookdev/lookFlag';
import { createStage, setStageInputs } from './avatar/meadowStage';
import { briefWave, tapHop } from './avatar/walkIn';
import { useReducedMotion } from '../../demo/hooks';
import './meadowScreens.css';

// avatar-integ: lazy, like VoiceMode's: three.js and the GLB only download when the child's page opens.
const Avatar = lazy(() => import('./avatar/Avatar'));

/**
 * The child's page on the painted meadow: one persistent stage behind every screen of the page (Home, the call, the
 * cards), so the camera can ease once from Home into the call framing and Sadiq never reloads between them.
 *
 *   Home (phase 'home')   Sadiq walks up the path and waves, then idles; now and then he strolls off and back.
 *   Call (phase 'call')   the camera eases ONCE into the call framing and stays steady for the whole session. There is no
 *                         zoom while he speaks or listens (the speaking close-up stays on the /page showcase).
 *
 * The painted meadow with its living layer is the default background. The 3D forest is opt-in (?forest=1).
 * Container contract: the section is a flex child (`flex-1 min-h-0`) of the page column and clips; the avatar canvas
 * is `absolute inset-0` behind the screen's own content (`children`).
 *
 * Props
 *   phase          'home' | 'call'
 *   hidden         true while the chat is open: the avatar stops drawing and is hidden (the meadow stays)
 *   walkControlRef the page's ref; filled with { walk, hop, wave } so the Home screen can read the walk and tap him
 *   the rest       forwarded to the Avatar (agent state, audio level, lip-sync, avatar context, language)
 */
export default function MeadowStage({
  phase = 'home',
  hidden = false,
  avatarSpeaking = false,
  agentState,
  getAudioLevel,
  getLipsync,
  getAvatarContext,
  lang,
  walkControlRef,
  children,
}) {
  const reduced = useReducedMotion();
  const [stage] = useState(() => createStage({ reduced: false })); // one stage per mount; the effect below feeds it `reduced`

  // The page sets the phase; the avatar's frame loop reads it.
  useEffect(() => {
    setStageInputs(stage, { phase, hidden, reduced });
  }, [stage, phase, hidden, reduced]);

  // Hand the Home screen the walk and two beats (a tap hop and a short wave); null again on unmount.
  useEffect(() => {
    if (import.meta.env.DEV) window.__stage = stage; // dev only: scripts/meadow-click-test.py reads the stage here
    if (!walkControlRef) return undefined;
    walkControlRef.current = {
      stage,
      walk: stage.walk,
      hop: () => tapHop(stage.walk),
      wave: () => briefWave(stage.walk),
    };
    return () => {
      walkControlRef.current = null;
    };
  }, [walkControlRef, stage]);

  return (
    <section data-meadow-stage="" data-phase={phase} className="relative flex min-h-0 flex-1 flex-col overflow-hidden bg-info-soft">
      <MeadowLife anchored={!lookdevEnabled()} />

      {/* The transparent avatar canvas renders above the lightweight panorama still. */}
      <div className="absolute inset-0 z-0" style={{ visibility: hidden ? 'hidden' : 'visible' }} aria-hidden={hidden || undefined}>
        <Suspense fallback={null}>
          <Avatar
            isSpeaking={avatarSpeaking}
            agentState={agentState}
            getAudioLevel={getAudioLevel}
            getLipsync={getLipsync}
            framing="meadow"
            walk={stage.walk}
            stage={stage}
            paused={hidden}
            getAvatarContext={getAvatarContext}
            lang={lang}
          />
        </Suspense>
      </div>

      <div className="relative z-10 flex min-h-0 flex-1 flex-col">{children}</div>
    </section>
  );
}
