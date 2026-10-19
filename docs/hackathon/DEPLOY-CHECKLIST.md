# Deploy checklist: alsadiqai.com (hackathon -> production)

For the lead (Abdulrahman Salamah). Judging is **6 Oct 2026**, about 30 judges on the one-tap demo.
A push to `production` auto-deploys via `.github/workflows/deploy.yml` onto the droplet (`/opt/alsadiq`).
Env var NAMES only in this file; never paste a value into chat, a ticket or the repo.

Shorthand on the server: `dc` = `docker compose -f docker-compose.prod.yml` (run from `/opt/alsadiq`).

## 1. At a glance

- **What ships:** `origin/hackathon` is ~548 commits ahead of `origin/production` (re-check with `git rev-list --count origin/production..origin/hackathon`).
  Production has **0** commits that hackathon lacks, so the push is a plain fast-forward.
- **New for users:** knowledge bank, source cards, verse recitation (74 mp3s served from `/static/quran/`), one-tap demo mode,
  ElevenLabs voice, the card gate (a card only when the child asks), parent sources in the Insights page.
- **Content after `seed_content`:** **273 reviewed items + 38 values**, 0 rejected
  (ledger `backend/session_moral_context/content/reviewed.json`).
  The DB ends with 273 reviewed items, plus one unverified item per legacy `IslamicReference` already in prod (copied by migration smc 0004). That is expected, not a bug.
- **Migrations:** 10 new, all applied cleanly on a rehearsal with legacy data. Two change data (section 9).
- **Code alone is not a safe rollback:** take the DB backup first (section 2).

## 2. Before the push (server, one-time)

1. Droplet is **at least 4 vCPU / 8 GB** (2 vCPU / 4 GB handles only about 4 to 5 voice sessions).
2. **OpenAI:** the org limit is about 200k TPM / 500 RPM, which is only **6 to 7 children talking at once**. Request a higher
   limit now; it can take days. Also confirm the account has credit.
3. **ElevenLabs:** credit covers `ELEVEN_DAILY_CHAR_CAP` (about 120000 chars/day recommended, section 8).
4. **LiveKit Cloud** project exists; you have its key, secret and `wss://` URL.
5. `.env` on the server is filled in (section 3). `ADMIN_ALLOWED_IPS` is **real IPs, space-separated, never a placeholder or
   a comma** (Caddy then fails to start and the whole site is down). Empty is fine: nobody reaches `/admin`.
   Also check the four Django switches (names only, never values; run in `/opt/alsadiq`):
   ```
   grep -oE '^(DEBUG|DJANGO_SECRET_KEY|DJANGO_ALLOWED_HOSTS|CSRF_TRUSTED_ORIGINS)=' .env   # must list all four
   grep -E '^DJANGO_ALLOWED_HOSTS=' .env | grep -c alsadiqai.com                            # must print 1 (a count, not the value)
   grep -c '^DEBUG=0$' .env                                                                 # must print 1 (DEBUG is not a secret)
   grep -E '^CSRF_TRUSTED_ORIGINS=' .env | grep -c 'https://alsadiqai.com'                  # must print 1
   curl --version | head -1                                                                 # must be 7.71 or newer
   ```
   The deploy's health gate uses `curl --retry-all-errors`, which needs curl 7.71+ (Ubuntu 22.04 ships 7.81). On an older curl the gate exits 2
   and a good deploy goes red: upgrade curl or drop that flag from `deploy.yml` before pushing.
   Why now: the production compose that is **live today** (`origin/production`) does not set `DEBUG`
   (`git show origin/production:docker-compose.prod.yml | grep -n DEBUG` finds nothing) and the old code default was on, so the live
   site may be running with DEBUG on. This push turns it off, which is when a wrong `DJANGO_ALLOWED_HOSTS` (HTTP 400), a wrong
   `CSRF_TRUSTED_ORIGINS` (login and POST failures) or a missing `DJANGO_SECRET_KEY` (backend will not boot) start to bite.
6. Validate **hackathon's** Caddyfile (not the one currently on the server) with the real `.env`. Check that the exit code is 0 / the output contains
   `Valid configuration` (Caddy prints shutdown lines after it, so it does not literally end with it). A comma in `ADMIN_ALLOWED_IPS` fails here with `ParseAddr ... unexpected character`; empty or
   space-separated passes:
   ```
   cd /opt/alsadiq
   git fetch origin hackathon && git show origin/hackathon:infra/caddy/Caddyfile > /tmp/Caddyfile.new
   dc run --rm --no-deps -v /tmp/Caddyfile.new:/etc/caddy/Caddyfile.new:ro caddy caddy validate --config /etc/caddy/Caddyfile.new --adapter caddyfile
   ```
