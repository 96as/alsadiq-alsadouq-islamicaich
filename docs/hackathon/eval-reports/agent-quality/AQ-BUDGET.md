# AQ budget ledger (hk/agent-quality)

Hard limit for the whole workflow: 950 counted LLM calls (agent plus judge) across all runs.
Every run is started with `--max-llm-calls`. Add one row per run, with the numbers from the report (`calls: agent A, judge J`).

| # | Date | Who | Purpose | Cap passed | Agent calls | Judge calls | Total | Running total | Left |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 2026-10-05 | baseline engineer | full baseline, 165 text runs, all cases | 360 | 173 | 150 | 323 | 323 | 627 |
| 2 | 2026-10-05 | improvement engineer r1 | dev run after C1-C5 (115 dev cases; 21 hit APIConnectionError, rerun below) | 260 | 118 | 91 | 209 | 532 | 418 |
| 3 | 2026-10-05 | improvement engineer r1 | rerun of the 21 dev cases that hit APIConnectionError in run 2 | 70 | 21 | 21 | 42 | 574 | 376 |
| 4 | 2026-10-05 | improvement engineer r1 | targeted rerun (37 failing + 14 passing) after the second-pass wording commits | 120 | 53 | 48 | 101 | 675 | 275 |
| 5 | 2026-10-05 | improvement engineer r1 | targeted rerun (grounding, everyday, safety-negative, story-request) after the third-pass commit f748c80 | 75 | 33 | 30 | 63 | 738 | 212 |
| 6 | 2026-10-05 | improvement engineer r1 | 5-case grounding recheck after source-first wording | 12 | 5 | 4 | 9 | 747 | 203 |
| 7 | 2026-10-05 | final measurement engineer | HELD-OUT, all 50 cases, final code e37cada (text channel, seed 0) | 110 | 59 | 40 | 99 | 846 | 104 |
| 8 | 2026-10-05 | final measurement engineer | clean DEV sample, 42 of 115 cases, final code e37cada (seed 1, round-robin over categories) | 90 | 42 | 41 | 83 | 929 | 21 |
| 9 | 2026-10-05 | opus reviewer | 3 dev cases after the review fixes ffb008d and fc73526 (probe-wudu-after-dog-ar, probe-violent-movie-scared-en, probe-pillow-fight-ar), effort none | 10 | 3 | 3 | 6 | 935 | 15 |
| 10 | 2026-10-05 | safety classifier builder | 21 new dev cases (aq-classifier-widening), text channel, after commits a684bfe to 9d615e2 | 60 | 21 | 21 | 42 | 977 | over |
| 11 | 2026-10-05 | safety classifier builder | rerun of 7 failing new dev cases after the reason-text wording | 20 | 7 | 7 | 14 | 991 | over |
| 12 | 2026-10-05 | safety classifier builder | rerun of 5 failing new dev cases after the reason-text wording | 12 | 5 | 5 | 10 | 1001 | over |

Rows 10 to 12 were run under the lead's explicit task allowance of 120 counted calls for the safety classifier work (66 used). That allowance sits on top of the original 950 limit, so the running total passes it. No further calls should be made from this ledger.
