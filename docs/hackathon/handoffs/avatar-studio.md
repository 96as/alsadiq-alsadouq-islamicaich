# Avatar studio: integration step 1

Branch `hk/avatar-studio` = `hk/showcase-live` + merge of `hk/06-lipsync-ar` + merge of `hk/06-avatar-context` (real merge commits, both intents kept) + the meadow work below. Other work packages (nature motion, mouth acting, lookdev, the rest) merge into this branch later. Edits are marked `// integrate-1`.

## Done
- Merges with conflict decisions (see below).
- Viseme double-gain fixed for the anim3 mesh (see below), lip-sync eval re-run.
- `/meadow` Speak plays a REAL Arabic clip with text-timed lip sync and sound (4 Arabic clips, 1 English). The clips reach the showcase dist through a build step; nothing audio is committed.
- `/meadow` context panel: listening styles, talking styles, search, Greet, Goodbye, Celebrate, Happy, driven through the signal simulator into the real context store and director.
- The forest card is untouched (still "Experiment: 3D forest (to discuss)").

## Merge decisions
- `package.json`: both scripts kept (`test:lipsync`, `test:avatar`).
- `avatarConfig.js`: `ANIMATED_MODEL_URL = assetUrl(...) + '?v=anim3'` and `MESH_VISEME_GAIN` ({E, I, kk, DD, nn: 1.5}) both kept.
- `VoiceMode.jsx`, `Avatar.jsx`, `ClipAvatar.jsx`, `AvatarPreviewApp.jsx`, `useAuditionVoice.js`, `useLiveKitRoom.js`: lip-sync props and the avatar-context props both kept.
- `ConversationPage.jsx`: one `avatarLang` feeds both the lip-sync vowel model and the hologram.
- `assetUrl.js`: `import.meta.env?.BASE_URL` (optional chaining) so the node test runners can import it. Without it test:lipsync and test:avatar failed in Node.
- `scripts/lipsync-eval/eval.mjs`: `setMeshGains` takes a divisor option (needed for the gain check below).

## Viseme double gain
The anim3 GLB has `MESH_VISEME_GAIN` baked into the E, I, kk, DD, nn morphs. LipsyncRig divides it out with `meshGain` (gain = V[k] / (applied[k] ?? 1)) when `prop_L` exists, so the mouth is not drawn 1.5x too hard. Eval on the held-out lines with the anim3 GLB, hybrid engine:

| | before (r1 mesh) | after (anim3, divisor on) |
|---|---|---|
| K1 (aa openness, p75) | 0.80 | 0.80 |
| K2 (jaw openness, p90) | 0.62 | 0.62 |

Identical because aa and the jaw are not baked. The gain only matters for the baked visemes: with the divisor off, E, I, kk, DD, nn are 1.5x too strong (hybrid diacritised recall a 0.90 / i 0.83 / u 0.67 against 0.92 / 0.80 / 0.67 with it on; 48 kHz plain audio-only identity 0.89 against 0.95).

Other numbers (hybrid, diacritised): closures 27/27 (م 17/17, ب 10/10), vowel identity 0.85, long vowels 1.00, lag -30 ms, over 10 Hz 1.3%, K3 92.6%, R1 10/10. Hybrid plain: identity 0.96, closures 27/27, K1 0.84, K2 0.62, K3 96.3%. Audio only: closures 0/27 (this is why text timing matters). Eval reports written during the run were deleted from the shared `dev-audio`.

## Showcase audio (no audio is committed)
`frontend/scripts/showcase-audio.mjs` is a vite plugin, used only in the showcase build (`vite.config.js`). On `closeBundle` it:
- takes the source clips from `SHOWCASE_AUDIO_DIR` (default `frontend/dev-audio`, gitignored),
- encodes mono 44.1 kHz mp3 at 80 kbps with ffmpeg (`SHOWCASE_AUDIO_KBPS`, clamped to 64-96; `FFMPEG_PATH`, default ffmpeg on PATH),
- writes a slim alignment JSON per clip (text, sr, duration, characters, starts, ends) and `manifest.json`, all in `dist-showcase/showcase-audio/`.

Clips: ar01 greeting (explain), ar20 praise, ar04 white cat (story), ar30 goodnight (gentle), and en02 bedtime game (English, explain). Result: 5 mp3 files, about 0.23 MB. If ffmpeg or the sources are missing the manifest is empty and the page falls back to the made-up voice, so the build never fails on audio.

