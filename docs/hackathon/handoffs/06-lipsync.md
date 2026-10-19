# Handoff: Task 06 lip-sync, in-browser mouth and blink driver

- **Date:** 2026-10-04
- **Owner:** Majd
- **Branch:** `hk/06-lipsync` (local only, never pushed), based on `hk/demo-mvp` at `6fc60f8`
- **Worktree:** `%USERPROFILE%\Documents\Alsadiq-wt\06-lipsync`
- **Commits, oldest first:**
  1. `7fcee13` feat(avatar): in-browser lip-sync driver with viseme morphs and blinks
  2. `759c730` fix(avatar): cut lip-sync lag, skip analysis without morphs, test iOS resume
- **Plus this file**, committed on its own afterwards.
- Technical reference for the code itself: `frontend/src/features/child/components/avatar/lipsync/README.md`. This handoff does not repeat it.

## 1. What this is

A lip-sync driver for the 3D squirrel on the child's voice screen. It listens to the agent's voice in the browser, works out which of the 14 Oculus visemes the mouth should show, and writes the weights into the avatar's morph targets. It also runs a natural blink timer. There is no server, no TTS timing data and no new dependency: the DSP is plain JavaScript in one folder.

It works with any voice, Arabic or English, because it analyses the sound (formants, noise spectrum, loudness), not the text.

## 2. What was built and why

Why: today's `avatar-web.glb` only moves a jaw bone with the voice level. The new avatar from the 3D plan (`avatar-animated.glb`) has 14 viseme shape keys, so the mouth can shape itself. The 3D plan says visemes are "driven only by web code", and this is that code.

Parts, all in `frontend/src/features/child/components/avatar/lipsync/`:

| File | Job |
|---|---|
| `dsp.js` | 2048-sample FFT plus a 12 kHz LPC fit: loudness, voicing, formants F1 to F3, band shares, centroid, flux |
| `visemeClassifier.js` | raw weights: vowels from F1/F2, s/sh/ch/f from the noise spectrum, nasals from tilt, stop closures and bursts, co-articulation |
| `visemeSmoother.js` | damped pre-filter, then attack and release per viseme, sum capped at 1, `sil` takes the rest |
| `blinkScheduler.js` | blink every 2 to 6 s, 18 percent doubles, deferred during stressed syllables, pulled forward at a phrase end, no doubles with reduced motion |
| `visemeDriver.js`, `useVisemes.js` | tap an audio source with an analyser, read the newest state without allocating; resume the AudioContext on a tap (iOS) |
| `morphTargets.js`, `lipsyncRig.js` | bind morph names in a loaded scene and write the weights each frame; jaw fallback when there are no viseme morphs |
| `lipsyncConfig.js`, `visemes.js` | every tuning number, the name lists and `VISEME_GAIN` |
| `dev/` | the lab page at `/dev/lipsync` (dev server only) |

Wiring into existing files (small edits): `useLiveKitRoom.js` creates the driver on the existing AudioContext and agent source and exposes `getAgentLipsync`; `ConversationPage.jsx` and `VoiceMode.jsx` pass it down as `getLipsync`; `Avatar.jsx` accepts `getLipsync`, `morphNames`, `modelUrl`; `useAvatarMotion.js` creates a `LipsyncRig`; `ForestStage.jsx` forwards the prop; `App.jsx` adds the dev route; `package.json` adds `test:lipsync`; `.gitignore` adds `frontend/dev-audio/`.

Design choices that matter for the feel: the driver adds about 60 ms of mouth lag (79 ms worst), no flutter above 10 Hz, and one analysis costs 0.07 ms per frame (0.7 ms with a 6x CPU throttle).

## 3. Where it lives

