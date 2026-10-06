> Source-checked fact sheet for the ElevenLabs plan in task 07 (plugin 1.5.1, models, voices, Arabic quality, livekit-agents text hooks).
> Written 2026-10-04 from the plugin and agents 1.5.1 wheels and ElevenLabs docs; no API key was used, so anything marked "unverified" still needs a key or a listening test.
> The evidence paths named as tmp/voice/... live in the author local job folder, not in this repo; the URLs and the plugin line numbers are the checkable parts.

# ElevenLabs plan fact-check (Al-Sadiq Al-Sadouq voice agent)

Date: 2026-10-04. Read-only check. Sources: the livekit-plugins-elevenlabs 1.5.1 and livekit-agents 1.5.1 wheels (extracted under tmp/voice/src), plugin 1.8.4 for comparison, ElevenLabs docs saved under tmp/voice/web. No API key was used. No other worktree or checkout was touched.

Verdict key: verified = confirmed in source or primary docs. wrong = contradicted. unverified = not confirmed, needs a listening test or a key.

## 1. Plugin 1.5.1

| Claim | Verdict | Evidence |
|---|---|---|
| livekit-plugins-elevenlabs 1.5.1 exists on PyPI | verified | https://pypi.org/project/livekit-plugins-elevenlabs/1.5.1/ ; wheel METADATA Version 1.5.1 |
| It depends on livekit-agents 1.5.1 | verified | METADATA: Requires-Dist livekit-agents[codecs]>=1.5.1 (a floor, not a pin). Plugin 1.8.4 needs livekit-agents>=1.8.4, so upgrading the plugin forces an agents upgrade |
| Default model is eleven_turbo_v2_5 | verified | plugin tts.py line 103. Set model explicitly |
| Constructor takes voice_id, model, language, voice_settings, apply_text_normalization, pronunciation_dictionary_locators, enable_ssml_parsing, sync_alignment, chunk_length_schedule, etc. | verified | tts.py lines 98-122 |
| apply_text_normalization defaults to "auto" | verified | tts.py line 110 |
| chunk_length_schedule has an effect | wrong | stored at tts.py lines 189 and 494, never sent in the URL or init packet. It is a no-op in 1.5.1 |
| Aligned transcripts supported via sync_alignment | verified | tts.py lines 150-153: TTSCapabilities(streaming=True, aligned_transcript=sync_alignment). Agents side flag is use_tts_aligned_transcript (agent_session.py line 222, agent.py line 663) |
| The HTTP path (synthesize / ChunkedStream) honors language, dictionaries, normalization | wrong | tts.py lines 319-339: POST body is only text, model_id, voice_settings. Use stream() (websocket) so those apply |
| Websocket path sends dictionaries and language | verified | init packet lines 617-636 (voice_settings, context_id, pronunciation_dictionary_locators); URL lines 849-867 (model_id, output_format, language_code, enable_ssml_parsing, enable_logging, inactivity_timeout, apply_text_normalization, sync_alignment, auto_mode) |
| Plugin 1.5.1 knows eleven_v4_turbo | wrong | models.py lines 3-12 list monolingual_v1, multilingual_v1, multilingual_v2, turbo_v2, turbo_v2_5, flash_v2_5, flash_v2, v3. No v4. A plain string may still be passed, but v4 turbo is Text-to-Dialogue websocket only, which the plugin multi-stream-input path does not use. See https://elevenlabs.io/docs/overview/models |
| VoiceSettings speed range is 0.8-1.2 | wrong | plugin comment at tts.py line 74 says 0.8-1.2. ElevenLabs docs say 0.7-1.2 (https://elevenlabs.io/docs/api-reference/text-to-speech/convert) |
| STT supports scribe_v1, scribe_v2, scribe_v2_realtime | verified | stt.py lines 63, 80-94 |
| Realtime STT sends keyterms | wrong | stt.py lines 195-197: keyterms only in the batch request. Lines 483-516: realtime URL has no keyterms, although the API supports them (https://elevenlabs.io/docs/developers/guides/cookbooks/speech-to-text/realtime/client-side-streaming ; keyterm prompting doc). Workaround: plugin >=1.8.x, or a custom STT subclass |

## 2. Models

| Claim | Verdict | Evidence |
|---|---|---|
| eleven_flash_v2_5 is the lowest latency model (~75 ms model time) and supports Arabic | verified | https://elevenlabs.io/docs/overview/models (flash v2.5 lists 32 languages including Arabic) |
| eleven_multilingual_v2 supports Arabic, higher quality, higher latency | verified | same models page |
| multilingual_v2 honors language_code | wrong | docs: language_code applies to flash v2.5 / turbo v2.5 / v3; multilingual_v2 detects language from text |
| Text normalization "on" for flash v2.5 | wrong (as a default) | normalization is off by default for flash v2.5, and forcing "on" is enterprise only. "auto" is the usable mode. https://elevenlabs.io/docs/overview/models |
| Pronunciation dictionary phoneme rules work on every model | wrong | phoneme tags work only on flash_v2, v3, v4 style models. multilingual_v2 and flash_v2_5 support alias rules only. https://elevenlabs.io/docs/eleven-api/guides/how-to/best-practices/pronunciation-dictionaries (saved pron-dict.md) |
| Phoneme or SSML tags over websocket need enable_ssml_parsing | verified | https://elevenlabs.io/docs/eleven-api/guides/how-to/websockets/realtime-tts |
| Pricing is per character, credits by plan | verified (shape) | https://elevenlabs.io/pricing/api . Flash/turbo cost half the credits of multilingual_v2 per character. Exact plan numbers change, recheck before buying |

## 3. Voice Library

| Claim | Verdict | Evidence |
|---|---|---|
| A library voice must be added to the account before use | verified (docs) | POST /v1/voices/add/{public_user_id}/{voice_id}, https://elevenlabs.io/docs/api-reference/voices/add-shared-voice and voice-library guide |
| Library voices usable through the API need a paid plan | verified | https://elevenlabs.io/docs/overview/capabilities/voices (free plan cannot use library voices via API) |
| The API accepts a library voice_id that was never added | unverified | no key, cannot test. Assume it fails and do the add step first |
| Shared-voice listing works without a key | wrong | GET /v1/shared-voices returned 401 unauthenticated (saved shared-ar.json) |
| The four voice ids exist and are Arabic | unverified | ids Habibah w4LX7bK479eHGM1k15Em, Asmaa qi4PkV9c01kb869Vh7Su, Anas R6nda3uM038xEEKi7GFl, Ashraf t8atLZaWuCcW6gENDwwa. Seen only in third-party and search results, no primary-source confirmation of language or accent. Verify with GET /v1/shared-voices?language=ar once a key exists, and listen |
| Voice slot quota on account | unverified | depends on plan (custom voice slots), check the plan page |

## 4. Arabic quality for kids

| Claim | Verdict | Evidence |
|---|---|---|
| Fully diacritized (tashkeel) text improves pronunciation | unverified | no primary doc. Test by ear. Plain-vowel-marked text for ambiguous words only is a reasonable start |
| The model reads the honorific sign (U+FDFA) correctly | unverified | not documented. agents filter_emoji does not strip it (see section 5). Safer: expand to the spoken phrase via a transform or alias rule |
| Arabic-Indic or Western digits are read correctly | unverified | docs say normalization handles numbers, and recommend spelling numbers out for non-English (numbers guide, https://elevenlabs.io/docs/overview/capabilities/text-to-speech/best-practices). Convert digits to Arabic words yourself |
| Pronunciation dictionaries can fix names and terms | verified | alias rules work on all models. Attach with pronunciation_dictionary_locators (max 3 dictionaries per request per docs) |
| voice_settings speed 0.7-1.2, stability, similarity_boost, style, use_speaker_boost | verified | convert API reference |
| Slower speed (~0.9) and higher stability suit a calm storyteller for kids | unverified | recommendation only, tune by ear |
| TTS must never read Quran verses | design rule | keep verses out of the text sent to TTS. Play recitation audio, route around the tts_node |

## 5. livekit-agents 1.5.1 text transform hooks

| Claim | Verdict | Evidence |
|---|---|---|
| AgentSession has tts_text_transforms | verified | voice/agent_session.py line 223 (param), line 140 (options field), docstring around lines 280-284, fallback at lines 362-365 |
| Default transforms are filter_markdown and filter_emoji | verified | agent_session.py line 190: DEFAULT_TTS_TEXT_TRANSFORMS |
| Passing your own list replaces the defaults | verified | agent_session.py lines 362-365 (default used only when not given). Re-include the builtins |
| Transforms accept builtin names or callables, applied before tts_node | verified | voice/transcription/text_transforms.py lines 7-31; voice/generation.py around lines 52-53; agent_activity.py lines 1984, 2193, 2732 |
| A replace() helper exists | verified | text_transforms.py lines 34-69, exported as livekit.agents.text_transforms (agents __init__.py line 26) |
| Agent.tts_node can be overridden for custom processing | verified | voice/agent.py line 342 signature (self, text, model_settings); default at lines 460-493 |
| filter_emoji strips U+FDFA | wrong | voice/transcription/filters.py EMOJI_PATTERN does not cover U+FDFA (read from the regex; a live test was blocked by a local types.py shadowing the stdlib) |
| Aligned transcript uses use_tts_aligned_transcript | verified | agent_session.py line 222 |

## Recommended settings

- Model: eleven_flash_v2_5 (lowest latency). Fallback eleven_multilingual_v2 if number handling or prosody is poor.
- Voice: add one library voice to the account first, then test all four by ear on real kid-style sentences. Start with Habibah, then Ashraf or Asmaa.
- voice_settings: stability 0.65, similarity_boost 0.75, style 0, use_speaker_boost true, speed 0.92 (tune by ear).
- language "ar" for flash v2.5 (ignored by multilingual_v2).
- Use the websocket stream() path, not synthesize(), so language, dictionaries and normalization apply.
- apply_text_normalization "auto". enable_ssml_parsing false unless break tags are needed.
- sync_alignment true only if aligned transcripts are shown, with use_tts_aligned_transcript on the session.
- tts_text_transforms: ["filter_markdown", "filter_emoji", custom transform for digits to Arabic words and the honorific sign to its spoken phrase].
- Pronunciation: alias dictionary for names and terms (works on flash v2.5).
- Do not rely on chunk_length_schedule or realtime STT keyterms in plugin 1.5.1.

## Risks

- Voice ids and Arabic quality are not confirmed without a key, and a library voice may fail until added to the account.
- Library voice API use needs a paid plan, and voice slots or monthly credits may run short during the build window.
- Flash v2.5 may mispronounce unvowelled Arabic. Keep multilingual_v2 as an A/B fallback.
- Honorific sign and digits may be spoken wrongly or skipped. Expand them in a transform.
- Plugin 1.5.1 ignores chunk_length_schedule and drops realtime STT keyterms. Upgrading to 1.8.x means upgrading livekit-agents too.
- eleven_v4_turbo is not usable via the 1.5.1 plugin.
- Quran verses must never reach TTS. Add a guard in the transform or tts_node.
