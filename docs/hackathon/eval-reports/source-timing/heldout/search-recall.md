# Search recall report (task 13)

Run 2026-10-06 11:56 UTC on `c466f5de`, 76 child phrasings (38 values x 10), agent model `gpt-5.4-mini`, reasoning effort `none`. Children's questions only: no scripture anywhere.

(a) raw: the child's words, topic guessed from the shape, no value names. (b) real: gpt-5.4-mini with the agent's real instructions and tool schema, forced to call `search_bank`; its arguments go to the search. A miss means no returned item is linked to the value the phrasing was written for.

## Overall

| mode | not found | no verse/hadith as asked | right value | before: not found | before: right value |
|---|---|---|---|---|---|
| (a) raw | 25.0% | 25.0% | 60.5% | 46.1% | 40.8% |
| (b) real | 0.0% | 5.3% | 77.6% | 17.1% | 52.6% |

"No verse/hadith as asked" counts a result that holds only RELATED items from the same value (the related-item fallback) as a miss of what was asked; "not found" counts only an empty result.

### (a) raw: by language and shape

| group | n | not found | right value |
|---|---|---|---|
| en | 38 | 31.6% | 47.4% |
| ar | 38 | 18.4% | 73.7% |
| verse | 9 | 22.2% | 77.8% |
| hadith | 14 | 14.3% | 85.7% |
| say | 14 | 28.6% | 71.4% |
| sit | 39 | 28.2% | 43.6% |

### (a) raw: miss classes

| class | count | meaning |
|---|---|---|
| no_keyword | 30 | no keyword matched: nothing of this value was a candidate |

### (b) real: by language and shape

| group | n | not found | right value |
|---|---|---|---|
| en | 38 | 0.0% | 68.4% |
| ar | 38 | 0.0% | 86.8% |
| verse | 9 | 0.0% | 88.9% |
| hadith | 14 | 0.0% | 92.9% |
| say | 14 | 0.0% | 92.9% |
| sit | 39 | 0.0% | 64.1% |

### (b) real: miss classes

| class | count | meaning |
|---|---|---|
| other_value | 8 | the model named a different value (and the question matched nothing of this one) |
| topic_filter | 5 | the topic filter emptied the value's items |
| ranked_out | 4 | the value's items were candidates but other items filled the top 3 |

## Per value, (b) real

| value | n | not found | right value | before: not found | before: right value |
|---|---|---|---|---|---|
| prayer | 2 | 0.0% | 50.0% | 0.0% | 50.0% |
| honesty | 2 | 0.0% | 100.0% | 0.0% | 100.0% |
| trustworthiness | 2 | 0.0% | 50.0% | 0.0% | 50.0% |
| honouring-parents | 2 | 0.0% | 100.0% | 0.0% | 50.0% |
| mercy | 2 | 0.0% | 100.0% | 0.0% | 50.0% |
| patience | 2 | 0.0% | 100.0% | 0.0% | 100.0% |
| gratitude | 2 | 0.0% | 50.0% | 50.0% | 0.0% |
| cooperation | 2 | 0.0% | 100.0% | 0.0% | 100.0% |
| kindness-to-animals | 2 | 0.0% | 50.0% | 0.0% | 50.0% |
| cleanliness | 2 | 0.0% | 100.0% | 50.0% | 50.0% |
| modesty | 2 | 0.0% | 100.0% | 50.0% | 50.0% |
| good-character | 2 | 0.0% | 100.0% | 0.0% | 50.0% |
| good-neighbour | 2 | 0.0% | 100.0% | 0.0% | 100.0% |
| seeking-knowledge | 2 | 0.0% | 100.0% | 50.0% | 50.0% |
| humility | 2 | 0.0% | 100.0% | 0.0% | 50.0% |
| justice | 2 | 0.0% | 50.0% | 0.0% | 100.0% |
| keeping-promises | 2 | 0.0% | 50.0% | 0.0% | 50.0% |
| generosity | 2 | 0.0% | 100.0% | 50.0% | 50.0% |
| forgiveness | 2 | 0.0% | 50.0% | 0.0% | 0.0% |
| kind-words | 2 | 0.0% | 100.0% | 0.0% | 100.0% |
| charity | 2 | 0.0% | 100.0% | 0.0% | 100.0% |
| respecting-elders | 2 | 0.0% | 100.0% | 50.0% | 50.0% |
| caring-for-orphans | 2 | 0.0% | 50.0% | 0.0% | 50.0% |
| brotherhood | 2 | 0.0% | 50.0% | 0.0% | 50.0% |
| controlling-anger | 2 | 0.0% | 100.0% | 0.0% | 100.0% |
| remembering-allah | 2 | 0.0% | 50.0% | 100.0% | 0.0% |
| trust-in-allah | 2 | 0.0% | 50.0% | 50.0% | 0.0% |
| visiting-the-sick | 2 | 0.0% | 0.0% | 0.0% | 0.0% |
| spreading-salam | 2 | 0.0% | 100.0% | 50.0% | 50.0% |
| table-manners | 2 | 0.0% | 50.0% | 0.0% | 50.0% |
| helping-others | 2 | 0.0% | 100.0% | 0.0% | 100.0% |
| avoiding-backbiting | 2 | 0.0% | 50.0% | 50.0% | 0.0% |
| courage | 2 | 0.0% | 100.0% | 0.0% | 50.0% |
| not-wasting | 2 | 0.0% | 100.0% | 50.0% | 50.0% |
| family-ties | 2 | 0.0% | 50.0% | 0.0% | 50.0% |
| love-of-the-prophet | 2 | 0.0% | 100.0% | 50.0% | 0.0% |
| sincerity | 2 | 0.0% | 50.0% | 0.0% | 50.0% |
| contentment | 2 | 0.0% | 100.0% | 0.0% | 50.0% |

