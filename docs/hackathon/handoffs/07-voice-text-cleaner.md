# Handoff: voice text cleaner and ElevenLabs fact-check (task 07)

Date: 2026-10-04. Branch `hk/07-voice-text`, worktree `%USERPROFILE%\Documents\Alsadiq-wt\07-voice-text`, code commit `56d7231`.

## 1. What this is

- Two helper pieces for task 07 (`docs/hackathon/tasks/07-elevenlabs-voice.md`), the move from xAI TTS to ElevenLabs.
- A text cleaner that runs on the LLM text just before it reaches TTS, with a guard that never speaks Quran verses.
- A source-checked fact sheet for the ElevenLabs plan: `docs/hackathon/handoffs/07-elevenlabs-facts.md`.
- It is NOT wired into the agent yet. The `hk/07-voice` team owns `entrypoint.py` and will merge this branch.

## 2. What was built or changed, and why

- `backend/conversation/agent/tts_text.py` (642 lines, pure Python, no livekit import).
  - Why: `eleven_flash_v2_5` does not normalise numbers, reads markdown symbols and emoji aloud, and cannot say the honorific ligatures. The product rule is that verses are never synthesised.
  - Strips markdown (headings, lists, emphasis, code fences, links, images), emoji, URLs and emails.
  - Expands the honorific ligatures (U+FDFA, U+FDFB, U+FDF2) to the spoken phrase in Arabic or English. The basmala ligature U+FDFD is dropped, never expanded.
  - Spells numbers out in Arabic and English: cardinals, English ordinals, percent, decimals, thousands separators (also Arabic ones), times like 10:30, very long digit runs digit by digit.
  - Keeps tashkeel. Removes tatweel and zero-width joiners.
  - Quran guard: anything between the ornate brackets U+FD3E / U+FD3F (either order) is dropped and replaced once by a neutral phrase ("listen to the recitation" in English, an Arabic equivalent in Arabic). Only the brackets are used to detect verses; no verse text is stored in the code.
  - Streaming adapter that is safe against chunk splits (a number, URL, link or bracket cut across chunks is still handled).
- `backend/conversation/agent/test_tts_text.py` (670 lines, 112 unittest tests).
- `docs/hackathon/handoffs/07-elevenlabs-facts.md`: verdicts (verified, wrong, unverified) on the ElevenLabs plan, with plugin line numbers and doc URLs.

Public API of `tts_text.py`:

- `prepare_for_tts(text, lang)` returns a cleaned string (one-shot).
- `TTSTextStream(lang)` has `feed(chunk)` and `flush()` (sync state machine).
- `tts_text_transform(lang)` returns the callable for `AgentSession(tts_text_transforms=[...])`. Create it ONCE per session.
- `clean_tts_stream(text, lang)` is the same thing as a plain async generator.
- `lang` is `"ar"`, `"en"` (region suffix such as `ar-SA` is fine), `"auto"`, or a zero-argument callable returning one of those.

## 3. Where it lives

- Repo: `%USERPROFILE%\Documents\Alsadiq-Alsadouq`; worktree for this work: `%USERPROFILE%\Documents\Alsadiq-wt\07-voice-text`.
- Branch `hk/07-voice-text`, based on `origin/hackathon` at `e7c98a3`. Local only, not pushed.
- Commit `56d7231` "feat(voice): add TTS text cleaner with Quran bracket guard" adds exactly two files: `tts_text.py` and `test_tts_text.py`. No existing file is touched, so the merge should not conflict.
- A later docs commit on the same branch adds the two files under `docs/hackathon/handoffs/` (this file and the fact sheet).
- The fact sheet cites evidence under `tmp/voice/...`; that folder is in the author's local job folder, not in the repo. The URLs and plugin line numbers are the checkable parts.

## 4. How to run, test and verify it

Run from `backend/` in the worktree:

```
cd backend
PYTHONIOENCODING=utf-8 python -m unittest conversation.agent.test_tts_text
```

- Expected (re-run on 2026-10-04): `Ran 112 tests ... OK (skipped=1)`.
- The skipped test needs `livekit-agents` installed; it was not installed on this PC. pytest is not installed either, but the tests are plain unittest.
- `PYTHONIOENCODING=utf-8` matters on Windows, otherwise Arabic output crashes the console encoder.

Quick manual check:

