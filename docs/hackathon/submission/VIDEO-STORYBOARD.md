# Video storyboard: 2 minutes

Written 4 Oct 2026. Arabic narration, English subtitles. **Hard limit 2:00. Target 1:58.** A video over 2 minutes is a disqualifier, so the exported file is checked (checklist B3).

## Rules for this video

- Real screen recordings of the live product only. No mock-ups, no stock footage.
- Synthetic data only. The "child" is a teammate's voice or typed text, never a real child. Demo family names come from the seeded demo accounts.
- No Quran or hadith text appears in this storyboard. On screen, the source card shows whatever the content bank returns for the question, in its exact approved form. Nobody retypes it. Before recording, check the card text against the bank record.
- Recitation, when shown, is the recorded recitation audio, never synthesised.
- Record on production after code freeze (Tue 6 Oct, 14:30). A backup cut is recorded on staging on Mon 5 Oct night, so a submission exists even if production fails.
- Every shot depends on a feature. If the feature is not merged by Mon 5 Oct 21:00, use the fallback column. Do not show a screen that does not work.

## Timeline

| Shot | Time | Length | Section |
|---|---|---|---|
| 1 | 0:00 to 0:10 | 10 s | Hook |
| 2 | 0:10 to 0:22 | 12 s | Meet Al-Sadiq on the meadow |
| 3 | 0:22 to 0:42 | 20 s | The child asks, by voice |
| 4 | 0:42 to 1:02 | 20 s | A grounded answer with a source card |
| 5 | 1:02 to 1:20 | 18 s | The parent view |
| 6 | 1:20 to 1:36 | 16 s | Safety: refer, never a personal ruling |
| 7 | 1:36 to 1:48 | 12 s | Built for real use |
| 8 | 1:48 to 1:58 | 10 s | Close |
| | | **118 s** | **1:58, with 2 s of margin** |

## Shot by shot

### Shot 1, 0:00 to 0:10, hook

- **Visual:** black screen. A child's question appears as a chat bubble. A second bubble shows a confident, wrong-looking answer with a red "no source" tag (a staged example made in our own UI, clearly labelled "example of an ungrounded chatbot"). The staged answer must hold no verse, no hadith and no religious ruling, real or invented: blur its text and let the red tag make the point. Cut to the title "الصديق الصدوق" over the painted meadow.
- **Arabic narration:** «طفلٌ يسأل، والذكاء الاصطناعي قد يخطئ. فكيف نثق بما يسمعه أبناؤنا عن دينهم؟»
- **English subtitle:** "A child asks. AI can be wrong. How can we trust what our children hear about their faith?"
- **Sound:** a soft low tone, then the meadow's ambience on the cut.
- **Fallback:** none needed, this shot is made of our own screens.

### Shot 2, 0:10 to 0:22, the meadow

- **Visual:** the child opens `alsadiqai.com` on a phone-sized window and taps the demo start. The child's Home shows the painted meadow, and the squirrel Al-Sadiq walks up the path and idles, with a stroll or a short wave (concept 1 in `JUDGE-DEMO-SCRIPT.md`). The meadow is the product scene; the 3D forest is an opt-in flag (`?forest=1`) that the demo does not use, so do not record it. Quick overlay chips: "6 to 13 years", "Arabic first", "voice and text".
- **Arabic narration:** «هذا هو الصديق الصدوق، رفيقٌ صوتيٌّ للأطفال من سنّ السادسة إلى الثالثة عشرة. يلتقيه الطفل ويحادثه بالعربية.»
- **English subtitle:** "This is Al-Sadiq Al-Sadouq, a voice companion for children aged 6 to 13. The child meets him and talks with him in Arabic."
- **Fallback:** none needed: this is the default product screen. The meadow painting is pre-existing and disclosed (`DISCLOSURE.md` section 2.4).

### Shot 3, 0:22 to 0:42, the child asks

- **Visual:** the child taps the microphone. The avatar tilts and leans in (listening), then looks up and sideways (thinking), then speaks with the jaw moving to the real voice. Add a small caption in the edit, because the product has no such label: listening, thinking, speaking.
- **Spoken on screen (the child, a teammate):** «يا صادق، لماذا يجب أن أقول الحقيقة حتى لو كنتُ خائفًا؟»
- **Arabic narration (after the question, over the thinking pose):** «يُنصت الصديق، ثم يفكّر، ثم يجيب بصوتٍ دافئ وكلماتٍ يفهمها الطفل.»
- **English subtitles:** "Child: Al-Sadiq, why must I tell the truth even when I am afraid?" then "Al-Sadiq listens, thinks, and answers in a warm voice, in words a child understands."
- **Timing inside the shot:** 0 to 6 s the question (a pause for the subtitle), 6 to 11 s listening and thinking with narration, 11 to 20 s the start of Al-Sadiq's spoken answer. Let it run into shot 4, ducked low under the narration.
- **Fallback:** if voice does not work in production, record on the text mode and say "يكتب الطفل أو يتحدث" (the child types or speaks). Keep the avatar states.

### Shot 4, 0:42 to 1:02, grounded answer and source card

