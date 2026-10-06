# Handoff: 10 Production hardening for the public demo

Branch `hk/10-prod-hardening`, 2026-10-04. Two commits on top of `e7c98a3`: `3d8f355` (builder) and `8334170` (reviewer fixes). Nothing is pushed. Nothing is deployed.

## 1. What this is

The judges will use the live demo at https://alsadiqai.com, which runs on the team's DigitalOcean server (`/opt/alsadiq`). A push to the `production` branch runs `.github/workflows/deploy.yml`: git pull, compose build, `up -d`, migrate.

Before this branch, that server had risks that were about to become public:

- `seed_admin` had a default password written in the repo.
- `/admin` was open to the whole internet.
- There was no health URL for an uptime monitor.
- The frontend feature flags could not be set in the production build.
- The voice agent kept up to 4 warm processes.
- A live test-account password sat in a docs file.

This branch fixes those. It also fixes one real deploy bug found in review (section 2, item 5).

Read this together with `docs/production-hardening.md`. That file holds the exact lead checklist commands. This handoff explains them.

## 2. What was built and why

1. **Safe `seed_admin`.** With DEBUG off it raises `CommandError` if `DJANGO_SUPERUSER_PASSWORD` is missing or equals the public dev default. With DEBUG on (local dev) nothing changes. If the admin already exists it is skipped, whatever its password. Why: the default is in a public repo.
2. **`/admin` blocked at Caddy.** Only client IPs or CIDRs in `ADMIN_ALLOWED_IPS` reach it. Everyone else gets a plain 404. Empty or unset means nobody. `/api/*`, `/static/*` and the SPA are unchanged. Caddy checks the real TCP client IP, so a forged `X-Forwarded-For` does not help.
3. **`GET` or `HEAD /api/health/`.** No auth, no throttle, never cached. It checks the database and Redis. It returns 200 `{"status":"ok"}` or 503 `{"status":"degraded"}`, plus `ok`, `error` or `skipped` per check, and never any error text. Redis reports `skipped` when `REDIS_HOST` is unset. Why: a free uptime monitor needs a URL that proves the stack is alive.
4. **Frontend flags in the build.** `frontend/Dockerfile` and the prod compose pass `VITE_FOREST_SCENE` and `VITE_DEMO_MODE` (default 0). Only the exact string `1` turns a flag on, which matches `forestFlag.js` on 06b and `demoService.js` on 10-demo.
5. **Frontend volume refresh (reviewer fix).** Docker fills a named volume from an image only once. So after the first deploy, `frontend_dist` kept the first build, and later frontend work (including the flags) would never reach the site. The busybox stage now keeps the build in `/dist` and copies it into the volume every time the container starts.
6. **Agent idle processes.** `backend/conversation/agent/main.py` reads `AGENT_NUM_IDLE_PROCESSES` and passes it to `WorkerOptions(num_idle_processes=...)`. Prod compose defaults it to 1. Without it livekit-agents 1.5.1 keeps one warm process per CPU core, up to 4, and each preloads Django and the VAD model (a few hundred MB). Invalid values are ignored with a message on stderr.
7. **Settings from env.** Prod compose sets `DEBUG=${DEBUG:-0}`. A new `_env_list` helper trims spaces and drops empty items for hosts, CORS and CSRF (CSRF used to produce `['']`). `SECURE_SSL_REDIRECT` can be toggled and defaults on.
8. **Env template and docs.** `.env.production.example` lists every new variable with placeholders only. `ADMIN_ALLOWED_IPS` is left empty on purpose. `docs/production-hardening.md` is the lead checklist.
9. **Test-account password removed** from `docs/mobile-uiux-audit.md`. The line now says "ask the lead". The old value is still in git history, so treat it as burned.
10. **`HTTP_PORT` and `HTTPS_PORT`** overrides on Caddy in prod compose, so a local smoke test can run beside other stacks. Leave them unset on the server.

## 3. Where it lives

| Area | File |
|---|---|
| Admin seeding | `backend/authentication/management/commands/seed_admin.py` |
| Health endpoint | `backend/config/health.py`, route in `backend/config/urls.py` |
| Env lists, DEBUG, SSL redirect | `backend/config/settings.py` |
| Agent idle processes | `backend/conversation/agent/main.py` (`_worker_options`) |
| `/admin` block | `infra/caddy/Caddyfile` |
| Build args, ports, DEBUG default | `docker-compose.prod.yml` |
| Frontend volume fix, flags | `frontend/Dockerfile` |
| Env template | `.env.production.example` |
| Lead checklist | `docs/production-hardening.md` |
| Tests (13 new) | `backend/config/tests.py` |
| Password removal | `docs/mobile-uiux-audit.md` |
| One-time server setup script | `scripts/init-prod.sh` (comment only added) |

## 4. How to run, test and verify

**Tests.** The new tests are in `backend/config/tests.py`: seed_admin, health (including HEAD, Redis client closed, no DB error text) and the env list helper. The default settings use Postgres, so run them where the db service exists, for example in the dev compose stack:
`docker compose run --rm backend python manage.py test config`
The builder and reviewer ran them in a python 3.12 container against SQLite through a throwaway settings override that is not committed. Result: 79 pass for the whole backend suite (66 before this branch plus 13 new).

