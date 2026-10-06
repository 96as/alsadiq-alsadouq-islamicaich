# Handoff: pw-ops (judging-day capacity, Arabic greeting, landing scene, submission docs)

Branch `hk/pw-ops` (from `hk/product-web` at dd50ac4), worktree `Alsadiq-wt/pw-ops`. Nothing pushed, no PR, nothing posted to the team
brain. Author: the ops agent (Claude Code), 2026-10-05. Part of `hk/product-web` section 11 (pointer added there).

## 1. What was built

1. **Demo capacity for about 30 judges behind one NAT.**
   - `DEMO_POOL_SIZE` default 8 to 40 (40 families in `demo/content.py`, slots 9 to 40 added; max is 40).
   - `DEMO_START_RATE` and `DEMO_RESET_RATE` default 10 and 30 per hour to 120 per hour (start: per IP; reset: per demo user, it is a signed-in call).
   - `DEMO_LEASE_SECONDS` stays 2700 (45 minutes): the landing copy and DISCLOSURE promise it, and copy.js belongs to another agent.
   - `manage.py seed_demo --ensure` (new flag) creates only the missing families and never wipes one in use (`demo.services.ensure_pool`,
     guarded by a cache lock). `seed_demo` without the flag still resets every family.
   - `backend/docker-entrypoint.sh` (new, LF via `.gitattributes`): with `DEMO_MODE=1` it waits until `migrate --check` passes, runs
     `seed_demo --ensure` in the background, then execs gunicorn. The Dockerfile `CMD` now runs it. `GUNICORN_WORKERS` is a new knob (default 3).
   - Safety net: the first `POST /api/demo/start` on an empty pool seeds on the spot (`acquire_slot`), so a visitor never gets a lasting 503.
2. **Arabic greeting.** `_GREETING_INSTRUCTIONS['ar']` in `conversation/agent/entrypoint.py`: Sadiq opens with «السلام عليكم» as the one who
   greets first (the initiator's form), never the reply «وعليكم السلام». Wording-only. Test: `ArabicGreetingTests` in `test_voice_wiring.py`.
   The lead owns the religious rules and prompts: the lead should read the one changed line.
3. **Landing scene.** `DemoHeroScene.jsx` mounts the 3D forest only when `isForestEnabled()` is true (`?forest=1`, remembered, or
   `VITE_FOREST_SCENE=1`). Otherwise the painted meadow (`data-demo-scene="meadow"`), like the product, with no forest chunk. Edit marked
   `// avatar-integ`. Check: `python scripts/landing-scene-check.py URL` (headless Edge): `/` meadow, `?forest=1` forest, `?forest=0` meadow, all PASS on 5414.
   Reviewer follow-up: the first meadow landing had no character at all (a bubble saying "I am Al-Sadiq" and "tap Al-Sadiq" over an
   empty path). The meadow branch now mounts `MeadowStage` (the child's Home stage), so Sadiq walks up the path, waves, greets at
   the wave and hops on a tap, as on Home. It has its own ref (the landing's controlRef expects the forest's `rt`/`look`), sits in
   a `z-0 pointer-events-none` layer so the tap button stays on top, and falls back to the plain living meadow without WebGL or if
   the avatar throws. Cost: the landing again loads the avatar GLB (as the forest landing did), which Home needs next anyway.
   Known, dev only: under React StrictMode three r184's `compileAsync` (HologramRig.warmUp) can throw "reading 'isReady'" and
   stall the avatar loop; it did not occur in 12 production-build loads.
4. **Submission docs.** `JUDGE-DEMO-SCRIPT.md` and `DECK-OUTLINE.md` now describe the meadow product, the lead's two concepts (Home walk, steady
   call) and the live features (lip sync, listening and thinking poses, gestures, held web page, living meadow, kid polish, ElevenLabs voice),
   say "40 families", and add the capacity notes. Both keep the claim that source cards need the knowledge bank, which is not merged.

## 2. Env values for the lead's CI

The code defaults already equal the judging-day column, so the server `.env` only needs these to change them. Full table and reasons:
`docs/hackathon/DEMO-LOGIN.md`, "Judging-day settings". Template: `.env.production.example`.

| Variable | Value | Note |
|---|---|---|
| `DEMO_MODE`, `VITE_DEMO_MODE` | 1 | the second is baked in at frontend build time |
| `DEMO_POOL_SIZE` | 40 | max 40 |
| `DEMO_LEASE_SECONDS` | 2700 | unchanged |
| `DEMO_START_RATE`, `DEMO_RESET_RATE` | 120/hour | start per IP, reset per demo user |
| `DEMO_DAILY_SESSIONS` | 5 (suggested, code default 3) | per demo family, survives leases and resets |
| `DEMO_SESSION_START_PER_HOUR` | 12 (suggested, code default 6) | per demo user |
| `ELEVEN_DAILY_CHAR_CAP` | about 120000 (suggested, code default 20000) | 20000 is about 10 voice sessions; the credits must cover it: the lead's spend decision |
| `GUNICORN_WORKERS` | 3 | raise only if the box has the CPU |

CI needs no new step: the deploy's `up -d` starts the backend, whose entrypoint seeds after `migrate`. The script is the image `CMD`, not an
`ENTRYPOINT`, so the CI's one-off `docker compose run --rm backend python manage.py migrate` replaces it and runs plain migrate, and the
long-running backend container (which waits for that migrate to pass) does the seeding.

## 3. Decisions

- Lease kept at 45 minutes (copy promise) rather than shortened for throughput. At 40 families that is up to about 53 new visitors an hour.
- Left the per-family guards (3 sessions a day, 6 starts an hour) and the ElevenLabs cap as they are in code and documented the values
  instead, because they are the lead's cost and safety controls.
- Seed is idempotent (`--ensure`) instead of `seed_demo` on every deploy, because the full seed resets families a judge may be using.
- Kept the xAI rollback wording in the submission docs: it is the lead's design (the code path `TTS_PROVIDER=xai` still exists in
  `tts_factory.py`). Under the "ElevenLabs only" rule the lead may want to drop it, see open issues.

