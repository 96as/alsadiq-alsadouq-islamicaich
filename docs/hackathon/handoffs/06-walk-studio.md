# Handoff: studio walk on the website (WP1 web step, branch hk/06-walk-studio)

Date: 2026-10-04. Branch `hk/06-walk-studio`, built on `hk/06-avatar-live`. Not pushed.

## 1. What was built

The studio walk from the 3D team (`avatar-animated.glb`, P1 studio merge: Walk 16 f, Walk_Start,
Walk_Stop_R, Walk_Stop_L) now drives the forest walk-in.

- `public/models/avatar/avatar-animated.glb` and `.json`: the studio files (2,481,008 bytes after the fix round, 30 clips, 32
  joints, 19 head morphs plus MouthBag). `ANIMATED_MODEL_URL` carries `?v=studio1` to bust caches.
- `studioWalk.js` (new, plain numbers, no three): the timeline. Start, n whole half steps of Walk, then
  the stop that begins on the matching heel strike (even n: Stop_R at Walk f0, odd n: Stop_L at f8). Root
  travel is the sidecar `root_speed_m_s` in the transitions and 0.525 m/s in the loop. Everything is in
  clip seconds, so frame rate and a late rush (timeScale up to 1.35) change nothing.
- `walkIn.js`: small hooks only (`w.sw`, a studio branch at the top of `stepClip`, `startStudio` at the
  WAIT to WALK entry). The old gait stays as the fallback when the GLB has no transitions.
- `AvatarAnimator.js`: a transition layer (`startTransition`, `setTransitionTime`, `endTransition`,
  `setLoopTime`, `snapBase`, `cancelTransition`, `hasStudioWalk`). Walk_Start blends in over Idle in 0.1 s,
  hands over to Walk f0 with no fade, the stops cut in with no blend and end on Idle f0. Idle glances are
  blocked while a transition plays.
- `ClipAvatar.jsx`: wires the legs from `walk.sw`, and the turn (chest, neck, head).
- `avatarConfig.js`: `WALK_CLIP` (studio numbers), `WALK_CLIP_LEGACY`, `WALK_TRANSITIONS` (copied from the
  sidecar; a test checks they match), new `CLIP` names.
- `tests/walkStudio.test.mjs` and `npm run test:walk`: 20 tests (15 first build, 5 added in the fix round).

## 2. Decisions and why

- New logic lives in a new file with small hooks, because `hk/avatar-signals` rewrites `walkIn.js` and
  `hk/06-avatar-context` / `hk/06-mouth-acting` touch `ClipAvatar.jsx`, `avatarConfig.js` and
  `AvatarAnimator.js`. Conflicts will be textual and small.
- The plan nudges the walk distance by at most half a half step (0.07 m) so the stop lands on a contact and
  on the spot. A preview-pinned distance instead scales the stop root motion (clamped 0.5 to 1.5).
- Turning (Bible 3.3): root yaw follows the path at most 3 rad/s, the head leads by 0.12 s, at the stop up
  to 15 deg of remaining turn goes into chest and neck (30/30/40 share) over 0.6 s, then the root catches
  up at 0.6 rad/s while the chest and neck hand the turn back.
- The R2 24-frame walk is superseded by the 16-frame studio walk; R2 files were not edited.

## 3. Run and test

- `cd frontend && npm run test:walk` (20 pass), `npm run test:lipsync` (22 pass), `npx eslint .` clean,
  `npm run build` ok.
