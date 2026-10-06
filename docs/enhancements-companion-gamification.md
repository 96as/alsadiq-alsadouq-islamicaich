# Companion, Gamification & Reporting Enhancements

Branch: `enhancement-claude-fable` · June 2026

This document describes the full set of enhancements added to Al-Sadiq Al-Sadouq:
a real companion personality with Grok-companions-style real-time leveling,
interactive quest types with three verification flows, a categorized locked-badge
system with streaks, agent response-speed improvements, and a parent activity
dashboard with quest verification.

---

## 1. Companion personality (Grok-companions style)

**File:** `backend/conversation/agent/agent_class.py`

Al-Sadiq is no longer a generic assistant — he is a specific character the child
gets to know across sessions:

- A young companion (~16) whose name means "the truthful friend" (الصديق الصدوق;
  Al-Sadiq = the friend, Al-Sadouq = the very truthful). _Superseded 5 Oct: the
  persona has no age, family, pets or home (AI disclosure, `agent_class.py`), and
  honesty is one of the 38 bank values he teaches, not the trait he loves most._
- **Likes:** stories of the Prophets (favorite: Prophet Yusuf), stargazing,
  dates with milk, his cat **Misk** _(superseded 5 Oct: no pets)_, drawing
  patterns, a "word of the day".
- **Dislikes:** lying and backbiting (they make him *sad*, never angry),
  bragging, wasting food, meanness to animals.
- **Quirks:** offers stories when excited, occasionally shares a small detail
  from his own world (_superseded 5 Oct: no Misk_; a star he spotted), says "Ma sha Allah!"
  when genuinely impressed, becomes gently serious when conversations drift
  somewhere unkind.

All seven safety rules are unchanged and still take priority over the persona.
The persona block works in both English and Arabic sessions (the existing
LANGUAGE directive governs output language).

## 2. Real-time leveling during conversation

Like Grok companions, the child's level now moves **live during the chat**, not
only after sessions.

### How it works

1. The agent has a new `record_engagement(quality, reason)` tool:
   - `excellent` **+10** — brave honesty moment, deep moral realization,
     sincere quest engagement
   - `good` **+5** — engaged talk about values/feelings/Islamic teachings
   - `poor` **−3** — drifting into unsuitable topics after one redirect
   - `bad` **−8** — persistently pushing inappropriate topics
2. The point change is applied through `gamification.services.award_points`
   (atomic, ledger-backed) and **pushed to the child's UI over the LiveKit data
   channel** (`topic="gamification"`).
3. The frontend (`ConversationPage`) updates the level bar instantly and shows
   an animated toast (+N / −N, quest complete, level up).

### Abuse guards