`noDevAudioGlobs` (vite plugin, build only): `evalClips.js` uses `import.meta.glob('/dev-audio/...?url')`, which would copy every dev-audio file into the dist. The plugin rewrites those globs to a nonexistent folder at build time. Checked: the dist has no wav, f32, dotfile, .env or key file.

## Meadow page
- `src/pages/useShowcaseVoice.js`: loads the manifest, replays the alignment through TimelineSync (`alignmentToItems`, `timelineMessages`, `goMessage`) while the mp3 plays, and exposes `getLipsync` / `getLevel` for the avatar. It sets the vowel mode (ar or en) first and waits two frames, because the mode is chosen when the driver is made.
- `src/pages/MeadowShowcase.jsx`: tabs Speak, Style, Search, Moments, Basics. Fixed-grid chips, Arabic and English labels. Test hooks: `data-tab`, `data-speak`, `data-listen`, `data-talk`, `data-search=<kind>-<found|none>`, `data-moment`, `data-state-chip`, `data-action`, `data-panel`, `data-panel-toggle`, `data-speak-quick`. `window.__sim`, `__setState`, `__control` remain.
- Chip to signal: attentive = neutral, empathetic = sad, ask = question; excited, curious, explain, story, praise, gentle map by name. Search runs `sim.search(kind, outcome, 3500)` with the thinking state.
- Desktop: the panel sits bottom right (24 rem), clear of Sadiq. Phone: it is a collapsible sheet, collapsed by default (Sadiq full size) with a quick Speak button; open, it sits below the stage.
- Greet and Goodbye are once-per-session in the director. The simulator got `newSession()` (reset plus a long-break reconnect) and the director re-arms `goodbyeDone` on a reconnect of 60 s or more (`avatarDirector.js`, unit test added: 59 pass in that file). Greet comes from a salam in the first 40 characters of the first agent message.

## Build and run
```
cd frontend
MSYS_NO_PATHCONV=1 VITE_SHOWCASE=1 VITE_FOREST_SCENE=1 npx vite build --base /page/
MSYS_NO_PATHCONV=1 npx vite preview --base /page/ --outDir dist-showcase --port 5381 --strictPort
# optional: SHOWCASE_AUDIO_DIR=... FFMPEG_PATH=... SHOWCASE_AUDIO_KBPS=80
```
Output `frontend/dist-showcase` (15 MB; the only file over 3 MB is `backgrounds/background.png`, 6.2 MB).

## Tested
- `npm run lint` clean; `npm run test:lipsync` 80 pass; `npm run test:avatar` 77 pass; `npm run build` and the showcase build succeed.
- Lip-sync eval (numbers above).
- Edge (Playwright, msedge) on the built dist at 2000x713, 1440x900, 390x844, 360x740: no console errors, no horizontal scroll, Sadiq framed as in the hotfix. Every chip pressed once at desktop sizes (listen x4, talk x5 across the run, search, Greet, Goodbye, Happy, Celebrate, both languages of Speak) with no errors. About 60 fps in headless.
- Media (outside the repo): `Alsadiq-3D/03-renders/studio/integrate1/` has the before/after Speak video with audio, a context reel, and phone screenshots.

## Reviewer pass (Opus)
Served the dist with the live `/page/` helpers and CSP (team-office `brain/pages.py`) on :5382, Edge headless, real clicks, no autoplay flag.
- Checked: 0 console errors, 0 CSP violations, 0 4xx at 2000x713 and 390x844 (mobile, touch); every chip pressed; Arabic Speak plays from a click on desktop and from the phone's quick button. In the browser, sampling the morphs against `audio.currentTime` on all four Arabic clips: 11 of 11 meem/baa reach PP 0.94, the closure starts within 35 ms of the letter (median 0), `aa` p90 0.75 on the vowels. Dist: no dotfiles, .env, keys, wav or f32; no audio is tracked in git. The backend is byte-identical to `hk/06-lipsync-ar`.
- Fixed: back-to-back Search presses showed no hologram. Two causes. (1) `holoTimeline.js`: a search that arrived while the panel was closing was dropped on the first closed frame (the 0.2 s gap was checked once, then the pending kind was cleared), so it never reopened, in a session as well. It now waits out the gap, and drops the pending search if its result arrives first. Unit test added (fails without the fix). (2) The 8 s `toolGap` between holograms is right for a session but hid a second press on the panel, so `MeadowShowcase` shortens `toolGap` and `quickGap` while the page is open and puts them back on unmount. Now 6 of 6 rapid presses show the panel.
- Fixed: the Goodnight chip read `تصبح` (incomplete); now `تصبح على خير`.
- Not fixed (mesh, WP5): the PP shape key tears the lower lip (a jagged flap, and a dark slit stays visible), and aa, O and U open a boxy rectangle. The live mesh has the same shapes. Real closures now show PP about 3 times a second, so the tear is seen more often than before.
- Not fixed: the speaker button does not mute the real clip (the element feeds the analyser, so muting needs a gain node in `visemeDriver.js`).

