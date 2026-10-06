# Handoff: Demo MVP integration (branch hk/demo-mvp)

Written 2026-10-04, phase 2b section added the same day. Worktree `%USERPROFILE%\Documents\Alsadiq-wt\demo-mvp`. Not pushed, no PR, nothing deployed.
The numbers below come from runs made in this worktree on the final merge result unless marked otherwise.

## Phase 2b (2026-10-04): landing, voice states, e2e

This is the newest section. Sections 1 to 9 below were written earlier the same day, so where they say "not in this branch" or "not done", read this section first. The branch is `hk/demo-mvp`, worktree `%USERPROFILE%\Documents\Alsadiq-wt\demo-mvp`. Nothing is pushed, no PR is open, nothing is deployed, and Majd's main clone was never touched.

### What is in the branch now

Merge order, all normal merge commits:

1. 07 voice, 06 avatar, 06b forest, glue, demo-guards, demo-walkin (phase 1, sections 2 and 3).
2. `hk/10-demo` (fbd74df): one-click demo login. `POST /api/demo/start` leases one of 8 synthetic Arabic families for 45 minutes. `seed_demo` creates them, `demo_reset_expired` frees expired leases. Handoff: `10-demo-login.md`.
3. `hk/10-prod-hardening` (c4da006): safe `seed_admin`, `/admin` blocked at Caddy unless the IP is in `ADMIN_ALLOWED_IPS`, health check, env template. Conflicts in `docker-compose.prod.yml` and `frontend/Dockerfile`, resolved by keeping both sides (the agent keeps `REDIS_HOST=redis` and also gets `DEBUG` and `AGENT_NUM_IDLE_PROCESSES`; the frontend build args are `VITE_FOREST_SCENE` and `VITE_DEMO_MODE`, default 0, only the string `1` is on; the busybox stage copies the build into the volume at every start). Handoff: `10-prod-hardening.md`.
4. `hk/10-submission` (586ec5d): the submission pack in `docs/hackathon/submission/` (checklist, judge script, deck outline, video storyboard, disclosure, sources register, judging map). Handoff: `10-submission-pack.md`. Note: JUDGE-DEMO-SCRIPT and DECK-OUTLINE still describe the landing as meadow only. Only CHECKLIST item F7 was updated.
5. Live forest hero (6fc60f8): the landing shows the live forest with the avatar and its walk-in. The parent copy is fixed in Arabic and English. `VITE_DEMO_MODE=1` now turns the forest on by default (`forestFlag.js`); `?forest=0` still turns it off.
6. `hk/demo-voiceui` (c2b6231, builder 0bacbd0 plus reviewer f2bbc05): the child voice screen now handles every guard signal, in Arabic and English. Text mode, daily_limit, rate_limited with a Retry-After countdown, voice_off, busy (503) with a text chat button, voice_error ("Sadiq's voice is resting" with a text retry), the clock chip, the one-minute note, the goodbye and the end card (with "start over" in demo mode). A child-requested `text_only` start option was added. It never turns a voice on, and the kill switch and daily cap still apply. Backend fixes inside this branch: `settings.py` now edits `CACHES['default']` and no longer replaces the whole dict (that had dropped the `guards` cache), and `CORS_EXPOSE_HEADERS = ['Retry-After']` is set. Review also fixed: status cards covering the avatar on desktop, the flipped send icon in RTL, repeated card titles, Arabic wording, dialog focus, and the language pill (the chosen language is now saved to the profile before a start, so Sadiq speaks it). Handoff: `docs/hackathon/demo-guards.md` has the contract.
7. `hk/demo-landing` (cba290e, builder 50b3e34 to d917558 plus reviewer 2baf3f9 and 17618ce): the MOLI-level landing, built from ideas only (MOLI is CC BY-NC, nothing copied). An arched window into the live forest, a page whose wall, text and cards follow the time of day (morning, noon, Maghrib, night), a greeting per time of day shown word by word above Sadiq's head, tappable lantern, book (six values in plain words, no scripture) and bulbul, pointer parallax and phone tilt, a language switch that glides, petals and fireflies, an opt-in sound pill (procedural WebAudio, off by default), an arch swell and veil into the child screen, a sticky mini button on phones, and a restyled judges card. It also adds `ChildIdleStage`, the Arabic and English child idle screen in the same forest world. The two 43 MB GLB files were deleted (`avatar-web.glb` is the shipped model; restore from 6fc60f8 if wanted). Reviewer fix that mattered most: the tap targets of the props had been projected to the wrong place, so tapping the book or the bird did nothing. Handoff: `demo-landing.md`.
8. Conflict between 6 and 7 in `frontend/src/pages/child/ConversationPage.jsx`, resolved so both stay. The voice-screen states are kept as they were. Idle and starting use `ChildIdleStage`, which now takes the page's `lang` and a small language pill. The landing's separate "voiceoff" state was dropped, because a text-mode start goes straight to the text chat with its notice. Refused, error and ended cards are drawn over the same forest stage, so there is no second walk-in. See the integration section at the end of this file.

