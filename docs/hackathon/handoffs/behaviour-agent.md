# Behaviour agent (W1): gesture planner, g/u timeline events, al.search publisher

Branch `hk/behaviour-agent`, created from 3686f2b. Brief: `Alsadiq-3D/behaviour/BEHAVIOUR-SPEC.md` section 8.3. Nothing is pushed. The main session merges this in integration step 3.

Majd's ask behind it: train it on when to do which animation and pose and in which combinations; show the web page in his hand with the window scrolling when it searches; make everything work with no glitches. W1 is the agent side only. The avatar side (W2) draws the gestures, the web page card (W3) draws `al.search`.

## Done
- `gesture_planner.py`: plans gestures for the exact text being spoken, per clause, with the T1 model. Zero added voice latency (no LLM call, no await on the reply path), no new runtime dependency.
- `g` and `u` events in the `lk.lipsync` packets, plus late-plan messages with no `t` key (spec 3.2). `lipsync_timeline.py` carries them.
- `tts_node` wiring in `agent_class.py` (about 10 lines).
- `search_results.py`: the `al.search` publisher with the scripture meta-word and diacritics filters, safe-search only, domain only. Plus a flagged dev fixture source (no web tool exists yet, see below).
- `content_guard.py`: the shared scripture-like guard (meta-words, diacritic ratio). Never raises, returns True (block) on error.
- Flag `GESTURE_EVENTS`.
- Tests per spec 3.6 W1.

## Files (all under `backend/conversation/agent/`)
| File | Status |
|---|---|
| `gesture_planner.py` | new |
| `content_guard.py` | new |
| `search_results.py` | new |
| `gesture_runtime.py`, `data/gesture_model.json`, `lexicon_fallback.json` | T1 files, verbatim copies |
| `lipsync_timeline.py` | edited: g/u in packets, late messages, `tap(frames, plan=None)` |
| `agent_class.py` | edited: planner wiring, `web_search`, `set_search`, `safety_flagged_this_turn` |
| `entrypoint.py` | edited: planner wiring, dev search wiring |
| `test_gesture_planner.py`, `test_search_results.py` | new |
| `test_lipsync_timeline.py` | one-line test-double change, see Flags |

## How it works
- `tts_text_transforms` run before `tts_node`, so the planner sees exactly the spoken text. `GestureSegment.tap_text` wraps the text stream in `tts_node`, cuts it into clauses (at punctuation followed by whitespace, at 90 chars, or at end of stream) and plans each clause with `GestureModel.plan()`.
- Planned words are matched to ElevenLabs timed words by ordinal (plus or minus 2) and the same normalised text, then the event rides in the packet holding the anchor word's first character. `ci` is the speech-global item index, so it keeps counting across segments.
- `g` = `[ci, n, id, k, h]`, `u` = `[ci, talk_style, expression]` (spec 3.2). Late plan: `{"v":1,"sp":...,"g":[...],"u":[...]}` with no `t` and no `seq`, sent when the plan lands after the packet that holds the anchor has already gone.
- Inventory is the closed 29-id list. Offering gestures never use the left hand (coerced to R). Left is only for beats. Beat hands come from a seeded rng (R .45, L .35, B .20, never the same non-R twice in a row), so the same seed gives the same speech.
- Hints (`GesturePlanner.set_hints(talk_style, praise, safety)`) are one-shot per speech. The model hint applies only when the style confidence is below 0.5. A safety hint forces gentle/soft.
- A scripture-like clause is skipped: no entries, counted in `stats["skipped"]`. Arabic text is never altered.
- A planner that cannot start (no model, no fallback) leaves the agent working exactly as before.

## Run and test
Backend agent suite, in docker, own throwaway container (no compose stack touched):
```
MSYS_NO_PATHCONV=1 docker run --rm --network none -e PYTHONUTF8=1 -e PYTHONIOENCODING=utf-8 \
  -v "%USERPROFILE%/Documents/Alsadiq-wt/behaviour-agent/backend:/work" -w /work \
  demo-mvp-livekit_agent:latest python manage.py test conversation.agent --settings=config.settings_sqlite_test
```
Result: **328 tests OK** (baseline 226, 102 added) in about 7 s; **330 OK** after the review fixes (see Review). The "Task was destroyed but it is pending" lines are noise from `LipsyncTimeline._send_loop` in tests that do not flush.

