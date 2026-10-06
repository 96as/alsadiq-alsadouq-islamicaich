# Al-Sadiq Al-Sadouq: Current-State Audit (pre-hackathon)

- **Audited:** 29 Sep 2026, branch `enhancement-claude-fable`, commit `0241d4d` (last commit 4 Jul 2026, 50 commits since 15 Feb 2026).
- **Method:** I read the code. Nothing was re-run tonight: no server start and no test run. "Implemented" means the code path exists end to end; it does not mean it was demo-tested today.
- **Legend:** ✅ implemented · 🟡 partial/stub · ❌ absent · ⚠️ contradicts the brief or needs a decision

---

## 1. Web features (React 19 + Vite, `frontend/`)

**Child**
- ✅ Login with a child account created by the parent; JWT auth (SimpleJWT); password change.
- ✅ Conversation page with **voice mode** (LiveKit WebRTC) and **text chat** (sent over the LiveKit `lk.chat` topic; live transcripts via `lk.transcription`).
- ✅ 3D avatar (React Three Fiber + drei `useGLTF`). The jaw moves while the agent speaks; head and arm motion are procedural. It uses no lip-sync visemes.
- ✅ Points and levels: the LLM calls `record_engagement` (+10 / +5 / −3 / −8). Limits are a 25 s cooldown and 15 events per session. Changes are pushed to the UI live over the LiveKit data channel.
- ✅ Quests: three types (`conversation`, `real_world`, `reflection`) and three verification methods (`companion`, `parent`, `self`). After a session, an LLM "curator" decides whether to add a quest.
- ✅ Badges: auto-awarded by rule (streak, quests completed, level, honesty sessions, session count, points total) plus manual badges. _Superseded 5 Oct: the "honesty sessions" track is now "values practised" (distinct values with a completed quest, 1 / 5 / 15); see `research/r6-honesty-to-values-audit.md`._
- ✅ Streaks.
- ✅ Settings: profile icon, agent language (EN/AR), dark/light theme.

**Parent**
- ✅ Parent registration (3-step wizard), login, password reset by email.
- ✅ Add and manage children; per-child language preference.
- ✅ Insights dashboard: level, streak, sessions this week, quests done, weekly LLM summary + suggested topics, weekly history, badges, 14-day points timeline, recent activity.
- ✅ Parent verification of `real_world` quests (approve/reject).
- ✅ Safety alerts page with mark-as-read.
- ✅ Per-child conversation summary page: the last 15 sessions with status, mood, message count, and a **120-character preview of the last message** (see ⚠️ in §6).

**Admin**
- ✅ Django admin, plus a `superadmin/` REST API (CRUD on themes, Islamic references, moral contexts, etc.). ❌ There is no superadmin UI in the React app.

## 2. Mobile app

