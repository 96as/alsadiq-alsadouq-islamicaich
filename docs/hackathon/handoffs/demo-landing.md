# Handoff: demo landing and child idle stage (branch hk/demo-landing)

## Done
- Landing (`/`) rebuilt to `LANDING-SPEC.md`: time-of-day tokens (wall, ink, card, rim glide 900 ms,
  fixed sun and leaf tokens), the forest arch with Sadiq, one greeting per time of day word by word,
  hint chip, idle beats and a nudge, tap Sadiq (hop, "Let's talk!", then the demo starts), lantern,
  book (six values, no scripture) and bulbul as real 48 px buttons with verb labels, gaze, parallax
  tilt, CTA micro-interactions, ع|EN switch, time pill, judges card restyle, phone layouts (CTA
  visible without scrolling at 390x844 and 360x740).
- Child idle (`/child`): `ChildIdleStage.jsx` draws the same world over the forest stage with all
  states in Arabic and English: idle (greeting by name), connecting, could not start (shows the
  server's refusal message when there is one), voice unavailable (key becomes "Type to Al-Sadiq"),
  ended. It uses the shorter `'landing'` walk preset.
- P1: opt-in sound pill (`sound.js`, 1.6 KB gz, loaded on first press), minute-level palette
  blending, arch swell plus wall-coloured veil between landing and child (`transitionVeil.js`),
  ع/EN FLIP glide (blur out, flip, arch glides by transform, blur in; no layout shift measured),
  petals and fireflies spilling from the arch (`Spill.jsx`, 12 sprites, 7 on phones), sticky 56 px
  mini CTA on phones once the main one scrolls away.
- Perf: offscreen pause of the 3D loop, poster preload with a 900 px variant, both 43 MB GLBs deleted.

## Files
- Landing: `src/pages/DemoLanding.jsx`, `src/features/demo/{demo.css,copy.js,stageParts.jsx,
  useStageSpeech.js,DemoHeroScene.jsx,TimePill.jsx,SoundPill.jsx,soundBus.js,sound.js,Spill.jsx,
  transitionVeil.js,useSceneTilt.js,hooks.js}`.
- Child: `src/features/child/components/ChildIdleStage.jsx`, `src/pages/child/ConversationPage.jsx`
  (small diff: idle branch and the 'voiceoff' state).
- Forest: `forest/{ForestProps.jsx,useStageAnchor.js,meadowPoster.js}` and small edits to the stage.

## Decisions
- Sound is procedural WebAudio (breeze, far birds, crickets, soft UI blips), not CC0 files, so
  there is no `public/sounds/ATTRIBUTION.md`. Off by default, no AudioContext before the press; a
  remembered "on" starts at the first tap; it ends for good when a voice session starts.
- The arch-grow transition is the simple fallback allowed by the spec: arch scales 1.0 to 1.06 and
  blurs to 6 px under the veil (450 ms). The veil always goes away within 4 s.
- Arabic bottom nav skipped to avoid colliding with task 05 (the nav is global in ChildLayout and
  English only today). It does not collide with the idle key.
- Both GLBs (`avatar-round7.glb`, `avatar.glb`, 43 MB each) are deleted. To restore:
  `git show 6fc60f8:frontend/public/models/avatar/avatar-round7.glb > ...`. The shipped model is
  `avatar-web.glb`; `scripts/optimize-avatar-web.mjs` now reads the source from `frontend/avatar-src/`
  (gitignored).
- No voice or provider code was touched. No fallback to xAI.

## Run and test
- `cd frontend && npm run dev`, open `/` (try `?forest=0` for the painted meadow). Pick a time with
  the pill; tests can use `data-time`, `data-forest-stage`, `data-state`, `?walk=off|hop`.
- `npx eslint src` clean; `VITE_DEMO_MODE=1 npm run build` passes.
- Measured in Edge (headless, software GL), 4 times x desktop 1440x900 / phone 390x844 / 360x740 x
  AR and EN: Sadiq visible about 3 s, greeting 3.0 to 4.1 s after he is visible (limit 6), bubble tail
  10 px above the head, CTA fully on screen on all phones, wall colour changes per time, draw calls
  18 to 30 (limit 30), triangles 55k desktop and 34k phone (limit 63k), about 62 fps (rAF) on desktop.
- Main JS about +8.5 KB gz at the first measurement and a little more after the veil, spill and mini
  CTA (small); 3D chunk +5.8 KB gz; no new dependencies.
- Reduced motion: no spill, no CTA animation, walk skipped, greeting still shown. No WebGL: painted
  meadow with the bubble and CTA. Offscreen pause confirmed (stats stop when the arch scrolls away).
- Impeccable detect: only the deliberate spring easing remains (playful motion is wanted); the
  side-stripe on the problem card was removed.

## Open
- `voice_error` and `session_limit` LiveKit data topics are not read on the idle screen (that needs
  voice code). Refusals at session start are shown.
- Real parent dashboard screenshot, self-hosted fonts, discovery counter,
  meadow tap puffs and girih pattern (P2) are not done.
- Not checked on a real phone GPU or on the live site. Phone fps was only checked in software GL.
- Arabic bottom nav (see above).

## Review (Opus, 2026-10-04)
Checked in headless Edge on the real GPU (RTX, D3D11) at 1440x900, 768x1024, 390x844 and 360x740, Arabic and
English, all four times, with motion on and with reduced motion. The CTA to child flow was also run with the
demo API mocked. Fixed on this branch:
- Tap targets missed the props. `projectBox` in `ForestProps.jsx` transformed the shared vector in place, so it
  projected a view-space point: the book's button sat over Sadiq, the bulbul's over the lantern, and the value
  card, sleep letters and gaze used the wrong spots. The buttons now sit on the lantern, book and bird.
- Phone header: the short name was cut to "ا..." / "A...". The login pill now moves to the footer at 480 px and
  below, and the header packs tighter, so "الصديق" / "Al-Sadiq" fits down to 360 px.
- Phone CTA is full width (it was 223 px in Arabic), the loading label fits at 360 px in English, and the
  breathing ring grows mostly up and down so it stays on screen.
- The judges' step badges vanished for about 1.7 s after a language switch (the steps were keyed by their
  text). They now stay.
- The book's own hover tag covered its value card on desktop. It hides while the card is open.
- The sticky mini CTA covered the footer login pill at the bottom of the page. The shell has room for it.
- Petals and fireflies pause while the arch is scrolled out of view.
Still open: the bubble can hide the bulbul on its post during the greeting (phones and night); the English
bottom nav on /child (task 05); real phone GPU not tested.
