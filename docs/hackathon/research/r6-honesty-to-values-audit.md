# R6 — Honesty-only to 38-values audit

Read-only audit, 5 Oct 2026. Branch `hk/01-knowledge-bank` plus the uncommitted `reporting/` + `gamification/` work (decision 8: no honesty grading).

**Name, stated once for the whole doc:** the product is **الصديق الصدوق — Al-Sadiq Al-Sadouq**. *Al-Sadiq* = الصديق, **the friend**; *Al-Sadouq* = الصدوق, **the very truthful / trustworthy**. So the name is "the truthful friend": friendship first, honesty as a trait of the companion, not the only value he teaches. Every "Sadiq" / "Talk with Sadiq" / "As-Sadiq Companion" string below is the friend identity and is **FINE as brand**. Only places that treat honesty/truthfulness as the main or sole *value*, or that mistranslate the name as "the Truthful (one)" / write **الصادق** instead of **الصديق**, are flagged.

Severity key: **BREAKS** (wrong now that `honesty_score` is null) · **MISLEADING** (to parents, children or judges) · **LIMITS** (hard-wires one value or the legacy 6 themes) · **NAME** (name meaning/spelling) · **FINE** (brand or neutral).

## Summary table

| Area | Findings | BREAKS | MISLEADING | LIMITS | NAME |
|---|---|---|---|---|---|
| Voice agent `conversation/agent/` | 8 | 0 | 1 | 5 | 2 |
| Reporting `reporting/` + admin surfaces | 5 | 0 (feeds G1) | 1 | 3 | 1 |
| Gamification `gamification/` + legacy `MoralTheme` | 5 | **1** | 1 | 3 | 0 |
| Eval harness `conversation/eval/` | 1 | 0 | 0 | 1 | 0 |
| Frontend `frontend/src/` | 4 | 0 | 1 | 2 | 0 |
| Mobile `mobile/src/` | 3 | 0 | 1 | 1 | 0 |
| Docs / marketing | 6 | 0 | 2 | 0 | 3 |
| **Total** | **32** | **1** | **7** | **15** | **6** |

Not affected (checked, nothing honesty-specific): `content_safety/`, `authentication/` (brand strings only), `turn_pipeline.py`, `retrieval.py` (indexes all `Value` rows), `turn_rules.json` (`retrieval_synonyms.honesty` is one entry of a per-value map), `entrypoint.py:201` (`available_themes` already comes from `value_index.value_names()`, i.e. all 38 values, not `MoralTheme`), frontend/mobile parent Insights (never read `honesty_score`), `IDEA_DESCRIPTION.md` (says "Islamic values", no honesty-only claim).

---

## A. Voice agent (`backend/conversation/agent/`) — owner: task 03 / voice-agent-dev

