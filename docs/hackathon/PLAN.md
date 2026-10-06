# Hackathon plan: Al-Sadiq Al-Sadouq (4–6 Oct 2026)

**Goal:** Al-Sadiq becomes a children's Islamic companion that can be trusted. Every verse and hadith it uses comes from an approved, graded and traceable source. Parents can see those sources and verify them. The experience is faster and more alive: ElevenLabs voice, an avatar that loads instantly and moves, and a web UI that matches the mobile app.

The current state is documented in [CURRENT_STATE.md](CURRENT_STATE.md). Onboarding is in TEAM_SETUP.md.

## How we work
- **Pick a task** from the table below. Claim it in the brain (`Task board`) and in the task file's `Owner:` line. Each task has its own branch, `hk/NN-name`.
- **Run one Opus 5.5 session as the "CEO" for your task.** Paste the task file's *Suggested CEO prompt* into it. The CEO delegates the work to subagents (`.claude/agents/`) and has their diffs reviewed.
- **Open PRs into `hackathon`** around 13:00 and 21:00. The lead merges them.
- **The brain is the shared memory.** Your AI reads and writes it automatically; the protocol is in `AGENTS.md`.

## Tasks
| # | Task | Est. | Fit | Depends on | Owner |
|---|---|---|---|---|---|
| 00 | Team AI setup | 1.5 h | full-day | none | Salamah (in progress) |
| 01 | Knowledge bank schema and seeding | 5 h | full-day | none | TBD |
| 02 | Content curation | 4 h of human review, plus agent batches | block-friendly | 01 schema (it can start drafting JSON before that) | TBD |
| 03 | Retrieval and grounding (RAG) | 6 h | full-day | 01 | TBD |
| 04 | Parent traceable sources | 4 h | block-friendly | 03 | TBD |
| 05 | Web UI/UX parity and source card | 10 h | full-day | 03, for the live source card only | TBD |
| 06 | Avatar: size, preload, animation, blink experiment | 8 h | full-day | none | TBD |
| 07 | ElevenLabs voice and STT check | 5 h | block-friendly | none | TBD |
| 08 | Response latency | 4 h | block-friendly | none | TBD |
| 09 | Eval harness | 4 h, plus writing the cases | block-friendly | 03 for the runner; cases can be written now | TBD |
| 10 | Demo and submission | 5 h | block-friendly | everything | TBD |

**Capacity.** Two members have about 7 h a day, and Mahmalji 3–4 h (Claude and Codex).

**Critical path: 01 → 03 → 04 and 09.** Task 01 must be merged by the end of Day 1.

## Timeline
| | Day 1 (Sun 4) | Day 2 (Mon 5) | Day 3 (Tue 6) |
|---|---|---|---|
| Work | 00 setup<br>01 bank<br>02 values list and first 15 values<br>06 avatar size, preload, idle motion<br>07 ElevenLabs behind a flag<br>08 baseline numbers<br>05 tokens | 03 grounding<br>04 parent sources<br>05 pages and source card<br>06 avatar states and blink timebox<br>07 voice audition and STT check<br>08 fixes<br>09 runner and cases<br>02 at 30+ values | 09 full eval and fixes<br>bug bash<br>production deploy<br>10 demo and submission |
| Checkpoint | **21:00 merge:** a voice session running on ElevenLabs with 15 values seeded | **21:00:** feature freeze and staging deploy | **13:00:** code freeze, then submit |

## Key decisions (the full log lives in the brain's `Decisions log`)
1. **Bank shape: a flat `ContentItem` linked to `Value`**, rather than a value → category tree. One hadith often serves several values.
2. **Retrieval: structured RAG.** The `on_user_turn_completed` hook injects verified items with no extra LLM round trip, and tools remain for explicit requests. pgvector is a stretch goal, only if the eval shows misses.
3. **No source, no answer.** Scripture is never generated. Verses are played as recitation audio, not synthesised with TTS.
4. **Sources.** Quranpedia or KFGQPC for the Quran, with Saheeh International for the English translation. Bukhari and Muslim, with grades from dorar.net, for hadith. dorar.net blocks cloud IPs, so we seed from a laptop.
5. **TTS.** ElevenLabs via `livekit-plugins-elevenlabs==1.5.1`, pinned to the current agents version. There is no automatic fallback: if ElevenLabs cannot be used the session fails with a clear error. xAI stays available only as a manual rollback an operator turns on with `TTS_PROVIDER=xai`.
6. **Tools.** We skip headroom because it duplicates the brain and adds a proxy as a point of failure. ponytail runs team-wide at the `lite` level. Codex users add `codex-plugin-cc`.