Planner latency (512 clauses, mixed en/ar, real T1 model, in the container): p50 0.22 ms, **p99 0.48 ms**, max 1.53 ms per clause. A test enforces p99 at or below 2.0 ms.

Flags:
- `GESTURE_EVENTS`: `0/off/false/no` = off, `1/on/true/yes` = on. Unset follows `LIPSYNC_TIMELINE` (spec 3.3). It needs `LIPSYNC_TIMELINE` on, because the events ride in the timeline packets. Off means packets are byte-identical to before. **So turning `LIPSYNC_TIMELINE=1` on for children's sessions also turns gesture events on.** Until the Gulf-Arabic review passes, set `GESTURE_EVENTS=0` there, or keep W2's gesture playback behind its own dev/showcase gate.
- `SEARCH_DEV_SIM=1`: dev/demo fixtures for the web page (below). Off by default.

## T1 model used
Newest T1 files, copied verbatim and not edited. T1-READY timestamp: **2026-10-05 01:08:10 +03:00** (file mtime of `T1-READY.json`; its own "written" field is only the date). T1's own `test_gesture_runtime.py` was not copied.
- `gesture_runtime.py` sha256 `bd208fc1bea6e4b1cb7d2f86d66599f21b1000e4615ac8662e45f61653fa55db` (source mtime 01:04:56)
- `data/gesture_model.json` sha256 `16b166fe351513b269dc177821dbc7f63d4f6d41fa01e7e14e09bc6f8e81549e` (source mtime 00:50:44, 385,456 bytes)
- `lexicon_fallback.json` sha256 `5555f74269bf2747f4847f5867422d83886d1fc7cf0930325cf3bbf0b76e3fee`

T1 metrics: anchor F1 0.694 (lexicon 0.602), beat F1 0.557, talk_style macro F1 0.717, expression macro F1 0.526.

## T1 caveats (gate for shipping)
- **The Gulf-Arabic review still blocks shipping gestures to children.** Treat gestures as dev/showcase only until that review passes. `GESTURE_EVENTS` is on by default whenever `LIPSYNC_TIMELINE=1` (spec 3.3), so the gate is `GESTURE_EVENTS=0` for kids' sessions (or a W2-side gate), not "leave it unset".
- The talk_style bar (0.80) and the expression bar (0.65) are failed. `tau_unc` retraining is pending.
- An `ask` anchor on a question can give two head-tilt entries. The planner dedupes within 3 words.
- `plan_clause` anchors multi-word cues on the first token.
- Smoke test: a negative Arabic sentence got a praise/proud `u`. The `u` event is the weakest output; W2 should treat it as a soft hint (never override a signals-driven style).

## Recorded fake session (real T1 model, seed 11)
Produced by a scratch script through the real `GestureSegment` and timeline with a fake room (no audio, no network). `item` is the speech-global char index; each event sits on the word shown.
```
== en: 160 items, 13 packets, 8 g, 5 u
  item   0  u praise/excited starts 'Well d'
  item   5  g clap     k3 B  on 'done'
  item  11  u explain/neutral starts 'I am s'
  item  19  g heart    k2 R  on 'proud'
  item  33  u question/curious starts 'Do you'
  item  48  g beat     k1 L  on 'hear'
  item  73  g tilt     k2 -  on 'whale'
  item  80  g wave     k2 R  on 'Hello'
  item  97  g think    k2 R  on 'Let'
  item 116  g beat     k1 R  on 'moment'
  item 155  g round    k2 B  on 'ball'
== ar: 129 items, 10 packets, 7 g, 6 u
  item   0  g clap     k2 B  on 'أحسنت'
  item  33  g greet    k2 R  on 'السلام'
  item  75  g round    k2 B  on 'الشمس'
  item  88  g tilt     k2 -  on 'اليوم'
  item  95  g shake    k2 -  on 'لا'       (u gentle/soft)
  item 107  g beat     k1 R  on 'صحيح'
  item 113  g nod      k2 -  on 'نعم'
```
(u events at the same item as a g are omitted from the list above for space; the full run shows them.)