```
PYTHONIOENCODING=utf-8 python -c "from conversation.agent.tts_text import prepare_for_tts as p; print(p('**Hi** I am 12, see 3rd', 'en'))"
```

After wiring (see section 6): start the agent, have the LLM answer with a number, a bullet and an emoji, and listen; then check the on-screen transcript (it shows the cleaned text too, see section 9).

## 5. Decisions and why

- Pure Python module with no livekit import: tests run anywhere, and the same cleaner can be reused in `tts_node`.
- Quran guard fails closed: a stray opening bracket drops text until the next bracket, or up to 400 characters, then speech resumes with a warning in the log. Better to skip words than to speak a verse. (Changed on hk/03-guard-integ: the live per-speech guard, `speech_tts_text_transform`, no longer resumes after 400 characters; it stays silent until a bracket closes the span or the speech ends, because a long verse with harakat passes 400 characters. See `handoffs/03-guard-integration.md` section 8.)
- Verses are detected by the ornate brackets only, as specified. Unbracketed verses are not detected.
- Streaming holds text back to the last whitespace, so tokens split across chunks are cleaned whole. Cost: a word of delay at most.
- Ligatures are written as `\u` escapes in the source, so the file stays unambiguous.
- The hook is `tts_text_transforms` on `AgentSession`, verified in the livekit-agents 1.5.1 wheel (`voice/agent_session.py` lines 190, 223, 362-366; `voice/generation.py` lines 261-264).
- Passing your own list REPLACES the defaults `["filter_markdown", "filter_emoji"]`. This module already strips both, so the list can be just `[tts_text_transform(lang)]`.

## 6. Current status

- Built and tested, local only, not pushed, not merged.
- Not wired: `entrypoint.py` still builds `AgentSession` with `XaiStreamingTTS` and no `tts_text_transforms`.
- `agent_class.py` line 187 still has its own `tts_node` with `filter_markdown(filter_emoji(text))`. It is harmless to keep: session transforms run first.
- Waiting on: the `hk/07-voice` team to merge and wire it.

Integration steps for the `hk/07-voice` team:

1. Merge the branch: `git merge hk/07-voice-text` (or cherry-pick `56d7231`).
2. In `backend/conversation/agent/entrypoint.py`, import and add one argument to `AgentSession(...)` (currently line 159):
   - `from conversation.agent.tts_text import tts_text_transform`
   - `tts_text_transforms=[tts_text_transform(<lang>)],`
3. Pick `<lang>` (design choice B below). Options: the already resolved `resolved_tts_language` (values like `ar-SA`, `en`, or `auto` from `XAI_TTS_LANGUAGE`; `ar-SA` is accepted), or a callable if the language can change mid-session.
4. Optional alternative, if the language must come from the agent object: in `AlSadiqAgent.__init__` build `self._tts_transform = tts_text_transform(lambda: self._language)` once, and in `tts_node` replace `filter_markdown(filter_emoji(text))` with `self._tts_transform(text)`. Never build it inside `tts_node`, or the Quran state is lost between calls.
5. Keep the ElevenLabs settings from the fact sheet (stream via websocket, `apply_text_normalization="auto"`, model set explicitly). The cleaner spells numbers out, so it does not depend on the model normalising them.
6. Test: unit tests (section 4), then a live call with a reply that contains a digit, a bullet, an emoji, an honorific ligature and a bracketed placeholder. Nothing of that should be spoken literally.
7. Test the aligned transcript (`use_tts_aligned_transcript=True`): digits show as words and a bracketed verse shows as the neutral phrase on screen. Confirm that is acceptable in the UI.

## 7. Known issues and limitations

- URL that ends a sentence leaves a space before the full stop: `see https://x.com/a.` gives `see .` (verified). A URL followed by more text is fine (`see. Next`). The streaming path cannot take back a space it already sent, and the one-shot path matches it so both give the same output. Does not change what is heard.
- No currency, date, or Arabic ordinal reading. Arabic numbers use the plain counting form, with no gender agreement with the counted noun.
- A stray ornate bracket drops text until the next bracket (fails closed; capped at 400 characters only outside the live per-speech guard, see the note in section 5).
- Unbracketed verses are not detected.
- English only: 4-digit numbers from 1100 to 2099 are read as years (verified: 1999 is "nineteen ninety-nine", 2005 is "two thousand five", 1500 is "fifteen hundred", 2100 is "two thousand one hundred"). Arabic always reads the plain cardinal.
- In `auto` mode the language is decided per released piece of text (see design choice B), so mixed text can differ from a fixed `ar` or `en`.
- With `use_tts_aligned_transcript=True`, the chat transcript is built from the TTS input, so the on-screen text also shows words for digits and the neutral phrase for a bracketed verse. A verse card must come from the content bank, not from the LLM text.
- The one livekit-specific test was skipped here (agents not installed). The helper ran the transform through the real 1.5.1 `_apply_text_transforms` loaded from the wheel source and got the expected output, but that was a manual check, not a test in the repo.