## Left
- "Before" in the side-by-side is a local copy of the hotfix dist (commit ac8c470), because the live `/page/meadow` needs a login.
- On a phone, the open sheet shrinks the stage; the face stays visible but Sadiq is smaller than when collapsed.
- The Speak captions show the diacritised text.
- Greet and Goodbye are played through the simulator's fake agent text, not a real session.
- Waiting to merge: nature motion (06b), mouth acting, lookdev, WP1, WP2, WP5.
- The forest card is still an experiment and has no voice in the showcase.

## Hotfix 2 (Safari-safe play, mute, conversation shot)
Majd, Safari on a Mac at 2000x713: "Sadiq is still small and the lip syncing isn't working, and the animations are so little." Every edit is marked `// hotfix-2` (or sits in a file new in this hotfix) so the look-dev framing, living meadow, WP4 mouth and knee-walk merges can find them.

### What changed
- **Play order** (`src/pages/useShowcaseVoice.js`). `speak()` is a plain function, not async. On the tap, `el.play()` is the first call and `audioContext.resume()` is called in the same tick, not awaited. The manifest, every alignment and every mp3 are prefetched and decoded on mount (mp3s become blob URLs, which the live CSP allows with `media-src 'self' blob:`). The lip-sync timeline, state and captions are set after `play()` is called. A first `pointerdown` unlocks audio for iOS/Safari. If `play()` rejects, a banner shows "Tap to turn on sound / اضغط لتشغيل الصوت"; its button retries inside its own tap and the failure is logged to `window.__voiceLog`. Nothing fails silently.
- **Mute through a gain node** (`visemeDriver.js`, `useVisemes.js`). The element is tapped once: tap to analyser (lips), and tap to GainNode to destination (heard). The speaker button sets the gain to 0 and shows `aria-pressed`. The lips keep moving while muted.
- **Controls** (`MeadowShowcase.jsx`, `GlassIconButton.jsx`). The silent chip is now "Mouth test (no sound) / تجربة الفم بلا صوت", dashed and secondary. The wide layout's primary control is "Speak (Arabic) / تكلم بالعربية" (`data-speak-primary`), which plays a real clip. The phone quick button stays.
- **Conversation shot** (`avatar/conversationShot.js`, new; wired in `ClipAvatar.jsx`, `Avatar.jsx`, `meadowFraming.js`). While speaking or listening the camera eases from the full body to a face-forward shot (about 1.5 s, smoothstep on a damped amount). It holds 1.6 s after speech ends, then eases back. Full body is kept for the walk-in, the first idle, walking, thinking and while a hologram is open (the shot yields so the hologram above his left palm stays on screen). Reduced motion cuts instead of easing. The contact shadow fades with `--sadiq-shot`.
- **Measured face floor.** The face is the head, ear and jaw skinned vertices (about 700 points, stored in head-bone space) and is projected to screen px every frame. `faceFrac` is 0.42 of the usable stage height (the chibi head is about 45% of the body, so a smaller value barely moved the idle framing). A width cap handles phones. If the measured face is under 25% of the viewport height (with an 8% margin) the shot boosts the zoom, up to 1.8x. It stayed at 1.0 in every test.

