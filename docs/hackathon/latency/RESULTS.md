# Task 08 latency: measured results

Date: 2026-10-04. Branch: hk/08-latency. Measured by the QA run on live docker stacks with ElevenLabs
voices (xAI skipped, no fallback to xAI). Raw numbers: `e2e-voice/runs/ab/*/*.json` (outside git).
Agent replies for the content team: `docs/hackathon/latency/transcripts/`.

## Verdict in three lines

1. The task 08 bar (median at least 30 percent below baseline) is NOT met. Server total went from
   5.47 s to 5.29 s (minus 3 percent). Client time to first sound went from 5.65 s to 4.95 s (minus 12 percent),
   and that gain comes only from the hum filler on 2 of 8 turns.
2. Cause: 15 of 16 reply turns (both runs) make two LLM rounds because the agent calls
   `get_islamic_reference` on nearly every turn. The tool plus the second LLM round cost a median of about
   2.1 to 2.4 s in every config, before and after. Task 08 does not change that step.
3. The model, STT and prompt A/B shows no winner. All differences are inside the run-to-run noise
   (about plus or minus 1 s with 8 turns per cell). Keep gpt-5.4-mini and gpt-4o-mini-transcribe.

## Baseline vs after

Medians over 8 reply turns (4 Arabic and 4 English), one session per language. Seconds.
"Server total" is the child's last voiced moment to the agent's first audio (speaking state, so the hum
is not counted). "Client first sound" is the browser's first inbound audio after the child stopped
(the hum counts).

| run | code and config | server total | p90 | eou | ttft | ttfb | client first sound |
|---|---|---|---|---|---|---|---|
| baseline | hk/demo-mvp code, dev `.env` (gpt-5.4-mini, gpt-4o-mini-transcribe) | 5.47 | 7.22 | 1.23 | 2.06 | 0.30 | 5.65 |
| after | hk/08-latency, all defaults (hum on) | 5.29 | 5.91 | 1.23 | 1.53 | 0.29 | 4.95 |
| after, no hum | hk/08-latency, FILLER_MODE=off | 6.15 | 6.56 | 1.28 | 1.87 | 0.30 | 6.35 |

Change, after vs baseline: server total minus 3 percent, ttft minus 26 percent, client first sound
minus 12 percent. After with no hum is plus 12 percent on server total, which is noise: the only code
difference between the two "after" rows is the hum, and the hum never delays the server-side total.

Per language (server total median): baseline Arabic 7.15 and English 5.35; after Arabic 5.35 and English 5.06.
The baseline Arabic median is pulled up by one 10.2 s turn (first LLM round took 6.2 s, a one-off).

Where the time goes (after, defaults), median seconds:
end-of-turn wait and STT final about 1.2, first LLM round about 1.5, tool plus second LLM round
about 2.1, TTS first byte about 0.3. Sum about 5.1, matching the 5.3 s total.
Reply turns without a tool call were 3.2 to 4.8 s (5 of the 56 turns in the after and A/B runs; 0 of 8 in baseline), so removing the tool round is the largest
available lever.

Hum: it plays only on tool turns and with probability 0.5. In the after run 2 of 8 turns got a hum at
about 1.75 s; the other 6 waited for the real reply.

## A/B table

All on hk/08-latency, filler off (clean reply time), reasoning effort set by the auto ladder. The ladder
picked `none` for every model (all of these models accept none and low, reject minimal). Median over
8 reply turns, seconds. Reference row: gpt-5.4-mini, gpt-4o-mini-transcribe, full prompt.

| config | LLM | STT | prompt | server total | p90 | eou | ttft | ttfb | client first sound | tool turns | reply words (median) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| reference | gpt-5.4-mini | gpt-4o-mini-transcribe | full | 6.15 | 6.56 | 1.28 | 1.87 | 0.30 | 6.35 | 8/8 | 23 |
| luna6 | gpt-6-luna | gpt-4o-mini-transcribe | full | 6.18 | 6.67 | 1.24 | 2.06 | 0.31 | 6.35 | 8/8 | 31 |
| luna56 | gpt-5.6-luna | gpt-4o-mini-transcribe | full | 5.78 | 6.29 | 1.22 | 2.15 | 0.29 | 6.10 | 6/8 | 27 |
| gpt52 | gpt-5.2 (reference) | gpt-4o-mini-transcribe | full | 5.89 | 7.76 | 1.25 | 1.79 | 0.32 | 6.10 | 8/8 | 35 |
| stt_gpt_transcribe | gpt-5.4-mini | gpt-transcribe | full | 6.22 | 7.22 | 1.50 | 2.49 | 0.33 | 6.40 | 7/8 | 28.5 |
| compact | gpt-5.4-mini | gpt-4o-mini-transcribe | compact | 6.33 | 6.75 | 1.32 | 2.12 | 0.36 | 6.45 | 7/8 | 27.5 |