**Compose and Caddy checks without a server.** With a dummy `.env` (never commit it):
- `docker compose -f docker-compose.prod.yml config` must be valid. Defaults: DEBUG 0, both VITE flags 0, `AGENT_NUM_IDLE_PROCESSES` 1, ports 80 and 443.
- `docker compose -f docker-compose.prod.yml run --rm --no-deps caddy caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile` must end with `Valid configuration`.

**Local prod-like smoke test.** The builder used project name `alsadiq10smoke`, `DOMAIN=localhost`, `HTTP_PORT=18080`, `HTTPS_PORT=18443`. Expected results:
- `/api/health/` returns 200 with db and redis `ok`.
- `/` returns 200.
- `/admin` and `/admin/login/` return 404.
- `/static/admin/...` returns 200.
- `/api/alerts/` returns 401.
- HTTP redirects to HTTPS.
- With `ADMIN_ALLOWED_IPS="0.0.0.0/0 ::/0"`, `/admin/login/` returns 200.

Tear down with `docker compose -p alsadiq10smoke ... down -v` (only for a project you created).

**On the real server, after deploy** (from the lead checklist):
- `curl -s -o /dev/null -w '%{http_code}\n' https://alsadiqai.com/admin/` prints 404 from outside the allowlist.
- `curl -s https://alsadiqai.com/api/health/` prints `{"status":"ok", ...}`.

## 5. Decisions and why

- **Block `/admin` in Caddy, not in Django.** It works before any app code runs and needs no code path for the demo. Default deny.
- **Space-separated IP list.** That is Caddy's `remote_ip` syntax. The cost is that a comma or typo stops Caddy loading, which takes the whole site down. The checklist therefore validates before use.
- **Health never leaks error text and has no throttle.** Monitors poll often, and the body is safe to expose.
- **Health pings Redis directly.** Django's cache is still locmem on this branch, so a Django cache check would prove nothing.
- **Dev behaviour kept.** `seed_admin` still works with no setup locally, so local stacks are not broken.
- **Flags default off.** A forgotten variable can never switch a half-finished feature on for the judges.
- **Idle processes default 1.** Saves RAM on a small droplet. The voice demo has few simultaneous users.
- **Volume copy on container start.** Simple and keeps old hashed assets, so a judge's already-open tab keeps working.
- **CI deploy workflow left unchanged.** The lead owns it. A post-deploy health curl is listed in next steps.

## 6. Current status

- Both commits are on `hk/10-prod-hardening` and nothing is pushed. A review gave "ship with notes".
- `git merge-tree` showed a clean merge with 06-avatar, 06b-forest, 07-voice, 07-voice-text, 10-demo and 10-submission when the reviewer checked.
- Every code item above is done and checked. The remaining work is on the server and belongs to the lead.
- Not run: the livekit agent container was never built or run here. The `num_idle_processes` argument was checked by creating `WorkerOptions` in a clean python 3.12 container with livekit-agents 1.5.1.

## 7. Known issues

- **Caddy keeps its old Caddyfile** until its container is recreated. The deploy does not recreate it unless `.env` changed in the same deploy. Until the lead recreates Caddy, `/admin` stays open.
- **A bad `ADMIN_ALLOWED_IPS` value takes the whole site down.** A comma, a typo or a placeholder makes Caddy fail to load.
- **Existing admin keeps its old password.** `seed_admin` skips existing users, so the default only disappears when the lead rotates it by hand.
- **Test accounts still exist on the server** and their old password is in git history.
- **Health can return 503 for an outage users would not notice.** Redis is down means 503, though Django does not use Redis yet. This changes when 10-demo merges, because the demo uses Redis for its lease and cache when `DEMO_MODE=1` and `REDIS_HOST` are set.
- **The VITE flags do nothing yet** until 06b (forest) and 10-demo (landing and banner) merge. This branch only wires them through the build. The backend `DEMO_MODE` variable on 10-demo is separate and reaches the backend through `env_file`.
- **Old hashed frontend assets pile up** in the volume (a few MB per deploy). Harmless.
- **CI has no `collectstatic` and no post-deploy health check.** Static files come from `scripts/init-prod.sh`, which is manual.

## 8. Next steps and improvements, ordered by value

1. **Lead server checklist, before the judges arrive.** See the box below. This is the highest value and is not done.
2. **Merge order and flags.** Merge 06b, 10-demo and the voice branches, then set the VITE flags on the server and rebuild the frontend. Remember `DEMO_MODE=1` for the backend as well, and run `seed_demo` once.
3. **Add a health curl to `deploy.yml`.** For example `curl -fsS https://alsadiqai.com/api/health/` after `up -d`, so a broken deploy fails in CI instead of in front of a judge.
4. **Recreate Caddy automatically in the deploy script** (`up -d --no-deps --force-recreate caddy`) and run `caddy validate` before it, so the `/admin` block cannot be forgotten.
5. **Rotate or delete leaked material properly.** If the repo goes public (see `PUBLIC-REPO-SCRUB.md` in the worktree folder), the old test password and the old dev admin default are in history. Rotation is the fix, not deletion.
6. **Make health honest about Redis.** Once Redis really backs the cache (10-demo), keep the check. Until then consider reporting Redis as informational so a Redis blip does not alert.
7. **Run the agent container once** on a staging or local stack with `AGENT_NUM_IDLE_PROCESSES=1` and watch memory.
8. **Add `collectstatic` to CI** or to the deploy script, so admin static files cannot go stale.
9. **Clear old frontend assets** occasionally by stopping Caddy and removing the `frontend_dist` volume, then redeploying.

