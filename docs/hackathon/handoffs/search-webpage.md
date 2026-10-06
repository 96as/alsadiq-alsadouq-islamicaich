# W3 Search web page in his hand (hk/search-webpage)

## Done
- A real browser window is held above his left palm (prop_L) while he searches the web. 0.24 x 0.32 m, logical 360 x 480.
  - Chrome with three dots, a URL pill (domain only), a query box, a procedural hero picture (sky, rainbow, bees, and so on), a topic title and result cards (title, domain, snippet).
  - A skeleton shimmer shows before the results arrive. Arabic is fully RTL (cards right-aligned, domains stay LTR).
  - The page scrolls. It drifts at 14 px/s while reading and flicks on SearchSwipe (flick time constant 0.33 s, at most 6 flicks, rubber band 24 px).
  - On Found the page springs so the card sits at 25% of the viewport, and the card gets a gold ring, glow and warm tint.
  - A camera-facing hero hold follows (min-jerk out 0.45 s, hold 2.0 s, back 0.45 s). Landscape slides out to the side. Portrait drops below his chin, then slides, so the window never crosses his face.
- Rendering is 1 draw call (one quad, one shader, three 480 px atlas tiles, 2 bands per tile, 1 upload per frame). Text is rasterised at texture scale 2.5 (phone tier 1.75) with a light in-shader unsharp mask. The window adds no halo or sparkle draw calls, and the old panel is hidden while it is up.
- Fed by the `al.search` topic, by the signal simulator and by the meadow showcase (Search tab, "Search the web" chips: sky-found, bees-found, sky-none, sky-grownup, in Arabic and English).
- Content filter: only fixture or tool text reaches the page. Scripture-like text gives a grown-up card, only a domain is ever shown, and no external images are used. The fonts are the app's own Baloo Bhaijaan 2 and IBM Plex Sans Arabic from Google Fonts (index.html loads them; the two preview pages now link the same stylesheet). The page itself makes no request (0 requests during a whole search, measured in review).
- Reduced motion: no scroll bar, no shimmer (`uShim = -5`), no sway, no hero move and no drift. The page jumps to the found card, and only the fade remains.

## Files
- New, in `frontend/src/features/child/components/avatar/hologram/webPage/`:
  - `contentFilter.js`, `pageLayout.js`, `pageRenderer.js`, `heroArt.js`, `fixtures.js`
  - `scrollPhysics.js`, `readingGaze.js`, `heroLayout.js`
  - `webPageShader.js`, `WebPagePanel.js`
- Hot-file edits, all marked `// w3`: `avatarSignals.js`, `useLiveKitRoom.js`, `avatarConfig.js`, `holoTimeline.js`, `avatarDirector.js`, `holoEnvelope.js`, `hologramShader.js`, `HologramRig.js` (`placeHero`, warm-up), `ClipAvatar.jsx`, `useSignalSimulator.js`, `SignalSimulatorPanel.jsx`, `MeadowShowcase.jsx`.
- Fonts link in `avatar-preview.html` and `avatar-component-preview.html`.
- Tests: `frontend/tests/webPage.test.mjs` (47 tests, one added in review), run with `npm run test:webpage`.

## Run and test
- Dev: `VITE_SHOWCASE=1 npx vite` and open `/meadow`. Panel, Search tab, chip "Search the web".
- Dev pages: `/avatar-component-preview.html?sim=1`, then `window.__sim.searchWeb('sky', {outcome:'found', lang:'en'})`.
- `npm run lint`, `npm run test:webpage` (47/47), `npm run test:avatar` (78/78) and `npm run build` (plus the showcase build) all pass.
- The browser tooling (Playwright, msedge) is outside the repo in `Alsadiq-wt\search-webpage-tools` (`wp1.py`, `rec.py`, `sharp.py`, `wp8.py`, `recvid.py`).

