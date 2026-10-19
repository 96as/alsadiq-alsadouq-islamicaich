# Eval reports: before and after, 5 Oct 2026

Measured on 5 Oct 2026 with the 09 eval runner (`docs/hackathon/handoffs/09-eval-runner.md`). The same question set was put to two builds, scored the same way, one run each.

- **BEFORE:** `origin/hk/01-knowledge-bank` at `4fccb39`, as the lead left it, plus the eval-only files from `hk/product-web` (the runner is not on 01). The eval files are identical on both sides; the agent code is the only thing that differs (agent-code fingerprint `75ea4513992c` before, `dbd03a14dfaf` after).
- **AFTER:** `hk/product-web` at `dba765e` (everything merged).
- **Agent:** `gpt-5.4-mini` (resolved `gpt-5.4-mini-2026-03-17`), reasoning effort `none`, which is what production's `auto` resolves to. **Judge:** `gpt-6-luna`, temperature 0. Text channel only.
- **Question set:** the whole held-out split (50 runs) plus a seeded sample of the dev split (110 of 136 runs, seed 1). The sample is planned round-robin over categories and does not depend on the code under test, so both sides got the same 160 runs. Case, rubric, eval-code and bank fingerprints match on all four live runs (`c2e9898ae84b`, `fc52b237aca5`, `943a21876eea`, `2baef1c358d2`, 74 bank items).
- **Budget:** 624 counted calls of the 700 cap (before 310, after 314; agent calls plus judge calls). No API errors, no rate-limit retries.

## Headline

Strict pass rate = every policy check, code check, judge tag and the rubric verdict pass. Counted over scored runs (pass plus fail). "Content gap" runs (the served items are not in the bank) are counted separately and are in neither rate: 17 on each side. 95% intervals are Wilson intervals for each side.

| Set | Before, strict | After, strict | Paired change (95% bootstrap) |
|---|---|---|---|
| Held-out (never used to tune) | 10/40 = 25% (14 to 40) | 18/41 = 44% (30 to 59) | +20.5 points (+5.1 to +35.9); fixed 10, regressed 2; exact McNemar p = 0.039 |
| Dev sample | 44/103 = 43% (34 to 52) | 69/102 = 68% (58 to 76) | +24.5 points (+13.7 to +35.3); fixed 32, regressed 7 |
| Both, 160 runs | 54/143 = 38% (30 to 46) | 87/143 = 61% (53 to 68) | +23.4 points (+14.2 to +32.6); fixed 42, regressed 9 |

The held-out row is the headline. The dev cases are the ones the guard and prompts may be tuned against (eval README, held-out rules), so the dev and pooled rows are likely to be kind to AFTER.

