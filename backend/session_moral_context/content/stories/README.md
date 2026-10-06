# Stories catalogue: candidate format

This folder holds the **candidate stories**: Quranic stories that teach one of our values. When we build the stories bank later, we start from these files, so the research is already done.

Nothing here is read by `seed_content`, and nothing here is ever shown to a child. It is planning material.



## One file per story

Put each story in `candidates/<slug>.json`. The slug is lowercase English with dashes, for example `sulayman-and-the-ant`. The file is a single JSON object.

| Field | What to write |
|---|---|
| `slug` | The same as the file name, without `.json`. |
| `title_ar` | Arabic title, for example the name of the prophet or the people. |
| `title_en` | English title. |
| `figures` | List of the people in the story, in English, for example `["Yusuf", "Ya'qub"]`. |
| `verse_ranges` | Where the Quran tells this story, as `"surah:ayah"` or `"surah:ayah-ayah"`. A story can have several ranges, even in different surahs, for example `["12:4-6", "12:89-92"]`. Check every range on Quranpedia (see below). |
| `bank_verses` | The verses from our bank (`content/items/*.json`) that belong to this story, as `"surah:ayah"`. Use `[]` if no bank verse points to it yet. |
| `values` | Value slugs this story teaches. Only slugs that exist in `content/values.json`. |
| `summary_ar` | The story in your own words, in Arabic, 3 to 6 sentences. |
| `summary_en` | The same in English. |
| `tafsir_sources` | List of the tafsir pages you checked: `{"site": "quranpedia.net", "book": "<tafsir book name>", "url": "<the page link>"}`. |
| `notes` | Anything you are not sure about, or that you could not confirm. Empty string if nothing. |
| `status` | Always `"candidate"`. Only the lead changes it later. |
| `found_by` | `"the team"`, or the name of the person who found the item. |

## Rules for the summaries

- `summary_*` are **for planning only**. They are never shown to children and never presented as scripture.
- Use your own words. Do **not** copy verse text or tafsir text into the file. Do not type any verse from memory.
- Every detail must come from the verses themselves or from approved early tafsir: Quranpedia tafsir books by authors of the first three Islamic centuries (for example al-Tabari).
- No Israiliyyat. No details from memory, movies, cartoons or story books.
- If a detail is uncertain, leave it out of the summary and write it in `notes`, for example: "Heard that X, but did not find it in the verses or al-Tabari."
- If you are not sure, write less. A short true summary is better than a long one with a doubtful detail.

## How to find the full verse range

The bank usually has only one verse of a story. To get the whole range:

1. Open the verse's `source_url` on quranpedia.net (the reading list from `show_items.py` prints it). Read the verses before and after it and see where the story begins and ends.
2. Open the tafsir on the same page. Early tafsir (for example al-Tabari) says which verses belong together.
3. If the story continues in another surah, search for it in the tafsir and add that range too.
4. Write the range as `"surah:first-last"`. Check the first and last number again before you save.

## Example

This is only an illustration of the format. The summary is deliberately minimal, and the verse range is only the bank verse. A real file has the full range and a real summary.

```json
{
  "slug": "sulayman-and-the-ant",
  "title_ar": "سليمان والنملة",
  "title_en": "Sulayman and the ant",
  "figures": ["Sulayman"],
  "verse_ranges": ["27:18"],
  "bank_verses": ["27:18"],
  "values": ["kindness-to-animals"],
  "summary_ar": "مثال فقط: هذه الآية في بنك الآيات تتعلق بقصة سليمان عليه السلام مع النملة. تكتب هنا الملخص الحقيقي بعد قراءة الآيات والتفسير.",
  "summary_en": "Example only: this bank verse belongs to the story of Sulayman and the ant. The real summary goes here after reading the verses and the tafsir.",
  "tafsir_sources": [
    {"site": "quranpedia.net", "book": "TO FILL: an early tafsir book, e.g. al-Tabari", "url": "https://quranpedia.net/tafsir/an-naml/18"}
  ],
  "notes": "TO DO: find the full range of the story around 27:18 and check the start and end verses.",
  "status": "candidate",
  "found_by": "the team"
}
```

## Check a file

```bash
python3 -m json.tool backend/session_moral_context/content/stories/candidates/<slug>.json
```

If it prints the JSON back, the file is valid. If it prints an error, fix the comma or quote it points to.
