# Handoff: product-web (product integration + meadow stage)

Branch `hk/product-web` (from `origin/hackathon`), worktree `Alsadiq-wt/product-web`. Nothing pushed, no PR, nothing posted
to the team brain. Author: the product integrator agent (Claude Code), 2026-10-05.

## 1. What this branch is

1. Seven real merge commits that put every hackathon branch into one product build on top of Abdulrahman Mahmalji's
   05-web-ui pages.
2. The "meadow stage": the lead's two concepts for the child page, built on the painted meadow.
   - Concept 1: Home shows Sadiq walking up the meadow path before the session, then idling (with an idle stroll beat).
   - Concept 2: at session start the camera eases ONCE into the call framing and stays steady. No zoom while he speaks.
3. The call screen and Home are restyled to the two WebUI reference photos (call screen = photo 1, Home = photo 2).

## 2. Merge log

| Order | Merge commit | Branch | Note |
|---|---|---|---|
| 1 | 0df826f | origin/hk/05-web-ui | mobile-parity web UI; owns the pages |
| 2 | 8d4ec07 | hk/demo-mvp | ElevenLabs voice, demo guards, landing, forest, walk-in |
| 3 | 0b3c38d | hk/avatar-studio | studio avatar, lip sync, context director, MeadowLife, studio walk |
| 4 | 9399608 | hk/avatar-signals | agent-side al.* attributes |
| 5 | aaa95c8 | hk/08-latency | latency flags, TTS warm-up, speak-first |
| 6 | ce15512 | hk/behaviour-agent | gesture planner, al.search topic |
| 7 | 1cc40a0 | hk/search-webpage | W3 held web page |

## 3. Conflicts and resolutions

- demo-mvp onto 05 (8d4ec07): ConversationPage = 05's startup (AbortController, late-allocation rollback, SourceRail, exit
  dialog with useDialogFocus, Pill status) carrying demo's voice states, text-only retry, session clock, notices and
  localised copy. useLiveKitRoom = 05's cleanup/teardown plus voice_error, session_limit, micEnabled. Chat, Level and
  VoiceMode = 05 light styling plus lang/dir/placeholder props. GlassIconButton dropped for 05's IconButton.
  check-session-startup.mjs got stubs for the demo collaborators.
- avatar-studio (0b3c38d): App, VoiceMode, Avatar, useAvatarMotion, walkIn, ForestStage, SceneClock, DemoHeroScene,
  DemoLanding, useLiveKitRoom, ConversationPage (merge logic kept, studio props passed through), a duplicate screen key
  in runtime.js. Showcase and dev pages stay gated by VITE_SHOWCASE or DEV, out of the product routes.
- avatar-signals, 08-latency, behaviour-agent: all three override or extend `AlSadiqAgent.tts_node`; the later definition
  silently won. There is now ONE async-generator node: text tapped for signals (tap_reply), frames through the lip-sync
  timeline when on, the gesture planner segment. Wiring tests now count only the timeline's own agent_state_changed
  handlers.
- search-webpage (1cc40a0): package.json keeps every test script plus test:webpage.

## 4. Decisions and deviations

- **GESTURE_EVENTS defaults OFF** (deliberate deviation from the behaviour-agent branch, which turned it on whenever
  LIPSYNC_TIMELINE was on). A real child session must not get gestures by accident. Env examples carry GESTURE_EVENTS=0.
  Turn on explicitly to demo gestures.
- **W3 offset and webSafety**: the spec 6.3 offset (0, 0.13, 0.03) and the webSafety freeze of the page's shift and scale
  apply only when the `SearchScroll_W` clip exists in the GLB (exported as SEARCH_SCROLL_W in avatarConfig.js). Without the
  P6 W clips the W3 behaviour is unchanged.
- **forestFlag change** (forest/forestFlag.js, marked avatar-integ): `isForestEnabled()` no longer turns on under
  `VITE_DEMO_MODE=1`. It is `?forest=1` (remembered in localStorage), or `VITE_FOREST_SCENE=1`. `?forest=0` turns off and
  forgets. The painted meadow with MeadowLife is the default child background.
- Avatar edits to Mahmalji's files are marked `// avatar-integ` (ConversationPage, SourceRail, BottomNav, ChildLayout,
  ChildIdleStage, VoiceMode). I integrated; I did not rewrite his pages.

## 5. Meadow stage design

Files (frontend/src/features/child/components): `MeadowStage.jsx`, `avatar/meadowStage.js` (pure logic),
`meadowScreens.css`, `LevelBar.jsx`; plumbed through `avatar/Avatar.jsx`, `avatar/ClipAvatar.jsx`,
`avatar/lookdev/AvatarLookdev.jsx`.

- One persistent `MeadowStage` sits behind every screen of the child page (Home, call, cards) so Sadiq never reloads
  between Home and the call. `ConversationPage` returns it from `withForest` when the forest is off. The page sets
  `phase` ('home' or 'call'); the avatar's frame loop reads it.
- `meadowStage.js`: two poses of the same level camera (home, call) mixed by `m`, eased once (1.3 s, smoothstep; reduced
  motion jumps). Only `dist` and `cx` change; horizon and eye height are fixed, so there is no tilt or parallax drift.
  Rest spot fixed in the world; a walker at depth z is placed on the painted path (`walkerX`).
- Idle beat state machine: arrive, rest, pivotAway, away, linger, pivotBack, return, with a rate-limited facing pivot.
  Phase 'call' sets `walk.rush` true (he does not stroll during a call).
- `STAGE.homeBoost` is **1.12**. Calibrated from the photos: photo 2's head scale is nearly equal to photo 1's, so Home
  is only slightly bigger than the call pose. 1.2 made his head about twice the photo's. The head top sits near eye
  height, so with the horizon and eye fixed the head cannot be raised; Home hips sit behind the CTA by design.
- `stage` is used only when the look-dev layer is on and framing is 'meadow' (so `?look=before` ignores it). The
  procedural fallback avatar gets no stage.
- Call screen (photo 1): clock and status top-start, Voice | Chat pill, `LevelBar`, three round keys (mic, red end,
  speaker). Voice | Chat: chat hides and pauses the avatar, the meadow stays, framing is unchanged on return.
  `SourceRail` has a `bare` prop so an empty rail no longer squeezes the controls.
- Home (photo 2): greeting, green CTA, level ring card, quest card, floating bottom nav (`BottomNav floating`,
  `ChildLayout floatNav`). The tap target on Sadiq (`.mh-tap`) is the same as the CTA (starts the call).
- The camera ease is one-way: on the call screen there is no speak-time zoom. The speaking close-up stays on the `/page`
  showcase only.

## 6. Tests (all green at the end of this branch)

From `frontend/`: `npx eslint .` clean; `npm run build` ok (chunk-size warning only); test:lipsync 80, test:avatar 78,
test:webpage 47, test:hotfix2 17, test:acting 31, test:walk 20, test:nature 17, test:lookdev 21, **test:meadowstage 31
(new)**; `node --test scripts/check-session-startup.mjs` 21; `node scripts/check-source-cards.mjs` passes.
Backend (sqlite settings, container with no network): 836 tests OK.

Browser click-test (Edge, headless, muted): `scripts/meadow-click-test.py`, 14/14 at 390x844 (en), 1280x720 (ar), and
earlier at 390x844 (ar) and 1280x720 (en). It covers Home, the single camera ease (the mix rises monotonically, reaches
1, then stays 1), level bar and pill, the nav hidden during the call, mic and speaker toggles, chat hiding the avatar,
and voice returning at the same framing. Flag sanity: `?forest=1` renders the forest instead of the meadow stage;
`?forest=0` and `?look=before` load the meadow stage with no page errors.

How to run it:

```
cd frontend
npx vite --port 5395            # dev mode (window.__stage is DEV only)
python scripts/meadow-click-test.py http://localhost:5395 OUT_DIR 390 844 ar
```

The API is mocked at localhost:8000 with a fake unsigned JWT, and the LiveKit hook is replaced by
`scripts/fixtures/useLiveKitRoom.stub.js` (synthetic state, no audio, no network). It never clicks mailto: or tel: links.

## 7. Open issues