- Preview: `npm run dev`, open `/dev/forest`, press "Replay walk".
- Browser measurement (Edge, headless, 1000x640, 1600x1000 and 390x780) with the scripts
  `Alsadiq-3D/tools/P1/web/walk_measure.py` and `walk_analyze.py`. Results (1000x640 / 390x780):
  - W1: cruise ground speed 0.5249 / 0.5250 model m/s at timeScale 1; 34 half steps; arrives exactly on the
    spot (traveled equals distance).
  - W9: the stop started at Walk phase 0.000 f (Stop_R); the Walk action was at f15.89 to f0.41 around the
    switch (inside 1 f). Both runs chose Stop_R (n = 34).
  - W10: peak yaw rate 0.27 / 0.02 rad/s (limit 3), head lead 0.120 s, root yaw at the stop 12.5 deg / 6.1 deg
    (limit 15), root turn after the stop 0.60 rad/s.
  - W2 (foot bone point, mid-stance window, not the sole): mean 0.010, peak 0.037 to 0.049 model m/s. The
    peak includes sampler timing noise; the gate itself was measured on the sole in Blender.
  - The ending frames were looked at: the avatar walks toward the camera, stops, waves and stands facing
    the child.

## 4. Known issues

- The head lead could only be measured on the 1000x640 path (6 frames with a real turn); the forest path is
  nearly straight, so the 3 rad/s limit is tested in node, not in the browser.
- Start to Walk `shin_R` junction: fixed in the fix round (section 8), 313.5 deg/s strict, worst bone ratio 0.91.
- Knee curve is choppy at frame level (steps up to 19 deg at 16 f).
- Phone viewport: headless Edge laid out 390 wide fine; the first run at panel=0 started the walk before the
  sampler, so Walk_Start was measured only at 1000x640.
- THREE.Clock deprecation warning comes from react-three-fiber, not from this branch.

## 5. Ship rule and merge order

This branch carries the P5-mesh GLB (19 morphs plus MouthBag). It needs WP4's V2 viseme gain switch, which
exists only on `hk/06-mouth-acting`. Merge order: lipsync-ar, avatar-context, mouth-acting, walk-studio,
nature-motion. If walk-studio ships first, the mesh plays with V1-style under-driving gains.

## 6. Next steps

- After merging, run `npm run test:walk` again; resolve conflicts in `walkIn.js` by keeping the studio hooks
  and avatar-signals' `w.cfg` / WALK_PRESETS side by side.
- `CLIP_META` does not exist on this branch; add it when the avatar-context branch lands.

## 7. Review measurements (Opus review, 2026-10-04 22:30)

Measured in Edge on `/dev/forest` with a virtual clock (frame-exact, 120 Hz) at 1000x640 and 2000x713. The tools
are outside the repo, in `Alsadiq-3D/tools/P1/review/` (`measure2.py`, `analyze2.py`, `corestance.py`,
`decomp.py`, `mapcheck.py`, `clipslip.py`, `phaseslip.py`, `overlap.py`).

- **W2 on screen fails.** The section 3 W2 numbers are the clip in the avatar's own frame (foot plus root
  motion), and those are clean in mid stance (about 0.01 model m/s). The page composites the avatar canvas onto
  the forest with a CSS translate and scale, and the avatar camera sees the ground at about 15.7 deg while the
  forest camera sees the far path at about 9 deg. A step backwards in the avatar canvas therefore lands 1.78x
  (far end) to 1.05x (spot) as long on the forest ground (`mapcheck.py`). In core stance the planted foot slides
  backwards along the path at 0.34 u/s in the far half and 0.15 u/s in the near half (`decomp.py`), which is
  0.35 model m/s mean, 6.6 to 7.8 px/s mean and 15 to 22 px/s peak at 1000x640 and 2000x713, against
  3 px/s mean and 9 px/s peak. Sideways it is fine (1:1). This is the camera composition (`CameraRig.jsx`,
  `Avatar.jsx`), not the clip, and the R2 walk had the same flaw.
- The avatar is 36 to 83 px tall (head to ankle) during the walk-in at both window sizes, so knees and the
  heel-toe roll are barely readable in the product shot.
- Walk_Start plays entirely while the canvas fades in (opacity 0 to 0.68 over the Start, 1 at 0.7 s), so its
  anticipation is not seen.

## 8. Fix round (2026-10-04 night, after the review in section 7)

