# Handoff: 06b forest scene

Written 2026-10-04 on branch `hk/06b-forest`. Owner: Majd. Last commit: `5c221c6`. Nothing is pushed.

## 1. What this is

A 3D forest that sits behind the avatar on the child "Talk with Sadiq" screens. It replaces the flat meadow photo. It is an MVP for the live demo, and it is **off by default** behind a flag.

- The avatar stands on a dirt path in a flowery meadow with trees, painted to look like our two AI-made meadow paintings.
- It has four looks from the device clock: morning, noon, Maghrib, night.
- The camera glides from a wide idle shot to a closer talking shot when a session starts.
- Abdulrahman Mahmalji's Blender forest can replace the built-in forest later. No code change is needed, only two files (see section 4).
- Task file: `docs/hackathon/tasks/06b-forest-scene.md`. Contract and file list: `frontend/src/features/child/components/forest/README.md`.

## 2. What was built and why

Five commits since `e7c98a3` (the hackathon base), all by Majd:

| Commit | What |
|---|---|
| `d6ddb72` | The scene, the flag, the dev preview, motion, time of day, glide, fallbacks, and the first version of the Blender contract. |
| `cd2bf27` | Fix: the avatar keeps its size after a resize, and unmounts in chat mode. |
| `5985b07` | The look. Round painted flowers, low lime grass, painted trees, smaller butterflies. Phone talk view: the avatar was off to the left, now centred. Night no longer turns the fur teal. |
| `5a42f8c` | The Blender loader: world-space wind sway for the pipeline's compressed models, Sway_ and Click_ matched on ancestors, avatar shadow follows `AvatarSpot`. |
| `5c221c6` | Fix: a Blender object with several materials is one click target and one sway box. |

Why it is built this way:
- The first goal was to look like the paintings, so the scene is built in code first and is demo-safe today.
- The avatar stays a separate canvas layer. `Avatar.jsx` is not modified (git shows no change under `components/avatar/`).
- The scene is cheap on purpose: instancing, no post-processing, capped pixel ratio. The phone is the real target.

## 3. Where it lives

Worktree: `%USERPROFILE%\Documents\Alsadiq-wt\06b-forest`, branch `hk/06b-forest`, working tree clean.

Scene code: `frontend/src/features/child/components/forest/` (about 20 files).

| File | Job |
|---|---|
| `ForestStage.jsx` | The full-size stage and its fallbacks. Props: `phase` (`wide` or `talk`), `timeOfDay`, `hidden`, `avatarSpeaking`, `onClickTarget`. |
| `ForestWorld.jsx` | Builds the scene. Draws the built-in forest until the Blender model has loaded. |
| `ProceduralForest.jsx`, `geometry.js`, `materials.js` | Built-in forest: ground and path, grass, flowers, trees, pines, bushes, shaders. |
| `ForestModel.jsx`, `useForestManifest.js` | Loads the Blender model and reads the contract. |
| `CameraRig.jsx` | Glide, breathing, small pointer parallax, pins the avatar layer to the path. |
| `timeOfDay.js`, `palette.js`, `SceneClock.jsx` | Time of day and the four palettes. |
| `Backdrop.jsx`, `Particles.jsx`, `Butterflies.jsx` | Painted backdrop, stars and moon, pollen, fireflies, three butterflies. |
| `forestFlag.js`, `quality.js`, `runtime.js`, `ForestBoundary.jsx` | Flag, phone tier, shared state, error boundary. |
| `ForestPreviewPage.jsx` | Dev-only preview page. |

Other touched files (kept small, flag only):
- `frontend/src/pages/child/ConversationPage.jsx`: loads `ForestStage` lazily and wraps each screen with it when the flag is on.
- `frontend/src/features/child/components/VoiceMode.jsx`: a `forest` prop skips the meadow image and the avatar wrapper.
- `frontend/src/App.jsx`: the dev-only `/dev/forest` route.
- `frontend/public/backgrounds/fantasy-meadow-1600.webp`: the backdrop texture (95.8 kB).
- `frontend/public/models/forest/README.md`: the drop folder. No model is committed.

## 4. How to run, test and verify