7. **Back up the DB** and write down what is running now (for rollback):
   ```
   cd /opt/alsadiq
   DUMP=~/pre-deploy-$(date +%F-%H%M).dump   # set once; every later command uses "$DUMP"
   git rev-parse HEAD                       # note this sha
   dc images                                # note the image ids
   dc exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -Fc "$POSTGRES_DB"' > "$DUMP"
   ls -lh "$DUMP"                           # must not be 0 bytes
   dc exec -T db pg_restore -l < "$DUMP" | head   # proves the backup is readable (pg_restore runs in the db container)
   ```
8. Server is clean and has room: `git status --porcelain` must print nothing (else `git pull` can fail mid-deploy),
   `df -h /` and `docker system df` need **several GB free** (the new images are about 1.0 GB backend + 1.4 GB agent).
9. Rotate the admin password if not done yet (`docs/production-hardening.md`, steps 4 and 5).

## 3. Env vars (`/opt/alsadiq/.env`, start from `.env.production.example`)

Legend: **⚠️** = if missing, the code silently falls back to a **dev default**. **(build)** = baked into the frontend image;
changing it needs `dc build frontend && dc up -d`.

### Django

| NAME | Purpose | Judging-day value | Notes |
| --- | --- | --- | --- |
| `DEBUG` | Production switch | `0` | Code default is 0 (off) and compose forces `${DEBUG:-0}`, so a missing value means off, not a dev default. DEBUG=0 also turns the demo guards on. |
| `DJANGO_SECRET_KEY` | Signing key | secret, set on server | App refuses to boot if unset with DEBUG off. |
| `DJANGO_ALLOWED_HOSTS` | Host allow-list | `alsadiqai.com` | Comma-separated. |
| `CORS_ALLOWED_ORIGINS` | CORS | `https://alsadiqai.com` | Comma-separated. |
| `CSRF_TRUSTED_ORIGINS` | CSRF | `https://alsadiqai.com` | Comma-separated. |
| `SECURE_SSL_REDIRECT` | HTTP to HTTPS in Django | `1` | Default on. `0` only for a plain-HTTP staging box. |
| `DOMAIN` ⚠️ | Caddy site address and certificate | `alsadiqai.com` | Falls back to `localhost`: no real certificate. |
| `VITE_API_BASE_URL` ⚠️ | API base in the frontend | `https://alsadiqai.com` | **(build)**. Empty makes the frontend call `http://localhost:8000`, and recitation URLs break too. |

### Admin

| NAME | Purpose | Judging-day value | Notes |
| --- | --- | --- | --- |
| `DJANGO_SUPERUSER_USERNAME` / `_EMAIL` | Admin account | your choice | Used by `seed_admin` (first deploy only). |
| `DJANGO_SUPERUSER_PASSWORD` | Admin password | secret, long random | `seed_admin` refuses a missing or the public dev password when DEBUG=0. Skips an admin that already exists. |
| `ADMIN_ALLOWED_IPS` | Who can reach `/admin` | real IPs/CIDRs, **space-separated** | Empty = nobody (404). Comma/typo/placeholder = Caddy will not start. Applies only after Caddy is force-recreated. |

### Postgres / Redis

| NAME | Purpose | Judging-day value | Notes |
| --- | --- | --- | --- |
| `POSTGRES_DB` / `_USER` / `_PASSWORD` ⚠️ | DB credentials | (existing values) | Keep the existing `POSTGRES_*` values; never change them on an existing volume (the postgres image only applies them at first init). User and password default to `postgres` in code if unset. |
| `POSTGRES_HOST` / `_PORT` | DB address | `db` / `5432` | Compose also forces `POSTGRES_HOST=db`. |
| `REDIS_HOST` / `_PORT` | Redis (demo pool, guards, kill switch) | `redis` / `6379` | Backend **and** agent need it; compose sets the host for both. |

### Demo

| NAME | Purpose | Judging-day value | Notes |
| --- | --- | --- | --- |
| `DEMO_MODE` | Enables the one-tap demo (`POST /api/demo/start`) | `1` | Off if empty. |
| `VITE_DEMO_MODE` | Landing page with the demo button at `/` | `1` | **(build)**: rebuild the frontend. Only the exact value `1` counts. |
| `DEMO_GUARDS` | Session and credit limits | leave unset | Unset = **on for ALL users while `DEBUG=0`**, not just demo users. Keep on for judging. `0` forces off, `1` forces on. |
| `DEMO_DAILY_SESSIONS` ⚠️ | Sessions per child per day | `5` or more | Code default 3. The count belongs to the family; a new lease picks a random free family, so judges can collide. Consider 8. |
| `DEMO_SESSION_START_PER_HOUR` ⚠️ | Session starts per user per hour | `12` or more | Code default 6. Judges may share a family. Consider 20. |
| `DEMO_SESSION_MAX_SECONDS` | Max session length | `300` (default) | Goodbye starts 20 s before the end. 0 = no limit. |
| `DEMO_POOL_SIZE` | Demo families | `40` (default, max 40) | |
| `DEMO_LEASE_SECONDS` | How long a visitor keeps a family | `2700` (default) | Landing copy promises 45 minutes. |
| `DEMO_START_RATE` / `DEMO_RESET_RATE` | Per-IP start / per-user reset throttle | `120/hour` (default) | Judges share one office IP; leave the default. |
| `AUTH_RATE` | Login (token obtain) throttle per client IP | `5/minute` (default) | Raise it (e.g. `30/minute`) if many judges log in from one NAT IP. |