"Gates" rate (same as strict, but ignoring a failure whose only failing check is the judge's rubric verdict) is a triage view and is not a quality claim: held-out 52% to 71%, dev 61% to 83%, pooled 59% (51 to 66) to 80% (72 to 85).

Policy-only dry run (no model calls: mode, level, flags and items checked against the case file), all 186 case-runs, gaps excluded: before 137/158 = 87% (81 to 91), after 153/158 = 97% (93 to 99). On the dev split alone: 109/122 = 89% to 122/122 = 100%. This checks routing rules only, not what the model says.

## Per category (both splits pooled, 160 runs; strict / gates)

| Category | Runs | Before strict | Before gates | After strict | After gates |
|---|---|---|---|---|---|
| ai-disclosure | 14 | 57% | 71% | 79% | 100% |
| everyday-chat | 8 | 25% | 62% | 75% | 75% |
| grounding | 21 | 52% | 57% | 43% | 57% |
| hostile | 3 | 0% | 0% | 67% | 67% |
| invented-hadith | 10 | 70% | 100% | 70% | 90% |
| level-coverage | 15 | 67% | 75% | 67% | 75% |
| misquote | 2 | 0% | 50% | 50% | 100% |
| out-of-bank | 2 | 50% | 50% | 100% | 100% |
| personal-case | 13 | 50% | 58% | 83% | 92% |
| safety | 25 | 12% | 56% | 72% | 100% |
| safety-negative | 18 | 28% | 50% | 67% | 89% |
| story-request | 5 | 50% | 100% | 0% | 50% |
| test-question | 22 | 17% | 33% | 15% | 46% |
| translation | 2 | 0% | 0% | 0% | 0% |
| all | 160 | 38% | 59% | 61% | 80% |

Rates use scored runs in each category; several categories have fewer than 10 runs, so single categories are anecdotes, not rates. Per-split tables, the failed-check counts and the case ids that were fixed or regressed are in `summary.json` and `tools/analyze.py`.

## Where the gain is, and where it is not

- Gains are in safety (12% to 72%), safety-negative, personal-case, everyday-chat and ai-disclosure: the policy routing and the safety rules now fire. Failures of the code checks on routing (`policy:mode`, `policy:flag_safety_concern`, `referral`, `overreact`) fell from 43 to 10 across the 160 runs.
- **No gain, or worse:** `test-question` (17% to 15%), `translation` (0%, 2 runs), `level-coverage` (unchanged), `story-request` (50% to 0%, 2 scored runs), and `grounding` (52% to 43%, 21 runs; within noise at this size, but the direction is the wrong way).
- **`scripture_without_source` went up, 10 to 21 failures.** An offline check of the AFTER replies (no model calls, `tools/verse_numbers.py`) found that of 18 English replies that say a verse number in words, 10 match a verse the bank served and 8 do not. In three of them the number said is the surah number (Al-Ahzab, "thirty-three"), which is the mistake the clause was written to prevent. The BEFORE replies never named a verse number, so there was nothing to get wrong. The cause was the wording of the spoken-verse clause added in `7665993` ("say only the verse number"). **Fixed and re-measured in round 3:** the clause now says the spoken reply never says a chapter, surah or verse number (the card carries the reference). On the 45 affected cases (all 18 English cases that named a number, the 21 grounding cases, the Arabic verse-served cases and 4 other `scripture_without_source` cases, one run each) 0 of 45 replies said any chapter, surah or verse number, and a repeat of the 10 English grounding cases gave 0 of 10, against 8 wrong of 18 before (`handoffs/product-web.md` section 17.1). The tables in this report are the first run and are not rewritten; the judge-tagged `scripture_without_source` count in the re-run (12 of 45) is the judge's reading of added explanations, not a wrong reference.
- BEFORE replied with bank verse text in one case (`grounding-honesty-en`); AFTER in none (checked with the word-run scan below).

## Latency and size

Latency here is the agent's time inside the API call for one text turn, not first audio (that is task 08). Median 1.02 s before and 1.03 s after; p90 1.70 s before and 1.41 s after; max 3.17 s before and 2.61 s after. Unchanged within noise. The prompt is about 11% larger (mean 5,810 to 6,434 tokens); completions are 101 and 107 tokens.

## Caveats, in plain words

1. **One run per side.** The agent is sampled (the judge is not), so the same build would score a little differently on a second run. No 3-run spread was measured; the budget did not allow it. The intervals above are sampling intervals over cases, not run-to-run spread.
2. **Held-out is 50 runs, 41 scored after gaps.** The held-out interval is wide (+5 to +36 points); the direction is clear, the size is not.
3. **BEFORE is the lead's 01 branch, not the original capstone agent.** It already had the bank. The gain is therefore integration work on top of the bank, not bank versus no bank. A true capstone baseline was not run.
4. **The cases and the rubric were written by the team**, and the judge is a model. Nobody outside the team has checked them. Strict rate counts the judge's verdict; treat the gates rate as triage only.
5. **Text channel only.** The voice channel, speech-to-text and text-to-speech were not measured.
6. **Not measured in this eval:** hadith rules against a real hadith bank (the bank has no hadith, so this only tests refusal of invented ones), live latency to first audio (measured separately in `../latency/LOAD-REHEARSAL.md`), 3-run repeatability.
7. **Content gaps** (17 per side) are excluded from every rate.

## Files

Reports (HTML, one per run; open in a browser). Arabic diacritics were removed from the replies and any reply text that reproduced a bank verse was replaced by `[source text removed]`; each file was re-scanned afterwards with 0 hits.

| File | What |
|---|---|
| `before-live-heldout.html`, `after-live-heldout.html` | live, held-out split, 50 runs each |
| `before-live-dev.html`, `after-live-dev.html` | live, dev sample, 110 runs each |
| `before-dry-run-full.html`, `after-dry-run-full.html` | policy-only dry run, all 186 case-runs |
| `before-dry-run-dev.html`, `after-dry-run-dev.html` | policy-only dry run, dev split, 136 case-runs |
| `summary.json` | counts, fixed and regressed case ids (ids only, no reply text) |
| `tools/` | `analyze.py` (aggregation, intervals, paired tests), `scan_scripture.py` (bank word-run scan, 4 Arabic or 5 English words), `verse_numbers.py` (spoken verse numbers vs served verses), `drun.sh` and `run_all.sh` (how the runs were started) |

The scripts were run from a scratch folder outside the repo (`out/<before|after>/` held the raw reports) and have the original paths in them; they are kept as a record of the method.

## How it was run

```
# for each side (the image mounts the worktree's backend at /app and the .env as a file; never printed)
python manage.py run_eval --settings=config.settings_sqlite_test --llm --channel text \
  --reasoning-effort none --tpm 100000 --concurrency 4 \
  --split heldout --sample 50 --seed 0 --max-llm-calls 110     # held-out: all 50
  --split dev     --sample 110 --seed 1 --max-llm-calls 225     # dev sample
# policy-only: the same command with --dry-run instead of --llm, no --sample
```

Environment: image `alsadiq-eval-runner:local`, `LLM_MODEL=gpt-5.4-mini`, `PYTHONUTF8=1`. The raw JSON reports (which contain the full replies) are not committed.

The agent-quality rounds (baseline, call budget, rounds) are in [`agent-quality/`](agent-quality/): `AQ-BASELINE.md`, `AQ-BUDGET.md`, `AQ-ROUNDS.md`.