Run it:
```
cd %USERPROFILE%\Documents\Alsadiq-wt\06b-forest\frontend
npm install
npm run dev
```
- Preview page: `http://localhost:5173/dev/forest`. Options: `?t=morning|noon|maghrib|night` and `?phase=wide|talk`. The page has time buttons and a Start session button for the glide.
- Real screen: open the child talk page with `?forest=1`. It is remembered in `localStorage` key `sadiq_forest_scene`. `?forest=0` turns it off and forgets it.
- Build-time switch: `VITE_FOREST_SCENE=1`. It is not set in any env or compose file.

Checks (re-run on 2026-10-04 for this handoff):
```
npm run lint     # clean
npm run build    # passes. ForestStage chunk 47.70 kB (16.74 kB gzip). Main bundle 260.82 kB gzip.
```
There is no JS test setup in `frontend/`, so there are no unit tests. Earlier reviews tested by hand in Edge with Playwright (`channel="msedge"`).

Test the fallbacks: with no manifest, with a manifest that is not JSON, and with a manifest pointing at a missing `.glb`, the page shows the built-in forest. With no WebGL the stage shows the meadow image (`data-state="fallback"`). Test hooks on the stage: `data-forest-stage`, `data-time`, `data-phase`, `data-quality`, `data-state`. In dev only: `window.__forestStats` and `window.__forest`.

