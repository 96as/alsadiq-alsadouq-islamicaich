# Knowledge-bank content format

Files read by `python3 manage.py seed_content [--dry-run] [--dir PATH]`:

- `values.json`: one list of values.
- `items/*.json`: each file is a list of items, read in filename order.

## No source, no answer

Scripture is copied from the approved source (Quran: quranpedia.net or qurancomplex.gov.sa; hadith: Sahih al-Bukhari / Sahih Muslim, or other collections only with a grade from dorar.net or shamela.ws), never typed from memory. A hadith needs book, number, grade, grader and source URL. A verse needs surah, ayah and the exact Uthmani text.

## Examples

```json
// content/values.json
[{"slug":"honesty","name_ar":"الصدق","name_en":"Honesty","keywords_ar":["صدق","كذب","الكذب","صادق"],
  "keywords_en":["honest","lie","lying","truth"],"child_description_ar":"...","child_description_en":"...","order":1}]
// content/items/honesty.json
[{"type":"hadith","values":["honesty"],"arabic_text":"...","english_text":"...","book":"Sahih al-Bukhari",
  "number":"6094","narrator":"...","grade":"صحيح","grader":"البخاري","source_site":"dorar.net",
  "source_url":"https://dorar.net/hadith/sharh/...","child_explanation_ar":"...","child_explanation_en":"...",
  "age_band":"all","verification_status":"seeded"}]
```

(The comments are for reading only; real files are plain JSON.)

## Required fields by type

| type | required when `seeded` | natural key |
|---|---|---|
| verse | `surah`, `ayah`, `arabic_text` (exact Uthmani), `source_site` = `quranpedia.net` or `qurancomplex.gov.sa` | `type`, `surah`, `ayah` |
| hadith | `book`, `number`, `grade`, `grader`, `source_url`, `source_site` | `type`, `book`, `number` |
| tafsir, aqidah, fiqh, sirah, faq, term, story | `source_site`, `source_url` | `type`, `source_url` |

For non-verse/hadith types use one item per `source_url`; add a `#fragment` to tell several items on one page apart.

Fiqh is general information only, never a personal fatwa.

## Allowed values

- `type`: verse, hadith, tafsir, aqidah, fiqh, sirah, faq, term, story
- `age_band`: all, 6-9, 10-13
- `verification_status`: `unverified`, `seeded` or `reviewed`. A file may say `reviewed` (with `reviewed_by` and `reviewed_at`), but it is only stored as `reviewed` if the review ledger proves it (see Review ledger); otherwise it is stored as `seeded`.
- `source_site`: quranpedia.net, qurancomplex.gov.sa, dorar.net, shamela.ws, dawa.center, islamic-content.com
- Other item keys: `arabic_text`, `english_text`, `child_explanation_ar`, `child_explanation_en`, `child_explanation_older_ar`, `child_explanation_older_en`, `girls_note_ar`, `girls_note_en`, `audio_url`, `narrator`, `translation_name`, `source_url`, `values` (list of value slugs, order kept). Unknown keys are rejected.

## Upsert behaviour

Values upsert on `slug`. Items upsert on the natural key above. Re-running with the same files leaves the data unchanged. Keys omitted from a file keep their existing database values. Items already `reviewed` in the database are left alone unless the file content changed (then they are downgraded to `seeded` and `STALE REVIEW` is printed). An item that fails validation is rejected with a reason and the rest of the file still loads. Use `--dry-run` to check files without writing.

## Optional explanation fields

- `child_explanation_older_ar` / `_en`: deeper explanation for ages 10-13, used instead of or next to `child_explanation_*` for older children.
- `girls_note_ar` / `_en`: an extra line shown only to girls (for example modesty or hijab); retrieval picks it from `ChildProfile.gender`.

All four are blank by default and are included in `search_text_norm`.

## Explanation tone (lead decision: hope first, gentle accountability)

- Our `child_explanation_*` lead with Allah's love, mercy and Jannah's reward (الترغيب قبل الترهيب). Jannah, the Fire, the Last Day and iman are taught at all ages.
- Ages 6-9: the Fire is mentioned briefly and simply as the result of wrongdoing, never in detail, always paired with mercy, forgiveness and repentance. 10-13 (`child_explanation_older_*`): fuller.
- Never a threat, never about a specific person's fate, never graphic for young children: grave torment and punishment descriptions stay `age_band` 10-13.
- Do not set `age_band` 10-13 just because a definition mentions punishment; write our explanation hope-first and keep `all`. `draft_from_page.py` only gives a tone check for simple afterlife words and an age hit for graphic ones.

