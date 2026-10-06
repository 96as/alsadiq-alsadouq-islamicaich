# Handoff: Task 06, the avatar (web model and motion)

- **Date:** 2026-10-04
- **Owner:** Majd
- **Branch:** `hk/06-avatar` (local only, never pushed)
- **Worktree:** `%USERPROFILE%\Documents\Alsadiq-wt\06-avatar`
- **Task file:** `docs/hackathon/tasks/06-avatar.md`
- **Commits, oldest first:**
  1. `9f2b77c` feat(avatar): 0.7 MB meshopt web avatar and idle-screen preload
  2. `8aeb1f7` fix(avatar): keep the session screen alive if the model fails to load
  3. `986fcbe` feat(avatar): idle life, agent-state poses and audio-driven jaw
  4. `08058c3` fix(avatar): carry the jaw with the head, auto-gain the jaw, calmer thinking pose

## 1. What this is

The 3D squirrel companion on the child's voice screen (Al-Sadiq Al-Sadouq). Task 06 made it small, fast to show, and alive. It covers the avatar only. The forest background is task 06b, and the voice agent wiring is task 07.

Nothing here contains Quran, hadith or any other scripture. The motion files are pure animation numbers, as `AGENTS.md` requires.

## 2. What was built and why

### Part 1: the web model and the preload

| Before | After |
|---|---|
| `avatar-round7.glb`: 42,988,508 bytes (about 43 MB), 1,000,279 triangles, a 4096 px JPEG, a hidden backdrop plane with a 2400 px PNG | `avatar-web.glb`: 722,648 bytes (0.69 MB), 79,999 triangles, one 1024 px WebP (about 166 KB), no backdrop |

Why: the child waited on a spinner while a 43 MB file downloaded after the session had already connected.

- **Reproducible build.** `frontend/scripts/optimize-avatar-web.mjs` reads the 43 MB source and writes the web file. Steps: drop the backdrop, dedup, prune, weld, simplify to 80k triangles, quantise, resize the texture to 1024 px WebP, then meshopt-compress. Re-running it gave a byte-identical file (the reviewer checked the sha1).
- **Meshopt, not Draco.** The three.js loader that drei uses has a meshopt decoder built in. Draco would fetch its decoder from a CDN at runtime.
- **Script guards.** The script exits with an error if a required bone (`head`, `neck`, `jaw`, `arm.l`, `arm.r`) is missing, if there is no skin, if meshopt was not applied, or if the output is over 3 MB.
- **80k, not 65k triangles.** At 65k there were small speckles under the mouth.
- **Measured load.** On a throttled 4G-like link (9 Mbps, 170 ms round trip) download plus parse went from 38.8 s to 0.85 s. On localhost it went from 195 ms to 31 ms. This is download and parse only. It excludes GPU upload and the first frame, and it was measured in the preview page, not in the full app.
- **Preload.** `ConversationPage.jsx` has an effect on mount that runs `import('../../features/child/components/avatar/Avatar')`. When that module loads, the last line of `Avatar.jsx`, `useGLTF.preload(MODEL_URL, false)`, starts the model download. So both the chunk and the model arrive while the child is still on the idle "Start Session" screen. The reviewer confirmed in the built app at phone size that both are fetched before Start Session. With the model warm, the avatar was drawn 534 ms after `VoiceMode` mounted (545 ms cold on localhost, software rendering). The goal was under 1 s.
- **Fail-safe.** `Avatar.jsx` wraps the canvas in `AvatarErrorBoundary`. If the model fails to download or parse, the avatar renders nothing, the meadow background and the voice session keep working, and `useGLTF.clear(MODEL_URL)` removes the cached failure so the next session retries. Before this fix (commit `8aeb1f7`), suspend-react cached the failure and the whole page crashed to the app error screen. The reviewer tested a 404 on the model, then a remount that drew the avatar. With no WebGL at all the meadow stays and nothing crashes.

### Part 2: motion and agent states

- **Idle life.** Breathing at 0.25 Hz (shoulders, neck, spine), head sway, random glances, a slow weight shift, and arms pulled in from the A-pose with a slow sway. Hands sway.
- **Agent states.** `useLiveKitRoom.js` reads the agent participant attribute `lk.agent.state` and exposes `agentState` (default `initializing`). Values handled: `initializing`, `listening`, `thinking`, `speaking`, `idle`. The avatar eases into a distinct pose for each:
  - listening: tilts toward the camera and leans in a little, steady gaze;
  - thinking: head up and a little to the side, slower sway, no glancing;
  - speaking: nods and sways follow the voice, faster sway.
