/**
 * AuroraBackground, the warm page backdrop for the child and parent shells.
 *
 * Mirrors the mobile ScreenBackground: a cream to green token gradient with
 * two soft colour washes. Pure decoration, static (no animation), and it
 * follows the light and dark tokens automatically.
 */
const AuroraBackground = () => (
  <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
    <div className="absolute inset-0 bg-gradient-to-b from-bg-1 via-bg-2 to-bg-3" />
    <div className="absolute -top-24 -start-24 size-96 rounded-full bg-accent-soft opacity-60 blur-3xl" />
    <div className="absolute -bottom-32 -end-24 size-[28rem] rounded-full bg-primary-soft opacity-60 blur-3xl" />
  </div>
);

export default AuroraBackground;
