# Handoff: Demo login and landing (task 10)

Branch `hk/10-demo`, 5 commits on top of `e7c98a3`, not pushed. Written 2026-10-04.
Everything below was checked against git and the code on that branch.

## 1. What this is

A one-click "Try Al-Sadiq" demo for the judges at https://alsadiqai.com. A judge opens the site, presses one big Arabic button (جرّب الصديق) and lands in a synthetic child's room. No sign-up, no password. A bar on every demo screen lets them flip to the parent dashboard of the same child, or start over.

It is off by default. With the two flags empty, `/` redirects to login as before and `/api/demo/*` answers 404.

This branch is the demo login and landing only. It does not contain the 3D forest, the new avatar, the voice work or the cost caps from the architect's plan. Those live on other branches (see section 8).

## 2. What was built and why

Why: judges must reach a working child screen in one tap, and several judges may arrive at once. So the demo uses a small pool of fake families that are leased out one visitor at a time.

Backend (`backend/demo/`, new Django app):
- 8 synthetic Arabic families (child plus parent), each with a short made-up week of sessions, summaries, points and memory. Seeded by `seed_demo`.
- `POST /api/demo/start` leases a free family and returns child and parent tokens for the same child. If all 8 are busy it returns a bilingual 503 with `retry_after`.
- `POST /api/demo/reset` ("start over") wipes and re-seeds the visitor's own family and renews its lease.
- A lease lasts 45 minutes (`DEMO_LEASE_SECONDS=2700`). The lock is an atomic `cache.add` on Redis, so two visitors never get the same family.
- `demo_reset_expired` command frees families whose lease ended.
- Privacy guards added in review: a demo token only works while its own lease is the family's live lease (checked on every request and on token refresh); demo accounts are read-only for password change and child creation; usernames starting with `demo-` are reserved.

Frontend:
- Arabic-first landing at `/` when built with `VITE_DEMO_MODE=1`: big CTA, a 3-step box for judges, a demo-data privacy line, an ar/en toggle.
- Demo bar on child and parent screens: parent view, start over, and a "time is up" state.
- `DemoHeroScene` shows the meadow picture with the existing 3D avatar. It is the slot where the forest and new avatar go.

## 3. Where it lives

Commits (oldest first):
- `516bbe8` feat(demo): one-click demo pool with leased synthetic families
- `bb344ba` feat(demo): Arabic-first "Try Al-Sadiq" landing, demo banner and wiring
- `b3be469` fix(demo): end demo tokens with the lease and lock the shared accounts
- `481dba1` fix(demo): fit the phone header, reuse the family on retry, handle expiry
- `78e8899` fix(demo): keep "Al-Sadiq" on one line in the English greeting bubble

Files:
- `backend/demo/services.py`: seed, lease, reset, tokens (the core)
- `backend/demo/views.py`, `urls.py`: the two endpoints
- `backend/demo/authentication.py`, `serializers.py`: lease check on requests and refresh
- `backend/demo/accounts.py`: demo username rules and the `NotDemoAccount` permission
- `backend/demo/content.py`: the synthetic family text (no scripture)
- `backend/demo/management/commands/seed_demo.py`, `demo_reset_expired.py`
- `backend/demo/tests.py`: 39 tests
- `backend/config/settings.py`: flags, Redis cache switch, throttle rates, JWT hooks
- `backend/authentication/views.py`, `serializers.py`: demo locks and reserved prefix
- `frontend/src/pages/DemoLanding.jsx`, `frontend/src/services/demoService.js`
- `frontend/src/features/demo/` (`DemoBanner.jsx`, `DemoHeroScene.jsx`, `copy.js`, `demo.css`)
- `frontend/src/App.jsx` (route at `/`), `guards/ProtectedRoute.jsx`, `features/child/components/ChildLayout.jsx` (banner mount)
- `frontend/Dockerfile`, `docker-compose.yml`, `docker-compose.prod.yml` (pass `VITE_DEMO_MODE` through)
- `.env.example`, `.env.production.example`
- `docs/hackathon/DEMO-LOGIN.md`: the short ops steps

## 4. How to run, test and verify

Env flags:
- `DEMO_MODE=1`: backend switch. Turns on the endpoints and moves Django's default cache to Redis (when `REDIS_HOST` is set).
- `VITE_DEMO_MODE=1`: frontend switch. Read at build time, so it needs a rebuild.
- Optional: `DEMO_POOL_SIZE` (8, the maximum), `DEMO_LEASE_SECONDS` (2700), `DEMO_START_RATE` (10/hour per IP), `DEMO_RESET_RATE` (30/hour).

Run locally (use your own ports and compose project name):
1. Set both flags in `.env`, start the stack, then `python manage.py seed_demo` in the backend container.
2. Open the frontend, press the button, check the child screen, press parent view, then start over.

Tests (the builder and reviewer both ran them in Docker with sqlite settings):
- Backend: 105 tests passed in total, 39 of them in `backend/demo/tests.py`. Run `python manage.py test demo` for the demo ones.
- Frontend: `npm run lint` is clean, and `VITE_DEMO_MODE=1 npm run build` works (only the old chunk-size warning).
- Browser: Edge via Playwright at 1440, 390 and 360 widths. Landing, language toggle, start, parent view, try again, start over and expiry were all clicked through against a real backend.

I did not re-run the tests or the browser in this handoff task. The numbers above come from the builder and reviewer reports, and the test count of 39 matches the code.

## 5. Decisions and why

