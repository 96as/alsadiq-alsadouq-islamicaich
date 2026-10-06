# Handoff: avatar signals, backend half (package 9.4)

Date: 2026-10-04. Branch `hk/avatar-signals` (from `hk/demo-mvp`), worktree `%USERPROFILE%\Documents\Alsadiq-wt\avatar-signals`. Local only, not pushed.
Spec: `%USERPROFILE%\Documents\Alsadiq-3D\SPEC-EXPERIENCE.md`, section 8 (contract) and 9.4 (this package).

## 1. What this is

- The agent now publishes a handful of short strings as LiveKit participant attributes on its own participant. The 3D avatar in the child's app reads them to choose how it listens, how it talks and when to show the search hologram.
- Pure Python keyword rules. No LLM call, no network call, no new dependency, no scripture. A classification takes well under 1 ms (a test guards 2 ms).
- It cannot break the voice: every public method catches its own errors, and a failing `set_attributes` is logged once at warning level, then at debug.

## 2. What was built or changed

- **new** `backend/conversation/agent/avatar_signals.py` (constants, `normalize`, `classify_listen`, `classify_talk`, `AvatarSignals`). The module docstring explains the design and the attribute list.
- **new** `backend/conversation/agent/test_avatar_signals.py`: 93 unittest tests (no livekit, a fake room records `set_attributes`).
- **hooks** in `agent_class.py` (+20 / -2 lines) and `entrypoint.py` (+4 lines). About 17 added lines of code, 4 re-indented (the two tool bodies), plus the import and two comments or docstrings. This is a little over the "about 15" target, because the two `async with` wrappers re-indent the tool bodies.
  - `agent_class.py`: import; `self.signals = AvatarSignals()` in `__init__`; `self.signals.bind(room)` in `set_room`; the `tts_node` override (the exact 3-line body from the spec); `search("library")` in `get_islamic_reference`; `search("folders")` in `list_my_quests`; `hint_praise()` in `record_engagement` after a recorded `excellent` or `good`; `hint_safety()` at the top of `flag_safety_concern`.
  - `entrypoint.py`: `agent.signals.attach(agent_session)` after the session is built; `agent.signals.start()` after `await agent_session.start(...)`; `agent.signals.on_child_text(event.text, new_turn=True)` in `_on_text_input`.
- **changed tests** in `test_voice_wiring.py`: the fake livekit `Agent.default` got a `tts_node`; the fake room got `set_attributes`; `test_speech_cleaning_is_not_done_twice` used to assert that the agent has no `tts_node`, and now asserts that the new override hands text on untouched (no second cleaning); new wiring tests; two new tests against the REAL livekit 1.5.1 (the override through `perform_tts_inference` with the real speech cleaner, and the signature check).

## 3. The attributes (section 8.1)

Set on the agent participant. Keys all start with `al.`, never `lk.`. No value is ever empty (an empty value deletes the key).

| Key | Values (strings) | Set when | Batched with |
|---|---|---|---|
| `al.sig_v` | `"1"` | once, right after `AgentSession.start` | the initial values |
| `al.activity` | `idle`, `searching`, `found`, `none` | `searching` when a search starts; `found` or `none` when it ends. `idle` only as the initial value. | `al.search_kind` (with `searching`) |
| `al.search_kind` | `library`, `folders`, `web` | with every `searching` | none |
| `al.talk_style` | `explain`, `story`, `praise`, `question`, `gentle` | once per reply, when the reply's opening has reached `tts_node` | `al.reply` |
| `al.reply` | `"<int>"`, +1 per reply | with `al.talk_style` | none |
| `al.listen_style` | `neutral`, `curious`, `sad`, `excited` | the first classification of a child turn (at least 2 tokens), then only on an upgrade (sad > excited > curious > neutral) | `al.turn` |
| `al.turn` | `"<int>"`, +1 per child turn | with the turn's first `al.listen_style` | none |

Initial batch: `{al.sig_v: "1", al.activity: "idle", al.search_kind: "web", al.talk_style: "explain", al.reply: "0", al.listen_style: "neutral", al.turn: "0"}`.

Reliability rules (section 8.7), all implemented and tested:

- One pump task with an ordered queue. Keys queued together merge into one call, but two `al.activity` changes never merge (`searching` always goes out before `found`). Unchanged values are not re-sent; `al.reply` and `al.turn` always are.
- At most one `set_attributes` call per 120 ms; each call has a 5 s timeout. The pump exists only while something is queued, so there is nothing to shut down.
- A turn costs about 4 calls (listen 1, search 2, talk 1; a test caps it at 5).

## 4. How the web should read it (short)

- Live when `al.sig_v === "1"`. Read `al.reply` and `al.turn` as change counters.
- Two replies that land inside one 120 ms window merge into one call carrying the latest `al.reply`, so the counter can skip a number. Treat any change as "a new reply".
- Interim transcripts drive `al.listen_style` while the child is still talking (see section 7).

## 5. Task 03 one-liners (copy these in when task 03 lands)

Inside the new tools (`get_value_content`, `search_content`), around the lookup. This is the same shape the two existing tools now use:

```python
async with self.signals.search("library") as s:
    items = await fetch_the_content(...)
    s.found = bool(items)
```

In `on_user_turn_completed`, after the content injection (an instant lookup, under 10 ms). It signals only on a match, at most once per 45 s, and stays quiet while a real search is open:

```python
self.signals.quick_find("library", found=bool(items))
```

`flag_safety_concern` never searches (it stays silent) and `complete_conversation_quest` has no signal (the gamification event drives Celebrate). Those two are as the spec says.

## 6. Deviations and decisions

- **`quick_find` sends two transitions.** The spec says it signals "only on a match". A bare `found` would be invisible when the last activity was already `found` (the web dedupes unchanged values), so a match goes out as `searching` then `found`, each an ordered activity change. A miss sends nothing and does not start the cooldown. The clock is injectable (`AvatarSignals(clock=...)`) for tests.
- **Overlapping searches share one signal.** A depth counter: `searching` goes out with the first, the end goes out when the last finishes, and it is `found` if any of them found something. An exception or a cancellation inside the block ends it as `none` (the exception still propagates).
- **A reply is one `tts_node` call.** With the default livekit nodes that is one per spoken answer. A turn where the model speaks, calls a tool and speaks again is two `tts_node` calls, so `al.reply` goes up twice and the second opening is classified on its own. A reply with no text does not count. A stream that is abandoned (an interruption, or a discarded preemptive generation) before its opening is known decides nothing and keeps the hints for the next reply.
- **What the tap sees is the speech-cleaned text** (the session transform runs before `tts_node`), so a verse is already the neutral phrase and the classifier never reads scripture.
- **Turn lifecycle.** A child turn ends when the agent starts speaking. The next transcript after that (or the child starting to speak) opens a new turn: the per-turn class and the praise and safety hints reset. `thinking` does not end the turn, because a final transcript can land just after the agent starts thinking. Typed chat is always a turn of its own (`new_turn=True`).
- **Single-token lines** (under 2 tokens) are never classified, as the spec says. A typed one-word message therefore does not bump `al.turn`.
- **Negators**: the spec list (`مو مب مش ما لا لست ليس مهو not no never dont don't isn't wasn't`) plus a few English spellings (`didn't aren't isnt wasnt arent`). They only cancel SAD and EXCITED hits within 2 tokens before the hit, never a question.
  - Review fix: `لا` and `no` are also the answer "no", so they cancel only the word right after them (`لا أخاف`, `no tears`). Before, `لا أنا زعلان` and `No, I'm sad` (a child answering "are you OK?") read as neutral, which lost the empathy listen and the sad-child gentle reply.
  - Review fix: a negation never reaches across punctuation (`لا، خايف` and `Not really, sad.` are sad).
- **Talk "question" start** (review fix): the nouns `سؤال` / `question` no longer count as a question word at the start of a reply (`سؤال حلو، ...` is "good question", followed by an explanation), and an opening that ends in `!` is an exclamation, not asking back (`What a brave thing to do!`, `كم أنت شجاع!`). Endings in `?` or `؟` count as before.
- **Unknown `al.search_kind`** is sent as `web` (the generic look) rather than dropped.
- **Text normalisation** follows 8.3 exactly (the diacritic ranges, tatweel, the letter folds, curly apostrophes). Phrases are matched as token sequences, which is the same as the padded-string match but also survives punctuation between tokens.

