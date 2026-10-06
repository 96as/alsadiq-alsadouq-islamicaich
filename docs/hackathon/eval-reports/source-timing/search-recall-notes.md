## What changed, and what it bought

The model's own arguments are cached in `search-recall-args.json` (one gpt-5.4-mini call per phrasing, real
instructions and tool schema, effort `none`, `tool_choice` forced to `search_bank`), so every row below runs the same
arguments through a different search. Re-run: `python manage.py search_recall --settings=config.settings_sqlite_test --no-llm
--baseline ../docs/hackathon/eval-reports/source-timing/search-recall-before.json --notes ../docs/hackathon/eval-reports/source-timing/search-recall-notes.md`
(`--refresh-args` asks the model again).

| step (cumulative) | (a) not found | (a) right value | (b) not found | (b) right value |
|---|---|---|---|---|
| before: the search as it was | 45.8% | 46.6% | 17.6% | 56.6% |
| 1. topic filter before the top-3 cut, 2. loose value names, 3. related-item fallback | 31.3% | 61.3% | 3.2% | 70.8% |
| 4. named values interleaved; items both signals point to rank first | 31.3% | 61.3% | 3.2% | 72.1% |
| 5. 458 child words in `retrieval_synonyms` (data) | 4.2% | 90.8% | 0.0% | 83.7% |

1. **Topic filter before the top-3 cut** (`retrieval.match_values(types=...)`). The keyword match used to keep its three
   best items and only then drop the wrong types, so "is there a hadith about X?" came back empty whenever the best three
   were verses (18 of the 54 topic-filter misses in (b)).
2. **Loose value names** (`bank_search._value_slugs`). A name matches a value by slug, English or Arabic name, else by one of
   its keywords, with `text_match` forms: case, diacritics, ال/و/ب clitics, singular/plural. One value per name, the model's
   order, at most two. Before: only an exact slug or name, so "kindness", "honest", «الصدق» with a clitic, "truthfulness" matched nothing
   (81 of the 165 (b) misses were calls whose value names matched nothing).
3. **Related-item fallback.** If the topic leaves nothing and the same value(s) have a verse or a hadith of the other kind, up
   to 2 come back with the header `NO <verse|hadith|...> FOUND for this; RELATED items from the same value:` (`Results.related`).
   The lead's case, "is there a verse about visiting the sick?", has no verse in the bank: it now offers the hadith.
4. **Ranking.** The named values' items are interleaved (value 1's best, value 2's best, ...); items the question and a named
   value both point to come first. (Counting the question's matches double was tried: +0.8 on this set, -1.3 on the held-out
   set, dropped.)
5. **Data.** Child words and inflections that matched nothing ("cheated", "forgiving", "showing off", "التفاخر", «جارتنا», ...)
   appended to `turn_rules.json` `retrieval_synonyms` by a script that keeps the file's layout (the diff only adds words;
   every existing word is still there, in place). Words only, no phrase rules. Generic words and person words were left out
   on purpose ("friend", "ill" which "I'll" normalises to, "teacher", ...).
6. **Spacing hint** (no recall effect). The result header carries `Last card shown: N turns ago.` or `No card shown yet this
   session.` (`TurnGuardMixin._turn_no`, counted in `_prepare`; `_last_card_turn`, set when `_cite` publishes a card; a re-cited
   card is not a new card). A not-found result has no hint.

Tried and dropped: letting person and role words ("friend", "mom") count without a value cue inside `search_bank` lifted (a) but
dropped (b) from 70.8% to 69.0%: "friend" pulled the brotherhood verses in front of the right value.

## The data gain is partly in-sample: the held-out set

The 458 words were chosen from the misses of the 380 phrasings, so (a) 90.8% overstates. `search_recall_heldout.yaml` has 76 new
phrasings (2 per value), written after the words were chosen; the model arguments for them are in `heldout/`.

| held-out, 76 phrasings | (a) not found | (a) right value | (b) not found | (b) right value |
|---|---|---|---|---|
| before: old search, old data | 46.1% | 40.8% | 17.1% | 52.6% |
| new search, old data | 36.8% | 50.0% | 1.3% | 75.0% |
| new search, new data | 25.0% | 60.5% | 0.0% | 77.6% |

The search fixes carry most of (b) (52.6% to 75.0%); the new words add about 10 points to (a) and 2.6 to (b) out of sample.
The fair numbers are the held-out ones: about 60% (a) and 78% (b) right value, with nothing empty in (b).

## What still misses, and why

(b), final run: 41 `topic_filter` (the model sent `word_meaning` 34 times and `worship` 7 times for "what does Islam say about X?"
and situations, and the bank holds terms or fiqh there, not the value's verses), 10 `other_value` (the model named a different
value and the question has no keyword of the right one), 9 `ranked_out` (a verse of another value, which sorts before a hadith,
took the top 3), 2 `bank_gap` (visiting-the-sick has 3 hadith and no verse; the model had named `mercy`, so mercy verses came
back instead of the hadith).

Values under 80% right in (b): visiting-the-sick 20%, table-manners 50%, honouring-parents 60%, remembering-allah 60%,
avoiding-backbiting 60%, sincerity 60%, family-ties 70%, spreading-salam 70%, not-wasting 70%. Apart from visiting-the-sick
(the bank gap above, plus verses of other values sorting before its hadith), nearly all of these are the same cause: the model's
topic. table-manners, honouring-parents, avoiding-backbiting, spreading-salam and not-wasting get `word_meaning` for "what does
Islam say about X?"; remembering-allah and sincerity get `worship` ("how can I remember Allah", "I only pray when my parents
are watching"). The search then looks only for terms or fiqh, and the value's verses and hadith are not what it was asked for.

## Not applied: a model-side fix (the tool description is the design lead's call)

The model does not know the 38 value names (the tool says "Up to two value names") and picks `word_meaning` for "what does Islam say about X?".
Re-asking the model for all 380 phrasings with a changed `search_bank` description, same search code:

| tool description | (b) not found | (b) right value | (b) misses |
|---|---|---|---|
| as now | 0.0% | 83.7% | topic_filter 41, other_value 10, ranked_out 9, bank_gap 2 |
| + the 38 value slugs listed under `values` | 0.0% | 86.3% | topic_filter 39, ranked_out 9, other_value 3, bank_gap 1 |
| + the slugs, and a `topic` line: `values` for manners and character and "what does Islam say about X", `word_meaning` only for what one Islamic word means | 0.0% | 91.6% | ranked_out 15, topic_filter 13, other_value 4 |

Not applied: it changes what the model sees and was not run against worship, creed or fiqh questions, where "what does Islam say
about X" must not be routed to `values` (verses and hadith only). The slug list alone is the low-risk part. The experiment's args are
not kept; to repeat it, edit the `Args:` block of `search_bank` and run with `--refresh-args --out <scratch dir>`.