- Pool of 8 leased families, not a shared account: visitors must not see each other's chats.
- Lease in Redis with `cache.add` and a TTL: atomic, and a forgotten tab frees itself.
- Both child and parent tokens come back from one start call, so the parent view needs no login.
- Every demo token is tied to its lease (`demo_lease` claim) and checked on each request and on refresh. Review found that without this, the last visitor could keep refreshing and read the next visitor's family.
- Access tokens never outlive the lease.
- Demo accounts have no usable password and are read-only for password change and child creation.
- Demo mode switches the cache to Redis so the lock and throttles are shared across gunicorn workers.
- The 45-minute lease and 10 starts per hour per IP are the defaults; both are env-tunable.
- No release endpoint: a closed tab keeps its family until the lease ends. Simpler and safe, but it limits throughput.
- The frontend flag is build-time, so a production build without it can never show the landing.
- The landing and demo bar are bilingual. The in-app child and parent screens stay as they were (English).

## 6. Current status

- Built, reviewed and committed on `hk/10-demo`. Not pushed, no PR.
- Review verdict was ship-with-notes. The privacy leak and the account holes it found are fixed.
- Not deployed. The server still needs the production steps below.
- Voice was not tested (no keys were used).

Production steps for the lead (Abdulrahman), on the droplet:
1. In `/opt/alsadiq/.env` set `DEMO_MODE=1` and `VITE_DEMO_MODE=1`. Compose passes `VITE_DEMO_MODE` to the frontend build as an arg, and the CI deploy already runs `docker compose build` and `up -d`, so a normal deploy after editing `.env` picks it up.
2. Seed once: `docker compose -f docker-compose.prod.yml exec backend python manage.py seed_demo`. CI does not do this.
3. Add a cron on the host, every 5 minutes: `*/5 * * * * cd /opt/alsadiq && docker compose -f docker-compose.prod.yml exec -T backend python manage.py demo_reset_expired`.
4. Check: open https://alsadiqai.com in a private window, press the button, confirm the child screen, then parent view, then start over.
5. If judges will share one venue Wi-Fi, set `DEMO_START_RATE` higher (for example `100/hour`) before judging.

To turn it off: empty both flags and redeploy.

## 7. Known issues

- Start throttle is 10 per hour per IP. Judges behind one venue IP share it and can get a 429.
- A closed tab holds its family for the full 45 minutes, which allows about 10 new visitors an hour across 8 families.
- In demo mode the cache is Redis. If Redis goes down, the throttles and the child last-seen middleware return 500.
- The start throttle reads the client IP from `X-Forwarded-For` set by Caddy. `NUM_PROXIES` is not set. The backend port is `expose` only, so this is fine as long as it stays private.
- Existing app bug, not from this branch: the axios interceptor keeps the new access token but drops the rotated refresh token, so a session can refresh only once. That is enough for a 45-minute demo.
- The Arabic text-direction fix (`unicode-bidi: plaintext`) applies only during demo sessions. Real Arabic users need `dir=auto` on the parent and child content components.
- The parent-view switch waits 120 ms for the role guard to redirect before navigating. Replace it with a guard-level fix if it proves flaky.
- The forest and new avatar are not in. In-app screens are English.
- `PRODUCT.md` and `DESIGN.md` were not created.
- Fonts load from Google Fonts (`Baloo Bhaijaan 2`, `IBM Plex Sans Arabic` added in `frontend/index.html`).
- Vite chunk-size warning existed before.

## 8. Next steps and improvements, ordered by value

1. Lead does the production steps in section 6 and runs one live click-through on https://alsadiqai.com. Without this nothing ships.
2. Integrate the forest and avatar into `frontend/src/features/demo/DemoHeroScene.jsx`. It has two marked blocks, BACKDROP and AVATAR. Swap them for `ForestStage` and the new avatar from `hk/06b-forest` and `hk/06-avatar`, and keep the props contract in the file header (`lines`, `label`, `className`; fill 100% of the parent; talk for a couple of seconds on each tap).
3. Add the voice cost guards from the architect's plan, which are not built here: a 5-minute session timer, daily session caps, an ElevenLabs daily character cap that falls back to xAI, and a `VOICE_MODE` kill switch in Redis. Each demo visit can now start voice sessions, so this protects the credit budget.
4. Raise `DEMO_START_RATE` if judging is on site, and consider a release endpoint (called when the tab closes) so abandoned families come back sooner.
5. Fix the axios interceptor so it stores the rotated refresh token.
6. Make the in-app child and parent screens bilingual, and use `dir=auto` on content components for real Arabic users.
7. Add an uptime check on `/` and a health endpoint, and a nightly full reset as a safety net.
8. Replace the 120 ms wait in the demo bar with a proper guard fix.

## 9. Gotchas

- `VITE_DEMO_MODE` is baked in at build time. Changing it in `.env` without rebuilding the frontend does nothing.
- Run `demo_reset_expired` and `seed_demo` in the `backend` container, not the `livekit_agent` one. Only `backend` gets `REDIS_HOST`; elsewhere the cache is per-process memory and the command would think every family is free and wipe live ones.
- `seed_demo` wipes and re-seeds every family. Do not run it during judging.
- Usernames `demo-child-N` and `demo-parent-N` (N up to 8) are reserved. `seed_demo` refuses to take over an account it did not create.
- Synthetic data only. Never type real child names into the demo; the landing says so.
- `content.py` has no Quran or hadith text. Keep it that way (AGENTS.md rule: sources only from the bank).
- Keep the backend port private. The throttle trusts the forwarded IP header.
- With `DEMO_MODE` off, a demo token from an earlier session is refused, so turning it off cleanly ends all demo sessions.