## Web search page (`al.search`, spec 6.2)
No web tool exists in the agent, so by the brief the publisher is wired only when one does. What exists now:
- `SearchPublisher(room, lang, safety_flagged)` in `search_results.py` publishes `searching`, `results` and `none` on topic `al.search`, reliable, compact UTF-8 JSON. Limits: max 5 results, title 70, snippet 140, domain only (host, validated), nothing clickable, tags/controls/bidi overrides stripped. Results with no title or domain, or that trip the scripture guard (meta-words, diacritic ratio), are dropped. A blocked query or a safety-flagged turn sends the grown-up card instead.
- `SearchPublisher.search(query, provider, ...)` refuses a provider without `safe_search is True`, never raises, and treats a failed or slow provider (8 s) as `none`.
- **The one-line hook for the real web tool:** `AlSadiqAgent.web_search(query)`. It is deliberately NOT a `function_tool`, so the LLM cannot call it. When the real tool lands, call `await self.web_search(q)` from it (or hand `set_search(publisher, provider)` a provider with `safe_search = True`). With the signals branch merged it runs inside `async with self.signals.search("web") as s`, so `al.activity` keeps driving the state machine.
- **Dev fixtures:** `SEARCH_DEV_SIM=1` wires `DevSearchProvider` (canned bees, moon, rain and generic results in en/ar; domains end in `.example`; `safe_search=True`, `is_fixture=True`) and a request topic `al.dev.search` (payload `{"q":"..."}`, other topics, bad JSON and blank q ignored). It logs a warning at startup. Every message from it carries `fx:1`. Never enable it in production.
- Two optional fields beyond spec 6.2, both additive: `gu:1` (neutral grown-up card, `q` is empty) and `fx:1` (content is a dev fixture, show a badge).

Integration notes:
- W3: handle `gu:1` (neutral grown-up card, no query shown) and optionally show a "demo" badge for `fx:1`. Draw all text as canvas text or `textContent`, never HTML.
- W2: gestures arrive in `lk.lipsync` as `g` (and `u`) arrays; a message with no `t` is a late plan, apply by `ci` as usual.

## Merge with the signals branch (`avatar-signals`)
- Its `tts_node` calls `self.signals.tap_reply(text)`. Compose as `text = seg.tap_text(self.signals.tap_reply(text))` so the planner sees the text signals passes on.
- Feed signals talk-style, praise and safety into `planner.set_hints(...)`.
- That branch deletes `lipsync_timeline.py`, so the merge needs care: this branch keeps and extends it.
- It also edits `flag_safety_concern` (hint_safety). My change adds `self._safety_flagged_msg = self._last_child_message_id` there, so expect a small textual conflict.
- Its agent tools use `async with self.signals.search("library") as s: ... s.found = ...`; `web_search` uses the same shape with `"web"`.

## Flags (things to know)
- `test_lipsync_timeline.py`: the `Spy.tap` test double became `tap(self, frames, plan=None)` to match the new signature. Test-only, no behaviour assertions changed.
- `LipsyncTimeline.tap(frames, plan=None)`: `plan` is a `GestureSegment` or None, and None gives the old behaviour exactly.
- No Quran or hadith text anywhere; fixtures and tests use synthetic lines only.

## Known issues and next steps
1. Gulf-Arabic review of the gesture mapping. Until it passes, `GESTURE_EVENTS=0` wherever `LIPSYNC_TIMELINE=1` is on for children (the flag defaults to on with the timeline), or W2 gates playback.
2. T1 retrain (`tau_unc`, talk_style and expression bars), then replace the three T1 files and re-run the suite.
3. A real web tool: one call to `web_search`, with a provider that is safe-search only.
4. Live check with W2/W3 against a real LiveKit room (not possible in this worktree: no audio, no browser run here).
5. The planner plans per clause, so a very long unpunctuated sentence is cut at 90 chars. The cut is always at whitespace, so no word is split, but the model sees half a phrase on each side and a phrase can get two gestures.

## Review (Opus reviewer, 2026-10-05)
Verdict: ship with notes. Everything below was measured by the reviewer in a throwaway `demo-mvp-livekit_agent` container (`--network none`, worktree mounted read-only) with a scratch harness that never entered the repo. The harness used the real T1 model, the real patched ElevenLabs `_to_timed_words`, the real `LipsyncTimeline` and `AlSadiqAgent._tapped`, and 120 synthetic replies from T1's corpus (60 en, 60 ar, every third speech in two segments).

