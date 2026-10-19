# Handoff: Submission pack (task 10)

- **Date:** 2026-10-04
- **Branch:** `hk/10-submission` (local only, not pushed)
- **Commits:** `f08f1f0` (the seven drafts), `0831659` (reviewer fixes), plus the commit that adds this file
- **Project:** Al-Sadiq Al-Sadouq, Islamic AI Challenge, Open Track, build window 4 to 6 Oct 2026 (Riyadh)

## 1. What this is

A set of seven drafts, in `docs/hackathon/submission/`, that cover what the challenge asks us to hand in besides the product itself: a checklist, a disclosure of pre-existing work, a sources register, a map to the judging criteria, a video storyboard, a deck outline and a judge demo script.

They are drafts written on 4 Oct, before most features were merged. The rule used throughout: a feature is called built only if it exists on a task branch. Tasks 01 to 05, 08 and 09 had no commits when this was written, so grounding, the source card, the parent sources view, the eval and the latency work are marked planned. Every metric we have not measured is a TBD placeholder.

An independent review checked the pack against the participant guide (downloaded again from islamicaich.org), the vault brief, the task branches and the handoffs. Its fixes are in `0831659`. Verdict: ship with notes.

Checks that passed: no scripture text and no emojis in any file; the judging weights match the guide (25, 20, 15, 15, 10, 10, 5); the video shots total 118 s, under the 2:00 limit.

## 2. The files and what each is for

All paths are under `docs/hackathon/submission/`.

| File | What it is for |
|---|---|
| `CHECKLIST.md` | The master list. Dates, required deliverables (A), disqualifier checks (B), documentation items (C), product proof boxes (D), the Tue 6 Oct run of show (E), and open questions for the lead (F). Start here. |
| `DISCLOSURE.md` | English and Arabic statement of pre-existing work versus work done in the window, with commit SHAs, third-party services and rights items. Undisclosed pre-existing work is a disqualifier, so this is the highest-risk file. |
| `SOURCES-REGISTER.md` | The approved source names only, with URLs. Per-item rows are empty on purpose and come from task 02. Flags Saheeh International as not approved. |
| `JUDGING-MAP.md` | The seven criteria with weights, the guide's 5/5 and 4/5 descriptors, our proof for each, and a proposed Open Track metric (before and after on the same cases). |
| `VIDEO-STORYBOARD.md` | Eight shots, 118 s, Arabic narration of about 145 words, English subtitles. Marks which shots depend on unmerged work. |
| `DECK-OUTLINE.md` | Twelve slides for a PDF or PPT, with the screenshots and numbers each one needs. |
| `JUDGE-DEMO-SCRIPT.md` | A ten-step, three-minute click path for a judge, with judge fallbacks and operator fallbacks (restart, xAI rollback, demo reset). |

## 3. How to finish each one

Search each file for `[confirm]`, `[TBD]` and `[range]`. Counts today: `DISCLOSURE.md` 18 confirm and 8 range; `JUDGING-MAP.md` 11 TBD; `DECK-OUTLINE.md` 4 confirm and 2 TBD; `JUDGE-DEMO-SCRIPT.md` 4 confirm; `SOURCES-REGISTER.md` 4 confirm; `VIDEO-STORYBOARD.md` 2 confirm and 2 TBD. Owners marked `[owner]` in `CHECKLIST.md` are to be assigned at the 4 Oct 21:00 sync. Majd holds task 10. Abdulrahman Salamah (lead) owns the production deploy and server `.env`.

- **CHECKLIST.md.** Assign owners at 21:00 on 4 Oct. Tick a row only after someone has opened the artifact from a signed-out browser. Fill the status column daily. Participation number goes in the team's private notes, not the repo.
- **DISCLOSURE.md.** Owner: Majd. Fill `[range]` with the final commit ranges at the Tue 17:00 docs pass. Resolve the `[confirm]` rights items (avatar, images, fonts, capstone, recitation audio) from the lead's answers. Replace the author and supervisor name placeholders once the capstone report is reachable. Add `docs/PROVENANCE.md` mapping private SHAs to public SHAs once the public repo exists. Link it from the top of the README and put a copy at the repo root.
- **SOURCES-REGISTER.md.** Owner: whoever runs task 02. Generate the per-item rows from the bank after task 02 lands. An item with no approved source cannot be seeded or reviewed. Replace Saheeh International with the King Fahd Complex translations if the lead agrees.
- **JUDGING-MAP.md.** Owner: Majd with the task 09 owner. Replace each TBD with a measured number after the final eval run on Tue morning. Decide the Open Track metric first (see open items), since the 20% criterion depends on it.
- **VIDEO-STORYBOARD.md.** Owner: whoever edits the video. Record a backup cut on staging after the Mon 21:00 freeze. Record the final on production on Tue 14:30. Re-time against the exported file, not the editor. Shots 4 to 6 need tasks 01 to 05 merged; if they are not, cut them or label them as design.
- **DECK-OUTLINE.md.** Owner: deck builder. Fill numbers from the final eval on Tue 16:00. Slides 5, 7, 8 and 9 depend on unmerged tasks. Export to PDF, check Arabic shaping and embedded fonts.
- **JUDGE-DEMO-SCRIPT.md.** Owner: Salamah for the operator steps, a fresh tester for the dry run. Check every button label against the merged UI. Fill the restart and reset commands the lead confirms. Dry run at Tue 19:00 from a signed-out browser.

