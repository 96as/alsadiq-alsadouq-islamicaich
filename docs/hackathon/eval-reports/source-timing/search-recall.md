# Search recall report (task 13)

Run 2026-10-06 13:17 UTC on `c8ab33be`, 380 child phrasings (38 values x 10), agent model `gpt-5.4-mini`, reasoning effort `none`. Children's questions only: no scripture anywhere.

(a) raw: the child's words, topic guessed from the shape, no value names. (b) real: gpt-5.4-mini with the agent's real instructions and tool schema, forced to call `search_bank`; its arguments go to the search. A miss means no returned item is linked to the value the phrasing was written for.

## Overall

| mode | not found | no verse/hadith as asked | right value | before: not found | before: right value |
|---|---|---|---|---|---|
| (a) raw | 6.8% | 7.4% | 86.6% | 45.8% | 46.6% |
| (b) real | 0.3% | 1.3% | 80.3% | 17.6% | 56.6% |

"No verse/hadith as asked" counts a result that holds only RELATED items from the same value (the related-item fallback) as a miss of what was asked; "not found" counts only an empty result.

### (a) raw: by language and shape

| group | n | not found | right value |
|---|---|---|---|
| en | 190 | 6.3% | 88.4% |
| ar | 190 | 7.4% | 84.7% |
| verse | 76 | 0.0% | 100.0% |
| hadith | 76 | 2.6% | 97.4% |
| say | 76 | 5.3% | 90.8% |
| sit | 152 | 13.2% | 72.4% |

### (a) raw: miss classes

| class | count | meaning |
|---|---|---|
| no_keyword | 50 | no keyword matched: nothing of this value was a candidate |
| topic_filter | 1 | the topic filter emptied the value's items |

### (b) real: by language and shape

| group | n | not found | right value |
|---|---|---|---|
| en | 190 | 0.0% | 81.0% |
| ar | 190 | 0.5% | 79.5% |
| verse | 76 | 0.0% | 97.4% |
| hadith | 76 | 0.0% | 100.0% |
| say | 76 | 0.0% | 65.8% |
| sit | 152 | 0.7% | 69.1% |

### (b) real: miss classes

| class | count | meaning |
|---|---|---|
| topic_filter | 42 | the topic filter emptied the value's items |
| other_value | 22 | the model named a different value (and the question matched nothing of this one) |
| ranked_out | 9 | the value's items were candidates but other items filled the top 3 |
| bank_gap | 2 | true bank gap: the value has no item of the kind asked for |

## Per value, (b) real

