# Content tools

Run everything below from `backend/session_moral_context/content`. All tools are plain Python 3 (standard library only; `ffmpeg` for audio cutting). Nothing here may type or "fix" scripture: verse text only ever comes from a pinned data file or from Quranpedia.

| Tool | Purpose |
|---|---|
| `fetch_verse.py` | Build new verse items (Arabic from a pinned KFGQPC file or Quranpedia mushaf 2, English from Quranpedia translation 1947). |
| `refresh_arabic.py` | One-shot: rewrite `arabic_text`, add `arabic_text_search` and `text_edition` in every verse item from the pinned file. |
| `verify_arabic.py` | Compare every verse item with the pinned file. Exit 1 on any mismatch. Run in CI. |
| `cut_ayah_clips.py` | Cut per-ayah mp3 clips from an mp3quran surah file with its `ayat_timing` data (only if the audio source is switched). |
| `fetch_audio.py` | Download the current everyayah clips. |
| `mark_reviewed.py`, `show_items.py` | Review ledger and item viewer (see `../README.md`). |
| `kfgqpc.py` | Shared loader for the pinned KFGQPC file (used by the three verse tools). |
| `test_tools_verse.py` | Tests for the verse tools: `cd tools && python3 -m unittest -v test_tools_verse` (no network, no Django). |
| `fetch_hadeethenc.py` | Hadith route H, step 1-2: rank Bukhari/Muslim `صحيح` candidates per value from a local HadeethEnc cache (offline), and draft an `unverified` item. |
| `fetch_hadith.py`, `hadith_common.py` | Parser for dorar.net pages that a human saved (the proof step), and shared helpers. Scripts never fetch dorar.net. |
| `test_tools_hadith.py` | Tests for the hadith tools: `cd tools && python3 -m unittest -v test_tools_hadith` (synthetic records only). |

## Which text is "the" Quran text

`arabic_text` is the King Fahd Complex (KFGQPC) Hafs `aya_text` of one pinned release, byte for byte, minus the trailing end-of-ayah number (NBSP or space, then digits in v18 or one presentation-form glyph in U+FC00-U+FDFF in v2-0). No NFC, no kashida removal, no waqf-sign changes. `arabic_text_search` is the same file's `aya_text_emlaey` (the Complex's own simple spelling, for search only). `text_edition` records release and hash, for example `KFGQPC Hafs v2-0 sha256:d2960b321796` (the hash shown is of the JSON you pinned). Background: `docs/hackathon/research/r4-quran-text-audio.md`. Quranpedia mushaf id 1 is not this text (imlaei-style); the right id is 2.

Accepted data-file shapes: JSON list of rows (or a dict holding one list), surah under `sura_no` or `sora`, ayah under `aya_no`, plus `aya_text` and optionally `aya_text_emlaey`; a UTF-8 BOM is fine. The open-tanween encoding differs between releases (U+0657/065E/0656 in v18, U+08F0-08F2 in v3.0). It is stored as published; the first line printed by `verify_arabic.py` shows the counts so you can see which one your file uses. The frontend font must match that release.

## Runbook for the lead (replace the 74 stored verse texts)

Prerequisites: the WP1 model change (`arabic_text_search`, `text_edition`) is merged, otherwise `seed_content` rejects the new keys.