## Gates (measured, headed Edge, off-screen)
| Gate | Result |
|---|---|
| WP-1 no cover of mouth or eyes | 0 overlaps at 2000x713, 1440x900 and 390x844, en and ar. Sampled every 0.2 s, which is more than the 12 frames asked for. |
| WP-2 sharpness vs DOM, DPR 2 | Laplacian ratio 0.86 (1440x900), 0.94 (390x844), 1.18 (2000x713). All within +-25%. |
| WP-2 at DPR 3 | NOT met: 0.21 to 0.25. The R3F canvas is capped at `dpr={[1, 2]}` in Avatar.jsx, so DPR 3 is upscaled. See open issues. |
| WP-3 frames over 33 ms under 4x CPU throttle | Panel JS: update mean 0.02 ms, pump mean 0.03 ms. Max pump task 10.8 ms (layout, on a frame with no band drawn). 1440x900: 2 over-33 frames, both in the first 0.6 s before the window exists (dev React re-render). 390x844 ar at DPR 2: 5 over-33 frames at 34.6 to 35.6 ms, all before the window is up (one coincides with the first warm band, 2.3 ms of work). None during scroll, flick, found or hero. |
| WP-4 scroll | Drift 14 px/s. A flick travels +3% of one card. Never past the rubber band. |
| WP-5 RTL | Cards right-aligned, domains LTR, no broken words (checked in stills). |
| WP-6 content | Only fixture or tool text. A scripture-like fixture gives the grown-up card. Domain only. Covered by unit tests. |
| WP-7 reduced motion | Emulated: shim -5, scroll bar 0, hero 0 (hk stays 0), one scroll jump to the found card, mode read then found. The window still follows his hand and the avatar's own idle body animation, which is outside W3. |
| WP-8 library and folder searches | Unchanged at 1440x900 and 390x844. The old panel shows, the web window never appears and the draw calls are as before. Web chips use the window. |
| Budget | The window is 1 draw call (5 in total at 1440: avatar, beam, halo, sparks, window. 3 at phone). At most 4 uploads in a whole search (1 + 3 as the tiles fill), at most 3 per content state. |

## Decisions
- One quad with an atlas rather than several meshes: 1 draw call and a trivial scroll (a uniform).
- The sharpness shader is a mask rather than a bigger texture. A higher scale gave no gain (ratio plateau about 0.42), because hinted DOM text cannot be matched by canvas resampling alone. The mask is stronger on the phone tier (0.9 against 0.55), where texels are below 1 device px.
- Found tint is multiplicative. A mix toward gold turned dark text olive.
- An idle `warm()` pre-draws fonts and layouts, which removed a 14 to 15 ms first-use spike.
- Portrait hero path: first drop, then slide (separate eases on the camera up and right axes), so it never sweeps across the face.

## Open issues
1. DPR 3 sharpness (WP-2 at DPR 3). Fix is a one-line change of the Avatar.jsx Canvas `dpr` cap from 2 to 3 (or raise it only during the hero hold via `setDpr`). I did not make it, because it triples the pixel cost of the whole 3D scene on phones. Needs a device GPU decision.
2. In the meadow showcase at 390x844 and 1440x900, the hero window's bottom edge sits behind the showcase's own mic and "Meadow" pill UI. It is page chrome, not the avatar. In the real app, pass the safe stage rect to `heroRect` if the real controls overlap.
3. WP-3 was measured against the dev server, not a production build. Production should only be better.
4. The 20 s videos have no audio. Playwright records webm, which was converted with a local ffmpeg.
5. `web-found` and `web-none` chips of the old panel (not `data-search-web`) deliberately keep the old panel.