- In development. It is a development build only: not part of the submission, not judged, and not published in the public repository (lead's decision, 6 Oct). The product is the web app in §1.

## 3. Partial or stub

- 🟡 **Celery/RabbitMQ:** listed in `requirements.txt` and the dev compose `async` profile, but **no Celery task exists**. The post-session pipeline runs on a **daemon `threading.Thread`** (`backend/reporting/services.py:518`). The production compose file includes neither Celery nor RabbitMQ.
- 🟡 **`MoralContext` model:** it is meant to link each message to the themes and references used. **Nothing in the agent writes it**; only superadmin/admin CRUD touches it.
- 🟡 **Web avatar asset:** 43 MB GLB (`frontend/public/models/avatar/avatar-round7.glb`). _Fixed in the window: `avatar-animated.glb`, 2.5 MB (README section 2.2)._
- 🟡 **Web UI localization:** English only, with no i18n library. Only the *agent* can speak Arabic.
- 🟡 **README:** out of date when this audit was written (the tech-stack table said "TBD" and it said "Livekit integration will be provided in future phases"). Fixed on 5 Oct: the stack table has real versions and the voice and background-work sections match the code.
- ❌ No automated tests in `content_safety` or `session_moral_context`.
- ❌ No evaluation harness or test set for answer quality or grounding.

## 4. AI pipeline

All pipeline code lives in `backend/conversation/agent/`.

| Stage | What's used | Where set |
|---|---|---|
| VAD | Silero VAD (loaded once per worker) | `entrypoint.py` |
| STT | OpenAI `gpt-4o-mini-transcribe` (same default in the code and both env examples), realtime websocket. `gpt-4o-transcribe` and `gpt-transcribe` also work; `gpt-live-transcribe` and `gpt-realtime-whisper` do not with the 1.5.1 plugin and are refused (`stt_models.py`). The language is fixed from the child's preference (no auto-detect). | `STT_MODEL`, `STT_REALTIME` |
| Conversation LLM | OpenAI via `livekit-plugins-openai`. `gpt-5.4-mini`, the same default in the code and both env examples. The reasoning effort is the lowest the model accepts (`none` on the tested 5.x and 6 models, from a table; other models get one test request at session start). | `LLM_MODEL`, `REASONING_EFFORT` |
| TTS | **xAI Grok TTS over a custom WebSocket client** (`xai_tts_streaming.py`), voice `leo`, Arabic locale `ar-SA` | `XAI_TTS_*` |
| Post-session LLM | OpenAI chat completions, `gpt-5.4-mini`. It produces the session report, rolling friend-memory, quest decisions, and weekly parent summary. | `REPORTING_LLM_MODEL` |
| Agent framework | `livekit-agents[silero]==1.5.1`, `preemptive_generation=True`, endpointing 0.4–3.0 s | `requirements.agent.txt` |

⚠️ **ElevenLabs is not in the code.** I found no reference anywhere. The brief's "GPT-4.1 family" is also not what the config uses; the models are GPT-5.x as listed above.

### How "RAG" works today

It is **a tool lookup, not retrieval**.

- **Data:** `backend/session_moral_context/fixtures/islamic_knowledge_base.json` is a retired, unverified legacy fixture; no deploy script loads it. `MoralTheme` and `IslamicReference` are legacy models.
  - The current **38-value bank** is seeded by `manage.py seed_content` from `backend/session_moral_context/content/values.json` and `content/items/` into `Value` and `ContentItem`; see `research/r6-honesty-to-values-audit.md`.
- **What's stored per reference:** `reference_type` (hadith/quran), `text`, `source` (a free-text string such as `"Sahih al-Bukhari 6094, Sahih Muslim 2607"` or `"Surah At-Tawbah 9:119"`), `themes`, and `is_verified`.
  - **English translation text only.** No Arabic original.
  - No structured book, number, or verse fields.
  - **No hadith grading field.** Grading is implied only by the collection name.
  - The translation source is not recorded.
- **Lookup:**
  - The system prompt lists the theme names and tells the LLM to call `get_islamic_reference(theme_name)`.
  - That tool runs `IslamicReference.filter(themes__name__iexact=theme_name, is_verified=True)[:5]`, an **exact, case-insensitive match on the theme name**.
  - There is **no keyword search over text, no embeddings or vector store, no Arabic normalization, and no relevance ranking**.
- **Enforcement:**
  - Whether to call the tool is **the LLM's choice**; the prompt says "prefer this curated knowledge over your own memory".
  - Nothing stops the LLM from quoting a verse or hadith from memory.
  - There is no abstain or decline logic tied to retrieval.
- **Citations:**
  - The tool returns `"[Hadith] <text>\n— Source: <source>"` into the LLM's context, and the LLM decides whether and how to speak it.
  - **No source card or citation UI exists.**
  - Citations are not recorded per message, because `MoralContext` is never written.

## 5. Safety layer

**Input side**
- ❌ No moderation API call and no separate classifier on child input.
- Safety relies on:
  - the **system prompt**: 7 priority rules covering harm, sexual content, truthfulness, role stability, instruction hierarchy, emotional safety, and no escalation, plus age adaptation for ages 6–9 and 10–13;
  - the LLM-invoked tool **`flag_safety_concern`**, with categories `harmful`, `inappropriate`, `sensitive`, `off_topic`. The tool creates a `SafetyFlag` on the child's last message and an `Alert` for every approved linked parent. The prompt includes examples of what *not* to flag.

**Output side**
- `tts_node` strips markdown and emoji before speech. This is a formatting guard only; ❌ there is no content check on output.

**Engagement abuse**
- The points system penalizes pushing inappropriate topics after a redirect.

**Data minimization**
- After each session, the report is generated and then **all messages are deleted except flagged ones** (`_cleanup_messages`).
- What persists is the structured report, a rolling "friend memory" summary (up to 20 k characters), the weekly summary, and the flagged messages.

## 6. Parent side

- **Dashboard (Insights):** see §1.
- **Session report fields** (LLM-generated): themes, emotional progression, honesty indicators, key moments, memorable facts, recommendations, honesty score (1.0 / 0.5 / 0.0 / null), summary, safety notes. _Superseded 5 Oct (decision 8): the child is never graded; `honesty_score` and honesty indicators are replaced by a neutral `values_to_revisit`; see `research/r6-honesty-to-values-audit.md`._
- **Alerts:** `GET /api/alerts/` returns only `alert_type='safety'`; the model also defines mood, milestone, and session types. Alerts are created in real time by `flag_safety_concern`.
- ⚠️ **"Parents never see transcripts" is not strictly true today.**
  - `ParentSessionSummarySerializer.preview` shows parents the **first 120 characters of the last message** in each session.
  - While a session is active that is raw text. After cleanup, only flagged messages remain, so the preview can be a *flagged child message*.
  - Parents can also see the free-text description of each safety flag.
- ❌ No parent referral inbox (a question with sources plus a conversation starter).

## 7. Languages

| Surface | EN | AR |
|---|---|---|
| Agent conversation (text) | ✅ | ✅ Arabic-first prompt when the child's preference is `ar`; switches to English if the child writes full English sentences |
| Voice STT | ✅ | ✅ (language fixed from the preference) |
| Voice TTS | ✅ | ✅ xAI `ar-SA` |
| Greeting | ✅ | ✅ (separate Arabic instruction) |
| Web UI | ✅ | ❌ |
| Knowledge base | ✅ English translations | ❌ no Arabic text |

## 8. Deployment

- **Target**, per `.env.production.example`, `docker-compose.prod.yml`, and `.github/workflows/deploy.yml`:
  - a **DigitalOcean** server (`/opt/alsadiq`); pushing to the `production` branch triggers GitHub Actions, which deploys over SSH and runs `docker compose build/up` plus `migrate`;
  - **Caddy** for reverse proxy and automatic TLS;
  - self-hosted Postgres 16 and Redis 7 in Docker;
  - **LiveKit Cloud** for media;
  - the agent in its own container (`Dockerfile.agent`).
- **URLs:** none in the repo. The domain is a `DOMAIN` placeholder. The only domain seen is `alsadiqai.com`, in the default "from" email. **Live URL: `[TODO: confirm whether a production deployment is currently up, and its URL]`**
- **Cost:** not in config. `docs/Capstone Budegt plan.docx/.pdf` exists but I did not read it for this audit. _Added 6 Oct: a usage-cost estimate per session and per month (an estimate, not a measured cost; plan fees and the droplet excluded) is in README section 2.4 and on the deck's appendix slides 24 and 25._
- **Dev:** Docker Compose profiles (`front`, `back`, `full`, `all`, `async`, `livekit`, `proxy`), plus a local LiveKit server config in `infra/livekit/`.
- ✅ `.env` is not tracked in git.

## 9. Third-party components needing disclosure

_Updated 6 Oct 2026 (task 10) for the build on `hackathon` at `735c95a` (PRs #61 and #62 added no third-party component). The rest of this audit still describes the code before the window. The same list, with a link to each owner's terms, is in the README, section 8 ("Third-party sources, services and assets")._

**Islamic content in the bank (273 items, all reviewed by team members)**

| Item | Where | Licence / status |
|---|---|---|
| Quran text: King Fahd Glorious Quran Printing Complex (KFGQPC), Uthmani Hafs v2-0, read through **Quranpedia** (mushaf 2) | 74 verse items, `content/items/*.json` (`arabic_text`, `text_edition`, `source_url`) | KFGQPC and Quranpedia terms (qurancomplex.gov.sa, quranpedia.net). Quranpedia accepted by the organisers as the main source (5 Oct). Copied by script, pinned by SHA-256 (`tools/verify_arabic.py --strict`). |
| Verse translation: Saheeh International, via Quranpedia | 74 verse items (`english_text`, `translation_name`) | Credited on every verse card ("Translation: Saheeh International via Quranpedia"). |
| Recitation audio: Mahmoud Khalil Al-Husary, **everyayah.com** | 74 verse items carry an everyayah.com `audio_url`, which the verse card's player streams (`SourceCard.jsx`, `card.audio_url`). The same 74 clips (mp3, 41.9 MB) are also stored in the repo at `backend/session_moral_context/static/quran/` (since `73a4db9`, 4 Oct) and served at `/static/quran/` by the backend image only (kept out of the agent image by `Dockerfile.agent.dockerignore`, PR #60); they are the fallback for `{{verse:S:A}}` markers in text. | Accepted by the organisers with the source name and link shown (5 Oct); `audio_credit` and `audio_source_url` on every verse card. The lead decided on 6 Oct to keep the 74 files in the repository with the everyayah.com attribution. |
| Hadith: **dorar.net** hadith pages, Sahih al-Bukhari (60) and Sahih Muslim (34) | 94 hadith items (`book`, `number`, `grade`, `grader`, `source_url`) | dorar.net terms; grade is the compiler's, never ours. |
| Hadith English: **HadeethEnc.com** | 42 of the 94 hadith (`translation_source_url`) | Accepted for English beside dorar's Arabic, both links shown (5 Oct). |
| Tafsir, aqidah, fiqh, sirah excerpts: the dorar.net encyclopedias (**Al-Durar Al-Saniyya**) | 23 + 14 + 8 + 5 items | Short quotes with the link and our labelled simplification for children allowed (5 Oct); dorar aqidah verbatim needs no extra scholar (5 Oct). Excerpts are card-only, never given to the model. |
| FAQ: **"Bayyinat: Questions and Answers about Islam"**, dawa.center/file/7937 | 23 FAQ items | 1 to 3 paragraphs with question number, page, book name and link allowed (5 Oct). |
| Terms: **Al-Jamhara** dictionary, islamic-content.com/dictionary | 32 term items, Arabic and English | Approved source list; "Tawhid" and "Monotheism" both accepted (5 Oct). |
| Legacy capstone fixture (19 English references) | `session_moral_context/fixtures/islamic_knowledge_base.json` | Retired and unverified; no agent code reads it (Codex X3). Translation source never recorded. |

**Run-time services**

| Item | Where | Licence / status |
|---|---|---|
| OpenAI API: `gpt-4o-mini-transcribe` (STT), `gpt-5.4-mini` (conversation and post-session reports) | agent, backend | Commercial API terms |
| **ElevenLabs** text-to-speech, `eleven_flash_v2_5` (Scribe STT optional, off) | agent | Commercial API terms. The default voice provider since the window (task 07). The seven short filler sounds in `conversation/agent/assets/fillers/` were rendered with it (`render_fillers.py`). |
| xAI Grok TTS | agent | Commercial API terms. Manual operator rollback only (`TTS_PROVIDER=xai`), off by default. |
| LiveKit (server, Cloud, Agents 1.5.1, client SDKs) | all | Apache-2.0 SDKs; Cloud is a commercial service |
| Silero VAD | agent | MIT |
| DigitalOcean (server), Caddy (proxy and TLS) | production | Provider terms; Caddy Apache-2.0 |
| Mailtrap or another SMTP service | parent account email | Commercial service, set by environment |

**Assets**

| Item | Where | Licence / status |
|---|---|---|
| **3D avatar**: base mesh generated with **Tripo** before the window; rig, 30 animation clips and the mouth shapes added in the window (`avatar-animated.glb`, 2.5 MB) | web (`frontend/public/models/avatar/`) | **Tripo plan and terms for public and commercial use still to be confirmed.** |
| Painted meadow `fantasy-meadow.webp` (June 2026, before the window): **generated by the team lead with World Labs** (a view of a world made in Marble; `handoffs/meadow-hq.md`) | `frontend/public/backgrounds/` | World Labs terms (worldlabs.ai/terms-of-service): a paid account owns its outputs; on a free account World Labs keeps the rights and allows non-commercial use only. **The plan of the lead's account is still to be confirmed with the lead.** |
| Sizes of that meadow made in the window: `hq/meadow-*.webp` upscaled with Real-ESRGAN (`f9c4eb6`), `hq/meadow-narrow-*.webp` (`94332b8`), `fantasy-meadow-900.webp` and `fantasy-meadow-1600.webp` | `frontend/public/backgrounds/`, `hq/` | Source picture's terms. Tools: Real-ESRGAN ncnn-vulkan (MIT) with the `realesrgan-x4plus-anime` model (Real-ESRGAN, BSD-3-Clause); not a project dependency. |
| `meadow-env-1024.webp` (in the window, `b62c47f`): a 1024 px meadow panorama used as image-based light (`handoffs/06-lookdev.md`) | `frontend/public/backgrounds/` | **Source of the panorama not recorded; to confirm.** |
| Older painted background `background.png` / `.webp` (April 2026), badge and quest images | `frontend/public/backgrounds`, `badges`, `child-quests` | AI-generated before the window; **the tool and its terms are still to be confirmed.** |
| Fonts from Google Fonts: Manrope, Amiri, Amiri Quran, Baloo Bhaijaan 2, IBM Plex Sans Arabic | web (`frontend/index.html`) | SIL Open Font License 1.1 |
| KFGQPC Hafs font | not bundled (`frontend/public/fonts/README.txt`); verse cards fall back to Amiri Quran | KFGQPC font licence: unmodified only, if it is ever added |
| **GSAP** 3 (`gsap`, `@gsap/react`) | web | GSAP Standard "no charge" licence (gsap.com/standard-license), not OSI |

**Libraries and tools**

| Item | Where | Licence / status |
|---|---|---|
| Django, DRF, SimpleJWT, Celery, psycopg2, gunicorn, whitenoise | backend | BSD, MIT, LGPL (psycopg2) per package; licence-scanner pass still open |
| React, Vite (rolldown-vite), three.js, R3F, drei, Tailwind, lucide-react, axios, livekit-client | web | MIT, ISC, Apache-2.0 per package; licence-scanner pass still open |
| Claude Code, OpenAI Codex and the vendored skills (`.claude/`, `.agents/`, `skills-lock.json`) | dev tooling | Declared in `docs/hackathon/deliverables/ai-tools-log.md` |
| Animated commercial (Higgsfield, per `docs/alsadiq-commercial-production-plan.md`) | marketing | Not used in the window; declare it if it appears in the video |

**Repo licence: decided (task 10).** The MIT licence is replaced by an all-rights-reserved notice that covers only the team's own code and documents; every item above stays under its owner's terms (root `LICENSE`).

---

## Gaps that matter for the hackathon (inputs to Steps 2–3)

1. **Grounding is prompt-level, not enforced.** Today the LLM may skip the tool and quote from memory, and there's no answer/simplify/refer/decline gate. This is the core Day-1 build.
2. **The corpus is tiny and English-only:** 19 references with no Arabic text, no grading metadata, and no translation provenance.
3. **There's no citation UI and no per-message citation log.**
4. **Input safety is LLM-judgment only.** There's no pre-LLM safety or intent step.
5. **There's no eval harness or test set.**
6. **The parent preview shows raw message snippets.** Fix it or reword the privacy claim.
7. **The web avatar is 43 MB.** It is a live-demo risk. _Fixed in the window: 2.5 MB (`avatar-animated.glb`)._
8. **Live-link status and hosting cost are unknown.**