### Lead server checklist (Abdulrahman)

Run from `/opt/alsadiq`. `dc` means `docker compose -f docker-compose.prod.yml`. Never paste secrets into chat or commits.

**A. Env vars to set in `/opt/alsadiq/.env`** (names and meaning only, values are yours):

| Variable | Value |
|---|---|
| `DEBUG` | `0` |
| `DJANGO_ALLOWED_HOSTS` | `alsadiqai.com` |
| `CORS_ALLOWED_ORIGINS` | `https://alsadiqai.com` |
| `CSRF_TRUSTED_ORIGINS` | `https://alsadiqai.com` |
| `SECURE_SSL_REDIRECT` | `1` (default) |
| `DJANGO_SUPERUSER_USERNAME` and `DJANGO_SUPERUSER_EMAIL` | your choice |
| `DJANGO_SUPERUSER_PASSWORD` | a long random secret, not the old default |
| `ADMIN_ALLOWED_IPS` | your own IP or CIDR, separated by spaces, or empty to block `/admin` for everyone. No commas, no placeholder |
| `VITE_FOREST_SCENE` and `VITE_DEMO_MODE` | `0` until the matching branches are merged, then `1` and rebuild |
| `AGENT_NUM_IDLE_PROCESSES` | `1` |
| `DOMAIN` | `alsadiqai.com` |

**B. Validate, then deploy.**
1. `dc run --rm --no-deps caddy caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile` must end with `Valid configuration`.
2. Merge to `production` so CI deploys (or run build and `up -d` by hand).
3. `dc up -d --no-deps --force-recreate caddy` so Caddy loads the new Caddyfile.
4. Check: `/admin/` prints 404 from outside the allowlist, and `/api/health/` prints 200.

**C. Rotate the admin password.** `seed_admin` skips an admin that already exists, so run `dc run --rm backend python manage.py changepassword <admin-username>`. Then confirm no superuser still has the public default. The one-liner is in `docs/production-hardening.md` step 4, and it must print `[]`.

**D. Delete the test accounts** named in the old audit doc: parent `codexParent505209` and child `codexChild505209`. Delete them on the server (Django admin from an allowlisted IP, or a `manage.py shell` delete). The password is no longer in the file but is still in git history, so do not reuse it anywhere.

**E. Seeding** (once, after migrations):
- Admin: `scripts/init-prod.sh` runs migrate, `seed_admin` and `collectstatic`. It needs the password var from A.
- Knowledge fixture: `dc run --rm backend python manage.py seed_islamic_knowledge`. This loads the committed fixture `islamic_knowledge_base.json`. Do not write scripture by hand. Content must come from the bank sources (AGENTS.md).
- Content bank and demo families: these live on other branches (task 01 and 02 for the bank, 10-demo for `seed_demo`). Run them once after those merge. The plan says "seed bank and demo once". Demo data is synthetic only.

**F. Uptime monitor.** Create a free monitor (for example UptimeRobot or Better Stack) on `https://alsadiqai.com/api/health/`. Expect 200. GET or HEAD both work. Alert by email. Check it every 1 to 5 minutes until the end of the judging window (the plan targets 22 Oct, ideally 27 Oct).

## 9. Gotchas

- **Never put a placeholder in `ADMIN_ALLOWED_IPS`.** Caddy cannot start with a bad value, and the whole site goes down.
- **Spaces, not commas, for `ADMIN_ALLOWED_IPS`.** The backend lists (hosts, CORS, CSRF) use commas. The two formats differ.
- **VITE variables are build-time.** Changing them in `.env` does nothing until the frontend image is rebuilt. Only `1` turns them on, so `true` does not work.
- **Frontend `VITE_DEMO_MODE` and backend `DEMO_MODE` are different switches.** Both are needed for the one-click demo.
- **Caddy mounts the Caddyfile at container creation.** Editing the file is not enough, recreate the container.
- **Seeding is skipped for an existing admin.** A changed `DJANGO_SUPERUSER_PASSWORD` in `.env` does nothing for an admin that already exists.
- **Health 503 does not always mean users are affected.** Check which sub-check says `error`.
- **Do not `down -v` on the server.** It deletes the Postgres volume. The `-v` in the smoke test is only for a throwaway project.
- **The local Python on Majd's PC cannot load livekit DLLs** (Application Control policy). Use a python 3.12 container for agent code checks.
- **Never commit a real `.env`.** `.env.production.example` is the only template, and it holds placeholders only.
