# Demo guards (credit and safety)

For the public demo at https://alsadiqai.com. The guards protect the ElevenLabs and OpenAI
credits and keep a stranger from running up long sessions. No migration, no new service: they
use Redis and the existing models.

Code: `backend/conversation/demo_guards.py` (shared), `backend/conversation/throttles.py`,
`backend/conversation/agent/demo_limits.py` (the agent half), the `voice_mode` command.

## The voice rule

ElevenLabs is the voice. Nothing ever switches to xAI by itself. If ElevenLabs cannot be used
(missing or placeholder key, plugin does not build, the API rejects the key or voice or plan)
the agent logs ONE error naming the cause (never the key), publishes a `voice_error` message to
the room and ends the session.

xAI exists only as a manual rollback an operator chooses: `TTS_PROVIDER=xai` in the env, or
`python manage.py voice_mode xai`. It never turns on by itself, not even when the ElevenLabs
budget runs out (that case goes text-only).

## What is limited

| Guard | Default | Env var | What happens |
| --- | --- | --- | --- |
| Session length | 300 s | `DEMO_SESSION_MAX_SECONDS` | 20 s before the end the agent stops taking new turns. A reply that is playing finishes (up to lead + grace = 30 s; only a longer one is cut). Then Sadiq says a short goodbye (no scripture) in the session language, with its own 12 s budget, and the room is closed. Worst case the room closes at limit + grace + 12 s. A rejoin after the limit is closed at once, without a greeting. The LiveKit token also expires a little after the limit. |
| Sessions per child per day | 3 | `DEMO_DAILY_SESSIONS` | The 4th start answers 429 `daily_limit` with a friendly Arabic and English message. |
| Session starts per user per hour | 6 | `DEMO_SESSION_START_PER_HOUR` | The 7th start in an hour answers 429 `rate_limited` (with `Retry-After`). Next to the existing login throttle. |
| Judge accounts (`judgeN-ar/en`) | 30 / day, 20 / hour | `JUDGE_DAILY_SESSIONS`, `JUDGE_SESSION_START_PER_HOUR` | Used instead of the two rows above for judge children. See `JUDGE-ACCOUNTS.md`. |
| ElevenLabs characters per day | 20000 | `ELEVEN_DAILY_CHAR_CAP` | Past it, NEW sessions are text-only with a "Sadiq's voice is resting, let's chat by text" message. Running sessions finish (they are bounded by the time limit). |

`0` means no limit. The guards are OFF while `DEBUG=1`, ON otherwise. `DEMO_GUARDS=1` forces them
on (even with DEBUG), `DEMO_GUARDS=0` forces them off. The day rolls over at midnight in
`DEMO_DAY_UTC_OFFSET_HOURS` (default 3, Riyadh). Other tuning: `DEMO_GOODBYE_LEAD_SECONDS` (20),
`DEMO_SESSION_GRACE_SECONDS` (10), `REDIS_GUARDS_DB`, `REDIS_URL`.

If Redis is down the guards fail open (the session goes ahead, one error is logged). The daily
session cap then falls back to counting `Session` rows.

Both the backend and the agent container need Redis (`REDIS_HOST`). The agent reads the
per-session voice decision there and counts the ElevenLabs characters there, so without it the
kill switch and the budget do not reach the agent. `docker-compose.prod.yml` sets
`REDIS_HOST=redis` for both. With the guards on and no Redis configured, each process logs one
error saying so.

## Kill switch

The Redis key `VOICE_MODE` is read at the start of every session (no redeploy, running sessions
are not touched):

| Value | New sessions |
| --- | --- |
| `eleven` | ElevenLabs voice |
| `text` | text-only, with the "voice is resting" message |
| `off` | refused with 503 `voice_off` and a friendly message |
| `xai` | xAI voice. Manual operator rollback only |
| unset (`auto`) | follows `TTS_PROVIDER` from the env |

On the server:

```
docker compose -f docker-compose.prod.yml exec backend python manage.py voice_mode          # status + today's usage
docker compose -f docker-compose.prod.yml exec backend python manage.py voice_mode text
docker compose -f docker-compose.prod.yml exec backend python manage.py voice_mode off
docker compose -f docker-compose.prod.yml exec backend python manage.py voice_mode eleven
docker compose -f docker-compose.prod.yml exec backend python manage.py voice_mode xai      # manual rollback
docker compose -f docker-compose.prod.yml exec backend python manage.py voice_mode auto     # clear the switch
```

The status shows the switch, what new sessions get and why, ElevenLabs characters used against
the cap, sessions today and the limits.

## API contract (for the frontend)

`POST /api/conversation/sessions/` takes an optional body `{"text_only": true}`: the child asked
for a text chat (the web app offers it after `voice_error` and after a busy 503). It can only turn
the voice off, never on, so it cannot cost credits or reach xAI. The kill switch and the daily cap
still apply.

A success (200 or 201) gains:

- `voice_mode`: `eleven` | `xai` | `text`
- `notice`: null, or `{code, ar, en}` (show it, and chat by text when `voice_mode` is `text`)
- `max_seconds`: number or null
- `session_ends_at`: ISO time or null

Refusals are `{detail, code, message: {ar, en}}`, `detail` already in the child's language:

- 429 `daily_limit`
- 429 `rate_limited`
- 503 `voice_off`

Data messages in the LiveKit room:

- topic `voice_error`: `{"type":"voice_unavailable","provider":"elevenlabs"|"xai"|"none","code":...}`
  (codes: `missing_key`, `plugin_unavailable`, `build_failed`, `key_rejected`, `voice_rejected`,
  `quota_or_plan`, `unreachable`, `failed`, `voice_off`)
- topic `session_limit`: `{"type":"session_ending","seconds_left":N}` then `{"type":"session_ended"}`

In text mode the agent does not use the microphone or speak. Chat works over the normal LiveKit
text channel.

## Credits

ElevenLabs bills per character. 20000 characters a day is about 10k credits a day on the flash
model (half a credit per character). Set `ELEVEN_DAILY_CHAR_CAP` from what is actually left
before the demo. Characters are counted as they stream to ElevenLabs (the cleaned text). The
Redis write runs in a worker thread in batches of about 200 characters, plus the rest at the
end of each reply, so it never stalls the audio. In a live check the count was within 2
characters of the spoken text.

## Known gaps

- The web child screen reads all of the above (branch `hk/demo-voiceui`: text chat, refusal cards,
  "voice is resting" with a text chat, the clock chip, the goodbye and the end card). The mobile
  app does not read them yet.
- A session restarted as text after `voice_error` counts as a new daily session.
- A page reload starts a new session and uses a daily slot.
- The token expiry does not kick a connected client. The agent closes the room.
- A running session is not cut when the character cap is passed. The time limit bounds it.
