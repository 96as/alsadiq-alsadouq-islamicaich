# Judging map

Written 4 Oct 2026. This maps each judging criterion to what we do about it and to the proof a judge can open. Weights add up to 100. The names, weights and 5/5 descriptors come from the participant guide, final-stage criteria (guide pages 37 to 41, checked on 4 Oct). The descriptors are our English translation.

How to use this file: every "proof" row names a thing that must exist at submission. If it does not exist by code freeze (Tue 6 Oct, 13:00), the claim is removed from the deck and the video. Numbers shown as `[TBD]` are measured later and copied in. We do not write a number before it is measured, with one labelled exception: the USD running cost is an estimate (measured units times the providers' public prices of 6 Oct 2026), and every place that shows it says so.

Status key: **have** (exists today on a branch), **building** (a task is on it), **gap** (no work yet).

| # | Criterion (guide name, translated) | Name in the guide | Weight |
|---|---|---|---|
| 1 | Technical quality and use of AI | جودة الحل التقني وتوظيف الذكاء الاصطناعي | 25 |
| 2 | Benefit against the track success criterion (Open Track: the team defines the metric) | تحقيق النفع وفق معيار نجاح المسار | 20 |
| 3 | Reliability and scholarly integrity | الموثوقية والسلامة العلمية | 15 |
| 4 | Innovation and added value | الابتكار والقيمة المضافة | 15 |
| 5 | Beneficiary experience, communication and accessibility | تجربة المستفيد والتواصل والإتاحة | 10 |
| 6 | Operational realism and completion | واقعية التشغيل والاستكمال | 10 |
| 7 | Clarity of presentation and ease of verification | وضوح العرض وإتاحة التحقق | 5 |
| | **Total** | | **100** |

---

## 1. Technical quality and use of AI (25)

**The guide asks:** does the product work stably, and does AI do a real job in it, with a clear method? **5/5:** results repeat consistently, the method and constraints are documented, and there is a verifiable improvement that comes from the chosen use of AI. **4/5:** it works on varied in-scope test cases and handles errors in an understandable way.

**How we score:**
- A retrieval-grounded design: the model may only quote what the bank returns (`ContentItem`, retrieved before each reply), with a decision step (answer, simplify, refer, decline). Status: have, merged in the round-2 integration; 4 of 4 live sessions sent the `reference` event and showed 3 source cards (`handoffs/product-web.md` section 15).
- A realtime voice pipeline: speech-to-text, language model, text-to-speech, with Arabic first. ElevenLabs is the default voice provider; the capstone's xAI Grok client stays only as a manual operator rollback (`TTS_PROVIDER=xai`). Status: have (task 07).
- A speech text cleaner with a guard so Quran brackets never reach the synthesiser (112 unit tests). Status: have.
- Measured latency from the end of the child's question to first audio: about 2.0 to 2.6 s median at 1 to 10 sessions on a local stack, greeting about 3.0 s, longer on turns that call the reference tool. Status: have (see the metric table).
- An evaluation set with a report: grounding, refusal of personal rulings, no invented hadith, child safety. Status: have, first before and after measured on 5 Oct (`docs/hackathon/eval-reports/`).
- Documented limits and failure modes. Status: gap, written at code freeze.
- Repeat runs: run the eval set 3 times on the final build and report the spread, because 5/5 asks for results that repeat. Status: gap. The 5 Oct measurement is one run per side; no repeat spread exists yet.

| Proof to show | Type | Where | Status |
|---|---|---|---|
| Architecture diagram with the grounding step marked | Doc and slide | deck slide 5 (the turn policy and the reviewed bank highlighted); README section 11 | have (6 Oct); `docs/architecture-diagram.png` is the capstone's and was not updated |
| Eval table: cases, pass rate, failures we know about | Metric | [`eval-reports/README.md`](../eval-reports/README.md) and the HTML reports beside it, deck slide 10 (appendix slides 22 and 23 for the quality gate and the lesson-creep proxy) | measured 5 Oct, one run each, text channel, `gpt-5.4-mini` agent, `gpt-6-luna` judge. 186 cases in the set (50 held-out, 136 dev); 160 run live (all held-out plus 110 dev). Strict pass rate over scored runs (17 content-gap runs excluded): held-out 18/41 = 44% (Wilson 95%: 30 to 59), dev sample 69/102 = 68% (58 to 76), both 87/143 = 61% (53 to 68). Policy-only dry run over all 186: 153/158 = 97% (93 to 99). Known failures: `test-question` 2 of 13 scored pass, `translation` 0 of 2, `story-request` 0 of 2, `grounding` 9 of 21. The spoken verse-number defect (8 of 18 English replies named a verse number that was not the served verse) is fixed: round 3 replaced the speech clause so the voice never says a chapter, surah or verse number, and a re-run measured 0 of 45 replies saying any number, plus 0 of 10 in a repeat of the English grounding cases (`handoffs/product-web.md` section 17.1). The remaining judge-tagged `scripture_without_source` counts are the judge's reading, not wrong references. |
| Latency: end of the child's question to first audio | Metric | [`latency/LOAD-REHEARSAL.md`](../latency/LOAD-REHEARSAL.md) and `latency/RESULTS.md`, deck slide 11 | have: about 2.0 to 2.6 s median from the end of the child's question to the first audio, at 1, 5 and 10 simultaneous sessions (local stack, real OpenAI and ElevenLabs, 2-turn sessions; add roughly 0.1 to 0.3 s for a real network). The greeting takes about 3.0 s. Turns that call the reference tool are longer (a second model round, about 2 s more; `latency/RESULTS.md` measured 5.3 s median on the 4-turn script where nearly every turn used the tool). ElevenLabs first byte about 0.2 s. The earlier "1.5 to 2.0 s warm, 3.6 s cold" figure came from four live sessions and is superseded. |
| Test counts | Metric | `manage.py test` output; 1330 backend tests on the SQLite test settings: OK (the threaded start-race test is skipped on SQLite; the skip count was 4 in one run and 1 in another, depending on the environment); the `conversation` suite on Postgres 16: 1133 tests, OK, 3 skipped, which runs that test; and the ten frontend node suites (377 tests in total; `test:meadowstage` 55/55) pass (`handoffs/product-web.md` sections 17.7, 18.4 and 18.5) | have, re-run at freeze |
| "No source, no answer" shown live: a question outside the bank gets a referral, not an invented answer | Screen | judge demo step 5 | building |
| Model and tool choices with reasons | Doc | README "How it works", deck slide 5 (which service does what; no reasons on the slide) | gap |

## 2. Benefit against the track success criterion (20)

**The guide asks:** is there a clear improvement in the target task, backed by verifiable results for the defined audience, against the track's success criterion? **5/5:** the improvement repeats across suitable, varied in-scope cases, and the results and the limits of what they show are documented. **4/5:** a reference comparison shows a clear improvement, with the measurement method shown. In the Open Track the team defines its own problem, audience and impact metric, so we must state ours. Our entry combines trusted dialogue (answers a child can rely on) and interactive learning (the child learns by doing).

**Our metric (proposal, `[team to confirm]`):** on one fixed set of child questions, (a) the share of answers whose religious statements trace to an approved, graded source, and (b) the share of personal-ruling and out-of-bank questions that are correctly referred or declined. Measured **before** (the capstone agent as it was before 09:00 on 4 Oct) and **after** (the final build), with the same questions and the same scoring rules (task 09).

**How we score:**
- Trusted dialogue: every religious statement carries a source card the child can open, and the parent sees a weekly summary, not a transcript, plus the "Sources discussed this week" list (task 04, merged in PR #59). Status: have (tasks 03, 04, 05).
- Interactive learning: a child talks to Al-Sadiq on the painted meadow (the product scene; the 3D forest is an opt-in flag the demo does not use), with quests and badges from the existing gamification. Status: have (meadow stage and avatar merged into `hk/product-web`; quests from the capstone, pre-existing and disclosed).
- Arabic first, ages 6 to 13, with level-appropriate wording. Status: have for the interface (Arabic first and right to left on every child and parent page, `handoffs/product-web.md` sections 12 and 16); the wording of answers depends on the bank and the prompts.
- A complete loop: child question, grounded answer with a source card, parent sees a weekly summary. Status: have; the parent does not see the sources (task 04 is not built).
- Not a prototype: deployed, health-checked, demo accounts seeded. Status: building (task 10).

| Proof to show | Type | Where | Status |
|---|---|---|---|
| Before and after on the same question set: capstone agent vs final build, with the scoring method and the limits of the result | Metric | eval report, deck slide 10 | measured 5 Oct: strict pass rate on the same 160 runs, held-out 25% to 44% (10/40 to 18/41; paired +20.5 points, 95% bootstrap +5.1 to +35.9, p = 0.039), both splits 38% to 61% (54/143 to 87/143; paired +23.4 points, +14.2 to +32.6). Limits: BEFORE is the 01 knowledge-bank branch (it already has the bank), not the original capstone agent; one run each, no repeat spread; team-written cases and a model judge; text channel only. See [`eval-reports/README.md`](../eval-reports/README.md) |
| One unbroken screen recording: child asks, Al-Sadiq answers with a source card, then the parent's weekly summary | Screen | video shots 3 to 5, judge demo steps 3 to 6 | building |
| Source card with source name, grade (for hadith) and a working link | Screen | child screen | have: cards built (`handoffs/product-web.md` section 11) and shown in 4 of 4 live sessions (section 15). The bank holds verses only today (section 16), so no card shows a hadith grade yet |
| Parent "sources discussed" list | Screen | parent dashboard | have: merged in PR #59, seeded for the demo families by PR #58 (README section 2.5, `DEMO.md` step 7b) |
| Quests and badges the child earns | Screen | child screen | have (pre-existing, disclosed) |
| Coverage: how many items, by type and by value, in the bank | Metric | `SOURCES-REGISTER.md` header | building: `seed_content` loads 112 rows (values and items) with 74 reviewed verses and no hadith (`handoffs/product-web.md` section 16, `DEPLOY-CHECKLIST.md` section 1); the count by source and by value is `[TBD]` |

## 3. Reliability and scholarly integrity (15)

**The guide asks:** how sound are the content and the sources, and how well do attribution, abstention and referral work where they are required? **5/5:** consistent performance on the full test set over repeated runs, with limits and errors disclosed so their handling can be tracked. **4/5:** also passes diversity, contradiction and missing-information cases, with clear source tracing and a human review that can actually run.

**How we score:**
- Only approved sources (names are in `SOURCES-REGISTER.md`). A hadith carries book, number, grade, grader and URL. A verse carries surah, ayah and the exact Uthmani text.
- Verses are played as recitation audio, never synthesised.
- Content levels A to D. Level C says only what is agreed, or refers. Level D (personal fatwa) is always referred to a parent or scholar.
- No scripture is written from memory by people or agents, in code, prompts, data or tests.
- Every item has a status (`draft`, `seeded`, `reviewed`) and only the last two can be served.
- A named human reviewer for the content policy. Status: gap, the team must name this person.

| Proof to show | Type | Where | Status |
|---|---|---|---|
| Sources register: every item with source, grade and URL | Doc | `SOURCES-REGISTER.md`, generated from the bank | building (task 02) |
| Content policy: levels A to D, referral wording in Arabic and English | Doc | `docs/CONTENT_POLICY.md` | gap |
| Eval cases for: personal fatwa request, "give me a hadith even if weak", question outside the bank, disputed issue, a misquoted verse, a contradiction, missing information (the sample cases in the challenge reference pack) | Metric | eval report | measured 5 Oct (task 09 runner): `safety` 18/25 = 72% strict (before 12%), `safety-negative` 12/18 = 67% (28%), `invented-hadith` 7/10 = 70% (70%), `misquote` 1/2 (0/2), `out-of-bank` 1/1 scored (1/2), `personal-case` 10/12 = 83% (50%); small counts, see the per-category table in [`eval-reports/README.md`](../eval-reports/README.md) |
| Screen: a personal question gets a warm referral to a parent | Screen | video shot 6, judge demo step 6 | building |
| Spot check: judge picks any source card and follows its link | Screen | judge demo step 4 | building |
| Reviewer sign-off list | Doc | register "Reviewer" column | gap |

## 4. Innovation and added value (15)

**The guide asks:** what is the proven addition compared with a specific alternative or with current practice? **5/5:** a test proves a clear advantage for the addition and states the limits of the comparison. **4/5:** a comparison with a specific alternative shows a worthwhile improvement.

**How we score:**
- A voice companion that is grounded: the child hears the answer and sees where it came from, in the child's own words, and the recitation is the real recitation.
- The parent gets a weekly summary and topics to talk about, not a transcript, which protects the child's privacy and still lets the parent follow up. Status: have. The "Sources discussed this week" list (task 04) is merged (PR #59).
- A realtime animated character reacting to the agent's state (listening, thinking, speaking) with the jaw driven by the real voice level. Status: have (task 06, on a branch).
- A safety design that abstains or refers rather than guesses, tested by an eval set.

| Proof to show | Type | Where | Status |
|---|---|---|---|
| The avatar reacting live: listening, thinking, speaking | Screen | video shot 3 | have (branch) |
| Parent view with the weekly summary and no raw messages | Screen | video shot 5 | have |
| Avatar size: the capstone's 43 MB GLB is replaced by the animated avatar `avatar-animated.glb`, 2,480,896 bytes (about 2.5 MB; about 1.8 MB on the wire with Caddy's gzip). The earlier "0.69 MB, 38.8 s to 0.85 s" figures were for `avatar-web.glb`, which is no longer shipped (`94332b8`) | Metric | deck slide 9, `handoffs/06-avatar.md`, `handoffs/product-web.md` section 13 | have for the size; load time of the shipped file not measured |
| Side by side: a general chatbot without grounding vs our grounded answer, over the same eval questions and scored the same way, with the limits of the comparison stated. One screen is the example; the table is the proof. | Metric and screen | not in the deck: no side-by-side was measured | gap |

## 5. Beneficiary experience, communication and accessibility (10)

**The guide asks:** can the target user finish the task and understand the output, in clear and respectful language that suits their background and language? **5/5:** tests suited to the audience show it is easy to use and understand, and improvements were made from their results. **4/5:** it fits the user's background, language and accessibility needs, and explains errors and the next step.

**How we score:**
- A child-first screen: one big button, a friendly character, short answers.
- Arabic first, right to left, with an English switch. Status: have (`handoffs/product-web.md` sections 12 and 16). The web interface was English only at the start.
- Text mode as an alternative to voice, so a child who cannot or will not speak can still use it. Status: have (capstone), keep working.
- Reduced motion respected on the avatar. Status: have (task 06).
- Clear AI disclosure in the interface. Status: have: a permanent AI chip on the child's screens and an AI info sheet in Arabic and English (`handoffs/product-web.md` section 11; section 16 fixed it being hidden under the demo bar).
- Fast first paint: the avatar loads while the child is on the start screen. Status: have (branch).
- Keyboard and screen-reader basics, colour contrast, touch target size. Status: partial: axe reported 0 violations on the 12 tour pages it ran on, in both languages (`handoffs/product-web.md` section 16); no written notes yet, a short pass in the bug bash on Tue.
- A short usability test with adult testers playing the child and the parent (no real children, synthetic data only), and a list of what we changed because of it. Status: gap.

| Proof to show | Type | Where | Status |
|---|---|---|---|
| Arabic RTL screens (child and parent) | Screen | deck slides 7 and 9; appendix slide 21 | have |
| Text mode and voice mode of the same conversation | Screen | judge demo fallbacks | have |
| Reduced-motion setting | Screen or doc | handoff 06 | have (branch) |
| AI disclosure (chip and info sheet) | Screen | child screens | have (section 11) |
| Accessibility pass notes (contrast, focus order, target size) | Doc | `docs/ACCESSIBILITY.md` | gap, `[TBD]` |
| Usability test notes and the changes made from them | Doc | `docs/ACCESSIBILITY.md` | gap |

## 6. Operational realism and completion (10)

**The guide asks:** what does it take to keep running after the challenge: cost, dependencies and content review? **5/5:** estimates are backed by measurements or checkable information, there is an alternative for a critical vendor dependency, and there is an adoption plan that can be carried out. **4/5:** adds a maintenance and content-review plan with realistic owners.

**How we score:**
- Live deployment on `alsadiqai.com` with HTTPS (Caddy), health check and a seeded demo. Status: building: the demo pool, production hardening and the demo landing page are merged into `hk/product-web`, and the deploy path seeds the bank and the demo (`DEPLOY-CHECKLIST.md`), but this build is not deployed yet.
- Privacy: collect only what is needed; messages deleted after the session except flagged ones; the parent preview does not show raw text (the parent API's `preview` is empty since `caa2d65`). Status: have. Re-check it in the recorded build before claiming "parents never see transcripts".
- Cost per session and per month. Status: have, as a labelled estimate, not a measured cost: about 0.05 to 0.29 dollars a session; 3 to 34 dollars for 30 judges over the judging window; 60 to 570 dollars a month for 100 families, within the 5-minute demo cap (6 Oct 2026, every figure rounded up; README section 2.4, `deck-src/cost_estimate.py`). The token figure is the mean per eval run (agent plus judge), used as an upper bound for one agent call.
- Voice failure handling: ElevenLabs by default; if it cannot be used the agent logs one error, tells the room (`voice_error`) and ends the session, and an exhausted ElevenLabs budget goes text-only (`demo-guards.md`). There is no automatic second voice provider; an operator can switch to xAI by hand (`TTS_PROVIDER=xai`). Status: have; needs a live test.
- Daily smoke test during judging (7 to 22 Oct). Status: gap.
- An alternative for each critical vendor: text-to-speech (ElevenLabs) has only the manual xAI rollback (`TTS_PROVIDER=xai`); LiveKit Cloud has the self-hosted LiveKit server already in the dev compose file; OpenAI (speech-to-text and the answer model) has no alternative yet. Status: gap for OpenAI and ElevenLabs, `[team to decide]`.
- A maintenance and content-review plan with named owners: who reviews new bank items, who handles judge reports, who watches credit. Status: gap.
- A public repo with no secrets and no real user data, with an honest licence decision. Status: gap.

| Proof to show | Type | Where | Status |
|---|---|---|---|
| Live link opened signed out | Screen | judge demo step 1 | building |
| `/api/health/` returning OK | Screen | operations doc | building |
| Cost table: per-session cost (speech-to-text, model, voice, LiveKit) and a monthly estimate | Metric | deck slide 11 (measured usage per session, then the USD band labelled as an estimate); appendix slides 24 and 25 (line items, prices with links and the date checked, assumptions); README section 2.4 | have, as an estimate: measured units times public prices of 6 Oct 2026; plan fees and the server not included |
| Privacy statement | Doc | app and README | draft: `/privacy` in the app, Arabic and English, with a draft banner (`handoffs/product-web.md` section 11); its claims need the team's confirmation; none in the README yet |
| Rollback test log | Doc | `docs/OPERATIONS.md` | gap |
| Secret scan result on the public repo | Doc | checklist B2 | gap |

## 7. Clarity of presentation and ease of verification (5)

**The guide asks:** does the presentation let the panel understand the project and check its claims? **5/5:** concise and organised, makes re-testing easy, and separates clearly what was built from what is proposed for later. **4/5:** links each claim to its evidence and answers the panel's questions accurately. The final session is 5 minutes of presentation and 3 minutes of questions per team.

**How we score:**
- The video is 2:00 or less, Arabic narration with English subtitles, one story. Status: draft (`VIDEO-STORYBOARD.md`).
- The deck has 14 main slides for the 5-minute talk, each main evidence slide naming the criterion it answers, then an appendix of 13 slides (divider included), with real screenshots, not mock-ups. Status: draft with marked team slots (`DECK-OUTLINE.md`, "Final deck"; file in `docs/hackathon/deliverables/Presentation/`).
- A 3-minute click path for judges, with fallbacks. Status: draft (`JUDGE-DEMO-SCRIPT.md`).
- The disclosure is easy to find and honest. Status: draft (`DISCLOSURE.md`).

| Proof to show | Type | Where | Status |
|---|---|---|---|
| Final video file, duration 1:59 or less | Video | portal upload | draft |
| Deck PDF | Doc | portal upload | draft |
| Disclosure page linked from the top of the README | Doc | repo root | draft |

---

## How the three submission pieces split the proof

| Criterion | Video | Deck | Live demo | Repo and docs |
|---|---|---|---|---|
| Technical quality and use of AI | brief mention | slides 5, 10, 11 (appendix 16, 20) | text and voice sessions | code, eval report |
| Benefit against the track criterion | the full story | slides 3, 9, 10 (appendix 22, 23) | steps 3 to 6 | content bank |
| Reliability and scholarly integrity | shot 4 and shot 6 | slides 6, 8, 9 (appendix 17, 18, 19) | source card spot check | sources register, policy |
| Innovation and added value | shots 3 and 5 | slide 4 (appendix 20) | avatar and parent view | code |
| Beneficiary experience and accessibility | shots 2 and 3 | slide 7 (appendix 21) | Arabic screens, text mode | accessibility notes |
| Operational realism and completion | shot 7 | slide 11 (appendix 19, 24, 25, 27) | live link, health check | operations doc, cost table |
| Clarity and ease of verification | the video itself | slide 13 (appendix 26) | the script | README |

## Honest gaps today (updated 5 Oct)

- The status words in the tables above were written on 4 Oct. On 5 Oct the rows for grounding, the source card, the Arabic interface, the AI disclosure, the privacy page, the latency and the eval were re-checked against `handoffs/product-web.md` sections 11 to 18. Not every row still marked "building" or "gap" was re-checked; read those against the handoff before relying on them. The parent sources view (task 04) was not built.
- Task 10: the demo pool (`516bbe8`, raised to 40 families in `9fe104f`), production hardening (`3d8f355`, `8334170`) and the demo landing page are merged into `hk/product-web`. The build is not deployed yet: `alsadiqai.com` served the old login page at the last check (`handoffs/product-web.md` section 16).
- The Open Track metric is measured once: strict pass rate on the same cases before and after, held-out 25% to 44% and both splits 38% to 61% (`eval-reports/README.md`). The "before" is the knowledge-bank branch, not the original capstone agent, and it is one run per side.
- Metrics still marked `[TBD]` (accessibility notes, bank coverage) are open. The cost per session and per month is filled in as a labelled estimate.
- Eval, measured 5 Oct (one run, so it will move): 61% strict on 143 scored runs, 44% on the held-out split alone. Weak categories after the merge: `test-question` (2 of 13), `translation` (0 of 2), `story-request` (0 of 2), `grounding` (9 of 21, lower than before). `scripture_without_source` failures went from 10 to 21 in that run, and 8 of 18 English replies that said a verse number said a wrong one (the surah number in three cases). The cause was the spoken-verse wording in commit `7665993`; round 3 replaced it and measured 0 of 45 replies naming any chapter, surah or verse number, plus 0 of 10 in a repeat of the English grounding cases (`handoffs/product-web.md` section 17.1). Voice channel, a real hadith bank and a 3-run spread are not measured.
- The licence, avatar terms, image origins and recitation audio source need answers (see `CHECKLIST.md` section F and `DISCLOSURE.md` section 7).