The lead's rule holds everywhere: ElevenLabs, or a clear failure (`voice_error`), or text only. There is no xAI path that switches on by itself. xAI runs only when an operator sets `TTS_PROVIDER=xai` or `voice_mode xai` by hand.

### End-to-end voice result

PASS, on the real stack, branch `hk/demo-mvp`, voice Abdullah (ElevenLabs), headless Edge with a fake mic fed a recorded question. Kit: `%USERPROFILE%\Documents\Alsadiq-wt\e2e-voice` (`python run_e2e.py`; notes in its `HANDOFF.md`).

| Run | Language | Join | Child text heard | Reply audio | Log says | First audio from TTS | Result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 20261004-184201 | Arabic | pass | pass | pass | elevenlabs | 257 ms | PASS |
| 20261004-183940 | English | pass | pass | pass | elevenlabs | 264 ms | PASS |
| 20261004-184526 | English, fresh signup accounts | pass | pass | pass | elevenlabs | 277 ms | PASS |

- The xAI rollback case was skipped on purpose (the lead's rule).
- Agent log: provider `elevenlabs` in every run, no xAI marker, 0 agent errors, 0 `voice_error`. The remote audio track carried real audio.
- Latency: greeting audio heard 5.0 s (Arabic) and 5.5 s (English) after clicking start. From the end of the child's question to reply audio: 6.2 s (Arabic) and 7.0 s (English). TTS is not the slow part (about 260 ms). The time goes to end-of-utterance wait (about 1.4 s), speech to text, and the first model token (1.3 to 2.0 s).
- Cost of 3 sessions: about 760 ElevenLabs characters and about 8 US cents of OpenAI (kit placeholder prices).
- Reports: `e2e-voice\runs\20261004-184201\report.html` (Arabic), `...183940\report.html` (English), `...184526\report.html` (English repeat), each with `report.json` and screenshots.
- The kit was updated for the new child screen (start button `button.demo-talk`, per-language end and chat labels). No pass check was weakened. Its dry run passes (31 checks, 40 unit tests).

### Current status

- Everything above is merged on `hk/demo-mvp` and tested together: 426 backend tests OK (3 skipped, sqlite settings), `npx eslint src` clean, `VITE_DEMO_MODE=1 npm run build` passes (only the old chunk-size warning; main JS about 279 kB gzip, 3D chunk about 23 kB gzip plus the lazy forest chunk).
- Full local stack with `DEMO_MODE=1` and `VITE_DEMO_MODE=1` in Edge at 390x844: landing, walk-in, the try button leading to `/child` with the forest and no `?forest=1`, Arabic and English idle, a real voice session, the end key back to idle, the parent view. Mocked in Edge: daily_limit and 500 cards.
- Not pushed, no PR, nothing deployed. The test stack is down (no `-v`).
- Not tested: a real phone, the live site, and a real GPU on a phone. Frame rate was measured on the desktop GPU (about 62 fps, 18 to 30 draw calls).
- The `.env` in this worktree is gitignored and has `DEMO_MODE=1` and `VITE_DEMO_MODE=1`.

### Known issues (newest first, the old list in section 7 still applies except items 1, 7 and 10)

Section 7 item 1 (frontend ignoring the guard messages) is fixed by demo-voiceui. Item 7 (English voice) is only fixed locally (see the env table). Item 10 is partly fixed (the two GLBs are gone; `avatar/README.md` still names `avatar.glb`).

1. Demo leases run out. After two demo-login runs back to back, a third got 503 `demo_busy`. Visitors will see this when all 8 families are leased (lease 45 minutes). Raise `DEMO_POOL_SIZE` or lower `DEMO_LEASE_SECONDS` if judges come in a crowd, and make sure the `demo_reset_expired` cron runs.
2. Latency is about 6 to 7 s from the end of the child's question to the first reply audio (see above). The easiest gain is the end-of-utterance wait. The `hk/08-latency` branch is looking at it and is not merged here.
3. Sadiq opens with "wa alaykum assalam" even when the child has not said anything. That comes from the agent prompt, not from the screen. Fix it in the prompt.
4. The English demo switches the profile to English, but the seeded Arabic family can still get an Arabic first greeting (the agent's memory or prompt wins).
5. `voice_error` takes about 11 s to appear (ElevenLabs retries first), with silence until then. A `voice_error` session and a text restart each use a daily slot. Demo "start over" does not reset the per-child daily counter.
6. The agent closes the room right after it sends `session_ended`, so that message can be lost. The client treats a closed room during the ending phase as the end. An optional short sleep before `close_room` in `backend/conversation/agent/demo_limits.py` would make it cleaner.
7. If the agent never joins (worker down), the child hears silence until the clock end plus 40 s, then gets the goodbye card. With the guards off it never ends.
8. Switching to the parent view during a live session ends it with the parent token (403 on `/sessions/<id>/end/`, harmless, one console error). The session runs on until the agent's limit, so the daily slot stays used.
9. On a 390x844 phone the refused, error and end cards cover most of Sadiq (only the head shows). Accepted, but a layout tweak would help.
10. In the no-WebGL fallback there is no character, but the hint still says to tap Sadiq. On phones at night the greeting bubble can hide the bulbul for its 4.5 s hold. Morning and noon scenes look alike. With `?forest=0` the child screen is a plain green background (judges never see this).
11. The Arabic bottom nav is still English, and digits are mixed (Arabic-Indic in the clock, Western in bubble times and the level percent). Both were left on purpose.
12. The walk-in is judged on the dev GPU only. The forest chunk is large (about 255 kB gzip) and loads lazily after idle. The CTA's swell and veil start only after `/api/demo/start` returns, so a slow API shows only the loading shimmer until then.
13. `ChildIdleStage` still has the unused `voiceoff` and `onType` code. It can be removed or kept for a later text-from-idle flow.
14. In production the frontend origin must be same-origin or in `CORS_ALLOWED_ORIGINS`, and `Retry-After` must stay in `CORS_EXPOSE_HEADERS`, or the rate_limited countdown falls back to 30 s.
15. The only ElevenLabs failure tested for real was a rejected key. The codes `quota_or_plan`, `unreachable` and `voice_rejected` share the same card but were not triggered for real.
16. Agent text can still be scripture adjacent in English ("beloved to Allah"). Not a defect of this build, but the content owner should read a few transcripts before the demo.
17. Reduced motion shows a faint extra ring around the scene window (cosmetic). The Vite dev server in docker does not pick up edits on the Windows bind mount (restart the frontend container; local testing only).
18. Left in local volumes (outside the repo): demo families leased by test runs and test children in `demo-mvp_db`. `docker compose down -v` from this worktree gives a clean database. Helper scripts are in `%USERPROFILE%\Documents\Alsadiq-wt\` (`demo-mvp-integ.py`, `demo-mvp-integ2.py`, and others).

### Next steps, in order

1. Majd reads this and says yes to opening PRs. Nothing is pushed until then.
2. PR order into `hackathon`. Preferred: 07 (`hk/07-voice`), then 06 (`hk/06-avatar`), then 06b (`hk/06b-forest`), then `hk/demo-mvp`. After the first three, the demo-mvp diff shows only the glue, guards, demo login, hardening, submission pack, voice states and landing. Alternative if the lead prefers one PR: open only `hk/demo-mvp` into `hackathon`, with this file as the description. Either way the lead merges, and nobody pushes the production branch. Re-run tests, lint and build after each merge.
3. The lead's server checklist (full text in `docs/production-hardening.md` and `10-prod-hardening.md`):
   1. Set the env vars in the table at the end of this file. The key ones are `DEBUG=0`, `DEMO_MODE=1`, `VITE_DEMO_MODE=1`, `REDIS_HOST=redis`, `TTS_PROVIDER=elevenlabs`, `ELEVEN_API_KEY`, `ELEVEN_VOICE_ID_AR`, `ELEVEN_VOICE_ID_EN`, `ELEVEN_DAILY_CHAR_CAP` (from the real credits), `ADMIN_ALLOWED_IPS` (spaces, no commas, no placeholder, or the site will not load), `DJANGO_SUPERUSER_PASSWORD`, and the hosts, CORS and CSRF origins. Rebuild the frontend after changing any `VITE_` value.
   2. Run `seed_demo` once, in the `backend` container: `docker compose -f docker-compose.prod.yml exec backend python manage.py seed_demo`. CI does not do this. It wipes and re-seeds all 8 families, so never run it during judging.
   3. Add the cron on the host, every 5 minutes: `*/5 * * * * cd /opt/alsadiq && docker compose -f docker-compose.prod.yml exec -T backend python manage.py demo_reset_expired`. Run it in `backend`, not `livekit_agent`.
   4. Recreate Caddy so it loads the new Caddyfile. Validate first (`run --rm --no-deps caddy caddy validate ...` must end with `Valid configuration`), then `up -d --no-deps --force-recreate caddy`. Check that `/admin/` gives 404 from outside the allowlist and `/api/health/` gives 200. Until Caddy is recreated, `/admin` stays open.
   5. Rotate the admin password with `docker compose -f docker-compose.prod.yml run --rm backend python manage.py changepassword <admin-username>`. `seed_admin` skips an admin that already exists, so changing the env var alone does nothing.
   6. Delete the old test accounts on the server: parent `codexParent505209` and child `codexChild505209` (their old password is in git history).
   7. Check the kill switch and budget with `manage.py voice_mode` and leave it on auto.
4. Real phone test with the live site: frame rate, the walk-in, the tap on Sadiq, a real voice session over mobile data, and the reduced-motion setting. Judges will likely use phones.
5. Voice pick for English. This build's local `.env` uses Abdullah (`pCKbQ4EPGE06zpEPGNvS`) for both Arabic and English, and the e2e passed with it. It is not yet confirmed by the team. Majd or the lead should listen to Arabic and English once and then set `ELEVEN_VOICE_ID_AR` and `ELEVEN_VOICE_ID_EN` on the server. If `ELEVEN_VOICE_ID_EN` is blank, English uses the Arabic voice.
6. Fix the agent prompt: no salaam reply when the child said nothing; English demo should greet in English. Consider the latency branch.
7. Update JUDGE-DEMO-SCRIPT and DECK-OUTLINE to describe the new landing (living forest, props, time of day), and re-record screenshots for the deck and video.
8. Public repo plan (from `10-submission-pack.md` and the checklist, not yet agreed): create a fresh public repo with one clean baseline commit, because the private history has committed credentials and local paths. Before that: rotate every credential that was ever committed, scan the new repo's full history with gitleaks or trufflehog, write `THIRD_PARTY.md`, `AI_TOOLS.md`, `OPERATIONS.md` and `CONTENT_POLICY.md`, fill `DISCLOSURE.md`, and settle rights for the avatar, images, fonts, capstone and recitation audio. MOLI is for ideas only (CC BY-NC), so keep credit lines honest. Public SHAs will differ from private ones. Target: Mon 5 Oct. The lead must confirm the route (open question 2 in `CHECKLIST.md`).
9. Small cleanup: fix `avatar/README.md`, remove the unused `ChildIdleStage` voiceoff code, correct the architect plan text about the ElevenLabs cap (it goes text only, never xAI).

## 0. Update (integration, earlier the same day)

`hk/10-demo`, `hk/10-prod-hardening` and `hk/10-submission` are now merged into this branch, in that order, with merge commits. The sections below were written before that, so read "not in this branch" as "now in".

- `docker-compose.prod.yml` and `frontend/Dockerfile` conflicted (guards and hardening both edited them). Resolution: the agent keeps `REDIS_HOST=redis` (guards) and also gets `DEBUG` and `AGENT_NUM_IDLE_PROCESSES` (hardening). The frontend build args are the hardening ones (`VITE_FOREST_SCENE` and `VITE_DEMO_MODE`, default 0, only the exact string `1` is on) and the busybox stage copies the build into the volume at every start.
- The landing hero (`frontend/src/features/demo/DemoHeroScene.jsx`) now renders the live `ForestStage` with the avatar and its walk-in. The first greeting bubble appears when the walk reaches the wave (`ForestStage`'s `walkControlRef` now also gives `walk`, read-only). Tapping the scene makes the avatar talk, one bubble per tap. Fallbacks: no WebGL or a failed chunk gives the painted meadow with sun glow, clouds and the bubbles (no character); reduced motion keeps the forest but calm (no walk, camera cuts, no parallax).
- The walk-in plays once per page load (`played` in `walkIn.js`), so after the landing the child screen shows the avatar already at its spot.
- Landing copy: parents now "see the sources, the highlights and insights", not what was said (Arabic and English, `features/demo/copy.js`).
- `forestFlag.js`: `VITE_DEMO_MODE=1` turns the forest on by default, like `VITE_FOREST_SCENE=1`. `?forest=0` still turns it off.
- Checks on the merged result: 423 backend tests OK (3 skipped, sqlite settings), `npm run lint` clean, `VITE_DEMO_MODE=1 npm run build` passes. Edge at 1440 and 390 wide: landing, walk-in, tap, English, reduced motion, no WebGL. A full local stack with `DEMO_MODE=1` and `VITE_DEMO_MODE=1`: the button leads to `/child` with the forest and no `?forest=1`.
- Screenshots: `%USERPROFILE%\.claude\jobs\9adf820e\tmp\shots\phase2b\`.

## 1. What this is

The integration branch for the public demo at https://alsadiqai.com. It stacks the finished feature branches on top of `origin/hackathon` (`e7c98a3`) so they can be tested together before any PR:

- ElevenLabs voice with no automatic xAI fallback (07)
- the new avatar (06)
- the 3D forest behind the avatar (06b)
- the glue between avatar and forest
- credit and safety guards (demo-guards)
- the avatar walk-in on the forest screen (demo-walkin)

It does NOT contain the one-click demo login (`hk/10-demo`) or the production hardening (`hk/10-prod-hardening`). Those are separate branches. A read-only `git merge-tree` check shows both, and `hk/10-submission`, merge into this branch with no conflicts.

The lead's rule (Abdulrahman, 2026-10-04) is built in: ElevenLabs is the voice, and nothing falls back to xAI by itself. If ElevenLabs cannot be used, the session fails clearly with one error log and a `voice_error` message to the room.

## 2. What was merged and built, and why

Order of merges on the branch (all normal merge commits, history kept):

1. `hk/07-voice` (69fb2ca): ElevenLabs TTS, optional Scribe STT, the TTS text cleaner, and removal of the automatic xAI fallback. Clean merge. Backend only.
2. `hk/06-avatar` (10f268c): the web avatar (`avatar-web.glb`), motion, `agentState` and audio level from the LiveKit hook. Clean merge. `package-lock.json` never conflicted.
3. `hk/06b-forest` (7d7ff78): the forest stage. Conflicts in `VoiceMode.jsx` and `ConversationPage.jsx`, resolved by keeping both sides (the avatar's `agentState` and `getAudioLevel` props plus the forest flag).
4. Glue fix (f8e8f36): `ForestStage` now passes `agentState` and `getAudioLevel` to the Avatar, and `ConversationPage` feeds them from the LiveKit hook. Forest and meadow mode use the same Avatar and the same `avatar-web.glb`. `/dev/forest` sends a fake voice level so poses and jaw can be checked without an agent.
5. `hk/demo-guards` (85a5c7f, builder eebfd74 plus reviewer 8b81428): session time limit with a spoken goodbye, 3 sessions per child per day, 6 starts per hour per user, an ElevenLabs daily character cap (past it, new sessions go text-only), and a Redis kill switch with `manage.py voice_mode`. Reviewer verdict: ship-with-notes. Merged in full, because the open point (the frontend) is a gap and not a defect in what was merged.
6. `hk/demo-walkin` (c0a8e2e, builder e0aa097 plus reviewer 9379617): the avatar fades in up the path, waddles toward the camera, turns to face the child and waves. Reviewer verdict: ship-with-notes. Merged in full.

Neither reviewer said "needs-work", so nothing was held back. Both merged clean with no conflicts.

Why this order: 07 is backend only, 06 and 06b touch the same two frontend files, and merging the forest last gives one place to resolve the conflict.

## 3. Where it lives

| Area | Path |
| --- | --- |
| Voice factory (no xAI fallback) | `backend/conversation/agent/tts_factory.py`, `entrypoint.py` |
| Text cleaner and Quran bracket guard | `backend/conversation/agent/tts_text.py` |
| Guards (shared) | `backend/conversation/demo_guards.py`, `throttles.py`, `views.py` (start endpoint) |
| Guards (agent half) | `backend/conversation/agent/demo_limits.py` |
| Kill switch command | `backend/conversation/management/commands/voice_mode.py` |
| Guard tests | `backend/conversation/test_demo_guards.py` (84 plus 14 tests) |
| Avatar | `frontend/src/features/child/components/avatar/` (`Avatar.jsx`, `useAvatarMotion.js`, `walkIn.js`) |
| Forest | `frontend/src/features/child/components/forest/` (`ForestStage.jsx`, `CameraRig.jsx`, `runtime.js`, `forestFlag.js`) |
| Voice screen glue | `frontend/src/features/child/components/VoiceMode.jsx`, `frontend/src/pages/child/ConversationPage.jsx` |
| Avatar and forest preview | `/dev/forest`, `frontend/avatar-component-preview.html` |
| Other handoffs | `docs/hackathon/handoffs/` (06-avatar, 06b-forest-scene, 07-elevenlabs-facts, 07-elevenlabs-switch, 07-voice-text-cleaner, demo-walkin) and `docs/hackathon/demo-guards.md` |

## 4. How to run and test it

Backend tests, in the agent image with the code mounted (no network needed). From Git Bash set `MSYS_NO_PATHCONV=1` first:

```
docker run --rm --network none -v "%USERPROFILE%/Documents/Alsadiq-wt/demo-mvp/backend:/work" -w /work demo-mvp-livekit_agent:latest python manage.py test --settings=config.settings_sqlite_test
```

Result on the final merge: 371 tests OK, 3 skipped.

Frontend, from `frontend/`: `npm run lint` (clean) and `npm run build` (passes, only the old chunk-size warning; main bundle 261 kB gzip).

Full stack:

1. Copy `%USERPROFILE%\Documents\Alsadiq-wt\07-voice\.env` to `.env` in this worktree (it is gitignored). Check it with `python ..\env-names.py` (names only). Its `COMPOSE_FILE` points to `../livekit-win`.
2. Make sure nothing runs on 5173, 8000 or 7880 (`docker ps`).
3. `docker compose --profile all up --build -d`. Open `http://localhost:5173/child?forest=1` after logging in as a child.
4. Stop with `docker compose --profile all down` (the profile flag matters, without it the network stays in use). Never `-v` unless you want a clean database.

Guards are off while `DEBUG=1`. To test them locally add `DEMO_GUARDS=1` (and for a quick clock `DEMO_SESSION_MAX_SECONDS=60`) to `.env`. Check with `docker compose exec backend python manage.py voice_mode`.

What I ran on the final merge (Edge, phone size 390x844, headless on the real GPU, fake mic and camera permission, guards forced on, 60 s limit):

- Forest idle screen at `/child?forest=1`: forest and avatar visible, walk-in frames taken at 0.8 s to 12 s, avatar ends standing on the path.
- Start Session: `POST /api/conversation/sessions/` answered 201. The agent log showed "Voice mode for session_id=2: eleven (time limit 60s)" and an assistant transcript saved. Only `avatar-web.glb` was requested.
- The goodbye path: at the limit the log showed "Demo session time limit reached: saying goodbye", a second transcript was saved, and the process exited with reason "demo session time limit".
- Counting: `voice_mode` status showed 185 of 20000 ElevenLabs characters and 1 session today.
- No ElevenLabs, xAI or voice error lines in the agent log. No console errors on the page.
- Screenshots: `%USERPROFILE%\.claude\jobs\9adf820e\tmp\shots\demo-mvp-final\` (idle-0 to idle-5, session-0 to session-7). The earlier merge-stage shots are in `...\shots\demo-mvp\`.

This was a fake mic with no audio capture. I did not hear the voice, and I did not check the avatar poses against the real agent voice. The separate voice e2e kit does that (section 8).

## 5. Decisions

- Merge, do not rebase or squash, so each branch's history and reviewer fixes stay visible.
- No automatic xAI fallback anywhere. `TTS_PROVIDER=xai` and `voice_mode xai` stay as explicit operator choices, documented as manual rollbacks. An exhausted ElevenLabs budget goes text-only, never xAI. An unknown `TTS_PROVIDER` value warns and uses ElevenLabs.
- Walk-in ships as the full procedural walk. `?walk=hop` and `?walk=off` stay as fallbacks. Reduced motion and the meadow mode skip it.
- Guards are on whenever `DEBUG=0` (production) and off while `DEBUG=1` unless `DEMO_GUARDS=1`. They fail open if Redis is down.
- The forest stays opt-in (`?forest=1` or `VITE_FOREST_SCENE=1`) so a missing flag cannot switch a half-finished feature on.
- The architect's plan text said the ElevenLabs cap switches new sessions to xAI. That is wrong against the lead's rule and against the code, which goes text-only. Fix the plan text if it is reused.
- Merged commits keep their authors' trailers. Two builder commits carry `Co-Authored-By: Claude Code` and not the Opus 5.5 line. History was not rewritten.

## 6. Status

- Done and checked on this branch: 07, 06, 06b, glue, guards, walk-in. Tests, lint, build and one full-stack voice session all pass.
- Not pushed. No PR. Majd's main clone was not touched.
- Still not in this branch: the one-click demo login and landing (`hk/10-demo`), and production hardening (`hk/10-prod-hardening`). Both merge clean when wanted.
- Not done anywhere yet: the frontend handling of the guard messages (section 7, item 1).

## 7. Known issues

1. The frontend does not read `voice_mode`, `notice`, the 429 and 503 start refusals, `voice_error` or `session_limit`. Today a child on the voice screen gets silence with no banner when the ElevenLabs cap or the text switch trips, or a generic error when a limit is hit. The agent already works in text mode over the LiveKit text channel. The contract is in `docs/hackathon/demo-guards.md`. This must be done before the demo.
2. A page reload starts a new session and uses one of the 3 daily slots.
3. Only new sessions go text-only past the character cap. A running session can overshoot the cap and is bounded only by the time limit. Worst case the room closes at limit + grace + 12 s (about 322 s with the defaults).
4. The text-mode goodbye (spoken with `say()` and no TTS) was only tested with a fake session. Check live that it shows in the chat.
5. `ELEVEN_DAILY_CHAR_CAP` defaults to 20000 (about 10k credits a day on the flash model). Set it from the real remaining credits.
6. `STT_PROVIDER=scribe` would spend ElevenLabs credits that are not counted. The default `openai` is fine.
7. The English voice is still Habibah (the Arabic voice) until `ELEVEN_VOICE_ID_EN` is set. The voice audition is pending.
8. Walk-in: about 10.5 s in total (walk 7.1 s, turn 0.75 s, wave 2.75 s). A presenter may want to wait for the wave before tapping Start. Legs are small and mostly hidden by the cardigan, so it reads as a waddle. Blender-forest mode walks in a straight line.
9. The forest and walk-in were judged on the dev GPU only, not on a real phone.
10. `avatar/README.md` still names `avatar.glb` (the real file is `avatar-web.glb`). The 43 MB `avatar.glb` and `avatar-round7.glb` are still in `public/` and get copied into `dist`.
11. `docker-compose.prod.yml` was changed by the guards (the agent gets `REDIS_HOST=redis` and a redis `depends_on`). `hk/10-prod-hardening` also edits it. They merged clean in a read-only check, but check the result when merging.
12. With `DEBUG=0` the guards apply to every child on production, not only demo families (5 minutes, 3 a day).
13. Left in the local database of this worktree: a test child `mvpkid` in the `demo-mvp_db` volume. `docker compose down -v` from this worktree gives a clean database.

## 8. Next steps, ordered

1. Merge `hk/10-demo` and `hk/10-prod-hardening` into this branch when their teams say they are ready (`hk/10-submission` too, if it is wanted in the demo). Re-run the tests, lint and build after each, and look at `docker-compose.prod.yml` and `.env.production.example`.
2. Frontend for the guards (known issue 1): start in chat mode with the mic off when `voice_mode` is `text`, show `notice`, show the 429 and 503 messages, react to `voice_error` and `session_limit`, and show a time chip from `session_ends_at`.
3. Run the voice e2e kit at `%USERPROFILE%\Documents\Alsadiq-wt\e2e-voice` (needs ports 5173, 5432, 6379, 7880, 7881, 7882/udp and 8000 free): `python run_e2e.py --dry-run` first, then `python run_e2e.py`. It has not run against a live stack yet, so expect a few fixes on the first run. It also covers the manual xAI rollback case.
4. Phone test on a real device with `?forest=1`: frame rate, the walk-in, and the Start Session tap during the walk.
5. Pick the voices (audition), set `ELEVEN_VOICE_ID_AR` and `ELEVEN_VOICE_ID_EN`, and set `ELEVEN_DAILY_CHAR_CAP` from the real credits.
6. PR order, each only after Majd says yes: 07, then 06, then 06b, then demo-mvp (its diff then shows only the glue, guards and walk-in). The lead merges. Never push the production branch.
7. Server env for the lead: see the table below. Flip `VITE_FOREST_SCENE` and `VITE_DEMO_MODE` to 1 only after the matching code is merged, then rebuild the frontend.
8. Small cleanup: fix `avatar/README.md`, drop the unused 43 MB GLB files from `public/`, correct the plan text about the xAI cap.

## 9. Gotchas

- Git Bash mangles Docker paths. Set `MSYS_NO_PATHCONV=1` for `docker run -v`.
- `docker compose down` without `--profile all` leaves the network behind. Never add `-v` unless you want to wipe the database.
- `DEBUG=1` in `.env` turns the guards off silently. Add `DEMO_GUARDS=1` to test them.
- The kill switch is a Redis key. It is read at session start, and running sessions are not touched.
- Both the backend and the agent need `REDIS_HOST`. Without it on the agent, the kill switch and the character budget do not reach it (an error is logged).
- ElevenLabs flash does not read digits well. Write numbers as words. `eleven_v4_turbo` does not work with plugin 1.5.1 and is replaced with a warning.
- The agent reads `ELEVEN_API_KEY` from `.env` only, not from `eleven-key.txt`.
- Only one stack can use the ports at a time. Check `docker ps` first.
- Click-test with Playwright `channel="msedge"`. Never click `mailto:` or `tel:` links. The default headless Edge uses the real GPU. Forcing SwiftShader gives rough frame timing.
- The avatar's Start Session button works during the walk-in. The walk then finishes at 2.6x speed.
- No scripture goes in code or data (AGENTS.md). The goodbye text and the demo texts follow that.
- Helper scripts outside the repo, not committed: `Alsadiq-wt\demo-mvp-shots.py`, `demo-mvp-stack.py` and `demo-mvp-final.py`. The copied `.env` in this worktree is gitignored.

## Server .env additions

Updated in phase 2b (2026-10-04) to cover every branch now merged here.

Names only. "Branch" shows where the variable is read. Everything is optional unless the last column says "set".

| Name | Branch | Production setting |
| --- | --- | --- |
| `TTS_PROVIDER` | 07 | `elevenlabs`. Never `xai` unless the lead chooses a manual rollback |
| `STT_PROVIDER` | 07 | `openai` |
| `ELEVEN_API_KEY` | 07 | set (the real key, never committed) |
| `ELEVEN_VOICE_ID_AR` | 07 | set. Local e2e used Abdullah `pCKbQ4EPGE06zpEPGNvS`, team pick pending |
| `ELEVEN_VOICE_ID_EN` | 07 | set. Local e2e used the same Abdullah voice, pick pending (blank means the Arabic voice) |
| `ELEVEN_MODEL` | 07 | `eleven_flash_v2_5` (leave) |
| `ELEVEN_STABILITY`, `ELEVEN_SIMILARITY`, `ELEVEN_STYLE`, `ELEVEN_SPEAKER_BOOST`, `ELEVEN_SPEED` | 07 | leave unset (defaults), tune by ear |
| `ELEVEN_TEXT_NORMALIZATION`, `ELEVEN_ALIGNMENT`, `ELEVEN_LANGUAGE_HINT` | 07 | leave unset |
| `STT_SCRIBE_MODEL` | 07 | leave unset (only for `STT_PROVIDER=scribe`) |
| `XAI_API_KEY`, `XAI_TTS_VOICE`, `XAI_TTS_LANGUAGE`, `ARABIC_TTS_LOCALE` | 07 | only needed for a manual xAI rollback |
| `DEBUG` | guards, hardening | `0` (this turns the guards on) |
| `DEMO_GUARDS` | guards | leave unset (on when `DEBUG=0`) |
| `DEMO_SESSION_MAX_SECONDS` | guards | `300`, or lower for the demo |
| `DEMO_DAILY_SESSIONS` | guards | `3`, raise if judges share an account |
| `DEMO_SESSION_START_PER_HOUR` | guards | `6`, raise for a shared venue network |
| `ELEVEN_DAILY_CHAR_CAP` | guards | set from the real remaining credits |
| `DEMO_GOODBYE_LEAD_SECONDS`, `DEMO_SESSION_GRACE_SECONDS` | guards | leave unset |
| `DEMO_DAY_UTC_OFFSET_HOURS` | guards | `3` (Riyadh, default) |
| `REDIS_HOST`, `REDIS_PORT` | guards | set, `redis` and `6379`. The backend and the agent both need them |
| `REDIS_GUARDS_DB`, `REDIS_URL` | guards | leave unset |
| `VOICE_MODE` | guards | not an env var, a Redis key. Set it with `manage.py voice_mode` |
| `VITE_FOREST_SCENE` | 06b, hardening | `1` once 06b is merged, then rebuild the frontend (`VITE_DEMO_MODE=1` also turns the forest on) |
| `VITE_DEMO_MODE` | 10-demo, hardening, landing | `1` (landing, try button, forest by default, demo end card). Build time, so rebuild the frontend |
| `DEMO_MODE` | 10-demo | `1` (backend), then run `seed_demo` once and set the `demo_reset_expired` cron |
| `DEMO_POOL_SIZE`, `DEMO_LEASE_SECONDS` | 10-demo | leave unset (8 and 2700) |
| `DEMO_START_RATE`, `DEMO_RESET_RATE` | 10-demo | raise `DEMO_START_RATE` if judges share one venue IP |
| `ADMIN_ALLOWED_IPS` | hardening | the lead's IPs separated by spaces, no commas, or empty to block `/admin` |
| `DJANGO_SUPERUSER_PASSWORD` | hardening | set, long and random (required when `DEBUG=0`) |
| `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL` | hardening | the lead's choice |
| `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS` | hardening | the site domain and its https origin |
| `AGENT_NUM_IDLE_PROCESSES` | hardening | `1` |
| `DOMAIN` | hardening | the site domain |
| `VITE_API_BASE_URL` | base | the site's https origin (build time) |
| `CORS_EXPOSE_HEADERS` | voiceui | not an env var, set in `settings.py` (`Retry-After`). Keep it |
| `HTTP_PORT`, `HTTPS_PORT` | hardening | leave unset on the server (local smoke tests only) |

## Integration of hk/demo-voiceui and hk/demo-landing (2026-10-04)

Both branches are merged into this one (voiceui first, then landing). One conflict, in `frontend/src/pages/child/ConversationPage.jsx`, resolved so both intents stay:
- The voice-screen states from demo-voiceui are kept as they were: refusals (daily_limit, rate_limited countdown, voice_off, busy), text mode, voice_error and the text retry, the clock chip, the one-minute note, the goodbye and the end card, the language save before a start.
- The idle and starting screens are now the landing's `ChildIdleStage` (forest, Sadiq, tappable props, time and sound pills, level chip, one sun key). It takes the page's `lang` and a small language pill (`onToggleLang`), so a child account opens in the profile language and a pick still reaches the profile. The old idle card and the three-dots start view are used only for the ending spinner.
- The landing's separate "voiceoff" state is dropped: a text-mode start goes straight to the text chat with its notice, as demo-voiceui does. `ChildIdleStage` still understands `voiceoff` but nothing sets it.
- Refused, error and ended screens stay the demo-voiceui cards, drawn over the same forest stage (same control ref and walk preset, so there is no second walk-in).
- No xAI path was added. Nothing switches provider on its own.

Checks: 426 backend tests OK (3 skipped, sqlite settings), eslint clean, `VITE_DEMO_MODE=1` build passes. Edge at 390x844 on the full stack (DEMO_MODE=1): landing and walk-in, the try button, forest idle in Arabic and English, a real voice session, the end key back to idle ("Our talk is over"), the parent view. Mocked in Edge: the daily_limit card and the error card over the forest. No horizontal scroll on any screen.

Known gaps seen while integrating:
- Flipping to the parent view during a live session ends it with the parent token (403 on `/sessions/<id>/end/`, harmless); the session then runs until the agent's time limit.
- The status cards cover most of Sadiq on a 390x844 phone.
- The bottom nav is still English in Arabic.