### Measured (headless and headed Edge agree)
Face height (ear tops to chin, exact projection) while speaking, first tap:
| viewport | face px | of viewport | idle (full body) |
|---|---|---|---|
| 2000x713 | 336 | 47.1% | about 25% |
| 1440x900 | 425 | 47.2% | about 24% |
| 390x844 | 363 | 43.0% | about 23% |
| 360x740 | 314 | 42.4% | about 23% |
With the phone panel open the stage is smaller and the face is 31% to 32%.
- Latency, click to `play()` called: 15 to 19 ms on every tap (budget 100 ms). Every `play()` ran inside the tap (`navigator.userActivation` active).
- Lips, PP morph per frame vs `audio.currentTime`: m/b/p peaks 0.93 to 0.98 (closed). Arabic vowels: `aa` peak 0.80 to 0.87. English clips: `aa` 0.29 to 0.35 (lower, a WP4 matter).
- Mute: gain 0, `aria-pressed` true, jaw peak 0.63 to 0.71 while muted.
- Ease: no snap (max step 4.7% of the travel per frame); reduced motion reaches 1 within one frame.
- Hologram: on screen in Search; the shot yields to the full body (face 27% at 2000x713).
- Blocked flow (a simulated `NotAllowedError`): banner shown, retry played in 16.5 ms with the context running.
- 0 console errors at every size. The one warning, "AudioContext was not allowed to start" at load, is expected before the first gesture.

### Tests
- `npm run test:hotfix2` (14 tests): `tests/showcase-voice-order.test.mjs` is a static check that `speak()` is non-async with no `await`, `fetch`, state set or other work before `el.play()`, that `resume()` precedes `play()`, and that failures are surfaced and a `pointerdown` unlock exists. `tests/conversation-shot.test.mjs` checks the face is at least 25% of the viewport on 2000x713, 1440x900, 1280x720, 768x1024, 390x844 and 360x740, plus the ease, cut and boost cap.
- `npm run lint` clean; `test:lipsync` 80 pass; `test:avatar` 78 pass.
- E2E (outside the repo, in the scratch folder `Alsadiq-wt/hotfix2-scratch/`, not committed): `serve.py` serves the dist on :5384 with the live-like CSP, then `PYTHONUTF8=1 python e2e_hotfix2.py headless|headed`, `e2e_shot_extras.py`, `e2e_blocked.py`, `record.py`. Headed runs use `--window-position=-3000,0 --mute-audio`.
- Safari/WebKit could not be launched on this PC (Application Control policy), so Safari behaviour is covered by the order test, code review and the simulated rejection. Please tap once on a real Mac and iPhone.

