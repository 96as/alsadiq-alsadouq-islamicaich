# Handoff: compliance guards wired into the live ElevenLabs voice path

- **Branch:** `hk/03-guard-integ` (worktree `%USERPROFILE%\Documents\Alsadiq-wt\03-guard-integ`), created from `origin/hk/01-knowledge-bank` (`4fccb39`), merged with `origin/hk/07-voice` (`09d16d1`, PR #48). Not pushed.
- **Written by:** the 03 integration builder, 5 Oct 2026.
- **Why this exists:** 01 (turn guard, scripture guard, AI disclosure, safety privacy) and 07 (ElevenLabs voice, speech cleaner) both rewrote `agent_class.py` and `entrypoint.py`. Merged naively, either the guards or the cleaner would have been lost. This branch keeps both and adds the one missing join: the speech cleaner now carries the scripture guard.

## 1. What changed

| Area | Result |
| --- | --- |
| `entrypoint.py` | Imports from both sides. `build_value_index` and the turn-pipeline imports kept; `stt_factory`/`tts_factory`/`speech_tts_text_transform` kept; the xAI streaming import is gone (07's no-fallback rule). The value index is fetched in the same `asyncio.gather` as memory and quests. `AlSadiqAgent(... age_band=, value_index=)` is built as 01 did. `AgentSession(tts_text_transforms=[speech_tts_text_transform(lambda: agent.language)], use_tts_aligned_transcript=False, ...)` is built as 07 did (after the agent, so the language is read live). The typed-message callback still calls `agent.reply_to_typed(session, text)`. The first-meeting greeting still adds the AI line. Value names from the bank are also the STT keyterms (they replace the old `MoralTheme` list). |
| `agent_class.py` | Keeps 07's `language` property and `_aligned_transcript_on()`. `tts_node` is back as an override that runs only `guard_speech` (attribution guard, then scripture filter) and no longer runs `filter_markdown`/`filter_emoji` (the cleaner does that, so nothing is stripped twice). `transcription_node` strips markdown and emoji AND applies `guard_transcript`; aligned (timed) text passes through. It is a plain `def` that returns an async iterable (the lead's tests iterate it directly; livekit 1.5.1 accepts an awaitable or an iterable, checked at `agent_activity.py:2011-2012` and `:2250-2251`). |
| Dead code removed | `_format_islamic_reference`, `_query_islamic_references` and the `﴿ ﴾` note from 07. 01 removed the `get_islamic_reference` tool, so the LLM is never given verse text and has nothing to bracket. The bracket guard in the cleaner stays as defence against a verse the model recalls on its own. |
| `tts_text.py` | `TTSTextStream` now runs the lead's `_ScriptureFilter` on the cleaned text. Words carrying dense Quranic recitation marks (no brackets needed) are replaced by the same neutral phrase the bracket guard uses ("listen to the recitation" / the Arabic equivalent). Runs of dropped words get one phrase; chunk boundaries do not change the result; spacing around the phrase is normalised; a lone single-mark word is kept (the filter's own rule). `scripture_guard.STATS["speech_cleaner_scripture"]` counts runs; logs carry no text. |

## 2. Layer order on the voice path

```
LLM text
  -> session tts_text_transforms: speech_tts_text_transform
       numbers to words, markdown/emoji/honorific cleaning,
       Quran-bracket guard (neutral phrase),
       scripture-mark guard (neutral phrase)            [new here]
  -> AlSadiqAgent.tts_node: guard_speech
       attribution guard (unlicensed "the Prophet said / Allah says" tail -> DECLINE text),
       scripture filter again (backstop)
  -> ElevenLabs TTS

LLM text (second copy, aligned transcript OFF)
  -> AlSadiqAgent.transcription_node:
       markdown/emoji strip + guard_transcript (same guards as the speech)
  -> chat bubble, DB message, and the LLM's own chat history
```

## 3. Decisions to check

