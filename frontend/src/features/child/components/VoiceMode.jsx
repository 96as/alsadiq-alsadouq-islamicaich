import { Suspense, lazy } from 'react';
import { Loader2 } from 'lucide-react';
import MeadowImage from './ambient/MeadowLife'; // the living meadow; it keeps ./MeadowImage as poster and fallback
import { lookdevEnabled } from './avatar/lookdev/lookFlag';

// Lazy-load Avatar so the three.js + GLB bundle only downloads when voice mode opens.
const Avatar = lazy(() => import('./avatar/Avatar'));

function AvatarSpinner() {
  return (
    <div className="flex h-full w-full items-center justify-center">
      <Loader2 aria-hidden="true" className="h-10 w-10 text-primary-strong motion-safe:animate-spin" strokeWidth={1.5} />
    </div>
  );
}

/**
 * VoiceMode, the big friendly avatar stage.
 *
 * Container contract (for the avatar team): this <section> is a flex child
 * (`flex-1 min-h-0`) of the page column, so it takes ALL the height left
 * between the header and the source-card rail / bottom, and the full width of
 * its column (phone: viewport width minus 16px padding; lg+: viewport minus
 * the 22rem rail). It has a min height of 18rem, rounded-4xl corners and
 * clips (overflow-hidden). The avatar layer is `absolute inset-0` inside it,
 * so size the canvas to 100% width and height of its parent, nothing else.
 *
 * Props:
 *   agentSpeaking  {boolean}   fallback speaking flag, forwarded to Avatar.
 *   agentState     {string}    lk.agent.state (listening, thinking, speaking), forwarded to Avatar.
 *   getAudioLevel  {() => number} live level of the agent's voice, forwarded to Avatar for the jaw.
 *   getLipsync     {() => object|null} live viseme state of the agent's voice (lip-sync), forwarded to Avatar.
 *   getAvatarContext {() => object|null} the avatar signal store's context (listen/talk styles, search), forwarded to Avatar.
 *   lang           {'ar'|'en'} the child's language, for the search hologram and its status line.
 *   controlRef     {object} optional ref that receives the avatar's dev handle (play, hold, look). The showcase uses it.
 *   forest         {boolean}   the forest stage (task 06b) already draws the scene and the
 *                  avatar behind this section, so skip the meadow image and the Avatar here.
 *   staged         {boolean}   avatar-integ: MeadowStage already draws the full-bleed meadow and the avatar behind this section;
 *                  skip the image and the Avatar and drop the card (no border, no corners, no fill).
 *   status         {ReactNode} optional status pill(s), shown top centre.
 *   children       {ReactNode} mic/speaker controls, overlaid at the bottom.
 */
const VoiceMode = ({ agentSpeaking, agentState, getAudioLevel, getLipsync, controlRef, getAvatarContext, lang, forest = false, staged = false, status = null, children }) => { // avatar-integ: lipsync + context props, staged
  const external = forest || staged; // somebody else draws the scene and the avatar behind this section
  return (
    <section
      aria-label={lang === 'en' ? 'Al-Sadiq' : 'الصديق'} // i18n // avatar-integ
      className={staged
        ? 'relative flex min-h-[18rem] flex-1 flex-col'
        : `relative flex min-h-[18rem] flex-1 flex-col overflow-hidden rounded-4xl border border-border shadow-[0_4px_16px_var(--color-shadow)] ${forest ? '' : 'bg-info-soft'}`}
    >
      {!external && (
      <MeadowImage anchored={!lookdevEnabled()} />
      )}

      {/* The transparent avatar canvas renders above the lightweight panorama still. */}
      {!external && (
      <div className="absolute inset-0 z-0">
        <Suspense fallback={<AvatarSpinner />}>
          <Avatar isSpeaking={agentSpeaking} agentState={agentState} getAudioLevel={getAudioLevel}
            getLipsync={getLipsync} controlRef={controlRef} framing="meadow"
            getAvatarContext={getAvatarContext} // 06-avatar-context
            lang={lang} // 06-avatar-context
          />
        </Suspense>
      </div>
      )}

      {/* Status pills overlay at the top */}
      {status ? (
        <div className="relative z-10 flex shrink-0 justify-center px-4 pt-4">{status}</div>
      ) : null}

      {/* Spacer, pushes controls to the bottom */}
      <div className="relative z-10 flex-1" />

      {/* Controls overlay at the bottom (mic, speaker buttons from ConversationPage) */}
      {children && (
        <div className={staged ? 'mc-controls' : 'relative z-10 flex shrink-0 items-center justify-center gap-6 pb-4'}>
          {children}
        </div>
      )}
    </section>
  );
};

export default VoiceMode;