## Top 20 misses, (b) real

| # | value | lang | shape | child said | model's args | returned | class |
|---|---|---|---|---|---|---|---|
| 1 | avoiding-backbiting | en | sit | my classmates were speaking badly about our teacher when she was out of the room, what should I do? | topic=values; values=['honesty', 'respect']; question=my classmates were speaking badly about our teacher when she was out of the room, what should I do? | 3 | other_value |
| 2 | brotherhood | en | sit | a boy from another school is being left out and I think we should include him, what does Islam say? | topic=values; values=['kindness', 'inclusion']; question=a boy from another school is being left out and I think we should include him, what does Islam say? | 3 | other_value |
| 3 | caring-for-orphans | en | verse | is there a verse about looking after kids who lost their parents? | topic=quran; values=['kindness', 'mercy']; question=is there a verse about looking after kids who lost their parents? | 3 | other_value |
| 4 | family-ties | en | sit | I have not talked to my grandma's sister for months, should I call her? | topic=values; values=['kindness', 'keeping ties']; question=Should I call my grandma's sister after months without talking? | 3 | other_value |
| 5 | forgiveness | ar | sit | أختي كسرت جوالي وتعتذر، لازم أرضى عنها؟ | topic=values; values=['forgiveness', 'kindness']; question=أختي كسرت جوالي وتعتذر، لازم أرضى عنها؟ | 3 | ranked_out |
| 6 | gratitude | ar | sit | ما عجبني الأكل اليوم وقلت إنه سيء، هذا ما يصير؟ | topic=values; values=['honesty', 'respect']; question=ما عجبني الأكل اليوم وقلت إنه سيء، هذا ما يصير؟ | 3 | ranked_out |
| 7 | justice | en | sit | my brother always gets blamed even when it is not his fault, what does Islam say? | topic=values; values=['justice', 'kindness']; question=my brother always gets blamed even when it is not his fault, what does Islam say? | 3 | ranked_out |
| 8 | keeping-promises | en | sit | I said I would help my friend move his things and then I did not show up, was that wrong? | topic=values; values=['keeping promises', 'honesty']; question=I said I would help my friend move his things and then I did not show up, was that wrong? | 3 | ranked_out |
| 9 | kindness-to-animals | ar | say | شو يقول الإسلام عن الحيوانات الأليفة؟ | topic=word_meaning; values=['kindness']; question=شو يقول الإسلام عن الحيوانات الأليفة؟ | 1 | topic_filter |
| 10 | prayer | en | sit | my dad wakes me up for fajr and I am so sleepy, do I really have to? | topic=worship; values=['patience']; question=my dad wakes me up for fajr and I am so sleepy, do I really have to? | 2 | topic_filter |
| 11 | remembering-allah | ar | sit | أبي أحفظ أذكار الصباح، من وين أبدأ؟ | topic=worship; values=['التعلم', 'المداومة']; question=أبي أحفظ أذكار الصباح، من وين أبدأ؟ | 2 | topic_filter |
| 12 | sincerity | en | sit | I helped someone only because I wanted a reward from my parents, is that okay? | topic=values; values=['honesty', 'kindness']; question=I helped someone only because I wanted a reward from my parents, is that okay? | 3 | topic_filter |
| 13 | table-manners | en | sit | I was talking with food in my mouth at dinner, is that rude? | topic=values; values=['respect', 'good manners']; question=I was talking with food in my mouth at dinner, is that rude? | 3 | other_value |
| 14 | trust-in-allah | en | sit | I did everything I could for my test, now what do I do about the result? | topic=values; values=['patience', 'trust']; question=I did everything I could for my test, now what do I do about the result? | 3 | topic_filter |
| 15 | trustworthiness | en | sit | my friend lent me his pen and I lost it, what should I do? | topic=values; values=['honesty', 'kindness']; question=my friend lent me his pen and I lost it, what should I do? | 3 | other_value |
| 16 | visiting-the-sick | ar | sit | جاري عنده حمى، أروح أسلم عليه؟ | topic=values; values=['kindness', 'respect']; question=جاري عنده حمى، أروح أسلم عليه؟ | 3 | other_value |
| 17 | visiting-the-sick | en | hadith | is there a hadith about going to see a person who is not well? | topic=hadith; values=['mercy', 'kindness']; question=is there a hadith about going to see a person who is not well? | 3 | other_value |