1. **The chat is guarded, not "the original".** The task text said the chat keeps the original. I did not do that. Reasons: (a) 01 never hands verse text to the LLM, so anything scripture-shaped in a reply is the model's own recall, which the content plan treats as unsafe to show; (b) verified in livekit 1.5.1 (`agent_activity.py:2044,2392`): the assistant message saved to the chat history and to our DB is the transcription node's output, so guarding that node also fixes the lead's "original text stays in the chat history" limitation; (c) the child still sees real verses, through the `reference` data events that carry the served source card. Digits and the honorific still stay written in the chat (only the speech is spelled out). If the lead wants the original back in the chat, delete `guard_transcript` from `transcription_node`; nothing else depends on it.
2. **`tts_node` stays, `filter_markdown`/`filter_emoji` do not run there.** One owner for each job: the cleaner cleans, the guards guard.
3. **xAI.** `tts_factory` still contains 07's operator-only `TTS_PROVIDER=xai` rollback; the entrypoint no longer imports the xAI streaming class directly, and nothing selects xAI automatically. Not touched here (07's decision).
4. **Tool and prompt text.** No change to `_AI_DISCLOSURE`, `_GROUNDING_RULES` or the greeting text; only verified present after the merge.

## 4. Tests

New: `backend/conversation/agent/test_guard_integration.py` (placeholder words and bare Quranic mark characters only, no scripture text).

- Cleaner: marked word becomes the phrase (en/ar); runs collapse to one phrase; chunk-size independence (1 to 11 chars); end-of-text and flush-sentinel cases; lone single mark kept; ordinary Arabic with harakat untouched; spacing; bracket plus marks in one reply; counter and log carry no text.
- Layer order (fake livekit): cleaner then `tts_node`; unlicensed attribution declined, licensed attribution passes; transcript gets the same guards as speech; timed words pass through.
- Disclosure and wiring: prompt carries the AI rule; first-meeting greeting has the AI line (en and ar), a returning child's greeting does not; age band and value-index slots set; turn-guard hooks come from `TurnGuardMixin` and precede `Agent` in the MRO; typed messages call `reply_to_typed`; the bracket helper from 07 is gone.
- Real livekit 1.5.1 (`RealPipelineGuardTests`): marks and brackets never reach the TTS input through `perform_tts_inference`; attribution declined there; real `TimedString` passes through the transcript node.

Changed from 07: `test_voice_wiring.py` (fake livekit gained `default.tts_node`, `livekit.agents.types.TimedString`, recorded `generate_reply` kwargs; the entrypoint harness patches `_get_value_index`; transcript tests no longer `await` the node and expect the guarded transcript; `BankVerseTests` and the real-pipeline bank-verse test were replaced by a bracketed-quote test, because the helper they tested no longer exists).

The lead's safety-privacy tests (`test_guard_round3.py`, `test_review_fixes.py`, `test_turn_guard_fixes.py`, `test_turn_policy.py`) pass unchanged on the merged code: staff-only flags with the no-parent-notify prefix, neutral parent alert text, persisted `SAFETY_QUIET`, quiet session. Nothing in the merge touched those paths.

## 5. How it was run

Local Python has no Django or livekit, so the suites ran in the existing agent image against this worktree (own `docker run --rm`, no compose stack touched):

```
docker run --rm -e PYTHONUTF8=1 -v <worktree>/backend:/app -w /app \
  --entrypoint python 07-voice-livekit_agent:latest manage.py test --settings=config.settings_sqlite_test <labels>
```

Results: `conversation.agent` 151 tests OK (before the new file); `conversation` 470 OK; full backend suite 599 OK, 3 skipped (the `scripts/voice` checks, because only `backend/` was mounted), with PyYAML installed in the throwaway container so the eval-case tests ran too. Real livekit tests ran (not skipped).

## 6. Latency

`scripts/guard_latency_bench.py` (pure Python, no network). Python 3.12 in the image, 200 runs per case, English 735 chars and Arabic 432 chars, per LLM chunk of 4, 12 and 40 chars:

| Cost | Per chunk |
| --- | --- |
| Scripture pass added to the cleaner | 1.0 to 1.4 us (4 chars), 1.8 to 2.9 us (12), 7.3 to 8.3 us (40) |
| `tts_node` guards (attribution + scripture filter) | about 10 us (4), 20 to 23 us (12), 50 to 59 us (40); p99 at most 115 us |
| Text taken in by the guards before the first output | 8 chars (about 2 words) at 4-char chunks, 12 at 12, 40 at 40: one to two chunks |

