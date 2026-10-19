# Showcase live: animated avatar on the team site

Branch `hk/showcase-live` = `hk/06-avatar-live` + a merge of `hk/showcase`.

## Done
- The /page/ showcase now uses the animated avatar (Blender clips, bone-eyelid blink, 14-viseme lip sync, look-at, planted-feet walk-in).
- New page `/meadow` ("Meadow, current background" / Arabic title): the animated avatar on the lead's meadow (`backgrounds/fantasy-meadow.webp`), built from the real child voice screen parts (AuroraBackground, VoiceMode, LevelCard, GlassIconButton). Chips: idle, listening, thinking, speaking. Buttons: wave, look around, blink.
- Speaking uses a made-up voice (`avatar/dev/fakeSpeech.js`): one syllable clock gives both the level (jaw) and the 14 viseme weights. No audio, no Web Audio, no network.
- The index lists the meadow card first, tagged as the product's current look. The forest card is "Experiment: 3D forest (to discuss)".
- `avatar-component-preview.html` and `avatar-preview.html` use the animated GLB and the base path.
- The animated model URL, the sidecar JSON and the dev-audio paths go through `assetUrl()`.

## Decisions
- Merge commit, not a rebase, so both histories stay.
- A press on Wave or Look around waits for the current one-shot (the avatar plays one gesture at a time) instead of being dropped. The button shows as pressed while it waits.
- In showcase builds the audition bar is hidden when there are no audio clips.
- Review: the meadow panel puts the chips in fixed grids (4 states, 3 actions), so on a phone the stage keeps about 75% of the screen and Sadiq stands clear of the mic, close to the real child screen.

## Build and run
```
cd frontend
MSYS_NO_PATHCONV=1 VITE_SHOWCASE=1 VITE_FOREST_SCENE=1 npx vite build --base /page/
npx vite preview --base /page/ --port 5341
```
Output: `frontend/dist-showcase` (about 13 MB; avatar.glb, avatar-round7.glb and the forest drop-folder README stay out).

CSP on /page/ is satisfied: no inline scripts, no eval, everything same-origin except Google Fonts.

## Tested
Reviewer (Opus): same checks against `vite preview --base /page/` and a static server sending the /page/ CSP header, at 1440x900, 1024x768, 768x1024, 390x844 and 360x740, plus reduced motion and pointer look-at. No CSP violations, errors or 4xx; no key patterns in the dist.

Edge (Playwright, channel msedge) at 1440x900 and 390x844: index, meadow (all chips, idle animation plays, blink, visemes and jaw move while speaking, wave and look around), /dev/forest walk-in (Walk clip), landing, both HTML entries. No console errors, no 4xx, no foreign hosts except Google Fonts. Lint clean.

## Left
- The forest page still has no working voice in the showcase (no server).
- THREE.Clock deprecation warning comes from three itself.
- The landing hero still shows the 3D forest walk-in (the experiment), not the meadow.
- On a phone the forest dev panel covers the avatar (`?panel=0` hides it).
- The back link from the meadow lands on `/page` (no slash) through the router; a reload there depends on the host.