1. Download the official file (needs a route the Complex's host answers, e.g. from Saudi Arabia) and pin it.

   ```bash
   mkdir -p tools/.cache/kfgqpc && cd tools/.cache/kfgqpc          # .cache/ is gitignored
   curl -L -o UthmanicHafs_v2-0.zip https://download.qurancomplex.gov.sa/resources_dev/UthmanicHafs_v2-0.zip
   sha256sum UthmanicHafs_v2-0.zip     # a third-party archive recorded a7b0e5591945712ec5e4d6142938ae4d1e9b49bdc89dff06222789bfebdfd72c
   unzip -o UthmanicHafs_v2-0.zip
   ls "UthmanicHafs_v2-0 data"         # hafsData_v2-0.json is the file we want
   sha256sum "UthmanicHafs_v2-0 data/hafsData_v2-0.json"
   cd ../../..
   ```

   The sha256 of the **JSON** is the pin (it is what goes into `text_edition`). Note it, and write down the release and download date. Fallback if the Complex is unreachable: the v18 mirror `https://raw.githubusercontent.com/thetruetruth/quran-data-kfgqpc/main/hafs/data/hafsData_v18.json`, sha256 `5d8bb91726e482839d0057633cb1973031e4d706fa9604eea5e08892f20ba140` (say so in the submission).

2. Set shell variables for the rest.

   ```bash
   KF="tools/.cache/kfgqpc/UthmanicHafs_v2-0 data/hafsData_v2-0.json"
   PIN=<sha256 of that JSON>
   ```

3. "Before" check (today expected: `74 mismatching verse(s)`, exit 1).

   ```bash
   python3 tools/verify_arabic.py --kfgqpc "$KF" --sha256 $PIN
   ```

4. Dry run, then refresh. The dry run lists every verse and field that would change and writes nothing. The refresh only touches items of type `verse`; it leaves `verification_status`, `reviewed_by` and `reviewed_at` alone on purpose, so the review hashes go stale and all 74 verses show up as needing re-review.

   ```bash
   python3 tools/refresh_arabic.py --kfgqpc "$KF" --sha256 $PIN --dry-run
   python3 tools/refresh_arabic.py --kfgqpc "$KF" --sha256 $PIN
   ```

   Optional, to restore the exact source wording of the English (fixes the added full stop in 74:4 and nothing else; needs a QuranEnc `english_saheeh` dump, e.g. `data/quranenc/english_saheeh.json` from `risan/quran-json`, or a QuranEnc API response):

   ```bash
   python3 tools/refresh_arabic.py --kfgqpc "$KF" --sha256 $PIN --fix-english path/to/english_saheeh.json --dry-run
   ```

5. Proof. This must print `0 mismatching verse(s)`; `--strict` also requires the two new fields on every verse, fails any verse whose `arabic_text` still ends in NBSP, a space, a digit or an ayah-number glyph, and refuses to run without `--sha256` (exit 2).

   ```bash
   python3 tools/verify_arabic.py --kfgqpc "$KF" --sha256 $PIN --strict
   ```

6. Stale reviews (expected: all 74 verses listed, exit 1).

   ```bash
   python3 tools/mark_reviewed.py --check
   ```

7. Human review of the 74 (scoped, about 30 minutes): the font renders without empty boxes; the five verses whose waqf signs differ from the old text (2:261, 2:262, 5:119, 16:78, 24:22) against a printed or app Madinah mushaf; a sample of the rasm changes (for example 2:153, 20:14, 39:9). Then mark them:

   ```bash
   python3 tools/mark_reviewed.py --by "Abdulrahman Salamah" --at YYYY-MM-DD verse:2:153 verse:49:12 ...   # or a file name / value slug
   python3 tools/mark_reviewed.py --check        # must print: all reviews valid
   ```

8. Reseed and commit the item files together with `reviewed.json`.

   ```bash
   cd ../.. && python3 manage.py seed_content --dry-run && python3 manage.py seed_content
   ```

CI (cheap and offline once the data file is available):

```bash
python3 tools/verify_arabic.py --kfgqpc "$KF" --sha256 $PIN --strict && python3 tools/mark_reviewed.py --check
```

## Adding new verses

```bash
python3 tools/fetch_verse.py --kfgqpc "$KF" --sha256 $PIN 2:153 49:12 > /tmp/new_verses.json      # preferred
python3 tools/fetch_verse.py 2:153                                                                 # Quranpedia mushaf 2, no search text
python3 tools/fetch_verse.py --audio-source none 2:153                                             # no audio_url
```

The English and the Quranpedia `source_url` still come from `api.quranpedia.net` / `quranpedia.net` (cached under `tools/.cache/`, one request every 2 s). Items come out with `verification_status: "seeded"`; only a human sets `reviewed`. Paste the output into the right `items/<value>.json` and add `values`, `age_band` and the child explanation.

## Cutting audio clips (only if the audio decision switches away from everyayah)

```bash
python3 tools/cut_ayah_clips.py --read 1 --server https://cdn.mp3quran.net/audio/ibrahim-akhdar/r1/ \
    --out ../static/quran 49:12 2:153
# offline, one surah:
python3 tools/cut_ayah_clips.py --timing-json t.json --surah-mp3 049.mp3 --out /tmp/clips 49:12
```

`--read` is the mp3quran moshaf id, `--server` its folder (the `server` field of `https://www.mp3quran.net/api/v3/reciters?language=eng&reciter=<id>`; surah files are `https://cdn.mp3quran.net/audio/<reciter>/rN/NNN.mp3`). Use the `www.` host: the bare `mp3quran.net` domain now 301-redirects to an HTML page. Output names are `SSSAAA.mp3`, the same as today's clips. Requests are paced and cached (one timing file and one surah file per surah); do not use this for bulk downloads. Listen to a few clips: the timing marks can include a breath of the neighbouring ayah. The timing and audio URLs above were checked against the live API on 2026-10-05 (a full online cut was not run); cutting is tested offline with a synthetic file.

## Hadith candidates (route H, plan section 4)

HadeethEnc finds, dorar.net proves. Everything below is offline once `fetch_hadeethenc.py pull` has filled `tools/.cache/hadeethenc/` (gitignored; the pull is the only network step and stops on HTTP 403).

```bash
cd tools
python3 fetch_hadeethenc.py candidates --value honesty                 # ranked table for one value
python3 fetch_hadeethenc.py candidates --value all                     # counts for all 38 values + .cache/hadeethenc/candidates.json
python3 fetch_hadeethenc.py draft --id 5504 --value honesty --dorar-file .cache/dorar/honesty.html
```

- **Gates** (every record): grade exactly `صحيح`; attribution only Bukhari, Muslim or agreed upon; no category (own, parent or list membership) in the deny-list of `hadeethenc_categories.json`; (category 324 "Descriptions of Paradise and Hell" is unblocked by the lead: those hadith are candidates, and the age screen above flags graphic ones 10-13; 323 grave, 83 barzakh, 63/84 portents of the Hour and the rest stay blocked); at most `--max-words` Arabic words (default 80).
- **Mapping:** `hadeethenc_categories.json` gives each value `categories` (every member counts) and `keyword_only_categories` (a member counts only if an Arabic or English keyword hits). Justice, caring for orphans and not wasting have no category of their own, so they are found by Arabic keyword inside broad categories (for example Bukhari 6005 is in 511, Muslim 1827 in 282). `keywords_ar` in that file wins over the child-voice `keywords_ar` of `values.json`.
- **Keywords:** Arabic is compared after normalisation (no tashkeel, alef/ya/ta-marbuta folded, word breaks kept) on the Arabic title and matn, so the 91 records without English still match. English keywords are word-start stems.
- **Rank per value:** category match, then Arabic keyword, then English keyword; inside a tier, English available, number known, more hits, shorter.
- **Numbers:** the number is read from the Arabic `reference`. When there is none, the candidate stays and is marked `needs_number` (`?` in the table, `null` in the JSON): read it off the dorar page.
- **`candidates.json`:** `[{value, hadeethenc_id, book, number|null, needs_number, grade, attribution, words, first_8_words_ar, hadeethenc_url}]`, every candidate of every value in rank order (`--limit` does not apply). `first_8_words_ar` is 8 words of the saying (after the narrator clause), enough to search dorar.net. `book` is `null` for an agreed-upon hadith whose reference names no number.
- **Still thin after the cache:** values with fewer than 2 candidates are flagged `<2`. They need more categories pulled (add to the mapping, then `pull --values slug`) or route D (saved dorar searches, `fetch_hadith.py`).

## Drafting from saved dorar pages (`draft_from_page.py`, plan section 6)

Pages are saved by hand into `tools/.cache/dorar-{tafseer,aqeeda,feqhia,history}/` (gitignored); the tool never fetches. `show` prints the cleaned page as numbered lines, `draft` copies a contiguous cut of those lines into a draft item (`arabic_text` is never typed).

```bash
cd backend/session_moral_context/content
python3 tools/draft_from_page.py show tools/.cache/dorar-history/1.md                 # numbered cleaned lines
python3 tools/draft_from_page.py show tools/.cache/dorar-history/1.md --sentences 43  # line 43 split into numbered sentences
python3 tools/draft_from_page.py draft tools/.cache/dorar-history/1.md --type sirah --value love-of-the-prophet \
    --lines 43 --sentences 1 --level C --disagreement-ar "..." --disagreement-en "..." --out /tmp/sirah.json
```

- **`--lines A-B`**: whole cleaned lines, joined with newlines.
- **`--sentences A-B`** (only with a single `--lines N`): dorar event pages put the whole event on one line, so this takes sentences A..B of that line. The rule (`split_sentences`): a sentence ends at `.` `؟` `?` `!` `؛` (a run counts once) that is outside `()` `[]` `{}` `«»` and straight `"..."` quotes and is followed by a space, the end of the line or an Arabic letter (dorar often drops the space between sentences); the terminator and the space after it stay with their sentence; text after the last terminator is the last sentence. The pieces re-join to the exact line, so every range is an exact substring of the page (asserted), and the cut goes through the same checks as a line cut: inline-verse refusal for ﴿ ﴾, `{...}` around Arabic letters (dorar history's verse format) and `[surah: ayah]` references (a cut that includes such a brace-quoted verse is refused; other inline Quran formats are not detected), the age screen, and the quoted-prophetic-speech warning (a speech verb or the Prophet's name followed by a quote mark: warning only, since a sirah/aqidah excerpt may not quote a saying without book, number and grade). A quoted saying or a bracketed remark inside a sentence cannot be cut out: pick another sentence or leave the page.

## FAQ extractor (Bayyinat PDF, plan section 6.5)

`extract_faq.py` needs PyMuPDF on the curator's machine only (`pip install pymupdf`). It is not a backend runtime dependency, so it is not in `backend/requirements.txt`. Its PDF tests skip when PyMuPDF is missing, and one test (verse glyphs drawn in a second font) also needs `DejaVuSans-Bold.ttf`. The PDF is never fetched: it stays on the lead's Mac (`~/Documents/alsadiq-sources/dawa-7937-bayyinat.pdf`) and its page cache is gitignored.

```bash
cd tools
python3 extract_faq.py toc "$PDF" --grep الكعبة                      # 263 questions, number / title / printed page
python3 extract_faq.py question "$PDF" 9 --render .cache/bayyinat    # blocks as paragraphs + one PNG per page
python3 extract_faq.py draft "$PDF" 9 --value prayer --paras 1 --allow-dropped-symbols --out /tmp/faq.json   # --paras takes one index (2) or a range (1-3)
python3 extract_faq.py glyphs "$PDF" 65                              # fonts, dropped glyphs, digit glyphs by colour
```

What the tool does with this PDF, and what the reviewer still has to check against the rendered page:

- **Finding a question.** The TOC's printed pages drift from the page headers (by 1 page at Q9, 21 at Q229), so question *n* is the *n*-th `السؤال` label of the book (263 labels, cached in `labels.json`); the TOC supplies the title only. Two questions never share a page in this book; if they did, the earlier one's label is skipped.
- **Ligatures.** The text layer draws lam-alef and `الله` as zero-width letters followed by the carrier letter; the tool regroups them (`الإسلام`, not `اإلسالم`). A ligature that carries a mark loses its alef in the text layer (`مبطلًا` → `مبطلً`, `إلَّا` → `إلَّ`, `وَلَا` → `وَلَ`; 906 such lams in the book, none with its alef). Where the loss is certain, namely a lam with fathatan at a word end and a standalone token that is a bare marked lam with at most a و/ف/ب and أ/إ prefix, the alef is restored and the paragraph is flagged `[alef xN]`; a lost alef inside a longer vocalised word (hadith and poetry quotes in the detailed answer, `الْأَذْهَان`) stays lost. The shadda of `ألَّا` is lost too, which only matters with `--keep-tashkeel`. A second loss is certain and fully repaired: the text layer (PyMuPDF `rawdict`) unpacks a lam-alef ligature into a zero-width alef at the carrier's right edge, and an alef drawn exactly there (the bold `الادعاء`, `الامتناع`, mid-word `بمجالات`; 173 alefs in the book) is dropped as a duplicate glyph. The page's glyph trace (`get_texttrace`) still has it, so the tool restores an alef that the trace draws where the rawdict has only a zero-width alef twin and a lam ending at that point, and counts it into the same `[alef xN]` flag. A question whose text has a verse hole or a dropped honorific gets the TOC title (title_ar cannot carry either); a similar wording with a verse hole is dropped from `keywords_ar`; a dropped honorific anywhere in the item (answer, question or similar wordings) needs `--allow-dropped-symbols`. Nothing is restored from a dictionary: `فهذا لاختبارِ صدقه` (Q247) has no alef on the page and keeps none.
- **Tashkeel.** The PDF places marks by position; the tool attaches them to the letter whose left edge they sit on, which is right in the samples checked, but it is not verified text. `draft` therefore strips tashkeel from `title_ar`, `keywords_ar` and `arabic_text`; `--keep-tashkeel` keeps the marks and the review must then check every one. `question` always shows the marks, for comparison with the page.
- **Verses and honorifics.** `QCF4_Hafs_*` glyphs are verse holes (`--related verse:S:A` per hole, never typed); `KFGQPCArabicSymbols01` glyphs are honorific signs with no text (the draft refuses until `--allow-dropped-symbols`, after they are restored against the page); the `ﷺ` glyph of the text font folds to its words and is kept.
- **Layout.** The ❋ list marker (the digit 3 of the heading font in the ornament colour, `BULLET_GLYPHS`) becomes a bullet, which splits the similar wordings; a bullet item's hanging lines stay in the item; a numbered marker `1)` starts a paragraph (the rawdict labels its three glyphs `)1 ` in the wrong order, the trace puts the characters back on the right boxes, 511 rows in the book); a `-:` at a line start is punctuation, not a marker, so the sentence continues; the bare `الجواب` box closes the block before it; `مضمون السؤال` is missing in 98 questions and the question text under `السؤال` in two (118, 235), where `title_ar` falls back to the TOC title, as it does (warned) when the question text is longer than 200 characters, the bank's `title_ar` limit (Q241).
- **Age screen.** Hits are warnings (`[jihad] "بالسيف"` on Q229 sets `age_band` 10-13); the deny-list is in `draft_from_page.py`. Hope first (الترغيب قبل الترهيب): simple afterlife words (الجنة, النار, جهنم, عذاب, يوم القيامة, الآخرة; Paradise, Hell, the Fire, the Last Day) are only a `tone check [afterlife_mention]` (no age change; explain for 6-9 with mercy, reward and repentance, the Fire briefly). Grave torment and punishment detail (`afterlife_graphic`: قبر, برزخ, زقوم, سعير, سقر, لظى, ضريع, غسلين, صديد, سلاسل, أغلال, نكير, grave, boiling...; not منكر or حميم, which mean "wrongdoing" and "close friend" in values text) still sets `age_band` 10-13.