## Schema v2 fields (task 01, plan §8)
All optional; absent keys never change an existing review hash.

- `title_ar`, `title_en`, `keywords_ar`, `keywords_en`: included in `search_text_norm`.
- `arabic_text_search`: verses only. When non-empty, search text is built from it instead of `arabic_text`. `arabic_text` stays the exact Uthmani text.
- `text_edition`, `translation_source_url`: provenance of the text and translation.
- `content_level` (`A`/`B`/`C`): when omitted, `seed_content` fills it by type: verse, hadith, term, story, sirah, aqidah = A; tafsir, faq, fiqh = B. Level C requires `disagreement_note_ar` or `disagreement_note_en`.
- `related`: list of natural-key labels resolved in a second pass after all items load: `verse:2:153`, `hadith:Sahih al-Bukhari:6094`, `tafsir:<source_url>` (other types use `type:<source_url>`). An unknown label rejects that item's `related` with a message; the item itself is still seeded. Reverse accessor: `cited_by`.

### Allowed `source_site` per type (seeded/reviewed)
| type | sites |
|---|---|
| verse | quranpedia.net, qurancomplex.gov.sa |
| hadith | dorar.net, shamela.ws |
| tafsir | dorar.net, quranpedia.net, shamela.ws |
| aqidah, fiqh, sirah | dorar.net, shamela.ws |
| faq | dawa.center |
| term | islamic-content.com |
| story | quranpedia.net |

`hadeethenc.com`, `quranenc.com`, `islamenc.com`, `terminologyenc.com` are valid choices but rejected for every type until organiser approval (plan §12 Q1). `mp3quran.net` is a choice for audio provenance and is not an allowed text source. The URL host must still match `source_site`.

### Other rules for seeded/reviewed items
- Hadith need `arabic_text` and `grade` exactly `صحيح` (surrounding brackets and whitespace are ignored when comparing).
- Non-empty `english_text` requires `translation_name`.
- Every non-verse type except story needs `arabic_text`; story must leave it blank.

### `ContentItem.objects.servable()`
Verses with status seeded or reviewed; every other type reviewed only; hadith additionally graded `صحيح`. Use it for anything the agent may serve.

## Review (status in the files, proof in the ledger)

Review status is visible in the item files: a reviewed item carries `"verification_status": "reviewed"`, `"reviewed_by": "Name"` and `"reviewed_at": "YYYY-MM-DD"`. These three keys are not content and are excluded from the hash. `reviewed.json` is the proof: a list of `{"key", "sha256", "by", "at"}`, where `key` is the natural key label (for example `verse:2:153`), `sha256` is the hash of the item dict minus the three status keys (`utils/review.py`) and `at` is `YYYY-MM-DD`.

Mark items with `python3 tools/mark_reviewed.py --by "Name" [--at YYYY-MM-DD] REF ...`, where REF is a value slug (every item with that value), a file name (`prayer.json`) or a natural key. It writes both the ledger entry and the three keys in the item file. Commit both with the content.

Any edit to an item's content (including `values`) changes its hash, so the ledger no longer proves the review:

- `python3 tools/mark_reviewed.py --check` (alias `--list-stale`) exits 1 and lists every item whose file says `reviewed` but whose ledger entry is missing or stale, and every stale ledger entry. It prints `all reviews valid` and exits 0 otherwise. Run it in CI or before committing.
- `seed_content` stores an item as `reviewed` only if the file says so AND the ledger hash matches (`reviewed_by` is looked up as a username or full name, else left empty). A file that says `reviewed` without a matching ledger entry is stored as `seeded` and prints `STALE REVIEW <key>`. If the ledger matches but the file says `seeded`, the item is still promoted and `NOTE <key> reviewed in ledger; run mark_reviewed to write it into the file` is printed. Ledger keys that match no item print `UNKNOWN REVIEW KEY`.

To re-review after an edit, check the new content and run `mark_reviewed.py` again.

## Recitation audio

Verse mp3s (Husary, normal-pace murattal, from everyayah) live in `backend/session_moral_context/static/quran/SSSAAA.mp3` and are served at `/static/quran/SSSAAA.mp3`. `audio_url` keeps the original everyayah URL as provenance. Download with `python3 tools/fetch_audio.py --out ../static/quran S:A ...`.