### Voice (ElevenLabs)

| NAME | Purpose | Judging-day value | Notes |
| --- | --- | --- | --- |
| `TTS_PROVIDER` | Voice engine | `elevenlabs` | Only `elevenlabs` or `xai` exist (section 7c). No automatic fallback. |
| `ELEVEN_API_KEY` | ElevenLabs key | secret, set on server | Missing or placeholder: each voice session ends with one error log and a `voice_error` message. |
| `ELEVEN_VOICE_ID_AR` / `_EN` ⚠️ | Voice ids | your chosen ids | A hardcoded voice id in `tts_factory.py` is used if unset. Set both. |
| `ELEVEN_MODEL` | Model | `eleven_flash_v2_5` | `eleven_v4_turbo` is rejected. |
| `ELEVEN_DAILY_CHAR_CAP` ⚠️ | Characters/day; past it new sessions go text-only | about `120000` | Code default 20000 (about 10 sessions). Needs credit to match. |
| `LIPSYNC_TIMELINE` | Mouth timed by ElevenLabs character timings | `1` | Needs `livekit-plugins-elevenlabs==1.5.1` (already pinned in `requirements.agent.txt`). `0` = safe audio-only fallback. On by default; the example files ship `1`. |
| `GESTURE_EVENTS` | Word-anchored gestures | `1` | Rides on the lip-sync timeline, so it needs `LIPSYNC_TIMELINE` on. On by default; `0` turns it off. |

### LLM / STT

| NAME | Purpose | Judging-day value | Notes |
| --- | --- | --- | --- |
| `OPENAI_API_KEY` | Answers, speech-to-text, reports | secret, set on server | |
| `LLM_MODEL` | Conversation model | `gpt-5.4-mini` | The model all evals and latency numbers used. |
| `REASONING_EFFORT` | Thinking before the first word | `auto` | Resolves to `none` for this model. |
| `REPORTING_LLM_MODEL` | Reports and weekly summaries | `gpt-5.4-mini` | |
| `STT_PROVIDER` | Speech-to-text | `openai` | |

### LiveKit

| NAME | Purpose | Judging-day value | Notes |
| --- | --- | --- | --- |
| `LIVEKIT_API_KEY` / `_API_SECRET` ⚠️ | LiveKit Cloud credentials | secret, set on server | Dev values in code if unset. |
| `LIVEKIT_URL` ⚠️ | Server/agent URL | `wss://<project>.livekit.cloud` | Defaults to `ws://localhost:7880`. |
| `LIVEKIT_PUBLIC_URL` ⚠️ | URL browsers connect to | `wss://<project>.livekit.cloud` | Same risk. |

### Agent and card gate

