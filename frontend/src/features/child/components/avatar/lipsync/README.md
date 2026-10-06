# Lip-sync driver

An in-browser lip-sync driver. It listens to the agent's voice, works out which of the 14 Oculus visemes the mouth should show, and drives the avatar. No server, no new dependency: the whole DSP is in this folder and runs the same live, offline and in the tests.

## How it works

1. `dsp.js` takes 2048 samples (Blackman window), runs an FFT and a 12 kHz LPC fit. It outputs the loudness, voicing, formants F1/F2/F3, band fractions (low, mid, high, sibilant), centroid and flux.
2. `visemeClassifier.js` turns those into raw weights: vowels from F1/F2 against prototypes, s/sh/ch/f from the noise spectrum, nasals from the spectral tilt, stop closures (a short silence inside a phrase gives PP) and stop bursts (kk, DD, PP). Loudness uses an auto gain, so it does not depend on the TTS volume. Between vowels the mouth keeps part of the last vowel (co-articulation).
3. `visemeSmoother.js` applies a damped pre-filter and then attack/release per viseme. The sum of the weights never exceeds 1; `sil` takes the rest.
4. `blinkScheduler.js` gives a blink every 2 to 6 s, 18 percent of them doubles, never during a stressed syllable (deferred, not dropped), and pulled forward at a phrase end. Reduced motion gives no double blinks.
5. `morphTargets.js` and `lipsyncRig.js` write the weights into the GLB's morph targets, or fall back to the jaw.

All numbers live in `lipsyncConfig.js` (`ANALYSIS`, `CLASSIFIER`, `SMOOTHING`, `BLINK`) and `visemes.js` (`VISEME_GAIN`).

## Using it

```js
const { getLipsync, resume } = useVisemes(trackOrElement); // hook, for a MediaStreamTrack or <audio>
const lipsync = getLipsync(); // null, or { weights (14), stress, speaking, phraseEnds, ... }
```

Production path: `useLiveKitRoom` already owns the AudioContext and the agent's source node, so it creates the driver with `createVisemeDriver({ context, input })` and exposes `getAgentLipsync`. `ConversationPage` passes it down as `getLipsync` to `Avatar`. When nothing is playing `getLipsync()` returns null and the avatar behaves as before.

iOS and Safari: an AudioContext starts suspended. `resumeOnGesture` listens for taps, clicks and key presses (`touchend` and `click` are the ones iOS accepts) and for `visibilitychange`, and calls `context.resume()` whenever the context is not running, so it also recovers after a call or a locked screen. A `MediaElementSource` can be made once per element, so the driver caches it in a WeakMap.

## Avatar integration

`Avatar` takes `getLipsync` and an optional `morphNames`. `LipsyncRig` binds morph targets by name (case-insensitive) and needs at least 5 viseme morphs to count as a viseme avatar (`MIN_VISEMES_FOUND`).

