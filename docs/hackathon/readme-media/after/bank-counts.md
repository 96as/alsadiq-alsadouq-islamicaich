# Reviewed content bank: counts only

Source of numbers: a read-only query (`ContentItem.objects.servable()`, `Value`, `ValueItem`) run through
`docker exec alsadiq-backend-1 python manage.py shell` against the running demo stack (app code 8c2ff0d), 2026-10-05.
No content text is reproduced here; only counts.

## By type

| Type | Items (servable) | Verification status | Source site |
|---|---:|---|---|
| verse | 74 | reviewed | quranpedia.net |
| hadith | 94 | reviewed | dorar.net |
| term | 32 | reviewed | islamic-content.com |
| faq | 23 | reviewed | dawa.center |
| tafsir | 23 | reviewed | dorar.net |
| aqidah | 14 | reviewed | dorar.net |
| fiqh | 8 | reviewed | dorar.net |
| sirah | 5 | reviewed | dorar.net |
| **Total** | **273** | all 273 reviewed, all 273 servable | |

Not-servable items (any other status): 0 (total rows 273, servable 273).

## By content level

| Type | Level A | Level B | Level C |
|---|---:|---:|---:|
| verse | 74 | 0 | 0 |
| hadith | 94 | 0 | 0 |
| term | 31 | 0 | 1 |
| faq | 0 | 23 | 0 |
| tafsir | 0 | 23 | 0 |
| fiqh | 0 | 8 | 0 |
| aqidah | 13 | 0 | 1 |
| sirah | 4 | 0 | 1 |
| **Total** | **216** | **54** | **3** |

Items carrying a disagreement note: 3 (equal to the three level-C items).

## Values (moral themes)

- Values: 38, all 38 have at least one servable item.
- Item-to-value links: 311.
- Servable items linked to no value: 30 (aqidah 4, faq 10, term 16).
- Items with a child explanation in English: 273 of 273; in Arabic: 273 of 273.

## Per-value coverage (number of items by type)

Columns: verse, hadith, tafsir, faq, term, aqidah, fiqh, sirah.

| Value (slug) | verse | hadith | tafsir | faq | term | aqidah | fiqh | sirah |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| prayer | 4 | 3 | 0 | 2 | 2 | 0 | 4 | 1 |
| honesty | 2 | 3 | 1 | 0 | 1 | 0 | 0 | 0 |
| trustworthiness | 3 | 2 | 1 | 0 | 1 | 0 | 0 | 1 |
| honouring-parents | 3 | 2 | 2 | 0 | 0 | 0 | 1 | 0 |
| mercy | 4 | 3 | 1 | 3 | 0 | 0 | 0 | 0 |
| patience | 3 | 3 | 2 | 1 | 1 | 1 | 1 | 0 |
| gratitude | 3 | 3 | 3 | 1 | 0 | 0 | 0 | 0 |
| cooperation | 3 | 2 | 1 | 1 | 0 | 0 | 0 | 2 |
| kindness-to-animals | 2 | 3 | 0 | 1 | 0 | 0 | 0 | 0 |
| cleanliness | 2 | 3 | 1 | 0 | 1 | 0 | 2 | 0 |
| modesty | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| good-character | 3 | 3 | 3 | 1 | 1 | 0 | 0 | 0 |
| good-neighbour | 1 | 3 | 1 | 0 | 0 | 0 | 0 | 0 |
| seeking-knowledge | 3 | 3 | 1 | 2 | 0 | 1 | 0 | 0 |
| humility | 3 | 3 | 2 | 0 | 0 | 0 | 0 | 0 |
| justice | 3 | 2 | 1 | 0 | 0 | 0 | 0 | 2 |
| keeping-promises | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| generosity | 3 | 3 | 1 | 1 | 1 | 0 | 2 | 0 |
| forgiveness | 2 | 3 | 3 | 0 | 0 | 0 | 0 | 0 |
| kind-words | 2 | 3 | 3 | 0 | 0 | 0 | 0 | 0 |
| charity | 4 | 3 | 1 | 1 | 2 | 0 | 2 | 0 |
| respecting-elders | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| caring-for-orphans | 3 | 2 | 1 | 0 | 0 | 0 | 0 | 0 |
| brotherhood | 3 | 3 | 2 | 1 | 0 | 0 | 0 | 1 |
| controlling-anger | 2 | 3 | 1 | 0 | 0 | 0 | 0 | 0 |
| remembering-allah | 2 | 3 | 1 | 0 | 3 | 0 | 0 | 0 |
| trust-in-allah | 2 | 3 | 1 | 1 | 1 | 1 | 0 | 0 |
| visiting-the-sick | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| spreading-salam | 2 | 3 | 1 | 0 | 0 | 0 | 0 | 0 |
| table-manners | 2 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| helping-others | 2 | 3 | 1 | 0 | 0 | 0 | 0 | 2 |
| avoiding-backbiting | 2 | 3 | 1 | 0 | 0 | 0 | 0 | 0 |
| courage | 2 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| not-wasting | 2 | 3 | 1 | 0 | 0 | 0 | 0 | 0 |
| family-ties | 2 | 3 | 0 | 0 | 0 | 0 | 1 | 0 |
| love-of-the-prophet | 5 | 3 | 2 | 0 | 5 | 3 | 0 | 1 |
| sincerity | 2 | 2 | 1 | 0 | 0 | 6 | 0 | 0 |
| contentment | 2 | 3 | 0 | 1 | 0 | 0 | 0 | 0 |

(An item can belong to more than one value, so column sums exceed the item totals: 311 links over 243 linked items.)

## Detail by type

- Hadith: 94 total, Sahih al-Bukhari 60, Sahih Muslim 34. Grade recorded on all 94 as "sahih" (graders: al-Bukhari 60, Muslim 34).
- Hadith with an English translation: 42 (HadeethEnc translation). Hadith with Arabic text only: 52.
- Verse: 74 total across 35 distinct surahs, all 74 with a recitation audio link, all 74 with the Saheeh International English translation.
- Term: 32 total, all 32 with the Al-Jamhara English entry.
- Items with English source text overall: 148 (74 verse + 42 hadith + 32 term).