| NAME | Purpose | Judging-day value | Notes |
| --- | --- | --- | --- |
| `AGENT_NUM_IDLE_PROCESSES` | Warm agent processes | `1` | Compose default is 1. Idle 2 is untested. |
| `TURN_CARD_GATE` | A card only when the child asks | `1` (default) | **Not in the example file.** `0` = rollback (section 7b). |
| `REPLY_LANGUAGE_FOLLOWS_CHILD` | The CEO's rule: the reply follows the language the child uses, Arabic or English only, instead of the language the parent chose for the session (`backend/conversation/agent/turn_language.py`) | `0` (default, off) | **Off: the lead's design**: the parent chooses the companion's language and the prompt and the TTS keep to it. With `0` every language is exactly hk/12's: `prompt.build_instructions` gives hk/12's prompt byte for byte (its LANGUAGE paragraph, "Always reply in ..."), `_prepare` returns hk/12's turn note and nothing else, and the TTS, the speech cleaner's numbers, the attribution guard's decline line, the goodbye line, `search_bank` and the cards use the session language; the fixed fallback lines use hk/12's script check. With `1`: the parent's language is the default; the reply moves to the other supported language only on a clear message in it (a typed message of 2 or more real words, or a spoken turn of 3 or more, and those words are 3/4 of the message's words), never on one word, a short or mostly-noise fragment, Arabizi, or another script (CJK, Cyrillic, Greek, ...: read as speech-to-text noise); a move to English also needs one common English word (`EN_EVIDENCE` in `turn_language.py`), so a French, Spanish, German, Italian, Portuguese, Turkish or Indonesian sentence does not switch an Arabic session to English; a spoken turn with a phrase speech-to-text models write for silence or music ("thank you for watching", "اشتركوا في القناة" and the others in `STT_HALLUCINATIONS`) never switches; beyond that list a spoken switch trusts the speech-to-text's words; an unclear message keeps the last reply language, and a message in the parent's language brings it back. A TURN LANGUAGE line goes after hk/12's turn note, on its own line (the note's text is not touched), and the LANGUAGE paragraph points to it instead of "Always reply in ..."; the speech cleaner, the decline line, the fixed lines and the goodbye follow the reply language; the ElevenLabs `language_code` hint follows it too (one reconnect on the turn the language changes), but the voice id stays the parent's-language voice and the speech-to-text stays on the parent's language, so a spoken switch happens only when it writes the child's words in the other language. `search_bank` results and the cards stay in the session language (hk/12's choice; the model answers in the reply language from them). On/off values: `1`/`on`/`true`/`yes` = on, read per turn (the prompt once, when the session starts). The eval driver calls `_prepare(text)` as a spoken turn, so with `1` its typed cases switch only at 3 or more words. Leave `0`. |

**Stray off-script characters (no flag; every setting).** The strip in front of the guards is
hk/12's, unchanged (`tts_text.strip_foreign_script`, in the speech cleaner and in the chat's
`transcription_node`): Kana, CJK ideographs and Hangul syllables are removed and every other
character is passed on as it was. So the card markers, the attribution guard and the scripture
filter read exactly hk/12's text, and strip, decline and drop exactly what hk/12's did. Everything
else is handled LAST, after the card markers, the attribution guard and the scripture filter, for
the voice (`tts_node`) and the chat (`transcription_node`) alike (`tts_text.tidy_off_script`, at
the end of `TurnGuardMixin.guard_speech`):

- a letter that looks like a Latin letter (Cyrillic `а е о р с х у і ј ѕ к м н т в`, Greek
  `ο α ε ρ`, Hebrew `ו ן ס`, Hangul `ㅇ ㅣ` and the others in `tts_text.HOMOGLYPHS`) becomes that
  Latin letter: `trusted аdult` with a Cyrillic `а` is said `trusted adult`, not `trusted dult`;
- full-width ASCII forms and the ideographic full stop, comma and space become their plain forms
  (`Hi！` is said `Hi!`), except `｛ ｝ ［ ］ （ ） ＜ ＞ ｀ ＠ ／ ＊ ～ ＿`: their plain forms are markup
  (the TTS reads them aloud or as a tag, the chat shows them raw), so they go like the rest;
- Devanagari and Thai digits become the ASCII digit of the same value (`call ๙๑๑` and
  `call ९११` are said `call 911`);
- any other run of off-script letters, digits, punctuation or symbols goes: one space between two
  other characters, so two words are never glued (`فعلдذلك` is said `فعل ذلك`), and nothing next to
  a space (so a run between two spaces leaves both spaces), at an end, after an opening bracket or
  quote, or before a closing one or a sentence mark.

Because this runs after the guards, it changes only how text they already passed is said or shown.
An attribution written with look-alike or full-width letters gets hk/12's verdict: hk/12's guard
lets `The Рrophet said` (Cyrillic `Р`) through, and so does this branch; it is then said in Latin
letters. On hk/03, until its round 3, this mapping ran in front of the guards, and the round-2 review found it hid
an attribution hackathon's guard declined (`The Prophet！ of Allah said ...`: the full-width `！` became a
sentence end) and let the scripture filter say marked words hackathon's filter dropped (a stray Cyrillic
letter inside a marked word became a space, split the word, and the unmarked half reset the
filter). Neither can happen here. Known changes in what is said: a stray off-script letter inside a word (one
hk/12 passes on, with no Latin look-alike) splits the word in two; a word written in Cyrillic
keeps its look-alike letters as Latin letters and loses the rest (`привет` is said `p bet`); and a
reply written entirely in off-script characters with no Latin look-alike (for example only
Cyrillic `д ж`, Hebrew `אבג`, Thai `ก`, Devanagari `किन`, or `｛｝`), which hk/12 says and shows, now comes out
silent (nothing said, nothing shown), as an all-CJK reply already did on hk/12.