| # | File:line | Today | Why honesty-only | Severity | Proposed change |
|---|---|---|---|---|---|
| A1 | `agent_class.py:25-28` `_PERSONA` | "You are Sadiq … whose name means 'The Truthful'. … **Honesty is the trait you value most**" | Mistranslates the name and makes honesty the top value in the persona | **MISLEADING + NAME** | "You are Sadiq — الصديق, *the friend*; Al-Sadouq, the truthful friend. What moves you most is a child being brave about any good value: telling the truth, saying sorry, sharing, holding back anger, thanking someone." |
| A2 | `agent_class.py:32`, `:42` | "what you care about: honesty, kindness, patience, gratitude…"; "if a child shares kindness or truthfulness you brighten up" | Hand-picked 4-5 values as the persona's interests | LIMITS (minor) | Keep as examples but add "…and every value in your trusted library" so the TRUSTED LIBRARY list (`:230-236`) is the authority. |
| A3 | `agent_class.py:163` base prompt | "help them develop **honesty**, good character, emotional intelligence…" | Honesty is the first named purpose | LIMITS | "help them understand and practise Islamic values (your library lists them), good character, emotional intelligence…" |
| A4 | `agent_class.py:114`, `:123` `_GAMIFICATION_DIRECTIVES` | `quality='excellent'` = "a brave **honesty** moment (admitting a mistake, telling a hard truth)"; bribe example "tell me the truth and you get points" | The only named "+10" example is honesty, so points skew to one value | LIMITS | "a brave moment practising any value: admitting a mistake, apologising, sharing, controlling anger, keeping a promise" |
| A5 | `agent_class.py:348`, `:355` `record_engagement` docstring | "'excellent' for brave honesty"; example reason "Told the truth about a mistake" | Tool schema the LLM reads every turn | LIMITS | "'excellent' for a brave moment with any value"; example "Apologised to his sister" |
| A6 | `agent_class.py:52` `_AI_DISCLOSURE` | Arabic: "أنا **صادق**، صديق كمبيوتر…" | Short Arabic name written صادق (truthful), not from الصديق | NAME (lead decision D2) | Decide the Arabic nickname once (see D2), then fix here. |
| A7 | `entrypoint.py:80` `_FIRST_MEETING_AI_LINE["ar"]` | "قل إنك **صادق**، صديق كمبيوتر" | Same as A6 | NAME (D2) | Same as A6. |
| A8 | `gamification/services.py:34` `ENGAGEMENT_DELTAS` comment | `'excellent': 10,  # … honesty moment` | Comment only | FINE (cosmetic) | "a brave values moment". |

FINE in this area: `agent_class.py:167` "Truthfulness rule: never lie" (about the agent, not the child); `:80`, `:180-181`, `:185`, `turn_policy.py:310` list honesty among example manners; `:34` dislikes (lying, backbiting, bragging, wasting food, cruelty to animals) map to real Value slugs (`honesty`, `avoiding-backbiting`, `humility`, `not-wasting`, `kindness-to-animals`).

## B. Reporting (`backend/reporting/`, `superadmin/`) — owner: backend reporting agent

| # | File:line | Today | Why | Severity | Proposed change |
|---|---|---|---|---|---|
| B1 | `prompts.py:177` quest JSON `"moral_theme": "short theme label e.g. Honesty, Patience, Gratitude, Kindness"`; `:221`, `:225`; `QUEST_GENERATION_USER_TEMPLATE` (`:245-255`) has **no Value list** | `services.py:448-454` looks the free label up in **`MoralTheme`** (legacy 6: Honesty, Truthfulness, Courage, Kindness, Responsibility, Patience). `seed_islamic_knowledge` is not run by `docker-compose.yml:41` or `scripts/init-prod.sh`, so on a fresh DB the table is **empty** and every AI quest gets `moral_theme=None`. | **LIMITS** (and the direct cause of G1) | Pass the same `values_list` the session-report prompt gets (`services.py:293`); ask for `"value_slug"` (exactly one of the list, or ""); resolve with `Value.objects.filter(slug=…)`. **Bridge (no migration):** `MoralTheme.objects.get_or_create(name=value.name_en)` and set the FK, so `moral_theme_name` and badge counting keep working for all 38 values. **Proper:** G3. |
| B2 | `views.py:36-80` `ChildInsightsView`; `services.py:492-507` `_build_reports_json` | Parents get `summary`, `suggested_topics`, badges by category; `values_to_revisit` goes only to the weekly LLM as raw slugs ("honouring-parents") | No "values discussed this week" exists; the only value-flavoured thing a parent sees is the honesty badge category | LIMITS | Add `values_this_week: [{slug, name_en, name_ar, count}]` computed **without an LLM** from `SessionReport.sources_used[*].value_names` (already snapshotted, `services.py:690-691`) plus `raw_llm_output.values_to_revisit`, over the week's reports. Give `WEEKLY_SUMMARY_SYSTEM` the slug→name map so topics read "Honouring parents", not a slug. |
| B3 | `services.py:645-646`, `:660-661` `QUESTIONS_TITLE["ar"]`, `QUESTION_DEFAULT_LABEL["ar"]` | "أسئلة طلب منك **صادق** مناقشتها مع طفلك", "سؤال أحاله إليك صادق" | Parent-facing Arabic uses صادق as the name | NAME (D2) | Follow D2. |
| B4 | `models.py:24-26` `honesty_score` null column; `admin.py:11-14`; `superadmin/serializers.py:178-182`; `superadmin/templates/superadmin/dashboard.html:511-512`; `superadmin/tests.py` | Column kept (no migration), shown read-only in Django admin and the superadmin table | Admin screens show a permanently-null "honesty_score" column; a teammate or judge browsing admin reads it as a feature | MISLEADING (internal, low) | Drop it from `fieldsets`, `fields`, `columns` (keep the model field until task 01 removes it in a migration). Show `raw_llm_output.values_to_revisit` instead. |
| B5 | `prompts.py:56`, `:108`, `:279` | "Do NOT assess the child's truthfulness"; "Never grade or label the child's honesty or character" | These are the new decision-8 guard rails; they single out honesty only because that was the old behaviour | FINE | Optional: "…honesty, piety or character". |

