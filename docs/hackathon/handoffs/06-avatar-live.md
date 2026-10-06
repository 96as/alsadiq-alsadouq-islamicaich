# Handoff: animated avatar live (task 06, branch hk/06-avatar-live)

Date: 2026-10-04. Branch: `hk/06-avatar-live`, built on top of `hk/06-lipsync`. Not pushed.

## 1. What this is

The 3D team's animated Al-Sadiq (`avatar-animated.glb`) running on the website. It replaces the
procedural avatar on the child screen and in the forest walk-in. The old avatar (`avatar-web.glb`
plus procedural motion) stays as an automatic fallback.

The asset: 2.1 MB, 93k triangles, 27 joints, 14 Oculus viseme morph targets, 9 clips (Idle,
LookAround, Listen, Think, TalkGesture, Wave, Walk, Happy, Blink). Its facts are in
`frontend/public/models/avatar/avatar-animated.json`. The 3D plan is
`%USERPROFILE%\Documents\Alsadiq-3D\PLAN-3D.md` (section 5, A4 clip table). The 3D review is
`REVIEW-3D.md` in the same folder.

## 2. What was built and why

- One animation controller (`AvatarAnimator.js`). Agent state picks the loop (Idle, Listen, Think,
  TalkGesture), with 0.4 s crossfades. One-shots (Wave, Happy, LookAround) play over it and hand
  back to the loop. Blink is a separate layer. Why: the avatar must feel alive in every agent
  state and never pop between them.
- Blink: the lip-sync blink scheduler (from `hk/06-lipsync`) decides when. The Blink clip is what
  the child sees. Why: the new GLB has no blink morph and the Blink clip owns the lids.
- Lip sync: `useVisemes` drives the 14 viseme morphs from the agent's audio track. The jaw is
  derived from the shown visemes (subtle, max 0.16 rad about local X). Why: body clips never key
  the jaw, so code owns it.
- Look-at (`lookAt.js`): head and neck turn toward the camera or the desktop pointer, within
  safe limits, after the mixer runs. Why: eye contact makes a companion feel present.
- Forest walk-in: plays the Walk clip at ground speed so the feet do not slide, then turns,
  waves and goes to Idle. Reduced motion skips straight to Idle facing the child. Why: the old
  procedural walk could not match the new legs.
- Fallback chain: animated GLB, then `avatar-web.glb` with procedural motion. Why: the child
  screen must never be blank because of a load failure.

## 3. Where it lives

Paths are under `frontend/` unless noted.
- `src/features/child/components/avatar/`: `avatarConfig.js` (model URL, clip names, tunables),
  `AvatarAnimator.js`, `ClipAvatar.jsx`, `lookAt.js`, `walkIn.js`, `Avatar.jsx` (clip path,
  procedural fallback, URL fallback chain), `dev/` (preview app and audition voice), `README.md`.
- `src/features/child/components/forest/`: `ForestStage.jsx`, `CameraRig.jsx` (works out the real
  travel direction for the Walk clip), `ForestPreviewPage.jsx`.
- `public/models/avatar/avatar-animated.glb` and `.json` (cache key `?v=anim2`).
- `scripts/inspect-avatar-glb.mjs` lists clips, morphs and joints of a GLB.
- `avatar-component-preview.html` at the frontend root.
- This file, at the repo root: `docs/hackathon/handoffs/06-avatar-live.md`.

## 4. How to preview it and play the clips

1. `cd frontend`, then `npm run dev` (pick a free port if the default is busy).
2. `/avatar-component-preview.html`: state switcher (idle, listening, thinking, speaking), hold a
   loop, play any one-shot, and a speak button that plays a dev audio clip through the visemes.
   The dev audio is gitignored (`frontend/dev-audio/`); the speak button needs it locally.
3. `/dev/forest`: the forest with the same controls, time of day, replay walk, and `?panel=0` to
   hide the panel.
4. Model URL: set `VITE_AVATAR_MODEL_URL` (default is the animated GLB). Point it at
   `/models/avatar/avatar-web.glb` or a missing file to see the fallback.
5. Checks: `npm run lint`, `npm run build`, `npm run test:lipsync` (22 tests).
6. Browser checks used Playwright with `channel: "msedge"`. Never click mailto or tel links.

## 5. Decisions

- Clip ownership (PLAN-3D D3 to D5): body clips never key the jaw or eyelids. The Blink clip owns
  the lids. No morph channels in clips. Code owns the jaw, visemes, blink timing and look-at.
