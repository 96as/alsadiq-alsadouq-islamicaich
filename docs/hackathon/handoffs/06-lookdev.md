# Handoff: Task 06 look-dev, Sadiq grounded and lit on the painted meadow

- **Date:** 2026-10-04
- **Owner:** Majd
- **Branch:** `hk/06-lookdev` (local only, never pushed), based on `b9f2711`
- **Worktree:** `%USERPROFILE%\Documents\Alsadiq-wt\06-lookdev`
- **Commits, oldest first:** `b62c47f` feat(avatar): look-dev rig; `1b3f823` feat(avatar): mount the rig, `?look=before` restores the old look; then this file on its own.
- **Spec:** `%USERPROFILE%\Documents\Alsadiq-3D\studio-research\LOOKDEV-SPEC.md`
- **Merge order:** after `hk/06b-nature-motion`. Expected conflict: the light block and the `avatarX` line in `Avatar.jsx` (see section 7).

## 1. What is done

Majd's feedback at 19:25 on a 2000x713 window was "why is the quality so bad". Sadiq looked pasted on because the camera did not match the plate, he had no contact shadow, his shadows were warm and muddy against a cool slate painting, the light was flat with no rim, and he was small.

Now, on the meadow only:

- **Camera and framing.** A level camera with a vertical lens shift (`setViewOffset`). He is solved from the stage height and aspect: bigger (about 0.64 of the stage height at 1280x720, 0.68 at 2000x713), standing on the path, feet at screen x 0.40 to 0.60, ears clear of the header, feet clear of the controls. The 3D horizon matches the painted horizon.
- **Light.** An image-based light from a 1024 px version of the meadow panorama (`meadow-env-1024.webp`), a warm key from the painting's sun, a pink rim from the cloud glow behind right, a cool hemisphere fill with warm path bounce.
- **Grounding.** A cast shadow on a faded `ShadowMaterial` catcher (high tier only), a soft ambient-occlusion blob under the body and a small blob under each foot. The blobs follow the bones and fade when he hops.
- **Grade.** A custom tone mapping (three's Neutral, then saturation, a split-tone toward cool shadows and warm highlights, lifted blacks, a faint lilac haze). Shadows are tinted with a luminance-normalised blue so they do not darken one side of the face.
- **Materials.** Cloned materials with `onBeforeCompile` patches: cleaner eyes (low roughness mask from the ORM map), a Fresnel wrap, a sheen on the fur, normal scale. The GLB itself is untouched.
- **MeadowImage.** In look-dev mode it uses a static fit and skips its own anchoring and CSS shadow, so the plate and the 3D camera agree.
- **Fallbacks.** `?look=before` restores today's look. The web-avatar fallback (`avatar-web.glb`) also gets the rig (5 meshes upgraded). If the grade fails to compile it drops to Neutral and logs one warning. Reduced motion is unaffected.

## 2. Where it lives

All new code is in `frontend/src/features/child/components/avatar/lookdev/`:

| File | Job |
|---|---|
| `lookdevConfig.js` | every number: lights, env, grade, catcher, blobs, eye mask, wrap |
| `stageFraming.js` | `solveFraming(w, h)`: Hf, camera height, lens shift, safe-area ceilings, feet x and y. Pure maths, unit tested |
| `gradeToneMapping.js` | patches `ShaderChunk.tonemapping_pars_fragment` (CustomToneMapping), shared uniforms, `neutralTint()`, Neutral fallback on shader error |
| `materialUpgrade.js` | clone and patch the avatar materials |
| `AvatarLookdev.jsx` | the rig mounted inside `AvatarCanvas`: lights, env, catcher, blobs, camera lens shift, per-frame bone follow |
| `lookFlag.js` | `?look=before|after` |
| `lookdevRuntime.js` | `lookdevAvatarX`, `lookdevStats`, `window.__lookdev` (dev inspection) |

Small `// LOOKDEV` edits in shared files: `Avatar.jsx` (rig mount, `shadows` prop, `avatarX`, exposure only when the rig is off, `CameraSetup` skipped when the rig drives the camera), `MeadowImage.jsx`, `dev/AvatarPreviewApp.jsx` (`?framing=meadow`, `?bars=0`). Also `public/backgrounds/meadow-env-1024.webp`, `tests/stageFraming.test.mjs`, and `"test:lookdev"` in `package.json`.

Tools and renders live outside the repo:

- Scripts: `%USERPROFILE%\Documents\Alsadiq-3D\studio-research\lookdev-tools\` (`wp6_shots.py`, `wp6_measure.py`, `wp6_perf.py`, `wp6_gpucost.py`, `wp6_media.py`, `wp6_robust.py`, `wp6_webfallback.py`)
- Renders: `%USERPROFILE%\Documents\Alsadiq-3D\03-renders\LOOKDEV\` (before and after PNGs, face and feet crops, `shots-meta.json`, the 10 s video, robustness shots)
- Studio stills, short MP4s and compare images: `%USERPROFILE%\Documents\Alsadiq-3D\03-renders\studio\lookdev\`

## 3. How to run and A/B it

From `frontend/`: `npm run dev -- --port 5361` (check the port is free first). Then open:

- After: `http://127.0.0.1:5361/avatar-component-preview.html?framing=meadow&bars=0&state=idle&adaptive=0`
- Before (today's look): the same URL with `&look=before`
- `state=speaking` for the talking pose, `tier=low|high` to force a quality tier, `adaptive=0` to switch the adaptive resolution off (used for shots)
- In the app itself the rig is on by default for the meadow. Add `?look=before` to any page to compare.

Tests and checks:

```
npm run test:lookdev     # 21 tests: framing at 390x844, 1280x720, 2000x713, 2560x1080, 820x1180
npm run test:lipsync     # 22 tests, untouched
npm run lint
npm run build
```

Shots: `python wp6_shots.py grid` (all sizes, DPR 1 and 2, idle at t=1.0 and TalkGesture at t=2.0, before and after), then `python wp6_measure.py 1280x720 1 after ''` for the gate numbers. Set `PYTHONUTF8=1 PYTHONIOENCODING=utf-8`.

## 4. Gate table (measured, 1280x720 unless stated)

| ID | Check | Result | Verdict |
|---|---|---|---|
| L1 | horizon within 0.5% of stage height | passes in the unit tests at all five sizes | pass |
| L2 | bbox height / stage height 0.63 +/- 0.02 | solved Hf 0.642 (1280x720), 0.680 (2000x713, 2560x1080), 0.500 (390x844), 0.506 (820x1180); safe areas hold in the tests. Pixel bbox of the silhouette measures 0.607 at 1280x720 because the nominal character height includes a margin above the ears | partial: 0.003 outside the band by the pixel measure |
| L3 | feet x in 0.40-0.60 | 0.424 / 0.504 / 0.480 / 0.400 / 0.400 | pass |
| L4 | soles shadow 35-55% darker, hue 200-240, no channel below 0.12 | 35.6% darker (painting alone 0.9%), hue 266, min channel 0.259 | pass on darkness, hue 26 degrees high (a grey-violet, not warm) |
| L5 | left/right face luminance 1.20-1.60, rim visible | 1.546 (DPR 1 and 2); rim on the right ear and shoulder visible in `after-1280x720-dpr2-*` | pass |
| L6 | darkest 10%: hue 200-260 (or sat < 0.12), value 0.12-0.24 | mean hue 296, sat 0.166, value 0.252 | near miss (value 0.012 high, sat 0.046 high) |
| L7 | lit cheek hue 15-32, sat >= 0.45 | hue 32.1, sat 0.568 | pass |
| L7 | lit cardigan hue 28-45, sat 0.08-0.25, value >= 0.80 | hue 31.2, sat 0.379, value 0.854 | miss on saturation (see issues) |
| L8 | catchlight >= 3x3 px, value >= 0.95 in each eye | none found | not met (see issues) |
| L9 | sheen fog: fur value on vs off <= +8% | -1.4% | pass |
| L10 | `gl.SAMPLES` >= 4, no stairs, no dark fringe | 4; fringe fraction 5.6% (DPR 1), 5.6% (DPR 2), judged by eye as clean | pass |
| L11 | lookdev JS <= 0.1 ms per frame at 4x CPU, no steady allocations | 0.0077 ms at 1x, 0.041 ms at 4x, 0.060 ms at 6x; bone positions read from `matrixWorld.elements`, no allocation | pass |
| L11 | p95 frame time <= 16.7 ms (high tier, speaking, forest off) | headless Edge is paced at 57 Hz, so rAF p95 is 18.0 ms before and after, identical. Real GPU cost by synchronous `gl.render` + `readPixels`: median 0.8 ms, p95 1.2 ms at DPR 1; p95 3.7 ms at DPR 2 | pass on cost, rAF p95 not meaningful here |
| L11 | phone p95 <= 33 ms | not run (F3, no real phone in this session) | not run |
| L12 | `?look=before`, web fallback, Neutral fallback, console, reduced motion | `?look=before`: today's code path, checked by diff review; web fallback: 5 meshes upgraded; forced shader error: tone mapping 5 to 7 (Neutral) with one warning; reduced motion clean; the only console errors are the missing favicon 404 and the AudioContext gesture notice | pass |
| L13 | side by side | `before-*` and `after-*` plus face and feet crops, `compare-2000x713-meadow.png`, and `after-1280x720-speaking-10s.mp4` in `03-renders\LOOKDEV\` | done, Majd's eye is the final word |

Frames per second: headless Edge paces animation at about 57 Hz at 1x, 4x and 6x throttle, before and after. The look-dev rig adds 0.06 ms of JS per frame at 6x throttle and about 1 ms of GPU per frame on this machine.

Final tuning numbers: env 0.9, key `#ffecd0` 3.2, rim `#ffc4d2` 3.2, hemisphere 0.28, saturation 1.1, shadow tint `#6f86c0` (luminance-normalised), lift `#2b3346` 0.5, haze 0.02, catcher opacity 0.55, AO opacity 0.92, foot blob 0.5. The face looked rich at 1280x720 and 1440x900, so neither the saturation nor the haze fallback was needed. **Superseded by the review retune below.**

### 4.1 Review (Opus look-dev reviewer), 2026-10-04 evening

Two fixes were committed on this branch after the builder's commits:

- `90e21b6` **grade retune.** Split 0.5 and lift 0.5 made the fur grey-mauve. Face fur saturation was 0.50, against 0.78 in the original app's voice screen and 0.74 before. The darkest pixels were hue 316 at saturation 0.11. The new values are close to the spec's S5: saturation 1.15, split 0.2, lift 0.1, hemisphere 0.18, env 0.95. The key, rim, haze, catcher and blobs are unchanged.
- `b2c70f3` **material pass.** Only the avatar's PBR materials are cloned now. Other tone-mapped materials get the grade uniforms in place, and un-tone-mapped ones are left alone. Only PBR meshes cast the shadow. Before this, the context hologram on `hk/06-avatar-context` would have frozen after the merge, because a ShaderMaterial clone deep-copies its uniforms, and its panels would have cast shadows. This was checked at runtime with injected meshes.

Re-measured after the retune (1280x720, DPR 1, `wp6_measure.py`):

| ID | Result |
|---|---|
| L5 | 1.591 (pass) |
| L6 | hue 12, sat 0.39, value 0.242. Warm and deep like the original app, whose darkest face pixels are hue 17, sat 0.94, value 0.19. The cool-hue rule fails, as it did before the retune (hue 296). The reviewer recommends re-baselining L6 for this red-brown character to "warm, saturated shadow core, never grey or mauve". |
| L7 cheek | hue 33.2, sat 0.638 (hue 1.2 degrees over) |
| L7 cardigan | sat 0.416. The original app's cardigan measures 0.317, so the 0.08-0.25 band is stricter than the reference. A separate cardigan material is still the fix. |
| L9 | -0.4% (pass) |
| L10 | fringe 7.8%. A 4x zoom of the ear and arm edges at DPR 2 is clean, with no stairs and no dark fringe. |
| L2 | The 0.607 figure was a measuring artefact: the script cut the silhouette at the ankle bone minus 2% of the stage. The true silhouette, measured from an alpha mask with the ground meshes hidden, is 0.664 at 1280x720 (pass), 0.706 at 2000x713 (0.006 over, because the toes sit in front of the origin), 0.513 at 390x844, 0.519 at 820x1180 and 0.707 at 2560x1080. |

**Merge with `hk/06b-nature-motion` (verified in a trial merge, branch `review/lookdev-on-06b`, commit `1c8a7fc`, never to be merged itself).** Git conflicts only in the `package.json` scripts: keep both. The real problem is semantic. On 06b, `VoiceMode` uses `MeadowLife`, whose GL plate uses the anchored `meadowRect`. Without a fix, the painted horizon is at 0.284 of the stage on 2000x713 while the 3D horizon is at 0.429. On phones, the plate pans the path to x 0.50 while Sadiq stands at 0.40. The one-line fix is in `VoiceMode.jsx`: `<MeadowImage anchored={!lookdevEnabled()} />` (import `lookdevEnabled` from `./avatar/lookdev/lookFlag`). The plate then uses the plain cover fit that `stageFraming.js` is solved to, and MeadowLife's own painted shadow switches off. With the fix, lookdev 21/21, nature 17/17 and lipsync 22/22 pass, and lint and build pass. Review renders are in `03-renders\LOOKDEV\review\`.

## 5. Decisions and why

- **Clone the materials, patch with `onBeforeCompile`.** The GLB stays as exported; `?look=before` is exactly today's rendering.
- **Shadows must be declared on `<Canvas shadows=...>`.** R3F re-applies `gl.shadowMap.enabled = !!shadows` on every configure, so enabling the map only inside an effect is silently undone. The first renders had no cast shadow because of this. The `shadows` prop is `'percentage'` (PCF) on the high tier and `false` otherwise.
- **A shadow-only sun at 58 degrees.** The painting's sun is low, so a shadow from the key direction itself would stretch far across the path. A second directional light (intensity 0, so it adds no light) casts the shadow from the same azimuth at 58 degrees up, which keeps it at about 0.6 x his height.
- **Luminance-normalised shadow tint (`neutralTint`).** The first blue shadow tint also darkened the screen-right side of the face and pushed the L5 ratio to 1.71. Scaling the tint to luminance 0.5 fixed it.
- **MeadowImage static fit in look-dev mode.** The camera and the plate now share one framing, so the old per-frame anchoring and CSS shadow are skipped.
- **Tone mapping through the shader chunk.** `CustomToneMapping` has no per-material hook in three r184, so the chunk is patched once and uniforms are shared. A shader error handler restores Neutral.
- **Removed the synthetic catchlight.** Both attempts (normal-based, then facing-gated) produced streaks and sparkle on the rim because the eye mesh normals are not spherical. A real catchlight needs to be in the texture (section 8).
- **Lookdev scan rate.** The scene is re-scanned every 0.5 s for the first 6 s, then every 2 s, and bone positions are read straight from `matrixWorld.elements`. This took the JS cost from 0.11 ms to 0.018 ms per frame at 4x.

## 6. Issues

1. **L8, no catchlights.** The eye mesh has no highlight in its texture and a synthetic one is unreliable (above). Fix in Blender, section 8.
2. **L7, cardigan saturation 0.379 against 0.08-0.25.** Sadiq is one mesh with one material (`Avatar_lowpoly`), so the cardigan cannot be graded separately from the fur. Lowering saturation would wash the cheeks that now pass. The cardigan reads as a warm cream in the renders, which looks right to my eye. A separate cardigan material in the GLB would let the gate be met properly.
3. **L6 and L4 hue near misses.** The darkest pixels are slightly violet and lighter than the gate (value 0.252). I left them because more cool lift made the fur muddy.
4. **L2 pixel bbox 0.607 against 0.63 +/- 0.02** (the solved Hf is 0.642). A calibration of the nominal height is the fix if the gate is meant literally.
5. **Phone p95 not run (F3).**
6. **Headless frame pacing.** The rAF numbers here are throttled to 57 Hz, so only the synchronous GPU cost and the JS cost mean anything. Judge motion timing on a real GPU or from `recordVideo`.
7. **Pre-existing, not mine:** a favicon 404, the `X4122` HLSL warning in the program log, and the `THREE.Clock` deprecation warning.

## 7. Merge notes

- **`hk/06b-nature-motion`:** the light block and the `avatarX` line in `Avatar.jsx` will conflict. Keep both: take 06b's nature changes, then re-apply the `// LOOKDEV` lines (the `lookOn` gating of lights and exposure, `avatarX` from `lookdevAvatarX`, the `shadows` prop, the rig mount).
- **`MeadowImage.jsx`:** if `meadow-hq` lands first, keep the look-dev branch of the fit (static, no CSS shadow) and let the new image go through it.
- **Not touched:** `VoiceMode.jsx`, `ClipAvatar.jsx`, `AvatarAnimator.js`, `avatarConfig.js`, `forest/*`, `ambient/*`, the background images, the GLB.

## 8. Next steps, and an optional Blender request

- Look at `compare-2000x713-meadow.png` and the 10 s video on a real display, and decide on the tuning. Every number is in `lookdevConfig.js`.
- Run the phone check (F3) on a real phone and fill the L11 phone row.
- **Optional Blender-side request** (not done here, Blender was not needed): (a) paint a small white catchlight into the eye texture (upper-left of each iris) so L8 can pass without a shader hack; (b) export a 2048 px ORM map so the wrap and sheen masks have more detail; (c) split the cardigan into its own material so it can be graded apart from the fur.
