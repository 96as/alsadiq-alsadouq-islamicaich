# Disclosure of pre-existing work and third-party services
# الإفصاح عن الأعمال السابقة والخدمات الخارجية

- **Project / المشروع:** Al-Sadiq Al-Sadouq (الصديق الصدوق)
- **Challenge / المسابقة:** Islamic AI Challenge, Open Track (تحدي الذكاء الاصطناعي الإسلامي، المسار المفتوح)
- **Build window / فترة البناء:** 4 Oct 2026 09:00 to 6 Oct 2026 23:59, UTC+3 (من 4 أكتوبر 2026 الساعة 09:00 إلى 6 أكتوبر 2026 الساعة 23:59 بتوقيت الرياض)
- **Status of this file / حالة الملف:** written on 4 Oct 2026, mid-window, and completed on 6 Oct 2026 for the submission. Where this repository does not document a fact, the file says so. / كُتب في 4 أكتوبر 2026 أثناء فترة البناء، واستُكمل في 6 أكتوبر 2026 للتسليم. وحيث لا يوثّق المستودع أمرًا، يذكر الملف ذلك.

Why this file exists: the rules judge only work done inside the window, and undisclosed pre-existing work is a disqualifier. So this file says plainly what existed on the first morning, what was built afterwards, and which outside services and tools we use.

سبب وجود هذا الملف: تُحكَّم الأعمال المنجزة داخل فترة البناء وحدها، والعمل السابق غير المُفصَح عنه سبب للاستبعاد. لذلك يبيّن هذا الملف بوضوح ما كان موجودًا صباح اليوم الأول، وما بُني بعده، وما نستخدمه من خدمات وأدوات خارجية.

---

# Part 1 (English)

## 1. Summary

Al-Sadiq Al-Sadouq started as a university capstone project, finished before the challenge opened. We reuse that product as the base and we do not count it as challenge work. The challenge work is the set of commits made from `e7c98a3` onward, on 4 Oct 2026.

## 2. Pre-existing work (not part of the judged work)

### 2.1 The capstone product

