# Load rehearsal: concurrent voice sessions

Date: 2026-10-05. Branch: hk/product-web (HEAD fec150e at the start). Measured by the load rehearsal engineer on a
local docker stack built from this worktree. Raw run output is outside git (`Alsadiq-wt/load-rehearsal/runs/`).

No product code and no agent prompt was changed. The agent prompts and religious rules stay with the lead.

## Verdict in five lines

1. One agent container with `AGENT_NUM_IDLE_PROCESSES=1` (the production default) handled 10 simultaneous voice
   sessions: 10 of 10 joined, no agent errors, and reply latency did not move with concurrency.
2. Time to first audio is about 3.0 s for the greeting and about 2.6 s from the VAD stop to the reply, at 1, 5 and 10
   sessions alike. The first greeting after a cold stack is about 0.4 s slower.
3. The real limit is hardware, not the worker count: about 0.1 core and about 165 MB per session at steady state, plus a
   short CPU burst of about 3 cores for about 10 s when 10 sessions start in the same second. Use a droplet of at least
   4 vCPU and 8 GB for 10 simultaneous sessions. A 2 vCPU droplet is fine for about 4 to 5.
4. FOUND A PRODUCT BUG: `start_session` can return HTTP 500 when two sessions start in the same instant (unique
   constraint race on `livekit_room_name`). 2 of 5 simultaneous starts failed. FIXED afterwards by the pre-deploy fixer
   (the suggested patch below, with a concurrency test); see `handoffs/product-web.md` section 18.1.
5. Budget used: 9573 ElevenLabs characters (cap 15000) and 293 OpenAI calls (cap 300).

## Method

- Own compose project `alsadiq-lr` (explicit `-f` files, so the `.env` `COMPOSE_FILE` is ignored). Ports remapped into
  5441 to 5445. Started and stopped by a scratch orchestrator; torn down with `docker compose down` and no `-v`.
- Stack: `docker-compose.prod.yml` services (db, redis, livekit, backend, ONE `livekit_agent`) with `DEMO_MODE=1`,
  then `seed_content` (112 created) and `seed_demo` (40 demo families). The agent runs `python -m
  conversation.agent.main start` (production mode), so every job gets its own forkserver process.
- Clients: the e2e voice kit (`Alsadiq-wt/e2e-voice`, `--project` this worktree). Headless Edge, fake microphone WAV,
  one browser per session, half Arabic and half English, 2 child turns each (the WAVs are cut after turn 2).
- Real services: OpenAI (`gpt-5.4-mini`, `gpt-4o-mini-transcribe`) and ElevenLabs. No gpt-4.x, no xAI.
- Counting: a log shim (scratch, mounted into the containers, not in git) logs every OpenAI SDK request and tags each kit
  line with the agent process id and room, so ten parallel sessions can be told apart. ElevenLabs characters come from
  the agent's own counter and match the Redis key `demo:eleven_chars:<day>` (delta equal in every run).
- Resources: `docker stats` and `docker top` sampled during each run.

### What the numbers mean

- Greeting TTFA: from the browser's click on Start to the first inbound audio. Includes session creation, the token,
  the room join, job dispatch and the first TTS bytes.
- Client first speech: from the end of the question audio at the microphone to the first inbound audio above a speech
  level of 0.03.
- Server total: from the agent's VAD user-stop to its first audio. It includes the end-of-turn wait of about 1.1 s.
- The reply numbers here (about 2.6 s server total) are lower than RESULTS.md (5.3 s). They are not comparable: this
  rehearsal uses only the first 2 questions of each script, and the earlier test used the 4-turn set where nearly every
  turn made a second LLM round for the reference tool. This document measures how latency changes with load, not its
  absolute value.

### Caveats

- The browsers, the stack and the load tool share one 24-core Windows machine, so client-side CPU competes a little. The
  stack runs with `DEBUG=1` from the dev `.env`.
- LiveKit and the network path are localhost, so real-world WebRTC and mobile network delay (add roughly 0.1 to 0.3 s)
  is not in these numbers.
- The 2-turn sessions are short. Memory and CPU for a full 5-minute session are a little higher; the cap
  `DEMO_SESSION_MAX_SECONDS` (300) bounds it.

## Results

All runs: one agent container, 1 idle process, `TTS_WARMUP` on, unless the label says otherwise. Seconds are medians.

| run | what | sessions | joined | greeting TTFA | client first speech | server total | agent CPU peak | agent mem peak | ElevenLabs chars | OpenAI chat calls |
|---|---|---|---|---|---|---|---|---|---|---|
| cold1 | 1 session on a fresh stack | 1 | 1/1 | 3.43 | 2.30 | 2.78 | 11% | 0.53 GB | 292 | 8 |
| c5_idle1 | 5 at the same instant (INVALID, see below) | 5 | 3/5 | 3.01 | 2.10 | 2.96 | 174% | 0.85 GB | 857 | 25 |
| c5s | 5, starts staggered 0.4 s | 5 | 5/5 | 2.98 | 2.05 | 2.64 | 111% | 1.20 GB | 1441 | 43 |
| c10b | 10, starts staggered 0.4 s | 10 | 10/10 | 2.96 | 2.60 | 2.63 | 297% | 2.03 GB | 3297 | 85 |
| cpu1 | 4, agent container limited to 1 CPU | 4 | 4/4 | 3.27 | 2.80 | 2.79 | 88% (of 1 core) | 1.01 GB | 1272 | 34 |
| nowarm2 | 2, `TTS_WARMUP=0` | 2 | 2/2 | 2.17 | 2.55 | 2.88 | 23% | 0.70 GB | 595 | 17 |

