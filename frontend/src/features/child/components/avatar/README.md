# Avatar component

3D character for voice mode: [`Avatar.jsx`](./Avatar.jsx) loads a skinned GLB, optional skeletal clips, and procedural head/jaw/upper-body motion.

## Animated model (current path)

`Avatar.jsx` loads `/models/avatar/avatar-animated.glb` (clips Idle, Listen, Think, TalkGesture, Walk, Wave, Happy, LookAround, Blink; 14 viseme morphs; metadata in `avatar-animated.json`). Set `VITE_AVATAR_MODEL_URL` to use another file (`avatarConfig.js`). If the file fails to load, or lacks the required clips, it used to fall back to `avatar-web.glb` with the procedural motion described further down (`ProceduralAvatar`); that 0.7 MB file is no longer shipped (perf), see `FALLBACK_SHIPPED` in `avatarConfig.js`, so the avatar now renders nothing and the page background stays. The animated path is `ClipAvatar.jsx`:

- `AvatarAnimator.js`: one `AnimationMixer` used as a blender. Loop clips crossfade (0.4 s), one-shots (Wave, Happy, LookAround) take weight over the base and hand back on the Idle first frame, Blink is its own layer (it keys only the eyelids). Idle plays LookAround every 12 to 20 s. Clip clocks are hand-driven, so the walk can follow the ground speed.
- Blink timing comes from the lip-sync blink scheduler (`LipsyncRig.blinker`), which triggers the Blink clip. The jaw and eyelids are never keyed by body clips.
- Lip sync: the 14 viseme morphs from `getLipsync`, plus a subtle jaw computed from the shown visemes (`JAW` in `avatarConfig.js`, rotation about the bone's local X, checked in the browser: +X opens).
- `lookAt.js`: head and neck look toward the camera or the desktop pointer, applied after the mixer, within small angle limits (`LOOK`). The model has no eye bones, so there is no eye-only gaze.
- Walk-in: the body moves at exactly the speed the Walk clip's feet push (timeScale x 0.525 m/s x `MODEL_SCALE` x the clip's blend weight, `WALK_CLIP`) and faces the way it really travels as the camera sees it (`walk.travelYaw`, set by the forest's `CameraRig`), so the planted foot stays put. It ends with a walk-to-idle blend at an unchanged cadence (`stopTime`), then turn, Wave, Idle. Reduced motion goes straight to Idle facing the child.
- `lookAt.restore()` runs before the mixer: three only rewrites a bone whose blended value changed, so without it a clip that holds the head still would let the look-at turn pile up.
- Dev handle: `controlRef.current` has `play`, `hold`, `look`, `jaw`, `animator`, `bones`, `info`. Used by the preview pages (`dev/`).

## Asset location (older model)

```
frontend/public/models/avatar/avatar-web.glb
```

Vite serves `public/` as static assets, so the URL is `/models/avatar/avatar-web.glb`. Everything below describes the procedural fallback.

The two 43 MB sources (`avatar.glb`, a duplicate, and `avatar-round7.glb`) were removed from `public/` because every build copied them into `dist`. They are in git history. To regenerate the web model, restore `avatar-round7.glb` into `frontend/avatar-src/` (see the comment at the top of `scripts/optimize-avatar-web.mjs`) or set `AVATAR_SRC`.

## Current GLB (inspection notes)

- **Rig / bones** (node names used in code): `head`, `jaw`, `arm.l`, `arm.r`, `pec.l`, `pec.l.001`, `hand.l`, `hand.r` (and others in the file not driven yet). If you re-export from Blender, fix `BONE_NAMES` in `Avatar.jsx` to match.
- **Animation** `ArmatureAction` in a typical export can have **duration 0**; `playFirstValidIdle` only plays a clip with length greater than 0.01s. If you add a real **Idle** clip, procedural **arm/pec** overrides are skipped while that clip is active (see `hasSkinnedClip` in `Avatar.jsx`).

## Props

| Prop         | Type    | Source |
|-------------|---------|--------|
| `isSpeaking` | boolean | `agentSpeaking` from `useLiveKitRoom`. Fallback only: used while `agentState` is not listening, thinking or speaking. |
| `agentState` | string | `agentState` from `useLiveKitRoom` (the `lk.agent.state` attribute): `initializing`, `listening`, `thinking`, `speaking`. Picks the pose. |
| `getAudioLevel` | `() => number` | `getAgentAudioLevel` from `useLiveKitRoom`: RMS of the agent's voice, negative when unavailable. Drives the jaw and head emphasis. Without it the jaw uses a synthetic wave. |
| `getLipsync` | `() => object or null` | `getAgentLipsync` from `useLiveKitRoom`: smoothed weights for the 14 visemes, see [lipsync/README.md](./lipsync/README.md). Drives viseme morph targets when the GLB has them; otherwise the jaw path above stays. |
| `morphNames` | object | Optional map from viseme to morph target name. |

The props are passed through [`VoiceMode.jsx`](../VoiceMode.jsx) from `ConversationPage.jsx`.

## Motion

[`useAvatarMotion.js`](./useAvatarMotion.js) drives the bones every frame; every number lives in [`motionConfig.js`](./motionConfig.js). Idle life (breathing, sway, glances, weight shift, relaxed arms) always runs; `STATE_TARGETS` eases the head and spine toward the listening, thinking or speaking pose. No allocations per frame, frame-rate independent, and `prefers-reduced-motion` shrinks the motion (the jaw is never reduced). Rig quirks: the torso is skinned to a static `neutral_bone` (the spine only carries the arms and head), and the jaw hangs off `neck > Bone.008` rather than `head`, so `Bone.008` copies the head's rotation every frame. The jaw opening uses auto gain, so it does not depend on the TTS volume. The model has no eyelid bones or morph targets, so there is no blink until the new GLB with viseme and `blink` shape keys is in; the lip-sync driver in [lipsync/](./lipsync/README.md) handles both and falls back to the jaw for this model. Preview with a state switcher at `/avatar-component-preview.html` (`npm run dev`).

## Integration and layout (2D + 3D)

1. **Framing (full body)**  
   The mesh is wrapped in `Bounds` with `fit`, `clip`, and `margin` so the **camera** frames the full skinned model. This prevents the “waist-only” crop that happened when the camera, look-at, and strong negative Y all fought each other.  
2. **Contact shadow**  
   `ContactShadows` is a **sibling** of `Bounds` (not inside the fit), so a large ground quad does not inflate the bounding box used to fit the camera.  
3. **Grounding vs `background.png`**  
   After fit, nudge the character with `AVATAR_ROOT` and align the contact ellipse with `CONTACT_SHADOW_POS`. Tweak with the 2D path in the background art.  
4. **Page layout**  
   [`VoiceMode.jsx`](../VoiceMode.jsx) bottom-anchors the canvas column so the 3D canvas sits in the **lower** part of the child screen, matching the painted path.

**Order to tune when art changes:** fit the body in view first (`Bounds` `margin`, initial camera in `Canvas`), then adjust `AVATAR_ROOT` / `CONTACT_SHADOW_POS` and optional FOV in `Canvas`.

## T-pose

- With **no** usable idle clip, the code uses procedural **A-pose** via `A_POSE_PITCH` and `PEC_FORWARD` on the arm/pec bones. If arms still look flat, add a real idle in the GLB (preferred) or raise the pitch values slightly.  
- When a non-degenerate clip exists, **arm/pec** procedural is disabled so the mixer is not over-written every frame.

## Scene setup

- **Canvas**: transparent so the 2D `VoiceModeBackground` shows through.  
- **Lighting**: warm ambient + hemisphere + directional + low-intensity `Environment` preset `park` (IBL only; `background={false}` on `Environment`).