- Names tried for each viseme: `viseme_aa`, `v_aa`, `visemeaa`, `mouth_aa`, `vis_aa`, `aa`. Edit `MORPH_NAME_PREFIXES` in `visemes.js` if the whole set shares another prefix, or pass `morphNames` for single names: `{ aa: 'Mouth_Ah', O: ['Mouth_Oh', 'oh'] }`. Pass a stable (module level or memoised) object.
- Blink: a morph named `blink`, `eyeBlink`, `eyes_closed`, `eyeBlinkLeft/Right` and so on (`BLINK_MORPH_NAMES`). All that are found are driven together.
- No viseme morphs (today's `avatar-web.glb`): the jaw path is unchanged, and the rig only supplies the blink if a blink morph exists.
- With visemes the jaw bone is scaled by `JAW_WITH_VISEMES` (0 by default, so the morphs do all the work).

New GLB hookup: the 3D plan (Alsadiq-3D `PLAN-3D.md`) exports `avatar-animated.glb` with 14 shape keys named `sil PP FF DD kk CH SS nn RR aa E I O U`; the bare names bind as they are (`viseme_*` works too). Point `MODEL_URL` (or the `modelUrl` prop) at it and check the dev page's avatar view. If a shape looks too strong, lower its entry in `VISEME_GAIN`. Do not weld or simplify the mesh after the shape keys exist, and check that the optimiser keeps the target names.

Blink on that GLB: the plan blinks with eyelid bones and a `Blink` clip, not a morph, so `hasBlink` will be false. `LipsyncRig.update()` still returns the scheduler's blink weight (0 open, 1 closed) every frame; feed it to the eyelid bones or the clip's time when that GLB lands. Until then a blink-only morph also works, and the voice analysis runs only when the GLB has viseme or blink morphs.

## Arabic mode and the text-timed hybrid

Two layers. Both are on for `lang: 'ar'` (the conversation page passes it) and cost nothing when a part is missing.

1. Audio-only Arabic mode (arabicVowels.js, `ARABIC` in lipsyncConfig.js). Three vowel classes (a, i, u from F1 and F2), no r shape, an amplitude floor so the mouth is visibly open on speech, and a jaw (jaw.js, `JAW` in avatarConfig.js) coupled to the vowel and the loudness.
2. Text-timed hybrid (hybridLipsync.js). The agent forwards the ElevenLabs per-character timings on the data topic `lk.lipsync` (PLAN.md section 5). The text gives the timing: every meem and baa is a lip closure (PP held at 0.95 or more), long vowels, pauses, teeth for fa, rounding for waw. The audio gives the colour: which short vowel a slot is (a, i or u, by votes from the classifier) and how loud it is.

Files:

- `arabicText.js` buildTrack: characters with times to a list of segments (consonant, vowel, slot, silence, unknown span). The letter map and the rules for wasla, sun lam, shadda, sukun, tanween, taa marbuta, hamza seats, emphatic letters, Latin labials and unknown characters are in it. Every number is in `TIMELINE`.
- `timelineTrack.js` TrackSampler: segments to the 14 weights at one moment. Dominance blend (Cohen and Massaro 1993), then hard floors for PP and FF. No allocation.
- `timelineSync.js` TimelineSync: keeps the text clock on the audio that is playing. Phases IDLE, ARMED, LOCKED, STALLED, AUDIO. It latches at the first voiced onset after a silence (plus `latchOffsetMs`, the gate lag), re-anchors after every pause, holds the clock over a stall, and never shows a timeline that has no `go`.
- `hybridLipsync.js` HybridLipsync: wraps LipsyncEngine. With no timeline `process()` returns the engine array unchanged (R2). With one it cross-fades to the text-timed mouth and leads the sound by `TIMELINE.leadMs` minus `AudioContext.outputLatency`.
- `timelineMessages.js`: the message format and the helpers the lab, the preview and the evaluation use to replay an alignment. The Python side is backend/conversation/agent/lipsync_timeline.py.

Kill switches: frontend `VITE_LIPSYNC_TIMELINE=0` removes the hybrid (audio-only Arabic mode stays); backend `LIPSYNC_TIMELINE` is on by default; `LIPSYNC_TIMELINE=0` stops the timeline (and gestures).

Evaluation: `frontend/scripts/lipsync-eval/` (eval.mjs, gt.mjs, synth_testset.py, testset-ar.json: 30 Arabic lines, tune split 1 to 20, held-out 21 to 30). `node scripts/lipsync-eval/eval.mjs --mode audio|hybrid --split tune|test|all [--stress none|late|stall|stale]`. The synthesised clips and alignments are not in the repo (ElevenLabs output); the script makes them from your key. Results and the before and after table: docs/hackathon/handoffs/06-lipsync-ar.md.

Tuning notes: `latchOffsetMs` (40) is the time the voice gate takes to open after a sound begins; if the gate or the FFT window changes, re-measure it first (eval.mjs prints the onset error of the closures, and the latch offset is the median of the audio onset minus the first letter start). A slot learns its vowel class from votes, not from one frame, because the audio class is only about 0.7 to 0.8 right for i and u. The mouth is shown `leadMs` (50) ahead of the sound; a device with output latency gets less lead, so the heard sync is a little later there.

## Dev tools

- `/dev/lipsync` (dev server only, not in the production build): plays clips from `frontend/dev-audio/` (gitignored, never commit audio) with live bars, a 2D mouth, an offline timeline, a mouth strip every 0.1 s, a reduced motion switch and the real avatar. Copy the audition mp3 files there; `lines.json` holds the text.
- `npm run test:lipsync`: 72 tests. lipsync.test.mjs (22): synthetic vowels, hiss, closures, loudness, smoothness, lag, sample rate independence, blinks, the iOS resume, morph binding on fake and real three.js meshes. lipsync-ar.test.mjs (11): the Arabic vowel mode and the jaw. lipsync-timeline.test.mjs (39): the text rules, the sampler, the clock, the messages, R2 (no timeline gives the audio-only output) and P1 (cost and allocation).
- `node scripts/lipsync-probe.mjs`: synthetic probe.
- `node scripts/lipsync-clips.mjs [clip from to]`: per-clip share of each viseme, or a frame trace. It reads decoded PCM from `dev-audio/pcm/` (export it from the dev page).

## Tuning notes

On ElevenLabs speech the low band holds almost all the energy of any voiced frame, so a nasal needs a strong tilt (mid/low below about -2.8 in log10), not a high low-band share. Formants drop out on some frames; the tracker then holds the last estimate. Voiced onsets are vowels, not stop bursts (`burstVoicingMax`). After changing `CLASSIFIER` run the node script on the clips (vowels should be about 35 to 40 percent of the active shapes, PP under 10) and `npm run test:lipsync`.

Lag: `SMOOTHING.preRate` and `LIVE_RATE` in `lipsyncRig.js` set it. On the 13 clips the avatar's mouth opening trails the voice's loudness by about 60 ms on average and under 80 ms at worst (cross-correlation of the two); the speaker's output latency hides part of that. Slower rates look calmer but drift late. On a 6x CPU throttle in Edge one analysis costs about 0.7 ms per frame (0.07 ms unthrottled).

Vowels on these voices: F1 rarely reaches the `aa` prototype (780 Hz), so Arabic fatha mostly shows as `E` (about 13 percent of active shapes against 7 for `aa`). That reads as a mid-open mouth and looks fine on the 2D mouth; once the real visemes are in, compare `aa` and `E` on Arabic clips and lower the `aa` F1 prototype (for example to 700) if the mouth looks too closed.
