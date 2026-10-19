# Submission checklist: Islamic AI Challenge

- **Project:** Al-Sadiq Al-Sadouq (الصديق الصدوق), Open Track (trusted dialogue plus interactive learning)
- **Written:** 2026-10-04; **updated 2026-10-06, about 01:30 Riyadh time** (task 10, branch `hk/10-submission`, first based on `08075e1`, then merged with the `hackathon` branch at `735c95a`, after PRs #57 to #62). The lead's answers of 6 Oct, 06:15, were applied at about 07:00 (rows A2, A4, C13, C14 and section F).
- **Use:** tick items as they are proven, not as they are hoped for. "Done" means someone opened the artifact and checked it; for the public repo and the live link, from a signed-out browser.
- **Owners:** Abdulrahman Salamah (lead) owns the production deploy, the server `.env` and the merges. Majd holds task 10 (documents). Rows marked "team" need a human decision or action.
- **Requirements source:** the participant guide (`https://islamicaich.org/files/Hackathon/i2xgA3mxVhrbRe0ReLlA86kTDbFZ9QQ9eb856dq8.pdf`) and the reference pack, as summarised in the team's brief.

## Dates (Riyadh time)

| When | What | Source |
|---|---|---|
| Sun 4 Oct, 09:00 | Build window opens. Only work from here is judged. | Challenge brief |
| Mon 5 Oct, 21:00 | Feature freeze and staging deploy. Backup video recorded on staging after this. | PLAN.md |
| **Tue 6 Oct, 13:00** | **Code freeze.** Production deploy, bug bash, final eval run. | PLAN.md |
| Tue 6 Oct, 18:00 | Deck and video final (internal target) | This plan |
| Tue 6 Oct, 20:00 | Submit (internal target, leaves almost 4 h of margin) | This plan |
| **Tue 6 Oct, 23:59** | **Hard close. No extensions.** | Challenge brief |
| 7 to 15 Oct | First judging. The live link must work every day. | Challenge brief |
| 18 Oct | Top 20 announced | Challenge brief |
| 19 to 22 Oct | Final judging on Zoom: 5 minutes of presentation and 3 minutes of questions per team. Live link must stay up through 22 Oct. | Challenge brief |
| Objection windows | 2 days after screening, 5 working days after the final result | Challenge brief |

## A. Required deliverables

Status values: `not started`, `draft`, `in progress`, `blocked`, `done`.

| # | Requirement (guide) | Our artifact | Owner | Status (6 Oct, 01:30) | Proof that it is done |
|---|---|---|---|---|---|
| A1 | **Live demo link**: a complete, working product (not a prototype) that stays up through 22 Oct; judges can test every function | https://alsadiqai.com, judged link (lead, 4 Oct) | Salamah (deploy) | **not done.** On 6 Oct at about 00:25 the domain still served the capstone build: its page loads only the Manrope font, and `/api/health/` and `/static/quran/002083.mp3` return 404 (both still 404 at about 01:05). The hackathon build deploys at code freeze. The deploy rehearsal in `docs/hackathon/DEPLOY-CHECKLIST.md` ("Rehearsal results") was local, with dummy keys. | Signed-out browser: Try Al-Sadiq works, one voice and one chat session succeed, `docs/hackathon/DEMO.md` steps 1 to 9 pass. Then update the README "Live demo" line. |
| A2 | **Public GitHub repo**: public (private repos are rejected), no user data, passwords or keys, component licences included | a fresh public repo from this branch (recommended in the scrub list kept outside git); what to leave out of it is listed in `docs/hackathon/PUBLIC-REPO-SCRUB.md` | team | **not started.** Licence decided and committed (`LICENSE`). Decided by the lead on 6 Oct: the 74 everyayah mp3s in `backend/session_moral_context/static/quran/` stay in the repo with the everyayah.com attribution (C14); `mobile/` is a development build and is left out of the public repo. Still to decide before publishing: the sealed quality-gate sets in `docs/hackathon/eval-reports/quality-gate-sets/` would become public (listed in `docs/hackathon/PUBLIC-REPO-SCRUB.md`). **Clone size** (6 Oct, about 06:50: `git clone --no-local --single-branch --branch hk/10-submission`, then `git count-objects -vH`): one pack of 121 MiB for 674 commits, and a checkout of 115 MB in 1,420 files. The largest items are the 74 mp3s (46 MB together, none over 2 MB), the deck pptx (13 MB; each committed version adds about 13 MB to the history), `frontend/public/backgrounds/background.png` (6 MB) and the deck's PDF preview (3.7 MB). No file is near GitHub's 50 MB warning or 100 MB block, so the size is not a problem; a fresh public repo carries less history than this branch. | Open the URL signed out; README, `LICENSE` and the disclosure are visible; secret scan clean (B2). |
| A3 | **Documentation**: idea, setup, operation, dependencies, and a register of sources, tools and licences | `README.md` (English and Arabic), `docs/hackathon/IDEA_DESCRIPTION.md`, `docs/hackathon/DEMO.md`, `docs/hackathon/deliverables/sources.md`, `docs/hackathon/deliverables/ai-tools-log.md`, `docs/hackathon/deliverables/known-limitations.md`, `docs/hackathon/CURRENT_STATE.md` section 9 | Majd | **in progress**: written on `hk/10-submission`, not yet merged into `hackathon` | Merged; every link in the README opens on GitHub; section C below all ticked. |
| A4 | **Deck**: PDF or PowerPoint, Arabic or English, unified template or the challenge identity; problem, solution, how it works, added value, tech in detail, screenshots | `docs/hackathon/deliverables/Presentation/Al-Sadiq-Al-Sadouq-Final.pptx` and its PDF preview, on the organisers' template (slide list: `DECK-OUTLINE.md`; numbers: README section 3; screenshots: `docs/hackathon/readme-media/`; build scripts: `Presentation/deck-src/`) | team | **draft**: 23 main slides (one idea each, about 30 words, criterion named on each, lead's edits of 6 Oct applied), then an appendix of 18 slides (divider included). Marked slots still open: the video link and the public repo link (slide 22). Slide 22 carries the judged quality-gate re-run of 6 Oct in its "after" column. Done with the lead's answers of 6 Oct: the team slide lists three members; the USD cost per session and per month is filled in as an estimate (slide 11, method on appendix slides 24 and 25, labelled "estimate, 6 Oct 2026"), never as a measured cost; the mobile app appears only as "in development". | The PDF opens on a clean machine with fonts embedded; numbers match README section 3. |
| A5 | **Video, at most 2:00** | `VIDEO-STORYBOARD.md`; flow in `docs/hackathon/DEMO.md` | team | **not started** | Exported file is 1:59 or less, played once from the final file. |
| A6 | **Synthetic or anonymised data only** | 40 synthetic demo families (`backend/demo/content.py`); every README screenshot uses synthetic data (`docs/hackathon/readme-media/`) | Salamah, Majd | **done** for the repo and screenshots | Seed script reviewed; no real name, email or recording in the repo, the database or the video. Re-check the video. |
| A7 | **Portal confirmation**: keep the confirmation email and the participation number; report failures to info@IslamicAIch.org with it | team's private notes (not the repo) | team | not started | The number is written in the private notes. |
| A8 | **Disclosure of pre-existing work**: starting version and rights documented; undisclosed work is a disqualifier | `DISCLOSURE.md`; README section 2 ("Before" = `0241d4d`) | Majd, lead for rights | **draft.** The `[range]` and `[confirm]` items are still open. Fixed on 6 Oct: the voice rows now match the code history (the capstone agent used xAI Grok text-to-speech, `backend/conversation/agent/entrypoint.py` at `e7c98a3^`; ElevenLabs was built in the window and xAI stays as a manual operator rollback). | `DISCLOSURE.md` at the repo root, linked from the README; rights items resolved. |
| A9 | **Submission sent** through the portal before 23:59 on 6 Oct | the portal | team | not started | Portal shows the submission; screenshot of the confirmation. |