FINE: `prompts.py:201` anti-repetition example ("tell the truth / admit a mistake"), `tests.py:746-811` and `test_values_to_revisit.py` (tests use Honesty as a sample value and assert no grading; keep).

## G. Gamification (`backend/gamification/`) and the legacy `MoralTheme` — owner: backend gamification agent, migrations via task 01

| # | File:line | Today | Why | Severity | Proposed change |
|---|---|---|---|---|---|
| **G1** | `models.py:32` `('honesty','Honesty')` badge category; `:43` `('honesty_sessions','N fully honest sessions')`; `migrations/0004:23-26` badges **Truthful Heart** ("your first fully honest conversation"), **Honest Soul** ("conversations where you were open and truthful"), **As-Sadiq Companion** ("Fifteen honest conversations — truthfulness is your habit now"); `services.py:42-44, 175-183` (uncommitted) counts completed quests whose `moral_theme.name` ∈ {Honesty, Truthfulness, الصدق} | Honesty is the **only** value with its own badge track. Copy still tells the child/parent that conversations were judged "fully honest" (decision 8 says never graded). With B1 the theme match fails for every LLM label outside the legacy 6 and on an unseeded DB, so the count stays 0 → the three badges are **unreachable** and the child sees three locked badges whose unlock hint ("Have your first fully honest conversation") can never be met. | **BREAKS + MISLEADING + LIMITS** | Replace the trio with a value-agnostic track: category `values`, requirement `values_practised` = number of **distinct Values** across the child's completed quests (via Quest→Value, see G3), thresholds 1 / 5 / 15 → e.g. "First Value", "Five Values", "Garden of Values" (name per D4). Until G3 lands, compute from `Quest.moral_theme__name` matched to `Value.name_en` (B1 bridge keeps names aligned). **Note:** `choices` edits produce an `AlterField` migration, and `0004` seeds with `update_or_create(name=…)`, so renaming badges needs a data migration (`RunPython`) or a `seed_badges` management command run at deploy. Lead decision D3. The `requirement_type` strings are free text in the DB: the smallest bridge is to keep the `'honesty_sessions'` key, re-label it "N values practised" and swap the three badge rows' name/description/category by data migration only. |
| G2 | `migrations/0004:7` Level 3 **'Honest Helper'** | Level names | One honesty-flavoured level among 8 | FINE (cosmetic) | Rename to "Helpful Heart" in the same data migration as G1. |
| **G3** | `models.py:223-229` `Quest.moral_theme` FK → `session_moral_context.MoralTheme`; `serializers.py:17-31` `moral_theme_name`; `views.py:27,48,171`; `admin.py:76,80`; `superadmin/serializers.py:252-258`, `superadmin/views.py:83-85,156`, `superadmin/urls.py:29` (`moral-themes` CRUD); `dashboard.html:581-586` "Moral Theme ID" | Quests are themed by the legacy 6-theme table, not by `Value` | LIMITS (legacy 6) | **Bridge (no migration):** B1 mirrors Values into `MoralTheme` by `name_en`; the FK, serializer and admin keep working and show real value names. **Proper (task 01):** add `Quest.value = FK(Value, null=True)`, `RunPython` copying `moral_theme.name` → `Value.name_en` match, expose `value_slug`/`value_name_ar` in `ChildQuestSerializer`, then drop `moral_theme`, `MoralTheme`, `IslamicReference`, `MoralContext` and the `moral-themes` superadmin route (r5 A1 already asked to retire this path). |
| G4 | `session_moral_context/fixtures/islamic_knowledge_base.json`; `management/commands/seed_islamic_knowledge.py` | 6 legacy themes: Honesty (7 refs), Truthfulness (2), Courage (2), Kindness (3), Responsibility (2), Patience (3); not in any deploy script | 9 of 19 refs are honesty; r5 flagged the refs as unverified | LIMITS (legacy 6) | Delete command + fixture once G3 lands; until then remove from docs (`CURRENT_STATE.md:72-73`). |
| G5 | `tests.py:176-197`, `:322` (uncommitted) | Assert "Truthful Heart" from an honesty quest; assert `{'streak','honesty','quest','level'} <= categories` | Pin the honesty track | follows G1 | Rewrite as `values_practised` tests (two quests on two different values → badge at 1 and not at 2nd duplicate value). |