## 4. Decisions

Made in this task:

- Only merged or task-branch features are called built. Everything else is planned, and metrics are TBD until measured.
- The disclosure lists the two commits before 09:00 (`e190c25`, `afa6568`) as pre-existing, with their contents.
- The sources register contains only names from the approved list in AGENTS.md. Nothing else is cited.
- No Quran or hadith text appears anywhere in the pack, and the staged ungrounded answer in the video must contain no verse, hadith or ruling.
- The public repo should be a fresh repo with a baseline commit, because the private history has committed credentials. This is a recommendation, not yet agreed.
- Recommended licence handling: pick one licence, and add a line for assets that it does not cover.
- Use King Fahd Complex translations rather than Saheeh International, since the reference pack approves the former.
- The judged link is `alsadiqai.com` (lead, 4 Oct), on one DigitalOcean droplet (8 GB RAM, 180 GB SSD) with LiveKit Cloud for media.

Needed from the team (not decided): licence, Open Track metric, avatar and image rights, capstone publication rights, recitation audio source, who signs off the content policy.

## 5. Open items

Decisions and rights
- Licence: the repo is MIT (Copyright 2026 96as); the brief's plan said all rights reserved.
- Open Track metric is undefined. The 20% criterion needs our own metric, measured before and after on the same cases, so task 09 must also run the capstone agent.
- Avatar origin conflict: the capstone report says Blender; the task files say Tripo then Blender. Tripo terms for public and commercial use are unconfirmed. The squirrel should get a likeness check against well-known cartoon chipmunks before going public.
- Origin of the meadow paintings (AI-generated, tool unknown), the badge and quest images, and the fonts. Arabic font and licence not chosen.
- Capstone rights: written agreement from the capstone team, and the university if required. Author and supervisor names are placeholders because the Y: drive was unreachable.
- Recitation audio source and licence are not on the approved list.
- Saheeh International appears only in PLAN decision 4 and is not an approved source.
- A named human reviewer for the content policy.

Product and copy
- The demo landing copy says parents "see what was said", which contradicts the planned "sources, not transcript" claim. Fix the copy or drop the claim before submission. The landing page change is still uncommitted.
- Tasks 01 to 05, 08 and 09 have no commits, so deck slides 5, 7, 8, 9, video shots 4 to 6 and demo steps 4 to 8 depend on them.
- Not yet tested live: the production voice session (a May audit saw "Couldn't connect"), the avatar states, and the `TTS_PROVIDER=xai` rollback.
- Demo labels (Try Al-Sadiq, Parent view, Child view, Start over) must be checked against the merged UI.
- No fallback for OpenAI, which the 5/5 operations descriptor asks for.
- Still uncommitted elsewhere: the 10-demo frontend, the prod-hardening follow-ups and the 07-voice edits.
- The old capstone fixture is still read by the lookup tool until task 01 lands, so the disclosure says so.

Lead to confirm
- LiveKit Cloud project, the exact agent restart command, the demo reset command, server region.

Documents still to create
- `THIRD_PARTY.md`, `docs/AI_TOOLS.md`, `docs/OPERATIONS.md`, `docs/CONTENT_POLICY.md`, `docs/PROVENANCE.md`, accessibility notes.

Quality
- The Arabic is MSA but has had no second human reader.
- The review did not re-read the 7-page reference pack PDF and relied on the vault summary. The guide PDF it checked against is at `%USERPROFILE%\AppData\Local\Temp\aic\guide.pdf`.
- Public repo SHAs will differ from private SHAs.

## 6. Next steps

1. Today, 4 Oct 21:00 sync: assign every `[owner]`, answer the lead questions in `CHECKLIST.md` section F, and decide the Open Track metric and the licence.
2. Today: fix the landing copy (or the privacy claim), and save the portal confirmation email and participation number.
3. Mon 5 Oct: rotate credentials, create the public repo from a clean baseline, write `THIRD_PARTY.md`, `AI_TOOLS.md`, `OPERATIONS.md` and `CONTENT_POLICY.md`, and settle the asset and capstone rights. Record the backup video after the 21:00 freeze.
4. Tue 6 Oct 09:00 to 13:00: last merges, final eval run, code freeze at 13:00, production deploy.
5. Tue 13:30 to 17:00: smoke test (text, voice, parent view, xAI rollback), secret scan on the new repo, final video and screenshots, fill deck and judging map numbers, regenerate `[range]` tables, generate the sources register from the bank.
6. Tue 18:00: one person reads every submission file against the merged code and removes any claim that is not merged.
7. Tue 19:00 dry run from a signed-out browser. Tue 20:00 submit and screenshot the confirmation. Hard close is 23:59.
8. Keep the live link up and smoke tested daily through 22 Oct.
