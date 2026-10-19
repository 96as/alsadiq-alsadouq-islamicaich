# Handoff: 06 avatar context, director, expressions, nod and search hologram (Phase A and B)

- **Date:** 2026-10-04
- **Owner:** Majd
- **Branch:** `hk/06-avatar-context` (local only, never pushed), from `hk/06-avatar-live` at `cec85d0`
- **Worktree:** `%USERPROFILE%\Documents\Alsadiq-wt\06-avatar-context`
- **Spec:** `%USERPROFILE%\Documents\Alsadiq-3D\SPEC-EXPERIENCE.md` (package 9.5, Phase A). **Motion bible:** `...\studio-research\MOTION-BIBLE.md`.
- Code lives in `frontend/src/features/child/components/avatar/`, called `AV/` below.

## 1. What was done

Phase A runs against today's GLB (`anim2`: Idle, LookAround, Listen, Think, TalkGesture, Wave, Happy, Walk, Blink) and degrades cleanly when a clip is missing. The new clips (SearchStart, SearchHold, SearchSwipe, Found, Nod, Greet, Goodbye, Celebrate, Listen and Talk variants) are not needed to see the system work.

| Part | Files | Job |
|---|---|---|
| Signals | `AV/context/avatarSignals.js`, `transcriptCues.js`, `src/hooks/useLiveKitRoom.js` | One store for `al.sig_v`, `al.activity`, `al.search_kind`, `al.talk_style`, `al.reply`, `al.listen_style`, `al.turn`, transcript cues, gamification, `session_ending`. `useLiveKitRoom` exposes `getAvatarContext`. |
| Director | `AV/context/avatarDirector.js`, `shotQueue.js`, `nodRules.js` | Pure JS, allocation free, one reused output object. Picks base clip, one-shots (priority and ttl queue), nod, blink, squint, smile, soft mouth, "ooh", gaze. Missing clips fall back through `resolveClip` and `FALLBACK` in `avatarConfig.js`. |
| Hologram timeline | `AV/context/holoTimeline.js` | Virtual clock, so the hologram works without new clips. Phases from open to burst and close. |
| Expression layer | `AV/context/expressionLayer.js`, `headLayer.js` | Post-mixer offsets: eyelid squint toward the Blink clip's closed pose (cap 0.35), head pitch for the nod. Restore order is lookAt, head, expression. |
| Nod | `AV/context/proceduralNod.js`, `AvatarAnimator.playAdditive` | Additive `Nod` clip via `makeClipAdditive` when it exists, else a procedural nod (peak 0.08 rad, attack 0.12 s, release 0.35 s, 2 slots). |
| Hologram | `AV/hologram/HologramRig.js`, `hologramShader.js`, `hologramConfig.js`, `holoEnvelope.js`, `holoIcon.js` | Glass panel in Sadiq's raised left palm, 3 skins (library, folders, web), halo, sparks, beam. |
| Wiring | `ClipAvatar.jsx`, `Avatar.jsx`, `VoiceMode.jsx`, `ConversationPage.jsx`, `forest/ForestStage.jsx` | `getAvatarContext`, `lang`, `lowTier`, `onStatus` props passed down. |
| Dev | `AV/dev/useSignalSimulator.js`, `SignalSimulatorPanel.jsx`, `AvatarPreviewApp.jsx`, `forest/ForestPreviewPage.jsx` | A fake agent that feeds the same store functions as LiveKit. |
| Tests | `frontend/tests/avatarDirector.test.mjs` (70), `hologramEnvelope.test.mjs` | Run with `npm run test:avatar`. |

## 2. Decisions, and where I deviated