What was measured, and only that (scratch scripts adapted from the #69 round-3.1 review, not part
of the suite), against hk/12-hybrid ccf4330 (a `git archive` of it) with `REPLY_LANGUAGE_FOLLOWS_CHILD`
unset: 301,899 replies, 4,655,772 runs through the voice and chat chains
(9,311,544 outputs); 94 off-script characters, inserted at every character
index (and replacing each character) of 33 attribution lines, 8 marked placeholder lines and 6
card-marker lines, and at word boundaries and inside words of the safety, disclosure and comfort
lines; look-alike spellings of their key words; licences none, hadith and quran; chunk sizes 1,
2, 3, 5, word by word and whole. Every output equals `tidy_off_script(hk/12's output)`
(9,311,544 of 9,311,544; 3,492,900 byte-identical), with 0 declines
lost, 0 gained (2,582,942 on both), 0 extra recitation marks and
0 safety words lost. No output came out empty where hk/12's had words; 3,546 outputs were empty on
both sides (hk/12's own chains already gave nothing for those replies). That grid had no reply
written entirely in off-script characters: the #69 round-3.1 review's probe of such whole replies
(the five shapes above, and `дж {{card:3}}`) found every one said or shown by hk/12 and silent here
(240 of its 4,096,944 outputs), the known change above. The prompt (144 inputs), `_prepare` (384
inputs: both sessions, typed and spoken), 12 turn sequences, the strip before the guards and the
one-shot speech cleaner on every reply above give hk/12's bytes.

Rechecked after merging hk/12-hybrid cfa101c (PR #70: a half-closed `{{card:N}` is now a card
marker, `_licence` reads this turn's items only, new SAFETY and POINTS prompt text; none of it in
the lines this port changed), with the #69 round-3.1 review's own script and corpus, cfa101c (a
`git archive`) against this branch, `REPLY_LANGUAGE_FOLLOWS_CHILD` unset: 98,737 replies, 2,048,472
runs, 4,096,944 voice and chat outputs. The speech cleaner's output, the text each guard read and
the scripture filter's output (the text before the tidy) are cfa101c's on every run; every output
equals `tidy_off_script(cfa101c's output)` (1,801,870 byte-identical); 0 declines lost, 0 extra
recitation marks, 0 safety words lost, 0 Arabic text changed; the 240 whole-reply outputs above are
the only ones silent here and not on cfa101c, and 4,504 were empty on both sides. (The review's
counter also finds 6,008 outputs with more decline lines than cfa101c's: each is a reply that is the
decline line itself with look-alike letters or other off-script characters in it, which the tidy
writes back as the plain line; no guard declined more.) These counts equal the review's run against
ccf4330, except that cfa101c's half-closed marker fix changed 10,796 of hk/12's own outputs (all
replies with a half-closed `{{card...}`; 1,800 of them were empty on ccf4330 and now have words), on
both sides alike. The prompt over 450 inputs (`build_instructions` with no flag argument: `ar`,
`en`, `fr`, empty and `AR`; no age band, the two bands `6-9` and `10-13`, and `4-6`, `10-12` and `x`,
which add no band text; no memory, an empty one, a blank one, a short one and one over the 450-word
cap; no quest list, an empty one and one quest), the agent's instructions (12 inputs: `ar` and `en`,
bands `6-9`, `10-12` and `10-13`, with and without a memory) and `_prepare` (152 inputs and 2 turn
sequences) give cfa101c's bytes.

- The suite holds the same checks on a smaller grid: `OffScriptOriginParityTests` and
  `Hk12ChainsTests` in `backend/conversation/agent/test_off_script_parity.py` (hk/12's chains
  built from its pieces, card markers first, with its own strip pinned).
- Other characters and shapes were not run; by construction the guards read hk/12's text
  whatever the character, since nothing in front of them changed.

### Optional

