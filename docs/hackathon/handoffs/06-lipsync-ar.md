# Handoff: Task 06, research-first Arabic lip sync (reviewed)

- **Date:** 2026-10-04
- **Owner:** Majd
- **Branch:** `hk/06-lipsync-ar` (local only, never pushed). Base `cec85d0` = the tip of `hk/06-avatar-live`, so it merges as a fast-forward.
- **Worktree:** `%USERPROFILE%\Documents\Alsadiq-wt\06-lipsync-ar`
- **Research and plan:** `%USERPROFILE%\Documents\Alsadiq-wt\lipsync-research\` (`RESEARCH-1-sota.md`, `RESEARCH-2-arabic.md`, `PLAN.md`). The acceptance bars are `PLAN.md` section 8.
- **Commits, oldest first:**

| Commit | What | By |
|---|---|---|
| `f29226a` | test(lipsync): Arabic ground-truth set, synth script and evaluation harness | builder |
| `2b7877c` | feat(lipsync): Arabic vowel mode, full vowel poses and a visible jaw | builder |
| `27cba71` | feat(lipsync): text-timed Arabic visemes from TTS alignment, with audio latch | builder |
| `ab977bc` | feat(agent): forward ElevenLabs character timings for lip sync behind LIPSYNC_TIMELINE | builder |
| `bb829f7` | fix(lipsync): keep the text clock steady at 48 kHz, add eval --sr | builder |
| `ad0edbb` | feat(lipsync): timeline replay in the lab and the avatar preview | builder |
| `a929436` | docs(hackathon): handoff for Arabic lip sync (replaced by this file) | builder |
| `5099903` | fix(lipsync): keep English closures shut and the text clock running through early pauses | reviewer |
| `6ee4f72` | perf(lipsync): vowels lead by 25 ms, full vowel poses, quicker hand-over | reviewer |
| `8faeaa0` | feat(lipsync): English eval clips and a frame sampler in the lab | reviewer |
| this file | docs(hackathon): reviewed handoff for Arabic lip sync | reviewer |

The builder's seven commits end with `Co-Authored-By: Claude Code` (its session told it to). The brief asked for `Claude Opus 5.5 (1M context)`; the reviewer's commits use that. History was not rewritten.

## 1. In one minute

- **Before:** the mouth followed the sound only. In Arabic it never closed on م or ب (0 of 27 on the held-out lines), read fatha as E, lagged the sound by about 40 ms, and barely opened.
- **Now:** when the agent sends the ElevenLabs character timings (flag `LIPSYNC_TIMELINE=1`, off by default), the mouth is timed by the text and coloured by the audio. Held-out lines: lips close on 27 of 27 م/ب and stay shut for at least 50 ms on 25 of 27 (diac) and 26 of 27 (plain); the mouth leads the sound by 30 to 43 ms; vowel identity 0.85 with long vowels 1.00. Without a timeline (flag off, English, a lost packet) the audio-only path runs, and it is also much better than before (identity 0.86, fatha fixed).
- **Live Edge check (real browser path, 48 kHz):** 27 of 27 closures, 26 of 27 held, on the 10 held-out lines.
- **Majd's eye check is still the final word** (section 6).
- **Bars still missed** (not loosened): F1 (frame accuracy gain), R1 on the plain variant, K1 for the audio-only path. Details in section 5.

## 2. What was researched

Two researchers and a director worked before any code (files above). Main findings:

- **State of the art** (RESEARCH-1): audio-only browser methods (the current DSP, HeadAudio's MFCC classifier) cannot see a closed-lip /m/, because a nasal murmur has no silence. GPU models (NVIDIA Audio2Face-3D) are server-only and not trained on Arabic; OVRLipSync, Mascotbot and Azure visemes are closed or do not match our ElevenLabs audio. Text timing gives exact closures for free if the TTS reports it.
- **Our stack** (RESEARCH-2, verified in code and with the real API): ElevenLabs flash v2.5 returns per-character start and duration for Arabic, on the websocket the agent already uses. livekit-plugins-elevenlabs 1.5.1 receives them and collapses them to words; a small wrapper keeps the characters. The LiveKit data channel can carry them (reliable, 15 KiB packets).
- **Arabic phonetics:** few lip-visible contrasts. م ب close the lips, ف puts teeth on the lip, و and damma round, the rest is tongue or throat and should let the neighbouring vowel show through (dominance, Cohen and Massaro). Only three vowel qualities (a, i, u); the voice's fatha sits at F1 about 550, F2 about 1550 Hz, which the English E prototype swallowed.
- **Sync tolerance:** viewers notice audio ahead of the picture from about 45 ms, picture ahead of audio only from about 125 ms (ITU-R BT.1359), so the mouth should lead, not lag. In running speech the natural audio-visual offset is small, from about 20 ms audio lead to about 70 ms visual lead (Schwartz and Savariaux 2014); mouth movement before an utterance starts can lead by 100 to 300 ms (Chandrasekaran et al. 2009).
- **Short vowels** are not written in replies. A diacritiser (libtashkeel MIT, CATT Apache-2.0) was deferred; the audio decides the short vowel instead.

## 3. What was chosen and why

**Hybrid: timing and closures from the text, short-vowel colour and loudness from the audio** (PLAN.md section 0).

```
agent (LIPSYNC_TIMELINE=1): ElevenLabs char times -> tts_node tap -> data topic lk.lipsync
   {"v":1,"sp":"<speech id>","seq":0,"lang":"ar","t":[["م",0,139],...]}   ms from the first sample
   {"v":1,"sp":"<id>","go":1}     the agent starts speaking this speech
   {"v":1,"sp":"<id>","stop":1}   interrupted
