# Production hardening (hk/10-prod-hardening)

What changed, and what the lead must do on the server (/opt/alsadiq/.env).

## What changed
- `seed_admin`: with DEBUG off it needs `DJANGO_SUPERUSER_PASSWORD` and refuses the public dev default. Dev behaviour is unchanged. An admin that already exists is skipped, whatever its password.
- Caddy blocks `/admin` for everyone except `ADMIN_ALLOWED_IPS` (space-separated IPs or CIDRs). Unset or empty means nobody. `/api/*`, `/static/*` and the SPA are unchanged. The check uses the real TCP client IP, so a forged `X-Forwarded-For` header does not get through.
- `GET` or `HEAD /api/health/`: no auth, no throttle. Checks the database and Redis. 200 `{"status":"ok"}` or 503 `{"status":"degraded"}`, plus `ok` / `error` / `skipped` per check and never any error text. Point the uptime monitor at `https://alsadiqai.com/api/health/`.
- Frontend build args `VITE_FOREST_SCENE` and `VITE_DEMO_MODE` (default 0; only `1` turns them on). They are baked in at build time, so a change needs a frontend rebuild (the CI deploy rebuilds).
- Frontend deploys now reach the site. Before, the build was copied into the `frontend_dist` volume only the first time (Docker fills a named volume once), so later deploys kept serving the old build. The frontend container now copies the new build into the volume each time compose recreates it.
- `AGENT_NUM_IDLE_PROCESSES` (default 1 in `docker-compose.prod.yml`) limits warm agent processes. Without it livekit-agents 1.5.1 keeps one per CPU core, up to 4.
- `DEBUG` defaults to 0 in the production compose file. Hosts, CORS and CSRF come from env (comma-separated, trimmed, empty items dropped). `SECURE_SSL_REDIRECT` can be turned off for a plain-HTTP staging box.
- `HTTP_PORT` / `HTTPS_PORT` let a local smoke test run next to other stacks. Leave them unset on the server.

## Lead checklist before the public demo
Run these from `/opt/alsadiq`. `dc` below means `docker compose -f docker-compose.prod.yml`.

1. Add the new vars to `.env` (see `.env.production.example`): `DJANGO_SUPERUSER_PASSWORD`, `ADMIN_ALLOWED_IPS`, `VITE_FOREST_SCENE`, `VITE_DEMO_MODE`, `AGENT_NUM_IDLE_PROCESSES`. For alsadiqai.com: `DJANGO_ALLOWED_HOSTS=alsadiqai.com`, `CORS_ALLOWED_ORIGINS=https://alsadiqai.com`, `CSRF_TRUSTED_ORIGINS=https://alsadiqai.com`.
   - `ADMIN_ALLOWED_IPS` takes spaces, not commas (`1.2.3.4 5.6.7.0/24`). A comma, a typo or a placeholder stops Caddy from loading, which takes the whole site down, not just `/admin`. Leave it empty if nobody needs `/admin`.
2. Check the Caddyfile and `.env` together before Caddy uses them:
   `dc run --rm --no-deps caddy caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile`
   It must end with `Valid configuration`.
3. After the deploy, recreate Caddy. It only reads the Caddyfile when its container is created, and the deploy leaves it running unless `.env` changed:
   `dc up -d --no-deps --force-recreate caddy`
   Then check: `curl -s -o /dev/null -w '%{http_code}\n' https://alsadiqai.com/admin/` prints `404` from outside the allowlist, and `https://alsadiqai.com/api/health/` prints `200`.
4. Rotate the production admin password. The old default was in a public repo. If the admin already exists, `seed_admin` skips it, so change the password in the shell: `dc run --rm backend python manage.py changepassword <admin-username>`.
   To confirm no superuser still has the public default (it must print `[]`):
   `dc run --rm backend python manage.py shell -c "from authentication.models import User; from authentication.management.commands.seed_admin import DEV_DEFAULT_PASSWORD as p; print([u.username for u in User.objects.filter(is_superuser=True) if u.check_password(p)])"`
5. Delete the audit test accounts `codexParent505209` and `codexChild505209` on the server. Their password was in `docs/mobile-uiux-audit.md` (now removed from the file, but still in git history).
6. Set up a free uptime monitor on `/api/health/`.