CPU is docker's percentage, where 100% is one core. The Python process RSS sum (c10b: 3.1 GB across 14 processes) double
counts pages shared between forked processes; the container figure is the one to size by.

Per-session detail for the two runs that matter most:

- c10b (10 sessions): greeting TTFA 2.56 to 3.08 s for nine sessions and 5.05 s for one (the 10th spawn waited behind the
  burst). Server total 2.15 to 3.16 s, p90 2.91 s. Zero error lines in the agent and backend logs.
- c5s (5 sessions): greeting TTFA 2.61 to 3.02 s. Server total p90 3.7 s; the worst turn (3.87 s) had a 2.1 s
  end-of-turn wait, which is speech-detection noise, not load.

### Invalid runs (kept for the record, not used for conclusions)

- c5_idle1: 2 of 5 browsers got HTTP 500 from session start. That is the product bug below. The three sessions that did
  start behaved normally.
- c10s: 4 of 10 browsers got `ERR_CONNECTION_REFUSED` before they reached the app. That was my static file server (a
  scratch one for the built frontend), whose listen backlog was too small for 10 browsers at once. It is a harness
  artefact. I fixed the harness and reran as c10b. Production serves the frontend from Caddy, which is not affected.

## What the load looks like

- Idle worker: one agent container idles at about 0.4 GB.
- Per session at steady state: about 0.1 core and about 165 MB (c10b: 0.4 GB baseline plus 10 sessions gave 2.0 GB).
- Spawn burst: every job is its own process, and the worker spawns a process on demand when more jobs arrive than idle
  processes. Each spawn loads Django and the Silero VAD model. 10 simultaneous starts drew about 3 cores for about 10 s
  (c10b peak 297%). 5 starts drew about 1.1 cores (c5s peak).