## 7. Interim transcripts (static finding, not verified live)

The question was whether `user_input_transcribed` fires for interim results with the STT the agent uses. Reading the installed plugin source (livekit-plugins-openai in the agent image):

- `STT_REALTIME=1` (the default) uses the realtime transcription websocket. It emits `INTERIM_TRANSCRIPT` events from `conversation.item.input_audio_transcription.delta` messages, throttled to one per 0.5 s (`_delta_transcript_interval`).
- livekit's `audio_recognition` forwards interim events to `user_input_transcribed` (`is_final=False`).
- So `al.listen_style` can follow the child about every half second while they talk, and the final transcript upgrades it. I did not run a real speech session to confirm this; a live voice test would. If an STT only gives final transcripts, the listen style simply arrives later (after the child stops), which the web's freshness rule (`al.turn` changed in the current cycle) already tolerates.

## 8. Live check

- The demo-mvp stack was not running when I checked, but I did not touch any stack. I started my own throwaway `livekit/livekit-server --dev` container (`avsig-livekit`) on a private docker network (`avsig-net`) with no published ports, so no host port was used. Both were removed afterwards.
- Two real participants joined one room: the agent side used the real `AvatarSignals` bound to a real `rtc.Room`; a viewer recorded `participant_attributes_changed`. The script is in the author's scratch folder, not in the repo.
- Result: the initial batch arrived as one event and a late-joining viewer saw all 7 keys in `remote_participants["agent"].attributes`. Attribute delivery latency over 40 single updates: p50 1.8 ms, p95 2.5 ms, max 2.6 ms. This is a loopback docker network, so it proves delivery and ordering, not internet latency. Over the internet add the real round trip (typically 30 to 100 ms); the 250 ms escape hatch in 8.7 (a reliable `avatar` data topic) is not needed on this evidence.
- One full turn, as the viewer saw it: `{listen_style: sad, turn: 1}` at +1 ms, `{activity: searching, search_kind: library}` at +304 ms, `{activity: found}` at +502 ms, `{reply: 1, talk_style: praise}` at +804 ms. Order and merging are as designed.
- A token without `can_update_own_metadata` cannot set attributes (the first attempt silently produced no events). Agent worker participants are created by the LiveKit server with that permission, which is how livekit itself publishes `lk.agent.state`; only a hand-made test token needs the grant.

## 9. Tests and how to run

From the repo root, in the agent image (system Python has no Django or livekit):

```
docker run --rm -v "<worktree>/backend:/app" -e PYTHONUTF8=1 demo-mvp-livekit_agent:latest \
  python manage.py test conversation.agent.test_avatar_signals conversation.agent.test_voice_wiring \
  conversation.agent.test_tts_text --settings=config.settings_sqlite_test
```

- The three modules: 271 tests, OK.
- Full backend suite: 525 tests, OK (3 skipped: `scripts/voice not in this checkout`, as before).
- `test_avatar_signals` needs only Python (no livekit); the `RealLivekitTests` additions run only where livekit-agents 1.5.1 is installed.

## 10. Known limits

- Text-only sessions never call `tts_node`, so `al.talk_style` stays stale there (the web falls back to `explain`). Search and listen signals still work.
- Keyword rules misclassify sometimes. `What a lovely day.` (ending in a period) reads as a question because it starts with a question word; `I lost my pen` and `I lost my tooth` read as sad; English `happy` is not in the excited list, so `I'm so happy` reads as neutral. This matches the spec's lists (which were not extended) and costs only a gesture choice.
- `al.talk_style` for a reply whose opening is slower than 350 ms is decided from the little text there is (the spec rule), so a late praise marker is missed.
- Preemptive generation may run `tts_node` for a reply that is then discarded; that consumes a hint and bumps `al.reply`. The web reads talk style only when speaking starts, so this is harmless.

## 11. Next steps

- Task 03 adds the one-liners in section 5.
- The web builder reads the attributes (section 8.6 of the spec).
- A live voice session would confirm the interim-transcript finding in section 7.