| NAME | Purpose | Value | Notes |
| --- | --- | --- | --- |
| `LATENCY_LOG` | One `turn_latency` log line per exchange, no text | `1` | Unset = off when DEBUG=0. Useful for judging-day timing. |
| `GUNICORN_WORKERS` | Backend workers | `3` (default) | Only raise with spare CPU. |
| `FRONTEND_URL` ⚠️ | Base of password-reset links | `https://alsadiqai.com` | Defaults to `http://localhost:5173`. Not in the example file. |
| `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | Password-reset email | server-specific | Not in the example file; without them reset emails do not work. Not needed for the demo. |
| `HTTP_PORT` / `HTTPS_PORT` | Caddy host ports | leave unset (80/443) | Local smoke tests only. |
| `XAI_API_KEY` | xAI voice rollback only | leave out unless needed | Section 7c. |

## 4. Deploy order

The order `.github/workflows/deploy.yml` runs on every push to `production` (with `set -e`, any failing step stops the deploy):

Expect about 4 s of backend downtime while `up -d` recreates the containers. Between `migrate` and `up -d` the old code briefly
runs on the new schema (possible short 500s on the gamification endpoints).

| # | Step | Notes |
| --- | --- | --- |
| 1 | `git pull origin production` | |
| 2 | `dc build` | Static files are collected **at image build** (`collectstatic` in `backend/Dockerfile`); no deploy-time collectstatic. A collectstatic failure now fails the build. |
| 3 | `dc run --rm --no-deps caddy caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile` | A bad Caddyfile or `ADMIN_ALLOWED_IPS` stops the deploy here instead of leaving Caddy restart-looping. |
| 4 | `dc run --rm backend python manage.py migrate` | Before `up -d`, so new code never meets the old schema. |
| 5 | `... migrate --check` | Non-zero exit fails the deploy loudly. |
| 6 | `dc up -d` | |
| 7 | `dc up -d --force-recreate caddy` | The Caddyfile is a bind mount; `up -d` alone does not reload it. |
| 8 | `... seed_content` | Idempotent. First run prints `created 311 ... reviewed 273, rejected 0` (273 items + 38 values); later runs `unchanged 311`. |
| 9 | `... seed_demo --ensure` | Only when `DEMO_MODE` is on. Safe: creates missing families, never wipes one in use. Prints `Demo pool ready: 40 families`. |
| 10 | `curl -fsS --resolve alsadiqai.com:443:127.0.0.1 --retry 10 ... https://alsadiqai.com/api/health/` | Health gate, last step: 200 only if Django, DB and Redis answer through Caddy on the box itself (no DNS dependency; the hostname must equal `DOMAIN` in `.env`). A wrong `DJANGO_ALLOWED_HOSTS` (400) or a down DB/Redis (503) turns the run red. |

Also: with `DEMO_MODE=1` the backend container runs `seed_demo --ensure` itself in the background once migrations pass.

**First deploy only** (`scripts/init-prod.sh`, run by hand): migrate, `migrate --check`, `seed_admin`, `seed_content`,
`seed_demo --ensure` (only if DEMO_MODE). `seed_admin` is first-deploy only; it skips an existing admin.

**NEVER run `seed_demo` without `--ensure` in production.** It wipes every demo family, including ones judges are using.

## 5. Deploying

1. From your laptop, in the repo:
   ```
   git fetch origin
   git rev-parse --short origin/production                      # write this down: your rollback sha (2bc1fe5f on 5 Oct)
   git rev-list --count origin/hackathon..origin/production     # must print 0
   git merge-base --is-ancestor origin/production origin/hackathon && echo "fast-forward OK"
   git push origin origin/hackathon:production
   ```
   Checked 5 Oct: production **is** an ancestor of hackathon (0 production-only commits), so the push is accepted without force.
   If the count is no longer 0 or "fast-forward OK" does not print (someone pushed to production meanwhile), the push will be
   **rejected**. Do not force. List them with `git log --oneline origin/hackathon..origin/production`, merge `origin/production`
   into a branch from hackathon, test it, and push that. Use `--force-with-lease` only after confirming those commits are
   already in hackathon.
2. Watch the run: `gh run watch` (pick "Deploy to Production").
3. On the server: `dc logs -f backend livekit_agent caddy`

| Where | Good | Bad |
| --- | --- | --- |
| Actions | green run, "Deployment complete." | red at migrate / `migrate --check` (non-zero = an unapplied migration) |
| seed_content | first run `created 311, updated 0, unchanged 0, skipped (reviewed) 0, reviewed 273, rejected 0`; re-run `created 0, updated 0, unchanged 311 ... reviewed 273, rejected 0` | `REJECTED ...`, `UNKNOWN REVIEW KEY`, any traceback |
| seed_demo | normally `Demo pool ready: 40 families (created 0: [])` (the backend entrypoint already seeded the pool in the background), or "demo seed skipped" with DEMO_MODE off. On a first deploy, backend log lines `demo: knowledge bank not seeded (run seed_content); no sources for slot N` are expected and harmless: the CI `seed_demo --ensure` after `seed_content` tops sources up | traceback; or "skipped" when you expected demo on |
| backend | gunicorn "Listening at ... :8000", workers booted | `ImproperlyConfigured` (missing `DJANGO_SECRET_KEY`), HTTP 400 / `DisallowedHost` (wrong `DJANGO_ALLOWED_HOSTS`; the health gate goes red too), DB connection refused |
| livekit_agent | worker registered with LiveKit, no errors | `voice_error`, `missing_key`, `key_rejected`, `quota_or_plan` (ElevenLabs auth/credit), "worker is at full capacity" |
| caddy | certificate obtained, serving on 443 | `adapting config` errors, `remote_ip` parse errors (bad `ADMIN_ALLOWED_IPS`), restart loop |
| OpenAI (in agent log) | none | `429` / rate-limit (section 8) |

## 6. Post-deploy smoke test (5 minutes)