## B. Disqualifier and gate checks

| # | Disqualifier | How we check | Owner | Status (6 Oct, 01:30) |
|---|---|---|---|---|
| B1 | Private repo | Open the repo URL in a signed-out window. | team | not started |
| B2 | Secrets in the repo | `gitleaks detect --log-opts="--all"` (or trufflehog) on the **new** public repo, full history, plus a `git grep` on the tip for the patterns in the private scrub list and in `docs/hackathon/PUBLIC-REPO-SCRUB.md`. Every credential that ever touched the private repo is rotated. | team | not started. The private history has committed credentials, so a fresh public repo is the planned route. `.env` is not tracked (`CURRENT_STATE.md` section 8). The security audit (PR #62, items C1 and H3 and "Manual actions for the lead") lists the credentials it found in the history and the rotation each one needs. |
| B3 | Video longer than 2 minutes | Check the exported file's duration. | team | not started |
| B4 | Missing 23:59 on 6 Oct | Submit at 20:00. | team | not started |
| B5 | Undisclosed pre-existing work | A8. The capstone code, the avatar mesh (Tripo), the images, the vendored skills and the pre-09:00 docs commits (`e190c25`, `afa6568`) are listed in `DISCLOSURE.md`; the README's before and after sections use `0241d4d` as "before". | Majd | draft |
| B6 | Personal fatwa, or fabricated or unsourced hadith | Policy eval at `735c95a`, the same output as at `8c2ff0d` and `08075e1` (`run_eval --no-fail`): invented-hadith 20 of 20 pass, safety 92 of 92, personal-case 26 pass, 2 fail (one held-out personal question is answered instead of referred), 2 gap. Hadith come only from the bank (94 reviewed, Bukhari and Muslim, with grade and dorar.net link). | lead (rules) | **in progress**: one personal-case gap, listed in `known-limitations.md` |
| B7 | Stopping at a prototype | Production deploy up, demo accounts seeded, health check green, daily smoke test. | Salamah | not started (A1) |
| B8 | Citing unapproved sources | Every item in the bank has a source from the approved list: all 273 items are from quranpedia.net, dorar.net, dawa.center and islamic-content.com, with everyayah.com recitation and HadeethEnc English as the organisers accepted (`deliverables/sources.md`). The retired capstone fixture is not read by the agent. | lead | **done for the bank at `735c95a`** (unchanged since `8c2ff0d`); re-check `seed_content` on the production database after the deploy |

## C. Documentation items

| # | Document | Where it lives | Status (6 Oct, 01:30) | Notes |
|---|---|---|---|---|
| C1 | Idea description | `docs/hackathon/IDEA_DESCRIPTION.md`, README section 1 | **done** | Rewritten for what is merged; each claim mapped to evidence; the application wording kept for the record. |
| C2 | Setup (run it yourself) | README section 5 | **done** | `cp .env.example .env`, keys, `DEMO_MODE=1`, `docker compose --profile all up --build`, then Try Al-Sadiq. Keys a judge must bring: OpenAI and ElevenLabs (LiveKit dev keys are in `.env.example`). |
| C3 | Operation | `docs/hackathon/DEMO.md` (pre-flight, fallbacks), `JUDGE-DEMO-SCRIPT.md` (operator fallbacks), `docs/hackathon/DEMO-LOGIN.md` (demo settings), `docs/hackathon/DEPLOY-CHECKLIST.md` | **in progress** | `docs/OPERATIONS.md` (daily smoke test log, who is paged, restart commands) is not written. |
| C4 | Dependencies and licences | README section 8, `CURRENT_STATE.md` section 9 | **done**, except a licence-scanner pass | Run `pip-licenses` and `license-checker` before publishing. |
| C5 | Register of sources | `docs/hackathon/deliverables/sources.md`, regenerated at `8c2ff0d`, checked at `08075e1` and `735c95a` | **done** | 273 items, reviewer per type, organiser rulings per source, the stored recitation copies (3.3). |
| C6 | Register of tools | `docs/hackathon/deliverables/ai-tools-log.md`, README section 9 | **done** | |
| C7 | Disclosure | `DISCLOSURE.md` | draft | See A8. Add `docs/PROVENANCE.md` (private to public SHAs) once the public repo exists. |
| C8 | Content policy (levels A to D, refusal and referral copy) | rules in `AGENTS.md` and README section 2.6; code in `turn_policy.py` and `turn_rules.json` | **in progress** | A separate `docs/CONTENT_POLICY.md` with a named human sign-off is not written. |
| C9 | Eval report | `docs/hackathon/eval-reports/README.md`, `docs/hackathon/eval-reports/quality-gate-summary.md`, README section 3 | **done** for the live eval of 5 Oct, the policy eval at `2c04305`, and the judged quality gate re-run on 6 Oct at `8cbe64a` (the same product code as `2c04305`) | The quality gate still fails: 2 of 11 rows pass (lesson creep 9.9%, identity 100%), 34 hallucinations. Both runs' numbers are in `quality-gate-summary.md` (sections 1 and 3), README section 3 and deck slide 22; the full report stays on `hk/09-quality-gate` (`f3caa82`) because it names and quotes sealed lines. |
| C10 | Limits and failure modes | `docs/hackathon/deliverables/known-limitations.md`, README section 7 | **done** | Rewritten at `8c2ff0d`, checked again at `08075e1` and `735c95a` (adds the child-echo filter's limit and the security audit's open items). |
| C11 | Privacy statement | In the app (`/privacy`, Arabic and English) and README sections 2.6 and 7 | draft | The page shows "Draft, pending legal review"; contact, controller and retention details still to fill. |
| C12 | AI disclosure in the UI | permanent AI chip and sheet on the child screens; AI notice at registration (`frontend/src/features/child/ai/`) | **in progress** | The demo landing page has a privacy link but no AI statement yet. |
| C13 | Licence decision | root `LICENSE` | **done** | Lead's decision: all rights reserved for the team's own code; third-party content under its owners' terms, listed in README section 8. Team name confirmed by the lead on 6 Oct: "Al-Sadiq Al-Sadouq team" (`LICENSE`, README section 12 in both languages). The `mobile/LICENSE` note is removed: `mobile/` is a development build that is not published in the public repo. |
| C14 | Third-party asset terms | README section 8, `CURRENT_STATE.md` section 9 | **in progress** | Open: (1) the Tripo plan and terms for the avatar mesh; (2) the meadow `fantasy-meadow.webp` was generated by the team lead with World Labs (Marble) (lead, 6 Oct; credited so in README section 8, `CURRENT_STATE.md` section 9, `LICENSE`, `SOURCES-REGISTER.md` and `deliverables/sources.md`). World Labs terms give a paid account its outputs, while a free account gets non-commercial use only, so the lead confirms which plan his account is on; (3) the source of the `meadow-env-1024.webp` panorama; (4) the tool and terms of `background.png`, the badge and the quest images; (5) decided by the lead on 6 Oct: the 74 everyayah recitation mp3s in `backend/session_moral_context/static/quran/` stay in the repo with the everyayah.com attribution (README section 8, `LICENSE`, `deliverables/sources.md` 3.3). |
| C15 | Open Track success metric | README section 3, `IDEA_DESCRIPTION.md` | **done** (one run each) | Strict pass on the same cases, held-out 25% to 44% (`eval-reports/README.md`); policy eval 338/24/30 to 340/22/30 across PR #56. A 3-run spread was not measured. |

## D. Product proof (what the demo, deck and video rely on)

Nothing below may be claimed until the box is ticked and the code is merged.

- [x] Grounded answers: a child question returns source cards. Checked at `8c2ff0d`, `08075e1` and `735c95a` with `prepare_turn` (`DEMO.md` steps 3 and 4) and in the after screenshots.
- [x] Recitation is a play button on every verse card, credited and linked to everyayah.com; verses never go to TTS (`tts_text.py`, `scripture_guard.py`). Play one clip in the rehearsal.
- [x] Parent "sources discussed this week" with grades and links: merged in PR #59 (Abdulrahman Mahmalji), demo families seeded by PR #58. Seen on the local demo stack on 6 Oct with 5 cards in English and Arabic (README section 2.5, `DEMO.md` step 7b). Check it again on production after the deploy.
- [x] Parent summary preview shows no message text (`backend/reporting/test_privacy_prompts.py`).
- [x] A personal-ruling question is referred to a parent (`DEMO.md` step 5). One held-out personal case still fails (B6).
- [x] Card gate: no card for plain chat or courtesy (`DEMO.md` step 6, `conversation/test_card_gate.py`).
- [x] Policy eval re-run after the last merge: 340 pass, 22 fail, 30 gap of 392 at `2c04305` (same as at `8c2ff0d`, `08075e1` and `735c95a`); backend tests 1686 passed, 2 skipped (1688 run) at `2c04305`, in the project's agent Docker image; frontend lint, build, `check:cards`, `test:i18n` 13 of 13 and `tests/security.test.mjs` 6 of 6 pass at `2c04305` (6 Oct). The live eval was not re-run after PR #56; the judged quality gate was re-run on 6 Oct at `8cbe64a` (`quality-gate-summary.md` section 3).
- [x] Latency stated with its conditions: about 2.6 s per reply and 3.0 s for the greeting at 1 to 10 sessions (`latency/LOAD-REHEARSAL.md`). No "before" figure.
- [ ] Voice failure path tested in a real session (ElevenLabs key rejected: one logged error, a `voice_error` message, the session ends cleanly; budget exhausted: text only).
- [ ] Avatar load time measured in the full app after login (`avatar-animated.glb`, 2,480,896 bytes).
- [x] Demo families seed themselves and "Start over" resets one (`docs/hackathon/DEMO-LOGIN.md`); confirm on production after the deploy.
- [ ] OpenAI and ElevenLabs credit checked on the production keys before judging. The local stack's OpenAI key hit an exhausted quota on 5 Oct and again on 6 Oct at about 00:11 Riyadh time (`429 insufficient_quota`; every reply became the fixed fallback line). Whether production uses the same OpenAI account is not known to us.

## E. Tuesday 6 Oct run of show

| Time | Step |
|---|---|
| 09:00 | Last merges, including `hk/10-submission`. Re-run the quality gate on the current build if possible. |
| 13:00 | **Code freeze.** Tag the release. Deploy production. |
| 13:30 | Smoke test: `scripts/smoke_alsadiqai.py`, a chat session and a voice session following `DEMO.md`, the parent view. Scan the new public repo for secrets. |
| 14:30 | Record the final video from production. Retake README screenshots only if the UI changed after `2c04305` (the parent sources were retaken there, after PR #64). |
| 16:00 | Deck numbers checked against README section 3. Export PDF. Check fonts and Arabic shaping. |
| 17:00 | Docs pass: README "Live demo" line, `DISCLOSURE.md` (ranges and `[confirm]` items), the deck's team slots, any number that changed after the freeze. |
| 18:00 | One person reads every submission file against the merged code and removes any claim that is not merged. |
| 19:00 | Dry run of `DEMO.md` by someone who has never seen the app, from a signed-out browser. |
| 20:00 | Submit. Screenshot the confirmation. Save the email. |
| 20:30 | Re-open the public repo and the live link signed out. Confirm the video plays. |
| 23:59 | Hard close. |

## F. Open questions for the lead

1. Answered 4 Oct: `alsadiqai.com` on one DigitalOcean droplet with LiveKit Cloud. Still open: the LiveKit Cloud project, the exact agent restart command, the server region.
2. Route for the public repo: a fresh repo with a baseline commit (recommended), and whether the sealed quality-gate sets go into it.
3. Answered 5 Oct: licence = all rights reserved for our code only (done in `LICENSE`). Answered 6 Oct: the team name for the copyright line is "Al-Sadiq Al-Sadouq team". Still open: whether the "judges may read, build and test" sentence in `LICENSE` is wanted.
4. Who confirms the Tripo terms, the `meadow-env-1024.webp` panorama source, and the origin of `background.png` and the badge and quest images (C14)? The meadow was generated by the lead with World Labs (6 Oct), so the lead confirms the plan of that account.
5. Which teammate signs off the content policy (levels C and D)?
6. Do the capstone authors, and the university, agree to the capstone code being published?
7. Answered 5 Oct (round 3): the landing copy says parents see weekly summaries, safety alerts and topics to talk about. Re-check it in the final build. The landing page still has no AI statement (C12).
8. Answered: the Open Track metric is the strict pass rate on the same eval cases, before and after (C15).
9. Answered 6 Oct: the 74 everyayah mp3s stay in the repo, with the everyayah.com attribution (C14, A2).
10. Answered 6 Oct: the focus is the web; `mobile/` is a development build that will not be in the public repo, so the `mobile/LICENSE` notes are removed (C13). The README and the deck mention the mobile app only as "in development".
11. Answered 6 Oct: the USD cost per session is an estimate, not a measurement: measured units times the providers' public prices of 6 Oct (slide 11, appendix slides 24 and 25, README section 2.4; `deck-src/cost_estimate.py`).
12. Answered 6 Oct: the video and public repo link slots stay empty and marked until the links exist (slide 13).
13. Answered 6 Oct: the team is three members, Abdulrahman Salamah (lead), Majd Awad and Abdulrahman Mahmalji. The team slide shows these three, and no submission document lists anyone else as a member.