1. `features/demo/DemoHeroScene.jsx` (the demo-only landing hero, behind VITE_DEMO_MODE) still lazy-loads the 3D forest
   when WebGL is available. The "meadow is default, forest opt-in" rule is applied to the child page only. Left alone
   (it is the landing's own hero); gate `forest` on `isForestEnabled()` with an `// avatar-integ` mark if the lead wants
   the landing to match.
2. The chat mode's empty-state text sits on a white card with a text shadow; that is 05-web-ui styling, untouched.
3. The procedural fallback avatar (no GLB) has no stage: it stays centred, no walk-in and no camera ease.
4. Shadow-catcher bounds with the walker at the far end of the path (up to about 3 units back) were not examined
   separately; the walk-in and rest were checked visually only.
5. The real LiveKit call path was not exercised in a browser here (no keys, no LiveKit server); the stub covers the UI
   states only. Do one real call before the demo.
6. Gestures are off by default (see section 4); the P6 W clips (SearchScroll_W) are not in the GLB yet.

## 8. Round 2: Home walk, steady call, mobile parity, kid polish (2026-10-05)

Concept 1 (Home walk). `meadowStage.js`: the idle beat now alternates, odd beats a stroll up the path and back (turns at
3 rad/s on the spot, `idleBeat.pivotRate`; the walk itself uses the studio Walk with Walk_Start/Walk_Stop and root
speed), even beats a short wave (`briefWave`). First beat at 9-13 s, then every 14-22 s. Reduced motion and a call keep him
standing. On a phone Home is photo 2's framing (bust above the key, `homeBoost` 1.12): the stroll shows as him walking away
up the path (back to camera, smaller) and returning. On a wide window (`isWide`: aspect >= 1.15) the Home pose is the new
`homeBoostWide` 0.8 of the call pose, and the CTA and cards move into a soft side panel (inline-end, so left in RTL) in
`meadowScreens.css`, so he stands whole on the path above the floating nav. The panel fades out while connecting.

Concept 2 (steady call). The ease (1.3 s, smoothstep, once) was already one-way. Leak closed in `Avatar.jsx`: with
`?look=before` the stage was null and the speak-time shot came back; `productStage` now keeps it off whenever the product
passes a stage. The speak zoom stays only for `/page` and VITE_SHOWCASE.

Mobile parity and kid polish. Bottom tabs speak the demo language (Arabic first, "Badges" instead of "Achievements"),
toasts localised (`COPY[lang].idle.toast`), RTL both ways. New: `Confetti.jsx` (CSS burst on points, level-up and quest
toasts, none under reduced motion), `soundFx.js` (synthesised WebAudio tap, chime and cheer; off until the child switches it
on with the speaker button on Home, remembered in localStorage; no audio files), level ring fills from empty on Home, press
bounce on tabs and cards, hover lift. Quests and Badges already had friendly empty states (05-web-ui), kept.

al.search showcase: already wired (useLiveKitRoom `al.search` -> avatarSignals -> page in hand); nothing faked. Gestures
stay behind GESTURE_EVENTS (demo env only).

Tests: all of section 6 green again (test:meadowstage 31, with the home-vs-call assertion split phone/wide); click test
14/14 at 390x844 en, 1440x900 ar, 2000x713 ar. Media (Alsadiq-3D/03-renders/product): `home-` and `call-` PNGs at 390x844,
1440x900, 2000x713 in ar and en, plus `product-home-walk-to-call.mp4` (30 s, Home stroll, Talk, camera ease, steady call).
Regenerate with `python scripts/product-media.py URL OUT shots|video` (dev vite) and `scripts/home-walk-sheet.py` for a
contact sheet of the walk.

Open from round 2: (a) the Home quest card still shows the generic "Find your quests" title, not the real quest; (b) on a
phone the legs are hidden behind the CTA by design (photo 2), so the whole-body stroll is only fully visible on wide
screens; (c) a Latin name inside the Arabic greeting puts the "!" on the wrong side (mock data only); (d) the sound
effects were not listened to (muted runs); (e) Quests and Badges page strings besides the nav are still English.


## 9. Product verifier (QA) pass (2026-10-05)

Stack: own compose project `product-web` (ports 5173 vite in docker, 8000 backend, 7880 livekit, 5432, 6379), `.env` copied from
demo-mvp with `DEMO_MODE=1`, `LIPSYNC_TIMELINE=1`, `GESTURE_EVENTS=0` (stays off). Extra vite on 5395 (dev, stub click test) and
`vite preview` on 5396 (production build, perf). QA scripts live outside git in `Alsadiq-wt/product-web-qa/`
(`tour.py`, `a11y.py`, `contrast.py`, `call_a11y_perf.py`, `netperf.py`, `rm_stage.py`); axe-core was installed only there
(not an app dependency). Results/screenshots: `product-web-qa/out/`.

Commit: `67b2acb` (small fixes below). Fresh DB needs `manage.py seed_demo` once, or demo login answers 503 "rooms busy".

### Voice e2e (e2e-voice kit, ElevenLabs, 4 of 4 sessions used)
- ar and en: join, child transcript, Sadiq reply, `lk.lipsync` timeline packets arriving (9 of 11 packets carry a timeline,
  2 are `go`; `stop` only goes out on interruption, so 0 is correct), avatar moves while speaking, 0 console errors, 0 agent
  errors. The kit was extended (not in git): start key `button.mh-cta`, new chat-bubble marker, Voice|Chat pill, a datachannel
  hook that counts lk.lipsync packets, a frame-diff motion score for the avatar crop, and two judge checks.

### Judge tour (Edge, ar and en, 390x844 and 1440x900)
landing, landing bottom, demo login (0.9 s), child Home (+ stroll frames), Quests, Badges, Settings, parent Children,
Insights, Alerts, Settings, child summary: 10 pages per run, 4 runs, 0 console errors, 0 bad requests, no horizontal scroll,
no broken images. Camera ease once, steady call, mic/speaker/end keys, Voice|Chat: click test 14/14 on all four
combinations; `check-source-cards.mjs` passes.

### Accessibility
- axe-core (wcag2a, 2aa, 21aa): 0 violations on landing, Home, Quests, Badges, Settings, call and chat, in both languages and
  both sizes (after the fixes below; the call and chat had 1 contrast violation each before).
- Keyboard: Tab order on Home is parent view, start fresh, mute, language, start talking, quest, then the four tabs; every
  stop shows a visible 4 px ring and stays on screen. In the call: Voice, Chat, mic, end, speaker, all with Arabic/English
  aria-labels, targets 44 to 86 px. Home to call works with Enter on the green key.
- Text over the meadow (real pixels under the text, worst-case 10th percentile): every Home label passes AA; the green
  key reads 3.6:1 but is large bold text (needs 3:1). The Home language key was 4.2:1 at 1440 wide and is now opaque enough.
- Reduced motion: the stroll is off (`rest` only), no infinite CSS animation on Home, camera still lands on the call
  framing. Transcript: the call has two polite live regions; the chat screen shows the messages.
- RTL: Arabic Home, call and chat mirror correctly (dir on the page root).

### Performance (6x CPU throttle, 390x844 at 2x DPR, production build, cold cache)
- fps on Home (idle, stroll window) and in the call: 30.7 fps with no frame over 34 ms and 0 long tasks. A blank page in this
  headless RDP session also tops out at 31 fps, so the app holds the session ceiling with headroom; true headroom above 31
  was not measurable here. Real-phone numbers still need a device.
- Cold download: landing 3.4 MB (avatar-animated.glb 2.37 MB, main JS 0.48 MB gz, fonts 0.2 MB), Home adds 0.6 MB (1440 wide)
  to 0.9 MB (phone, see open issue 4). Whole first visit about 4 MB. JS heap 72 MB on Home.

### Fixed in 67b2acb
1. Arabic streak read "١ أيام متتالية"; it now reads "يوم واحد متتالٍ" (the count arrives as a formatted string).
2. Language sources disagreed: nav tabs and toasts read the demo language once per render and went stale after a toggle, and
   a non-demo account's profile language never reached them. New `useDemoLang()` (useSyncExternalStore) in `demoService.js`;
   `writeDemoLang` notifies; `ConversationPage` mirrors the profile language. Verified: toggle on Home flips the nav at once.
3. Voice|Chat active pill: white on #1f9a4e (3.6:1) now white on #167a3c.
4. Chat empty state: white text with a dark shadow on the light chat card (2:1) now dark green.
5. Home language key background 0.82 to 0.94 opacity.

### Open issues (not fixed here)
1. Quests, Badges, Settings and the whole parent app stay English and left to right when the demo is Arabic (heading
   "Achievements" under the tab "الأوسمة"; a Settings label truncates). Biggest remaining gap for an Arabic-first judge.
2. The chat screen still uses the legacy header, not the call's Voice|Chat pill look.
3. The Arabic greeting starts with "وعليكم السلام" (a reply form) instead of an opening greeting. Prompt text in the agent;
   not changed, because no live-voice sessions were left to verify it.
4. A phone downloads `meadow-3840.webp` and `meadow-2560.webp` (0.8 MB together) and the 2.37 MB animated GLB on the landing
   page; a smaller tier for narrow viewports and meshopt/Draco on the GLB would cut about 2 MB. `avatar-web.glb` (0.7 MB) is shipped but unused.
5. `<html lang>` stays `en` and has no `dir`; the page roots set `lang`/`dir` themselves so screen readers are right, but the
   document language is wrong on Arabic pages.
6. Demo capacity: 8 families, 2700 s lease, `demo_start` 10 per hour per IP (429 with "Expected available in 2889 s"). A judge
   room behind one NAT, or someone reloading often, will hit it. Raise `DEMO_START_RATE` and the pool before the live demo.
7. Sound effects were never listened to (muted runs). The voice kit was capped at 4 sessions, so the greeting wording
   above was seen in only a few sessions per language.
8. Quest card on Home still shows the generic title (from round 2, item a).

## 10. Judge-panel pass (2026-10-05)

Scored as the official judges would (dev vite on 5397/5398 with the stub, the renders and the MP4; no live voice
sessions used). Total 64/100: technical 17/25, track 11/20, scholarly 6/15, innovation 12/15, UX 7/10, operations 7/10,
presentation 4/5. Verdict: ship-with-notes (PR into `hackathon` is clean, `origin/hackathon` is an ancestor).

Fixed in `08b3577`: with a verse or hadith card on the meadow call, the SourceRail took a flex row, so on a phone the
mic, end and speaker keys jumped up onto Sadiq's chest and on a wide window the cards slid under the level rail. The
cards now float in `.mc-sources` (meadowScreens.css): above the keys on a phone, a column at the inline end clear of the
level rail on lg+. SourceCard's English translation and grader line are `dir=ltr`, so punctuation no longer flips on
Arabic pages. Checked with placeholder cards (`window.__mockReference`) at 390x844, 768x1024, 1024x768, 1440x900, ar
and en; click test 14/14; eslint, build, check-source-cards, check-session-startup green.

Found, not fixed (largest first):
1. `origin/hk/01-knowledge-bank` is not merged here. Without it a real session never sends `reference` events, so no
   source card ever appears, and every turn pays the `get_islamic_reference` tool round (about 2.1 s of the 5.3 s median,
   see latency/RESULTS.md). A trial `git merge-tree` shows 3 conflicts: `agent_class.py` (imports, `__init__` kwargs
   prompt_profile vs age_band/value_index, the prompt assembly, the tts_node area), `entrypoint.py` (imports; it also
   imports `xai_tts_streaming`, which must not come back as a voice path) and `.gitignore`.
2. `05-cards-ai-privacy.md` (on the knowledge-bank branch) is a P0 spec with exact strings that nobody built: the
   permanent AI chip and info sheet, the two-tier card ("From the Quran:" vs "In simple words (AI-assisted):"), Arabic
   card labels, the sahih-only grade guard, `{{verse:S:A}}` marker replacement (the knowledge bank sends these; today's
   card would show the raw marker), and `/privacy`.

## 11. Cards, AI disclosure and privacy (cards-spec 05, 2026-10-05)

Branch `hk/pw-cards`, built on `hk/product-web`. Spec: `docs/hackathon/handoffs/05-cards-ai-privacy.md` and
`docs/hackathon/privacy-policy-draft.md` on `origin/hk/01-knowledge-bank`. Every edit in existing files is marked
`cards-spec (05)`. No backend file was touched.

### What was built
- Source cards (section 1 and 2). `normalizeReference` in `useSourceCards.js` enforces the spec: type and kind, the
  host allowlist, Hafs bounds, sahih-only for hadith (any other grade drops the card), the translation-link rule
  (a HadeethEnc link only to its own host), level C needs a disagreement note, 3 cards at most. `sourceLabels.js` has
  every Arabic and English label, the citation line (`Sahih al-Bukhari 12 · graded sahih (al-Bukhari) · source: ...`),
  the translation credit and the recitation credit (always shown). Two tiers: the source block, then the "In simple
  words (AI-assisted):" block, visibly different. `{{verse:S:A}}` markers become a reference chip with its own play
  button (audio = `VITE_QURAN_AUDIO_BASE/SSSAAA.mp3`); a broken marker drops the card. Quran text is 28px or larger.
- Permanent AI chip and info sheet (section 4). `AiChip` is `position: fixed` top-end, 56px, in `withForest` in
  ConversationPage, so every session state and both modes carry it. `AiInfoSheet` has the exact ar and en strings,
  focus trap and Escape (`useDialogFocus`), an EN/AR toggle, and a privacy link.
- `/privacy` (section 5), public route outside every guard (App.jsx, also in the showcase router), content in
  `src/features/privacy/privacyContent.js` in ar and en, real tables, draft banner. Linked from: landing footer, login,
  registration step 1 (with the AI notice) and step 3, the Terms modal (clause 3 link, new clause 11 on the AI
  companion), the AI sheet, child settings and parent settings.
- Tests: `npm run check:cards` (`scripts/check-source-cards.mjs`, evaluates the real modules; includes the real
  `parseData` from `useLiveKitRoom.js` over every mock kind and garbage bytes) and the browser click test
  `scripts/cards-click-test.py` (75 checks).

### Decisions
- The chip is fixed, so each header with a control at the top end reserves inline-end room (`.mc-top`, `.mh-top`,
  the chat-mode header) and the chip carries its own `dir` from the child's language so it sits on the side the header
  reserved, also when the document is not `dir=rtl`.
- Privacy links open in a new tab where leaving would lose state (AI sheet, registration); elsewhere a normal `Link`.
- AI sheet line 5 (parent summaries) is behind `SHOW_PARENT_SUMMARY_LINE = false` in `aiStrings.js`: the parent API
  still sends the raw 120-character `preview`, so the line would be untrue. Flip it when the preview is removed.
- Quran font: the `@font-face` points at `/fonts/KFGQPCHafs.ttf`, which I did not have. Drop the file into
  `frontend/public/fonts/` (see the README there). Until then the Amiri Quran fallback is used, with a display-only
  mapping of three legacy code points (3-second detection timeout); the stored text is never changed. Nothing in the
  build fails without the file.
- The privacy draft's `[bracket]` placeholders were replaced by neutral "to be confirmed" wording and the draft banner
  stays. The OpenAI row is as in the draft, xAI was dropped.
- Test port: 5411 was taken by another worktree's vite, so my runs used 5421 and 5422 (showcase).

### Needs a human
- The privacy claims ("you do not see your child's conversations", "we do not draw conclusions about religion", "no
  recordings kept", "no training on your data") are only true once the team confirms them. Do not publish the page
  as final before that. Contact, controller and retention values are still to be filled in.
- The `related` ids ("About S:A" pill) are skipped: P1 gap.
- Section 10 item 1 still stands: without `origin/hk/01-knowledge-bank` merged, no real session sends `reference` events.
  The cards were tested with placeholder payloads through the real decoder, never with live agent output.
- Placeholders only in tests and mocks: no real Quran or hadith text anywhere in this branch.

### Run and test
- `cd frontend && npm run check:cards && npx eslint . && npm run build` (plus the node --test suites in package.json).
- Click test: `VITE_QURAN_AUDIO_BASE=https://audio.test/quran npx vite --port 5421 --host 127.0.0.1`, then
  `PYTHONUTF8=1 python scripts/cards-click-test.py http://127.0.0.1:5421 OUT_DIR 390 844 en` (also `ar`, and 1280 800).
  The landing check needs the showcase build: `VITE_SHOWCASE=1 npx vite --port 5422` and `LANDING_URL=http://127.0.0.1:5422`;
  without it that one check is skipped. The script writes and removes `scripts/fixtures/_cards-stub.generated.js`.
- Results at the end: eslint clean, build OK, check:cards pass, all other node suites pass, click test 75/75 at 390x844
  en, 390x844 ar and 1280x800 en, no console errors.

### Review (2026-10-05)
Every spec string (sections 1, 4.2, 4.3) matches the code exactly. The 74 real knowledge-bank verse items, shaped as
`card_payload()` sends them, all pass `normalizeReference` with their text unchanged. Fixes made in the review (marked
`cards-spec (05) review`). They were left uncommitted in the pw-cards worktree and so missed the round-2 merge; the
judge panel (section 16) ported them onto `hk/product-web`:
- The call screen header: the room kept for the AI chip pushed the Voice | Chat pill onto the clock at 360px (touching)
  and 320px (the time was hidden). Narrow phones now get tighter gutters and a slimmer pill (`meadowScreens.css`).
  Checked pairwise at 320, 360, 375 and 390, en and ar: no overlaps on the call or chat screens.
- `sourceLabels.js` matched book and grader names by substring, so "Hisn al-Muslim" or a commentary on Sahih Muslim
  would be relabelled "Sahih Muslim". It now matches exact names only (case, spaces and tashkeel ignored). New asserts
  are in `check:cards`.
- The fiqh line and the "Scholars may differ" note are our words, so they moved out of the quote block (`SourceCard.jsx`).
  A verse marker chip carries its own `lang`, so an English label inside the Arabic text is not read as Arabic.
- Terms clause 11: the bold heading is now "11. AI Companion" like the other clauses (it was only "11.").
- `quranText.js`: the three code-point pairs are `\u` escapes and their comments name the right targets (open
  fathatan, dammatan, kasratan). The mapping is unchanged and follows the spec.
Still open: the privacy page states as fact some claims the draft marked "team to confirm". One of them, "You do not see
your child's conversations", is not yet fully true: the parent conversation list still shows the 120-character preview
until the session report deletes the messages, and it still shows flagged messages after that.

## 12. Arabic-first localisation, RTL and chat parity (2026-10-05, branch hk/pw-i18n)

### What was done
- New `frontend/src/i18n/` module (no library): `strings.js` (ar and en dictionaries: common, nav, time, quests, badges,
  settings, password, validation, levels, badgeCatalog, chat, sources, parent), `format.js` (`num`, `pct`, `arCount`,
  `shortDate`, `clockTime`), `stringsFor.js`, and `index.js` (`useLang`, `useStrings`, `useDocumentLang`, `timeAgo`,
  `localName`). The language is still the existing `useDemoLang()` store (`demo_lang`, default `ar`).
- Child Quests, Badges and Settings pages, the quest and badge components, the badge toast and the change-password
  modal are localised. The Badges page heading is now "الأوسمة" (was "Achievements"). Settings labels no longer truncate.
- Arabic-Indic digits everywhere a digit is shown (points, counts, percentages, streaks, times, dates). Dates are
  Gregorian whatever the device calendar; the formatter forces `ar-u-ca-gregory-nu-latn` and maps digits itself.
- `<html lang>` and `dir` follow the active language (`useDocumentLang`, used by ChildLayout, which ParentApp also uses,
  and by DemoLanding); the previous values are restored on unmount.
- Bidi: the Arabic greeting wraps the name in `<bdi dir="auto">` ("السلام عليكم يا Omar!"). User text from the
  backend (nicknames, quest titles, summaries) uses `dir="auto"`; emails and usernames use `dir="ltr"`.
- Home quest card shows the real quest title (`useHomeQuest.js`: first quest that is not pending verification).
- Chat mode parity with the call: the Voice|Chat pill header with a mini End key, the level card with Arabic digits
  and the Arabic level name, chat bubble times, empty-state hint and the SourceRail strings localised.
- Parent pages (Children, Insights, Alerts, Settings, conversation summary) are localised and RTL as well.
- Backend badge and level names are seeded in English (gamification migration 0004). The client maps them through
  `strings.badgeCatalog` (19 badges) and `strings.levels` (8 levels) and falls back to the original name.
  The backend is untouched.

### Decisions
- A small dictionary instead of a library: the app has two languages and one store, and the node tests can import the
  pure modules directly (explicit `.js` extensions in `format.js`, `strings.js`, `stringsFor.js`, `validators.js`).
- Existing `// cards-spec (05)` and `// avatar-integ` markers were kept; the lines this branch added are marked
  `// i18n` on the imports and the main hooks.
- `SourceCard` was left alone: the cards-spec agent (hk/pw-cards) owns it. Only SourceRail's region label and empty
  text were localised here, so the two branches should merge without a conflict in SourceCard.
- AddChildModal, Register and ResetPassword stay English for now (login and registration are outside the shells).
  `utils/formatTime.js` `formatRelativeTime` is now unused; it was left in place.

### How to run and test
- `cd frontend && npm run test:i18n` (10 tests: digits, plurals, dates and times, key parity ar/en, the 19 badges, the
  8 levels, headings, password messages). `npm run lint`, `npm run build`, every `tests/*.test.mjs` (352 pass),
  `node scripts/check-session-startup.mjs` (21 pass) and `node scripts/check-source-cards.mjs` all pass.
- Click test (Playwright, `channel="msedge"`, headless, dev server on 5412, API mocked on localhost:8000, the LiveKit
  hook replaced by `scripts/fixtures/useLiveKitRoom.stub.js`): child ar at 390x844 (13/13) and 1440x900 (13/13), child
  en at both sizes (11/11 each), parent ar and en at 390x844 (10/10 and 9/9). It checks html lang and dir, the bdi
  isolate in the greeting, the real quest title, the headings, Arabic badge names, the chat header and level card,
  and that there are no console errors. Never click `mailto:` or `tel:` links.

### Known issues and next steps
1. A parent who is not in the demo defaults to Arabic and has no language toggle on the parent pages.
2. Quest titles and descriptions come from the backend as written (the seed quests are English): they are shown
   as-is with `dir="auto"`. Translating them needs a backend change or a client catalogue like the badges.
3. Badge and level names that are not in the catalogue fall back to the English backend text.
4. The check that the login page restores `lang="en"` and `dir="ltr"` after leaving a shell was not shown in the
   click test (a signed-in user is redirected away from /login); it relies on the unmount cleanup in `useDocumentLang`.
5. Only 390x844 was run for the parent pages. The numbers were not read by a screen reader; no axe run was made.
6. Register, ResetPassword and AddChildModal are still English.

### Review pass (Opus reviewer, 2026-10-05)
Every child page (Home, Quests, Badges and the locked-badge sheet, Settings and the password dialog, the call, chat)
was run in Arabic and English at 390x844 and 1440x900 (Edge headless, API mocked with the real seed shapes: the 19
English badges, English level names, the Arabic demo quests plus AI quests with English theme labels). Checks: html
lang and dir, no Latin text or labels and no Western digits in Arabic, no clipped text or placeholders, no page-wide
horizontal scroll, axe WCAG 2.1 A/AA. All clean after the fixes below. The only Latin left in Arabic mode is the
language key ("EN", labelled "Switch to English" with `lang="en"`), which is intended. Logging out of an Arabic shell
puts the sign-in page back to `lang="en"` with no `dir` (item 4 above is now shown).

Fixes in the review commit:
- Quest theme pills: AI quests carry English theme labels ("Honesty", "Kindness": the knowledge-base fixture and the
  quest prompt are English). `strings.themes` maps them; an unknown English label is hidden in Arabic.
- The chat-mode End key was not mini: `.mc-end` (5.4rem) came later in the file and won. It is now `.mc-end.mc-end-mini`.
- The call stage's region label was "Sadiq" in Arabic too: now "الصادق".
- The password dialog showed the browser's English "Please fill out this field." bubble: the form is `noValidate`, so
  our own message in the page language shows. The placeholder was cut off at phone width in both languages: the full
  rule moved to the intro, the placeholder is now "٨ أحرف على الأقل" / "At least 8 characters".
- The locked-badge sheet sat under the bottom nav on phones (its Close key hidden): it is centred now.
- English badge hints were clamped to two lines (earned badges had no other place to read them): no clamp.
- English icon label "Achievement" was cut to "Achieve…" at 390: now "Success".
- A Latin nickname on Settings drifted to the far side under `dir="auto"`: it is a `<bdi>` in the RTL line now.
- The LiveKit test stub's `sendTextMessage` returned nothing and used the wrong message shape (the page calls
  `.catch` on it); it is async and matches the real hook now.

Merge note: a trial `git merge-tree` against `hk/pw-cards` conflicts in `SourceRail.jsx` (both branches localised
the same two strings; keep pw-cards' `SOURCE_LABELS` + `lang` prop and pass `lang={lang}` from ConversationPage) and
in `pages/child/SettingsPage.jsx` (adjacent imports; keep both). `hk/pw-perf` conflicts in `frontend/package.json`
(scripts). The handoff doc conflicts with every sibling branch.
## 13. Performance and phone framing pass (`hk/pw-perf`, 2026-10-05)

Branch `hk/pw-perf` from `hk/product-web` (dd50ac4), worktree `Alsadiq-wt/pw-perf`. Nothing pushed. Edits to Mahmalji's 05
files are marked `// cards-spec (05)`; avatar edits `// avatar-integ`.

What was done:
1. Phone Home framing (like photo 2: head and chest above the green Talk key). `meadowStage.js` has a vertical lens
   shift (`camera.setViewOffset` y) on phone Home only. `homeLift(W,H)` raises him until his ears sit at
   `homeEarsKey` (0.43) of the stage above the key (`H - cardsPx`, cardsPx 351), clamped to `liftMax` 0.14, and 0 for
   stages wider than `liftMaxWidth` 600 or wide layouts. The lift fades out over `liftFade` 0.6 world units of the stroll
   (`placeStage`), so the painting stays put and he is never cut off while walking; `walkerX` follows the lift so his feet
   stay on the path. The call pose is unchanged. Tests: `tests/meadowStage.test.mjs` (phone-only, bounds, fade, feet on
   the path measured with a real PerspectiveCamera).
2. Narrow meadow tier. `npm run meadow:narrow` (`scripts/make-narrow-meadow.mjs`) writes
   `public/backgrounds/hq/meadow-narrow-{900,1600,2560,3840,5120}.webp`: the same picture at the same pixel size with only
   the visible band (u 0.19..0.75) sharp and the rest a colour wash, so the framing and the GL maths do not change.
   `MeadowImage.jsx` is a `<picture>` with `media="(max-aspect-ratio: 3/4)"`; `MeadowLife` and `meadowLifeGL.js` pick the
   same tier (`isNarrowMeadow()`) and cache masks per tier. `tests/meadowNarrow.test.mjs` checks the band against both fits.
3. Avatar GLB. The premise "the animated GLB is uncompressed" was wrong: `avatar-animated.glb` (2,480,896 B, sha
   ce266e8f...) is already EXT_meshopt_compression + quantization with WebP textures. Re-encoding gave no gain and risked
   the morph targets, so it is left byte-identical (32 joints, morph targets, animations and sidecar contract untouched).
   Removed the unused `avatar-web.glb` from what ships (`FALLBACK_SHIPPED = false` in `avatarConfig.js`, so `Avatar.jsx`
   no longer tries it; `scripts/optimize-avatar-web.mjs` now writes to `avatar-src/`, outside `public/`, if anyone wants to regenerate it). The real lever is
   transfer compression: `infra/caddy/Caddyfile` now has an `encode` block (zstd, gzip 6) that also covers
   `model/gltf-binary`. Checked in an own caddy:2-alpine container: the GLB goes 2,480,896 -> 1,835,424 B (gzip) /
   1,844,626 B (zstd), the main JS 165,569 -> 62,138 B, JSON and HTML are encoded; webp is not (already compressed).
4. AvatarSpinner already uses `text-primary-strong` in this base, so no change was needed.

First-visit bytes, phone profile (390x844, ar, CPU throttled, cold cache, `vite preview`, VITE_DEMO_MODE=1;
`pw-perf-tools/perf_bytes.py`, CDP encodedDataLength):

| DPR | Home phase before | after | whole visit before | after |
|---|---|---|---|---|
| 2 | 933 KB | 492 KB (-47%) | 4395 KB | 3955 KB |
| 3 | 1141 KB | 589 KB (-48%) | 4651 KB | 4100 KB |

Reviewer fix (same profile, re-measured): a phone still downloaded two narrow files, the `<img>`'s 3840/5120 and the GL
layer's 2560 (the GL layer caps at 2560 on every phone, `quality` 'low', and it covers the `<img>` once live). The
narrow `<source>` now stops at the GL layer's cap (`meadowCap`, `meadowNarrowSrcset` in `meadowFraming.js`), so both
take `meadow-narrow-2560.webp`, one download. Home phase 268 KB at DPR 2 and DPR 3 (from 933 / 1141 KB: -71% / -77%);
whole visit 3731 KB / 3779 KB. The picture on screen is unchanged (the GL layer already drew the 2560 file); only the
poster before the GL layer starts, and the no-WebGL fallback, are the 2560 file on a phone. Wide screens are untouched.

`vite preview` does not compress the GLB; behind Caddy the avatar GLB is about 0.6 MB smaller on the wire (reviewer
re-checked in an own caddy:2-alpine container: 2,480,896 -> 1,835,424 B gzip / 1,844,626 B zstd, served as
`model/gltf-binary`; webp left alone; Range requests still answer 206). No console errors.

Verification: eslint, `npm run build`, test:lipsync 80, test:avatar 78, test:webpage 47, test:hotfix2 17, test:acting 31,
test:walk 20, test:nature 17, test:lookdev 21, test:meadowstage 55 (includes the new lift and narrow tests),
check-session-startup, check-source-cards: all green. Backend untouched, so no backend suites. The Caddyfile was
validated with `caddy validate` in docker. Visual checks (headless msedge, dev server) at 360x640, 360x740, 375x667,
390x844, 430x932: head and chest above the key at rest, lift fades during the stroll (walk sheet).

Run it: `npm run meadow:narrow`, `npm run test:meadowstage`; measure with a build made with `VITE_DEMO_MODE=1`.

Risks and notes:
- `cardsPx = 351` is a measured layout constant of the Home cards block; if the cards block changes height, re-tune it.
- The narrow tier assumes a viewport-shaped (full-screen) meadow container and a 3:4-or-narrower portrait viewport.
- The narrow `<img>` and the GL layer share one file through `meadowCap` (reviewer fix). The full tier still has the old
  split on a 4K screen (the `<img>` takes 5120, the GL layer caps at 3840): out of scope here, same fix would apply.
- On short phones (360x640, 375x667, with the demo bar and the two-line Arabic greeting) the lift hits `liftMax`: the
  head stands above the key but the chest stays behind it. On 390x844 and taller it is photo 2 (head and chest).
- During the stroll the lift fades in about 1 s, so on a short phone he sinks behind the key quickly as he walks off
  (his feet are behind the cards there, so nothing slides visibly).
- The narrow files are a re-encode (about 37-39 dB PSNR against the original within the band); the band is only sharp
  where a phone can see it, a rotated phone gets the full tier through the media query.
- With `avatar-web.glb` gone there is no fallback avatar if the animated GLB fails to load.
- Not measured: total bytes behind the real Caddy with the compressed GLB (only the per-file sizes above).

## 14. Ops pass (2026-10-05)

Judging-day demo capacity (40 families, 120 starts an hour per IP, self-seeding backend entrypoint), the Arabic greeting wording, the meadow-by-default demo landing and the refreshed judge script and deck outline are on branch `hk/pw-ops`. Details, CI env values and open issues: `docs/hackathon/handoffs/pw-ops.md`.


## 15. Round-2 integration (2026-10-05, branch hk/product-web)

One branch now holds everything: `hk/agent-quality`, then `hk/pw-cards`, `hk/pw-i18n`, `hk/pw-perf` and
`hk/pw-ops`. Nothing was pushed, no PR, nothing posted to the team brain.

### Merge log
| Order | Merge commit | Branch |
|---|---|---|
| 1 | 5b9e1bd | hk/agent-quality (merged after the safety classifier landed) |
| 2 | db7796a | hk/pw-cards |
| 3 | 326c828 | hk/pw-i18n |
| 4 | 935c51c | hk/pw-perf |
| 5 | 87da6db | hk/pw-ops |

Follow-up commits: 2519757 (greeting tests expect the first-meeting AI line, handoff sections renumbered),
40b0c15 (English opening stays English with Arabic memory; chapter:verse reading), 7665993 (spoken verse clause),
006b8ca (meadow click test follows the localized nav label and the Voice|Chat pill).

### Conflict resolutions and decisions
- One `tts_node`. agent-quality and the turn guard both wrapped it; there is a single override that runs the turn
  guard's cleaning and the TTS text stream, not two stacked ones.
- `entrypoint.py` was merged by hand: agent-quality's classifier wiring, the demo limits and the first-meeting AI line
  all stay. The xai import dropped out (ElevenLabs only, no xai path in the live agent).
- The library cue now comes from the turn guard, so the `al.search` topic and the cue are sent once.
- `SourceRail` stays the cards-spec (05) version (`// cards-spec (05)` markers kept); pw-i18n's strings were added
  to it, not swapped in.
- Handoff sections renumbered 11 Cards, 12 i18n, 13 Perf, 14 Ops; leftover merge markers in this file are removed.

### Tests at the end
- Backend: 1317 tests, all pass (docker runner `alsadiq-eval-runner:local`, sqlite test settings, empty `.env`).
- Frontend: eslint clean, node suites pass (`test:meadowstage` 55/55), vite build OK.
- Meadow click test, 14/14 in all four runs: 390x844 ar, 390x844 en, 1280x800 en, 1280x800 ar, no console errors.
  The script itself was stale after the merges and was fixed (it looked for the English nav label and for the old
  "Switch to voice" button; now it follows the localized nav label and the Voice|Chat pill). Not a product bug.
- axe (wcag2a, 2aa, 21aa) on landing, child home, quests, badges and settings at 390x844, ar and en: 0 violations.
  Reduced motion: 0 infinite CSS animations. Console errors: 0. The crude "unnamed control" helper flags the dark-mode
  switch (it is named by its label element; axe is clean) and the hidden demo mini button; both are false positives.

### Live voice sessions (my own stack, DEMO_MODE=1, LIPSYNC_TIMELINE=1, seed_content bank, headless Edge, 4 of 4 used)
| Run | Lang | Client first audio after the question | TTS first byte | Result |
|---|---|---|---|---|
| 20261005-101957 | en | 3.6 s (slow first LLM call, ttft 2.3 s) | about 0.2 s | PASS |
| 20261005-102240 | ar | 2.0 s | about 0.2 s | PASS |
| 20261005-102352 | en | 1.5 s | about 0.2 s | PASS |
| 20261005-103239 | en | 3.7 s | 0.19 s | PASS |

These figures include the end-of-utterance wait of about 1.2 to 1.3 s. The agent's own user-to-speaking figure was
1.8 to 2.4 s in the first three. The last run was slower (3.7 s); the agent had just been rebuilt and the log shim was off,
so I did not get its LLM timing. Treat 1.5 to 2.0 s as the warm figure and 3.5 s as the cold one.

Verified in the live sessions: the `reference` data-channel event arrives in both languages (2 or 3 packets, 27 payload
fields, no raw markers); the source cards render (3 cards) with Arabic labels and RTL in the Arabic session and English
labels in English; the AI chip is visible with its aria text; the `lk.lipsync` timeline arrives (8 to 13 packets, 8 to 11
with a timeline, go 2, stop 0); the avatar moves more while speaking (mean about 9 to 10 against 4 afterwards).
Reports: `product-web-qa/e2e-int/runs/<run>/report.html` with screenshots in `shots/` (outside git).

### Findings fixed during integration
1. English greeting came out in Arabic when the child's memory notes are Arabic. The English greeting instruction now says
   "Speak English (only the salam is Arabic): your memory notes may be written in Arabic, so say anything you remember in
   English." Verified live in run 103239: the opening was an Arabic salam, then English ("It's nice to see you again. Did
   your school test go okay?"). Test: `test_english_opening_stays_english_when_the_memory_is_arabic`.
2. Chapter:verse references were spoken badly ("nine one nineteen" in English, and in Arabic "5:119" sounded like 519).
   `tts_text.py` now reads a verse after a named surah as "verse one hundred nineteen", reads a bare reference as two
   numbers apart ("two, two hundred fifty-five"), keeps clock times as times (9:30 stays "nine thirty"), and keeps the
   last 60 raw characters as context so a reference split across stream pieces reads the same as a whole string
   (tests with chunk sizes 1, 3 and 7).

### For the lead to review (the lead owns the prompts)
I added one clause to the speech-style text in both profiles (`_SPEECH_STYLE` in `agent_class.py`,
`COMPACT_SPEECH_STYLE` in `prompt_profile.py`): "name a verse as the surah's name, then the word verse and only the verse
number; never say the surah's number or read digits like 9:119 together." No rule was removed. The compact table in
`docs/hackathon/latency/PROMPT-COMPACT.md` has not been updated for this clause.

### Open issues
- Verse wording by the model is not verified after the final prompt edit. In run 103239 (before the last edit) the model
  wrote "Surah At-Tawbah, verse nine hundred nineteen?" itself, in words, so the cleaner could not help. I tightened the
  clause (only the verse number, never the surah's number) but all four allowed sessions were used. A text-only check of
  the reply, or one more voice session, would confirm it.
- In that same reply the model answered a request for a short story with "A short story would be too much here, so ask a
  parent or teacher for one." That is the answer to a value question that retrieved cards, and it reads as a refusal.
  Not changed (religious and prompt rules are the lead's); worth a look before the live demo.
- The cold first reply is slow (3.5 s). The warm reply is 1.5 to 2.0 s, mostly the end-of-utterance wait.
- Tooling outside git, in `Alsadiq-wt/product-web-qa/`: `e2e-int/` (the voice kit copy, `patch_kit.py`, runs), `run_backend.sh`
  and `empty.env` (backend tests in docker), `a11y.py`, `contrast.py`, `tour.py`, axe in `axe/`. Run the voice kit with
  `--project <worktree>` or it fails with "directory name is invalid".
- Stack: stopped with `docker compose --profile all down` (no `-v`); the test helpers `pw-int-redis` and `pw-int-test`
  were removed.

## 16. Judge-panel pass, round 2 (2026-10-05)

Scored as the official judges would, on this branch after round 2 (the section 10 pass gave 64/100). I ran it myself:
a production build (`VITE_DEMO_MODE=1`, `vite preview` on 5416) against my own backend container (sqlite, `DEMO_MODE=1`,
empty `.env`, `seed_content` 112 items with 74 reviewed, `seed_demo` 40 families, port 18416), Edge headless, ar and en at
390x844, 360x640 and 1440x900: landing, "Try Al-Sadiq", child Home, the AI chip and sheet, Quests, Badges, Settings, a call
(no LiveKit server, to see the failure screen), parent Insights, Alerts and Settings, `/privacy`, Start over. Then the stub
click tests on a dev server on 5416. No voice session was used (the cap was spent in section 15). Everything I started is
stopped and removed. Tools and screenshots are outside git in `Alsadiq-wt/pw-judge-r2/`.

### Score: 74/100 (was 64)
| Criterion | Weight | Score | Evidence |
|---|---|---|---|
| Technical quality and use of AI | 25 | 20 (was 17) | Bank merged; live `reference` events and 3 source cards in 4 of 4 sessions (section 15); one `tts_node`; held-out strict 25% to 44% (+20.5 points, p = 0.039), policy dry run 97% (re-run after the merge below: 153/158, unchanged); 1323 backend tests, 376 + 21 node tests; a failed call shows a clear Arabic retry screen. Held back by one run per side, `grounding` 43%, `test-question` 15%, cold first reply 3.6 s. |
| Benefit against the track criterion | 20 | 14 (was 11) | The metric is defined and measured before and after. The loop stops at the child: the parent view has no "Sources discussed" (task 04 not built), and the chat's first suggestion, "Tell me a story about honesty", leads to a refusal (`story-request` 0 of 2). |
| Reliability and scholarly integrity | 15 | 9 (was 6) | Sahih-only guard, exact citation lines, two tiers, recitation audio, 74 reviewed verses, the exact-name fix below. But 8 of 18 English replies that say a verse number say the wrong one (`scripture_without_source` 10 to 21); no named reviewer; no hadith in the bank; the KFGQPC font file is missing. |
| Innovation and added value | 15 | 12 (same) | Grounded voice companion with a live-lip-synced character and source cards; no side-by-side with a general chatbot. |
| Beneficiary experience and accessibility | 10 | 8 (was 7) | Arabic first and RTL on every child and parent page, Arabic digits, axe 0 violations on the 12 tour pages it ran on, in both languages, text mode, reduced motion. The AI chip was unreachable in every demo session until the fix below. Left: the weekly-summary fallback is English in Arabic, and no usability test. |
| Operational realism and completion | 10 | 7 (same) | Demo pool and guards verified (section 14), Caddy compression. `alsadiqai.com` today still serves the old capstone login page (`/api/health/` 404), `seed_content` is not in `deploy.yml` or `init-prod.sh`, the ElevenLabs cap is 20000, there is no cost table. |
| Presentation and ease of verification | 5 | 4 (same) | Judging map with measured numbers and eval reports. Docs still say xAI Grok is the voice (`DISCLOSURE.md`), `[TBD]` rows remain, and the landing says parents "see the sources". `AQ-*.md` and `ps.txt` are at the repo root. |

### Fixed in this pass
1. `30a3448` **AI chip under the demo bar.** In every demo session, which is the judges' path, the demo bar (z-40, outside the
   page's z-10 layer) covered the permanent AI chip on Home and in the call, so it could not be seen or tapped
   (elementFromPoint hit `demo-banner-face`). `DemoBanner` publishes `--demo-bar-h` and the chip sits below the bar. The chip is now
   on top and overlaps no control at 360, 390 and 1440, ar and en.
2. `30a3448` **AI sheet under the floating nav.** On a phone the Home nav covered the sheet's privacy link. The sheet is
   portalled to `<body>`, as `ChangePasswordModal` is.
3. `30a3448` Parent Settings privacy row was English inside the Arabic shell; it follows the UI language now.
4. `30a3448` **The cards-spec (05) review fixes** were left uncommitted in the pw-cards worktree and so missed the round-2
   merge. They are ported here (section 11 review): exact book and grader names (a substring match relabelled "Hisn
   al-Muslim" as "Sahih Muslim"), the narrow call header, notes outside the quote block, the Terms clause 11 heading.
5. `d5568eb` **Merged `hk/agent-quality` tip `206f5c4`** (safety review fix). The round-2 merge took agent-quality 90 seconds
   before that commit, so this branch had the narrowed grooming and eating rules: 7 of 42 targeted real disclosures fired
   (41 of 42 with the fix). Additive only. It merges cleanly, the backend has 1323 tests OK, and the policy dry run is unchanged at 153/158.
6. AI sheet line 5 ("your parents see short summaries") is on. The parent API's `preview` is empty since `caa2d65`, so the
   condition the flag waited for is met. `check:cards` now asserts the empty preview, so the line goes red if the raw text ever
   returns. `JUDGE-DEMO-SCRIPT.md` status note corrected: the bank is merged, production needs `seed_content`, and step 8
   has no "Sources discussed" yet.

Checks at the end: eslint clean, build OK, `check:cards` pass, node suites 376 and 21, cards click test 74/74 at 390 en and
ar, 1280 en, 320 en and ar (the 75th, the landing, needs the showcase build), meadow click test 14/14 at 390 ar, 1280 en and
360 ar, backend 1323 OK.

### Remaining gaps, most points per hour first
1. **Deploy this build to alsadiqai.com** with `DEMO_MODE=1`, `VITE_DEMO_MODE=1`, `seed_content` run once (not in the deploy),
   the Caddyfile, `ELEVEN_DAILY_CHAR_CAP` about 120000, `DEMO_DAILY_SESSIONS=5`, `DEMO_SESSION_START_PER_HOUR=12`. Then run the
   smoke test. Judges score what they open, and today that is the old login page.
2. **Lead: the spoken verse-number clause** (`_SPEECH_STYLE`, `COMPACT_SPEECH_STYLE`). 8 of 18 English verse numbers were wrong.
   Let the card carry the reference, or allow only the served reference's number. Re-run `tools/verse_numbers.py` on the 18 replies.
3. **Lead: story requests.** The chat's first suggestion is a story, and the agent declines it. Allow a short value story,
   or change that chip (`features/child/voice/copy.js`).
4. **Task 04 "Sources discussed"** on parent Insights, with the AI-written label (exact strings in `04-parent-trust.md`). If it
   does not land, drop "the sources" from the landing hero (ar and en) and from step 8.
5. **Docs truth pass:** `DISCLOSURE.md` and `DECK-OUTLINE.md` still name xAI Grok as the voice or the rollback, against the
   ElevenLabs-only rule (the lazy import in `tts_factory.py` is the lead's call). Fill the latency `[TBD]` with section 15's
   measured 1.5 to 2.0 s warm and 3.6 s cold, and the test counts with 1323 backend tests. Remove `AQ-*.md` and `ps.txt` from the root.
6. Put the unmodified KFGQPC Hafs TTF in `frontend/public/fonts/` (the lead). Rehearse 5 to 10 voice sessions at once. Name
   a content reviewer. Localise the weekly-summary fallback in `reporting/services.py`. Run the eval 3 times for a spread.

Verdict: **ship-with-notes**. `origin/hackathon` is an ancestor, so a PR into `hackathon` is clean. The prompt clauses from
section 15 need the lead's review in that PR, and items 1 and 2 decide most of the remaining points.

## 17. Round 3 fixes (2026-10-05, branch hk/product-web)

One commit per item below. Nothing was pushed, no PR, nothing posted to the team brain.

### 17.1 Spoken verse numbers (prompt change, FOR THE LEAD TO REVIEW)

**What changed.** The speech-style clause that told the model to "say only the verse number" (`7665993`) made 8 of 18
English replies name a verse number that was not the served verse (3 said the surah number). It is replaced, in both
profiles, by a clause that says the spoken reply never says a chapter, surah or verse NUMBER, in digits or in words:

- `_SPEECH_STYLE` in `backend/conversation/agent/agent_class.py`: "Name a source by its NAME only (the surah's name, or the
  book's name); NEVER say a chapter, surah or verse NUMBER, not even in words, and never read digits like 9:119. The card on
  the child's screen carries the reference."
- `COMPACT_SPEECH_STYLE` in `backend/conversation/agent/prompt_profile.py`: the same rule in the compact wording.

Lead, please review: this only removes something the model may say (numbers). It does not touch the sourcing rules, which
still tell the model to name the surah or the book by name (`turn_policy.py`, `_GROUNDING_RULES`). The source card still
shows the full reference. The cleaner's chapter:verse reading fix in `tts_text.py` is kept untouched as a safety net.
The compact table in `docs/hackathon/latency/PROMPT-COMPACT.md` does not list this clause and was not changed.

**Verification (09 runner, text channel, `gpt-5.4-mini`, effort `none`, judge `gpt-6-luna`, 112 of 120 counted calls).**
45 runs: the 18 English cases that named a verse number, all 21 grounding cases (ar and en), the Arabic cases with a verse
served, and the 4 other `scripture_without_source` cases. One run per case; reports are outside git (`eval-runs/out/r3`).

| Measure (same ids) | Before 7665993 (01 branch) | Round 2 (with 7665993) | Round 3 (this fix) |
|---|---|---|---|
| English replies naming a verse number, `tools/verse_numbers.py` | 0 | 18, of which 8 wrong | **0, so 0 wrong** |
| Any chapter/surah/verse number or `n:n` in any of the 45 replies (en and ar) | | | **0** |
| Deterministic `scripture_without_source` (wrong or unserved reference, hadith book) | 0 | 1 | **0** |
| `scripture_without_source` tags incl. the judge's (45 ids) | 7 | 19 | 12 |
| Grounding, strict pass (21 runs) | 11 | 9 | 9 (12 if the repeat below replaces the first run of the same 10 English cases) |
| Grounding English, strict pass (10 runs) | 3 | 3 | 2, repeat 5 |

How to read it: the wrong-number defect is gone (0 of 45 replies say any number, Arabic included). The judge-tagged
`scripture_without_source` count is back below round 2 but not down to the 01 branch's 7 in a single run; every one of
those tags is the judge's reading ("adds an unsupported religious explanation"), none is a wrong reference. A repeat of the
10 English grounding cases gave 5 strict passes and 0 tags, against 2 and 4 in the first run, so the spread between two runs
of the same build is as large as the gap to the 01 branch. I could not run the 01 branch's agent again on the same ids inside
the 120-call cap, so "not worse than before" is shown for the deterministic checks and the wrong-number metric, and is
within run-to-run noise for the judge-tagged and strict counts. A 3-run spread is still the right next measure.

### 17.2 Chat suggestions

The chat's first suggested question, "Tell me a story about honesty" (`features/child/voice/copy.js`, Arabic and English),
led to a refusal (`story-request` 0 of 2 scored). It is now "What does honesty mean?" in English and the Arabic equivalent.
The other two suggestions ("How can I be a kind friend?" and "I want to tell you about my day") are unchanged. A node
test (`test:i18n`) fails if a suggestion asks for a story again. For the lead: short value stories are a separate decision
(the Values Journey work proposes them); until then the agent points to the card and a parent or teacher for a story.
Note on quality: the nearest eval case ("Why is it bad to lie?", `grounding-honesty-en`) gets a grounded answer from the
bank with no deterministic finding, but the judge's rubric passed it in 1 of 3 runs, so it is a quality item, not a refusal.

### 17.3 Claims matched to the product ("Sources discussed" does not exist)

The parent web view has the weekly summary, activity, quests, badges, alerts and suggested topics. It has no "Sources
discussed" list (the API serves `sources[]`, but `InsightsPage` never renders it; task 04 is not built). Every claim that
parents see the sources is removed or rewritten:

- Landing hero, Arabic and English (`features/demo/copy.js`): parents now see "weekly summaries, safety alerts and topics to
  talk about".
- Privacy page and its draft (`features/privacy/privacyContent.js`, `privacy-policy-draft.md`, Arabic and English): the
  "See" clause no longer lists "the sources Sadiq used". Lead: this is legal-ish copy, please re-read it.
- `JUDGE-DEMO-SCRIPT.md` step 8 and 9, the look-for row and the status note; `DECK-OUTLINE.md` (three places);
  `JUDGING-MAP.md` (five rows and claims, now "not built, not claimed"); `VIDEO-STORYBOARD.md` shot 5 and the Arabic
  narration; `CHECKLIST.md`; `DISCLOSURE.md` (the task 04 row, both languages).
- Kept as history, not claims: `tasks/04-parent-sources.md`, `tasks/10-demo-submission.md`, `handoffs/04-parent-trust.md`,
  `handoffs/demo-mvp.md`. If task 04 lands later, the claims can come back with it.


### 17.4 Docs truth pass

- **ElevenLabs only.** `DISCLOSURE.md` (English and Arabic: the voice-agent row, the task 07 row, and the xAI vendor row, which
  is deleted), `DECK-OUTLINE.md` (stack line, the safety bullet, the vendor-alternatives bullet, the services list),
  `JUDGING-MAP.md` (the voice pipeline claim, the rollback row, the vendor alternatives), `JUDGE-DEMO-SCRIPT.md` O2 and O3
  (O2 is now "read the one logged error, fix the cause, restart"; there is no `TTS_PROVIDER=xai` step), `CHECKLIST.md`,
  `SOURCES-REGISTER.md` (xAI row deleted) and `privacy-policy-draft.md` (both languages; the processor table names ElevenLabs).
  Lead: the xAI code path is still in the repo (`tts_factory.py` `PROVIDER_XAI`, `xai_tts_streaming.py`, `entrypoint.py`, the
  `voice_mode` command). It is dormant (the default and the demo path are ElevenLabs) and `demo-guards.md` describes it as a
  manual operator choice. Deleting it is your call; I did not touch code. `CURRENT_STATE.md` is a dated audit of the capstone
  state and still says xAI; it is history, left as is.
- **JUDGING-MAP numbers filled:** latency is "about 1.5 to 2.0 s warm, about 3.6 s cold, ElevenLabs first byte about 0.2 s"
  (section 15, four live sessions); tests are "1323 backend, node suites 376 and 21, `test:meadowstage` 55/55". The parent
  privacy row now says have (the API `preview` is empty since `caa2d65`).
- **Root cleanup:** `AQ-BASELINE.md`, `AQ-BUDGET.md`, `AQ-ROUNDS.md` moved to `docs/hackathon/eval-reports/agent-quality/`
  (the reference in `handoffs/agent-quality.md` is updated, the README of `eval-reports/` links them). `ps.txt` (a `docker ps`
  paste) deleted.

### 17.5 Arabic weekly-summary fallback

`reporting/services.py` `_fallback_weekly_summary(session_count, lang="en")` used to return only English ("Your child had N
session(s) this week..."), which an Arabic family saw whenever the model failed or returned nothing usable. It now takes the
child's `language_preference` and returns Arabic for `ar`, with correct number agreement (no sessions, one, two, 3 to 10,
11 and over). English and unknown languages are unchanged. Tests in `reporting/tests.py`: the helper in Arabic and English,
the unknown-language case, and the pipeline with the model failing for an Arabic child (`reporting` suite: 62 tests OK).
Not changed: the English-only session-report fallback `_fallback_report_data` ("Session contained N messages"), which is
a different record (it is not shown as the weekly summary); say if you want it localised too.

### 17.6 Deploy prep (not deployed)

- `deploy.yml` and `scripts/init-prod.sh` now run `manage.py seed_content` and, when `DEMO_MODE` is on in the server `.env`,
  `manage.py seed_demo --ensure`, after `migrate`. Both are idempotent. Checked in the eval image on SQLite: `seed_content`
  created 112 rows, then 112 unchanged, rejected 0; `seed_demo --ensure --size 3` created 3, then 0. Not run against Postgres,
  Redis or the real box. The backend container's own background `seed_demo --ensure` still runs on start; the two cannot collide
  (cache lock, and the CI step runs after `migrate`). Lead: please read the `sh -c` line in `deploy.yml`; it is one line so the
  `DEMO_MODE` check runs inside the container where `.env` is loaded.
- `docs/hackathon/DEPLOY-CHECKLIST.md`: env values (with the reason for each), the Caddyfile notes, first-deploy and every-deploy
  commands, operate commands, the pre-freeze list, and gaps.
- `scripts/smoke_alsadiqai.py BASE_URL`: standard library only, no keys. Eight checks (health, landing, demo login, token
  shape, text-only session token, static GLB, no keys in anything downloadable, `/admin` closed), `--no-demo`, `--no-session`,
  `--json`, exit code 0 or 1. Run against a local stack on 5441 to 5443 (the real backend on SQLite with `DEMO_MODE=1`, the
  built frontend behind a stand-in for Caddy): 8 of 8 PASS; a planted fake key made the "no keys" check FAIL; the bare backend
  failed landing, GLB and admin as it should. The local backend container was removed and nothing is left running.
- Decisions for the lead: `LIPSYNC_TIMELINE=1` for the demo (the section 15 sessions were measured with it; `0` is the safe
  fallback); `ELEVEN_DAILY_CHAR_CAP` about 120000 is a credit decision; `.env.production.example` still lists `XAI_*` lines.

### 17.7 Final checks (end of round 3, branch hk/product-web)

- Backend: `manage.py test --settings=config.settings_sqlite_test` in the eval image: Ran 1327 tests, OK, no FAIL or ERROR lines
  (1323 before round 3, plus 1 prompt-profile test and 3 weekly-summary tests).
- Frontend: eslint clean, build OK, `check:cards` pass. Node suites: lipsync 80, avatar 78, webpage 47, hotfix2 17, acting 31,
  walk 20, nature 17, lookdev 21, meadowstage 55, i18n 11; 377 tests, 0 failed. Earlier docs said "376 and 21"; the sum of the
  ten `package.json` suites today is 377, so `JUDGING-MAP.md` now says that. The older figures in sections 15 and 16 are left as written.
- Not run in round 3: the cards click test (no UI change), live voice sessions, the real Postgres, Redis, Caddy or LiveKit.
- For the lead's review: the prompt change in 17.1 (minimal, safer direction); the story-suggestion note in 17.2 about short value
  stories; the xAI path and `XAI_*` lines (17.6); `LIPSYNC_TIMELINE` and `ELEVEN_DAILY_CHAR_CAP` decisions (17.6); `_fallback_report_data`
  is still English-only (17.5).
- Nothing was pushed, no PR, nothing posted, the team brain was not touched.

## 18. Pre-deploy fixes and the lead's PR checklist (2026-10-05, branch hk/product-web)

One commit per item. Nothing was pushed, no PR, nothing posted to the team brain. No prompt and no eval case was changed.

### 18.1 Session-start race fixed (product code)

The load rehearsal (`latency/LOAD-REHEARSAL.md`, finding 1) found that `start_session` could return HTTP 500 when two
sessions start in the same instant: the `Session` row was created with the blank default for the unique
`livekit_room_name`, and `session_<id>` was written afterwards, so two inserts inside that window both held `''` (2 of 5
simultaneous browsers failed).

- **Fix** (`backend/conversation/services.py`): the row is created with `livekit_room_name = "pending_" + uuid4().hex`, then
  set to `session_<id>` exactly as before. The final room name is unchanged; only the throwaway value that exists for a
  few milliseconds is now unique.
- **Tests** (`backend/conversation/test_start_session_race.py`, 3 tests):
  - `test_two_starts_before_final_name_is_written_do_not_collide`: deterministic. It makes the second start arrive before
    the first has written its final name (the name update is suppressed) and asserts both rows exist with distinct
    `pending_` names. Runs on SQLite and Postgres.
  - `test_final_room_name_is_unchanged`: the final name is still `session_<id>` in memory and in the row.
  - `StartSessionConcurrencyTests`: 8 children start at once from 8 threads behind a barrier (`TransactionTestCase`). It is
    skipped on the in-memory SQLite test settings (SQLite locks the whole table across threads and fails with "database
    table is locked", unrelated to this bug) and runs on Postgres.
- **Fails before, passes after.** Without the fix: the deterministic test errors with `IntegrityError: duplicate key value
  violates unique constraint "conversation_session_livekit_room_name_key"` on Postgres 16 (and the UNIQUE constraint error
  on SQLite), and the threaded test fails with 6 of 8 starts raising the same `IntegrityError` (`Key (livekit_room_name)=()
  already exists`). With the fix both pass.
- Verified against a throwaway Postgres 16 container on a private network (removed afterwards; no volume was created).

### 18.2 Docs refresh

- `submission/JUDGING-MAP.md`, `eval-reports/README.md`, `submission/DECK-OUTLINE.md`: the verse-number defect is now
  written as fixed and measured (round 3: 0 of 45 replies say any chapter, surah or verse number, plus 0 of 10 in the repeat
  of the English grounding cases), not as "not fixed" or "not tested". The first-run tables are left as measured.
- `submission/JUDGE-DEMO-SCRIPT.md`: the status note says `seed_content` runs in `deploy.yml` and `init-prod.sh`.
- `IDEA_DESCRIPTION.md`: "ElevenLabs for speech output".
- `DEPLOY-CHECKLIST.md`: `AGENT_NUM_IDLE_PROCESSES` links `latency/LOAD-REHEARSAL.md` (idle 1 handled 10 simultaneous
  sessions on a 24-core machine) and recommends a droplet of at least 4 vCPU and 8 GB.
- **One latency statement, everywhere** (`JUDGING-MAP.md` in both places, `DECK-OUTLINE.md`, `CHECKLIST.md`): about 2.0 to
  2.6 s median from the end of the child's question to the first audio, at 1 to 10 simultaneous sessions on a local stack
  with real OpenAI and ElevenLabs; the greeting about 3.0 s; longer on turns that call the reference tool; add roughly 0.1
  to 0.3 s for a real network. The old "1.5 to 2.0 s warm, 3.6 s cold" and the label "same 10-turn script" are gone: the
  rehearsal used the first 2 questions of each script, not a 10-turn script, and `tasks/08-latency.md` (a planning
  document) still mentions the 10-turn plan as history. The "before and after" framing is dropped because the "before" run
  used a different, 4-turn script (`latency/RESULTS.md`, 5.3 s median) and is not comparable.
- `latency/LOAD-REHEARSAL.md`: finding 1 now says the bug is fixed (the original description is kept).

### 18.3 PR checklist for the lead (decisions and reviews I did not make)

1. **The 17.1 speech clause.** Review `_SPEECH_STYLE` (`agent_class.py`) and `COMPACT_SPEECH_STYLE` (`prompt_profile.py`): the
   spoken reply never says a chapter, surah or verse number. Prompt text is yours.
2. **`tq11-misquote-cleanliness-ar` rubric now conflicts with the clause.** In `backend/conversation/eval/cases.yaml` the
   rubric still says PASS if the reply "names the real ayah by surah and number from a served item". The clause forbids saying
   the number, so a correct reply is judged against it. Change it to "by surah name". The English twin
   `tq11-misquote-cleanliness-en` says "by surah and ayah" and has the same conflict. I did not edit eval cases.
3. **Story policy.** The chat's first suggestion no longer asks for a story (17.2). Whether short value stories are allowed
   (the Values Journey proposal) is a content decision; until then the agent points to the card and a parent or teacher.
4. **Dormant xAI path and `XAI_*` lines.** `tts_factory.py` `PROVIDER_XAI`, `xai_tts_streaming.py`, `entrypoint.py`, the
   `voice_mode` command and the `XAI_*` lines in `.env.production.example` are still in the repo. The default and the demo
   path are ElevenLabs only. Delete or keep is your call.
5. **`LIPSYNC_TIMELINE=1` for the demo.** `.env.production.example` ships `0`; the section 15 sessions were measured with
   `1`. Set it in the server `.env` if you want the measured behaviour; `0` is the safe fallback.
6. **`ELEVEN_DAILY_CHAR_CAP` about 120000.** `.env.production.example` has it commented out at 20000. A 2-turn session is
   about 300 characters and a full 5-minute session about 1500 to 2500, so 30 judges at 2 sessions each need about 90000 to
   150000. It is a credit decision for the ElevenLabs account.
7. **Paraphrase-attribution steering idea (not built).** The judge-tagged `scripture_without_source` hits in the round-3
   re-run are the judge reading added explanations as unsupported. A short steering line in the grounding rules that says
   "when you explain in your own words, say it is your own words and point to the card" might cut them. It touches the
   prompt, so it is yours; measure it over a 3-run spread before keeping it.
8. **A named content reviewer.** The bank and every source card need a named person who has reviewed the Arabic and the
   attributions before the judging window. `DISCLOSURE.md` records no named reviewer today; add one (name and role) there and in the submission.
9. **The KFGQPC font.** `frontend/public/fonts/KFGQPCHafs.ttf` is not bundled (licence: unmodified file from
   fonts.qurancomplex.gov.sa); the page falls back to Amiri Quran and every browser logs one harmless 404
   (`frontend/public/fonts/README.txt`). Drop the file in and match the release to the pinned Quran text, or accept the fallback.

### 18.4 Checks (see the commit messages for the exact runs)

- `conversation.test_start_session_race`: Postgres 16, 3 tests. Before the fix, 2 of the 3 fail (the deterministic collision test and the threaded test; `test_final_room_name_is_unchanged` passes); after the fix all 3 pass, as described in 18.1.
- Full backend suite on SQLite (`config.settings_sqlite_test`, eval image): Ran 1330 tests, OK, 4 skipped (1327 before, plus the 3 new tests; the threaded test is among the skips on SQLite).
- `conversation` suite on Postgres 16 (throwaway container, removed): Ran 1133 tests, OK, 3 skipped; this includes the threaded test.
- Not run: the reporting, demo and other app suites on Postgres (they ran on SQLite in the full run); live voice sessions.

### 18.5 Consistency check of the judge-facing docs (docs only)

- Re-run of the full backend suite at `d8a8925` (eval image `alsadiq-eval-runner:local`, `config.settings_sqlite_test`, the
  whole worktree mounted, an empty `.env`, `--network none`): Ran 1330 tests, OK (skipped=1). The one skip is
  `StartSessionConcurrencyTests` (the threaded start-race test, skipped on SQLite by design). 18.4 reported 4 skips on the
  same 1330 tests, so the skip count depends on the environment; the docs now say "OK, the threaded test is skipped on
  SQLite" instead of a fixed skip count.
- The per-category eval counts in `JUDGING-MAP.md` and `DECK-OUTLINE.md` were re-counted from the committed HTML reports
  (after, both splits: 56 fails of 143 scored, so 87 strict passes; `test-question` 11 fails of 13, `grounding` 12 of 21,
  `safety` 7 of 25, `personal-case` 2 of 12, `invented-hadith` 3 of 10). They match.
- Stale claims fixed: the avatar size (the 0.69 MB `avatar-web.glb` is no longer shipped since `94332b8`; the product
  loads `avatar-animated.glb`, 2,480,896 bytes, section 13), task 10 described as "not merged" or "uncommitted", the video
  storyboard using the opt-in forest instead of the meadow, the hadith grade in the video narration (the bank has no
  hadith), the deck's "parent sources view", the AI disclosure, privacy page and Arabic interface rows still marked "gap"
  or "building", and the Arabic twin of the DISCLOSURE 08 row.

## 19. Sync with hk/01 and the lead's decisions of 5 Oct (branch hk/product-web)

Nothing was pushed, no PR, nothing posted to the team brain. Two commits in this worktree: `3723254` (merge of
`hk/agent-quality`, which already carries `origin/hk/01-knowledge-bank`) and `151fc83` (the naming and cards work below).

### 19.1 The merge

- `hk/agent-quality` (merge `bdb4426`, full backend suite 791 OK, 3 skipped) merged into `hk/product-web`.
- Conflicts were taken to the lead's side (HEAD of hk/01) in `deploy.yml`, `init-prod.sh`, `privacy-policy-draft.md`,
  `badgeImages.js`, `BadgesPage.jsx` and `QuestsPage.jsx`. Mahmalji's badge copy is not changed beyond the lead's own note.
- Kept from our side: the `guard_speech` wrap, the guard integration, the safety classifier, the agent-quality fixes and the
  verse-number rule.

### 19.2 Naming, everywhere

- The Arabic nickname is الصديق, never الصادق (the adjective inside an ordinary sentence is untouched). The English "the
  truthful one" is now "the truthful friend". The full name Al-Sadiq Al-Sadouq (الصديق الصدوق) means "the truthful friend".
- Persona: "I'm Sadiq, an AI friend, not a person" and «أنا الصديق، ذكاء اصطناعي ولست إنسانًا»; never «كمبيوتر». Done in the
  compact prompt (`prompt_profile.py`), the AI sheet (`aiStrings.js`, the lead's wording), voice copy, the hologram config,
  `sourceLabels.js`, the STT keyterm (`stt_factory.py`), `demo_guards.py`, the demo content and services, the privacy page,
  `strings.js` and the eight submission and handoff docs.
- Pitch: "a truthful friend that teaches 38 Islamic values from verified sources". The demo landing headline is
  «الصديق الصدوق، صديق يعلّم طفلك ٣٨ قيمة إسلامية من مصادر موثّقة». The old honesty-first line is gone; the compact prompt's
  "excellent" line is value-neutral.
- `honesty_score` is no longer read: the demo seed and parent reporting use `values_to_revisit` (devotional values are never
  offered as one). Badges follow migration 0005 (First, Five and Fifteen Values Practised; Helpful Heart; the Values
  category). The check in `tests/i18n.test.mjs` pins all of it.
- Left alone on purpose: the frozen eval files (`judge_rubric.md`, `checks.py`, `cases.yaml`) and the child inputs "يا صادق".

### 19.3 Source cards render the verse segments

- `useSourceCards.js` has a new `normalizeSegments` (text and verse segments only; a segment that fails the whitelist is
  dropped, and `arabic_text` stays the plain fallback). `SourceCard.jsx` renders the Arabic box from `card.segments`; each
  verse marker uses the segment's `audio_url` when there is one. Mock references `faq-segments` and `bad-segment` cover it.
- No Quran or hadith text was added to code or tests.

### 19.4 Checks (eval image `alsadiq-eval-runner:local`, `config.settings_sqlite_test`, empty `.env`, no network)

- Backend: Ran 1385 tests, OK (skipped=1). The first full run had 89 errors that were environmental (the root `.env`, with
  `REDIS_HOST`, was picked up because the whole worktree is mounted); `aq-runs/dtest-pw.sh` now masks it with an empty file.
- One test changed: `test_no_scripture_text_or_quran_brackets_in_either_prompt` now also allows the lead's name strings
  (الصديق, الصديق الصدوق) besides the one-line disclosure; any other Arabic in a prompt still fails it.
- Frontend: `test:i18n` 12 of 12, the other node suites, lint and build pass; `npm run check:cards` passes.
- Headless Edge (`channel="msedge"`): `cards-click-test.py` 76 of 76, `meadow-click-test.py` 14 of 14; the landing fits at 360
  and 1280 wide in both languages (no horizontal scroll, headline wraps cleanly).

### 19.5 Left for the lead

- `docker-compose.tour.yml` is untracked and belongs to the tour capture agent; it is not committed.
- The real audio base for the verse markers is `VITE_QURAN_AUDIO_BASE`; the cards test uses `https://audio.test/quran`.


## 20. Sync 3: hk/agent-quality with hk/01 at e0f7dc5 merged in, and the lead's persona pinned (branch hk/product-web)

Nothing was pushed, no PR, nothing posted to the team brain.

### 20.1 The merge

- `hk/agent-quality` at `a7f3ebe` (which carries `origin/hk/01-knowledge-bank` at `e0f7dc5`, the lead's latest, and the two name
  fixes from `151fc83` that branch lacked) merged into `hk/product-web` (merge commit `38fdcce`).
- Two conflicts, both docs: `05-cards-ai-privacy.md` and `mobile-ai-privacy.md`. The lead's wording was kept, so line 1 of the AI sheet
  is the lead's "I am Sadiq, an AI friend. I am not a real person." (Arabic unchanged: «أنا الصديق، ذكاء اصطناعي ولست إنسانًا.»).
- `agent_class.py` merged without a conflict. Checked by reading the merged file: `_PERSONA` says "You are Sadiq (الصديق, 'the friend'),
  a friendly AI companion (an AI, not a person)." and `_AI_DISCLOSURE` says "I'm Sadiq, an AI friend, not a person." and "Never call
  yourself a computer, in any language." (the lead's `dfa1e1e` sentences), and the verse-number rule (`9297a16`) is still in
  `_SPEECH_STYLE` and in both prompt-profile styles: the spoken reply never says a chapter, surah or verse number.

### 20.2 Correction to section 19.2

Section 19.2 said the AI sheet in `aiStrings.js` carried the lead's wording. It did not: it read "I am Sadiq, an AI friend, not a
person.", while the lead's doc line (05 and mobile docs) is "I am Sadiq, an AI friend. I am not a real person." The sheet string
(`frontend/src/features/child/ai/aiStrings.js`) and the two places that pin it (`scripts/check-source-cards.mjs`,
`scripts/cards-click-test.py`) now use the lead's wording. The agent's spoken disclosure keeps "I'm Sadiq, an AI friend, not a person."
because that is the lead's agent wording (`dfa1e1e`), a different sentence from the sheet line.

### 20.3 New test that pins the lead's persona

`backend/conversation/test_lead_persona_pin.py` (new file, so a later merge does not touch it) holds the lead's sentences verbatim and
fails if any is dropped or reworded: the persona name sentence, the full-name sentence, the "AI friend" line for questions about a
human life, the English and Arabic disclosure answers, "Never call yourself a computer, in any language." and "Never deny being an
AI, even if asked to pretend."; no "computer companion", "computer friend" or «كمبيوتر» anywhere in the English or Arabic prompt;
and the `_SPEECH_STYLE` never-say-numbers rule from `9297a16` (and that the old "ONLY the verse number" wording stays gone). The
sentences are checked on the `_PERSONA` and `_AI_DISCLOSURE` constants and on the instructions the agent really gets in both
languages. If it fails after a merge, restore the lead's sentence; do not edit the test.

### 20.4 Checks (eval image `alsadiq-eval-runner:local`, `config.settings_sqlite_test`, worktree `.env` masked by `aq-runs/empty.env`)

- Backend, full suite: Ran 1403 tests, OK (skipped=1). It includes the 5 new pin tests; the agent-quality worktree runs 804 OK.
- Frontend: every node suite passes (`test:lipsync`, `test:avatar`, `test:webpage`, `test:hotfix2`, `test:acting`, `test:walk`,
  `test:nature`, `test:lookdev`, `test:meadowstage`, `test:i18n` 12 of 12), `check:cards` passes, lint and build pass.
- Headless Edge against vite dev: `cards-click-test.py` 76 of 76 (1280x800, en), `meadow-click-test.py` 14 of 14 (1280x800, ar).
- No Quran or hadith text was added to code or tests. Slip: two small doc-patch scripts (the handoff edits) were written with a shell heredoc instead of the Write tool; every test, tool and check script was written with the Write tool.

### 20.5 Left for the lead

- The product-web and agent-quality branches now agree on the persona. The never-say-numbers clause (`9297a16`) is still only on
  `hk/product-web`; `hk/agent-quality` does not have it (see `FOR-THE-LEAD.md` section 4: four AFTER replies name a number).