Not committed before this round; committed on `hk/06-walk-studio`, not pushed.

- **W2 camera (the on-screen moonwalk).** New `src/features/child/components/avatar/avatarCam.js`. While the
  avatar waits or walks, the avatar canvas camera is orbited about the avatar's feet to the forest camera's
  elevation over the stand point (`camElev`) and azimuth (`camAz`). The orbit is a rigid motion about a fixed
  point, so the feet pixel, the distance and the scale do not change and the CSS placement in `CameraRig.jsx` is
  untouched. `CameraRig.jsx` publishes `walk.camElev` / `walk.camAz` (set to null in `walkIn.js` on replay and
  finish); `Avatar.jsx` `CameraSetup` re-places the camera only when either changes. In TURN both blend back to
  the default over 0.6 s, afterwards they are null, so the talk shot is exactly the old camera (0, 0.9, 3.2).
  The azimuth is needed because `travelYaw` is measured against the eye ray; without it the ground direction was
  off by the eye bearing (about 0.03 u/s sideways slip). Its sign is the mirror of the forest bearing (tested).
- **Canvas transform precision.** `CameraRig.jsx` writes origin and translate with 3 decimals and scale with 6; the
  old 0.1 px quantisation showed up as px/s jitter in the slip metric (mid-stance R mean 2.6 to 1.2 px/s).
- **W9.** `WALK_CLIP` has `holdIn 0.3 / fadeIn 0.3`: Walk_Start holds its first frame under the fade for 0.3 s and
  then plays fully visible (`studioWalk.js` `hold`, `ClipAvatar.jsx`). Verified in the browser.
- **GLB.** New publish (2,481,008 bytes): knee chart and bob, Walk_Start shin_R ease, contact lift, chest twist lag
  2 f, tail bounce halved, soft Idle layer on 21 clips. `?v=studio1` cache key unchanged in name; bump it if a
  CDN holds the old file.
- **Tests and gates.** `npm run test:walk` 20 pass (new azimuth, bearing and elevation tests), `npx eslint .` clean,
  `npm run build` ok.
- **Measured on screen** (Edge, virtual clock, 1000x640 and 2000x713): depth map avatar +z 0.1 gives forest
  0.100 to 0.104 over the whole walk (before: 0.179 at the start, 0.106 at the end); lateral 1:1. Mid-stance slip
  R 0.039 to 0.040 and L 0.060 to 0.062 model m/s, 1.2 to 1.4 px/s (R) and 3.1 to 3.2 px/s (L) mean, mid-stance
  peak 2.5 (R) and 6.8 to 6.9 (L) px/s. Before: about 0.29 model m/s and 5 to 6 px/s.

## 9. Open items from the fix round

- Residual slip is above the 0.03 model m/s target (0.04 to 0.06) and L is marginally above 3 px/s mean. It comes
  from the late-stance toe-roll slip trend in the clip, not from the camera. Contact-frame vertex-switch blips of
  11 to 20 px/s appear in the full window. A Newton step on the elevation would bring the z map from 1.03 to 1.00.
- Staging, for the forest and lookdev owner: the walk-in frame is wide and the avatar is small (knees and heel-toe
  roll are hard to read); the forest backdrop's right edge shows at 2000x713.
- The GLB uses the approved P5 mesh (MODE=swap in `m_chain.sh`); rebuild with MODE=p5 once WP5's PP_jaw is final.
- The soft Idle layer touches 21 non-walk clips. Step of 18 deg at Start shin_R f5 (Stops 18.3 / 18.1) is chart-intrinsic.
- Majd: delete `C:\03-renders\P1` by hand.

## 10. Review 2 measurements (Opus review of commit 7d0014d, 2026-10-04 23:45)

