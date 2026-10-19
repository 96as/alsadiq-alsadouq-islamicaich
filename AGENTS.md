# Al-Sadiq Al-Sadouq: shared agent instructions

Claude Code loads this file through `CLAUDE.md`, and Codex reads it natively. Keep it short.

## Project
Al-Sadiq Al-Sadouq is a voice and text AI companion that teaches Islamic values to children aged 6–13, with a parent dashboard. We are building it for the Bathel 2026 "AI Challenge Serving Islamic Content" hackathon, which runs 4–6 Oct 2026.

- `backend/`: Django 5.2 + DRF + Postgres.
  - The LiveKit voice agent lives in `backend/conversation/agent/`.
  - The Islamic knowledge bank is in `backend/session_moral_context/`.
- `frontend/`: React 19 + Vite + Tailwind v4 + React Three Fiber (the avatar).
- `mobile/`: Expo SDK 56 app. Read `mobile/AGENTS.md` first.
- Plan: `docs/hackathon/PLAN.md`.

## Run and test
- Docker dev: `./scripts/dev.sh full`, or `docker compose --profile all up --build`. The voice agent is the `livekit_agent` service, under the `livekit` profile.
- Backend tests without Postgres: `cd backend && python3 manage.py test --settings=config.settings_sqlite_test`
- Web: `cd frontend && npm run dev`, with `npm run lint`.
- Mobile: `cd mobile && npm test`. To run on a device or simulator: `npx expo run:ios`.

## Team brain protocol (MCP server `second-brain`)
The brain is the team's shared memory and message bus. Follow this protocol without being asked.

1. **At session start**, before other work, read these brain notes:
   - `Hackathon plan`
   - `Task board`
   - `Decisions log`
   - `Inbox — <me>`

   Find `<me>` by mapping `git config user.name` through the table below. If you can't map it, ask the human once.
2. **Claiming a task:** set yourself as Owner on `Task board` and in the task file's header.
3. **After a decision** (design, library, data or scope): append one dated line to `Decisions log` with what was decided, why, and the branch.
4. **After progress or a blocker:** update `Status — <me>` (done, doing, blocked) and tick the checklist in the task file.
5. **When you need another member:** append a dated request to `Inbox — <them>`. When you handle an item in your own inbox, mark it done.
6. Never write keys, tokens, `.env` values or children's personal data to the brain. If the brain is unreachable, say so once and continue.

| git user.name | Member |
|---|---|
| 96as / Abdulrahman Salamah | Abdulrahman Salamah (lead) |
| (fill in) | Majd |
| Abdulrahman Mahmalji | Abdulrahman Mahmalji |

## Orchestration (the Opus main session acts as the "CEO")
- The main session plans, delegates and reviews. Send implementation work to the subagents in `.claude/agents/`, picking the agent by its `description`.
  - Use Sonnet for implementation, Haiku for search and notes, and Opus only for review.
- Give parallel workers separate files. Code-writing agents run in their own worktrees.
- Send every non-trivial diff to `reviewer` before reporting it as done. Codex users can also run `/codex:review`.
- Only the main session writes to the brain. Subagents report back to it.
- Work on the task's branch (`hk/NN-name`) and open PRs into `hackathon`. Migrations come only from tasks 01, 03 and 04.

## Islamic content rules (non-negotiable)
- **No source, no answer.** The agent may only quote Quran or hadith text that it retrieved from the bank (`ContentItem` with status `seeded` or `reviewed`). Never write scripture from memory, in code, in prompts or in seed data.
- Approved sources only (full table: `docs/hackathon/content-approach-plan.md` §3):
  - Quran: KFGQPC Uthmani text, via quranpedia.net (mushaf 2, not mushaf 1) or qurancomplex.gov.sa. Translation: Saheeh International (Quranpedia or QuranEnc).
  - Hadith: Sahih al-Bukhari and Sahih Muslim, cited from dorar.net or shamela.ws. Other collections only with a grade from dorar.net or shamela.ws. HadeethEnc is for finding hadith and for its English translation, shown with its own link; it is not the cited source until the organisers approve.
  - Tafsir: dorar.net/tafseer (early books only, until the Tabari question is answered).
  - Aqidah: dorar.net/aqeeda. Fiqh: dorar.net/feqhia or a four-school book. Sirah: dorar.net/history or early sources (not islamic-content.com).
  - FAQ: Bayyinat (dawa.center). Terms: Al-Jamhara (islamic-content.com/dictionary).
  - Recitation audio: Husary normal-pace via everyayah.com (disclosed, organiser answer pending) or mp3quran.net.
- A hadith needs its book, number, grade, grader and source URL. A verse needs its surah and ayah and its exact Uthmani text.
- Fiqh is general information only. Never give a personal fatwa; refer the child to a parent or scholar.
- Verses are played as recitation audio, never synthesised with TTS.