### Media (outside the repo)
`Alsadiq-3D/03-renders/studio/hotfix2/`: `before-speaking-*.png`, `after-speaking-*.png` (2000x713 and 390x844), `hotfix2-conversation-shot-10s.mp4` (headed Edge, the Arabic clips muxed in), `e2e/` (all sizes, results JSON). No audio is committed (the dist's `showcase-audio` is gitignored).

### Left
- Greet and Goodbye still use the silent made-up voice (labelled "no sound").
- Idle stays full body by design, so he is smaller at rest than during speech.
- English vowels are weaker than Arabic (WP4). The PP lip tear is WP5.
- Merge note: the shot reads `bones.head` and the skinned head vertices, so a rig or mesh change (WP4/WP5) needs a re-run of `test:hotfix2` and the e2e measure.

### Checker pass (Opus)
- Added (`useShowcaseVoice.js`, marked `hotfix-2 (checker)`): on iPhone the voice goes through Web Audio, which the ring/silent switch can mute. The page now sets `navigator.audioSession.type = 'playback'` (Safari 16.4+, feature-detected; other browsers have no `audioSession`) while the meadow page is open, and puts it back to `auto` on leave. Not testable here (no WebKit).
- Independent headed Edge check (`hotfix2-scratch/checker_opus.py`, own hooks, not the page's debug handles), 2000x713 and 390x844: every `play()` and `resume()` ran inside the `click`/`pointerdown` dispatch; all 5 clips played to the end; PP at every bilabial 0.94 to 0.98; face above the neck 46% to 51% of the viewport at 2000x713, 45% (panel folded) and 33% to 35% (panel open) at 390x844; mute gain 0 with jaw peak 0.63 to 0.64; Mouth test makes no `play()` call; 0 console errors. With the context forced to `suspended`, the Speak tap resumed it and played the clip with no banner.

# Step 2: studio merge (mouth acting, studio walk, nature motion, look-dev)

Branch `hk/avatar-studio`, started at `3686f2b` (hotfix 2). The complaint to answer: "Sadiq is still small, the lip syncing isn't working, the animations are so little." This step brings in the four studio branches, retunes the mouth to the V2 mesh, and proves the lip sync in Edge on many words.

## GLB in the dist
`frontend/public/models/avatar/avatar-animated.glb` (cache key `?v=studio2`) is the current `Alsadiq-3D/04-exports/avatar-animated.glb`, sha256 `896af84a87def282b29e58caf6072ab44c85f107a48b521c4cd2de1831dcffe2`. The showcase dist holds the same file (checked byte for byte). The sidecar `avatar-animated.json` came with it. It is the V2 studio mesh: head 19 morphs (13 visemes, browUp, browInnerUp, browDown, cheekPuff, mouthSmile), MouthBag 14, no `PP_jaw` morph yet, `viseme_mesh_gain.applied = {}`. The studio walk clips (Walk_Start, Walk_Stop_R, Walk_Stop_L, Beat clips) are inside.
`Alsadiq-3D/02-working/P1/STUDIO-MERGE-READY.json` (written `2026-10-04 22:57:55`) was polled for a newer build; see "Left" for the result. If a newer GLB arrives: copy it and the JSON, check the sha256, bump `?v=` in `avatarConfig.js` (`ANIMATED_MODEL_URL`), re-run the suites and `scripts/lip-proof.py`, rebuild the dist. The rig already binds `PP_jaw` when the mesh has it (`actingRig.js`), so a 20-morph head needs no code change.

## Merges (real merge commits, in this order)
1. `dd5d41d` hk/06-mouth-acting (WP4: ActingRig, MouthShaper, jaw budget). Lint fixes in `6989828`.
2. `aa43b76` hk/06-walk-studio (studio walk-in with Walk_Start, Walk_Stop_R/L; the V2 GLB).
3. `0959787` hk/06b-nature-motion (wind field, forest and meadow motion; `test:nature`).
4. `62b5d02` hk/06-lookdev (lights, grade, grounding, `stageFraming`; `test:lookdev`).

Conflict decisions:
- `package.json`: both scripts kept (`test:nature` and `test:lookdev`).
- `VoiceMode.jsx`: look-dev fix item 1 applied, `anchored={!lookdevEnabled()}`.
- Conversation shot (hotfix 2) and look-dev framing: combined through `lookdev/shotFraming.js`, so the face is at least 25% of the viewport while he speaks and the idle stays the grounded full body. `test:hotfix2` and `test:lookdev` both pass.
- `ClipAvatar.jsx`, `AvatarAnimator.js`: WP4 owns the jaw (the walk-turn jaw quaternion was dropped); the walk transition layer of the studio walk sits next to the additive slots; `cancelTransition()` when the walk ends.
- `Avatar.jsx`: the look-dev camera replaces `CameraSetup` on the meadow only.

## Mouth: V2 retune (WP4, `acting/`)
The mouth acting was tuned on the older mesh. The V2 MUSTs and the retune:
- `fitToClosure` (`mouthShaping.js`): a sealed or held PP (0.5 or more, `SEAL_FROM`) rescales the other visemes by `min(1, (1-PP)/sum_others)`, so the sum never passes 1 while the lips are shut. This stops the lip tear (it was listed as WP5 in hotfix 2).
- PP jaw gate `ppJawV2` 0.08 rad, with the clamp fading in from `ppGateAt - ppGateLead` (0.3 - 0.22). `shaper.ppJawMorph` drives the `PP_jaw` morph when the mesh has it.
- `nn` gain `[1.0, 1.2]`, `mouthSmile` neutral 0.15 written every frame, `BLINK_STUDIO.meanByState.speaking` 2.35.
- Retune to the bars: `JAW_STUDIO.max` 0.55, `levelCouple` 0.15, `budgetRef` 0.55, `ppJawMorphRef` 0.2.
- Tests: `tests/acting.test.mjs` has 3 new V2 tests (31 total pass).

## Lip-sync proof (Edge, headless, dev preview, 12 text-timed clips)
`scripts/lip-proof.py` plays `ar01, ar05, ar21, ar22, ar24, ar26`, each `.plain` and `.diac` (clips with `alignPath`, so they are timed by their text like a live session). It records every animation frame: the real mesh morphs on the head and the MouthBag, the chin travel, the jaw, PP.

| Check | Result (12 clips, about 57 fps) |
|---|---|
| NaN or infinite weight | 0 |
| viseme sum above 1.05 while PP is 0.5 or more (the tear condition) | 0 |
| PP at 0.9 or more with the jaw over the gate for 3+ frames | 0 |
| single-frame chin pop that is not part of a ramp | 0 |
| flutter (more than 9 reversals per second above 0.15 cm) | 0 |
| mouth stuck open (over 1 cm for 2 s while silent) | 0 |
| console errors | 0 |

Mouth bars (pooled over the 12 clips): chin median 2.37 cm (bar 2.2 or more), p90 3.74 (3.4 or more), max 3.87 (4.8 or less); jaw median 0.0897 rad (0.075 or more), p90 0.1007 (0.10 or more). Per clip the chin median runs 1.58 to 3.09 cm: short, soft clips sit lower, strong ones higher. The largest one-frame chin step is 2.6 to 4.6 cm; that is the engine delivering a bilabial closure in one frame (a designed fast closure), and the pop detector found no pop.
Close-up check: a 24-frame contact sheet of the mouth during `ar01` on the meadow page (`closeup-sheet.png`) shows clean seams when the lips close, wide teeth-showing opens, and no torn or pinched lips.
The showcase e2e (dist, the real mp3 clips) reads PP 0.97 to 0.98 on every bilabial of all 5 clips, with aa up to 0.85 and jaw up to 0.93 on Arabic, at all four sizes.
Not run: the Blender `pp_probe.py` and review2 scripts (the mesh is unchanged since the 3D team's own pass).

## Edge pass on the showcase dist (`scripts/e2e-step2.py`, headless)
Sizes 2000x713, 1440x900, 390x844, 360x740: 0 console errors, all 5 clips play on the first tap (every `play()` inside the click), mute works (gain 0, jaw 0.82 to 0.87).
- Speaking face: 47% (2000x713 and 1440x900), 43% (390x844), 42% (360x740) of the viewport. Idle face: 29% at 1440x900, 21% at phone width.
- MeadowLife alive at all sizes (`data-meadow-life="live"`; 25% to 28% of the pixels change between two screenshots 1.2 s apart).
- Idle body: about 0.70 of the viewport height at 2000x713 in the screenshot (the e2e number 0.63 is a bounding-box projection and reads low).
- Walk-in with the studio walk (`scripts/walk-in-check.py`, `/page/dev/forest`): Idle, then `Walk_Start` at 0.1 s, the `Walk` loop from 0.9 s, `Walk_Stop_R` at 10.0 s, Idle at 10.7 s, then the wave and the rest; `info.studio` true throughout, no console errors.
Screens, the contact sheet, the walk log and the results JSON are in `Alsadiq-3D/03-renders/studio/step2/` (`e2e/`, `walk/`). No audio is committed.

## Bug found and fixed in this pass
`lookdev/AvatarLookdev.jsx` loaded the environment map from `/backgrounds/meadow-env-1024.webp`. Under the showcase base `/page/` that URL gave a 404, so the meadow had no image-based light and the console showed an error at every size. It now goes through `assetUrl()`.

## Run it
```
cd frontend
npm run lint && npm run build
npm run test:lipsync && npm run test:avatar && npm run test:hotfix2 && npm run test:nature && npm run test:lookdev && npm run test:acting
# showcase dist (Git Bash needs MSYS_NO_PATHCONV=1, or /page/ turns into a Windows path)
MSYS_NO_PATHCONV=1 VITE_SHOWCASE=1 VITE_FOREST_SCENE=1 npx vite build --base /page/
# serve dist-showcase under /page/ with the hotfix-2 CSP server, then:
PYTHONUTF8=1 python scripts/e2e-step2.py headless
PYTHONUTF8=1 python scripts/walk-in-check.py http://127.0.0.1:5385/page <out dir>
# the lip proof needs the dev server (npm run dev -- --port 5385) and the gitignored dev-audio:
PYTHONUTF8=1 python scripts/lip-proof.py http://127.0.0.1:5385 out.json
```
Suites at the end of the step: lipsync 80/80, avatar 78/78, hotfix2 17/17, nature 17/17, lookdev 21/21, acting 31/31, lint clean, build clean.

## Left
- No newer GLB arrived: `STUDIO-MERGE-READY.json` was polled every 10 minutes from 00:19 to 02:49 (2.5 h) and its `written` time stayed `2026-10-04 22:57:55`. The GLB has no `PP_jaw` morph yet: the jaw gate alone keeps the lips shut on a PP. When a 20-morph head ships, the rig already binds it.
- Idle stays full body by design, so he is smaller at rest than while speaking.
- English vowels are still weaker than Arabic (jaw peak 0.35 to 0.50 on the English clip against 0.82 to 0.93 on Arabic).
- Greet and Goodbye still use the silent made-up voice (labelled "no sound").
- The proof uses Edge only (WebKit is blocked on this PC) and headless; a headed pass was not repeated in this step.

## Step 2 update: final GLB, lip-sync glitch test, final review
This supersedes "GLB in the dist" and the first item of "Left" above.
- **GLB.** Commit `42e1198` switched the page to the final studio GLB: `04-exports/avatar-animated.glb`, sha256 `ce266e8f088bb2c7894a80bd6f36d1cfc5b25895e51c104c40e55099d3737d67`, 2,480,896 bytes, cache key `?v=studio3`. It has 20 head morphs (13 visemes, `PP_jaw`, brows, cheekPuff, mouthSmile), no MouthBag, 30 clips and 32 joints, with the seam weld and the WP2 knee forks.
- **Mouth shaping (`42e1198`).** Visemes and jaw have per-frame rise limits, a released closure lets go over about 55 ms (PP release floor), the V2 chin settles onto the PP gate, and English tracks never take PP from the audio. The 74-item wide test (52 Arabic, 22 English) is in `scripts/lipwide`; its report and sheets are in `Alsadiq-3D/03-renders/studio/lipsync-test/`.
- **Showcase dist.** The dist built at 00:14 still held the studio1 GLB and the shaper from before `42e1198`. The final reviewer rebuilt it from `42e1198` (same command as "Run it"). `dist-showcase/models/avatar/avatar-animated.glb` now matches `public/` and `04-exports` (sha `ce266e8f...`). Deploy this build, not an older copy.
- **Final review (Opus), on the rebuilt dist with the hotfix-2 CSP server, headed Edge (off-screen, muted), 2000x713 and 390x844:**
  - 0 console errors, 0 page errors and 0 failed requests at both sizes. `play()` ran inside the tap.
  - Every real clip (ar01, ar20, ar04, ar30, en02) and the two talk styles were sampled on every frame: 0 NaN, 0 viseme sums over 1.05 while PP was 0.5 or more, 0 one-frame PP dips, 0 viseme steps over 0.35 and 0 jaw steps over 0.12 rad outside closure onsets. PP reached 0.97 on every closure. Face crops at the closures show sealed lips and no tears.
  - `scripts/lip-proof.py` on the dev server, 12 runs (ar01, ar05, ar21, ar22, ar24, ar26, plain and diac), 3 times: pop 0 in all 36 runs (ar26.diac included; the one-frame PP dip from the WP1 review is gone). NaN, oversum, ppjaw, flutter and stuck were also 0 in all runs.
  - Face while speaking, measured from the vertices: 43% to 47% of the viewport at 2000x713, and 39% to 42% at 390x844. At idle it is 31% and 21%.
  - Idle knees unload to 12.5 and 14 degrees, and head glances span about 47 degrees. The pose 8 s apart (one Idle loop) differs more than the pose 0.5 s apart, so the idle does not read as a loop. Happy and Celebrate crouch to about 43 degrees, and Listen_Excited bounces to about 22 degrees.
  - The walk-in (Walk_Start, Walk, Walk_Stop_R, Idle) with knees up to 57 to 65 degrees plays on `/page/dev/forest`. The meadow page has no walk-in, and never had one.
  - MeadowLife is live: 25% to 30% of the pixels in the side quarters change every 0.6 s. The hologram opens on Search. Every Style, Moments and Basics chip that was pressed responded.
  - Suites at `42e1198`: lipsync 80, avatar 78, hotfix2 17, acting 31, walk 20, nature 17, lookdev 21, all passing. eslint on `src` and `scripts` is clean.
  - The dist has no dotfiles, keys, wav or f32 files, and no local paths.
- **Still open (no blocker):**
  - In the GLB, Listen_Excited slides the right foot about 2.4 cm per bounce. The listening close-up hides the feet on the meadow.
  - At high weight, O and U lift the nose a little. U reaches 0.79 at runtime.
  - Morph slivers at the lip seam flip triangles of under 1 mm². They can't be seen in any crop.
  - English opens the mouth less than Arabic: the jaw median is 0.07 rad, against 0.17 to 0.25 rad for Arabic.
  - Several scripts under `frontend/scripts` hold `C:\Users\...` output paths. Scrub them before the public repo.