- **Visual:** split screen. Left: the answer bubble, short and child-level. Right: the source card slides in, showing the source name (from the approved list), the item type, the grade for a hadith, and an "open source" link. The cursor taps the link and the source page opens for one second, then returns. If the answer includes a verse, a play button on the card plays the recitation audio and the waveform animates.
- **Arabic narration:** «قبل أن يُجيب، يبحث الصديق في بنكِ محتوًى موثَّق: لا مصدر، فلا جواب. وتُظهر بطاقةُ المصدر اسمَه، ودرجةَ الحديث، ورابطَه. وتُسمَع الآيات بتلاوةٍ مسجَّلة، لا بصوتٍ مُولَّد.»
- **English subtitle:** "Before answering, Al-Sadiq searches a verified content bank: no source, no answer. The source card shows the source, the hadith grade and a link. Verses are heard in recorded recitation, never a generated voice."
- **Overlay text:** "No source, no answer" (Arabic: «لا مصدر، لا جواب»).
- **Depends on:** tasks 01, 03 and 05 (content bank, grounding, source card and recitation). Source name and grade are read from the bank record, not typed. The bank holds verses only today (74 reviewed verses, no hadith: `handoffs/product-web.md` section 16), so the card will not show a hadith grade. Unless a hadith card is on screen, drop «ودرجةَ الحديث» from the narration and "the hadith grade" from the subtitle.
- **Fallback:** if the recitation is not ready, remove the last sentence of narration and the play button. If the source card is not ready, do not record this shot. Merge shots 4 and 6 and tell the story with the referral and the parent view only.

### Shot 5, 1:02 to 1:20, the parent view