- **Hologram timeline on a virtual clock** in the director, not on clip markers, so Phase A shows the full search with no new clips. When SearchStart/Hold/Swipe/Found land, the clips play on the same timeline; nothing in the rig changes.
- **Think stands in for SearchHold** (`FALLBACK`). SearchStart, SearchSwipe, Found, Nod, Celebrate and Happy resolve to nothing (spec section 6 table: Celebrate is "nothing"). Greet and Goodbye fall back to Wave, so a session limit shows `Wave`.
- **Draw calls:** at most 4 (panel, halo, sparks, beam), 2 on the low tier (panel and beam). The beam only exists when there is a SearchHold clip or a `prop_L`/hand anchor, so with today's GLB the hold uses the virtual anchor and has no beam. Triangles added: about 4 (measured 93339 against 93335 with no hologram), far under the 300 cap.
- **Blending (gotcha).** The canvas is transparent and premultiplied, so an additive layer that writes alpha 1 paints a dark box on the page. Beam and sparks use `LIGHT_BLEND` (One/One for colour, no alpha write). The panel and halo are premultiplied (One/OneMinusSrcAlpha). Do not switch these to `AdditiveBlending`.
- **(Superseded in Phase B, section 12.) Shaders use three's default (`highp`), spec says `mediump`.** I did not set a precision, so they run at highp; the cost is negligible at these sizes, and I did not test on a phone GPU. To follow the spec, set `precision: 'mediump'` on the hologram `ShaderMaterial`s in `HologramRig.js` and check the SDF edges for banding.
- **`softSil` / `softI` deviation.** The spec says the soft mouth biases `sil` by +0.35. At rest `sil` is already 1, so that is a no-op. I use `softSil` 0.35 plus `softI` 0.08 so the closed smile is visible at rest. Values are in `DIRECTOR.bias`.
- **Reduced motion:** no panel animation. A 128 x 128 canvas icon at avatar-local (0.24, 0.86, 0.10) fades in and out; the status line is a DOM `aria-live="polite"` caption (`onStatus(kind, seq)`), also shown as a small caption.
- **RTL:** designed in one space and mirrored for English with `uRtl`. Arabic is the default look.
- **Low tier:** `isLowTier()` is true when hardwareConcurrency <= 4, deviceMemory <= 4, or the screen short side is under 500 px. Override with the `lowTier` prop, or `?holotier=low|high` on the dev pages. Playwright at 390 x 780 lands on low.
- **(Fixed in Phase B, section 12.) Gold flash looks pale cream** over bright backdrops (found flash). I added a soft knee and gold dimming; it is still cream rather than gold at the peak frame. Left as is.

## 3. Behaviour you might mistake for a bug

- **Interrupt** means the agent state returns to `listening` after a non-listening state, not `al.activity=idle`. That closes the hologram fast (INT_CLOSE). The simulator's `interrupt()` does both.
- **8 s `toolGap`.** A second search within 8 s of the last close does not open a hologram (`DIRECTOR.holo.toolGap`). Other limits: `minShow` 1.4 s, `foundGrace` 0.3 s, `maxHold` 15 s (then it closes as "none").
- **Repeated `found`.** LiveKit attribute updates only fire on a change. If the backend sets `al.activity=found` twice in a row, the second does nothing. The backend must go back to `idle` between searches (or alternate values).
- **`al.sig_v`.** `markDisconnected()` sets it to 0. The backend must set `al.sig_v='1'` when it publishes signals. The simulator's `connect()` does this. The backend's `session_limit` sends `{"type":"session_ending","seconds_left":N}`, which triggers Goodbye.
- **`avatar-web.glb`** (the clip-less fallback) gets the director's expression layer but no hologram and no `info`; it does not crash.

## 4. How to run and test

```
cd frontend
npm run lint
npm run build
npm run test:lipsync     # 22 pass
npm run test:avatar      # 76 pass (director, timeline, nod, envelope, sidecar match, viseme gain)
npm run dev -- --port 5320
```

- Preview: `http://127.0.0.1:5320/avatar-component-preview.html`. Params: `?holotier=low|high`, `?lang=ar`, `?sim=0` (hide the simulator panel), `?model=/models/avatar/avatar-web.glb`.
- Forest scene: `/dev/forest` (`?panel=0` hides the control panel).
- Console / Playwright helpers: `window.__sim` with `connect`, `listen(v)`, `talk(v)`, `search(kind, outcome, ms)`, `interrupt`, `gam(name)`, `say(text)`, `child(bool)`, `limit`, `lang(code)`, `reset`; `window.__setState(name)`; `window.__control.current` with `info` (base, shot, talkStyle, holoPhase, drawCalls, triangles, tier, directorMs), `perfReset()`, `rig`, `director`.
- Edge pass used: Playwright `channel="msedge"`, headless, `--use-angle=d3d11 --enable-gpu-rasterization --ignore-gpu-blocklist`. Never click mailto or tel links.

## 5. Gate results

Verified in Edge at 1000 x 640 and 390 x 780 (low tier), no console errors or GLSL errors:

- Listen: neutral, curious, sad, excited. Talk: explain, story, praise, question, gentle.
- Search: library found, folders none, web interrupt, on all three skins; Arabic (RTL); reduced motion (icon plus caption); low tier (2 draw calls).
- Celebrate (no clip, expression only), Greet and session-limit Goodbye (both play Wave today).
- `avatar-web.glb` fallback: no crash, no hologram.
- Forest page: the hologram shows over the scene.

Cost of the director plus the hologram (JS ms per frame, measured around `applyDirector`, `director.step` and `rig.update`, scene of about 93k triangles):

| Rate | Idle avg | Search avg | Search max | Peak draw calls |
|---|---|---|---|---|
| 1x | 0.017 ms | 0.038 ms | 0.60 ms | 4 high, 2 low |
| 6x CPU throttle | 0.14 ms | 0.40 ms (0.45 ms low tier) | 3.8 ms (8.4 ms low tier) | 4 high, 2 low |

Honest read: the 0.15 ms target is met at 1x and at 6x idle. At 6x during a search it is about 0.4 ms. Part of that is timer noise: `performance.now` is quantised to 0.1 ms in Edge and is read twice per frame, and the maxima are single GC or scheduler spikes. `director.step` alone costs about 0.1 us per step in node, and a 200k-step soak showed 5 KiB (idle) and about 103 KiB (search loop) of heap growth, so there is no steady allocation. The remainder is `rig.update` (uniform writes, anchor and camera projection). No optimisation was done beyond keeping it allocation free; if 6x matters, profile `rig.update` first.

## 6. Videos