- **Jaw from the real voice.** `useLiveKitRoom.js` opens a Web Audio `AnalyserNode` on the agent's remote audio track (only when `track.source === Track.Source.Microphone`) and exposes `getAgentAudioLevel()`, which returns RMS or -1 when unavailable. The analyser is read-only and never connected to the speakers, so playback and the speaker mute are unaffected. Background audio can't move the jaw.
- **Jaw fallbacks.** With no analyser level, the jaw uses two sine waves. With no `agentState`, the old `isSpeaking` boolean still picks idle or speaking (`resolveMotionState` in `motionConfig.js`).
- **Reduced motion.** With `prefers-reduced-motion`, oscillations shrink to 20% and pose biases to 50%. The jaw is never reduced.
- **No per-frame allocations.** Rest rotations are plain numbers, bones are set with `rotation.set`, pose state lives in a preallocated `Float32Array`, and one shared quaternion is reused. Motion is frame-rate independent (`MathUtils.damp`).
- **Review fixes (`08058c3`).**
  - The jaw hangs off `neck > Bone.008`, not off `head`, so head turns left the lower face behind and the mouth gaped in the thinking pose. `Bone.008` now copies the head's turn from rest each frame.
  - Auto gain: the jaw is fully open at the loudest recent level. A fixed 0.13 ceiling left it open on about half the frames of real speech.
  - The thinking pose turns less (yaw 0.15, no roll) because the left cheek clipped the jacket collar.
  - The chest-scale breathing was removed. The torso is skinned to a static `neutral_bone`, so it only scaled the head and arms.

## 3. Where it lives

All paths are under the worktree root.

| What | Path |
|---|---|
| Web model (shipped) | `frontend/public/models/avatar/avatar-web.glb` |
| 43 MB source (kept, never edited) | `frontend/public/models/avatar/avatar-round7.glb` |
| Unused 43 MB duplicate | `frontend/public/models/avatar/avatar.glb` |
| Build script | `frontend/scripts/optimize-avatar-web.mjs` (npm script `avatar:optimize`) |
| Avatar component, `MODEL_URL`, preload, error boundary | `frontend/src/features/child/components/avatar/Avatar.jsx` |
| Per-frame motion | `frontend/src/features/child/components/avatar/useAvatarMotion.js` |
| Every tuning number, state poses, jaw settings | `frontend/src/features/child/components/avatar/motionConfig.js` |
| Component notes | `frontend/src/features/child/components/avatar/README.md` |
| Agent state and analyser | `frontend/src/hooks/useLiveKitRoom.js` |
| Prop pass-through | `frontend/src/features/child/components/VoiceMode.jsx` (props `agentState`, `getAudioLevel`) |
| Idle-screen warm-up, VoiceMode call | `frontend/src/pages/child/ConversationPage.jsx` |
| Preview pages (dev only, not in `vite build`) | `frontend/avatar-preview.html`, `frontend/avatar-component-preview.html` |

`MODEL_URL` is `/models/avatar/avatar-web.glb?v=web1`. Change the `?v=` value whenever the file changes, or browsers keep the old copy.

Dependencies added to `frontend/package.json` (devDependencies, exact pins): `@gltf-transform/core`, `@gltf-transform/extensions`, `@gltf-transform/functions` at 4.3.0, `meshoptimizer` 1.1.1, `sharp` 0.35.1.

## 4. How to run, test and verify

```
cd %USERPROFILE%\Documents\Alsadiq-wt\06-avatar\frontend
npm install
npm run dev
```

Previews (Vite prints the port, usually 5173):
- `/avatar-component-preview.html` is the real `Avatar` component with buttons for idle, listening, thinking and speaking. Query options: `?state=thinking`, `?speaking=1` (old boolean path, no agent state), `?level=none` (sine jaw fallback), `?level=synthetic` (fake voice level, the default).
- `/avatar-preview.html?model=/models/avatar/avatar-web.glb&view=three&jaw=0.2` is a raw model viewer. Views: `front`, `three`, `face`. Use `model=/models/avatar/avatar-round7.glb` to compare with the original.
- For reduced motion, emulate `prefers-reduced-motion: reduce` in the browser.

