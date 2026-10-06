# Forest scene (task 06b)

One React Three Fiber scene: the avatar stands on a dirt path in a flowery forest meadow, framed like the painted backgrounds. It is an MVP, opt-in and off by default.

## Turning it on
- `?forest=1` in the URL turns it on and remembers it in `localStorage` (`sadiq_forest_scene`). `?forest=0` turns it off again.
- `VITE_FOREST_SCENE=1` at build time turns it on for everyone.
- When on, it replaces the meadow image on the idle "Talk with Sadiq" screen and on the voice screen. In chat mode the stage stays mounted but hidden and paused.
- Dev only: `/dev/forest` (only when `import.meta.env.DEV`) shows the avatar with a time-of-day switcher and a start/stop session button. Query params: `?t=morning|noon|maghrib|night`, `?phase=wide|talk`, `?walk=off|hop`, `?panel=0`. Also an agent-state switcher, the avatar's clips (hold a loop, play a one-shot) and a button that speaks a clip from the gitignored `frontend/dev-audio/` with lip sync.

## Files
- `ForestStage.jsx` (default export): the full-size stage. Props: `phase` (`'wide'` or `'talk'`, changing it glides the camera), `timeOfDay` (forces a time, default is the device clock), `hidden`, `avatarSpeaking`, `onClickTarget(name)`, `children` (HTML overlay), `className`.
- `ForestWorld.jsx`: composes the scene (clock, backdrop, procedural forest or Blender model, particles, butterflies, camera rig).
- `ProceduralForest.jsx`, `geometry.js`, `materials.js`: ground with a winding path, instanced wind-sway grass, dandelions and pink/white flowers, round trees, pines and bushes, all in code. Each flower head is one quad, and the shader paints the round dandelion or the five petals on it. The trees use a painterly shader (soft wrapped light, cool shadows, warm tops, noisy leaf clumps) instead of a lit material. Grass and flowers turn lime toward the horizon, as in the paintings.
- `Backdrop.jsx`: the painted image (`/backgrounds/fantasy-meadow-1600.webp`) on a distant curved cylinder, plus stars and moon.
- `Particles.jsx`, `Butterflies.jsx`: pollen, sparkles, fireflies, three butterflies.
- `SceneClock.jsx`, `timeOfDay.js`, `palette.js`: time of day from the device clock only (morning 05-09, noon 10-16, Maghrib 17-19, night otherwise).
- `CameraRig.jsx`: camera glide, breathing, small clamped pointer parallax, and pinning of the avatar layer.
- `ForestModel.jsx`, `useForestManifest.js`: the Blender contract below.
- `forestFlag.js`, `quality.js`, `runtime.js`, `forestContext.js`, `ForestBoundary.jsx`: flag, quality tiers, shared state, error boundary.

## The avatar
`Avatar.jsx` is used as is, apart from a `controlRef` (dev handle) and the clip-driven walk-in. It owns its own `<Canvas>`, so it cannot live inside the forest canvas. Instead it is a transparent, pointer-events-none layer above the forest canvas. The built-in scene keeps the avatar's feet where `Avatar.jsx` draws itself for the current aspect (x = -0.13 on wide screens, -0.02 on narrow ones). Every frame `CameraRig` projects the avatar's feet in the forest camera and sets a CSS translate and scale on the layer so the feet stay on the path, and sets a CSS filter that tints the avatar for the time of day. A soft contact shadow is drawn in the forest canvas.

## Shared Blender contract
The Blender pipeline writes two files:
- `frontend/public/models/forest/forest.glb`
- `frontend/public/models/forest/forest-manifest.json`, shaped as `{"model":"/models/forest/forest.glb","version":<int>,"bytes":<int>,"triangles":<int>,"source":"<blend file name>","generated":"<ISO time>"}`

Behaviour:
- The manifest is fetched once. If the fetch fails, or the response is not valid JSON with a `model` string (Vite's SPA fallback returns `index.html` with status 200, so this is checked), the procedural forest is used. Nothing breaks without the files.
- The model URL gets `?v=<version>` for cache busting.
- Export the GLB **without Draco**. Meshopt (what the pipeline writes) and plain files both load; the meshopt decoder ships with the bundle and no Draco decoder is fetched from a CDN. Textures must be embedded or relative.
- Node names:
  - empties `AvatarSpot` (where the avatar's feet go), `CamStart` + `CamStartLook` (idle wide shot), `CamTalk` + `CamTalkLook` (talking shot). Missing empties fall back to the built-in defaults. Empties are read with `getWorldPosition`. `frontend/public/models/forest/` holds no committed model; the real file arrives from the pipeline.
  - meshes named `Sway_*`, or with a `Sway_*` ancestor, get the wind-sway shader. The pipeline quantises positions, so the bend weight uses the vertex's world height measured against the object's world bounding box (base of the box stays still, the top moves most). No origin placement is needed. The material parts of one object share one box, so a two-material tree bends as one piece.
  - objects named `Click_*` (or children of one) are clickable. A click calls `onClickTarget(name)` with the object's name, and each object gets one real HTML button (screen-reader and keyboard only). three.js splits a multi-material mesh into parts (`Click_shelf_1`, `Click_shelf_2`), and the pipeline can move an object's mesh into a same-named child (`Click_lamp_1`); those parts report the object's name (`Click_shelf`, `Click_lamp`) and get no button of their own.
  - nodes named `Sky*` or `Backdrop*` hide the painted backdrop, so the model can bring its own sky.
  - Blender lights and cameras are ignored. The scene lighting and fog come from the time of day.
- Triangle budget: about 60k for the scene, excluding the avatar.

## Phones and safety
- Quality tiers: `low` for coarse pointers or a short side under 700 px (fewer instances), `high` otherwise. The pixel ratio is capped at 1.5 on low and 2 on high. No post-processing anywhere.
- Instancing keeps the draw calls near 25. The frame loop is paused when the tab is hidden and when the stage is hidden (chat mode).
- `prefers-reduced-motion`: the camera does not glide (it cuts), sway and particles are much calmer, no pointer parallax, the poster fades in gently.
- If WebGL is missing, the context is lost, or anything in the canvas throws, the stage falls back to the meadow image (`data-state="fallback"`). The avatar layer has its own error boundary.
- All text is HTML (Arabic and RTL safe). Nothing is drawn as 3D text.
- The stage exposes `data-forest-stage`, `data-time`, `data-phase`, `data-quality` and `data-state` (`loading`, `ready`, `fallback`) for tests. In DEV only, `window.__forestStats` and `window.__forest` are published.

## Known trade-offs
- There is no foreground grass in front of the avatar, because the avatar is a separate canvas layer on top.
- The avatar canvas keeps its own pixel ratio cap of 2.
- With the flag on, the avatar model starts loading when the idle screen mounts (a plus for task 06, a cost on slow links).
- R3F events use the stage root as the event source, so a click on the HTML UI also reaches the canvas. This only matters for `Click_*` objects.
- With the flag on, the Avatar chunk splits into a small `Avatar` chunk and a separate Gltf chunk; the total is about the same.
- The built-in night look, stars and fireflies are procedural, not from the painted image. The painted backdrop is only tinted for night.
- Flower rims use alpha to coverage on the high tier (MSAA on). The low tier has no MSAA, so the rims are a plain alpha cut and slightly harder.
