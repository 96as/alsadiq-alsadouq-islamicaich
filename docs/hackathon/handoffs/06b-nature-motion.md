# 06b nature motion (WP3): the meadow and the forest on one wind

Branch `hk/06b-nature-motion`, worktree `%USERPROFILE%\Documents\Alsadiq-wt\06b-nature-motion`. Nothing is pushed.

## Look at it

- Dev server (already running): http://localhost:5331
  - Painted meadow, alive: http://localhost:5331/dev/meadow?panel=0
  - Forest: http://localhost:5331/dev/forest?t=noon&walk=off (add `panel=0` for a clean view; the panel now has a wind strength slider, Freeze time, Prints in grass, gust / sway / flutter switches and a stats line)
  - The forest follows the device clock unless you pass `t=noon|morning|maghrib|night`.
- Videos (real GPU, Edge with D3D11 on the RTX 5070 Ti, 16 s each, 30 fps) in `%USERPROFILE%\Documents\Alsadiq-3D\03-renders\studio\nature`:
  - `before-*` and `after-*` for `meadow` and `forest` at `2000x713` and `390x844`
  - `compare-*-2000x713-before-over-after.mp4` (before on top) and `compare-*-390x844-before-left-after-right.mp4`
  - `tools\` holds the scripts that made them and ran the gates (`record.py`, `forestcheck.py`, `forestperf.py`, `n6.py`, `n3n7.py`, `n8.py`).

## What was built

One wind field drives everything: a world-space gust field, with a CPU mirror (`forest/wind/windField.js`) and a GLSL twin (`windGlsl.js`). 17 node tests cover the maths (`npm run test:nature`).

- Painted meadow (`ambient/MeadowLife.jsx` plus `meadowLifeGL.js`, `meadowLifeShader.js`): the lead's painting is kept as is. A raw WebGL2 layer over it adds a masked warp of the grass and trees, a gust colour wave, cloud shadows and wisps, light shafts, painted blades, pollen and seeds. The poster image stays underneath as the fallback.
- Foreground strip (`forest/ForegroundStrip.jsx`): blades and spring flowers drawn in front of the avatar's feet, on the same wind clock. About 0.11 to 0.15 ms per frame.
- Forest, grass: every blade bends by a rotation about its own base, so its length cannot change (gate N2). 12 culled InstancedMesh chunks (4 depth rings by 3 sectors). Near blades have 5 triangles, far blades 3 and widen with distance. Clumps sway at their own rate, tips flutter near the camera only.
- Forest, flowers: the near 280 (140 on low) run real second-order springs on the CPU; the rest use the same formula in the shader.
- Forest, trees: a main crown bend, a branch tier and a leaf flutter.
- Forest, ground and sky: cloud shadows drift over the ground and grass. The backdrop painting gets a masked warp, a gust light wave and a cloud wisp, and is mirrored past its edges so ultra-wide windows show no lime bars.
- Avatar footprints: the last 8 prints push the grass away (lean about the base), fading over 2.4 s.
- Pollen and sparkles are steered by the gust.

## Gates

Measured with Playwright, Edge, real GPU, frozen clock pairs where noted.

| Gate | Result | Where |
|---|---|---|
| Tests, lint, build | 17 nature tests, 22 lipsync tests, eslint and `npm run build` all clean | repo |
| N1, N2, N4, N5 (maths) | pass in `tests/windField.test.mjs`; N2 holds by construction (rotation about the base) | node |
| N3 motion visible | meadow 26 to 31 % of the lower pixels change over 0.5 s; forest 45 % (1000x640), 16 % (390x780) | GPU |
| N6 foot push | a print in the open grass changes 5,116 px at 1400x900 (blades near the print lean away); small by design | GPU |
| N7 painted warp | sky and horizon diff 0, warp at most 3.4 px times scale, particles at most 12 | GPU, meadow |
| N8 | 0.0046 to 0.0073 | GPU, meadow |
| N9 reduced motion | meadow 1.4 to 3.6 %; forest changed share drops from 45 % to 23 % (1000x640) and 16 % to 6 % (390x780) | GPU |
| Draw calls (45 max) | forest 37 (high), 33 (low) | `window.__forestStats` |
| Triangles (220k high, 110k low) | 184k high (1400x900), 77k low (390x780) | `window.__forestStats` |
| F1, F2 | PARTIAL. With a 4x CPU throttle the forest frame time stays at 17.5 ms (p95 18 ms) on both tiers, so it is not CPU bound. I did not isolate the nature JS to a per-frame figure of 1.0 ms or less, and I did not run an allocation profile. | GPU |
| F3 real phones | NOT RUN. No phone was measured. The 390x844 runs are a desktop browser at phone size. | n/a |

## Decisions and honest deviations

- Grass tip bend is 32 degrees at full gust (`WIND.tipDeg`); this is a tuned value that differs from the Bible's number.
- N4 (flower spring) is applied to the dandelion spring with a 0.3 s ramp, my reading of the gate.
- The calm-share spread differs from the Bible's example (tuned by eye).
- The painted warp scales with the image scale (`sc`), so it stays 3.4 px at most at any size.
- On phones the poster and the GL texture are downloaded twice (poster for the fallback, texture for the layer).
- The foot push only shows off the path. Grass is cleared 0.05 m beyond the path edge and the push radius is 0.42 m.
- Grass coverage was widened (the old scatter left bare ground at the sides on wide windows). Near blades read a little darker than the old ones (ambient occlusion at the base times cloud shadow); lighten `ao` in `GRASS_VERT` if you want them brighter.
- `NatureDevPanel` is mounted with one line in `ForestPreviewPage.jsx` and in dev only.
- The only edit in `VoiceMode.jsx` is the import line that swaps in MeadowLife. The strip mount was removed in review; see the end of this file.

## Not done (cut order)

- Butterflies steered by the wind, dandelion seeds and the Blender `ForestModel` `Sway_*` objects on the wind functions. The forest's own procedural scene does not use `ForestModel`, so this only matters if that model is switched on.
- Avatar dimming under cloud shadows.
- A forest or painted switch in the dev panel.

## Next steps

- Measure F1 and F2 properly (per-frame nature JS time and an allocation profile) and run F3 on real phones.
- Merge order per Motion Bible 9.7; the forest files touched here are listed in commit `2210a0a`, the earlier two commits are `6b769c5` and `67609ea`.

## Reviewer changes (Opus review, 4 Oct evening)

Three changes on top of the build. Each was measured before and after; the scripts are in
`%USERPROFILE%\Documents\Alsadiq-3D\03-renders\studio\nature\_review\` (`rv_*.py`).

1. **The painting is sharp again on phones and HiDPI screens** (`ambient/MeadowLife.jsx`). The canvas covers the
   sharp `<img>` but was drawn at DPR 1 on the low tier and DPR 1.5 on the high tier, so every phone and Retina
   laptop saw a blurred painting. Laplacian detail in the trees and horizon band, compared with the plain `<img>`:
   DPR-3 phone 0.14 before and 0.24 after; DPR-2 desktop 0.35 before and 1.04 after. Both tiers now start at
   DPR 2 and step down 2 → 1.5 → 1.25 → 1 when frames are slow. GPU time of the whole layer at 1170x2532 is
   0.068 ms on the RTX 5070 Ti (0.035 ms at DPR 2), so even a phone GPU 50-100 times slower stays at 2-4 ms. This
   overrides Bible 7.10 ("MeadowLife DPR at most 1.5, 1.0 on low"): that cap undid the sharp-meadow hotfix on
   exactly the screens Majd complained about. A DPR-3 phone is still softer than the plain `<img>` (which loads the
   5120 file); see the fix list.
2. **Foreground strip removed from painted mode** (`VoiceMode.jsx`; Bible 9.4 cut order #4). At 1000x640, 390x780
   and 2000x713 it covered 0% of Sadiq's legs, because it sits entirely below his feet in the mic-row reserve. So it
   did not ground him. Its evenly spaced cone blades and sticker flowers also read as clip art over the painting.
   The component is unchanged and still mounts in forest mode; to restore it, add back
   `{!forest && <ForegroundStrip mode="painted" />}` after a repaint. `VoiceMode.jsx` now differs from
   `hk/06-avatar-live` only by the import line, which keeps the SPEC-frontend merge simple.
3. **The far meadow no longer sweeps faster than the foreground** (`forest/wind/windField.js` `screenToWorld`,
   mirrored in `meadowLifeShader.js` `screenWorld`).
   - The screen-to-world spread used to shrink toward the horizon (8.4 m per screen width there, 24 m at the bottom),
     which is the opposite of perspective. Distant gust patches were 3.7 screens wide and crossed at about 0.3
     screens/s, so the far band pulsed and swept.
   - It is now `24 / (0.3 + 0.7 d)`: 24 m at the bottom, unchanged, so the strip sync is unchanged too, and about
     76 m at the horizon. Far patterns now travel at about 80 px/s at 2000 px wide.
   - The silver ripple keeps 65% of its contrast at the horizon (aerial perspective).
   - Mean change per frame, far band against near band: 1.38 against 1.01 before, 1.05 against 1.04 after.
   - N3 after the change: 25.4% at 1100x640 and 28.4% at 2000x713 (gate 25-60%). At 390x844 it is 23.4%.
   - The N8 GPU/CPU gust agreement is still at most 0.0072.

All four checks pass after the changes: `npm run lint`, `npm run build`, `test:nature` 17/17 and `test:lipsync` 22/22. There are no console errors on
`/dev/forest` (1000x640, 390x780) or `/dev/meadow` (390x780). With WebGL disabled, `/dev/meadow` still shows the
plain `<img>` (`data-meadow-life="poster"`, no canvas).

Reviewer media, frame-stepped at exact 30 fps wind time: the avatar keeps its own real-time clock there, so its
motion is aliased; use these for nature timing only. They are in `_review\`: `final-wide.mp4` (2000x713, 6 s) and
`final-phone.mp4` (390x844 at DPR 3, 4 s).