| value | n | not found | right value | before: not found | before: right value |
|---|---|---|---|---|---|
| prayer | 10 | 0.0% | 100.0% | 10.0% | 80.0% |
| honesty | 10 | 0.0% | 90.0% | 0.0% | 90.0% |
| trustworthiness | 10 | 0.0% | 90.0% | 0.0% | 60.0% |
| honouring-parents | 10 | 0.0% | 60.0% | 50.0% | 20.0% |
| mercy | 10 | 0.0% | 90.0% | 10.0% | 70.0% |
| patience | 10 | 0.0% | 100.0% | 0.0% | 90.0% |
| gratitude | 10 | 0.0% | 80.0% | 0.0% | 80.0% |
| cooperation | 10 | 0.0% | 90.0% | 0.0% | 80.0% |
| kindness-to-animals | 10 | 0.0% | 70.0% | 10.0% | 70.0% |
| cleanliness | 10 | 0.0% | 100.0% | 10.0% | 70.0% |
| modesty | 10 | 0.0% | 80.0% | 40.0% | 50.0% |
| good-character | 10 | 0.0% | 90.0% | 10.0% | 60.0% |
| good-neighbour | 10 | 0.0% | 90.0% | 10.0% | 90.0% |
| seeking-knowledge | 10 | 0.0% | 80.0% | 20.0% | 50.0% |
| humility | 10 | 0.0% | 90.0% | 10.0% | 70.0% |
| justice | 10 | 0.0% | 100.0% | 10.0% | 90.0% |
| keeping-promises | 10 | 0.0% | 80.0% | 0.0% | 60.0% |
| generosity | 10 | 0.0% | 80.0% | 10.0% | 80.0% |
| forgiveness | 10 | 0.0% | 90.0% | 10.0% | 70.0% |
| kind-words | 10 | 0.0% | 100.0% | 10.0% | 60.0% |
| charity | 10 | 0.0% | 100.0% | 0.0% | 100.0% |
| respecting-elders | 10 | 0.0% | 80.0% | 80.0% | 20.0% |
| caring-for-orphans | 10 | 0.0% | 50.0% | 10.0% | 20.0% |
| brotherhood | 10 | 0.0% | 90.0% | 20.0% | 70.0% |
| controlling-anger | 10 | 0.0% | 100.0% | 0.0% | 80.0% |
| remembering-allah | 10 | 0.0% | 60.0% | 40.0% | 20.0% |
| trust-in-allah | 10 | 0.0% | 100.0% | 50.0% | 40.0% |
| visiting-the-sick | 10 | 0.0% | 20.0% | 10.0% | 20.0% |
| spreading-salam | 10 | 0.0% | 60.0% | 70.0% | 10.0% |
| table-manners | 10 | 10.0% | 40.0% | 10.0% | 30.0% |
| helping-others | 10 | 0.0% | 100.0% | 40.0% | 50.0% |
| avoiding-backbiting | 10 | 0.0% | 60.0% | 20.0% | 20.0% |
| courage | 10 | 0.0% | 70.0% | 10.0% | 50.0% |
| not-wasting | 10 | 0.0% | 70.0% | 10.0% | 20.0% |
| family-ties | 10 | 0.0% | 60.0% | 10.0% | 70.0% |
| love-of-the-prophet | 10 | 0.0% | 90.0% | 50.0% | 40.0% |
| sincerity | 10 | 0.0% | 60.0% | 20.0% | 50.0% |
| contentment | 10 | 0.0% | 90.0% | 0.0% | 50.0% |

## Top 20 misses, (b) real