browser: TimelineSync (clock latched to the first sound, re-anchored at pauses, held over stalls)
   -> arabicText.buildTrack (letters to mouth segments: closures, long vowels, vowel slots, pauses)
   -> TrackSampler (dominance blend, PP and FF floors, lead) + audio engine (gate, level, a/i/u)
   -> HybridLipsync -> 14 Oculus visemes -> LipsyncRig morphs + jaw (ClipAvatar)
no timeline, not latched, or stale -> exactly the audio-only output (R2)
```

Why not the alternatives: a playback delay (DelayNode) adds 90 ms to every reply while the team is cutting latency; a retrained MFCC classifier or a diacritiser does not fix the missing closures, the largest visible flaw. Both stay as next steps.

Safety rules kept: a timeline is shown only after its `go` (a preemptive reply that is thrown away never shows); a `stop`, the agent leaving "speaking" for 400 ms, or 300 ms past the end clears it; the agent never awaits anything on the audio path (a sender queue); the backend flag is off by default; `VITE_LIPSYNC_TIMELINE=0` is the browser kill switch.

## 4. What the review found and changed

1. **English timelines did not close the lips.** In `lang: en` every non-labial letter is an "unknown" span whose audio share was blended in after the PP floor, so the lips never met (offline 12 to 14 of 23 closures, 0 held). Fix: no audio share inside a closure or labiodental. Now 23 of 23, 19 to 20 held. (`timelineTrack.js`)
2. **The text clock fell behind at pauses.** The stall rule held the clock whenever the voice stopped more than 50 ms before the alignment's pause (silent final letters, an English silent e, a fading consonant). On an English line the clock ended 1.2 s behind; in Arabic it fired on 10 of the 30 diacritised lines (mostly near the end) and, at 48 kHz, on 2 plain lines. Fix: a silence that starts at most 200 ms before a text pause is that pause (unless it is digital silence, which a TTS pause never is and a network stall is); a silence that outlasts a pause by 300 ms is a stall held at the end of the pause; re-anchoring happens only after a pause of the text. (`timelineSync.js`)
3. **The `'?'` speech-id fallback was not implemented in the browser.** The agent sends `"sp":"?"` when it cannot read livekit's speech handle; the browser dropped those timelines at the next `go`. Now the next `go` takes the newest unstarted `'?'` timeline and its later packets. (`timelineSync.js`)
4. **Vowels were shown too early.** With the 50 ms lead, a short vowel's frames showed the next consonant, and a slot showed its prior (a) before the audio had voted. Vowels now lead by 25 ms, closures and rounding still by 50 ms. Identity 0.80 to 0.85, long vowels 0.88 to 1.00. (`vowelLeadMs`)
5. **The mouth was still small in the hybrid.** Undershoot and fast-speech scaling are off and the timeline vowels let go at 38/s instead of 30/s: K1 0.74 to 0.80, K2 0.59 to 0.62, K3 77.8 to 92.6 percent (diac).
6. **A reply starting with م/ب missed its closure** when the `go` and the sound arrive together (the eval's worst case). Hand-over rate 25 to 60/s: line-initial closures 14 to 16 of 16 on the tune split.
7. **English is not untouched** (the builder's handoff said it was). `SMOOTHING.attack.aa` 24 to 60 and the jaw changes are shared. Measured on the 7 English audition clips, audio only, against the base: open-vowel lag (against the loudness envelope) 50 to 33 ms, motion above 10 Hz 0.69 to 0.73 percent median (max 0.99, still under 1), jaw about 1.5 times wider. Not a regression; the 22 old tests pass.

Fixes 1 to 4 each have a unit test that fails on `a929436` (5 new tests with the vowel lead, 80 in all). All tuning was done on lines 1 to 20 only.

Tried and dropped: making the vowel before a long vowel a voted slot (for diphthongs like كيف; +0.2 points, cost one R1 line); letting a closing PP keep its weight in the smoother (K3 up but identity down 4 points and motion above 10 Hz 1.65 percent).

## 5. Numbers, every bar (held-out lines 21 to 30)

Scored at the clips' 22.05 kHz, as PLAN.md defines; 48 kHz (the live rate) in brackets. "diac" is the voweled variant (the vowel ground truth; the hybrid still gets the letters only), "plain" is the text as a reply has it. Before = the old engine at `cec85d0`. Builder = `a929436`. Reviewed = `8faeaa0`.

| Bar | Metric | Before | Builder | Reviewed | Bar | Result |
|---|---|---|---|---|---|---|
| G0 | GT validity | n/a | pass | pass: pauses 37.9 dB under letters, F1/F2 in order (a 553/1554, i 311/2127, u 350/1041 Hz), bias +13 ms | all pass | pass |
| A1 | audio-only vowel identity | 0.58 | 0.86 | 0.86 [0.90]; always-a 0.57; a .96 i .77 u .61 | >= 0.75, >= always-a + .04; a .85 i .55 u .35 | pass |
| A2 | audio-only lag, >10 Hz, old tests | +38 ms, 0.5 % | +40 ms, 0.8 % | +40 ms [+26], 0.8 % [0.9], 22 of 22 | <= +85 ms, < 1 % | pass |
| C1 | closure hit | 0/27 | .96 (م .94, ب 1) | 1.00 both variants (م 17/17, ب 10/10) [1.00] | >= .90, each >= .85 | pass |
| C2 | false closures per s | 0 | 0.00 | 0.00 | <= 0.3 | pass |
| L1 | openness lag | +38 ms | diac -34, plain -47 | diac -30, plain -43 [-23, -50] | -60 to 0 | pass |
| L2 | closure onset | n/a | -51, -55 | -51, -55 [-59, -58] | -60 to +15 | pass |
| V2 | hybrid identity (diac) | 0.58 | 0.80, long 0.88 | 0.85, long 1.00 [0.87, long 1.00] | >= A1 - .02 (0.84), long >= .90 | pass (at 48 kHz 0.87 vs 0.88, short by .01) |
| F1 | lenient frame accuracy gain | n/a | diac -1.9, plain +5.8 | diac +1.1 (62.6 vs 61.5), plain +5.4 (58.8 vs 53.4) | >= +15 points | miss |
| S1 | >10 Hz share | 0.5 % | 1.2, 1.1 % | 1.3, 1.2 % [1.4, 1.2] | < 1.5 % | pass |
| R1 | lines passing (none, late, stall, stale) | n/a | diac 9,9,8,9; plain 7,6,7,7 | diac 10,9,9,10 [9,9,9,9]; plain 8,7,8,8 [9,7,8,9] | >= 9 of 10 | diac pass, plain miss |
| R2 | no timeline = audio-only | n/a | pass | pass (unit tests) | identical | pass |
| P1 | hybrid step cost | n/a | +0.002 ms | +0.0011 ms over the engine's 0.073 ms (node, 48 kHz); no per-frame array | < 0.05 ms | pass |
| D1 | flag off | n/a | pass | pass (unit tests) | unchanged, nothing sent | pass |
| D2 | flag on | n/a | pass | pass; 477 of 477 backend tests | tests | pass |
| K1 | p75 aa on open vowels (hybrid; audio-only) | 0.08 | .74, .79; .78 | .80, .84 [.79, .83]; audio .78 [.81, .80] | >= .80 | hybrid pass; audio-only miss at 22 kHz |
| K2 | jaw p90 of JAW.max (hybrid; audio-only) | 0.29 | .59, .54; .63 | .62, .62 [.59, .59]; audio .63, .62 [.60, .60] | >= .6, JAW.max by eye | pass at 22 kHz; hybrid .01 short at 48 kHz |
| K3 | PP >= .9 held 50 ms | 0/27 | 77.8, 85.2 % | 92.6, 96.3 % [92.6, 96.3] | >= 85 % | pass |
| E1 | eye check | n/a | sheets | new sheets, live Edge recordings (below) | Majd decides | needs Majd |
| Hygiene | lint, build, no audio, no new dependency, flag off | | | lint 0, build ok (no lab, no dev-audio in dist), no audio in git, no dependency, `LIPSYNC_TIMELINE=0` | | pass |

Why the misses remain:
- **F1:** recessive consonants let the vowel show through (by design), and the audio-only path was already strong once Part B landed, so a 15-point gain over it is not reachable without per-consonant tongue shapes the avatar does not have.
- **R1 plain:** ar24 (lag -82 ms, limit -80), ar26 (+32 ms) and, under "late", ar22 (the line-start meem is over before the late `go`). The plain ground truth has no vowel timing (a letter span holds its unwritten vowel), so per-line lag on plain lines is a crude, noisy measure: ar26's correlation peak is 0.54 and broad. Diac lines, which have real vowel timing, pass all four runs.
- **K1 audio-only:** passes on the tune split (0.82, 0.86) and at 48 kHz on diac (0.81); misses on the held-out 22 kHz clips (0.78). Not tuned further on the test lines.

**Live in Edge** (Playwright, `channel=msedge`, the lab playing each clip through the real media element, Web Audio analyser at 48 kHz, rAF about 57 fps, every frame recorded):

| | Arabic held-out, text timing | Arabic, audio only | English en01-03, text timing | English, audio only |
|---|---|---|---|---|
| closures (PP >= .5, 2 frames) | 27 of 27 | 0 of 27 | 22 of 23 | 0 of 23 |
| PP >= .9 held 50 ms | 26 of 27 | 0 | 15 of 23 | 0 |
| >10 Hz after the rig | 0.7 to 1.4 % | 0.7 to 1.5 % | 2.6 to 3.1 % | 0.75 to 0.97 % |
| lag against the element clock (median) | -2.5 ms | +35 ms | n/a | n/a |

Headless Edge reports an output latency of 40 ms, which the hybrid takes off its lead (`leadMs - outputLatency`), so at the speaker the text-timed mouth leads by about 40 ms and the audio-only mouth is within about 5 ms of the sound. The clock held steady: in a recording of ar24, position minus element time was 14 ms with a 4 ms spread over the whole line.

## 6. See it, run it, evaluate it, tune it

**In the browser** (port 5321, never 5311; Majd's Docker stack and build stay untouched):

```
cd %USERPROFILE%\Documents\Alsadiq-wt\06-lipsync-ar\frontend
npx vite --port 5321 --host 127.0.0.1
```

- Lab: `http://127.0.0.1:5321/dev/lipsync?clip=ar24.plain&avatar=1` (add `&timeline=0` for audio only). The "Eval line" list has ar01 to ar30 (plain, then diac) and, if present, en01 to en03. "Text timing" toggles; the scrub shows any frame on the real morphs.
- Avatar preview: `http://127.0.0.1:5321/avatar-component-preview.html?clip=ar24.plain&timeline=1`, then "speak audition clip". `?clip=en02` plays English with closures from the text.
- Eye-check sheets (Edge, real morphs, 3 closures and 3 vowels, audio only above, text timing below), in `%USERPROFILE%\Documents\Alsadiq-wt\shots\lipsync-ar\`: `review-ar22-plain-…`, `review-ar24-plain-…`, `review-ar26-plain-…`, `review-en02-audio-vs-timeline.png`, and `review-preview-speak-strip.png` (Speak button: ar24 text timing, ar24 audio only, en02). The builder's sheets without `review-` show the build before this review.

**Tests and checks:**

```
cd frontend
npm run lint                  # 0 errors, 0 warnings
npm run build                 # lab, dev-audio and eval clips are not in dist
npm run test:lipsync          # 80 tests (22 old, Arabic, timeline, sync, P1)
cd ../backend
set PYTHONPATH=%USERPROFILE%\Documents\Alsadiq-wt\_venv-lipsync\site;%USERPROFILE%\Documents\Alsadiq-wt\lipsync-research\_scratch\pylib2
python manage.py test --settings=config.settings_sqlite_test      # 477 tests
```

`test_voice_wiring.py` needs livekit on the path to import (that was so before this branch).

**Offline evaluation** (clips are gitignored; re-create them with `python scripts/lipsync-eval/synth_testset.py`, about 2,700 characters, the key is read inside the script and never printed):

```
node scripts/lipsync-eval/eval.mjs --mode hybrid --split test            # the bars
node scripts/lipsync-eval/eval.mjs --mode audio  --split test
   --sr 48000        the live rate      --stress late|stall|stale     the R1 runs
   --split tune      tune here only     --set TIMELINE.vowelLeadMs=35  sweep one number