## 4. Checks (all green, 2026-10-05)

- Backend full suite in `product-web-backend:latest` with the repo mounted, sqlite settings, no network: 854 tests OK (22 skipped, real LiveKit).
  Demo suite 52 tests (new: family content, `ensure_pool`, judging-day concurrency of 40 leases, deploy wiring); `test_voice_wiring` 71.
- Frontend (`frontend/`): `npx eslint .` clean; `npm run build` OK; test:lipsync 80, test:avatar 78, test:webpage 47, test:hotfix2 17,
  test:acting 31, test:walk 20, test:nature 17, test:lookdev 21, test:meadowstage 31; `check-session-startup` 21; `check-source-cards` passed.
- Landing scene check (headless Edge, own vite on 5414, stopped afterwards): PASS x3.
- Entrypoint flow tested with a fake `python` (waits for migrate, seeds once, then execs the server).

## 5. Open issues

1. Voice concurrency is not measured: how many simultaneous rooms one `livekit_agent` worker (`AGENT_NUM_IDLE_PROCESSES=1`) carries. Rehearse with 5 to 10 browsers.
2. `ELEVEN_DAILY_CHAR_CAP` at the default 20000 turns new sessions text-only after about 10 voice sessions. Needs the lead's decision and credits.
3. The entrypoint seed was not run against a real Postgres and Redis here (tests use sqlite and a local cache); the first deploy should be watched:
   `docker compose -f docker-compose.prod.yml logs backend | grep -i demo`.
4. Source cards and the verified FAQ still need `hk/01-knowledge-bank` (see product-web section 10), so JUDGE-DEMO-SCRIPT steps 4 to 7 stay conditional.
5. The xAI rollback appears in DECK-OUTLINE, DISCLOSURE, JUDGING-MAP and the operator table: the lead decides whether it stays (ElevenLabs-only rule).
6. The landing's own header comment in `DemoLanding.jsx` still says "arch window onto the forest" (a comment only, not mine to edit).