| # | Do this | Expect |
| --- | --- | --- |
| 1 | `curl -fsS https://alsadiqai.com/api/health/` | HTTP 200, `{"status":"ok"}` (db and redis `ok`) |
| 2 | `python3 scripts/smoke_alsadiqai.py https://alsadiqai.com` (add `--no-session` to save a daily session), from an IP **not** in `ADMIN_ALLOWED_IPS` (e.g. phone hotspot) | 8 checks, all PASS, exit 0. Leases one demo family for 45 min. From an allowed IP check 8 fails by design (it gets a 302 to the admin login). |
| 3 | Open https://alsadiqai.com on a phone, tap the one-tap demo | Lands in the child view, no login |
| 4 | Child voice session in Arabic: say hello | Arabic voice reply in the ElevenLabs voice, the mouth moves |
| 5 | Ask «ليش لازم اكون صادق؟» | A source card appears and the verse recitation plays. Confirm the audio file is served: `curl -sI https://alsadiqai.com/static/quran/002083.mp3` prints `200` and an audio type (or see 200 in devtools) |
| 6 | Parent view (banner button), then the parent Insights page (`/parent/insights`) | The "Sources discussed this week" (المصادر التي تمت مناقشتها هذا الأسبوع) section shows this week's sources. Data: `GET /api/reporting/insights/<child_id>/`, field `sources` |
| 7 | `/admin/` from a phone on **mobile data** (not an allowed IP), then from an allowed IP | Mobile data: **404** "Not found" (the Caddyfile answers 404, not 403). Allowed IP: the Django admin login page |

If step 1 fails, go straight to section 7.

## 7. Rollback

**a) Code rollback to the old production commit.** The new migrations are forward-only in practice (gamification 0005 deletes
honesty-badge awards; smc 0006 unverifies legacy references), so old code needs the **pre-deploy DB backup restored**.
Do **not** start by force-pushing the old sha to `production`: the workflow that runs is the old one, its `git pull` of an
ancestor says "Already up to date", and the new code is rebuilt. Roll back on the server first:
```
# server
cd /opt/alsadiq
git fetch origin && git reset --hard <previous-sha>
dc build
dc stop backend livekit_agent
# restore the pre-deploy DB into a fresh database (--clean is unreliable: new tables have FKs into old ones)
dc exec -T db sh -c 'dropdb -U "$POSTGRES_USER" --force "$POSTGRES_DB" && createdb -U "$POSTGRES_USER" "$POSTGRES_DB"'
dc exec -T db sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --exit-on-error' < "$DUMP"   # same file as the backup; in a new shell: DUMP=$(ls -t ~/pre-deploy-*.dump | head -1)
# the old frontend image only refills frontend_dist when it is EMPTY, and caddy depends_on frontend, so drop both and the volume
dc rm -sf caddy frontend
docker volume rm "$(basename "$PWD")_frontend_dist"   # = alsadiq_frontend_dist; NEVER `down -v` (it drops postgres_data)
dc up -d && dc up -d --force-recreate caddy
# laptop, only after the server is healthy, so the branch matches (the workflow it triggers is then harmless)
git push --force-with-lease origin <previous-sha>:production
```
Notes: the old production Caddyfile proxies `/admin` to everyone, so a full rollback **reopens `/admin` publicly**; restrict it
another way until you roll forward. Retagging the old image ids you recorded in section 2 (`dc images`) is faster than
rebuilding. Anything done after the backup is lost (acceptable: demo data is synthetic). If only a feature is bad, prefer b to e
over a full rollback.

**b) Prompt or card regression:** set `TURN_CARD_GATE=0` in the server `.env`, then
`dc up -d --force-recreate livekit_agent`.

**c) Voice broken (ElevenLabs auth or credit out):** `tts_factory.py` knows only two providers: `elevenlabs` and `xai`. There is no OpenAI voice.
- Fastest, no redeploy, new sessions only: `dc exec backend python manage.py voice_mode text` (text-only chat with a "voice is resting" notice). Undo with `voice_mode eleven`.
- Manual xAI rollback: `voice_mode xai`, or `TTS_PROVIDER=xai` in `.env` (then recreate `livekit_agent`). Needs `XAI_API_KEY`
  (optional `XAI_TTS_VOICE`, `XAI_TTS_LANGUAGE`, `ARABIC_TTS_LOCALE`). The xAI path is dormant and was not rehearsed here;
  the team rule is that it is a manual choice, never automatic.

**d) Lip sync glitches:** `LIPSYNC_TIMELINE=0` in `.env`, then `dc up -d --force-recreate livekit_agent`.

