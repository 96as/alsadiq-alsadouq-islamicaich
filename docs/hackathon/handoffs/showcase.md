# Handoff: showcase build (branch hk/showcase)

Branched from `hk/demo-mvp` (6fc60f8). Not pushed, no PR.

## What it is
A static build of the animated demo for the team site, served under `/page/`: the forest scene, the landing visuals and the avatar states. No backend.

## Build
From `frontend/`, in Git Bash set `MSYS_NO_PATHCONV=1` first (otherwise `/page/` becomes a Windows path):

```
MSYS_NO_PATHCONV=1 VITE_SHOWCASE=1 VITE_FOREST_SCENE=1 npx vite build --base /page/
```

Output: `frontend/dist-showcase` (gitignored, about 11 MB; the two 43 MB source avatar models are left out, only `avatar-web.glb` ships). Test with `VITE_SHOWCASE=1 npx vite preview --base /page/ --port 5331`.

## What changed
- `src/utils/assetUrl.js`: `assetUrl()`, `ROUTER_BASENAME`, `SHOWCASE`. Every absolute public asset URL (avatar GLB, meadow images, forest manifest and model, badges) goes through `assetUrl`; the router uses `ROUTER_BASENAME`. With base `/` nothing changes.
- `VITE_SHOWCASE=1` (off by default): `App.jsx` mounts only `/` (index page), `/dev/forest` and `/landing`; unknown paths go to the index. The landing's demo button shows "Demo login needs the live server" (Arabic and English), and its sign-in pill becomes a Showcase link. `api.js` rejects every request in this mode. The forest manifest is not fetched when none is shipped (`VITE_FOREST_MANIFEST=0`, set by the config), so there is no 404.
- `vite.config.js`: in showcase mode builds `avatar-component-preview.html` and `avatar-preview.html` as extra entries (base-aware model path, favicon, a Showcase link back), outputs to `dist-showcase`, drops the heavy models.
- `src/pages/ShowcaseIndex.jsx`: the bilingual card index.
- `eslint.config.js` ignores `dist-showcase`.

## Checks
Edge (msedge), against `vite preview --base /page/`: index (desktop and 390 wide, no horizontal scroll), forest walk-in, four times of day, session and speak, landing in Arabic and English with the demo button message, avatar states, walk-in and model views. No console errors, no 4xx, requests only to the preview host and Google Fonts. `THREE.Clock` deprecation warnings come from three, not this change.
Normal build (base `/`, no flag): `index.html` uses `/assets/...`, no `ForestPreviewPage` chunk, no `/dev/forest` string, `npm run lint` clean.

## Hosting notes
The `/page/` host must serve `index.html` for `/page/dev/forest` and `/page/landing` (SPA fallback) and the other files as they are, including `avatar-component-preview.html` and `avatar-preview.html`. Google Fonts load from the internet.