## E. Eval harness — owner: task 09

| # | File:line | Today | Severity | Proposed change |
|---|---|---|---|---|
| E1 | `conversation/eval/test_cases_schema.py:50-53` `GROUNDING_VALUES` | Hard-coded 10 slugs (honesty first) out of 38 | LIMITS | Load slugs from `session_moral_context/content/values.json` at import; add at least one grounding case per value family the demo shows. |

## F. Frontend (`frontend/src/`) — owner: task 05 / frontend-dev

| # | File:line | Today | Severity | Proposed change |
|---|---|---|---|---|
| F1 | `pages/child/BadgesPage.jsx:14` `CATEGORY_META` | `['honesty', 'Honesty badges', 'For brave, truthful conversations']` | MISLEADING (child reads "your conversations are judged truthful") | `['values', 'Values badges', 'For practising values with Sadiq']` — key must match G1's category. |
| F2 | `pages/child/QuestsPage.jsx:66` | "Small steps that build **honesty and heart**." | LIMITS | "Small steps that put good values into practice." |
| F3 | `features/parent/data/badgeImages.js:14` + `public/badges/honesty-seed.png` | Maps badge label "Honesty Seed" to art; no seeded badge has that name (seed names are Truthful Heart / Honest Soul / As-Sadiq Companion) | FINE (dead code) | Delete the entry/PNG or re-point the art to the new "First Value" badge. |
| F4 | `pages/parent/InsightsPage.jsx:210, 300-303` | Shows badges by name, `suggested_topics`, level; no values view | LIMITS | Add a "Values this week" chip row from B2's `values_this_week` (name_en/name_ar by locale). |

`QuestListCard.jsx:102-103` already renders `themeLabel` (`moral_theme_name`) generically — it will show all 38 values once B1 lands. No Arabic UI strings exist in the web app (nothing to fix for D2).

## M. Mobile (`mobile/src/`) — owner: mobile-dev

