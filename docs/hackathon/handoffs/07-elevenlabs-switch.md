# Handoff: ElevenLabs voice switch (task 07)

Date: 2026-10-04. Branch `hk/07-voice`, worktree `%USERPROFILE%\Documents\Alsadiq-wt\07-voice`. Local only, not pushed. Task file: `docs/hackathon/tasks/07-elevenlabs-voice.md`.

Read next to this file (not repeated here):
- `docs/hackathon/handoffs/07-voice-text-cleaner.md`: how the speech cleaner (`tts_text.py`) works.
- `docs/hackathon/handoffs/07-elevenlabs-facts.md`: source-checked facts on plugin 1.5.1, models and voices.

Update 2026-10-04 (no-fallback rule, section 10): the lead ruled that nothing may fall back to xAI by itself. Sections 1, 2, 4, 5, 6, 7 and 8 below are updated to match. Section 10 has the new behaviour, the contract for the frontend and the live test results.

Before that update no ElevenLabs key existed, and nothing had been run live. Sections 3 to 9 still describe the earlier mock-only work except where they say otherwise. Section 10 is the live-tested part.

## 1. What this is

- The voice agent used to speak through xAI Grok TTS (voice `leo`). It now speaks through ElevenLabs by default.
- There is NO automatic fallback to xAI. If ElevenLabs cannot be used, the session fails clearly (section 10). An operator can still choose xAI by hand with `TTS_PROVIDER=xai`. That switch never turns on by itself. The xAI client file `backend/conversation/agent/xai_tts_streaming.py` is untouched.
- An optional second switch tries ElevenLabs Scribe for speech-to-text. It is off by default.
- A cleaner runs on the text just before it is spoken. It spells numbers as words and never speaks Quran verses.
- Two helper scripts let humans audition voices and compare speech-to-text engines once keys arrive.

## 2. What was built and why

| Piece | Why |
|---|---|
| `livekit-plugins-elevenlabs==1.5.1` and `openai>=2,<3` in `backend/requirements.agent.txt` | The plugin must match `livekit-agents==1.5.1`; do not upgrade the framework mid-hackathon. openai 3.x dropped httpx, which livekit-agents 1.5.1 still imports, so the agent would not start. |
| `backend/conversation/agent/tts_factory.py` | `build_tts(lang, ...)` picks ElevenLabs, or xAI only when `TTS_PROVIDER=xai`. A missing or placeholder `ELEVEN_API_KEY`, a missing plugin or a build error raises `VoiceConfigurationError` with one error log. It never builds xAI. |
| `backend/conversation/agent/stt_factory.py` | `build_stt(...)` returns the old OpenAI STT unless `STT_PROVIDER=scribe`. Scribe without a usable key fails clearly; it does not switch to OpenAI. |
| `backend/conversation/agent/entrypoint.py` | Builds the agent first, then the voices (a configuration error publishes `voice_error` and ends the job), then the `AgentSession` with the cleaner and aligned transcripts off. Also handles TTS errors raised during the session. |
| `backend/conversation/agent/agent_class.py` | New live `language` property for the cleaner. New `transcription_node` (strips markdown and emoji from the chat). The old `tts_node` override is gone. `get_islamic_reference` now wraps Quran text in ornate brackets. |
| `backend/conversation/agent/tts_text.py` | `speech_tts_text_transform(...)`, the per-session cleaner entry. The Quran guard keeps its state per speech, not per session. |
| `scripts/voice/audition.py`, `stt_compare.py`, `_common.py` | Listening and comparison tools (section 4). |
| `.env.example`, `.env.production.example` | The new env names with comments. No real keys. |
| Tests: `conversation/test_voice_factories.py`, `conversation/agent/test_tts_text.py`, `conversation/agent/test_voice_wiring.py` | Factories with mocked plugin classes; the cleaner; wiring against the real livekit code. |

Why the cleaner runs for both providers: `eleven_flash_v2_5` does not normalise numbers and cannot say honorific ligatures, and the manual xAI switch has the same product rule (no verse is ever synthesised).

## 3. Where it lives