### The GLB contract and how to drop in Abdulrahman's file
The pipeline (outside git, `%USERPROFILE%\Documents\blender-mcp\forest-pipeline\`) writes two files into `frontend/public/models/forest/`:
- `forest.glb`
- `forest-manifest.json` = `{"model":"/models/forest/forest.glb","version":<int>,"bytes":<int>,"triangles":<int>,"source":"<blend file>","generated":"<ISO time>"}`

Steps:
1. Put his `.blend` in `%USERPROFILE%\Documents\blender-mcp\incoming\`.
2. Run:
   ```
   powershell -NoProfile -ExecutionPolicy Bypass -File "%USERPROFILE%\Documents\blender-mcp\forest-pipeline\prepare-forest.ps1" -Blend "%USERPROFILE%\Documents\blender-mcp\incoming\forest.blend" -Install
   ```
   The last line says `RESULT: OK` or `RESULT: FAILED`. Without `-Install` it only writes to `forest-pipeline\out\`.
3. Read `forest-pipeline\out\inspect.txt` for warnings.
4. Open `/dev/forest`. `window.__forestStats` should show GLB mode, and the look and camera framing should be right.
5. Commit the two files yourself. The pipeline never commits.

Names Abdulrahman must use in Blender (exact):
- Empties: `AvatarSpot`, `CamStart`, `CamStartLook`, `CamTalk`, `CamTalkLook`. Missing ones fall back to defaults.
- Meshes: `Sway_*` gets wind sway. `Click_*` is clickable.
- Nodes named `Sky*` or `Backdrop*` hide the painted backdrop.
- Lights and cameras in the file are ignored.
- Export format: meshopt, no Draco. The pipeline already does this.

How the loader treats the file:
- The manifest is checked, not just fetched. Vite answers a missing file with `index.html` and status 200, so the body must be JSON with a `model` string ending in `.glb`.
- The model URL gets `?v=<version>` so a new install is not cached.
- `Sway_` and `Click_` match on the object or any ancestor. The parts of one multi-material object count as one object (one button, one sway box, one reported name).
- Positions are quantised, so sway uses world height against the object's world bounding box.
- While the model downloads, the built-in forest stays on screen. If it fails, the error boundary keeps the built-in forest.

## 5. Decisions and why

- **Opt-in flag, default off.** The demo must not depend on a heavy 3D scene that is unproven on phones. Flag off means nothing changes.
- **Day 2 17:00 gate.** If the scene is not smooth on phones by then, the live demo keeps the meadow image. The forest then appears only in the demo video.
- **Procedural first.** The scene works today in code. The Blender model slots in later through a small contract.
- **Avatar is a separate canvas layer above the forest.** `Avatar.jsx` owns its own canvas and the task says not to modify it. `CameraRig` projects the avatar's feet each frame and moves and scales the layer to match. Cost: no foreground grass in front of the avatar.
- **Round flowers are one square each,** with the dandelion or five petals drawn in the shader. This looks like the paintings and costs fewer triangles than modelled petals.
- **Grass is a low carpet that turns lime toward the horizon.** Taller grass at distance made a green wall.
- **Time of day from the device clock only.** Morning 05:00 to 09:59, noon 10:00 to 16:59, Maghrib 17:00 to 19:59, night otherwise. No location or network. Maghrib is a fixed window, a mood and not a prayer time.
- **Night look on the avatar is darker and greyer,** not hue-shifted. A hue shift turned the brown fur teal.
- **No Draco, no post-processing.** No CDN fetches, and the phone budget stays small.
- **Do not keep procedural grass over the Blender model.** It could clip against a different ground, so it was skipped.
- **Chat mode:** the stage stays mounted but hidden and paused (no drawing), so it does not reload when the child returns to voice.
- **Reduced motion:** the camera cuts instead of gliding, sway and particles are calmer, and there is no pointer parallax.

## 6. Current status

Done (steps 1 to 8 and the lint and build step in the task file):
- Scene, motion, four times of day, glide, avatar layer, flag, dev preview, phone measures, Blender contract and loader.
- Reviewed: look reviewer and loader reviewer both said ship-with-notes.

Not done:
- **Step 9:** real-device check on a mid-range Android phone and an iPhone. Only software rendering has been used, which proves it draws, not that it is smooth.
- **Step 10:** Abdulrahman's real model has not arrived. The loader was tested only with the pipeline's own sample forest (27,574 triangles, 0.55 MB), which has been removed.
- Not pushed, no PR. The PR goes into `hackathon`.

Phone budget numbers (measured in Edge with software rendering, so triangle and draw numbers are exact and speed is not):

| Case | Triangles | Draw calls | Pixel ratio |
|---|---|---|---|
| Built-in forest, desktop 1440x900 | 54,538 | 26 | up to 2 |
| Built-in forest, phone 390x844 | 33,316 | 18 | capped at 1.5 |
| Pipeline sample model, desktop | 27,574 | 39 | up to 2 |
| Pipeline sample model, phone | 27,574 | 28 | capped at 1.5 |

Other budget rules: about 60k triangles for the scene (avatar excluded), at most about 25 draw calls for the built-in forest, and the pipeline warns above 150 mesh nodes. The phone tier is picked for coarse pointers or a short side under 700 px, and it uses fewer instances (grass 1000 against 1600, dandelions 650 against 1100, blooms 700 against 1200) and no anti-aliasing.

Bundle: with the flag off, the main bundle is 260.82 kB gzip. The lazy `ForestStage` chunk (16.74 kB gzip) loads only with the flag on. No forest preview code reaches the production bundle.

## 7. Known issues

- Not checked on a real phone. See step 9.
- The real Blender model is untested, so its look and the time-of-day tint are unknown.
- On the phone tier (no anti-aliasing) flower edges are a little harder than on desktop. Tree crowns show some polygon edges up close.
- In Blender-model mode the portrait-phone camera adjustment is off. A phone sees a narrow strip around `CamStart`. Anything clickable or the avatar must be near the centre line of `CamStart`, or it can be off screen.
- The sample's talk camera crops the avatar at the waist. For the original framing, `CamTalk` should be about 3.2 m in front of `AvatarSpot` at 0.9 m height, and `CamTalkLook` at 0.7 m height on `AvatarSpot` (these are the built-in defaults).
- The `AvatarSpot` rotation is ignored. The avatar is a flat layer, so only its position is used.
- A `Sway_` parent with separate child objects gives each child its own sway box. An apple hanging from a swaying tree would sway on its own.
- `Click_*` targets report a name through `onClickTarget`, but `ConversationPage.jsx` does not pass that prop, so nothing in the real app reacts to them yet. Only the preview shows "Clicked: name".
- With no WebGL the Avatar's own canvas logs an error. This also happens without the forest.
- The `THREE.Clock` deprecation warning in the console comes from React Three Fiber.
- Every Blender material exports double-sided (a pipeline note). It is a small GPU cost.
- `npm ci` failed on the older `package-lock.json` (missing platform packages) per the builder report. I did not re-test it here. The 06 avatar branch changes the lock file, so expect a conflict there.
- Nothing searched GitHub or git history for API keys. See section 9.

## 8. Next steps and improvements, ordered by value

1. **Real-device check (step 9), before Day 2 17:00.** Open `?forest=1` on a mid-range Android phone and an iPhone. Check the glide, sway and frame rate. If not smooth, keep the meadow image in the live demo (the gate). Possible quick wins if slow: lower the `low` counts in `quality.js`, cap the pixel ratio at 1.25, or drop butterflies and particles.
2. **Get the `.blend` from Abdulrahman and run the pipeline (step 10).** Ask him for: the five empties named exactly, `CamTalk` about 3.2 m in front of `AvatarSpot` at 0.9 m height, clickable and key things near the centre line of `CamStart`, image textures (the pipeline flattens procedural materials to one colour), and about 60k triangles in total. Then tune the palettes in `timeOfDay.js` for his look.
3. **Merge safely.** Push `hk/06b-forest` and open the PR into `hackathon` only when Majd is happy. Expect small conflicts in `ConversationPage.jsx` (the 06 avatar branch adds a warm-up effect there, and task 07 voice work touches it) and in `package-lock.json`. Regenerate the lock rather than merging it by hand.
4. **Wire `onClickTarget`** in `ConversationPage.jsx` if Abdulrahman adds `Click_` objects, and decide what a click does.
5. **Disclosures for task 10:** add the lines below to the submission.
6. Optional: foreground grass layer (needs the avatar inside the forest canvas, which is a task 06 change), a texture bake for painterly shaders in the pipeline, and a hosting check that the `.glb` and manifest are served with the right headers.
7. Optional: add a small test setup (Vitest) for `validateManifest` and the name-matching helpers.

## 9. Gotchas

- **Default is off.** If you see no forest, check `?forest=1` or `localStorage` `sadiq_forest_scene`.
- **`/dev/forest` exists only in `npm run dev`.** It is removed from production builds.
- **Dots in names:** three.js strips dots from node names (`CamStart.001` becomes `CamStart001`). The loader accepts a numeric suffix on the empties.
- **Do not commit sample models.** `frontend/public/models/forest/` holds only `README.md`. `frontend/dist` is gitignored, and `npm run build` rebuilds it (a stale sample was in it until the build I ran for this handoff).
- **`forest-pipeline\out\` holds a leftover sample** (`source` is `sample.blend`). Do not install from it. Run the real command with the real file.
- **The pipeline never edits the `.blend`,** and checks the file hash after each run. `-Install` backs up the old files to `forest-pipeline\out\backup\<timestamp>\`. The manifest version goes up by 1 on each install, which busts the browser cache.
- **Use Playwright with `channel="msedge"`** for browser checks. Never click `mailto:` or `tel:` links (Windows pops up a "Pick an app" dialog).
- **Software rendering is slow** (about 5 fps under SwiftShader). That says nothing about real phones.
- **Islamic content rules** (`AGENTS.md`): this task has no scripture and no Arabic text in code or data (checked with a search of the forest folder and the task file). TTS and content rules are task 07 and 01 to 04.
- **API keys:** the 06b builder and the loader reviewer only scanned tracked files in this checkout (no real key patterns; only placeholders in `.env.example` and the Django dev default in `settings.py`). GitHub itself and git history were not scanned. Do not print `.env` files.
- **Disclosure lines for the submission (task 10):**
  - The painted meadow backgrounds (`fantasy-meadow.webp` and the 1600 px copy used as the backdrop) are AI-generated images already in the repo.
  - The avatar model is generated with Tripo (task 06).
  - The procedural forest is our own code, built on `three`, `@react-three/fiber` and `@react-three/drei` (MIT). No other third-party 3D assets were added.
  - Abdulrahman's `.blend` is pre-existing work that predates this task and is used as supplied. Anything added to it during the hackathon must be listed separately.