- **Visual:** cut to the parent dashboard on a laptop, signed in as a demo parent. The weekly summary, the week's activity and the suggested topics to talk about are visible, and the screen shows no raw chat transcript.
- **Arabic narration:** «ولِيُّ الأمر يتابع تقدّم طفله وملخّصه الأسبوعي، لا نصَّ المحادثة، فتبقى خصوصية الطفل محفوظة، ويجد ما يُكمل به الحديث معه.»
- **English subtitle:** "The parent follows the child's progress and weekly summary, not the chat transcript. The child's privacy is kept, and the parent has topics to follow up on."
- **Depends on:** the parent view as it is, which now includes "Sources discussed this week" (task 04, PR #59; it may be shown in this shot). "Not the transcript" holds: the parent API's `preview` is empty since `caa2d65`; check it again in the recorded build.
- **Fallback:** if the recorded build shows any raw chat text in the parent view, change the narration to «ولِيُّ الأمر يتابع تقدّم طفله وملخّصه الأسبوعي» ("The parent follows the child's progress and weekly summary"), and do not mention privacy.

### Shot 6, 1:20 to 1:36, safety

- **Visual:** back to the child screen. The child asks (typed or spoken): «هل أُفطر اليوم؟ أشعر بدوار.» Al-Sadiq answers kindly and refers: tell a parent now, and ask a scholar for a ruling. A "Tell a parent" button highlights, and a small badge reads "Referred" (Arabic: «أُحيل إلى الوالدين»). Then a second quick test: the child types «أعطني حديثًا حتى لو لم يصح»; the answer declines and offers a sourced alternative.
- **Arabic narration:** «وحين يسأل الطفل عن حالتهِ الشخصية، لا يُفتي الصديق. بل يُحيله بلطفٍ إلى والديه وإلى عالِم، ولا يُخمّن أبدًا.»
- **English subtitle:** "When a child asks about a personal case, Al-Sadiq does not give a ruling. He gently refers the child to parents and a scholar, and never guesses."
- **Depends on:** tasks 03 and 09 (decision step, eval cases).
- **Fallback:** if the second test is not reliable, keep only the first.

### Shot 7, 1:36 to 1:48, built for real use

- **Visual:** a fast montage over a dark panel with four proof chips, each an actual screen or figure: the architecture diagram with the grounding step highlighted, the eval result (186 cases in the set, 61% strict on 143 scored runs, 44% on the held-out split alone; `eval-reports/README.md`, one run each), latency (end of the child's question to first audio, about 2.0 to 2.6 s median at 1 to 10 sessions on a local stack; `latency/LOAD-REHEARSAL.md`; a single figure with its conditions, not a before and after), and the live link with the health check showing OK. The avatar size figure can be used if the others are late: "43 MB to 2.5 MB" (the shipped animated avatar, `handoffs/product-web.md` section 13; the older "0.69 MB" file is no longer shipped). If the eval chip cannot carry its conditions (one run, text channel, held-out 44%) in the time on screen, drop it, per the rule below.
- **Arabic narration:** «مبنيٌّ للاستخدام الحقيقي: تعرُّفٌ على الكلام، ونموذجٌ لغويٌّ، وصوتٌ عربي، ومنشورٌ على الإنترنت اليوم، مع اختباراتٍ للسلامة والتأصيل.»
- **English subtitle:** "Built for real use: speech recognition, a language model, an Arabic voice, live on the internet today, with safety and grounding tests."
- **Rule:** every figure on screen is copied from the final eval or the measurement report, with the date. If a figure is not final by Tue 16:00, remove the chip. Never show a placeholder.

### Shot 8, 1:48 to 1:58, close

- **Visual:** the meadow again, Al-Sadiq on the Home path in his idle motion (he strolls or gives a short wave every few seconds; do not wait for a wave on cue). The logo and the link `alsadiqai.com` fade in. One line of credit: "Islamic AI Challenge, Open Track". A last small line: "AI tool: answers come from verified sources" (the AI disclosure).
- **Arabic narration:** «الصديق الصدوق: ذكاءٌ اصطناعيٌّ يعرف مصدره، ويعرف حدَّه. جرِّبوه الآن.»
- **English subtitle:** "Al-Sadiq Al-Sadouq: an AI that knows its sources and knows its limits. Try it now."
- **Sound:** soft music up for the last 3 seconds, ending with a clean fade by 1:58.

## Narration script, in one block (Arabic, for the voice-over reader)

1. طفلٌ يسأل، والذكاء الاصطناعي قد يخطئ. فكيف نثق بما يسمعه أبناؤنا عن دينهم؟
2. هذا هو الصديق الصدوق، رفيقٌ صوتيٌّ للأطفال من سنّ السادسة إلى الثالثة عشرة. يلتقيه الطفل ويحادثه بالعربية.
3. يُنصت الصديق، ثم يفكّر، ثم يجيب بصوتٍ دافئ وكلماتٍ يفهمها الطفل.
4. قبل أن يُجيب، يبحث الصديق في بنكِ محتوًى موثَّق: لا مصدر، فلا جواب. وتُظهر بطاقةُ المصدر اسمَه، ودرجةَ الحديث، ورابطَه. وتُسمَع الآيات بتلاوةٍ مسجَّلة، لا بصوتٍ مُولَّد.
5. ولِيُّ الأمر يتابع تقدّم طفله وملخّصه الأسبوعي، لا نصَّ المحادثة، فتبقى خصوصية الطفل محفوظة، ويجد ما يُكمل به الحديث معه.
6. وحين يسأل الطفل عن حالتهِ الشخصية، لا يُفتي الصديق. بل يُحيله بلطفٍ إلى والديه وإلى عالِم، ولا يُخمّن أبدًا.
7. مبنيٌّ للاستخدام الحقيقي: تعرُّفٌ على الكلام، ونموذجٌ لغويٌّ، وصوتٌ عربي، ومنشورٌ على الإنترنت اليوم، مع اختباراتٍ للسلامة والتأصيل.
8. الصديق الصدوق: ذكاءٌ اصطناعيٌّ يعرف مصدره، ويعرف حدَّه. جرِّبوه الآن.

Word count is about 140 words of narration (excluding the child's question). At a calm pace of about 2 words per second this takes about 70 s, which leaves room for the child's lines, the avatar pauses and the transitions. The busiest shot is shot 4: about 27 words (about 14 s) in 20 s, plus a short recitation clip. Read each line aloud against the shot timing before recording. If a line runs over its shot, cut words, never speed up.

## Subtitles

- English, white text with a dark band, bottom third, never over the source card or the avatar's face.
- At most two lines, about 42 characters per line, each cue on screen at least 2 seconds.
- The Arabic child lines on screen are not subtitled twice: the English cue replaces the Arabic text only when it is spoken, not typed on screen.
- Export a separate `.srt` as a backup, but burn the subtitles into the final file so they always show.

## Production checklist

| Step | Who | When | Done |
|---|---|---|---|
| Pick the narrator (an Arabic speaker, clear MSA) and the "child" voice (adult teammate) | [owner] | Mon 5 Oct | [ ] |
| Arabic narration reviewed by a second Arabic reader for grammar and vowel marks | [owner] | Mon 5 Oct | [ ] |
| Backup cut on staging, exported, duration checked | [owner] | Mon 5 Oct night | [ ] |
| Final recording on production, 1080p, browser at 100% zoom, notifications off, no personal tabs | [owner] | Tue 6 Oct 14:30 | [ ] |
| Source card text compared against the bank record, character by character | [owner] | Tue 6 Oct 15:00 | [ ] |
| Metrics chips filled from the final report | [owner] | Tue 6 Oct 16:00 | [ ] |
| Export, play the final file from the start to the end, confirm duration under 2:00 | [owner] | Tue 6 Oct 17:00 | [ ] |
| Upload with the submission | [owner] | Tue 6 Oct 20:00 | [ ] |

## Tools and music

- Screen capture and editing tools `[confirm which]`, listed in `docs/AI_TOOLS.md` if any AI tool is used.
- Music and sound effects must be licence-free or self-made, and listed in `THIRD_PARTY.md` with the licence. `[confirm track and licence]`
- If an AI voice is used for the narration, say so in the video description and the disclosure. A human narrator is preferred.
- The earlier commercial plan mentions another AI video tool (Higgsfield). If any footage from it is used, disclose the tool and its terms. The storyboard above does not need it.
