# Deck outline

## Final deck (6 Oct 2026, hk/17 restructure)

The deck is `docs/hackathon/deliverables/Presentation/Al-Sadiq-Al-Sadouq-Final.pptx`, with a PDF preview beside it (`Al-Sadiq-Al-Sadouq-Final-preview.pdf`). It is in Arabic, on the organisers' template, in Readex Pro only. Following the lead's feedback that judges scan, each main slide carries one idea in about 30 words or fewer; the detail is in the speaker notes and the appendix. Each main slide's section label names the judging criterion it answers, and slide 2 maps every criterion to its slides.

How it is built: `deck-src/build_deck.py` made the 27-slide deck (commit `84830269`); `deck-src/restructure.py` takes that deck as input, adds the new main slides as clones of its template slides, and moves the old detail slides into the appendix. Icons come from `deck-src/icons.js` (react-icons); `deck-src/render.py` makes the PDF and slide images with headless LibreOffice. No scripture is typed anywhere: it appears only inside screenshots of the app's own source cards. The README verse-card screenshot still names the old Muallim recitation, so that one line is cut out of the image (the app now shows Husary, normal pace, everyayah.com).

**Round 3 (6 Oct evening, `deck-src/edit_v3.py`):** the lead edited the deck by hand, and `edit_v3.py` was run on that file. It added:
- a contents slide (2), which moves the judges' guide to 3 (renumbered);
- a comparison with ChatGPT, Grok Companions and Replika after the solution (6), per published terms and features as of Oct 2026, with sources in the notes;
- an expected-impact slide after the results (19): child → family → community, labelled as expected and not measured, with how it will be measured.

It also made the safety slide (17) say what was tested, and what the two numbers mean. There are now 26 main slides and 44 slides in total. The slide table below is from before round 3; add 1 to the slide numbers from 2, and 2 from 5.

