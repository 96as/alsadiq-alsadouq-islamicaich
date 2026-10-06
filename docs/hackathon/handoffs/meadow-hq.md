# Handoff: meadow-hq (branch hk/meadow-hq)

Hotfix after Majd's feedback "why is the quality so bad and the animations are so bad". Scope: a sharper,
better-framed meadow page (/meadow and the child voice screen that uses the meadow). Nothing else.

## Done

- A sharper painted meadow served as a srcset (900, 1600, 2560, 3840, 5120 wide, WebP, 16:9), in
  `frontend/public/backgrounds/hq/`. Phones get the small file, 4K and ultra-wide windows get the big one.
- The picture is never stretched: `object-fit: cover` with a focal point that follows the stage, so the path
  stays under Sadiq and his feet stay on the same painted row on any shape from 9:19.5 to 32:9.
- Sadiq is framed by stage height: about 57% of the stage height on the talk view, standing on the path,
  feet above the mic row. A soft contact shadow sits under his feet.

## Source finding

- The lead's current meadow is `fantasy-meadow.webp` (2560x1440), a Marble (World Labs) world view.
  It is NOT the same painting as `background.png` (2752x1536, a sunnier painting in the repo since April).
  There is no higher-resolution original of the Marble view, so the 2560 file was the best source.
- Upscale: Real-ESRGAN ncnn-vulkan (BSD-3, tool in `Alsadiq-3D/tools/realesrgan`, not a project dependency),
  model `realesrgan-x4plus-anime`, run natively at x4 with `-t 256 -j 1:1:1`. (Its `-s 2` output on the 4x model
  comes out tile-scrambled; do not use it.) Then Pillow Lanczos down to each width plus a mild unsharp mask,
  WebP quality 90 to 93. Script: `Alsadiq-3D/studio-research/hotfix/encode.py`.
- Honest limit: the source is a soft, smeared AI-render look. The upscale gives cleaner shapes and edges, not
  new detail. A real step up needs a new high-resolution painting or the living meadow.

## Framing numbers (frontend/src/features/child/components/meadowFraming.js)

- `computeFraming(w, h)` is one pure function used by the image layer (`MeadowImage.jsx`) and the avatar camera
  (`avatar/Avatar.jsx`, `CameraSetup` and `SceneRig`), so they always agree.
- PATH_X 0.455 (path column in the painting), FEET_ROW 0.82 (painting row for his feet), fov 32, no tilt,
  AVATAR_SHARE 0.57, AVATAR_HEIGHT 0.865 (calibrated by measuring: 0.92 gave about 54%).
- Reserve at the bottom 88 to 124 px (mic row) and at the top 64 to 104 px (header).
- Checked at 2000x713, 2560x1080, 1440x900, 1280x720, 390x844 and 360x740: Sadiq on the path, feet above the mic.

## How to swap the picture

Change `MEADOW_IMAGE` in `meadowFraming.js` (dir, file name pattern, widths, aspect). Re-measure `PATH_X` and
`FEET_ROW` for the new painting. Nothing else holds the path. `VoiceMode.jsx` uses `<MeadowImage anchored />`
and `framing="meadow"` on `Avatar`.

## Run and test

- Dev: `npm run dev` in `frontend/`. Showcase build: `VITE_SHOWCASE=1 npx vite build --base /page/ --outDir dist-showcase`
  (see showcase-live.md), then `vite preview` and open `/page/meadow?state=idle`.
- Screenshots: `Alsadiq-3D/studio-research/hotfix/shots.py PREFIX [BASE_URL]` (Playwright, Edge). Results are in
  `Alsadiq-3D/03-renders/studio/hotfix/before-*.png` and `after-*.png`.

## Not touched

The landing page, the forest scene, the lighting rig and the avatar model and clips. The animation quality
Majd mentioned (motion, not the picture) is not addressed here.

## Next steps

- A new high-resolution meadow painting, or the living meadow, for real detail.
- If wanted, a motion pass on the avatar (separate package).