- Code: `frontend/src/features/child/components/avatar/lipsync/`
- Tests: `frontend/tests/lipsync.test.mjs`
- Scripts: `frontend/scripts/lipsync-probe.mjs` (synthetic probe), `frontend/scripts/lipsync-clips.mjs` (per-clip viseme shares or a frame trace)
- Lab clips (not in git): `frontend/dev-audio/`
- Screenshots and measurement output: `%USERPROFILE%\Documents\Alsadiq-wt\shots\lipsync\` and `...\shots\lipsync-review\`
- The new avatar and its plan: `%USERPROFILE%\Documents\Alsadiq-3D\` (`PLAN-3D.md`, export goes to `04-exports\avatar-animated.glb` with an `avatar-animated.json` sidecar listing the morph names)

## 4. How to run and test it

Tests and lint (from `frontend/`):

```
npm run test:lipsync     # 22 tests, about 0.2 s
npm run lint
npm run build            # dev page and dev-audio must not appear in dist
```

The lab:

1. Copy the audition mp3 files into `frontend/dev-audio/`. A set is in `%USERPROFILE%\Documents\Alsadiq-wt\audition-out\` (the worktree already holds 15 files). Optionally add a `lines.json` with the clip text.
2. `npm run dev -- --port <free port>` and open `/dev/lipsync`.
3. Pick a clip. You get live bars, a 2D mouth, an offline timeline, a mouth strip every 0.1 s, a reduced motion switch and a toggle for the real avatar.
4. Browser checks: Playwright with `channel: "msedge"`. Never click mailto or tel links.

Per-clip statistics: export decoded PCM from the lab page into `frontend/dev-audio/pcm/`, then `node scripts/lipsync-clips.mjs [clip from to]`. After changing `CLASSIFIER`, vowels should be about 35 to 40 percent of the active shapes and PP under 10 percent.

## 5. Decisions

- **No dependency.** Own FFT and LPC. Licence and lockfile questions do not arise; `package-lock.json` is unchanged.
- **Analyse the sound, not the text.** Works for Arabic and English and needs nothing from the agent. Cost: it follows what the voice sounds like, so it is plausible, not phoneme exact.
- **Auto gain.** Loudness is judged against the recent peak, so TTS volume does not matter.
- **Share the existing audio source.** The LiveKit hook already owns the AudioContext and agent source; the driver adds its own listen-only analyser, so playback and the mute are unaffected.
- **Jaw fallback stays.** Without viseme morphs (today's GLB) the jaw path is unchanged, and the voice analysis is skipped so phones do not pay for it. With viseme morphs the jaw bone is scaled by `JAW_WITH_VISEMES` (0).
- **Lag over smoothness, within reason.** `SMOOTHING.preRate` 40 to 60 and the rig follow rate 60 to 120 cut lag from 78 ms (104 worst) to 59 ms (79 worst) with motion above 10 Hz still under 1 percent.
- **Blink deferred, not dropped,** during stressed syllables, and never longer than 3 s.
- **Dev page is dev only.** It sits behind `import.meta.env.DEV`; audio is gitignored and must never be committed.
- **Bare names bind as they are.** The 3D plan names its shape keys `sil PP FF DD kk CH SS nn RR aa E I O U`, so `viseme_` prefixes are optional.

## 6. Status

- Done and committed on `hk/06-lipsync`, not pushed. Re-run during this handoff: `npm run test:lipsync` gives 22 of 22 pass. The builder and reviewer also ran lint (clean) and build (OK) before the commits.
- Reviewer verdict: ship with notes. Live output matches the offline analysis closely (mean absolute error 0.06, aligned within 10 to 20 ms); s and sh give SS, m and b give PP, a long u gives U, pauses close the mouth.
- Not done: the morph path has never been seen on a real viseme GLB (only unit tests on synthetic and cloned three.js meshes); no real phone or Safari test; the eyelid blink is not wired to bones.
- Vault journal for the builder run: `memory/2026-10-04-lipsync-driver.md` in the vault (the reviewer could not write one; the main session should journal the review fixes).

## 7. Known issues

- **Blink does nothing on the new GLB yet.** The 3D plan (D3) blinks with `eyelid_L` and `eyelid_R` bones and a `Blink` clip, not a morph, so `rig.hasBlink` is false. The scheduler still runs and `LipsyncRig.update()` returns its blink weight every frame; nothing consumes it.
- **Arabic fatha reads as E more than aa** (about 13 percent against 7 percent of active shapes), because these voices rarely reach the aa F1 prototype of 780 Hz. Fine on the 2D mouth; check on the real shapes.
- **Formants drop out on some frames;** the tracker then holds its last estimate.
- **Safari and iOS unverified.** The resume on tap is tested in Edge (suspended context, then a tap) and in a node test. Whether Safari's `MediaStreamSource` works on the remote WebRTC track is unknown.
- **Burst detection depends a little on frame rate:** PP is 7 percent at 120 fps against 9 percent at 60.
- `AvatarErrorBoundary` only clears the default `MODEL_URL`, not a custom `modelUrl` prop (dev only).
- Commit `7fcee13` carries the attribution line "Claude Code", not the Opus line used elsewhere. History was left alone on purpose.
- `frontend/dev-audio/` is gitignored, so a fresh checkout has an empty lab until clips are copied in.

## 8. Next steps

1. **Plug in `avatar-animated.glb`** (steps below).
2. **Wire the blink to the eyelid bones.** Take `const blink = lipRig.update(...)` in `useAvatarMotion.js` (it is already called each frame, the return value is currently discarded), and rotate `eyelid_L` and `eyelid_R` by `blink * closedAngle` about their local blink axis. Do this instead of playing the `Blink` clip: the scheduler already owns timing, and the clip's 9 frame curve is fixed. If the clip is kept, drive the scheduler only for timing and trigger the clip from it. Do not key the lids from any other clip (the 3D plan already forbids it).
3. Look at the real mouth on Arabic and English clips in the lab's avatar view. Lower `VISEME_GAIN` for shapes that look too strong. Lower the `aa` F1 prototype from 780 to about 700 in `CLASSIFIER.vowels` if the mouth looks too closed.
4. Test on a real iPhone and Safari (first tap should start the mouth; check a locked screen and call interruption).
5. Merge into `hk/demo-mvp` once the other team is done with it. The edits to existing files are small, and the bulk is new files.

### How to plug in the new avatar-animated.glb morph names

1. Get the export from `%USERPROFILE%\Documents\Alsadiq-3D\04-exports\avatar-animated.glb` and read `avatar-animated.json` for its `morph names`. The plan says 14 shape keys: `sil PP FF DD kk CH SS nn RR aa E I O U`.
2. Copy the GLB to `frontend/public/models/avatar/`. In `Avatar.jsx` change `MODEL_URL` to the new file and bump `?v=` (for example `avatar-animated.glb?v=anim1`). For a quick look without editing code, pass `modelUrl` to `Avatar` instead (the dev page's avatar view takes one too).
3. Names that already bind with no change (case-insensitive, first match wins per mesh): `viseme_aa`, `v_aa`, `visemeaa`, `mouth_aa`, `vis_aa`, `aa`, and the same pattern for every viseme. So the bare plan names work as they are. The prefix list is `MORPH_NAME_PREFIXES` in `lipsync/visemes.js`.
4. If the names differ, either edit `MORPH_NAME_PREFIXES` (the whole set shares one prefix) or pass `morphNames` to `Avatar`, one entry per viseme, a string or an array:
   ```js
   const MORPHS = { aa: 'Mouth_Ah', O: ['Mouth_Oh', 'oh'], sil: 'Mouth_Rest' };
   <Avatar morphNames={MORPHS} ... />
   ```
   Define `MORPHS` at module level or memoise it; a new object each render rebuilds the rig.
5. The avatar counts as a viseme avatar once at least 5 of the 14 are found (`MIN_VISEMES_FOUND`). To see which names bound, call `bindMorphTargets(scene)` (in `morphTargets.js`) on the loaded scene and read `foundVisemes` and `missingVisemes`; `LipsyncRig` keeps the same result as `rig.binding`. A missing name simply stays at 0.
6. Several meshes (head, teeth, tongue) may share names; every mesh that has the name is driven by the same weight.
7. A blink morph (`blink`, `eyeBlink`, `eyes_closed`, `eyeBlinkLeft/Right`, see `BLINK_MORPH_NAMES`) binds automatically if the GLB has one. The planned GLB uses bones instead, so do next step 2 above.
8. Jaw: with viseme morphs the jaw bone is scaled by `JAW_WITH_VISEMES` (0, so the morphs do all the work). The 3D plan says code drives `jaw` from the voice. If the visemes are mouth shapes only and the chin should drop with them, set `JAW_WITH_VISEMES` to about 0.3 in `lipsyncConfig.js`.
9. Do not weld or simplify the mesh after the shape keys exist, and check that the optimiser keeps the target names (the plan's post chain already says so). No clip may carry a `weights` channel, or it will overwrite the lip-sync every frame.
10. Check in the lab: play an Arabic and an English clip with the avatar view on, watch for jumps, and confirm `npm run test:lipsync` still passes.

## 9. Gotchas

- Voice analysis only runs while the agent is speaking and the GLB has viseme or blink morphs. On today's `avatar-web.glb` it is off, so "nothing happens" there is correct.
- `getLipsync()` returns null until the AudioContext runs (iOS needs a tap). The mouth then follows the jaw level on the `aa` shape, so a short fallback period is normal.
- Every stage adds lag. Changing a smoothing rate to look calmer will make the mouth late; measure with the lag test before and after.
- After changing `CLASSIFIER` numbers, re-run the clip script and the tests; formant based tuning is sensitive.
- `useAvatarMotion` rebuilds the rig when `scene` or `morphNames` changes; pass a stable `morphNames`.
- The worktree `%USERPROFILE%\Documents\Alsadiq-wt\demo-mvp` is being edited by another team. Do not touch it; merge from this branch when ready.
- No Islamic text lives in this code. Keep it that way (`AGENTS.md`): the config files are signal-processing data only.
- Never commit audio. If `git status` shows anything under `frontend/dev-audio/`, the ignore rule was lost.
