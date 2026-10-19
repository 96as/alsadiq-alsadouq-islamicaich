# Try Al-Sadiq: one-click demo

Judges open https://alsadiqai.com, press one button, and land in a synthetic child's room. No account, no password.

## Turn it on (server)

1. In the server `.env`: `DEMO_MODE=1` and `VITE_DEMO_MODE=1`.
2. Rebuild the frontend (the flag is baked in at build time): `docker compose -f docker-compose.prod.yml up -d --build frontend backend`.
3. Nothing to seed by hand. The prod backend image starts through `backend/docker-entrypoint.sh`: with `DEMO_MODE=1` it waits until the CI's `migrate` has finished, then runs `python manage.py seed_demo --ensure`, which creates only the families that are missing and never wipes one a visitor holds. It runs on every deploy and every container restart, so a fresh database and a pool that grew from 8 to 40 both fill themselves. As a second safety net, the first `POST /api/demo/start` on an empty pool seeds it on the spot (a visitor who beats the seed waits a few seconds, never a 503 that lasts).
4. Optional, every 5 minutes: `python manage.py demo_reset_expired` (wipes visitor data from families whose lease is over; leases themselves expire on their own).

By hand when needed: `docker compose -f docker-compose.prod.yml exec backend python manage.py seed_demo --ensure` (safe) or `seed_demo` (resets every family, including ones in use).

With both flags empty, `/` redirects to login as before and `/api/demo/*` is off.

## Judging-day settings (for the lead's CI)

About 30 judges, some on two devices, all behind one office IP. The code defaults already match this column, so the `.env` only needs them to change them. Template: `.env.production.example`.

| Variable | Old default | Judging-day default | Why |
|---|---|---|---|
| `DEMO_POOL_SIZE` | 8 | 40 (max 40, the families in `demo/content.py`) | One family per browser for the lease; 30 judges, a few with two devices. |
| `DEMO_LEASE_SECONDS` | 2700 | 2700 | Unchanged: the landing page and DISCLOSURE promise 45 minutes. At 40 families that is up to about 53 new visitors an hour. |
| `DEMO_START_RATE` | 10/hour | 120/hour per IP | Judges share one NAT; the busy page's own retries count too. 120 still stops one script cycling the pool all day. |
| `DEMO_RESET_RATE` | 30/hour | 120/hour per demo user | The "start over" button. It is a signed-in call, so DRF counts it per demo account (which outlives a lease), not per IP. |
| `GUNICORN_WORKERS` | 3 (fixed) | 3 | New knob, change it only if the box has the CPU. |

Related guards (on in production by default: `DEMO_GUARDS` unset and `DEBUG` off; their values are commented in `.env.production.example`), worth setting for the day:

| Variable | Default | Suggested | Note |
|---|---|---|---|
| `DEMO_DAILY_SESSIONS` | 3 | 5 | The count belongs to the demo family and survives its resets, and a new lease picks a random free family. With 3, two judges who land on one family can hit `daily_limit`. |
| `DEMO_SESSION_START_PER_HOUR` | 6 | 12 | Per demo user, same reason. |
| `ELEVEN_DAILY_CHAR_CAP` | 20000 | about 120000 | 20000 characters is roughly 10 voice sessions; after it every new session is text-only. 30 judges at 2 sessions each need about 120000. The ElevenLabs credits must cover it: the lead's spend decision, not set here. |

Not measured here: how many simultaneous voice rooms one `livekit_agent` worker (`AGENT_NUM_IDLE_PROCESSES=1`) carries. Do a rehearsal with 5 to 10 browsers at once before the day.

## How it behaves

- Start leases one family from a Redis-backed pool. If all are busy, the page shows a bilingual "busy" message and retries by itself.
- Pressing "Try" again from the same browser starts over inside its own family, so one visitor never holds two of the pool.
- The banner on the child and parent screens has two buttons: parent view (same family, no login) and start over (wipes and re-seeds that family). When the 45 minutes are up it says so and offers a new demo.
- All data is synthetic. No real child data is ever used.

## Privacy and safety rules (enforced in code)

- A demo token only works while its own lease is the family's live lease, on every request and on refresh (`demo/authentication.py`, `demo/serializers.py`). The last visitor can never read the next visitor's family.
- Each new lease, start over and the cron wipe the family's sessions, messages, reports, alerts, quests, points, summaries and memory, and restore the names and settings a visitor can edit.
- Demo accounts never have a password. A demo child cannot set one and a demo parent cannot add children.
- Usernames starting with `demo-` are reserved: registration and child creation refuse them, and `seed_demo` refuses to take over an account it did not make.
- The start throttle counts the client IP from Caddy's `X-Forwarded-For`, which Caddy sets itself. Keep the backend port private (it is `expose`, not `ports`), or the header could be spoofed.

## Where the 3D forest plugs in

`frontend/src/features/demo/DemoHeroScene.jsx` has two marked blocks (BACKDROP, AVATAR). Swap them for ForestStage and the new avatar. The props contract is in the file header.