```

Each run writes `dev-audio/eval-ar/report-<tag>.json` (confusions, per-line R1, 14x14 matrix).

**Reviewer tools** (not in git, `%USERPROFILE%\Documents\Alsadiq-wt\lipsync-research\_scratch\reviewer\`): `summ.mjs` (the whole matrix in one table), `sweep.mjs` (overrides any config object, including arrays), `live_record.py` and `live_score.mjs` (record and score live Edge plays), `english-timeline.mjs` (English closures), `english-regress.mjs` (English audio-only against the base), `diag_vowels.mjs` (why a vowel frame is wrong), `shots_review.py` and `preview_review.py` (the sheets). `synth_en.py` made the three English lines in `frontend/dev-audio/eval-en/` (gitignored, 219 ElevenLabs characters, key read inside the script only).

**Tuning knobs** (all in `lipsync/lipsyncConfig.js` unless noted; tune on `--split tune`, then check `test` at both rates):
- `TIMELINE.leadMs` (50) closures and rounding ahead of the sound; `vowelLeadMs` (25) vowels. Lower both if the mouth looks early on a phone.
- `TIMELINE.ppFloor` (0.95), `closureHoldMs` (120), `bMinMs`/`mMinMs` how firmly and how long lips close.
- `TIMELINE.alpha`, `thetaBefore`, `thetaAfter` per role: how much consonants cover the vowels.
- `TIMELINE.undershoot`, `fast` (1.0 = off) and `TIMELINE_SMOOTHING` for the size and speed of the text-timed mouth.
- `ARABIC.f2i`, `f1i`, `f2u`, `f1u` the a/i/u rule; `ampBase`, `ampSpan` the vowel size.
- `JAW` in `avatarConfig.js`: `max` 0.28 rad, `levelCouple` 0.55. Judge by eye first, then re-run K2.
- Sync: `latchOffsetMs`, `stallMs`, `pauseAheadMs`, `pauseOverrunMs`, `reanchorMaxStepMs`.

## 7. Agent side and the live smoke test

`backend/conversation/agent/lipsync_timeline.py` (Part D) wraps the plugin's private `_to_timed_words` (only on livekit-plugins-elevenlabs 1.5.1, else it logs once and stays off), taps `tts_node` without delaying frames, offsets times across `tts_node` calls of one speech, splits at 120 characters, publishes `go` on "speaking" and `stop` on interruption. `tts_factory.build_tts(lipsync_alignment=True)` adds `sync_alignment` without changing the chat transcript. Flag off gives byte-identical arguments (D1 tests).

**Not run live** (it needs the agent on Majd's LiveKit stack and spends ElevenLabs characters). Steps:
1. `LIPSYNC_TIMELINE=1` in the agent's environment, restart the agent. Leave `VITE_LIPSYNC_TIMELINE` unset.
2. Open the child voice screen in Edge with an Arabic profile; say a sentence.
3. In devtools, log `RoomEvent.DataReceived` for topic `lk.lipsync` (a temporary `console.log` in `useLiveKitRoom.js`). Expect `seq` packets before the first sound, one `go`, a `stop` only when interrupted.
4. Watch م and ب close. Interrupt mid-sentence: the mouth must fall back to the audio at once.
5. Compare time to first audio with the flag on and off (`sync_alignment` cost is unmeasured).
6. Try a phone and a Bluetooth speaker (150 to 250 ms output latency; the lead goes to 0 above 50 ms).

## 8. Known issues

- **English with the flag on moves faster** (2.6 to 3.1 % above 10 Hz, against 0.7 to 1.0 % audio-only). It is the crisp closures themselves (most of English motion energy is now PP), not flicker, but have a look in the lab (`?clip=en02`). English PP hold is 15 to 20 of 23.
- **Diphthongs** (كيف kayf, يوم yawm) show i or u where a is heard first; about 3 % of vowel frames.
- **Short vowels before the audio arrives:** a slot shows a (the prior) for its first 25 ms; a is 57 to 70 % of vowel frames, so the prior is usually right.
- **Late `go`:** a closure that is already over when `go` arrives cannot be shown (ar22 under "late").
- **The eval is synthetic:** 30 lines, one voice, TTS alignment as ground truth (bias +13 ms, shifted out). One held-out line is 10 % of R1. The plain ground truth has no vowel timing.
- **Output latency** is taken from `AudioContext.outputLatency`; Safari and Bluetooth may under-report it.
- **Private plugin internals** (`_to_timed_words`, `_SpeechHandleContextVar`) can change in an update; versions are pinned at 1.5.1 and the tests fail loudly.
- **`hk/06-mouth-acting`** merged an earlier state of this branch (`27cba71`, `ab977bc`) and changed the same `STALLED` case in `timelineSync.js` for the same early-stall problem. Expect a conflict there (section 9).
- **`hk/08-latency`** edits `agent_class.py` and `entrypoint.py` (no `tts_node` override); expect text conflicts, not logic ones. Its hum filler is not a TTS speech, so it gets audio-only shapes.

## 9. Next steps

1. **Majd's eye check** in the lab and on Speak (section 6). If the open vowel feels small, raise `JAW.max` and re-run K2.
2. **Merge into `hk/06-avatar-live`:** it is a fast-forward (`git -C %USERPROFILE%\Documents\Alsadiq-wt\06-avatar-live merge --ff-only hk/06-lipsync-ar`, run by whoever owns that worktree). Then run `npm run test:lipsync`, `npm run lint`, the backend tests, and one eval run.
3. **Then merge `hk/06-mouth-acting`:** in `timelineSync.js` keep this branch's `STALLED` case and `pauseEnd`/`silenceExpected` (they cover its early-stall case and the long-pause case), keep its rig, jaw and Speak changes, and re-run `--split test` at both rates plus its own acting gates.
4. **Live smoke** with `LIPSYNC_TIMELINE=1` (section 7), then decide whether to turn it on for the demo.
5. **Score real replies:** record a few live Arabic replies with their timelines and run the closure and lag scores on them.
6. **Vowels:** a shadow diacritiser (libtashkeel, MIT) as the slot prior, or an MFCC classifier trained on the eval audio (HeadAudio method, MIT), if a/i/u still look wrong by eye.

## 10. Licences

All new code is our own; nothing was copied. Ideas only: Cohen and Massaro dominance, the JALI jaw and lip split, ITU-R BT.1359 thresholds, Schwartz and Savariaux asynchrony ranges. No new npm or pip dependency. HeadAudio and TalkingHead (MIT) were read for ideas only. Nothing from GPL or non-commercial sources (Mishkal, espeak-ng, Arabic-Phonetiser, MMS weights). ElevenLabs audio and alignment stay in the gitignored `frontend/dev-audio/` and are not in git or in `dist`. The test-set text is original, with no scripture or religious text.

## 11. Sources

- Cohen and Massaro, co-articulation and dominance: https://link.springer.com/chapter/10.1007/978-4-431-66911-1_13
- JALI, jaw and lip axes: https://dgp.toronto.edu/~elf/JALISIG16.pdf
- ITU-R BT.1359-1, audio-video sync thresholds: https://www.itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.1359-1-199811-I!!PDF-E.pdf
- Schwartz and Savariaux 2014, audiovisual asynchronies in chained speech: https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003743
- Chandrasekaran et al. 2009, natural statistics of audiovisual speech: https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1000436
- ElevenLabs with-timestamps: https://elevenlabs.io/docs/api-reference/text-to-speech/convert-with-timestamps
- ElevenLabs websocket stream-input: https://elevenlabs.io/docs/api-reference/text-to-speech/v-1-text-to-speech-voice-id-stream-input
- LiveKit data packets: https://docs.livekit.io/home/client/data/packets/
- LiveKit ElevenLabs plugin source: https://github.com/livekit/agents/blob/main/livekit-plugins/livekit-plugins-elevenlabs/livekit/plugins/elevenlabs/tts.py
- Oculus viseme reference: https://developers.meta.com/vr/documentation/unity/audio-ovrlipsync-viseme-reference/
- HeadAudio (MIT): https://github.com/met4citizen/HeadAudio ; TalkingHead (MIT): https://github.com/met4citizen/TalkingHead
- libtashkeel (MIT): https://github.com/mush42/libtashkeel ; CATT (Apache-2.0): https://github.com/abjadai/catt