Reading it:

- LLM: gpt-6-luna, gpt-5.6-luna, gpt-5.4-mini and gpt-5.2 are within 0.4 s of each other on the median,
  which is inside the noise. gpt-5.6-luna was lowest (5.78) partly because it skipped the tool on 2 of 8
  turns. gpt-5.2 had the worst p90 (7.76). No model is clearly faster, so the choice can be made on Arabic
  quality (see transcripts) and cost. gpt-4.x and gpt-4o chat models were not tested, by the lead's rule.
- STT: gpt-transcribe added about 0.2 s to the end-of-turn wait (eou 1.50 vs 1.28) and its ttft cell is
  higher only by chance. Its transcripts were exact on all 8 questions, including "Sadiq" and "عليكم". The default
  gpt-4o-mini-transcribe made two small slips in the after-default run ("Sadik", "عليك") but none in baseline. gpt-live-transcribe
  and gpt-realtime-whisper were NOT run: `stt_models.py` refuses them (the plugin path does not accept them).
- Prompt: compact did not help (6.33 vs 6.15). Prompt size is not the bottleneck at these sizes.
- Reply length: gpt-5.2 and gpt-6-luna write longer replies (35 and 31 words) than gpt-5.4-mini (23),
  which adds TTS time after the first sentence but not to time to first audio.

## Method

- Kit: `%USERPROFILE%\Documents\Alsadiq-wt\e2e-voice` (Playwright, Edge, fake-mic WAV, WebRTC stats
  poller, chat bubble reader, agent log shim). Extra scripts for this task: `ab_audio.py`, `ab_driver.py`,
  `ab_parse.py`, `ab_report.py`.
- Stacks: docker compose, project `08-latency` for after and A/B, `08-latency-base` (detached worktree at
  6fc60f8, hk/demo-mvp code, copy of the `.env`) for baseline. Only `livekit_agent` is recreated between
  configs (`up -d --no-deps --force-recreate`). `docker compose down` without `-v` after each run.
- Audio: four short synthetic child questions per language, rendered once with ElevenLabs, 20 s of
  silence between them, one session per language. Topics: honesty, kindness to a sad friend, why five prayers,
  anger at a brother. No real child data. No scripture was added to code, prompts or data.
- Numbers: end-of-turn delay (eou), STT final delay, LLM ttft (first round), TTS ttfb, from the livekit
  `metrics_collected` events through the same shim for baseline and after, so both are measured the same
  way. Server total is the child's last voiced moment (user state "listening") to the agent state "speaking".
  Client times come from the browser's inbound audio level.
- Not changed: Silero end-of-turn wait stays at 0.55 s and interruptions stay on.
- Budget: 16 measured sessions plus 1 smoke session and one aborted start, at or under the cap of 18.

## Caveats

- Small sample: 8 turns per cell, one session per language per config. Treat differences under about
  1 s as noise. Rerun with 3 or more sessions per cell before deciding between close models.
- The baseline is the dev `.env` (gpt-5.4-mini and gpt-4o-mini-transcribe), so baseline vs after
  isolates the code only. A production-like baseline (gpt-5.2 and gpt-4o-transcribe) was not run; its numbers are unknown
  and it was out of the session budget.
- Nearly every turn used the Islamic reference tool, partly because the questions are about values and
  prayer. Casual chatter would call it less often and be faster; this test set is therefore a worst-ish
  case. Plain (no tool) turns were 3.2 to 4.8 s.
- The hum filler counts in client first sound only. For a clean reply time use the filler-off rows.
- Network, ElevenLabs and OpenAI are live and vary by the minute; runs were sequential on one machine.
- Arabic replies in the chat-bubble capture often end without final punctuation (also in baseline and
  gpt-5.2), so a few Arabic transcripts look cut mid-sentence. Content reviewers should read the endings
  with that in mind. The cause was not found (capture artifact or agent text sync). It does not affect timings.
- The Message table showed 0 rows although the agent logged saves, so transcripts come from chat bubbles.
- Not run: xAI (skipped by instruction), gpt-live-transcribe and gpt-realtime-whisper (refused by the
  plugin), any gpt-4.x chat model (excluded by the lead).

## What would move the number

1. Skip or shorten the tool round: call `get_islamic_reference` only for religious questions, or fetch the
   theme in parallel with the first LLM round, or answer first and attach the reference after.
2. Speak a short opener before the tool starts so the child hears something at about 1.5 s. The
   hum is only a partial version of this (half the tool turns, and it is not speech).
3. Re-measure after that change with 3 sessions per language.