Commits on `hk/07-voice` since `origin/hackathon` (`git log origin/hackathon..hk/07-voice`), newest first:

```
c5fea9d fix(voice): bracket bank Quran text so the TTS guard can see it
e3f11ba feat(voice): wire the speech cleaner into the agent and keep the original transcript
547e103 Merge hk/07-voice-text into hk/07-voice
210f70d fix(voice): keep exact transcript text and harden key handling
c68d460 docs(handoff): task 07 voice text cleaner and ElevenLabs fact-check
56d7231 feat(voice): add TTS text cleaner with Quran bracket guard
63ed2f3 feat(voice): audition and STT comparison tools, tick task 07 items
b2b5448 feat(voice): ElevenLabs TTS and optional Scribe STT behind env switches
605da56 feat(voice): add livekit-plugins-elevenlabs 1.5.1 and keep openai on 2.x
```

Files outside git, in `%USERPROFILE%\Documents\Alsadiq-wt\`:
- `07-voice\.env`: the real env file, gitignored (`.gitignore` line 154). Never print or commit it.
- `livekit-win\compose.livekit-win.yml` and `livekit-win\livekit.yaml`: the Windows LiveKit port override. Details in `HANDOFF-local-run.md` in the same folder.
- `env-names.py`: prints `.env` names only, never values.
- `eleven-key.txt`: optional key file for the two scripts only. It does not exist yet.
- `audition-out\`: default output folder of the audition script.

## 4. How to run, test and verify

### Env switches

All are read from `.env`. After a change, recreate the agent container: `docker compose up -d livekit_agent`.

| Variable | Values and default | Effect |
|---|---|---|
| `TTS_PROVIDER` | `elevenlabs` (default) or `xai` | Which voice speaks. `xai` is a manual operator choice. Unknown value: warning, uses `elevenlabs`, never xAI. |
| `STT_PROVIDER` | `openai` (default) or `scribe` | Which engine hears the child. `scribe` without a usable key fails clearly, no OpenAI fallback. |
| `STT_SCRIBE_MODEL` | `scribe_v2_realtime` (default) | Only with `scribe`. |
| `ELEVEN_API_KEY` | key | Blank, or a value starting `your-`, `<`, `changeme`, counts as missing. |
| `ELEVEN_VOICE_ID_AR`, `ELEVEN_VOICE_ID_EN` | voice IDs | Blank means Habibah `w4LX7bK479eHGM1k15Em` for both. The `.env` on Majd's PC has both set (checked by name only). |
| `ELEVEN_MODEL` | `eleven_flash_v2_5` (default), `eleven_multilingual_v2` | `eleven_v4_turbo` is refused with a warning (plugin 1.5.1 cannot stream it). |
| `ELEVEN_STABILITY`, `ELEVEN_SIMILARITY`, `ELEVEN_STYLE`, `ELEVEN_SPEAKER_BOOST`, `ELEVEN_SPEED` | defaults 0.65, 0.75, 0.0, on, 0.92 | Calm storyteller settings. Speed range 0.7 to 1.2. |
| `ELEVEN_TEXT_NORMALIZATION` | `auto` (default), `on`, `off` | `on` with flash may be refused by the API. |
| `ELEVEN_LANGUAGE_HINT` | `on` (default) or `off` | `on` sends the session language (`ar` or `en`) to flash models. Set `off` if an English reply in an Arabic session sounds wrong. |
| `ELEVEN_ALIGNMENT` | `original` (default), `normalized` | Only used if aligned transcripts are ever turned on (they are off). |
| `XAI_API_KEY`, `XAI_TTS_VOICE`, `XAI_TTS_LANGUAGE`, `ARABIC_TTS_LOCALE` | as before | Used only by the manual `TTS_PROVIDER=xai` switch. |
| `ELEVEN_KEY_FILE` | path | Scripts only. Overrides `eleven-key.txt`. |

### Audition (needs the ElevenLabs key)

1. Put the key in `%USERPROFILE%\Documents\Alsadiq-wt\eleven-key.txt` (one line), or set `ELEVEN_API_KEY` in the shell. The script never prints it.
2. From the `07-voice` folder:
   - Plan only, no API call (works now): `python scripts/voice/audition.py --dry-run`
   - Full run: `python scripts/voice/audition.py`
   - Cheaper: `python scripts/voice/audition.py --voices habibah,asmaa --models eleven_flash_v2_5 --lines ar:1-3,en:1`
3. Open `%USERPROFILE%\Documents\Alsadiq-wt\audition-out\index.html` and listen across each row. `results.csv` has time to first byte per request.
4. The script checks the account first (`/v1/voices`, `/v1/user/subscription`) and refuses a run bigger than the remaining quota unless `--force`. Use `--max-chars N` for your own cap.
5. Record the pick (voice ID, model, settings) in the brain `Decisions log`, then put the IDs in `.env`.

Checked on 2026-10-04: the dry run prints 15 lines (10 Arabic, 5 English), 4 voices, 2 models, 120 requests, 9,480 characters billed.

### Live session (needs `OPENAI_API_KEY` and `ELEVEN_API_KEY`)

1. Fill the keys in `%USERPROFILE%\Documents\Alsadiq-wt\07-voice\.env`. Check with `python %USERPROFILE%\Documents\Alsadiq-wt\env-names.py` (names only; the three keys show EMPTY today).
2. In `%USERPROFILE%\Documents\Alsadiq-wt\07-voice` run `docker compose --profile all up --build`. On Majd's PC `.env` has `COMPOSE_FILE=docker-compose.yml;../livekit-win/compose.livekit-win.yml`, so the `livekit-win` override loads on its own. It must run from this folder.
3. Open http://localhost:5173, sign up as a parent, add a child, start a voice session. Watch the agent logs on the first run (`docker compose logs -f livekit_agent`).
4. Test Arabic, then English. In the Arabic session also type one English message and listen to how it is read.
5. Check the chat shows the text with digits as digits, and a reload shows the same text (that is the DB copy).
6. Manual switch check (optional): set `TTS_PROVIDER=xai` in `.env` (needs `XAI_API_KEY`), run `docker compose up -d livekit_agent`, talk again. The log says the operator chose it. Set it back to `elevenlabs` afterwards. xAI never starts on its own.
7. Because `./backend` is bind-mounted into the agent container, code edits need only a restart. A change to `requirements.agent.txt` needs `--build`.

### Tests

- Backend suite without Postgres: `cd backend && python manage.py test --settings=config.settings_sqlite_test`.
- Reported by the integrator and reviewer: 251 tests OK at `c5fea9d`, run in a temporary venv with livekit-agents 1.5.1 and plugin 1.5.1 (PyAV stubbed or real). The class `RealLivekitTests` in `test_voice_wiring.py` runs only when livekit is importable; elsewhere it is skipped.
- I did not re-run the suite for this handoff: the system Python on this PC has no Django. Claims were checked by reading the code and diff, and by running the audition dry run.
- Quick check without keys: `python scripts/voice/audition.py --dry-run`.

### STT comparison (optional, needs both keys)

`python scripts/voice/stt_compare.py CLIPS_DIR --dry-run`, then without `--dry-run`. Clips must be synthetic, or consented and anonymised. Never use real children's recordings from the live app. Put `NAME.txt` next to a clip for word error rate. Switch to Scribe (`STT_PROVIDER=scribe`) only if it is clearly better.

## 5. Decisions and why

1. **Aligned transcripts are OFF** (`_USE_TTS_ALIGNED_TRANSCRIPT = False` in `entrypoint.py`). Checked in livekit-agents 1.5.1 (`agent_activity.py` about lines 1984 to 2004, `generation.py` about 225 to 265): the LLM text goes down two paths. One goes through `tts_text_transforms` and `tts_node` to the voice. The other feeds `transcription_node`, which is what the chat and DB show. With aligned transcripts on, the second path is replaced by the TTS's timed words, so digits would show as words and a quoted verse as the neutral phrase.
   - Result: the chat and DB keep the LLM's original text. Only the audio is cleaned.
   - Cost: captions are paced by livekit's speaking-rate estimate, not exact ElevenLabs word times. Word-synced captions are lost. `sync_alignment` is false, so ElevenLabs no longer sends word timings (safe in plugin 1.5.1: audio and the final flag do not depend on them).
2. **The cleaner is a session `tts_text_transforms` entry** for both ElevenLabs and xAI. It replaces livekit's default markdown and emoji filters, because it does both. `AlSadiqAgent.transcription_node` strips markdown and emoji from the chat copy.
3. **Quran guard state is per speech task**, not per session. livekit runs all segments of one speech in one task, so a verse split across segments stays suppressed. An interrupted reply, or a preemptive reply that is discarded inside a bracket, cannot swallow the next reply.
4. **The cleaner reads the live session language** (`agent.language`), so the agent is built before `AgentSession`.
5. **Bank Quran text is bracketed.** The guard detects verses only by the ornate brackets, and the bank stores verses without them. `get_islamic_reference` now adds the brackets (removing any already there) and tells the LLM to keep them. A quoted bank verse shows in the chat but is replaced in speech by the neutral phrase. Hadith text is unchanged.
6. **Streaming path only.** The plugin's WebSocket `stream()` is the only path that honours language, normalisation and dictionaries.
7. **Default model `eleven_flash_v2_5`.** Cheapest per character and lowest latency. `eleven_multilingual_v2` is the quality fallback at double the credits.
8. **Original text for alignment** (`ELEVEN_ALIGNMENT=original`) in case aligned transcripts are ever enabled, so ElevenLabs does not put its rewritten text in the chat.
9. **Placeholder keys count as missing**, so a copied `.env.example` fails at session start with a clear error instead of failing mid-call.
10. **No fallback of any kind, no `FallbackAdapter`** (lead's rule, 2026-10-04). ElevenLabs is the voice. If it cannot be used the session reports it. See section 10.

## 6. Current status

- Code: done and committed on `hk/07-voice`. Worktree clean at `c5fea9d`. Not pushed. No PR yet.
- Docker is installed and the images built earlier (see `HANDOFF-local-run.md` section 10). Those images were built before the wiring commits, so rebuild with `docker compose --profile all up --build`.
- Keys: `OPENAI_API_KEY`, `ELEVEN_API_KEY` and `XAI_API_KEY` are all empty in `07-voice\.env`. With no ElevenLabs key a voice session ends with a `voice_error`. (This line was written before the keys arrived; see section 10 for the live result.)
- Task file `docs/hackathon/tasks/07-elevenlabs-voice.md`: pin, factory, wiring and env docs ticked. Still open: the audition and `Decisions log` entry, the STT comparison, the live Arabic and English sessions in the app, and time-to-first-byte logging (task 08 owns it).
- Brain notes for this work were not written by the agents (their rules forbade it). The main session should post the handoff note and the decision line.

## 7. Known issues

1. **No fallback, by decision.** If ElevenLabs rejects the key, voice ID, plan or quota, or cannot be reached, the agent logs one error with the cause, publishes `voice_error` and ends the session (section 10). It does not speak with another voice. The frontend does not show the `voice_error` message yet.
2. **Placeholder voice IDs.** Habibah is the default for both Arabic and English, so English sessions read with an Arabic voice until `ELEVEN_VOICE_ID_EN` is set. The four candidate IDs come from a third-party directory and are unverified. They are Voice Library voices: add each to My Voices on the account, and note a free plan may block them through the API. A paid plan is needed if that happens.
3. **PyAV is blocked on this PC.** Windows Application Control blocks the PyAV DLL, so `livekit.agents` cannot be imported with the system Python here. Earlier checks stubbed `av` in a temporary venv. Docker (Linux) or another machine must confirm the agent starts with the real plugin.
4. **Scribe keyterms do nothing on the realtime model.** Plugin 1.5.1 sends keyterms only on batch models (`scribe_v1`, `scribe_v2`), not `scribe_v2_realtime`. Fixing it needs plugin 1.8.x (which forces a livekit-agents upgrade) or a custom STT subclass. `stt_compare.py` uses the batch endpoint, so it tests keyterms, but the live agent would not get them.
5. **Captions are estimate-paced.** A bracketed verse in the chat will scroll quickly while only the short phrase is spoken. Check how it looks in the live UI.
6. **English reply in an Arabic session.** Nothing changes the session language mid-session, so the cleaner reads digits in the session language. If `ELEVEN_LANGUAGE_HINT=off` is chosen after the live test, switch the cleaner to per-text language detection with the session language as the fallback.
7. **Verses are detected only by brackets.** A verse that reaches the LLM text without brackets from somewhere else is spoken. Tasks 03 and 05 own verse delivery and the recitation audio. Until then the neutral phrase plays with no recitation after it.
8. **Unverified live:** the voice quality, Arabic with the settings, time to first byte, the chat and DB text in the real UI, and the full path in the real UI and a real room (the factory was tested live against the ElevenLabs API, section 10).
9. **Older lint.** About thirteen ruff findings remain in older agent files (for example a blind `except` near `entrypoint.py` line 134). They were there before this work and were left alone.
10. **Phone on the LAN does not work** with the local LiveKit setup (`HANDOFF-local-run.md` section 7).

## 8. Next steps and improvements, ordered by value

1. Get `ELEVEN_API_KEY` (and `OPENAI_API_KEY`) from Abdulrahman. Everything else waits on this.
2. Add the voices to My Voices, then run the audition (section 4). Team listens, picks voice and model. Log the pick in `Decisions log`. Set `ELEVEN_VOICE_ID_AR` and `ELEVEN_VOICE_ID_EN` (an English voice distinct from the Arabic one if the Arabic voice sounds off in English).
3. Run the live Arabic and English sessions and the English-in-Arabic test in the app. Optionally try the manual `TTS_PROVIDER=xai` switch. Tick the task file items.
4. Rebuild the agent image on a normal machine or in Docker and confirm it starts with the real plugin (PyAV issue).
5. Frontend: listen for the `voice_error` data topic and show a friendly "voice unavailable" message (section 10). No `FallbackAdapter`: the lead ruled out any automatic fallback.
6. Open the PR `hk/07-voice` into `hackathon` when Majd says so.
7. Log TTS time to first byte from `metrics_collected` (task 08), and record it for the demo.
8. Tune settings by ear (stability, speed). Try `eleven_multilingual_v2` only if flash sounds thin in Arabic.
9. Optional: STT comparison on 15 synthetic Arabic clips. Switch to Scribe only if clearly better; then solve keyterms (plugin 1.8.x or a custom STT class).
10. Optional: if captions feel off, revisit aligned transcripts with a transcript path that keeps the original text (needs livekit work).
11. Update task 10 docs and the deck: replace xAI with ElevenLabs (Inbox item in the task file).

## 9. Gotchas

- **Credit budget.** The account is reported to have about 64k credits (Abdulrahman's; not checkable from code, the audition script prints the real number when it runs). Flash costs half the credits per character of `eleven_multilingual_v2` (fact sheet, `07-elevenlabs-facts.md`).
  - Full audition: 9,480 characters per the script. At those rates that is about 2.4k credits on flash plus 4.7k on multilingual, roughly 7k. The earlier estimate was about 6k. Narrow it with `--voices`, `--models`, `--lines` to save credits.
  - A 5-minute live session: about 1.5k credits (estimate from the brief).
  - To save credits while building UI or prompts, an operator may set `TTS_PROVIDER=xai` by hand. Use ElevenLabs for listening tests and the demo.
- Never print, paste or commit `.env`. Use `env-names.py` to check it.
- The two scripts read `eleven-key.txt`. The live agent does not: it reads `ELEVEN_API_KEY` from `.env` only.
- `docker compose` must run from `%USERPROFILE%\Documents\Alsadiq-wt\07-voice`. Another folder breaks the `livekit-win` override path. The override is PC-only and not in git.
- Changing `.env` needs `docker compose up -d livekit_agent`. A plain restart may not pick it up.
- Do not add `eleven_v4_turbo`: plugin 1.5.1 cannot use it on the streaming socket, and it is replaced by the default with a warning. `eleven_v3` is untested.
- Do not upgrade `livekit-agents` or the plugin mid-hackathon, and keep `openai` below 3.
- Do not turn aligned transcripts on without reading decision 1: the chat and DB would lose digits and quoted verses.
- No scripture in code, tests, data or audition lines. The audition citation lines only name a book. Tests use placeholder words.
- Never click `mailto:` or `tel:` links when click-testing the web app (Windows "Pick an app" popups). Use Playwright with channel `msedge`.
- Never `git init` or zip-import a copy of this repo: `.gitignore` protects `.env`, and exports can drop it.
- Key scan done at `c5fea9d`: no provider key patterns in tracked files or history of this worktree. The only env files ever committed are the two `.example` files with placeholders. This covered the local copy, not GitHub itself.

## 10. No fallback to xAI (lead's rule, 2026-10-04)

The rule: ElevenLabs is the voice. If it cannot be used, fail clearly. Never speak with another voice by itself.

What happens now:

| Situation | Result |
|---|---|
| `ELEVEN_API_KEY` missing, blank or a placeholder | `build_tts` raises `VoiceConfigurationError` (code `missing_key`) and logs one error. |
| Plugin not installed | Same error, code `plugin_unavailable`. |
| Plugin fails to build | Same error, code `build_failed`. The message names the exception, never the key. |
| `STT_PROVIDER=scribe` and the same problems | Same errors from `stt_factory`. It does not switch to OpenAI. |
| Key, voice or plan rejected, or ElevenLabs unreachable, after the session started | The session error handler logs one error naming the cause (`key_rejected`, `voice_rejected`, `quota_or_plan`, `unreachable`, or `failed`) and says "No fallback voice is used". It then ends the session once. |
| `TTS_PROVIDER=xai` set by an operator | xAI speaks. One warning says the operator chose it. This is the only path to xAI. |
| `TTS_PROVIDER` has an unknown value | Warning, then ElevenLabs. Never xAI. |

In the first three rows and in the session error row the entrypoint also publishes a data message to the room, so the app can tell the child the voice is not available. Contract for the frontend (not built yet; the frontend only listens for the `gamification` topic today):

- Topic: `voice_error`. Reliable delivery.
- Payload (JSON): `{"type": "voice_unavailable", "provider": "elevenlabs", "code": "<missing_key | plugin_unavailable | build_failed | key_rejected | voice_rejected | quota_or_plan | unreachable | failed>"}`.
- Then the agent job ends, so the room has no agent. Show a short friendly message and offer to try again later. Do not show the code to a child.

Why the real cause is read from the plugin log: the ElevenLabs WebSocket accepts the connection even with a bad key or voice. The API sends an error message, the plugin logs it ("elevenlabs tts returned error") and closes the socket, so livekit only sees a generic "connection closed". `tts_factory.install_api_error_capture()` keeps the last such message (key redacted) so the cause can be named.

Live test, 2026-10-04, real ElevenLabs API, plugin 1.5.1 inside the agent image, through `build_tts` (outside a job, so the check script gives the plugin its own http session):
- Real key, Arabic line: audio returned, first audio about 0.5 to 1.7 s across runs.
- Real key, English line: audio returned, same range.
- Wrong key: reported as `key_rejected`. Nothing spoke.
- Wrong voice id: reported as `voice_rejected`. Nothing spoke.
- Not run: a full room with the browser. The wiring is covered by `NoFallbackVoiceTests` in `test_voice_wiring.py` (fake session, real handlers).

Tests: `TtsNoFallbackTests` and `TtsRuntimeFailureTests` in `conversation/test_voice_factories.py`, `NoFallbackVoiceTests` in `conversation/agent/test_voice_wiring.py`. They check that a missing or placeholder key, a build error and a missing plugin each raise with xAI never built, that the key never appears in an error or log, and that the only path to xAI in the source is the explicit switch. Full backend suite in the agent image with sqlite settings: 273 tests OK, 3 skipped.
