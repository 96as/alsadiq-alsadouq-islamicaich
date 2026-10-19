# Idea description

**Project:** Al-Sadiq Al-Sadouq (الصديق الصدوق, "the truthful friend")  
**Track:** Open Track, combining trusted dialogue and interactive learning  
**Status:** updated 5 Oct 2026 (task 10) and checked again on 6 Oct against what is merged on the `hackathon` branch at `735c95a` (after PRs #57 to #62). The deck and the video are written from this description. The wording sent with the application before the window is kept at the end for the record.

## Ready-to-paste English description

Al-Sadiq Al-Sadouq is an AI voice friend for Muslim children aged 6 to 13, with a view for their parents. Children already talk to general AI assistants, but those are not built for Islamic learning at a child's level: they can quote scripture from memory, invent a hadith, give a personal ruling, or turn small talk into a lecture.

The child talks with Sadiq, an animated 3D squirrel in a painted meadow, by voice or by typing, in Arabic or English. Sadiq teaches 38 Islamic values from a bank of 273 items that team members checked against approved sources: 74 verses (King Fahd Complex text via Quranpedia, with Al-Husary's recitation from everyayah.com), 94 hadith from Sahih al-Bukhari and Sahih Muslim with book, number, grade and a dorar.net link, and tafsir, aqidah, fiqh and sirah excerpts from dorar.net, answers from the Bayyinat book and terms from the Al-Jamhara dictionary. A rules layer runs before the model on every turn: safety and distress first, personal rulings referred to a parent, disputed matters marked as such, and a source card only when the child asks. Each card keeps the source's words apart from our simple explanation and links to the source. Verses are played as recitation, never synthesised. With no source, Sadiq says so and suggests asking a parent or teacher.

Parents see weekly summaries, safety alerts, quests to confirm and topics to talk about, never the transcript. Every card shown is recorded with the session, and the parent's "Sources discussed this week" lists those sources with their reference, grade and link, so a parent can open the same source and talk about it. Text written by AI is labelled as such.

The product uses LiveKit for real-time voice, OpenAI for speech recognition (`gpt-4o-mini-transcribe`) and conversation (`gpt-5.4-mini`), ElevenLabs for Sadiq's voice, React and React Three Fiber for the interface and avatar, and Django and PostgreSQL for the backend.

We measure trust as well as engagement. On the same eval cases, the strict pass rate on held-out cases rose from 25% to 44% during the window, the rules layer passes 340 of 392 policy runs with all 92 safety runs passing, and every card on screen links to its source page. The project fits the Open Track by combining trusted Islamic dialogue with an interactive learning journey for children.

## Why this fits the Open Track

The single product combines Track 3's interactive learning journey with Track 1's age-appropriate, source-grounded dialogue. The hackathon work is the improvement of the existing experience during 4 to 6 October, not the earlier capstone build (`docs/hackathon/submission/DISCLOSURE.md`). The [participant guide](https://islamicaich.org/files/Hackathon/i2xgA3mxVhrbRe0ReLlA86kTDbFZ9QQ9eb856dq8.pdf) permits a combined-track solution in the Open Track.

## What each claim rests on

| Claim | Evidence at `735c95a` |
|---|---|
| 273 items, 38 values, all reviewed | `backend/session_moral_context/content/items/*.json`, `values.json`, ledger `content/reviewed.json`; `seed_content` prints "reviewed 273, rejected 0" |
| 74 verses, 94 hadith (60 al-Bukhari, 34 Muslim), the other types | counts in README section 2.3 and `docs/hackathon/readme-media/after/bank-counts.md` |
| "Checked by team members", not by a scholar | the `reviewed_by` field of each item (Abdulrahman Salamah, Abdulrahman Mahmalji); the cards say "Checked against the source by our team". A second hadith check on dorar.net is in progress. |
| Rules before the model, card only when asked | `backend/conversation/agent/turn_policy.py`; tests `conversation/test_card_gate.py`, `conversation/test_distress_gate.py` |
| Source words apart from our explanation; links on the card | `frontend/src/features/child/sources/SourceCard.jsx`, `sourceLabels.js`; `npm run check:cards` |
| Verses as recitation, never TTS | `backend/conversation/agent/tts_text.py`, `scripture_guard.py`; recitation credit on every verse card |
| Parents never see the transcript | the parent API's `preview` is always empty, and summary sentences that copy a run of the child's words are removed (PR #62, `strip_child_echo`): `backend/reporting/test_privacy_prompts.py` |
| Sources recorded per session and shown to the parent | `SessionReport.sources_used`, insights `sources`: `backend/reporting/test_sources.py`; the parent page `SourcesDiscussed` in `frontend/src/features/parent/components/InsightsTrust.jsx` (PR #59); demo families seeded with this week's sources (PR #58) |
| ElevenLabs voice | `TTS_PROVIDER=elevenlabs`, `livekit-plugins-elevenlabs==1.5.1`; xAI only as a manual operator rollback |
| 25% to 44% held-out strict pass | `docs/hackathon/eval-reports/README.md` (one run each side; before = knowledge-bank branch `4fccb39`) |
| 340 of 392 policy runs, 92 of 92 safety | `python manage.py run_eval --settings=config.settings_sqlite_test --no-fail`, run at `8c2ff0d` on 5 Oct and at `08075e1` and `735c95a` on 6 Oct, same output |

## Original application wording (sent before the window, kept for the record)

> Al-Sadiq Al-Sadouq gives children aged 6–13 an AI companion they enjoy talking to while helping them understand and practise Islamic values, with parents involved in the journey. General-purpose AI assistants attract children but are not designed for age-appropriate Islamic moral learning, practical activities, or meaningful parent participation.
>
> Our existing Arabic and English voice-and-text companion pairs a friendly 3D character with storytelling, reflection, quests, points, and badges. A parent dashboard provides summaries, safety alerts, suggested discussion topics, and quest confirmation. The AI can already fetch selected Quran verses and hadiths on demand through function calls, although the source collection and matching are limited.
>
> During the hackathon, we will strengthen this experience by expanding and reviewing the Islamic source collection, improving on-demand retrieval and reference display, enriching the conversation-to-quest journey, and giving parents source-linked insights and clearer ways to discuss and practise values with their child. The product uses LiveKit for real-time voice, OpenAI for speech recognition and conversation, ElevenLabs for speech output, React and React Three Fiber for the interface and avatar, and Django and PostgreSQL for the backend.
>
> We expect stronger child engagement with Islamic values, more parent–child interaction, and greater trust in the guidance. We will assess quest completion, parent participation, and the accuracy and traceability of religious references. The project fits the Open Track by combining trusted Islamic dialogue with an interactive learning journey for children.

Note on that wording: before the window the voice was xAI Grok, not ElevenLabs (`docs/hackathon/CURRENT_STATE.md` section 4); ElevenLabs was the plan and is what the build uses now. Quest completion and parent participation were not measured during the window.
