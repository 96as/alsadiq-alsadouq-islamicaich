# Handoff: avatar walk-in (branch hk/demo-walkin)

## Done
- On the forest child screen the avatar fades in far up the dirt path, waddles toward the camera,
  stops at its spot, turns to face the child and waves. The walk takes about 7 s and the whole
  sequence about 10.5 s (walk, 0.75 s turn, 2.75 s wave). It plays once per page load.
- Procedural gait on the leg bones (hip Bone.005/006, shin leg.r/leg.l, foot Bone.013/014), body
  bob, roll and sway on the model root, arm swing, then a raised-arm wave. No new assets.
- The ground point moves with the walk (`rt.stand` in CameraRig). Gait cadence follows distance
  travelled, so the feet do not skate. The body turns three quarters toward its screen direction
  while walking (the legs read badly head-on), then turns to face the child.
- Skipped for reduced motion and in the meadow (non-forest) mode. If reduced motion is switched on
  mid-walk, the avatar jumps to its spot. If the child starts the session mid-walk, the rest plays
  at 2.6x speed while the camera glides in.
- Fallback kept in code: `?walk=hop` on the forest stage gives a small hop and the same wave.
  `?walk=off` skips it.
- Preview: the "Replay walk" button on `/dev/forest` and in `avatar-component-preview.html`
  (`?walk=1|treadmill|hop`).

## Files
- `frontend/src/features/child/components/avatar/walkIn.js` (new): tuning in `WALK`, the state
  machine (`stepWalk`), the rig side (`applyWalk`).
- `useAvatarMotion.js`, `Avatar.jsx`: take a `walk` option and run it after the idle pose.
- `forest/runtime.js`, `CameraRig.jsx`, `ForestStage.jsx`, `ForestPreviewPage.jsx`.

## Decisions
- Shared plain object (`rt.walk`), no React state, nothing allocated per frame.
- Walk shipped, not the hop. The legs are small and mostly hidden by the cardigan, so the walk
  reads as a waddle with body motion more than as individual steps. That is intended.

## Test
- Preview only: `npm run dev`, open `/dev/forest`, press "Replay walk". Phone and desktop
  frames were checked in Edge.
- Review (Opus, 2026-10-04) on the real GPU (headless Edge uses the NVIDIA card by default; the
  first captures forced SwiftShader). Display rate (57 to 60 fps) during the walk and after it,
  at 1280x720 and at 390x844 with 3x DPR and 4x CPU throttle; the walk adds no measurable frame
  cost. Start session works at 0.2 s, 1 s (phone tap), 3 s and 7.5 s. `?walk=hop` and
  `?walk=off` work.
- Review change: `brakeRate` 1.5 to 2.6. The old stop crept for about 2 s at the end, so the
  avatar seemed to stall before it turned. It now stops in about 1 s.
- `npm run lint` and `npm run build` pass. The Python voice tests (95) pass with
  `config.settings_sqlite_test`. In review they also ran in the `demo-mvp-livekit_agent` image
  (livekit installed, no network): 219 conversation tests pass, 3 skipped (the scripts/voice
  key-file tests). The 74 demo-guard tests pass on the hk/demo-guards worktree (its working
  tree had uncommitted edits at the time).

## Open
- Not yet judged on a phone GPU or on the live site.
- Blender-forest mode uses a straight line away from the wide camera, because that path is not
  known to the code. It looks right on the built-in forest path only if the Blender path is
  roughly straight toward the camera.
- The architect's guard plan still says new sessions use xAI once the daily ElevenLabs cap is hit.
  The code does not do this (see the next section); the plan text should be corrected.

## Voice: no automatic xAI fallback (verified)
- `tts_factory.build_tts` returns xAI only when `TTS_PROVIDER=xai` is set by an operator. A
  missing key, a plugin import error or a build error raises `VoiceConfigurationError`.
- `demo_guards.resolve_voice` (branch hk/demo-guards) returns xai only for the operator switch;
  an exhausted budget goes text-only.
- Tests that pin this: `test_missing_key_raises_a_clear_error_and_never_builds_xai`,
  `test_plugin_build_failure_raises_and_never_builds_xai`,
  `test_unknown_provider_value_never_selects_xai`,
  `test_source_has_one_path_to_xai_and_it_is_the_explicit_switch`.