Measured again in Edge (virtual clock, 120 Hz) on `/dev/forest` at 1000x640, 2000x713 and 390x780, plus the
component preview (`avatar-component-preview.html?walk=1` and `?walk=treadmill`, talk camera). Tools and outputs are
outside the repo in `Alsadiq-3D/02-working/P1/review2/` (`gates.py`, `twist.py`, `w2clip.py`, `cap_forest.py`,
`cap_preview.py`, `crack_check.py`, plus the earlier `tools/P1/review/` scripts).

| Gate | Measured | Read |
|---|---|---|
| W1 | 0.5250 model m/s cruise, 16 f loop, stop lands on the spot | pass |
| W2 clip (avatar scene, sole vertex) | stance f0.5-f9: 0.002-0.013 model m/s per frame bin; contact frame f0 0.09 | pass |
| W2 clip (Bible wording, ankle bones, 3 mm rule) | mean 0.043 / 0.049, peak 0.33 model m/s | fails, but the ankle swings about the heel and toe by design (heel-toe roll), so this method measures the roll, not slide |
| W2 on screen, mid stance f2.5-7.5 | R 0.054 / L 0.075 model m/s; px/s mean R 1.4-1.7 / L 3.3 (1000, 2000), R 3.9 / L 1.8 (390); peak 3.7-8.9 px/s | the moonwalk is gone (under 1 px of drift per stance at this framing); the model m/s Must is still about 5x over |
| W2 on screen, f1-8.5 | 0.12-0.13 model m/s; px/s mean 2.5-4.8, peak 12-21 (contact-frame vertex switches) | residual is the composite map: avatar ground +z maps to forest 1.03 to 1.00 with a 4 to 10 deg rotation that grows toward the end of the path |
| W3 | sole -0.9 (R) / -1.3 (L) mm in stance | pass |
| W4 | stance about 10 f, swing 6 f, double support about 2 f | pass |
| W5 | hips (Bone) bob 34.8 mm p-p, lowest f2/f10, highest f6/f14; pelvis sway +-10.8 mm | phases pass, amplitude 0.2 mm under 35 |
| W6 | knee contact 16.8 / 17.2, down 26.8 / 25.3, swing max 54.8 (R f12) / 53.8 (L f4), never below 5, max step 15.7 deg | swing max about 1 deg under 55 (triangle method) |
| W8 | pelvis = `root` yaw +-7.9; torso `Bone` counter-twist lags 2 f (corr 1.00); chest world +-5.9; head yaw +-0.8, roll +-1.4 | pass (the "lag 8 f" in overlap.py came from treating `Bone` as the pelvis; the legs hang from `root`) |
| W9 | fade 0.1, 0.6, 1.0 at 0, 0.15, 0.3 s with Walk_Start held at 0, then plays visible (all three sizes, phone included); stop at Walk phase 0.000 | pass |
| W10 | peak yaw rate 0.28 rad/s; stop yaw 12.4 deg (1000) / 5.8 deg (390) | pass |
| F4 | 2,481,008 bytes, 32 joints, 30 clips, branch GLB = `04-exports` (sha256 896af84a) | pass |
| Late note 2 (seams) | `seam_weights.mjs`: 580 mismatched coincident pairs (R2 had 627); 73 on leg bones (shin_L 32, leg.r 21, leg.l 9, shin_R 7, Bone.014 3, Bone.013 1) | not met: hairline see-through slits on the thighs and cardigan hem in leg close-ups on magenta; sub-pixel at the product framing |

Also: `npm run test:walk` 20 pass and eslint clean on the changed folders. The Start cut-in and the Stop cut-in
show no pop in frame-stepped captures (at the talk camera the avatar's bounding box moves at most 4 px per frame
there, the same as in the cruise).

Where the walk is seen: only the forest stage passes a walk to the Avatar (`/dev/forest`, the demo landing hero,
`?forest=1` on the conversation page). The painted meadow mode never walks, so the meadow page Majd judged at 19:25
shows none of this work. In the forest walk-in the avatar is 37-90 px tall (head to ankle), so the knees and the
heel-toe roll cannot be read there; that is staging for the forest and lookdev owner.