Checks:
```
npm run lint
npm run build
npm run avatar:optimize
```
- Lint was clean on this branch when I re-ran it for this handoff. Build was ok in the reviews, with only the existing large-chunk warning (the avatar chunk is about 953 kB, 255 kB gzip, separate from the main bundle).
- `npm run avatar:optimize` ends with `OK: within the 3 MB web budget.`

For browser click-tests use Playwright with `channel="msedge"`, and never click `mailto:` or `tel:` links (they open a Windows "Pick an app" popup).

Everything above was checked in the preview pages and the built app in Edge with software rendering (SwiftShader), with a mocked API. Screenshots are in `%USERPROFILE%\.claude\jobs\9adf820e\tmp\shots\` (`avatar`, `review-avatar`, `avatar-motion`) and `...\tmp\avatar-review\` (start with `thinking-before-after.png` and `states-compare-after.png`).

## 5. Decisions and why

- **Meshopt only, no Draco.** No CDN fetch at runtime, and the loader needs no setup.
- **Delete the backdrop in the build.** The page supplies its own background, so the plane and its PNG were dead weight.
- **Keep the 43 MB source files.** The web file is generated from them. `avatar.glb` is a duplicate and is not deleted yet because the team has not confirmed.
- **Warm the Avatar chunk, not a hidden canvas.** It is a six-line effect and already gives about 0.5 s to first draw. A hidden canvas would touch the layout that task 05 owns.
- **Error boundary inside `Avatar`.** The preload starts the download earlier than before, so a failure must never take down the session screen.
- **Real state wins over the boolean.** `isSpeaking` is only a fallback until the agent publishes `lk.agent.state`.
- **Auto gain for the jaw.** It works at any TTS volume without a hand-tuned ceiling.
- **Jaw carrier bone.** The model's rig is odd (jaw under the neck), so code compensates instead of editing the model.
- **No faked blink.** See section 8.
- **Small pass-through edits outside the avatar files.** `VoiceMode.jsx` (two props) and `ConversationPage.jsx` (a few lines). Without them the state can't reach the avatar.

## 6. Current status

| Task 06 step | Status |
|---|---|
| 1. Size under 8 MB | Done, 0.69 MB |
| 2. Preload | Partly done. Chunk and model warm on the idle screen. Hidden canvas warm-up and skeleton placeholder not done. |
| 3. Idle motion | Done |
| 4. Agent states | Done in code. Not tested in a live LiveKit session. |
| 5. Blink | Not done. The model can't support it. |
| 6. Mobile parity | Not done (optional) |
| Before and after network size and time-to-visible | Partly measured (numbers in section 2). Not measured in the full app after login. |

The two reviews were "ship-with-notes". Nothing is pushed. Tasks 06b and 07 are separate and were not touched by this work.

## 7. Known issues

- **Live path untested.** I did not connect to a real LiveKit room. `lk.agent.state` timing and the analyser on the real agent track need one real voice session. The code was checked against the livekit-agents 1.5.1 source (the attribute is published on the agent participant with `initializing`, `listening`, `thinking` or `speaking`; `idle` is declared but never set) and livekit-client 2.18.0.
- **Safari and iOS.** The analyser `AudioContext` is created outside the user click, so it may stay suspended. The jaw then falls back to the sine wave. It still works, but it is not driven by the voice.
- **Merge conflicts likely.** The 06b branch edits `ConversationPage.jsx`, `VoiceMode.jsx` and `Avatar.jsx`; 07 may edit `ConversationPage.jsx`. Expect small conflicts around the `VoiceMode` call and the Canvas.
- **`package-lock.json` note.** The original lock was out of sync with `package.json`, so `npm ci` failed on a clean checkout (missing platform packages such as lightningcss and rolldown bindings). I regenerated it with `npm install`. The lock diff in `9f2b77c` is about 1,300 added and 130 removed lines. The reviewer found no existing version changed and `npm ci` passed after it. If it conflicts with another branch, do not merge it by hand: take one side and re-run `npm install`. The 06b agent reverted its lock change, so that branch still has the old lock.
- **Docker.** The frontend image now also installs `sharp` (a dev dependency) at build time. It works on `node:20-slim` but the build is a little slower.
- **Big files in `dist`.** Both 43 MB GLBs are copied into `dist`. They are not downloaded at runtime.
- **Heavy material.** The model has clearcoat, so it uses the physical material. With `dpr` up to 2 and antialiasing, check frame rate on a real low-end phone, especially once the forest is added.
- **Stale README lines.** `avatar/README.md` still says the asset is `avatar.glb` in its "Asset location" section. The real file is `avatar-web.glb`.
- **Console noise in the preview.** A harmless favicon 404, and a `THREE.Clock` deprecation warning that comes from R3F, not from this code.
- **Frame rate unknown on real devices.** Only software rendering was tried.

## 8. Next steps and improvements, ordered by value

1. **Run one real voice session** and watch the avatar through listening, thinking and speaking. Check that the jaw follows the agent's voice. About 15 minutes. This is the one thing nobody has verified.
2. **Merge order with 06b and 07.** Decide the order, resolve the small conflicts in `ConversationPage.jsx`, `VoiceMode.jsx` and `Avatar.jsx`, and regenerate the lock file if it conflicts.
3. **Check frame rate on a real mid-range phone** with the forest on. If it is not smooth, lower `dpr` on the avatar canvas or drop antialiasing.
4. **Blink in Blender (about 2 h).** The reason there is none: `avatar-web.glb` has one mesh, one material, 0 morph targets, and its only bones are spine, shoulders, arms, hands, neck, `Bone.008`, head, jaw and legs. The eyes are painted into the face texture, so moving vertices only smears them. The plan, with the Blender MCP (inspect the scene first):
   1. Import `avatar-web.glb` (already decimated). Do not simplify again.
   2. Build two thin, skin-coloured eyelid caps just outside the painted eyes, with a material that samples the cheek colour.
   3. Preferred: weight each cap to a new bone `eyelid.l` or `eyelid.r` parented to `head`. Rest pose is lid raised and hidden in the brow. The closed pose rotates it over the eye. Alternative: one shape key `blink` on the caps.
   4. Export the GLB with skinning and morph targets. Then only quantise and meshopt-compress. `optimize-avatar-web.mjs` runs simplify, so add a flag or a second script that skips it. Simplify after shape keys breaks them.
   5. In `buildRig` in `useAvatarMotion.js`, add the eyelid bones (or `morphTargetDictionary.blink`) and drive a 150 ms close and open every 2.5 to 6 s, with an occasional double blink. Keep the jaw as is.
   Do not merge `enhancements/avatar-eyes-2`. It targets another model and disables the jaw.
5. **Disclosure.** The avatar was generated with Tripo. `docs/hackathon/CURRENT_STATE.md` section 9 still has a TODO for the avatar origin, and `docs/hackathon/tasks/10-demo-submission.md` lists it ("confirm the terms"). Someone must confirm the Tripo terms and add it to the third-party list for the submission, and tell the owner of task 10.
6. **Task 06 step 2 leftovers.** A skeleton placeholder instead of the spinner, and a hidden canvas warm-up. Low value, since first draw is already about 0.5 s. Coordinate with task 05.
7. **Delete `avatar.glb`** (the 43 MB duplicate) after the team confirms nothing uses it.
8. **Fix the stale lines in `avatar/README.md`** (asset name).
9. **Measure properly.** Network size and time-to-visible before and after in the full app, on a warm and a cold cache.
10. **Mobile parity (optional).** Apply the idle motion and agent states to `mobile/src/features/child/session/AvatarView.jsx`. Mobile already ships a 4.3 MB model built by `mobile/scripts/optimize-avatar.mjs`.
11. **Safari and iOS audio.** Create or resume the analyser `AudioContext` from the Start Session click so the jaw stays voice-driven.

## 9. Gotchas

- **Bone names lose their dots.** The three.js loader turns `arm.l` into `arml` and `pec.l.001` into `pecl001`. `buildRig` looks up both spellings. Any new bone code must too.
- **The jaw is not under the head.** It hangs off `neck > Bone.008`. Never rotate the head without the carrier logic in `useAvatarMotion.js`, or the mouth gapes.
- **The torso is static.** It is skinned to `neutral_bone`, so scaling or rotating the spine moves only the shoulders, arms and head.
- **Never simplify after adding shape keys or eyelid work.** Quantise and meshopt only.
- **Bump `?v=`** in `MODEL_URL` when the GLB changes.
- **Bone axes** (see the top of `motionConfig.js`): `rotation.x` positive pitches forward, `y` positive turns toward the viewer's right, `z` positive rolls the head to the viewer's left. Bones run along local +Y.
- **Pose limits are tight.** More than yaw 0.15 in the thinking pose pushes the cheek through the jacket collar.
- **Preview pages are dev only.** They are not part of `vite build`.
- **Never click `mailto:` or `tel:` links** in browser tests.
- **No keys in this work.** `.env` files are gitignored. Do not print them.