| # | value | lang | shape | child said | model's args | returned | class |
|---|---|---|---|---|---|---|---|
| 1 | table-manners | ar | sit | بدأت آكل قبل الكل ونسيت أقول بسم الله، هذا غلط؟ | topic=word_meaning; values=[]; question=بدأت آكل قبل الكل ونسيت أقول بسم الله، هذا غلط؟ | 0 | topic_filter |
| 2 | avoiding-backbiting | ar | say | شو يقول الإسلام عن الحكي عن الناس من ورا ظهرهم؟ | topic=word_meaning; values=['honesty', 'kindness']; question=شو يقول الإسلام عن الحكي عن الناس من ورا ظهرهم؟ | 2 | topic_filter |
| 3 | avoiding-backbiting | ar | sit | حكيت لصاحباتي شي سيء عن بنت وهي مو موجودة، هذي غيبة؟ | topic=word_meaning; values=['honesty', 'kindness']; question=حكيت لصاحباتي شي سيء عن بنت وهي مو موجودة، هذي غيبة؟ | 1 | topic_filter |
| 4 | avoiding-backbiting | en | say | what does Islam say about talking about people behind their back? | topic=word_meaning; values=['honesty', 'kindness']; question=what does Islam say about talking about people behind their back? | 2 | topic_filter |
| 5 | avoiding-backbiting | en | sit | I told my friends something bad about a girl when she was not there, is that gheebah? | topic=word_meaning; values=['honesty', 'kindness']; question=I told my friends something bad about a girl when she was not there, is that gheebah? | 1 | topic_filter |
| 6 | brotherhood | ar | sit | جا ولد مسلم جديد بالمدرسة وما عنده أصحاب، كيف أساعده؟ | topic=values; values=['kindness', 'welcoming new student']; question=جا ولد مسلم جديد بالمدرسة وما عنده أصحاب، كيف أساعده؟ | 3 | ranked_out |
| 7 | caring-for-orphans | ar | sit | في ولد بصفي مات أبوه، كيف أكون طيب معه؟ | topic=values; values=['kindness', 'mercy']; question=كيف أكون طيبًا مع ولد مات أبوه؟ | 3 | other_value |
| 8 | caring-for-orphans | ar | sit | أبي أساعد الأطفال اللي ما عندهم ماما وبابا، شو أسوي؟ | topic=values; values=['رحمة', 'إحسان']; question=أبي أساعد الأطفال اللي ما عندهم ماما وبابا، شو أسوي؟ | 3 | other_value |
| 9 | caring-for-orphans | en | say | what does Islam say about kids who have no parents? | topic=word_meaning; values=['mercy', 'care']; question=what does Islam say about kids who have no parents? | 1 | topic_filter |
| 10 | caring-for-orphans | en | sit | there is a boy in my class whose dad died, how can I be nice to him? | topic=values; values=['kindness', 'mercy']; question=there is a boy in my class whose dad died, how can I be nice to him? | 3 | other_value |
| 11 | caring-for-orphans | en | sit | I want to help kids who have no mom and dad, what can I do? | topic=values; values=['kindness', 'mercy']; question=I want to help kids who have no mom and dad, what can I do? | 3 | other_value |
| 12 | contentment | ar | sit | كل أصحابي عندهم جوال جديد وأنا أبي واحد، شو أسوي؟ | topic=values; values=['الصبر', 'القناعة']; question=كل أصحابي عندهم جوال جديد وأنا أبي واحد، شو أسوي؟ | 3 | ranked_out |
| 13 | cooperation | ar | say | شو يقول الإسلام عن العمل مع بعض؟ | topic=word_meaning; values=['kindness', 'cooperation']; question=شو يقول الإسلام عن العمل مع بعض؟ | 1 | topic_filter |
| 14 | courage | ar | sit | أخاف من الظلام، هذا سيء للمسلم؟ | topic=word_meaning; values=['رحمة', 'صبر']; question=أخاف من الظلام، هذا سيء للمسلم؟ | 1 | other_value |
| 15 | courage | ar | sit | ولد يتنمر على صاحبي وأنا أخاف أوقفه، شو أسوي؟ | topic=values; values=['الصدق', 'الرحمة']; question=ولد يتنمر على صاحبي وأنا أخاف أوقفه، شو أسوي؟ | 3 | other_value |
| 16 | courage | en | sit | I am scared of the dark, is that bad for a Muslim? | topic=word_meaning; values=['patience', 'trust in Allah']; question=I am scared of the dark, is that bad for a Muslim? | 2 | other_value |
| 17 | family-ties | ar | say | شو يقول الإسلام عن زيارة عماتي وخوالي؟ | topic=word_meaning; values=['صلة الرحم', 'الزيارة']; question=شو يقول الإسلام عن زيارة عماتي وخوالي؟ | 1 | topic_filter |
| 18 | family-ties | ar | sit | عمي وبابا ما يحكون مع بعض، شو يقول الإسلام؟ | topic=values; values=['صلة الرحم', 'الإصلاح بين الناس']; question=عمي وبابا ما يحكون مع بعض، شو يقول الإسلام؟ | 3 | ranked_out |
| 19 | family-ties | en | sit | I do not want to go to my cousins' house, is that bad? | topic=values; values=['respect', 'patience']; question=I do not want to go to my cousins' house, is that bad? | 3 | other_value |
| 20 | family-ties | en | sit | my uncle and my dad are not talking to each other, what does Islam say? | topic=values; values=['keeping ties of kinship', 'forgiveness']; question=my uncle and my dad are not talking to each other, what does Islam say? | 3 | other_value |

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