- Clip clocks are hand driven with normalised weights, so the T-pose bind pose never shows
  through and the walk can follow speed. Every one-shot ends on the Idle first frame and the base
  is rewound under it, so the hand back is seamless.
- Blink: triggered by the scheduler counter, so lip sync and the clip stay in step. LookAround
  also blinks, at a fixed offset (the JSON has no LookAround markers).
- Visemes: the shown values drive the morphs. The jaw is a small function of them, not of raw
  audio level.
- Look-at: head and neck only (the model has no eye bones). `lookAt.restore()` runs before the
  mixer update, because three.js skips bones whose clip value did not change, which would let
  the turn build up if a clip ever held the head still.
- Walk: the body faces the true direction of travel as the camera sees it (`walk.travelYaw`).
  The stop blends Walk into Idle over 0.9 s at the same step rate, with no slow motion.
- Fallback: any load error or missing clip gives `avatar-web.glb` with the procedural avatar.
- `MODEL_SCALE` 0.87 sizes the new avatar to about the old one's height. Judged by eye.

## 6. Status

- Lint 0 errors, build ok, 22 lip-sync tests pass.
- Checked in Edge with the real GPU (headless) at 1000x640 and 390x780, and in reduced motion:
  states, blink, Wave, jaw axis, look-at signs, viseme audition, walk-in, and the fallback with a
  missing file and with `avatar-web.glb`.
- Planted-foot drift in the walk-in: 5 to 7 px/s (about 20 before the review fix).
- JS cost of animator, look-at and lip rig: about 0.05 ms per frame on desktop, 0.35 ms at 6x
  CPU throttle, no steady allocations.
- The GLB in the repo is the 3D reviewer's re-export, sha256 `f334bf99...`. On 2026-10-04 it was
  compared with `Alsadiq-3D\04-exports\avatar-animated.glb` and is identical, so no refresh was
  needed. Clip, morph and joint names match the code.
- Review verdict: ship with notes. Three feature and fix commits on the branch, none pushed.

## 7. Known issues

- Not tested on a real phone or in a live LiveKit session. GPU cost is unmeasured (93k
  triangles, 2048 textures).
- No eye bones, so the eyes never lead a glance.
- Happy is a hop with the arms out, close to the T bind pose (no forearm bones). Nothing plays it
  automatically. Keep it out of the live flow.
- TalkGesture is subtle and loops every 4 s. It is not tied to the speech rhythm.
- The mouth trails the voice by 40 to 80 ms on four test clips. The lip-sync driver owns this.
- A load failure logs an uncaught error in dev, but the fallback still works.
- Walk cruise scale (1.2) and distance (4.2) were judged in short captures, not frame by frame.

## 8. Next steps

1. Real-phone test (an iPhone and a mid-range Android): frame rate in `/dev/forest` and on the
   child screen. If it is too heavy, ask the 3D team for a 1024 texture or lower-poly variant.
2. Merge into `hk/demo-mvp`. Both branches edit `Avatar.jsx`, `walkIn.js`, `ForestStage.jsx` and
   `CameraRig.jsx`, so expect conflicts there. Keep both the clip path and the procedural
   fallback. Rerun the Edge pass of states and the walk-in after merging.
3. PR order: `hk/06-lipsync` first (this branch sits on it), then `hk/06-avatar-live`, then
   rebase `hk/demo-mvp` onto both. Push when Majd is ready:
   `git push -u origin hk/06-avatar-live`.
4. Test with a live LiveKit agent: states from `lk.agent.state`, visemes on the real track, and
   iOS audio resume.
5. Tune the `LOOK`, `JAW` and walk numbers in `avatarConfig.js` by eye on real devices.
6. If the 3D team re-exports: compare the sha256, run `node scripts/inspect-avatar-glb.mjs`, bump
   the `?v=` cache key, rerun lint, build and the Edge pass.

## 9. Gotchas

- Clip names in `avatarConfig.js` must match the GLB exactly. If a clip is missing, the avatar
  drops to the fallback.
- Do not key the jaw, lids or morphs in clips. The code assumes it owns them.
- The walk speed is tied to ground speed. Changing the path distance or the walk scale without
  retuning brings back foot slide.
- Software GL in Edge hides GPU cost. Use the real GPU and still test on a phone.
- The favicon 404 in page loads is harmless.
- Dev audio files are gitignored on purpose.
- In browser tests, never click mailto or tel links. They open Windows "Pick an app" popups.