## Renders
`%USERPROFILE%\Documents\Alsadiq-3D\03-renders\studio\webpage\`
- `websearch-1440x900-en-sky-found.mp4`, `websearch-1440x900-ar-sky-found.mp4` and `websearch-390x844-en-sky-found.mp4`: 20 s each (search start, skeleton, results, scroll flicks, found highlight, hero hold, close).
- `still-*` PNGs. `scratch\` holds the raw measurement JSON and the sharpness crops.

## Review (Opus reviewer, 2026-10-05)
Measured on a fresh dev server (5392) with headed, off-screen, muted Edge, through the real meadow chips with the panel closed. Tools are outside the repo in `Alsadiq-wt\search-webpage-review` (`rv.py`, `stills.py`, `wp8r.py`, `dbg_safety.py`).

Fixes made (commit "W3 review"):
1. Phone: the held window hung 13 to 17 css px off the right edge of a 390 x 844 screen for the whole reading, en and ar (visible in `still-390x844-en-sky-found-06.5.png`). Cause: frame safety ran at the open while the palm was still rising, so its shift was for the low hand (it pushed the window toward the edge to clear the head). Now `HologramRig.webSafety` re-checks the web window every 0.25 s while it is held, starting from where it is heading (a safe placement is left alone, so it never wobbles), with a head circle 1.3x wider for the cheeks, shrinks when squeezed between the face and the edge, and eases in about 0.25 s. Result at 390 x 844: 0 samples off screen after the open (2 px for one sample during the materialise), goal stable at shift -0.015, scale 0.857 from 1.5 s on. 1440 x 900 and 2000 x 713 unchanged (0 off screen). Library and folder panels untouched (`frameSafety` without `keep` is the old code path).
2. Scroll: the drift was gated on `vel < 1`, so it stayed off for about 2 s after every flick and with a flick every 1.6 to 2.4 s the page all but stopped (2 to 3 px/s) before each one; measured median 7 to 11 px/s, not 14. The drift now runs under the flick. New test "the page never stalls between flicks" (fails at 4.2 px/s without the fix). The flick test still gives one card within 2%.
3. Reduced motion: no SearchStart plays, so the palm stayed at his waist and the page sat half behind his arm and sweater (1440 and 390). The reduced-motion page is now held still at the raised-palm spot beside the left shoulder (`REDUCED_WEB_ANCHOR`, BEHAVIOUR-SPEC 6.11), no beam, fully visible, placed once.
4. Meadow showcase: "Search the web: why is the sky blue" overflowed its nowrap chip and overlapped the next one at 390 px. The found chips now show the query alone; the section label is "Web page in his hand". No overflow at 360, 390 and 1440 (measured).
5. Rule fix: `webPage.test.mjs` used a line of scripture (the basmala, fully voweled) as its diacritics sample. Replaced by an everyday voweled sentence about the sky, and the fold test by a plain word. A scan of every file the branch touches finds no other voweled religious text (the filter's meta words stay; they are detectors, not text).

Re-measured after the fixes:
| Check | Result |
|---|---|
| Window on screen (390 x 844 en, ar) | 0 samples off screen in reading and hero; before: 91 to 100 samples, up to 17 px |
| Window vs eyes and mouth | never over the mouth or an eye. True gap from the window to the eyelid region: phone median 29 css px (min 8.5 during the materialise), 1440 median 57, 2000 x 713 median 41. The builder's stricter WP-1 metric (eye box grown by 60 percent, 39 px on a phone) now flags the phone in-hand samples, because the window moved left to stay on screen; visually it sits beside the cheek |
| Frame cadence | median 17.5 ms, p95 18 ms at 390 DPR 2, 1440 and 2000 x 713. The only long frames were the test's own screenshots |
| Draw calls | window 1; 1 to 3 total on the phone, 2 to 5 at 1440 |
| External requests during a search | 0 |
| Reduced motion (390 en, 1440 ar) | page beside the left shoulder, still, fully visible, 0 samples off screen; gap to the eyes median 30 css px (phone) and 51 (1440); scroll 0 then one jump to the found card; no hero |
| Re-check cost | `frameSafety(keep)` 0.0125 ms per call at 4x CPU throttle, every 0.25 s |
| WP-8 | library and folder searches before and after web searches: never the web window, old panel shows, all close |

Review renders (after the fixes, 20 s, no audio): `%USERPROFILE%\Documents\Alsadiq-3D\03-renders\studio\webpage\review\websearch-390x844-en-sky-found-review.mp4` and `websearch-390x844-ar-sky-found-review.mp4` beside it.

Still open (not changed in review): the SearchSwipe paw brushes at his chest, not on the page, so the flick looks self-driven until P6's SearchScroll_W lands; DPR 3 sharpness (Avatar.jsx dpr cap), the showcase's mic, speaker and Meadow pill sit over the bottom of the hero window on a phone, WP-3 on a production build, GPU cost of the 5-tap unsharp mask on a real mid-range phone (spec budget 0.4 ms in hand, 0.8 ms hero) not measured.