| Item | What it was on 4 Oct 2026 before 09:00 | Where |
|---|---|---|
| Product | A voice and text AI companion for children aged 6 to 13, v1 focused on the value of honesty, with a parent dashboard. | whole repo |
| Origin | Graduation capstone built before the challenge by the original capstone team. The history of our private working repository, from the first commit `de9ce72` (29 Jan 2026) to the last capstone code commit `0241d4d` (4 Jul 2026), records 79 commits (merges included) by four authors: 96as (67), 3moori7 (5), Abdulaziz Altamimi (4) and MADm10d (3) (`git shortlog -sn 0241d4d`; the public repository does not carry this history, see section 3). These are the author names git records for the four GitHub accounts. 96as is the GitHub account of Abdulrahman Salamah, the hackathon team lead (team table in `AGENTS.md`); the repository does not link the other three accounts to any member of the hackathon team. Per the team lead, 6 Oct: since day one, the idea belonged to the lead, Abdulrahman Salamah, and his GitHub account (96as); after the capstone, his capstone teammates (3moori7, Abdulaziz Altamimi and MADm10d) agreed that they keep the credit for the code they worked on, so they can show that code, but not for the idea. The git history also has `77ace9d` "merge develop into production" on 9 May 2026. | git history (`de9ce72` to `0241d4d`), `AGENTS.md`, the team lead (6 Oct) |
| Backend | Django 5.2, DRF, Postgres, JWT login, child and parent accounts, conversations, gamification (quests, badges), moral-context knowledge bank (19 references, English only, no grading metadata), reports and notifications. | `backend/` |
| Voice agent | LiveKit agent with OpenAI speech-to-text and LLM, xAI Grok text-to-speech through a custom WebSocket client (`xai_tts_streaming.py`, voice `leo`), a safety prompt, a tool to look up references. ElevenLabs was not used yet: it was added in the window (section 3.1, task 07). | `backend/conversation/agent/` (`entrypoint.py` at `e7c98a3^` imports the xAI client) |
| Web app | React 19, Vite, Tailwind, React Three Fiber avatar, child and parent screens, English only. | `frontend/` |
| Mobile app | In development: a development build only. It is not part of the submission and is not published in the public repository (lead's decision, 6 Oct). | not in the public repository |
| Deployment files | Docker Compose, a production compose file, Caddy, a deploy workflow. | `docker-compose*.yml`, `infra/` |
| Last capstone code commit | `0241d4d`, 4 Jul 2026. | git history |
| Documents | README, architecture diagram, budget plan, mobile audit, gamification notes, commercial plan. | `docs/` |

The full audit of this starting point is `docs/hackathon/CURRENT_STATE.md`. It was committed at 08:43 on 4 Oct, just before the window opened (commit `e190c25`, section 2.2), and describes the product before any challenge work.

### 2.2 Two documentation commits before the window opened

Two commits by the lead are dated 4 Oct 2026 at 08:43, before the window opened at 09:00. They are work-in-progress documents and a cleanup, not product code, and we treat them as pre-existing:

- `e190c25` (work-in-progress hackathon documents and plan): adds `CURRENT_STATE.md`, `IDEA_DESCRIPTION.md` and the commercial production plan
- `afa6568` "chore: stop tracking generated graphify-out and .DS_Store"

The first window commit is `e7c98a3` (4 Oct 2026, 11:21, "team AI setup, plan and task files"). In the private working repository, `git log e7c98a3^..HEAD` gives the boundary; the public repository is a single-commit copy without this history (section 3).

### 2.3 The 3D avatar

| Item | Detail |
|---|---|
| What | The 3D squirrel companion Al-Sadiq (the web GLB model `avatar-round7.glb`, one skinned mesh of about 1 million triangles, 43 MB, no morph targets, no animations). |
| Origin | Existed before the window. The mesh was generated with the Tripo 3D generation service and then worked on in Blender. The capstone report describes the avatar as designed in Blender. This repository does not record who generated the mesh, or which Tripo plan and terms applied to it; the team lead confirms on request. |
| What we did in the window | We did not redraw the character. We built a reproducible script that compresses the existing model for the web, and added code-driven motion on its existing bones (see section 3, task 06). The original file was never edited. It was removed from `frontend/public/` in `aa118be` (every build copied it into `dist`) and stays in git history. The avatar the product loads today is the animated `avatar-animated.glb` (2,480,896 bytes; `handoffs/product-web.md` section 13). It entered the repository in the window in `c0e3b00` (4 Oct) and was updated in `2e8ff23`, `952321a`, `7d0014d` (4 Oct) and `42e1198` (5 Oct) (`git log -- frontend/public/models/avatar/avatar-animated.glb`). |

### 2.4 Images and fonts

| Item | Status |
|---|---|
| Background and badge images (`frontend/public/backgrounds`, `badges`, `child-quests`) | Existed before the window. The painted meadow backgrounds in `frontend/public/backgrounds` are AI-generated images (task 06b handoff); the meadow `fantasy-meadow.webp` was generated by the team lead with World Labs (Marble) (lead, 6 Oct). In the window, task 06b added `fantasy-meadow-1600.webp`, a smaller copy of the same painting, as the forest backdrop. The badge and quest images were first committed on 12 Apr 2026 (`04528b3`). How the badge, quest and other background images were made, and the terms of the tools used, are not documented in this repository; the team lead confirms on request. |
| Manrope font | Google Fonts, SIL Open Font License. Existed before the window. |
| Arabic fonts added in the window | Amiri, Amiri Quran, Baloo Bhaijaan 2 and IBM Plex Sans Arabic, loaded from Google Fonts (`frontend/index.html`; added in `062ecfe`, `bb344ba` and `ca7bee5`, 4 and 5 Oct), all under the SIL Open Font License. The King Fahd Complex Quran font is not bundled (`frontend/public/fonts/README.txt`). |
| Quran and hadith English translations in the capstone fixture | Existed before the window. The new content bank (task 01) is merged into the product branch, and the voice agent now reads only the bank (`backend/conversation/agent/retrieval.py`, servable `ContentItem` rows); no agent code reads the old fixture, which stays in the repo with its seed command and admin page. The challenge build does not use them as a source; the new bank takes its texts only from the approved sources (see `SOURCES-REGISTER.md`). The old fixture is kept (`backend/session_moral_context/fixtures/islamic_knowledge_base.json`). It cites the hadith and verse references but not the English translation it uses, so the translation's licence is not documented in this repository. |

### 2.5 Libraries, kits and tools that existed before the window

| Item | Use | Licence (as each project publishes it; no licence-scanner report is in this repository) |
|---|---|---|
| Django, Django REST framework, SimpleJWT, Celery, gunicorn, whitenoise, psycopg2 | Backend | BSD, MIT, LGPL |
| React, Vite, Tailwind, three.js, React Three Fiber, drei, axios, lucide-react | Web | MIT, ISC |
| GSAP | Web animation | GSAP 3.15 (`frontend/package.json`); the package's licence field reads "Standard 'no charge' license: https://gsap.com/standard-license" (not an OSI licence) |
| LiveKit server, Agents SDK, client SDKs | Realtime voice | Apache-2.0 |
| Silero VAD | Voice activity detection, through the LiveKit Silero plugin (`livekit-agents[silero]==1.5.1` in `backend/requirements.agent.txt`) | MIT (the `snakers4/silero-vad` repository); the LiveKit Agents repository is Apache-2.0 |
| Vendored agent skills (`skills-lock.json`: LiveKit agent skills, Expo skills, R3F skills) | Developer guidance for coding assistants, not shipped to users | `livekit/agent-skills` and `expo/skills`: MIT. `EnzeD/r3f-skills` publishes no licence on GitHub. |

## 3. Built in the window

Everything below was built after the window opened. Commit SHAs are from the private working repository and name each task's main commits; the full history is `git log e7c98a3^..HEAD` there. The public repository is a fresh, single-commit copy of the private repository and does not carry its history; its `docs/PROVENANCE.md` names the private commit it was made from. Times are 4 Oct 2026, UTC+3. **Merged** means on the shared `hackathon` branch.

### 3.1 First tasks (4 Oct)

| Task | Work | Commits | Status |
|---|---|---|---|
| 00 Setup | Team AI setup (agent roles, plan and task files, shared instructions) | `e7c98a3` | merged |
| 06 Avatar | Optimised the avatar for the web: 43 MB down to 0.69 MB, loaded from a preview server in 0.85 s on a throttled link instead of 38.8 s (download and parse only), avatar drawn about 0.53 s after the voice screen mounts (warm cache); idle breathing and gaze, a pose for each agent state, and a jaw driven by the real voice level. The 0.69 MB file is no longer shipped (`94332b8`); the product loads the animated avatar (section 2.3) | `9f2b77c`, `8aeb1f7`, `986fcbe`, `08058c3`, `833e95f` | merged |
| 06b Forest | An opt-in 3D forest scene behind the avatar (React Three Fiber, with a built-in procedural forest), and a contract for loading a Blender-made forest if one is supplied. No third-party 3D assets were added. The look was inspired by the MOLI's Little Room web scene (CC BY-NC): ideas only, no code or assets copied. No Blender forest file is in the repository (`frontend/public/models/forest/` holds only its `README.md`), so the product uses the built-in procedural forest. | `d6ddb72`, `cd2bf27`, `5985b07`, `5a42f8c`, `5c221c6`, `a2d4105` | merged |
| 07 Voice | ElevenLabs text-to-speech (model `eleven_flash_v2_5`), the default voice provider, replacing the capstone's xAI Grok voice, which stays only as a manual operator rollback (`TTS_PROVIDER=xai`, `tts_factory.py`); a text cleaner for speech with a Quran bracket guard (112 unit tests), wired into the agent while keeping the original transcript; voice audition and speech-to-text comparison tools | `605da56`, `b2b5448`, `63ed2f3`, `56d7231`, `c68d460`, `210f70d`, `547e103` (merge), `e3f11ba`, `c5fea9d`, `3552256` | merged |
| 10 Demo | One-tap demo start: a pool of synthetic Arabic families, each with a made-up week, given to a visitor for 45 minutes (`DEMO_MODE`, `POST /api/demo/start`, `POST /api/demo/reset`). 8 families in `516bbe8`, raised to 40 for judging day in `9fe104f` (`handoffs/pw-ops.md`). The demo landing page is committed (`bb344ba`, `481dba1`). | `516bbe8`, `bb344ba`, `481dba1`, `9fe104f` | merged |
| 10 Production | `/api/health/` (database and Redis), safer admin seeding, `/admin` limited to allowed IPs in Caddy, hosts and CORS from the environment, agent idle process setting | `3d8f355`, `8334170` (reviewer fixes) | merged |

Test status at the end of the 5 Oct pre-deploy round (`handoffs/product-web.md` sections 18.4 and 18.5): the full backend suite on the SQLite test settings ran 1330 tests, OK (the threaded start-race test is skipped on SQLite); the `conversation` suite on Postgres 16 ran 1133 tests, OK, 3 skipped. (The voice task had reported 251 tests at `c5fea9d`; that figure is superseded.) These figures are from that 5 Oct round.

### 3.2 Other tasks in the window

These rows were written as the plan on 4 Oct. What was built, and its limits, is described in `docs/hackathon/deliverables/known-limitations.md`.

| Task | Work |
|---|---|
| 01 Content bank | A `ContentItem` bank that stores each verse, hadith and explanation with its source, grade and status; Arabic text. |
| 02 Sources | Filling the bank from approved sources only, with a register entry for every item. |
| 03 Grounding | Retrieval before every answer and an answer, simplify, refer or decline decision; no source, no answer. |
| 04 Parent view | A fix for the raw-text preview; the "Sources discussed this week" section and AI labels on the parent Insights page (PR #59), with this week's sources seeded for the demo families (PR #58). |
| 05 Child UI | Source card and recitation audio for verses; Arabic web interface. |
| 08 Latency | Faster first reply. Measured at 1 to 10 simultaneous sessions (`docs/hackathon/latency/LOAD-REHEARSAL.md`); there is no comparable before-and-after figure. |
| 09 Evaluation | A safety and grounding test set, with a report. |

We claim nothing in this table beyond what that file and the code show.

## 4. Third-party services used at run time

| Service | Provider | What it does here | Data it sees | Notes |
|---|---|---|---|---|
| OpenAI API | OpenAI | Speech-to-text (gpt-4o-transcribe family), the language model that writes answers (gpt-5.x family), and the background reports: session report, rolling memory summary, quest suggestions and the weekly parent summary | The child's spoken or typed words, and the session's messages for the reports | Commercial API terms. Demo data is synthetic only. |
| ElevenLabs | ElevenLabs | Text-to-speech for Al-Sadiq's voice (model `eleven_flash_v2_5`). Optional Scribe speech-to-text, off by default. | Only the text Al-Sadiq is about to say (and the child's audio, only if Scribe is switched on) | Used from 4 Oct. Verse text inside the Quran brackets is replaced by a neutral phrase before speech, so it is not sent. |
| xAI Grok text-to-speech | xAI | The capstone's voice before the window. Now a manual operator rollback only, off by default (`TTS_PROVIDER=xai`) | Only the text Al-Sadiq is about to say, and only when an operator switches it on | Pre-existing (`backend/conversation/agent/xai_tts_streaming.py`). |
| LiveKit Cloud and the LiveKit Agents framework | LiveKit | Realtime audio rooms between the browser and the voice agent | Audio streams of the session | Apache-2.0 SDKs, commercial cloud. |
| Hosting | DigitalOcean (server), Caddy (proxy and TLS) | Runs the live demo | Application data (synthetic) | One droplet with 8 GB RAM and 180 GB SSD (lead, 4 Oct). The droplet's region is not recorded in this repository. |
| Email | A transactional email service (Mailtrap in the capstone) | Parent account emails | Parent email address | By default emails are only printed to the server console (`EMAIL_BACKEND` in `backend/config/settings.py`); SMTP sending needs it set in the server's environment. The production template `.env.production.example` does not set it, and `docs/hackathon/DEPLOY-CHECKLIST.md` lists SMTP as not needed for the demo. The demo server's own settings are not recorded in this repository. |

## 5. AI tools used to build it

Claude Code (Anthropic) was the main development assistant, with Opus 5.5 as the planning and review session and Sonnet and Haiku as sub-agents for coding, search and notes. Some team members also use OpenAI Codex (with `codex-plugin-cc`). AI assistants also wrote first versions of documents, including this one, which a team member reviews before submission. The log of tools and what each did is `docs/hackathon/deliverables/ai-tools-log.md`. Each task branch is reviewed before it is merged into the shared branch. Content rules were written for the agents: they may not write Quran or hadith text from memory, and may use only the approved sources.

## 6. Source of religious content

The rule for the challenge build is that all religious text and rulings come from the approved sources and nowhere else (names in `SOURCES-REGISTER.md`). No verse or hadith text was written into code, prompts or tests in the window. The one older store of such text that we know of is the capstone fixture (section 2.4).

## 7. Rights and open points

1. **Licence.** Decided by the lead on 5 Oct: the repository is all rights reserved for the team's own code and documents (root `LICENSE`: "Copyright (c) 2026 the Al-Sadiq Al-Sadouq team. All rights reserved."). Third-party content is not covered by that notice and stays under its owners' terms (README section 8, `docs/hackathon/deliverables/sources.md`). The capstone repository started with an MIT licence ("Copyright (c) 2026 96as", added in the first commit `de9ce72` on 29 Jan 2026); it was replaced by the current notice in `4dfc524` on 5 Oct 2026. The same file lets the judges of the Islamic AI Challenge 2026 read, build and test the repository for judging; all other rights are reserved.
2. **Capstone rights.** The capstone code (section 2.1) was written before the window by the four GitHub accounts in its git history. The team lead, Abdulrahman Salamah (96as), is one of them. His statement (6 Oct): "The capstone code is reused with the agreement of the capstone team; the idea and the project belong to the lead, who maintains it."
3. **Avatar.** Origin and generation terms, see 2.3: who generated the mesh and the Tripo terms are not documented in this repository.
4. **Images and badges.** See 2.4: how the badge, quest and background images were made, other than the meadow painting, is not documented in this repository.
5. **Recitation audio.** The verse cards stream Mahmoud Khalil Al-Husary's recordings from everyayah.com, credited with a link on every card, a source the organisers accepted on 5 Oct; the same 74 clips are stored in the repository (`docs/hackathon/deliverables/known-limitations.md`). The recordings' licence is not documented in this repository.
6. **Third-party licences.** As each project publishes them (section 2.5). No licence-scanner report is in this repository.

---

# الجزء الثاني (بالعربية)

## 1. ملخص

بدأ مشروع «الصديق الصدوق» مشروع تخرج جامعيًّا، اكتمل قبل افتتاح المسابقة. نستخدم ذلك المنتج أساسًا للعمل، ولا نحتسبه من أعمال المسابقة. أما أعمال المسابقة فهي الإيداعات (commits) المنجزة ابتداءً من الإيداع `e7c98a3` في 4 أكتوبر 2026.

## 2. الأعمال السابقة (ليست ضمن العمل المُحكَّم)

### 2.1 منتج مشروع التخرج

| البند | حالته صباح 4 أكتوبر 2026 قبل الساعة 09:00 | الموضع |
|---|---|---|
| المنتج | رفيق ذكاء اصطناعي صوتي ونصي للأطفال من عمر 6 إلى 13 سنة، تركّز نسخته الأولى على قيمة الصدق، مع لوحة تحكم لأولياء الأمور. | المستودع كاملًا |
| الأصل | مشروع تخرج أنجزه فريق المشروع الأصلي قبل المسابقة. ويسجّل سجل المستودع الخاص الذي نعمل فيه، من أول إيداع `de9ce72` (29 يناير 2026) إلى آخر إيداع برمجي لمشروع التخرج `0241d4d` (4 يوليو 2026)، 79 إيداعًا (بما فيها إيداعات الدمج) لأربعة مؤلفين: 96as (67) و3moori7 (5) وAbdulaziz Altamimi (4) وMADm10d (3) (الأمر `git shortlog -sn 0241d4d`؛ ولا يحمل المستودع العام هذا السجل، انظر القسم 3). وهذه أسماء المؤلفين كما يسجّلها git للحسابات الأربعة على GitHub. والحساب 96as على GitHub هو حساب عبدالرحمن سلامة، قائد فريق المسابقة (جدول الفريق في `AGENTS.md`)، ولا يربط المستودع الحسابات الثلاثة الأخرى بأي عضو في فريق المسابقة. وبحسب قائد الفريق (6 أكتوبر): كانت الفكرة منذ اليوم الأول لقائد الفريق عبدالرحمن سلامة ولحسابه على GitHub (96as)، وبعد انتهاء مشروع التخرج اتفق زملاؤه فيه (3moori7 وAbdulaziz Altamimi وMADm10d) على أن يُنسب إليهم ما عملوا عليه من الشيفرة ليعرضوه، دون الفكرة. وفي سجل git أيضًا الإيداع `77ace9d` «merge develop into production» بتاريخ 9 مايو 2026. | سجل git (من `de9ce72` إلى `0241d4d`)، `AGENTS.md`، قائد الفريق (6 أكتوبر) |
| الخلفية (Backend) | Django 5.2 وDRF وPostgres، وتسجيل دخول JWT، وحسابات الأطفال والأهل، والمحادثات، والتحفيز (مهمات وأوسمة)، وقاعدة معرفة للسياق الأخلاقي (19 مرجعًا بالإنجليزية فقط، دون بيانات عن درجة الأحاديث)، والتقارير والإشعارات. | `backend/` |
| الوكيل الصوتي | وكيل LiveKit مع تحويل الكلام إلى نص ونموذج لغوي من OpenAI، وتحويل النص إلى كلام من xAI Grok عبر عميل WebSocket خاص (`xai_tts_streaming.py`، الصوت `leo`)، وتعليمات للسلامة، وأداة للبحث عن المراجع. ولم يكن ElevenLabs مستخدمًا بعد، فقد أُضيف داخل الفترة (القسم 3.1، المهمة 07). | `backend/conversation/agent/` (الملف `entrypoint.py` عند `e7c98a3^` يستورد عميل xAI) |
| تطبيق الويب | React 19 وVite وTailwind، وشخصية ثلاثية الأبعاد بمكتبة React Three Fiber، وشاشات للطفل والأهل بالإنجليزية فقط. | `frontend/` |
| تطبيق الجوال | قيد التطوير، وهو نسخة تطوير فقط، وليس جزءا من التسليم، ولا ينشر في المستودع العام (قرار قائد الفريق، 6 أكتوبر). | ليس في المستودع العام |
| ملفات النشر | Docker Compose، وملف إنتاج، وCaddy، وسير عمل للنشر. | `docker-compose*.yml`، `infra/` |
| آخر إيداع برمجي لمشروع التخرج | `0241d4d` بتاريخ 4 يوليو 2026. | سجل git |
| الوثائق | README، ومخطط المعمارية، وخطة الميزانية، ومراجعة تطبيق الجوال، وملاحظات التحفيز، والخطة التجارية. | `docs/` |

يوجد تدقيق كامل لنقطة البداية هذه في الملف `docs/hackathon/CURRENT_STATE.md`. أُودِع الساعة 08:43 يوم 4 أكتوبر، قُبيل افتتاح الفترة (الإيداع `e190c25`، انظر 2.2)، ويصف المنتج قبل أي عمل للمسابقة.

### 2.2 إيداعان وثائقيان قبل افتتاح الفترة

يحمل إيداعان من قائد الفريق تاريخ 4 أكتوبر 2026 الساعة 08:43، أي قبل افتتاح الفترة عند 09:00. وهما وثائق قيد الإعداد وتنظيف، وليسا شيفرة منتج، ونعدّهما عملًا سابقًا:

- `e190c25` (وثائق المسابقة والخطة قيد الإعداد): يضيف `CURRENT_STATE.md` و`IDEA_DESCRIPTION.md` والخطة التجارية للإنتاج
- `afa6568` «chore: stop tracking generated graphify-out and .DS_Store»

أول إيداع داخل الفترة هو `e7c98a3` (4 أكتوبر 2026، الساعة 11:21، «إعداد الفريق بالذكاء الاصطناعي والخطة وملفات المهام»). وفي المستودع الخاص الذي نعمل فيه يعطي الأمر `git log e7c98a3^..HEAD` الحدّ الفاصل، أما المستودع العام فنسخة من إيداع واحد دون هذا السجل (انظر القسم 3).

### 2.3 الشخصية ثلاثية الأبعاد

| البند | التفصيل |
|---|---|
| ما هي | رفيق «الصديق» السنجاب ثلاثي الأبعاد (نموذج GLB للويب باسم `avatar-round7.glb`، شبكة واحدة مُهيكلة من نحو مليون مثلث، حجمها 43 ميغابايت، دون أهداف تشكيل ودون حركات). |
| الأصل | كانت موجودة قبل الفترة. وُلّدت الشبكة بخدمة Tripo لتوليد النماذج ثلاثية الأبعاد ثم عُولجت في Blender. ويصف تقرير مشروع التخرج الشخصية بأنها صُمّمت في Blender. ولا يسجّل هذا المستودع من ولّد الشبكة، ولا خطة Tripo وشروطها التي انطبقت عليها، ويؤكد قائد الفريق ذلك عند الطلب. |
| ما فعلناه في الفترة | لم نُعد رسم الشخصية. بنينا سكربتًا قابلًا للإعادة يضغط النموذج الموجود للويب، وأضفنا حركة برمجية على عظامه الموجودة (انظر القسم 3، المهمة 06). ولم يُعدَّل الملف الأصلي قط، وقد أُزيل من `frontend/public/` في الإيداع `aa118be` (لأن كل بناء كان ينسخه إلى `dist`)، ويبقى في سجل git. أما الشخصية التي يحمّلها المنتج اليوم فهي النموذج المتحرك `avatar-animated.glb` (بحجم 2,480,896 بايت؛ `handoffs/product-web.md` القسم 13). ودخل المستودع داخل الفترة في الإيداع `c0e3b00` (4 أكتوبر)، وحُدّث في `2e8ff23` و`952321a` و`7d0014d` (4 أكتوبر) و`42e1198` (5 أكتوبر) (الأمر `git log -- frontend/public/models/avatar/avatar-animated.glb`). |

### 2.4 الصور والخطوط

| البند | الحالة |
|---|---|
| صور الخلفيات والأوسمة (`frontend/public/backgrounds` و`badges` و`child-quests`) | كانت موجودة قبل الفترة. ولوحات المرج المرسومة في `frontend/public/backgrounds` صور مولَّدة بالذكاء الاصطناعي (بحسب ملف تسليم المهمة 06b)، والمرج `fantasy-meadow.webp` ولّده قائد الفريق بأداة World Labs (Marble) (قائد الفريق، 6 أكتوبر). وأضافت المهمة 06b داخل الفترة الملف `fantasy-meadow-1600.webp`، وهو نسخة أصغر من اللوحة نفسها، خلفيةً لمشهد الغابة. وأُودعت صور الأوسمة والمهمات أول مرة في 12 أبريل 2026 (الإيداع `04528b3`). أما كيف صُنعت صور الأوسمة والمهمات والخلفيات الأخرى، وشروط الأدوات المستخدمة، فلا يوثّقها هذا المستودع، ويؤكدها قائد الفريق عند الطلب. |
| خط Manrope | من Google Fonts برخصة SIL للخطوط المفتوحة. كان موجودًا قبل الفترة. |
| الخطوط العربية المضافة في الفترة | Amiri وAmiri Quran وBaloo Bhaijaan 2 وIBM Plex Sans Arabic، تُحمَّل من Google Fonts (الملف `frontend/index.html`؛ أُضيفت في الإيداعات `062ecfe` و`bb344ba` و`ca7bee5` يومي 4 و5 أكتوبر)، وكلها برخصة SIL للخطوط المفتوحة. ولم يُضمَّن خط مجمع الملك فهد للمصحف (`frontend/public/fonts/README.txt`). |
| الترجمات الإنجليزية للقرآن والحديث في بيانات مشروع التخرج | كانت موجودة قبل الفترة. وقد دُمج بنك المحتوى الجديد (المهمة 01) في فرع المنتج، وصار الوكيل الصوتي يقرأ من البنك وحده (`backend/conversation/agent/retrieval.py`، صفوف `ContentItem` القابلة للعرض)، ولا تقرأ أي شيفرة في الوكيل البيانات القديمة، وهي باقية في المستودع مع أمر تعبئتها وصفحتها في لوحة الإدارة. ولا يعتمدها بناء المسابقة مصدرًا، إذ يأخذ البنك الجديد نصوصه من المصادر المعتمدة وحدها (انظر `SOURCES-REGISTER.md`). وقد أُبقيت البيانات القديمة (`backend/session_moral_context/fixtures/islamic_knowledge_base.json`)، وهي تذكر مراجع الأحاديث والآيات دون الترجمة الإنجليزية المستخدمة، فلا يوثّق هذا المستودع رخصة تلك الترجمة. |

### 2.5 المكتبات والحزم والأدوات السابقة للفترة

| البند | الاستخدام | الرخصة (كما ينشرها كل مشروع؛ ولا يوجد في هذا المستودع تقرير من أداة فحص رخص) |
|---|---|---|
| Django وDjango REST framework وSimpleJWT وCelery وgunicorn وwhitenoise وpsycopg2 | الخلفية | BSD وMIT وLGPL |
| React وVite وTailwind وthree.js وReact Three Fiber وdrei وaxios وlucide-react | الويب | MIT وISC |
| GSAP | حركة الواجهة في الويب | GSAP 3.15 (`frontend/package.json`)، وحقل الرخصة في الحزمة نصه: "Standard 'no charge' license: https://gsap.com/standard-license" (ليست رخصة OSI) |
| خادم LiveKit وحزمة الوكلاء وحزم العميل | الصوت الفوري | Apache-2.0 |
| Silero VAD | كشف النشاط الصوتي، عبر إضافة Silero في LiveKit (`livekit-agents[silero]==1.5.1` في `backend/requirements.agent.txt`) | MIT (مستودع `snakers4/silero-vad`)، ومستودع LiveKit Agents برخصة Apache-2.0 |
| مهارات الوكلاء المضمّنة (`skills-lock.json`: مهارات LiveKit وExpo وR3F) | إرشاد للمساعدين البرمجيين، ولا تصل إلى المستخدمين | `livekit/agent-skills` و`expo/skills`: برخصة MIT. ولا ينشر `EnzeD/r3f-skills` رخصةً على GitHub. |

## 3. ما بُني داخل الفترة

كل ما يلي بُني بعد افتتاح الفترة. رموز الإيداعات (SHA) من المستودع الخاص الذي نعمل فيه، وتسمّي الإيداعات الرئيسة لكل مهمة، والسجل الكامل هناك هو `git log e7c98a3^..HEAD`. أما المستودع العام فنسخة جديدة من إيداع واحد من المستودع الخاص، لا تحمل سجله، ويذكر الملف `docs/PROVENANCE.md` فيها الإيداع الخاص الذي أُخذت منه. الأوقات بتاريخ 4 أكتوبر 2026 بتوقيت الرياض. و**مدموج** يعني أنه على فرع `hackathon` المشترك.

### 3.1 المهام الأولى (4 أكتوبر)

| المهمة | العمل | الإيداعات | الحالة |
|---|---|---|---|
| 00 الإعداد | إعداد الفريق بالذكاء الاصطناعي (أدوار الوكلاء، وملفات الخطة والمهام، والتعليمات المشتركة) | `e7c98a3` | مدموج |
| 06 الشخصية | تحسين الشخصية للويب: من 43 ميغابايت إلى 0.69 ميغابايت، وتحميل في 0.85 ثانية على اتصال مُقيَّد بدل 38.8 ثانية (التنزيل والتحليل فقط)، وظهور الشخصية بعد نحو 0.53 ثانية من فتح شاشة الصوت (والذاكرة المؤقتة دافئة)، وتنفّس ونظرات في حالة السكون، ووضعية لكل حالة من حالات الوكيل، وفك يتحرك بحسب مستوى الصوت الحقيقي. ولم يعد ملف 0.69 ميغابايت يُشحن مع المنتج (`94332b8`)، فالمنتج يحمّل النموذج المتحرك (القسم 2.3) | `9f2b77c` و`8aeb1f7` و`986fcbe` و`08058c3` و`833e95f` | مدموج |
| 06b الغابة | مشهد غابة ثلاثي الأبعاد اختياري خلف الشخصية (بمكتبة React Three Fiber مع غابة مولَّدة برمجيًّا)، ومواصفة (contract) لتحميل غابة مصنوعة في Blender إن وُجدت. لم تُضَف أصول ثلاثية الأبعاد من جهات خارجية، واستُلهم الطابع من مشهد الويب MOLI's Little Room (برخصة CC BY-NC) فكرةً فقط، دون نسخ شيفرة أو أصول. ولا يوجد في المستودع ملف غابة من Blender (المجلد `frontend/public/models/forest/` لا يحوي إلا ملف `README.md`)، فيستخدم المنتج الغابة المولَّدة برمجيًّا. | `d6ddb72` و`cd2bf27` و`5985b07` و`5a42f8c` و`5c221c6` و`a2d4105` | مدموج |
| 07 الصوت | تحويل النص إلى كلام عبر ElevenLabs (النموذج `eleven_flash_v2_5`) وهو مزوِّد الصوت الافتراضي، بدلًا من صوت xAI Grok في مشروع التخرج، الذي بقي خيار رجوع يدويًّا للمشغّل فقط (`TTS_PROVIDER=xai`، `tts_factory.py`)، ومنظِّف نصوص للكلام مع حارس لأقواس القرآن (112 اختبار وحدة) موصول بالوكيل مع حفظ النص الأصلي للمحادثة، وأدوات لتجربة الأصوات ومقارنة تحويل الكلام إلى نص | `605da56` و`b2b5448` و`63ed2f3` و`56d7231` و`c68d460` و`210f70d` و`547e103` (دمج) و`e3f11ba` و`c5fea9d` و`3552256` | مدموج |
| 10 العرض | بدء العرض بنقرة واحدة: مجموعة من الأسر العربية الاصطناعية لكلٍّ منها أسبوع افتراضي من النشاط، تُخصَّص للزائر مدة 45 دقيقة (`DEMO_MODE` و`POST /api/demo/start` و`POST /api/demo/reset`). كانت 8 أسر في `516bbe8`، ثم رُفعت إلى 40 ليوم التحكيم في `9fe104f` (`handoffs/pw-ops.md`). وصفحة الهبوط للعرض مودَعة (`bb344ba` و`481dba1`). | `516bbe8` و`bb344ba` و`481dba1` و`9fe104f` | مدموج |
| 10 الإنتاج | `/api/health/` (قاعدة البيانات وRedis)، وإنشاء أكثر أمانًا لحساب المدير، وقصر `/admin` على عناوين IP مسموح بها في Caddy، وضبط النطاقات وCORS من متغيرات البيئة، وإعداد عمليات الخمول للوكيل | `3d8f355` و`8334170` (إصلاحات المراجعة) | مدموج |

حالة الاختبارات في نهاية جولة 5 أكتوبر (`handoffs/product-web.md` القسمان 18.4 و18.5): شُغّلت حزمة الخلفية كاملةً على إعدادات SQLite للاختبار: 1330 اختبارًا، نجحت (ويُتخطّى على SQLite اختبار السباق متعدد الخيوط عند بدء الجلسة). وشُغّلت حزمة `conversation` على Postgres 16: 1133 اختبارًا، نجحت، وتخطّت 3. (كانت مهمة الصوت قد أبلغت عن 251 اختبارًا عند `c5fea9d`، وقد حلّ محلها الرقم الجديد.) وهذه الأرقام من جولة 5 أكتوبر تلك.

### 3.2 مهام أخرى في الفترة

كُتبت هذه الصفوف خطةً في 4 أكتوبر. أما ما بُني وحدوده فيصفه الملف `docs/hackathon/deliverables/known-limitations.md`.

| المهمة | العمل |
|---|---|
| 01 بنك المحتوى | بنك `ContentItem` يحفظ كل آية وحديث وشرح مع مصدره ودرجته وحالته، ونصٌّ عربي. |
| 02 المصادر | ملء البنك من المصادر المعتمدة وحدها، مع سجل لكل بند. |
| 03 التأصيل | استرجاع قبل كل إجابة، وقرار بين الإجابة والتبسيط والإحالة والاعتذار؛ لا مصدر فلا جواب. |
| 04 عرض الأهل | إصلاح المعاينة التي تُظهر النص الخام، وقسم «المصادر التي نوقشت هذا الأسبوع» ووسوم الذكاء الاصطناعي في صفحة الرؤى للأهل (PR #59)، مع تعبئة مصادر هذا الأسبوع لأسر العرض (PR #58). |
| 05 واجهة الطفل | بطاقة المصدر وتلاوة صوتية للآيات، وواجهة ويب بالعربية. |
| 08 الزمن | تسريع الرد الأول. قيس عند 1 إلى 10 جلسات متزامنة (`docs/hackathon/latency/LOAD-REHEARSAL.md`)، ولا يوجد رقم قبل وبعد قابل للمقارنة. |
| 09 التقييم | مجموعة اختبارات للسلامة والتأصيل مع تقرير. |

ولا ندّعي في هذا الجدول شيئًا أبعد مما يُظهره ذلك الملف والشيفرة.

## 4. الخدمات الخارجية المستخدمة أثناء التشغيل

| الخدمة | المزوّد | وظيفتها هنا | البيانات التي تراها | ملاحظات |
|---|---|---|---|---|
| واجهة OpenAI | OpenAI | تحويل الكلام إلى نص (عائلة gpt-4o-transcribe)، والنموذج اللغوي الذي يكتب الإجابات (عائلة gpt-5.x)، والتقارير الخلفية: تقرير الجلسة، والملخص التراكمي للذاكرة، واقتراح المهمات، والملخص الأسبوعي للأهل | كلمات الطفل المنطوقة أو المكتوبة، ورسائل الجلسة لإعداد التقارير | شروط الواجهة التجارية. بيانات العرض اصطناعية فقط. |
| ElevenLabs | ElevenLabs | تحويل النص إلى كلام بصوت الصديق (النموذج `eleven_flash_v2_5`)، وخيار تحويل الكلام إلى نص عبر Scribe، وهو معطَّل افتراضيًّا | النص الذي سينطقه الصديق فقط (وصوت الطفل، إن فُعِّل Scribe فقط) | مستخدمة منذ 4 أكتوبر. يُستبدَل نص الآية الواقع بين أقواس القرآن بعبارة محايدة قبل النطق، فلا يُرسَل إليها. |
| تحويل النص إلى كلام من xAI Grok | xAI | صوت مشروع التخرج قبل الفترة. وهو اليوم خيار رجوع يدوي للمشغّل فقط، معطَّل افتراضيًّا (`TTS_PROVIDER=xai`) | النص الذي سينطقه الصديق فقط، وحين يفعّله المشغّل فقط | سابق للفترة (`backend/conversation/agent/xai_tts_streaming.py`). |
| LiveKit Cloud وإطار LiveKit Agents | LiveKit | غرف صوتية فورية بين المتصفح والوكيل الصوتي | تدفقات صوت الجلسة | حزم برخصة Apache-2.0 وسحابة تجارية. |
| الاستضافة | DigitalOcean (الخادم) وCaddy (الوكيل العكسي وTLS) | تشغيل العرض الحي | بيانات التطبيق (اصطناعية) | خادم واحد بذاكرة 8 غيغابايت وتخزين SSD سعته 180 غيغابايت (بحسب قائد الفريق، 4 أكتوبر). ولا يسجّل هذا المستودع منطقة الخادم. |
| البريد الإلكتروني | خدمة بريد معاملات (Mailtrap في مشروع التخرج) | رسائل حسابات الأهل | البريد الإلكتروني لولي الأمر | تُطبع الرسائل افتراضيًّا في سجل الخادم فقط (`EMAIL_BACKEND` في `backend/config/settings.py`)، ويحتاج الإرسال عبر SMTP إلى ضبطه في بيئة الخادم. ولا يضبطه قالب الإنتاج `.env.production.example`، ويذكر الملف `docs/hackathon/DEPLOY-CHECKLIST.md` أن SMTP غير مطلوب للعرض. أما إعدادات خادم العرض نفسه فلا يسجّلها هذا المستودع. |

## 5. أدوات الذكاء الاصطناعي المستخدمة في البناء

كان Claude Code من Anthropic المساعد الرئيس في التطوير، وتولّت جلسة Opus 5.5 التخطيط والمراجعة، وعمل Sonnet وHaiku وكلاء فرعيين للبرمجة والبحث وتدوين الملاحظات. ويستخدم بعض أعضاء الفريق أيضًا OpenAI Codex (مع `codex-plugin-cc`). وكتبت المساعدات الذكية الصيغ الأولى للوثائق أيضًا، ومنها هذا الملف، ويراجعها عضو من الفريق قبل التسليم. وسجل الأدوات وما فعلته كل أداة في الملف `docs/hackathon/deliverables/ai-tools-log.md`. ويُراجَع فرع كل مهمة قبل دمجه في الفرع المشترك. وُضعت قواعد محتوى للوكلاء: لا يكتبون نص آية أو حديث من الذاكرة، ولا يستخدمون إلا المصادر المعتمدة.

## 6. مصدر المحتوى الشرعي

القاعدة في بناء المسابقة أن يُؤخذ كل نص شرعي وكل حكم من المصادر المعتمدة وحدها (أسماؤها في `SOURCES-REGISTER.md`). ولم يُكتب داخل الفترة نص آية أو حديث في الشيفرة أو التعليمات أو الاختبارات. والموضع القديم الوحيد المعروف لنا لمثل هذه النصوص هو بيانات مشروع التخرج (انظر 2.4).

## 7. الحقوق والنقاط المفتوحة

1. **الرخصة.** قرّر قائد الفريق في 5 أكتوبر أن جميع الحقوق محفوظة لشيفرة الفريق ووثائقه (ملف `LICENSE` في جذر المستودع: "Copyright (c) 2026 the Al-Sadiq Al-Sadouq team. All rights reserved."، أي: حقوق النشر 2026 لفريق «الصديق الصدوق»، وجميع الحقوق محفوظة). ولا يشمل هذا الإشعار المحتوى الخارجي، فيبقى على شروط أصحابه (القسم 8 من `README.md`، و`docs/hackathon/deliverables/sources.md`). وقد بدأ مستودع مشروع التخرج برخصة MIT ("Copyright (c) 2026 96as"، أُضيفت في أول إيداع `de9ce72` بتاريخ 29 يناير 2026)، ثم حلّ محلها الإشعار الحالي في الإيداع `4dfc524` بتاريخ 5 أكتوبر 2026. ويأذن الملف نفسه لمحكّمي تحدي الذكاء الاصطناعي الإسلامي 2026 بقراءة المستودع وبنائه واختباره لغرض التحكيم، وما عدا ذلك فجميع الحقوق محفوظة.
2. **حقوق مشروع التخرج.** كتب شيفرةَ مشروع التخرج (القسم 2.1) قبل الفترة أصحابُ حسابات GitHub الأربعة المسجَّلة في سجل git، ومنهم قائد الفريق عبدالرحمن سلامة (96as). ونص بيانه (6 أكتوبر): «يُعاد استخدام شيفرة مشروع التخرج بموافقة فريق مشروع التخرج، أما الفكرة والمشروع فهما لقائد الفريق، وهو الذي يتولى صيانة المشروع.»
3. **الشخصية.** الأصل وشروط التوليد، انظر 2.3: لا يوثّق هذا المستودع من ولّد الشبكة ولا شروط Tripo.
4. **الصور والأوسمة.** انظر 2.4: لا يوثّق هذا المستودع كيف صُنعت صور الأوسمة والمهمات والخلفيات، عدا لوحة المرج.
5. **التلاوة الصوتية.** تبثّ بطاقات الآيات تسجيلات الشيخ محمود خليل الحصري من موقع everyayah.com، مع رابط إليه على كل بطاقة، وهو مصدر قبله المنظّمون في 5 أكتوبر، والمقاطع نفسها (74 مقطعًا) محفوظة في المستودع (`docs/hackathon/deliverables/known-limitations.md`). ولا يوثّق هذا المستودع رخصة التسجيلات.
6. **رخص الجهات الخارجية.** كما ينشرها كل مشروع (القسم 2.5). ولا يوجد في هذا المستودع تقرير من أداة فحص رخص.