- Backend (gunicorn, 3 workers): at most 7% CPU and 0.3 GB in every clean run. It is not a bottleneck.
- Per session: about 300 characters of ElevenLabs text for the greeting and 2 turns, about 8 OpenAI chat calls (about 4 in
  the agent and about 4 in the backend's post-session reporting) and one speech-to-text stream. The OpenAI column in the
  table counts chat calls only; the 31 speech-to-text streams are in the budget table.

## Findings

### 1. Session start race (product bug; fixed after this rehearsal, see handoff 18.1)

The text below describes the code as it was when the rehearsal ran. The patch suggested at the end of this finding is now
applied in `conversation/services.py`.

`conversation/services.py` `start_session` creates the `Session` row first and sets the room name afterwards:

```python
session = Session.objects.create(child=child_profile, status='active')
room_name = f"session_{session.id}"
session.livekit_room_name = room_name
session.save(update_fields=['livekit_room_name'])
```

`livekit_room_name` is `CharField(max_length=100, unique=True, blank=True)`, so every new row first holds the empty
string. Two requests that insert in the same moment both write `''` and one hits the unique constraint: HTTP 500 to
that child. Reproduced: 2 of 5 browsers pressed Start in the same instant. With starts 0.4 s apart there were no
failures in 19 sessions.

Real exposure on judging day: two children pressing Start within a few milliseconds. Low, but a judge who gets a 500 sees
a broken demo.

Suggested patch (now applied in commit `34af7ec`, `conversation/services.py`; the suggestion is kept as it was written):

```python
import uuid
...
session = Session.objects.create(
    child=child_profile, status='active',
    livekit_room_name=f'pending_{uuid.uuid4().hex}')
session.livekit_room_name = f"session_{session.id}"
session.save(update_fields=['livekit_room_name'])
```

Add a test that starts several sessions from threads at once (or at least asserts that two fresh sessions never share a
placeholder room name).

### 2. `load_threshold` and the CPU monitor

`conversation/agent/main.py` builds the worker options with only `AGENT_NUM_IDLE_PROCESSES` from the environment;
`load_threshold` stays at the production default of 0.7. The CPU monitor is cgroup aware: it measures the agent
container's own CPU use against its cgroup quota, or against `psutil.cpu_count()` when there is no quota. Effective load
is the measured load plus a reservation for jobs that are starting. While the load is above 0.7 the worker marks itself
unavailable and LiveKit assigns new rooms to no one.

On a 2 vCPU droplet 0.7 is 1.4 cores. A 10-session burst draws about 3 cores, so it can flip the worker to FULL.

The cpu1 run is the evidence: the agent container was limited to 1 CPU (threshold 0.7 core) and 4 sessions were started
0.4 s apart. The worker logged "worker is at full capacity" twice (load 0.86 for about 5 s, load 0.77 for about 2.5 s)
and "worker is below capacity" after each. All 4 sessions still joined, greeting TTFA 2.5 to 3.9 s (median 3.27 s, the
slowest of the clean runs). Short FULL windows recover; sessions that start in a window can wait for the next one.

Options, in order of cost:

- Use a bigger droplet (recommended, no code change).
- The `NUM_CPUS` environment variable overrides the CPU count the monitor uses. It raises the capacity the monitor
  believes it has. It is a no-code knob but it hides real overload; only use it on a droplet that really has the cores.
- Code change (flagged option, not applied): read an `AGENT_LOAD_THRESHOLD` environment variable in `_worker_options`.
- `AGENT_NUM_IDLE_PROCESSES=2`: from reading the livekit-agents source, a larger idle count shrinks the per-job
  reservation (`load_threshold / max(idle, 1)`) and avoids one cold spawn. It is UNTESTED; I ran only idle=1 because the
  OpenAI budget ran out. It costs about 0.2 GB of memory per extra idle process.

### 3. Cold start and TTS warm-up

- Cold: the first greeting on a fresh stack was 3.43 s against a warm median of about 3.0 s (+0.4 s). Once an idle
  process exists, a new session pays no spawn cost; the idle process is replaced in the background.
- The TTS warm-up (`TTS_WARMUP`, on by default, never fatal) shows no measurable effect: TTS time to first byte was about
  0.2 s with it on and off. The nowarm2 greeting (2.17 s, 2 sessions) was in fact faster than the warm runs, so the
  difference is inside the noise. Keep the default (on). It is cheap and removes the connection setup from the first
  caller.

### 4. Known 404 in the browser console

Every browser logs one 404 for `KFGQPCHafs.ttf`. This is the intentional fallback described in
`frontend/public/fonts/README.txt` (the font file is not bundled; the page falls back to the system font). It is not a
failure and appears in every run. It is not counted in the error totals above.

## Recommendation for judging day

| setting | value | why |
|---|---|---|
| agent containers | 1 (`livekit_agent`) | One worker with idle processes covered 10 sessions. A second worker adds memory, not reliability, at this size. |
| `AGENT_NUM_IDLE_PROCESSES` | 1 (default). Optional 2 if the droplet has 8 GB or more, after a quick 5-browser check. | idle=1 is the measured setting. idle=2 is reasoned, not measured. |
| `TTS_WARMUP` | leave on (default) | Cheap, no measurable cost or gain. |
| droplet | 4 vCPU and 8 GB for up to 10 simultaneous sessions. 2 vCPU and 4 GB only if you expect 4 to 5. | See the load numbers above. Caddy, Postgres, Redis, LiveKit and gunicorn share the machine with the agent. |
| `ELEVEN_DAILY_CHAR_CAP` | about 120000 as in DEPLOY-CHECKLIST.md | A 2-turn session is about 300 characters; a full 5-minute session of 8 to 10 turns is about 1500 to 2500. 30 judges at 2 sessions each need about 90000 to 150000, so 120000 is right if the account has the credits. |
| `DEMO_DAILY_SESSIONS` | 5 | As in DEMO-LOGIN.md. |
| `DEMO_SESSION_START_PER_HOUR` | 12 | As in DEMO-LOGIN.md. |
| `DEMO_SESSION_MAX_SECONDS` | 300 (default) | Bounds each session's CPU, memory and characters. |

Before judging:

1. The session start race patch above is applied (`34af7ec`); nothing to do. The deploy must include that commit.
2. Check `docker stats` on the real droplet during a 5-browser rehearsal and confirm the agent never logs "worker is at
   full capacity". If it does, the droplet is too small or the starts are too bunched.
3. Watch the agent log for "worker is at full capacity" during the event. Restarting the agent container clears a stuck
   state and costs the active sessions only.
4. Confirm the droplet's vCPU count. The lead gave 8 GB RAM and 180 GB SSD on 4 Oct (`submission/CHECKLIST.md` section F,
   item 1); the vCPU count is not recorded. 10 simultaneous sessions need at least 4 vCPU (table above).

## Budget

| resource | used | cap |
|---|---|---|
| ElevenLabs characters | 9573 (cold1 292, c5_idle1 857, c5s 1441, c10s 1819, c10b 3297, cpu1 1272, nowarm2 595) | about 15000 |
| OpenAI calls | 293 (262 chat completions, of which c10s about 50, and 31 speech-to-text streams) | 300 |

c10s is the invalid run; its spend is included. The OpenAI budget is used up, so idle=2 and a second 10-session pass were
not run.

## Reproduce

The harness is scratch code outside git (`Alsadiq-wt/load-rehearsal/`): `lr.py up`, `lr.py agent --idle N`,
`lr.py run --n 10 --stagger 0.4 --label X`, `lr.py down`. It needs the e2e voice kit and a built frontend served on port
5441. It never prints key files or tokens.