In `%USERPROFILE%\Documents\Alsadiq-3D\03-renders\R2\web\` (1000 x 640, from the simulator, Edge headless):

- `avatar-context-search-flow.mp4`: hold, swipes, found and burst for a library search, then a web search that ends as none.
- `avatar-context-listen.mp4`: the four listen styles.
- `avatar-context-talk.mp4`: the five talk styles with transcript cues.

## 7. Phase B: when the new clips land

1. Copy the new GLB in and point `avatarConfig.js` at it. `animator.has(name)` picks up the clips; the `FALLBACK` entries stop applying by themselves.
2. Check the markers in `CLIP_META` (`avatarConfig.js`) against the spec table: SearchStart, SearchHold, SearchSwipe (3 variants), Found, Nod (additive), Greet, Goodbye, Celebrate, Listen_Curious/Empathy/Excited, Talk_*.
3. With a SearchHold clip or `prop_L`, the rig anchors to the palm (`prop_L`, else `handl` plus `fallbackOffset`) and draws the beam. Re-tune `fallbackOffset` and `virtualAnchor` in `hologramConfig.js` if the new hand differs.
4. Re-run the Edge pass and re-record the three videos.

## 8. For the mouth-acting builder (WP4)

- `DIRECTOR.nod.emphasis.enabled` (in `avatarConfig.js`) is the switch for the director's voice-onset emphasis nods. Set it to `false` when the stress-timed accent nod lands so only one system nods while Sadiq speaks.
- `AV/context/headLayer.js`, in `apply()`, has a marked spot (`06-mouth-acting: add speech-head and micro-drift offsets ...`). Add the offsets to `this.pitch / yaw / roll` there so they sum with the nod.

## 9. Merge notes

Builder merge order: lipsync-ar, avatar-context, mouth-acting, walk-studio, nature. Expected conflict files, all marked with `06-avatar-context` comments:

- `ClipAvatar.jsx` (the frame loop: director, layers, hologram, look-at order)
- `avatarConfig.js` (CLIP names, FALLBACK, DIRECTOR, LOOK weights)
- `AvatarAnimator.js` (underlay, `playAdditive`, `interrupt`, `weightOf`)
- `lipsync/lipsyncRig.js` (viseme `bias` array, added in one place)
- `VoiceMode.jsx`, `Avatar.jsx`, `forest/ForestStage.jsx`, `pages/child/ConversationPage.jsx`, `hooks/useLiveKitRoom.js` (prop and hook plumbing)
- `package.json` (`test:avatar` script)

## 10. Not done

- Phase B clips and markers: done, see section 12.
- No new dependency, no backend change. The backend still has to publish the `al.*` attributes (section 3).
- The 6x search average was above the 0.15 ms target in Phase A; Phase B numbers are in section 12 (still above on the wrapper metric, under it by CPU profile).

## 11. Review (Opus reviewer, 2026-10-04)

Fixed in `fix(avatar): review fixes for the context director and hologram`:

- **Found kept the base on Idle** (Phase B bug, latent today): `playOnce` switched a transition's base to its `to` loop after the director had chosen the state loop, so a Found while speaking left Sadiq on Idle for the rest of the reply. `applyDirector` now passes `switchBase: false`; the director owns the base.
- **The old Happy played on points.** Today's GLB has a `Happy` clip (the round-1 arms-out one), so `resolveClip` returned it. `LEGACY_GATE` in `avatarConfig.js` keeps it out until the GLB also has `Greet` (same talk package as the Happy fix). The smile still plays.
- **Procedural nod:** minimum-jerk segments (no velocity jump on the first frame), a 20 percent rise past rest before it settles, and `nodScale` now stretches the nod in time (empathy 0.8 is slower) instead of scaling its size.
- Two per-frame allocations removed (the hologram's view key string, the shot queue's env literal).

Measured by the reviewer (Edge headless, per frame, single call; `performance.now` averages):

| | 1x idle | 1x search | 6x idle | 6x search |
|---|---|---|---|---|
| `director.step` | 0.011 ms | 0.016 ms | 0.12 ms | 0.17 ms |
| `rig.update` | 0.003 ms | 0.027 ms | 0.02 ms | 0.28 ms |

`rig.update` costs 0.037 ms at 6x when called warm (20 times a frame), so most of the single-call cost is cold caches and the `updateWorldMatrix(true, false)` parent chains. The director's closure `let` doubles are boxed by V8 on every write (about 100-250 bytes of garbage per step, measured in node); harmless in practice, but not strictly allocation free.

## 12. Phase B (anim3 GLB, `prop_L`, review fix-list)

Branch `hk/06-avatar-context`, still local only. Code under `AV/` as above.

**What changed**

- **`avatar-animated.glb` and `.json` replaced with the anim3 export** (30 joints, `prop_L`, 14 morphs, 24 clips). sha256 `6143009db9d0ad48b62262104bdab9b8cdfecd62026fc6a6835ee08001debe76` checked, `inspect-avatar-glb` run, `ANIMATED_MODEL_URL` now `?v=anim3`. All 24 clips are wired through the director. `LEGACY_GATE` and `FALLBACK` are still in `avatarConfig.js`, but nothing hits them with this GLB (they only matter for an older GLB).
- **CLIP_META vs sidecar test** (`frontend/tests/avatarDirector.test.mjs`, now 76 tests) reads `public/models/avatar/avatar-animated.json` and checks names, frames, kind, duration, markers (in seconds), entry (`entry_mode` running gives `entry` null, reset gives 0, else `entry_s`), home, the transition `to` loops, and Found `from` SearchHold. Only the Happy markers (`takeoff` f8, `apex` f15, `land` f21) were missing; added.
- **Hologram on `prop_L`.** The panel floats 5 cm above the open palm and the beam runs from the socket. `panelOffset` changed from `[0, 0.11, 0.03]` to `[0.035, 0.125, 0.04]` so the card clears the cheek and sleeve and sits as in `03-renders\R2\listen\holo-placeholder.png` (right of the face, over the palm). `fallbackOffset` and `virtualAnchor` are unchanged (only used when there is no `prop_L`).
- **Gold found flash:** before the luma boost the colour is pulled toward `uFound` at the same peak brightness (`add = mix(add, uFound * peakC, 0.7 * uGold)`). At the Found peak frames it reads gold, not cream; the outer halo is still a little pale from the bloom.
- **mediump (deviation, read this).** `precision mediump float;` is prefixed to the four hologram fragment shaders only, with `highp` kept for `uTime` and the hash function. The vertex stage stays highp. I did not use `ShaderMaterial.precision` because that would also drop the vertex stage and shimmer the panel edge. Desktop GPUs (this machine) compute mediump as highp, so **banding on a real phone is unverified**. F3 (real phone) was not run.
- **Viseme double gain.** The R2 mesh bakes 1.5x into the E, I, kk, DD and nn shape keys. `MESH_VISEME_GAIN` (in `avatarConfig.js`, test-pinned to the sidecar `applied` values) is divided out in `LipsyncRig` (new `meshGain` option, applied to `VISEME_GAIN`) only when the scene has `prop_L`, so other GLBs are untouched. E 0.9 gives 0.6 on the R2 mesh.
- **Frame budget.** (a) The director's 19 numeric closure variables are fields of one state object `S` (V8 boxes a closure double on every write). (b) `HologramRig` no longer calls `updateWorldMatrix(true,false)` and `getWorldPosition` per node. It reads the skeleton as the last render left it (one frame behind; the 60 ms anchor spring hides it), and the root inverse is computed once per frame. The frame that snaps the anchor (the open) does one exact `refreshChain()` of the cached ancestor list.
- **Dev refused-shot warning:** `applyDirector` logs `[avatar] the animator refused the director shot "..."` in dev builds. No such warning fired in any run below.
- **Dev preview:** the three button rows now live in one flex column so a wrapped row cannot sit on top of the next (the overlap at 390 px). Added a `nod` button. Kept small because WP4 edits `AvatarPreviewApp.jsx` too.

**Verified in Edge (headless, 1000 x 640 and 390 x 780, no console error, no GLSL error)**

- Listen: neutral, Curious, Empathy (sad), Excited. Talk: TalkGesture, Talk_Story, Talk_Praise, Talk_Ask, Talk_Gentle (director debug confirmed each base within 0.5 s).
- Search on library (found), folders (none), web (interrupt) at both sizes; RTL; low tier (3 draw calls); reduced motion (icon plus caption, no panel). Found while speaking: the base stays `TalkGesture`, Found plays on top, then the shots follow normally.
- Greet, Goodbye (it waits for the speaking state, then plays), Celebrate. Nod (additive clip) button, no error. `avatar-web.glb`: the clip avatar rejects it, the plain avatar renders, no hologram. `/dev/forest`: the hologram shows over the scene.

**Frame budget (wrapper metric around applyDirector, director.step and rig.update, scene about 93k triangles)**

| Rate | Idle avg | Search avg | Search max | Peak draw calls |
|---|---|---|---|---|
| 1x | 0.016 ms | 0.046 ms | 0.6 ms | 5 high, 3 low |
| 4x | 0.079 ms | 0.231 ms (low tier 0.242) | 4.0 ms | 5 high, 3 low |
| 6x | 0.176 ms (0.124 on the run before the rig change, so noisy) | 0.278 ms | 5.0 ms | 5 high, 3 low |

Honest read: the 0.15 ms gate at 4x holds for idle and is **not met on the wrapper metric during a search** (0.23 ms). The wrapper reads `performance.now` twice per frame and Edge quantises it to 0.1 ms, so about 0.08 ms of that is the idle floor. A CDP CPU profile over a 5 s search at 4x puts `HologramRig.update` self time at about 0.065 ms per frame and `director.step` at about 0.02 ms, together under 0.15 ms. `director.step` alone is 0.13 microseconds in node with 103 KiB heap growth over 200k search steps (no steady allocation). Draw calls are 5 and 3 now (the Found flash and the beam on `prop_L` add one each over Phase A); the triangle cap still holds (about 93343 against 93335). If the gate matters on a phone, profile `rig.update` first (uniform writes and the spark buffer), then consider skipping the halo while the panel is dimmed.

**Videos** (`%USERPROFILE%\Documents\Alsadiq-3D\03-renders\R2\web\phaseB\`, 760 x 700 crops of a 1600 x 1024 recording, no blank lead-in, Edge headless): `avatar-phaseB-walkin.mp4`, `avatar-phaseB-idle.mp4`, `avatar-phaseB-listen.mp4` (four contexts), `avatar-phaseB-talk.mp4` (five styles), `avatar-phaseB-search-flow.mp4` (library found, then web none). Edge headless throttles animation, so judge timing from the event logs and not from the video smoothness.

**Merge notes for WP4 (mouth acting)**

- `ClipAvatar.jsx`: `lipRig` is built with `meshGain` (detected via the `prop_L` node). If WP4 changes the `LipsyncRig` constructor call, keep that option.
- `lipsync/lipsyncRig.js`: the constructor builds `this.gains` from `VISEME_GAIN / meshGain`, and `update` passes it to `applyVisemes`. WP4's stress-timed accent code must read `this.gains`, not `VISEME_GAIN`, or the R2 mouth doubles up again.
- `context/avatarDirector.js`: all per-step numbers are `S.xxx`. New director code that keeps a changing number should add a field to `S` (no closure `let` for a double).
- `dev/AvatarPreviewApp.jsx`: the bars share one `stack` container; add new rows inside it.

**Not done / open**

- F3 (real phone: mediump banding and frame time) was not run.
- The wrapper-metric search budget at 4x and 6x is above 0.15 ms (see above).
- No backend change; the backend still has to publish the `al.*` attributes (section 3).