| Check | Result |
|---|---|
| Suite | 330 OK (328 plus 2 review tests) |
| Text passthrough | every chunk identical, in order, for all 120 speeches |
| Frames | every frame `is` the input frame, none dropped or added |
| Chunk latency, LLM-paced (3 ms apart) | tap p50 17 us, p99 39 us; without the tap p50 20 us, p99 49 us: no measurable difference |
| Planner per clause (512 clauses) | p50 0.23 ms, p99 0.54 ms, max 0.69 ms (budget 2 ms) |
| Event-loop block per chunk | p50 0.4 us; p99 0.36 ms, max 0.66 ms (only the chunk that closes a clause pays) |
| `_publish_frame` per frame | 5 us without a plan, 11 us with (p99 15 / 53 us) |
| Model load at session start | 17-30 ms, once per session (not on the reply path) |
| Packet schema | 882 g and 562 u events: arity, types, closed ids, k 1-3, h R/L/B/"", L only on beats, every ci inside its own packet and on its timed word's first item, n = the word length |
| Delivery | planned 1,444 events, delivered 1,444, dropped 0 |
| Late plan | forced a final clause with no trailing space: one message `{"v","sp","g","u"}`, no `t`, no `seq`, ci on the right words ("What", "think?") |
| Fault injection (12 kinds) | planner, model, guard, take, note_word, bind_sink, word_norm, word_len, drain, segment and _note_ms raising, and publish_data failing: text and frames unchanged, nothing raised. An upstream error still propagates and closes the upstream; an early close closes the upstream |
| al.search | 15 scripture-like rows (meta-words in en/ar, clitics, curly apostrophe, vowelled Arabic, quran domain) all dropped; safe rows kept (max 5); blocked query and a flagged turn give the grown-up card with `q` ""; non-safe-search, failing, slow (timeout) and a raising safety callback all give 0 cards |
| Flags with a clean env | LIPSYNC_TIMELINE off, GESTURE_EVENTS off, SEARCH_DEV_SIM off |

Fixes made by the reviewer (one commit):
- Beat hands: when all four redraws repeated the last non-R variant, it was kept, so about 0.4% (explain) and 0.9% (story) of beats repeated L or B back to back, against spec 2.5 step 5 ("never"). It now falls back to R. Measured after: 0 repeats in 400,000 draws. Test added.
- Safety turns: the safety hint forced the `u` event to gentle/soft, but the gestures still followed the model's own style (clap, wow and beats could ride next to a gentle `u`). With the safety hint the planner now keeps only the gentle set (heart, calm, me, you, hug) at k 1 and no beats (spec 2.7); head gestures stay. This only matters once the signals branch feeds `set_hints(safety=...)`. Test added.
- The content-guard test named a real surah. It now uses a generic phrase, because spec 1.7 bans surah names in tests.
- This handoff: `GESTURE_EVENTS` is on by default with `LIPSYNC_TIMELINE` (spec 3.3), so the Gulf gate is `GESTURE_EVENTS=0` for kids, not "flip it on later".

Notes for integration (not fixed here):
- A question like "What do you think?" gets two tilts: one with `ask` on the first word and one at the `?`. Both follow the spec's rules (1.5, 2.9). W2 should treat a tilt that arrives while a tilt is held as a no-op, so the head does not tilt twice.
- The novelty history (`used_ids`) is per speech, so the first sentence of a new reply does not know the last reply's gesture. W2's "no repeats in a row" rule (2.6) covers this across replies.
- T1 is retraining right now: `behaviour\train\model\gesture_model.json` changed at 01:56 (sha 2762f5...) after T1-READY (01:08). This branch has the READY version (16b166...). Re-copy only when T1 writes a new READY, then re-run the suite.
- Spec 6.2 asks results to "pass the same blocklist as the safety flag". The backend has no keyword blocklist (the safety flag is an LLM tool), so the provider's strict safe search plus the scripture guard are the only filters. A real web tool should bring its own blocklist.
- When the speech cleaner replaces a Quran bracket with "listen to the recitation", the planner can put a beat on "recitation" (en). It is harmless, but if the avatar should stay still there, skip the cleaner's phrase in `_plan_clause`.
- The model loads per session (17-30 ms at connect). It could be loaded once per process in `prewarm`.