- Cooldown: ≥ 25 s between engagement events (`_ENGAGEMENT_COOLDOWN_SECONDS`).
- Cap: max 15 engagement events per session.
- The prompt forbids using points as bribes ("tell the truth and you get
  points" is explicitly forbidden) and forbids inventing point amounts.
- Negative totals are impossible — `award_points` clamps at 0.

### Data-channel payloads

```json
{ "type": "points", "delta": 5, "reason": "…", "total_points": 55,
  "level_number": 2, "level_name": "Kind Companion", "progress_pct": 7,
  "leveled_up": true, "leveled_down": false }

{ "type": "quest_completed", "quest_title": "…", "reward_points": 15,
  "total_points": 70, "level_number": 2, "…": "…", "new_badges": [ … ] }
```

## 3. Interactive quest types

**Files:** `backend/gamification/models.py`, `views.py`, `services.py`,
`backend/reporting/prompts.py`, `backend/reporting/services.py`

Every quest now has a `quest_type` and a `verification_method`:

| Type | Completed by | Verified by | Flow |
|---|---|---|---|
| `conversation` | Talking it through with Al-Sadiq | **companion** | The agent's `complete_conversation_quest` tool marks it done mid-session when the child genuinely engaged (not just "I did it"). Celebration toast + points appear live. |
| `real_world` | Doing something concrete IRL | **parent** | Child taps "I did it — ask my parent" (optional `proof_note`); status becomes `pending_verification`; a linked parent approves/rejects from the Insights page. |
| `reflection` | A quiet self-task (think/notice/write) | **self** | Child marks it complete; points awarded immediately. |

- The AI quest generator now outputs `quest_type` per quest and is instructed
  to vary types; verification is mapped automatically
  (conversation→companion, real_world→parent, reflection→self).
- The agent receives the child's open quests in its system prompt at session
  start and has a `list_my_quests` tool for mid-session refresh, so it can
  naturally weave quests into conversation ("I remember you had a quest
  about…").
- **Bug fix:** quest completion now actually awards points (previously
  `QuestCompleteView` only flipped the status — observation #945).

### New statuses & fields

- `ChildQuestProgress.status` gains `pending_verification`.
- `ChildQuestProgress.proof_note` — what the child says they did.
- `ChildQuestProgress.verified_by` — `child` | `companion` | `parent`.

## 4. Locked badges in categories

**Files:** `backend/gamification/models.py`, `services.py`,
`migrations/0004_seed_badges_and_levels.py`

`Badge` gains `category`, `requirement_type`, `requirement_value`,
`sort_order`. A badge engine (`evaluate_badges`) auto-awards any badge whose
requirement the child now meets; it runs after quest completions, streak
extensions, and post-session reports.

### Seeded catalog (19 badges, 5 categories)

- **Streak:** First Spark (2d), Three-Day Glow (3d), Steadfast Week (7d),
  Two-Week Champion (14d), Moon of Consistency (30d)
- **Honesty:** Truthful Heart (1 honest session), Honest Soul (5),
  As-Sadiq Companion (15) — based on `SessionReport.honesty_score == 1.0`
- **Quest:** First Quest (1), Quest Explorer (5), Quest Hero (15),
  Quest Legend (30)
- **Level:** Rising Star (L2), Bright Moon (L4), Radiant Sun (L6),
  Wisdom Seeker (L8)
- **Conversation:** First Hello (1 session), Good Listener (10),
  Heart to Heart (25)

8 levels are seeded if none exist (New Friend 0 → Radiant Soul 1000).

The child's Achievements page groups badges into category sections with
earned/total counters, and locked badges show **live progress** ("3 / 7") in
the unlock modal.

## 5. Daily streaks

**Files:** `backend/gamification/models.py` (`ChildStreak`),
`services.py` (`update_streak`), `backend/conversation/services.py`

- Starting a session rolls the streak: same day = no change, consecutive day =
  +1, gap = reset to 1. `longest_streak` is preserved.
- Each new streak day awards a +5 daily bonus (source `streak`) and triggers
  badge evaluation, so streak badges unlock the moment the child shows up.

## 6. Points ledger

**Model:** `gamification.PointsEvent`

Every point change (conversation, quest, streak, badge, adjustment) is recorded
with delta, reason, source, and optional session. `Points.total` stays the
aggregate. This powers the parent activity feed and the 14-day timeline, and
makes every level change explainable. Both new models are registered in the
Django admin.

## 7. Agent response speed

**Files:** `backend/conversation/agent/main.py`, `entrypoint.py`

| Change | Effect |
|---|---|
| `prewarm_fnc` loads Silero VAD once per worker process | Removes the multi-second VAD model load from *every* session join |
| Per-child DB context (memory, themes, quests) fetched with `asyncio.gather` | Three sequential queries → one round-trip time |
| `preemptive_generation=True` on `AgentSession` | LLM + TTS start while end-of-turn is still being confirmed — first audio arrives noticeably sooner |
| `min/max_endpointing_delay` 0.4 s / 3.0 s (env-tunable: `AGENT_MIN_ENDPOINTING_DELAY`, `AGENT_MAX_ENDPOINTING_DELAY`) | Faster turn detection after the child stops speaking |
| `STT_MODEL` env override (default unchanged: `gpt-4o-transcribe`) | Allows switching to `gpt-4o-mini-transcribe` for lower STT latency |

## 8. Parent reporting enhancements

**Files:** `backend/reporting/views.py`, `urls.py`,
`frontend/src/pages/parent/InsightsPage.jsx`

### New: activity dashboard API

`GET /api/reporting/dashboard/<child_id>/` returns:

- `sessions`: total, this week, talk minutes this week
- `streak`: current, longest, last active date
- `level`: full level snapshot (points, level, % to next)
- `quests`: counts by status (incl. `pending_verification`)
- `badges`: total + 5 most recent (with categories)
- `points_timeline`: daily point deltas for the last 14 days
- `recent_activity`: last 10 ledger events

### Enhanced: insights API

`GET /api/reporting/insights/<child_id>/` now also returns
`badges_detailed` (category + earned date), `history` (last 4 weekly
summaries), and `gamification` (level/streak snapshot). The original fields are
unchanged for backwards compatibility.

### Parent quest verification API

- `GET /api/gamification/parent/children/<child_id>/quests/?status=pending_verification`
- `PATCH /api/gamification/parent/quests/<progress_id>/verify/` with
  `{"action": "approve" | "reject"}` — approve completes the quest (points +
  badges); reject sends it back to `in_progress`.

All parent endpoints enforce an **approved** `ParentChildLink`.

### Insights page UI

Per child: stat cards (level, streak, sessions/talk-time this week, quests
done), a "Quests waiting for your confirmation" panel with the child's proof
note and Confirm/Not-yet buttons, the weekly summary with a collapsible
previous-weeks history, badges, and suggested topics.

## 9. Child frontend changes

- **ConversationPage** — listens to the `gamification` data topic via a
  subscription API on `useLiveKitRoom` (`onGamificationEvent`); the level bar
  updates live and animated toasts appear for points/quests/level-ups
  (`features/child/components/GamificationToasts.jsx`).
- **QuestsPage / QuestListCard** — type chips (💬 Chat with Sadiq · 🌍 Real
  world · 📓 Reflection), a "Waiting for parent" state, per-type guidance
  ("Talk this one through with Sadiq…"), and verification-aware button labels.
- **BadgesPage** — badges grouped into category sections with earned/total
  counts; locked-badge modal shows a live progress bar toward unlock.

## 10. Data model changes & migrations

- `0003_…` (auto): Badge category/requirements, Quest type/verification,
  ChildQuestProgress proof/verified fields + new status, **PointsEvent**,
  **ChildStreak**.
- `0004_seed_badges_and_levels`: idempotent seed (badges upserted by name;
  levels only when the table is empty). Reversible.

Deploy: `python manage.py migrate gamification`.

## 11. Tests

`backend/gamification/tests.py` — 23 new tests covering `award_points`
(ledger, clamping, level-up), streak transitions (first/same-day/consecutive/
gap), the badge engine (award, no-duplicates, quest-completion badges), all
three quest completion flows, parent verification (list/approve/reject/
unlinked-403), badge & level API shapes, and the parent dashboard (shape +
permissions).

Full suite: **61/61 passing** (`python3 manage.py test
--settings=config.settings_sqlite_test` — new SQLite test settings allow
running without Postgres).

## 12. New environment variables (all optional)

| Var | Default | Purpose |
|---|---|---|
| `STT_MODEL` | `gpt-4o-transcribe` | OpenAI STT model (use `gpt-4o-mini-transcribe` for speed) |
| `STT_REALTIME` | `1` | Realtime websocket STT — transcribes *while* the child speaks |
| `AGENT_MIN_ENDPOINTING_DELAY` | `0.4` | Seconds of silence before the turn can end |
| `AGENT_MAX_ENDPOINTING_DELAY` | `3.0` | Hard cap on end-of-turn wait |

No other configuration changes are required; everything else works with the
existing `.env`.

---

# Round 2 — Conversation realism, latency, memory (June 2026)

## 13. Realistic, friend-like conversation

**File:** `backend/conversation/agent/agent_class.py` (`_SPEECH_STYLE`),
`entrypoint.py` (`_GREETING_INSTRUCTIONS`)

- **No more topic menus.** The persona now explicitly forbids assistant
  behavior ("What would you like to talk about today?", listed options). The
  greeting instruction was rewritten (EN + AR): salam + one short sentence,
  two max, and — when memory exists — follow up on something concrete from
  last time (the test, the friend, the cat) instead of a generic opener.
- **Short, spoken replies.** New speech-style rules: one to three short
  sentences (~35 words) by default, at most one question per reply, react
  first like a friend, vary openings, contractions and natural interjections.
  Stories only when asked, and in short spoken lines.
- **Symbol-free output, enforced in code.** The prompt bans markdown, lists,
  emojis, and digit-numbers (write "three", not "3") because TTS reads text
  literally. As a guarantee, `AlSadiqAgent.tts_node` now pipes the LLM stream
  through LiveKit's built-in `filter_markdown` + `filter_emoji` before
  synthesis. Since transcripts are TTS-aligned, the chat display inherits the
  same cleaned text — fixing both the robotic speech and the symbol-filled
  chat bubbles.

## 14. Latency round 2

| Change | Why it matters |
|---|---|
| **Realtime STT** (`use_realtime=True`, env `STT_REALTIME`) | Audio is transcribed over a websocket *while the child speaks*; the transcript is ready the instant the turn ends, instead of uploading buffered audio afterwards. Typically saves 300–800 ms per turn. |
| `.env`: `STT_MODEL=gpt-4o-mini-transcribe` | Faster transcription model. |
| `.env`: `LLM_MODEL=gpt-5.4-mini` | Mini-class model with much lower time-to-first-token; the persona + guardrails live in the prompt and Islamic content comes from the verified knowledge-base tool, so quality holds. Revert to `gpt-5.2` if replies feel less rich. |
| Shorter replies (speech style) | Less text → TTS finishes the first sentence sooner; turn-taking feels snappier. |

Combined with round 1 (prewarmed VAD, parallel DB fetch, preemptive
generation, 0.4 s endpointing), the pipeline is now within ~1–1.5 s
voice-to-voice, which is the practical floor for an STT→LLM→TTS architecture.
The remaining step-change would be a speech-to-speech realtime model
(e.g. `openai.realtime.RealtimeModel` as a drop-in for the LiveKit session) —
an architecture swap that trades away the xAI voice and per-stage control.

## 15. Memory that remembers facts

**Files:** `backend/reporting/prompts.py`, `agent_class.py`

- The session report now extracts **`memorable_facts`** — concrete details a
  friend would remember ("Has a cat named Luna", "Math test on Sunday",
  "Best friend is Yousef").
- The rolling summary was restructured from a behavioral profile into a
  friend's memory with labeled sections: **FACTS I KNOW** (durable, kept
  unless contradicted), **THINGS TO FOLLOW UP** (time-bound, dropped when
  stale), **HOW THEY'VE BEEN** (patterns), **NEXT TIME** (priorities).
- The agent receives this as "WHAT YOU REMEMBER ABOUT THIS FRIEND" with
  instructions to use it the way a real friend does — mention the cat by
  name, ask how the test went — one remembered detail at a time.

Note: existing children's memories regenerate in the new format after their
next completed session (no migration needed).

## 16. AI-decided quest generation

**Files:** `backend/reporting/prompts.py`, `services.py`, `config/settings.py`

Quest generation no longer relies on a blunt one-batch-per-day cap. The quest
LLM now acts as a **curator that decides for itself** whether the child needs
new quests:

- It receives the child's **full open-quest board** — every non-completed
  quest with its type, status, reward, age in days, and description — plus
  recently completed quests and the session report.
- It returns `{"decision": "add" | "skip", "reason": …, "quests": […]}`.
  Decision guidance: skip when the plate is full (3+ open), when open quests
  already cover what the session surfaced, or when the session was thin; add
  when the plate is empty-ish, when the session surfaced something specific
  that no open quest addresses, or when open quests have gone stale (4+ days).
  Target: total open count stays ≤ 4.

Mechanical gates that remain (backstops, not the primary logic):

| Setting | Default | Role |
|---|---|---|
| `REPORTING_GENERATE_QUESTS` | `1` | Master switch |
| per-report idempotency | always on | Never generate twice for one report |
| `REPORTING_QUESTS_MAX_OPEN` | `5` | **New** — skip the LLM call entirely at 5+ open AI quests (cost guard) |
| `REPORTING_QUESTS_DAILY_CAP` | **`0` (was `1`)** | Legacy throttle, now opt-in |
| `REPORTING_QUESTS_SKIP_IF_PENDING` | `0` | Legacy throttle, opt-in |

Old-format LLM responses without a `decision` key still work (default "add"),
and the LLM's skip reasons are logged for tuning. Covered by 5 new tests
(`LLMQuestDecisionTests`) — full suite now **66/66 passing**.

---

## Native Mobile App (Expo React Native)

A production Expo React Native app in `mobile/` brings the
companion to iOS + Android. It reuses **every backend contract documented above**
with **zero backend changes** — it is just another LiveKit client joining the
same rooms the Python agent runs, and it calls the same REST endpoints with the
same JWT auth.

**What's reused, unchanged:**

- **Auth:** login / refresh / logout / parent registration / password reset
  (deep link `alsadiq://reset-password?uid=&token=`), child profile + password.
- **Conversation:** `POST /api/conversation/sessions/` → join LiveKit; live
  transcription stream (`lk.transcription`), chat via `sendText` on `lk.chat`,
  and the **gamification data channel** (`points` / `quest_completed`) drive
  in-app toasts, a live level bar, and a celebration overlay.
- **Gamification:** typed quests (conversation / real_world / reflection) with
  `verification_method` honored exactly as on web — companion quests are
  completed by Sadiq in-session, parent quests go to `pending_verification`,
  self quests complete immediately; badges by category with progress; level +
  streak.
- **Parent:** children list with in-app status, conversation summaries,
  insights (stat cards, **verification panel** to approve/reject pending
  real-world quests, weekly summary + history, badges, suggested topics), and
  safety alerts.

**Mobile-specific design:**

- **Native avatar:** the 41 MB Blender GLB is optimized to ~4.3 MB
  (decoder-free, Hermes has no WASM) and rendered with expo-gl + three; the jaw
  bone is driven by the agent's speaking state, with a graceful animated
  fallback.
- **Child-first redesign:** warm light/dark themes, ≥56pt touch targets, large
  type, haptics, confetti — with reduced-motion support.
- **RTL-safe** i18next layouts; language preference still only controls the AI
  agent's language (no Arabic UI yet).

Setup, dev-build, and LAN configuration: `mobile/README.md`.