So the guards add tens of microseconds of CPU per chunk against a TTS first-audio time of hundreds of milliseconds. The only real effect is the attribution check holding back a short tail of words (it must wait to see if a trigger phrase is forming), which in practice is one to two LLM chunks before the first audio.

## 7. Known limits and next steps

- A verse written in plain script (no marks, no brackets) is not detected by any layer; the prompt rules and the attribution check are the defence (lead's documented limitation, unchanged).
- `tts_text.py` imports a private name (`_ScriptureFilter`) from `scripture_guard.py`. If the lead renames it, the import in `tts_text.py` is the only other place to change.
- With aligned transcripts switched on (they are off), the transcript would be the TTS's timed words and the transcript guard would pass them through untouched; the cleaner's scripture pass would still cover them.
- Not done here: a live call with real ElevenLabs audio (no key was used), and the task 09 eval runner.

## 8. Review fixes (Opus review, 5 Oct 2026)

Adversarial placeholder cases were run through livekit 1.5.1's real `perform_tts_inference`, with the session transform and the real `AlSadiqAgent.tts_node` (only the ElevenLabs call was replaced by a capture), at chunk sizes 1 to 40. Two integration defects were found and fixed:

1. **A bracketed span longer than 400 characters was partly spoken.** The cleaner runs before `tts_node`. It removes the bracket characters, so the lead's span filter in `guard_speech` never sees them. But the cleaner stopped dropping text after 400 characters and spoke the rest. A long verse with harakat easily passes 400 characters. On `hk/01` alone, the lead's filter dropped the whole span, so this was a regression from the merge order. **Fix (`tts_text.py`):** `_QuranGuardState` takes a `cap`, and `speech_tts_text_transform` creates its per-speech states with `cap=None`. An opening bracket now keeps the speech silent until a bracket closes the span or the speech ends, however long the span is. In the worst case, a stray bracket silences the rest of one reply, and the next reply starts closed. A single warning (with no text) is logged once 400 characters have been dropped. The capped behaviour stays for the plain `TTSTextStream`/`tts_text_transform` use, so 07's tests are unchanged.
2. **The chat could show an attribution that the audio declined.** `transcription_node` ran the guards before stripping markdown. Input like "the \*\*Prophet\*\* said" or "the \_Prophet\_ said" did not match the attribution patterns, so the chat bubble, the DB message and the LLM's own history kept the attribution. The speech was declined, because the cleaner strips markdown before the guard. **Fix (`agent_class.py`):** markdown and emoji are stripped first, then `guard_transcript` runs.

Tests added in `test_guard_integration.py`: `LongBracketedSpanTests` (3 tests), a markdown-attribution test in `LayerOrderTests`, and 2 real-livekit tests. All 6 fail on the pre-fix code and pass now. The full backend suite passes: 605 OK with 0 skipped, with the whole repo mounted so the `scripts/voice` checks ran too. Stale comments in `entrypoint.py` and `tts_text.py` ("the chat keeps the original text", "a bank verse still shows in writing") were also updated.

Limits that were measured and left as they are (they belong to the lead's `scripture_guard.py` or need a policy decision):

- These verse formats are still spoken and still shown in the chat: plain or harakat-only script; marks only on every other word; waqf signs written as separate words with spaces around them; verses quoted in curly braces `{...}`, which is common on Arabic websites. In an unlicensed turn, the attribution check still declines a lead-in such as "Allah says" or "قال الله". In a turn where a verse was served and that kind of attribution is licensed, nothing stops a verse the model recites from memory.
- Reversed ornate brackets (U+FD3E first): the speech is safe (the cleaner accepts either order), but the chat shows the span. This is because the lead's `_despan` only opens on U+FD3F. Suggestion for the lead: accept either order there, as the cleaner does.
- The attribution hold costs about 0 to 4 extra words before the first sentence is released when a trigger word ("Allah", "الله", "النبي") is near the start, for example with "Ma sha Allah" openers. The CPU cost stays in the tens of microseconds per chunk.