**e) Demo flood or runaway cost:** lower `DEMO_DAILY_SESSIONS`, `DEMO_SESSION_START_PER_HOUR` or `ELEVEN_DAILY_CHAR_CAP`, or
`voice_mode off` (new sessions refused politely). To turn the demo off: `DEMO_MODE=0` (then `dc up -d --force-recreate backend`)
and `VITE_DEMO_MODE=0` (needs `dc build frontend && dc up -d`).

## 8. Capacity and judging-day watch list

- **OpenAI is the first ceiling.** About 200k TPM / 500 RPM is roughly **6 to 7 children talking at once**. 30 judges can overlap, so
  request a higher limit before the day. Symptom: `429` / rate-limit lines in `livekit_agent`, slow or empty replies.
- **Droplet:** 4 vCPU / 8 GB. Majd's load rehearsal (`docs/hackathon/latency/LOAD-REHEARSAL.md`): one agent container, idle 1,
  handled 10 simultaneous voice sessions (about 0.1 core and 165 MB each, plus a burst of about 3 cores for about 10 s when 10 start together).
  Watch for "worker is at full capacity" in the agent log.
- **ElevenLabs cap math:** 20000 chars is about 10 sessions. 30 judges x 2 voice sessions needs about 120000 a day. Past the cap new
  sessions go text-only (running ones finish). Check usage: `dc exec backend python manage.py voice_mode` (chars used vs cap).
- **Demo pool:** 40 families, 45-minute lease: up to about 53 new visitors an hour. When all are busy, visitors see a "busy" page that retries.
- **Uptime:** point a monitor at `https://alsadiqai.com/api/health/` (200 ok, 503 degraded).
- **Daily smoke test** until 22 Oct: `python scripts/smoke_alsadiqai.py https://alsadiqai.com --no-session`.

## 9. Known risks (after the fixes)

| Risk | Level | What to do |
| --- | --- | --- |
| Data-changing migrations: smc 0006 unverifies all legacy references (irreversible); gamification 0005 deletes honesty-badge awards (re-awarded under "values practised"); gamification 0004 overwrites admin-edited badges with the same name | Medium | Take the backup (section 2). No user, child or session columns are changed. |
| Demo guards apply to **all** users when `DEBUG=0` (300 s sessions, daily/hourly caps, char cap) | High if forgotten | Intended for judging. Afterwards decide: raise the caps or set `DEMO_GUARDS=0`. |
| Caddy only reads its config on creation; a bad `ADMIN_ALLOWED_IPS` takes the whole site down | High | Validate (section 2, step 6); force-recreate in the deploy order. |
| Silent dev defaults when `.env` lacks values (LiveKit, Postgres, `VITE_API_BASE_URL`, `FRONTEND_URL`, `DOMAIN`) | Medium | Walk every ⚠️ row in section 3. |
| Frontend build ignores `package-lock.json` (`npm install` in `frontend/Dockerfile`, on purpose, for linux native binaries): caret deps can float between builds | Low | Do not rebuild the frontend casually on judging day. |
| Frontend base image is Node 20 while a dependency wants Node >= 22.22 | Low | `EBADENGINE` warning only; the build succeeds. |
| Password-reset links point to `localhost` and email is unconfigured (pre-existing) | Low | Set `FRONTEND_URL` and `EMAIL_*` if reset must work; not needed for the demo. |
| `REPORTING_QUESTS_DAILY_CAP` code default flipped to off; the example sets `1` | Low | Keep it set in `.env`. |
| Recitation mp3s (46 MB) only exist if the image build's `collectstatic` worked (a failure now fails the build) | Low | Smoke step 5 (the `curl -sI` on an mp3). |

## Rehearsal results

Local rehearsal 2026-10-05 on `hk/deploy-preflight`, Docker, dummy keys.

- **Builds OK:** backend 1.04 GB (build-time collectstatic: 237 files, 74 Quran mp3s), agent 1.33 GB (no mp3s), frontend 35 MB.
- **Upgrade from production `2bc1fe5f`** with legacy parent/child/session/messages: all migrations applied, `migrate --check` 0, legacy rows intact.
- **seed_content:** reviewed 273, rejected 0, 38 values. 40 demo families, each with this-week sources. Second run fully idempotent.
- **Fresh install** via the `init-prod.sh` steps: PASS.
- **Smoke:** 8/8 (from a non-admin IP). `/static/quran/002083.mp3` 200 `audio/mpeg`; `/admin` 404; parent insights `GET /api/reporting/insights/<child_id>/` returns `sources` (5 for a demo parent).
- **Backend tests:** 1495 in the backend image, 0 failures introduced. 79 environmental errors, identical on the base: 76 need agent deps (they pass in the agent image) and 3 read the repo-root `.env.example`, which is outside the docker context.
- **Not exercised:** real LiveKit / OpenAI / ElevenLabs calls (dummy keys). Covered by post-deploy smoke test steps 4 and 5.