**Main deck** (23 slides; lead's edits of 6 Oct applied):

| # | Slide | Criterion |
|---|---|---|
| 1 | Cover: a voice companion teaching 38 values through fun conversation, quests and badges, bringing the child closer to the parents | |
| 2 | Judges' guide: where each criterion is | all |
| 3 | 01 The problem: children ask general AI about everything (unsuitable content, religion without a source, busy parents, children who don't tell everything); our aim: a companion for every question, Islamic in spirit, teaching at the right time and citing sources | Benefit |
| 4 | 02 The solution: one sentence + the child's home screen | Innovation |
| 5 | 02 What is new: six tiles (incl. learning through play, a living character with 30 movements) + the badges page | Innovation |
| 6 | 03 The child's experience (three screens; 30 movements and gestures) | Beneficiary experience |
| 7 | 03 The source card | Beneficiary experience |
| 8 | 04 The parents' experience | Beneficiary experience |
| 9 | 04 Every feature at a glance (child 14, parents 10, safety and content 10) | Beneficiary experience |
| 10 | 05 The 38 values in six themes; every value has reviewed hadith and sources, 37 also have verses | Benefit |
| 11 | 06 No source, no answer | Reliability |
| 12 | 06 Approved sources | Reliability |
| 13 | 07 How it works (diagram) | Technical quality and use of AI |
| 14 | 07 The technology | Technical quality and use of AI |
| 15 | 08 Safety (60/60 flagged, 48/60 alerted, 3/66 false alerts) | Reliability |
| 16 | 09 Results (PR #76) | Benefit |
| 17 | 10 What we built in 3 days (incl. ElevenLabs, lip sync and 30 movements) | Benefit |
| 18 | 11 Operations ($0.29 per session upper bound, an estimate; 10 sessions; 165 MB; through 22 Oct) | Operational realism |
| 19 | 12 Limitations and next steps, stated at a high level (details in the notes and appendix; reviewed by a student of Islamic knowledge, not yet a scholar) | Clarity |
| 20 | 13 Family accounts and judge accounts: only a parent can register and create the children's accounts; five seeded judge families (hk-18), because Al-Sadiq builds on every conversation | Clarity and verifiability |
| 21 | 14 The team: Abdulrahman Salamah (idea owner and lead, backend logic and the bank, the student of Islamic knowledge who reviewed every source and explanation), Majd (the whole UI/UX), Abdulrahman Mahmalji (assists with the Dorar review and UI/UX); note on Musa and Tariq, who left after the challenge began | |
| 22 | 15 Verify it yourself; note: with the organisers' approval (Riwa), deployment stays on the private repo for security, the public repo is identical, and judges can ask the lead for read access to the private one | Clarity and verifiability |
| 23 | Thank you, with a pointer to the appendix | |

**Appendix** (18 slides, divider included): how it works in four steps; the voice agent's architecture; the content bank table; content and safety rules; the review workflow; the avatar; accessibility; the source-timing table (PR #76, all metrics, by language); alert precision (PR #72, main, held-out and fear-of-home sets); the 5 Oct results; the quality gate before and after; the lesson-creep proxy; operations and cost; cost per session; cost per month; disclosure; roadmap.

The USD numbers come from one script, `deck-src/cost_estimate.py`, and are always labelled an estimate.

**Slots the team still fills** (dashed boxes marked «خانة للفريق»): slide 22, the video link and the public repository link.

## Plan written on 4 Oct

The brief asks for a PDF or PowerPoint file, in Arabic or English, in the unified template or a custom one that follows the challenge identity. It must cover: the problem, the solution, how it works, the added value, the technology in detail, and screenshots.

## Decisions for the deck

- **Language:** Arabic slide titles with English sub-lines, so Arabic and English judges both follow. Each slide is readable without the speaker. `[confirm with the team: all-Arabic, or bilingual]`
- **Template:** use the challenge's unified template if the organisers supplied one. If not, a custom template in the challenge's colours, with right-to-left layout for Arabic text. `[confirm template]`
- **Screens:** real screenshots from production, taken after code freeze (Tue 6 Oct, 14:30). No mock-ups. Any staged example (for example, the ungrounded chatbot) is labelled as such.
- **Numbers:** only measured numbers, each with its date and how it was measured. `[TBD]` stays out of the final file. If a number is not ready, the slide shows the method and says "measured on 6 Oct".
- **No scripture typed by hand.** Any verse or hadith in a screenshot comes from the bank, and the screenshot itself is the proof.
- **Fonts:** an Arabic font with a licence that allows embedding, embedded in the PDF. `[confirm font and licence]`
- **Export:** PDF as the main file. Open it on a clean machine and check Arabic shaping, right-to-left order and image quality. A PowerPoint copy is optional.
- **Status labels:** a feature that is not merged by freeze is not on a slide.
- **Talk length:** the final judging session gives each team 5 minutes to present and 3 minutes for questions, so the deck must also carry a 5-minute talk (about 25 seconds a slide).

## Slide plan

| # | Title (Arabic / English) | Section |
|---|---|---|
| 1 | الصديق الصدوق / Al-Sadiq Al-Sadouq | Title |
| 2 | المشكلة / The problem | Problem |
| 3 | الحل / The solution | Solution |
| 4 | تجربة الطفل / The child's experience (the meadow) | Solution |
| 5 | كيف يعمل: لا مصدر، لا جواب / How it works: no source, no answer | Mechanism |
| 6 | التقنية / The technology | Tech in detail |
| 7 | إجابات موثوقة / Trusted answers | Added value |
| 8 | العربية أولًا، وعرض الأهل / Arabic first, and the parent view | Added value |
| 9 | النتائج المقيسة / Measured results | Tech in detail |
| 10 | جاهز للتشغيل / Ready to run | Operations |
| 11 | ما كان موجودًا وما بنيناه / What existed and what we built | Disclosure |
| 12 | الخطوة التالية / What is next | Close |

---

## Slide 1. Title

- **Key points:**
  - Name, one-line promise: "A voice companion that teaches children Islamic values, and knows its sources."
  - Challenge name, Open Track, team names, date.
  - Live link `alsadiqai.com`.
- **Visual:** the squirrel Al-Sadiq on the painted meadow path (the product's scene), full bleed, from a production screenshot. Logo top corner.
- **Judging link:** presentation.

## Slide 2. The problem

- **Key points:**
  - Children now ask AI about their faith, by voice, on the family phone.
  - General chatbots can invent a hadith, quote a verse wrongly, or give a personal ruling to a child.
  - Parents cannot see what was said, and cannot check where it came from.
  - Most Islamic content tools are written for adults and are not in a child's language.
- **Visual:** left, a child's question as a chat bubble. Right, an ungrounded answer with a red "no source" tag, labelled "staged example". Below it three short icons: wrong, unsourced, unsafe.
- **Note:** do not quote any real chatbot answer. Keep the example in our own UI. The staged answer holds no verse, hadith or ruling, real or invented: blur its text and let the tag make the point.
- **Judging link:** track success, scholarly reliability.

## Slide 3. The solution

- **Key points:**
  - Al-Sadiq Al-Sadouq: a voice and text companion for ages 6 to 13, Arabic first, built around honesty and good character.
  - Every religious statement comes from a verified bank and shows its source.
  - It refers personal rulings to parents and scholars, and never guesses.
  - A parent dashboard shows progress, a weekly summary, alerts and topics to talk about, and no raw chat text.
- **Visual:** three screens in a row: child screen, source card, parent dashboard (production screenshots).
- **Judging link:** track success.

## Slide 4. The child's experience

- **Key points:**
  - The child enters a painted meadow and meets Al-Sadiq, a squirrel who greets first ("السلام عليكم"), listens, thinks and answers.
  - Concept 1, the Home walk: on Home he walks up the meadow path and idles, with a stroll or a wave every few seconds.
  - Concept 2, the steady call: when the session starts the camera eases once into the call framing and then stays still. It never zooms while he speaks.
  - The character reacts to the conversation: leaning in to listen, a thinking pose and a jaw that moves with the real voice. (Gestures and the web page in his hand exist in code but are off or unwired in production, see JUDGE-DEMO-SCRIPT; do not claim them unless they are on and shown.)
  - Voice or text, short answers, quests and badges for steady practice, Arabic right to left.
  - Loads fast: the character is ready while the child is still on the start screen.
- **Visual:** a screenshot strip of the three states (listening, thinking, speaking) on the meadow call screen, the Home walk (two frames of the stroll), plus the badge screen.
- **Note:** the quests and badges are from the capstone and are disclosed on slide 11. The product scene is the meadow. The 3D forest is an opt-in flag (`?forest=1`) and is not the product, so do not say "forest" on a slide unless it is shown with that label.
- **Judging link:** track success, innovation, UX.

## Slide 5. How it works: no source, no answer

- **Key points:**
  - The flow in five steps: child speaks, speech-to-text, retrieval from the bank, a decision (answer, simplify, refer, decline), then the reply and its voice.
  - The model may only quote what the bank returned. Retrieval runs before every reply.
  - Each reply records which items it served, and the parent sees them under "Sources discussed this week" on Insights (PR #59, seeded for the demo families by PR #58; README section 2.5, `DEMO.md` step 7b).
  - Verses play as recorded recitation, never as synthesised speech. A guard in the speech cleaner keeps Quran brackets out of the synthesiser.
- **Visual:** an architecture diagram, left to right, with the grounding step in the accent colour. The "refer" branch goes to a "parent or scholar" box.
- **Note:** draw this only as built. If the decision step ships in a reduced form, draw the reduced form.
- **Judging link:** technical quality, scholarly reliability.

## Slide 6. The technology

- **Key points:**
  - Backend: Django 5.2, Django REST framework, Postgres. Web: React 19, Vite, React Three Fiber. (A mobile app is in development; it is not a deliverable.)
  - Voice: LiveKit Agents. Speech-to-text and the answer model from OpenAI. Text-to-speech from ElevenLabs (`eleven_flash_v2_5`), the default voice provider; the capstone's xAI voice stays only as a manual operator rollback.
  - Why these choices, in one line each, taken from the task 07 voice comparison and the latency report `[fill after the reports are final]`, plus one switch to roll back.
  - Hosting: DigitalOcean, Caddy for HTTPS, LiveKit Cloud for media.
- **Visual:** a layered stack diagram with logos of the services and a small table "what we chose and why".
- **Note:** say nothing about voice quality or speed that the task 07 and task 08 reports do not show.
- **Judging link:** technical quality.

## Slide 7. Trusted answers

- **Key points:**
  - The source card: source name, item type, grade for a hadith, link to open.
  - Approved sources only, listed by name: King Fahd Complex and Quranpedia, Sahih al-Bukhari and Sahih Muslim, Dorar al-Saniyyah (graded), Bayyinat, Islamic Content portal.
  - Four content levels: A direct answer, B explanation, C disputed so only what is agreed, D personal case so refer.
  - Side by side: an ungrounded answer vs ours to the same question.
- **Visual:** left, the ungrounded bubble from slide 2. Right, our answer with the source card. Underneath, a strip of the four levels A to D with a one-word example each.
- **Judging link:** scholarly reliability, innovation, track success.

## Slide 8. Arabic first, and the parent view

- **Key points:**
  - Right-to-left Arabic screens for the child and the parent, with an English switch.
  - Parent dashboard: progress, weekly summary (labelled as written by AI), alerts, suggested topics to talk about, and "Sources discussed this week" with each source's reference, grade and link (merged in PR #59; screenshots `docs/hackathon/readme-media/after/parent-sources-en.webp` and `parent-sources-ar.webp`).
  - Privacy: the parent sees short summaries, not the transcript (the parent API's `preview` is empty since `caa2d65`). Messages are deleted after each session except flagged ones.
  - AI disclosure visible in the interface. Text mode for children who prefer typing. Reduced-motion setting.
- **Visual:** two screenshots, child (Arabic, right-to-left) and parent (weekly summary, alerts and suggested topics), with callouts. (Built since: the parent's sources list, PR #59, now on slide 9.)
- **Judging link:** UX and accessibility, operational realism, innovation.

## Slide 9. Measured results

- **Key points:**
  - Evaluation, measured 5 Oct: 186 cases across grounding, refusal of personal rulings, "give me a hadith even if weak", out-of-bank questions and child safety; 160 run live (all 50 held-out plus 110 dev), same questions, same scoring, before and after. Strict pass rate on the held-out split: 25% to 44% (10/40 to 18/41, Wilson 95% intervals 14 to 40 and 30 to 59; paired +20.5 points, 95% bootstrap +5.1 to +35.9). On both splits: 38% to 61% (54/143 to 87/143). Policy-only dry run over all 186: 87% to 97%. Safety: 12% to 72%.
  - Failures we still know about, said on the slide: test questions (2 of 13 pass), translation, story requests, and the judge-tagged `scripture_without_source` count. (Spoken verse numbers, 8 of 18 wrong in the first run, are fixed: 0 of 45 in the round-3 re-run.) Footnote: one run each (no repeat spread), "before" is the knowledge-bank branch and not the original capstone agent, team-written cases scored by a model judge, text channel only. Reports: `docs/hackathon/eval-reports/`.
  - Latency: end of the child's question to first audio, about 2.0 to 2.6 s median at 1 to 10 sessions on a local stack (greeting about 3.0 s; longer on turns that call the reference tool). Say the conditions on the slide.
  - Avatar: the capstone's 43 MB GLB is replaced by the animated avatar, 2,480,896 bytes (about 2.5 MB; about 1.8 MB on the wire with Caddy's gzip), `handoffs/product-web.md` section 13. Do not use the older "0.69 MB" or "38.8 s to 0.85 s" figures: they were for `avatar-web.glb`, which is no longer shipped. The load time of the shipped avatar is not measured.
  - Before and after on our Open Track metric: the same questions put to the earlier build and to the final build, scored the same way (`JUDGING-MAP.md` section 2). This is the main proof for the 20% criterion. Measured 5 Oct: the earlier build is the knowledge-bank branch (it already had the bank), so the slide says "before integration", not "before the bank". If a run against the original capstone agent is wanted, it has not been done.
  - Repeat runs: not done. The 5 Oct numbers are one run per side; the slide says so. One pass over the 160 runs cost about 310 counted calls per side, so three passes did not fit the 700-call cap.
  - Tests: backend suite and the 112 speech-cleaner tests, counts from the final run.
- **Visual:** one clean results table, plus one latency figure with its conditions written beside it (2.0 to 2.6 s median, first audio, 1 to 10 sessions, local stack; there is no latency before-and-after chart, the earlier run used a different script) and the avatar size before and after (43 MB to about 2.5 MB). Method in a footnote.
- **Note:** copy numbers from the final reports on Tue 16:00. The avatar size exists today (the file sizes); its load time in the full app is not measured, so do not show a load time unless it is measured.
- **Judging link:** technical quality, scholarly reliability.

## Slide 10. Ready to run

- **Key points:**
  - Live at `alsadiqai.com` with HTTPS, a health check, and a one-click demo that never needs a password, and it stays up through 22 Oct.
  - Judging-day capacity: a pool of 40 imaginary families, 120 starts an hour per office IP, and a deploy that seeds the demo data by itself, so a fresh server never answers 503. One agent worker carried 10 simultaneous voice sessions on a local stack (`latency/LOAD-REHEARSAL.md`); rehearse with 5 browsers on the real droplet before the day.
  - Cost: USD per session and per month. Built as an estimate (measured units times public prices, 6 Oct 2026): slide 11 and appendix slides 24 and 25.
  - Privacy and safety controls, and demo guards (daily caps; when the ElevenLabs budget runs out the session goes text-only). Say "tested" only after a live test.
  - An alternative for each critical vendor (media: self-hosted LiveKit; voice and OpenAI: no alternative, `[team to decide]`), and named owners for maintenance and content review.
  - A public repo, no secrets, no real data, with a licence and a daily smoke test during judging.
- **Visual:** an operations strip: live link badge, health check OK screenshot, cost table, rollback toggle diagram.
- **Judging link:** operational realism.

## Slide 11. What existed and what we built

- **Key points:**
  - Pre-existing and disclosed: the capstone product (v1, honesty), the avatar model (Tripo, then Blender, `[confirm]`), the AI-generated meadow paintings, quests and badges, base libraries.
  - Built in the window: the voice switch and speech cleaner, the web avatar and its motion, the meadow stage (the Home walk and the steady call), the one-click judge demo and its capacity, `[the content bank, grounding, source card, evaluation, as merged]`, and the parent sources view (merged in PR #59).
  - Where to verify: `DISCLOSURE.md`, the commit range from `e7c98a3`, and the private-to-public SHA table.
  - Services and tools used: OpenAI, ElevenLabs, LiveKit, and AI coding assistants.
- **Visual:** a two-column "before 4 Oct, 09:00" and "built 4 to 6 Oct" table with a timeline bar. Small logos for services.
- **Note:** the second column lists only merged work.
- **Judging link:** presentation, and the disqualifier on undisclosed work.

## Slide 12. What is next

- **Key points:**
  - Next: more reviewed content across values beyond honesty, parent referral inbox, scholar review workflow, more recitations and Arabic voices.
  - What we need to go further: a scholarly review partner and a pilot with families.
  - The honest limits: a small bank, a few values, and the cases our eval does not cover.
  - Close: "An AI that knows its sources and knows its limits." Live link, repo link, team names.
- **Visual:** a simple roadmap with three steps and the closing line over the meadow image.
- **Judging link:** presentation, innovation.

---

## Screenshot list (take after freeze, Tue 6 Oct 14:30)

| # | Screen | Used on slide |
|---|---|---|
| 1 | Meadow and Al-Sadiq, full screen, phone size | 1, 12 |
| 2 | Child screen: listening, thinking, speaking (meadow call) | 4 |
| 2b | Home walk: two frames of the stroll up the path | 4 |
| 3 | Source card with a working link, Arabic | 3, 7 |
| 4 | Parent dashboard, weekly summary and topics | 3, 8 |
| 5 | Parent summary with no raw text | 8 |
| 6 | Referral to a parent (personal case) | 7 |
| 7 | Health check, repo page signed out | 10 |
| 8 | Eval table and latency figure (with its conditions) | 9 |
| 9 | Badges and quests | 4 |

## Production steps

| Step | Who | When | Done |
|---|---|---|---|
| Choose template, fonts and the Arabic or bilingual decision | [owner] | Mon 5 Oct | [ ] |
| Draft slides 1 to 8 with placeholder screens | [owner] | Mon 5 Oct | [ ] |
| Real screenshots on production | [owner] | Tue 6 Oct 14:30 | [ ] |
| Fill numbers from the final eval and measurements | [owner] | Tue 6 Oct 16:00 | [ ] |
| Arabic text read by a second Arabic reader | [owner] | Tue 6 Oct 16:30 | [ ] |
| Export PDF, check on a clean machine | [owner] | Tue 6 Oct 17:30 | [ ] |
| Remove every claim not merged | [owner] | Tue 6 Oct 18:00 | [ ] |
