# Handoff: Voice reply latency (task 08)

Branch `hk/08-latency`, 13 commits on top of `6fc60f8` (an older `hk/demo-mvp`), not pushed. Written 2026-10-04.
Owner: Majd. Numbers and claims below come from the task file, `docs/hackathon/latency/RESULTS.md`, the code on the branch and the review run.

## 1. What this is

The voice companion took about 3 s (dev) to 5 s or more (measured, tool turns) from the end of the child's sentence to the first reply sound. Task 08 measures that gap and tries the free fixes: a faster model setup, a shorter prompt, fewer LLM rounds, a warm voice socket and a soft thinking sound.

Result in one line: the plan is built and measured, but the task bar (median at least 30 percent below baseline) is NOT met. Server total went from 5.47 s to 5.29 s (minus 3 percent). The cause is a tool round that task 08 does not touch (section 6).

Everything is behind env flags. Defaults are safe: nothing changes the end-of-turn wait or interruptions.

## 2. What was built and why

The research deck is "Instant Replies for Al-Sadiq". Its plan is `APPROACH.md` (in the job folder `%USERPROFILE%\.claude\jobs\9adf820e\tmp\deck\`, with `AUDIT.md` and `RESEARCH.md`). Key idea from it: the gap is four steps in a row (end of turn and STT final, LLM first sentence, TTS first byte, network), so each step gets its own lever. The numbers in section 3 of that file were estimates. This task replaced them with measurements.

Built, one commit per step (plan step numbers from APPROACH.md section 4):

| Plan step | What | Why |
|---|---|---|
| 1 | One `turn_latency {json}` log line per exchange | Every number except TTS was a guess |
| 3 | One model default everywhere: `gpt-5.4-mini` and `gpt-4o-mini-transcribe`, `STT_REALTIME=1`, a test keeps code and both env examples equal | Prod used gpt-5.2 and no STT model |
| 4 | `REASONING_EFFORT` (auto, none, minimal, low, medium, high, xhigh, off) | On GPT-5 and GPT-6 models the hidden thinking is the biggest first-word cost. The 1.5.1 plugin sends nothing for gpt-5.4-mini, gpt-5.6-luna or gpt-6-luna |
| 4 | `STT_MODEL` guard | Two OpenAI live models cannot run on the 1.5.1 plugin (section 9) |
| 5 | Speak first: the model says its reply, then calls `record_engagement`, and that second LLM round is cancelled | A points call used to cost a whole extra round |
| 6 | `PROMPT_PROFILE=full or compact`, plus a 3 to 6 word opener line and a 450 word memory cap (both profiles) | Fewer tokens to read before the first word |
| 7 | TTS warm-up: open the ElevenLabs socket as soon as the voice is built | The first reply paid the connection set-up |
| 8 | Soft hum filler with `BackgroundAudioPlayer` | Gives the child a sound while a slow answer is on its way |

The lead's rules are kept: no automatic fallback to xAI, no scripture in code, prompts or data, no safety rule weakened, no gpt-4.x model suggested anywhere (a test fails if one reappears in the env examples), Silero stays at 0.55 s, interruptions stay on.

## 3. Where it lives

All in `backend/conversation/agent/` unless noted. Tests sit next to the code.

- `latency_log.py` and `test_latency_log.py`: the per-turn line.
- `reasoning_effort.py` and `test_reasoning_effort.py`: effort table, probe for unknown models, drop on rejection.
- `stt_models.py`: the STT guard and the TODO for the live models.
- `speak_first.py` and `test_speak_first.py`: cancels the follow-up round after `record_engagement`.
- `prompt_profile.py` and `test_prompt_profile.py`: full vs compact. Rule-by-rule table for the content team: `docs/hackathon/latency/PROMPT-COMPACT.md`.
- `tts_warmup.py` and `test_tts_warmup.py`.
- `filler.py`, `test_filler.py`, `assets/fillers/` (seven clips `hum-01.ogg` to `hum-07.ogg`, `README.md`, `render_fillers.py`).
- `entrypoint.py` and `agent_class.py`: the wiring. `test_model_defaults.py`, `test_voice_wiring.py`.
- `.env.example`, `.env.production.example`: all switches, with comments.
- `docs/hackathon/latency/RESULTS.md` and `docs/hackathon/latency/transcripts/` (16 reply transcripts for the content team).
- `docs/hackathon/tasks/08-latency.md` (ticked, with a status section) and `docs/hackathon/CURRENT_STATE.md` (STT and LLM rows).

Commits: `10d9af0` latency line, `8f8ddc1` one model default, `f82f906` speak first, `0e60143` TTS warm-up, `a68720d` prompt profile, `8211c74` hum filler, `1bb66b8` REASONING_EFFORT and STT guard, `35709f9` docs, `a4c92a8` task file, `d56b0e4` and `a6d892a` and `3a88b62` review fixes, `7237382` results.

Outside git: the e2e kit and the A/B scripts (`ab_audio.py`, `ab_driver.py`, `ab_parse.py`, `ab_report.py`) in `%USERPROFILE%\Documents\Alsadiq-wt\e2e-voice`, raw run JSON in its `runs/ab/`, and two probe scripts in `%USERPROFILE%\Documents\Alsadiq-wt\08-latency-probe` (they read the key inside the script and never print it). A detached worktree `Alsadiq-wt\08-latency-base` (baseline code) can be removed with `git worktree remove`.

## 4. How to run, measure and flip the flags

Tests (from `backend/`, plain unittest, no Postgres needed):

```
python manage.py test conversation.agent --settings=config.settings_sqlite_test
```

Last result: 324 tests in `conversation.agent`, all pass. The full backend suite (575 tests) has 57 errors, all in `conversation.test_demo_guards`, which needs a Redis host named `redis` that does not resolve on this PC. They are not related to this work.

Stack run: copy a working `.env` into the repo root (it is gitignored; the one used came from `Alsadiq-wt\07-voice\.env`), then `docker compose up -d`. Between configs recreate only the agent: `docker compose up -d --no-deps --force-recreate livekit_agent`. Use `docker compose down` without `-v`.

Measure: one line per exchange in the agent log.

```
docker compose logs livekit_agent | grep turn_latency
```

Fields: `kind`, `language`, `eou_delay_s`, `stt_delay_s`, `llm_ttft_s`, `llm_rounds`, `tts_ttfb_s`, `total_s`, `reply_s`, `tool_called`, `tools`, `spoke`, and the labels `llm_model`, `stt_model`, `prompt_profile`, `reasoning_effort`. It never holds transcripts, reply text, tool arguments or ids. Browser-side numbers come from the e2e kit (`run_e2e.py`, "reply audio after question").

Flags (agent environment; set in the `.env`, then recreate `livekit_agent`):

| Flag | Values | Default | Notes |
|---|---|---|---|
| `LLM_MODEL` | `gpt-5.4-mini`, `gpt-5.6-luna`, `gpt-6-luna`, `gpt-5.2` (reference) | `gpt-5.4-mini` | No gpt-4.x |
| `REASONING_EFFORT` | auto, none, minimal, low, medium, high, xhigh, off | auto | auto picks the lowest the model accepts (none for the five tested models, from a table). off sends nothing |
| `STT_MODEL` | `gpt-4o-mini-transcribe`, `gpt-4o-transcribe`, `gpt-transcribe` | `gpt-4o-mini-transcribe` | live models are refused |
| `STT_REALTIME` | 1 or 0 | 1 | |
| `PROMPT_PROFILE` | full, compact | full | compact needs content approval first |
| `FILLER_MODE` | off, hum | hum | unknown value counts as off; `spoken` is a TODO and acts as off |
| `FILLER_PROBABILITY` | 0.0 to 1.0 | 0.5 | |
| `FILLER_DELAY_S` | seconds | 0.25 | wait in "thinking" before a hum |
| `FILLER_VOLUME` | 0.0 to 1.0 | 0.8 | |
| `LATENCY_LOG` | 1 or 0 | unset | the metrics switch: unset means on while `DEBUG=1`, off otherwise. Set 1 in production to measure |
| `TTS_WARMUP` | 1 or 0 | 1 | |

For a clean reply time set `FILLER_MODE=off` (the hum counts in the client first-sound number only).

## 5. Decisions

- Model rule from the lead (Abdulrahman, 4 Oct): no older model such as gpt-4. Candidates are `gpt-6-luna`, `gpt-5.6-luna`, `gpt-5.4-mini`, reference `gpt-5.2`. Default stays `gpt-5.4-mini`. No speed winner was found, so the final pick is for the content team (Arabic and persona) and cost.
- Default `REASONING_EFFORT=auto` now sends `none` to gpt-5.4-mini. Before this branch nothing was sent. Judge persona and Arabic quality in the content team's A/B.
- Known models do not get a test request. A live test request took 1.0 to 3.3 s and livekit runs every session in a fresh process, so it held up every greeting. Unknown models still get one tiny request (about 16 tokens) per session.
- Rejected or untestable effort values are logged and dropped, never a crash.
- `gpt-live-transcribe` and `gpt-realtime-whisper` are refused with one error and the default is used, so a typo never gives a dead microphone.
- Hum, not spoken filler. Words change what the child hears from the companion, so a spoken "let me think" is the content team's call.
- Compact prompt stays opt-in (default full) until the content team reads `PROMPT-COMPACT.md`. It drops no safety, scholarly or content rule. It is about 26 percent shorter (11,195 to 8,281 characters), a little under the 30 percent target on purpose.
- The Silero 0.55 s wait, interruptions, `AGENT_MIN/MAX_ENDPOINTING_DELAY` and `preemptive_generation` are untouched (kids rule; APPROACH.md step 0).
- No fallback to xAI. xAI was not measured.

## 6. The measured results

Live docker stacks, ElevenLabs voices, 16 measured sessions (cap 18). Medians over 8 reply turns (4 Arabic, 4 English), one session per language, synthetic child questions only. Seconds.

| run | server total | p90 | eou | ttft | ttfb | client first sound |
|---|---|---|---|---|---|---|
| baseline (demo-mvp code, dev .env) | 5.47 | 7.22 | 1.23 | 2.06 | 0.30 | 5.65 |
| after (hk/08-latency, defaults) | 5.29 | 5.91 | 1.23 | 1.53 | 0.29 | 4.95 |
| after, FILLER_MODE=off | 6.15 | 6.56 | 1.28 | 1.87 | 0.30 | 6.35 |

- Server total minus 3 percent, ttft minus 26 percent, client first sound minus 12 percent. The client gain comes only from the hum, which played on 2 of 8 turns.
- Why the bar is missed: 15 of 16 reply turns (baseline and after) made two LLM rounds, because the agent calls `get_islamic_reference` on almost every turn. Tool plus second round cost about 2.1 s. Breakdown (after): end of turn and STT about 1.2, first LLM round about 1.5, tool round about 2.1, TTS first byte about 0.3. Turns without a tool were 3.2 to 4.8 s.

A/B (filler off, effort none, server total median): gpt-5.4-mini 6.15, gpt-6-luna 6.18, gpt-5.6-luna 5.78, gpt-5.2 5.89. `gpt-transcribe` 6.22 with eou 1.50 vs 1.28 (about 0.2 s slower, transcripts exact). `PROMPT_PROFILE=compact` 6.33 vs 6.15, no gain. Median reply words: gpt-5.2 35, gpt-6-luna 31, gpt-5.4-mini 23. Gaps under about 1 s are noise at this sample size.

Effort check on the team key: gpt-5.4-mini, gpt-5.4-nano, gpt-5.2, gpt-5.6-luna and gpt-6-luna accept none and low and reject minimal with a 400. `gpt-transcribe` works through the plugin; the two live models do not.

Full tables, method and caveats: `docs/hackathon/latency/RESULTS.md`.

## 7. Known issues

- The 30 percent bar is not met (section 6).
- Speak first: if the model says only the short opener and then calls `record_engagement`, the cancelled round cuts the rest of the reply. Also, `record_engagement` comes at the end of the LLM output, so if the child cuts in before the LLM finishes, livekit never starts the call and no points are given for that reply. Watch for both in live runs.
- The effort probe still delays session start by about 1 to 3 s for models not in the table (for example gpt-6-sol).
- Hum clips use the voice from the team `.env` (`pCKbQ4EPGE06zpEPGNvS`), not the code default. If deploy uses another voice the hum will not match; render again with `render_fillers.py`. Check the ElevenLabs plan allows commercial use of the clips (licence note in the clips README).
- Stopping a hum clears a private livekit attribute (`BackgroundAudioPlayer._audio_source`). It is guarded and never raises, but recheck it on a livekit upgrade. A cut hum may click softly.
- `llm_ttft_s` in the latency line is sometimes null (an LLM metric that arrives before the reply starts thinking is dropped).
- `LATENCY_LOG` is off in production unless set.
- Arabic replies in the chat-bubble capture often lack final punctuation, also in baseline. Cause unknown; the content team should read the endings with care.
- The `Message` table showed 0 rows although the agent logged saves. Cause unknown; transcripts came from chat bubbles.
- Not done: the 10-turn live baseline per the original script (3 runs), a production-like baseline (gpt-5.2 and gpt-4o-transcribe), a tiny LLM warm-up request at connect, Caddy `encode` and cache headers, the final 30 percent check. DB reads were not made concurrent.
- Sample is small: 8 turns per cell, one session per language.

## 8. Next steps

1. Content team: read `PROMPT-COMPACT.md` and approve or reject the compact prompt. Confirm the "caring, never cheerful" opener wording. Decide the filler style (non-verbal hum as built, or a spoken mode). Judge the Arabic and persona of gpt-5.4-mini, gpt-5.6-luna and gpt-6-luna from `docs/hackathon/latency/transcripts/`, then pick the voice LLM.
2. Task 03 (source injection): this is the lever that moves the number. Injecting references in `on_user_turn_completed` (keep it under 10 ms) removes the tool round, worth about 2 s. A cheaper interim: call `get_islamic_reference` only for religious questions, or run it in parallel. The hook place is marked with a comment in `agent_class.py` (about line 229). After it lands, re-measure with 3 or more sessions per language per cell.
3. Optional Scribe trial (APPROACH.md step 10): pass `server_vad={"vad_silence_threshold_secs": 0.5}` in `stt_factory.py`, because without it the plugin never commits. Costs ElevenLabs credits, so it needs a yes. Also optional: the live OpenAI STT models via a small `SpeechStream` subclass (TODO in `stt_models.py`).
4. LiveKit upgrade after 6 Oct: move all packages together to 1.6.1 or later and try the audio turn detector (supports Arabic; kids accuracy unverified). Recheck the private hum attribute and the effort plugin behaviour then.
5. Caddy `encode zstd gzip` and cache headers for `/models/*` and `/audio/*` (task file item, `infra/caddy/Caddyfile`).
6. PR order relative to `hk/demo-mvp`: this branch only touches `backend/conversation/agent/`, the two env examples and docs. `hk/demo-mvp` has moved on (`cba290e`) and touched only `demo_guards.py`, `test_demo_guards.py` and `views.py` under `backend/conversation/`. A trial merge of `hk/demo-mvp` into this branch is clean, with no conflicts. So merge `hk/08-latency` into `hk/demo-mvp` once the content team has approved the defaults (or send it with `PROMPT_PROFILE=full`, which is already the default). Do it before task 03 starts, because both edit `agent_class.py`. Do not push without the lead's go.

## 9. Gotchas

- livekit 1.5.1 runs each session in a fresh process, so anything cached "per process" is really per session. Keep start-up work off the greeting's path.
- `BackgroundAudioPlayer`'s `stop()` alone does not stop a hum: about 400 ms of audio stays queued. The code clears the queue too.
- The `minimal` effort value is rejected by the new models (it is the old GPT-5 value). Do not set `REASONING_EFFORT=minimal` on them; it is logged and dropped, which means the model's own default thinking applies.
- The 1.5.1 plugin sends no effort on its own for gpt-5.4-mini, gpt-5.6-luna or gpt-6-luna, so `off` means they think at their own default.
- `gpt-live-transcribe` and `gpt-realtime-whisper` stream text while the child speaks but need a client-side commit the plugin never sends. They look fine in a set-up check and then produce no transcript.
- The Scribe path in `stt_factory.py` also never commits without `server_vad` (read from source, never run live).
- Never run the e2e kit or tests with real children's recordings: synthetic or consented clips only.
- A first agent start after 180 s idle can still pay the socket set-up (`WS_INACTIVITY_TIMEOUT` is 180 s in the plugin).
- When two stacks share ports, only one can run. The measurement run found the ports free; someone started a demo-mvp compose stack afterwards and it was not touched.
- Reasoning on the tool turns: nearly every test question was a values or prayer question, so this test set is a worst-ish case. Casual chat will be faster.
- Never print or commit the `.env`. Keys were never printed in any probe.