| # | File:line | Today | Severity | Proposed change |
|---|---|---|---|---|
| M1 | `features/child/badges/BadgeTile.jsx:11` `honesty: {icon:'heart', tone:'danger'}`; `BadgesScreen.jsx:16` `CATEGORY_ORDER` includes `'honesty'`; `i18n/locales/en.json:130` "Honesty", `:138` "For brave, truthful talks"; `features/parent/insights/InsightsScreen.jsx:268` reuses `CATEGORY_META` | Same honesty category as F1, on child badges and parent insights | MISLEADING | Rename key to `values`, icon `leaf`/`ribbon`, copy "Values" / "For practising values with Sadiq". |
| M2 | `features/parent/insights/InsightsScreen.jsx:219-230` | `suggested_topics` only; no values view | LIMITS | Same as F4. |
| M3 | `i18n/locales/ar.json` | File is `{}` — every Arabic string falls back to English, including the badge category | side note, not honesty | Out of scope here; flag to mobile-dev. |

`QuestCard.jsx` does not show the quest theme at all (no `moral_theme_name`), so nothing to generalise there; optionally show it once G3 exposes `value_name_ar`.

## D. Docs and marketing (note only)

| # | File:line | Today | Severity | Proposed change |
|---|---|---|---|---|
| D-1 | `README.md:9` | "The initial version (v1) focuses on **Honesty** as the core moral value."; `:14` "(e.g., lying, fear, jealousy)" | **MISLEADING to judges** (first paragraph of the repo) | "…teaches Islamic values from a reviewed knowledge bank of 38 values (honesty, patience, gratitude, honouring parents, …), every verse and hadith traceable to its source." |
| D-2 | `docs/hackathon/IDEA_DESCRIPTION.md` | Says "Islamic values" throughout; never explains the name | FINE | Optional one line for the judges: "Al-Sadiq Al-Sadouq (الصديق الصدوق), *the truthful friend*". |
| D-3 | `docs/enhancements-companion-gamification.md:20` | "whose name means 'The Truthful'; honesty is the trait he loves most" | NAME (stale design doc that A1 was written from) | Correct to الصديق الصدوق = the truthful friend; mark the section superseded. |
| D-4 | `docs/hackathon/CURRENT_STATE.md:17`, `:73`, `:114` | "honesty sessions" badge rule; the 6 legacy themes; "honesty indicators … honesty score (1.0 / 0.5 / 0.0 / null)" | MISLEADING (stale after decision 8) | Replace with `values_to_revisit`, drop the 6-theme paragraph after G3/G4. |
| D-5 | `docs/hackathon/privacy-policy-draft.md:115` "**الصادق** الصدوق تطبيق … رفيق ذكي اسمه «صادق»"; `handoffs/mobile-ai-privacy.md:79,82`, `handoffs/05-cards-ai-privacy.md:248,253` "**الصادق** الصدوق" | Parent-facing legal copy spells the product الصادق | NAME (D2) | Write **الصديق الصدوق** everywhere; nickname per D2. |
| D-6 | `docs/hackathon/tasks/10-demo-submission.md:16` | Demo question is "ليش لازم أكون صادق؟" (honesty) | FINE (a demo pick) | Consider a second beat on another value (e.g. honouring parents or patience) so judges see breadth, and say "38 values" out loud. |

Also NAME-adjacent but FINE: `backend/conversation/eval/cases.yaml:41, 2029, 2046, 2269` and `test_guard_round3.py:505-514` use "يا صادق" as *child* input — children will use whatever nickname the UI shows; update only if D2 changes the nickname.

---

## Recommended change list (priority order)