Design choices to confirm (Majd or the voice team):

- A. Years, 1100 to 2099. In English, a plain 4-digit number in this range is read year style, so "1500 apples" becomes "fifteen hundred apples", and "1999" becomes "nineteen ninety-nine". Alternative: always cardinal, or year style only after words like "in" or "year". Confirm the range, or drop the year rule for a children's app that talks about quantities.
- B. `auto` language per piece. In `auto`, each released piece (text up to the last space of each streamed chunk) is classified by script: more Arabic letters means Arabic, more Latin letters means English, a tie keeps the previous choice. The same sentence can therefore number differently depending on where the LLM chunks split (for example `I am 12` followed by Arabic text reads "twelve" in English). A fixed language from the child's setting avoids that, but then English replies to an Arabic-language child get Arabic number words. Pick one: fixed from child language, `auto` as it is, or a per-session callable that follows the language the agent last replied in.
- C. The URL space glitch (section 7). Accept as is (inaudible) or fix by buffering one space more, at the cost of making the streaming and one-shot paths differ.

## 8. Next steps and future improvements, ordered by value

1. Wire it into `entrypoint.py` (steps in section 6) and run a live audition with real ElevenLabs lines.
2. Decide A, B, C above and adjust the code and tests to match.
3. Make sure verses can never reach the TTS text unbracketed: either the prompt tells the LLM to put any verse in the ornate brackets, or verses are served only from the content bank (tasks 03 and 05) and never via LLM text. The guard only sees brackets.
4. Add a livekit-agents integration test that runs in CI where the package is installed (the skipped test is a start).
5. Use the fact sheet to correct task 07 (see section 9) and decide the speed and stability settings by ear.
6. Pronunciation: alias pronunciation dictionary for names and terms (works on flash v2.5; phoneme rules do not).
7. Optional: currency, dates, Arabic ordinals, gender agreement for counted nouns.
8. Optional: let the callable `lang` follow the language of the last reply, so ar and en can switch mid-session without `auto` guessing.

## 9. Gotchas

- Console encoding on Windows: always set `PYTHONIOENCODING=utf-8`.
- `tts_text_transforms=[...]` replaces the default filters. Keep the markdown and emoji filters only if you do NOT use this module (this module covers both).
- Create the transform once per session. Per-call creation loses the open-bracket state and a verse split across two speech segments would leak.
- The cleaned text is also the on-screen transcript when aligned transcripts are on.
- The fact sheet contradicts parts of `docs/hackathon/tasks/07-elevenlabs-voice.md`. Do not copy the task file blindly:
  - `eleven_v4_turbo` is not in plugin 1.5.1 (`models.py` lists up to `v3`) and is not usable through its websocket path. Use `eleven_flash_v2_5`, fallback `eleven_multilingual_v2`.
  - Realtime STT in plugin 1.5.1 does NOT send `keyterms` (only batch STT does), although the API supports them. Fix: a newer plugin (which forces a livekit-agents upgrade) or a custom STT subclass.
  - `chunk_length_schedule` is stored but never sent in 1.5.1; it does nothing.
  - The HTTP `synthesize()` path ignores language, dictionaries and normalization. Use the streaming (websocket) path.
  - Speed range is 0.7 to 1.2 per the API docs, not 0.8 to 1.2 as in the plugin comment.
  - Phoneme rules in pronunciation dictionaries do not work on flash v2.5 or multilingual v2; only alias rules do.
  - The four candidate voice ids and Arabic quality are unverified until someone has a key; library voices need a paid plan and an add-to-account step first.
  - Pricing was checked only in shape (per character, Flash and Turbo half the credits of multilingual v2); recheck plan numbers before buying.
- No Quran or hadith text is in the code, tests or these docs. Tests use placeholder text inside the brackets. Keep it that way.