| P | Change | Files | Owner | Needs |
|---|---|---|---|---|
| **P0** | **G1** Retire the honesty badge trio → `values_practised` track; relabel category; re-seed by data migration or `seed_badges` command | `gamification/models.py`, `services.py`, new data migration or command, `tests.py` | backend gamification | D3 (migration route), D4 (badge names) |
| **P0** | **B1** Quest generation gets the Value list, returns `value_slug`, resolves to `Value`, mirrors into `MoralTheme` (bridge) | `reporting/prompts.py`, `reporting/services.py:381-470`, tests | backend reporting | none (no migration) |
| **P0** | **D-1** README first paragraph | `README.md:9-14` | lead / docs | D1 |
| **P0** | **A1 + A3** Persona: correct name meaning, honesty no longer "the trait you value most", purpose = all values | `agent_class.py:23-46`, `:163` | task 03 voice-agent-dev | D1 |
| P1 | **F1, M1** Badge category copy (web + mobile) in the same PR as G1 | `BadgesPage.jsx:14`, `BadgeTile.jsx:11`, `BadgesScreen.jsx:16`, `en.json:130,138` | frontend 05, mobile | G1 key name |
| P1 | **B2 + F4 + M2** "Values this week" in parent insights, computed from `sources_used` + `values_to_revisit` | `reporting/views.py`, `InsightsPage.jsx`, `InsightsScreen.jsx` | backend reporting, 05, mobile | none |
| P1 | **A4, A5** Points directives and `record_engagement` docstring generalised | `agent_class.py:114-123`, `:348-355` | task 03 | none |
| P1 | **F2** Quests page copy | `QuestsPage.jsx:66` | 05 | none |
| P1 | **A6, A7, B3, D-5** Arabic name spelling | `agent_class.py:52`, `entrypoint.py:80`, `reporting/services.py:645-661`, privacy policy, handoffs | 03 + reporting + docs | **D2 first** |
| P2 | **B4** Hide `honesty_score` in admin/superadmin, show `values_to_revisit` | `reporting/admin.py`, `superadmin/serializers.py`, `dashboard.html` | backend | none |
| P2 | **E1** Eval grounding values from `values.json` | `eval/test_cases_schema.py:50-53` | task 09 | none |
| P2 | **G3 + G4** `Quest.value` FK, drop `MoralTheme` path, delete `seed_islamic_knowledge` + fixture | `gamification/models.py`, `session_moral_context/`, `superadmin/` | task 01 (migration) | D3 |
| P2 | **G2, F3, D-3, D-4, M3** Level name, dead badge art, stale docs, empty `ar.json` | as listed | misc | none |

## Lead decisions needed

| # | Decision | Recommendation |
|---|---|---|
| **D1** | Keep the brand/persona name "Al-Sadiq Al-Sadouq" / "Sadiq"? | **Yes.** It means *the truthful friend* (الصديق الصدوق): friendship is the identity, truthfulness is the companion's own trait. Fits 38 values. Fix the gloss everywhere ("the Truthful" → "the truthful friend"). |
| **D2** | Arabic nickname the companion uses for himself and that UI/parent copy uses: keep **صادق** (current everywhere; a common given name meaning "truthful", echoes الصدوق) or switch to a form of **الصديق** (e.g. "صديقك الصدوق")? | Lead call. If kept, write the full product name as **الصديق الصدوق** (never الصادق) and keep صادق only as the nickname. If switched, A6, A7, B3, D-5, eval cases and the mobile AI-sheet strings all change together. |
| **D3** | Badge/quest generalisation route: (a) data-only migration (`RunPython` re-seed + `AlterField` for the new choices) owned by task 01, (b) `seed_badges` management command run at deploy with no model change (keep `'honesty_sessions'` as an internal key, relabel), or (c) proper `Quest.value` FK migration now | (b) today for the demo, (c) in task 01's next migration. (a) alone still needs the FK to be useful. |
| **D4** | Badge shape: one "values practised" track (count of distinct values) vs one badge per value family | Values practised. `values.json` has no `family` field; per-family badges would need new data and 38-way art. |
| **D5** | Does honesty stay the flagship value in marketing/demo? | Lead the pitch with "the truthful friend who teaches 38 values from traceable sources"; use honesty as the *first* demo beat, not the only one. Change `README.md:9` either way. |
| **D6** | Should `seed_content` (Values) be added to `docker-compose.yml` / `init-prod.sh` next to `seed_admin`? Without it a fresh DB has no `Value` rows, so `values_to_revisit`, retrieval and B1 all come back empty. | Yes (task 01/02), out of this audit's scope but it is the same failure mode as G1. |
