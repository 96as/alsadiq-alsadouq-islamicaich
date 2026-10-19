# R4: Quran text fidelity, display, audio and translation

Status: research output, 4 Oct 2026, branch `hk/01-knowledge-bank`. Nothing in the repo was changed except this file. Scratch scripts and downloaded data are in `/tmp/claude-0/r4/` (not committed). Reads: `docs/hackathon/resource-package-en.md` (the "package"), `backend/session_moral_context/content/README.md`, `content/tools/fetch_verse.py`, `content/tools/fetch_audio.py`, all 74 verse items in `content/items/*.json`, `models.py`, `utils/arabic.py`, `utils/review.py`, tasks 02 and 05.

## 0. Verdict

1. **The 74 stored `arabic_text` values are not the King Fahd Complex (KFGQPC) Uthmani text.** Measured against the KFGQPC Hafs data (v18): 0 of 74 match exactly, 2 of 74 match after trivial encoding normalisation, 0 contain alef wasla (U+0671; KFGQPC uses it 13,483 times in the Qur'an and 297 times in these same 74 verses). Our text is an imlaei-style script with diacritics: **74 of 74 are identical to Tanzil's "Simple Plain" text once waqf signs are removed**, and 72 of 74 have the same letters as KFGQPC's own search column `aya_text_emlaey`. Details in section 2.
2. **It is not only spelling.** 20 of 74 verses differ in rasm (for example `الصَّلَاة` instead of `ٱلصَّلَوٰة`, `شَيْئًا` instead of `شَيۡـٔٗا`), and **5 of 74 verses carry different waqf (pause) signs from the Madinah mushaf** (2:261, 2:262, 5:119, 16:78, 24:22). That is a difference in the transmitted text, not in typography.
3. **Why:** `fetch_verse.py` reads `GET /v1/mushafs/1/{s}/{a}` from Quranpedia and the docstring and `tasks/02` assume that is "Uthmani, King Fahd Hafs". Quranpedia's own dump metadata says the KFGQPC Uthmani text is **mushaf id 2** ("مصحف حفص نسخة نصية", QPC Hafs). Mushaf id 1 is titled "القرآن الكريم برواية حفص عن عاصم" and, judging by what we stored, serves a different script. The git history shows no verse text was ever edited by hand (0 of 76 verses ever had two different `arabic_text` values).
4. **Fix is cheap.** Quranpedia mushaf 2 equals the KFGQPC v18 file on all 6,236 ayat (modulo kashida placement and NBSP), so we can keep Quranpedia as the `source_site` and `source_url`, switch the fetch to mushaf 2 (or to the Complex's own JSON), and add a second field for search text. About 2 to 3 hours including re-review (section 7).
5. **Display:** KFGQPC text needs the KFGQPC font (or a font that implements the Unicode open-tanween code points). I rendered the text: Amiri Quran shows empty boxes for 1,807 U+065E code points in the Qur'an when fed the legacy KFGQPC encoding, and general fonts draw the wrong marks. The font's embedded licence allows free use and distribution unmodified; it forbids modification and "reproduction", which makes a woff2 conversion a question for the organisers.
6. **Search will break if `arabic_text` is simply replaced.** `normalize_ar()` turns `الصلاة`, `الوالدين` and `يا ايها` into strings that no longer occur in the KFGQPC text. Store KFGQPC's `aya_text_emlaey` as a separate search field (section 6).
7. **Audio:** `everyayah.com` is not in the package and states no licence; we also commit 74 mp3 files (46 MB) into git. `mp3quran.net` is the only audio platform the package names, has an ayat-timing API, but **no Husary Muallim in the snapshot I could read** (Husary has five other moshafs). The Complex also publishes complete per-ayah recitations (Hudhaifi, Al-Muaiqly and others). Recommendation: keep everyayah for the demo, disclose it, and decide on a switch after the live checks in section 9.
8. **Translation:** the 73 of 74 English texts equal the QuranEnc `english_saheeh` text (Noor International Center, v1.1.2) after markup removal; the 74th differs by one added full stop. The Complex publishes no English translation in the archive I read. Saheeh International is acceptable under the package because it is on QuranEnc, an Association platform, and on Quranpedia.

## 1. Evidence tags and the sources I used

Every claim carries one of these tags.

- `[V-CODE]`: I ran code or read a data/code file myself. A repo path or a raw GitHub URL follows.
- `[V-DOCS]`: I read the document, page or metadata file itself (URL follows). If the document is a third party's statement about someone else, I say so.
- `[NLC]`: needs a live check. Used when the host is blocked from this sandbox (qurancomplex.gov.sa, quranpedia.net, api.quranpedia.net, mp3quran.net, everyayah.com, quranenc.com, cdn.quran.ws, scancode-licensedb) and I only saw the fact in a web-search summary, or when I infer it.

Blocked hosts were not bypassed. GitHub raw, PyPI and npm worked.

### 1.1 Data files used for the comparison

| ID | What | Where | Notes |
|---|---|---|---|
| S1 | KFGQPC "Uthmanic Hafs" v18 data: `hafsData_v18.json/.csv/.xml` (6,236 rows; fields `id, jozz, sora, sora_name_*, page, line_start, line_end, aya_no, aya_text, aya_text_emlaey`) | `https://raw.githubusercontent.com/thetruetruth/quran-data-kfgqpc/main/hafs/data/hafsData_v18.json` and, byte-identical, `https://raw.githubusercontent.com/ibnhazm/KFGQPC/master/hafs/data/hafsData_v18.json` `[V-CODE]` | sha256 of the JSON `5d8bb91726e482839d0057633cb1973031e4d706fa9604eea5e08892f20ba140`. Its own `hafs/README.md`: "KFGQPC Hafs Uthmanic Data, Version 0.18, Date 2021-10-25". JSON, CSV and XML agree on all 6,236 `aya_text` values `[V-CODE]`. |
| S2 | KFGQPC "Hafs Smart" v8: `hafs_smart_v8.json` | same repo, `hafs-smart/data/hafs_smart_v8.json` `[V-CODE]` | `aya_text` is **not Unicode Arabic**: every glyph is a Private Use code point (U+E000 to U+E9xx) preceded by U+200F, so it only renders with the Hafs Smart font and cannot be searched or read by a screen reader. Not usable for us. `aya_text_emlaey` is plain. |
| S3 | The Complex's current release, as described by a third-party archive: `UthmanicHafs_v2-0.zip`, server `Last-Modified` 19 Sep 2023, sha256 `a7b0e5591945712ec5e4d6142938ae4d1e9b49bdc89dff06222789bfebdfd72c`; `kfgqpc_hafs_smart_4.zip`, 30 Jun 2022 | `https://raw.githubusercontent.com/quran-ws/kfgqpc-resources/main/resources/quran-dev/uthmanic-hafs/metadata.json`, official URL `https://download.qurancomplex.gov.sa/resources_dev/UthmanicHafs_v2-0.zip` `[V-DOCS]` (the archive is a third party; this is their metadata) | I could not download the zip (host blocked here; the archive says the official host answers only from inside Saudi Arabia `[NLC]`). Contents listed by the archive: `hafsData_v2-0.{csv,html,json,sql,txt,xlsx,xml}`, `read.me`, `uthmanic_hafs_v20.ttf`. |
| S4 | Quranpedia dump of **mushaf 2** ("مصحف حفص نسخة نصية", dump version 2026-09-30) as captured by `risan/quran-json` | `https://raw.githubusercontent.com/risan/quran-json/main/data/quranpedia/qpc-hafs.json` `[V-CODE]`; metadata in `https://raw.githubusercontent.com/risan/quran-json/main/data/meta/sources.json` `[V-DOCS]` | sha256 of the snapshot `0136b913aeb5a6a0389681f988215791ddd848c4347f7cf5e9d2574db7f1da49`. It is a third-party copy of a Quranpedia dump, not a call to the live API. |
| S5 | KFGQPC Hafs text from `UthmanicHafs-v-3.0.zip` (release year 2026 in the metadata), rebuilt by quran.ws as words plus separate marks | PyPI wheel `quran_text-0.1.0` (`quran_text_data/hafs.json`, `UthmanicHafs-v-3.0.ttf`), `https://pypi.org/project/quran-text/` `[V-CODE]` | quran.ws itself records "No source URL is recorded for this package" for v3.0 `[V-CODE]`, so I treat S5 only as a cross-check. I rebuilt ayah strings by re-attaching the marks as its README describes. |
| S6 | Tanzil texts (`simple-plain`, `simple`, `uthmani`, `simple-min`, ...) | `https://raw.githubusercontent.com/risan/quran-json/main/data/tanzil/*.json` `[V-CODE]` | Used to identify what our stored script is. |
| S7 | QuranEnc `english_saheeh` v1.1.2, `english_rwwad`, `english_hilali_khan` | `https://raw.githubusercontent.com/risan/quran-json/main/data/quranenc/english_saheeh.json` etc. `[V-CODE]` | Translation comparison. |

### 1.2 How sure am I that S1 is the unmodified KFGQPC text?

| Evidence | Result |
|---|---|
| Repo claims | Both repos say the data comes from `qurancomplex.gov.sa/en/techquran/dev/` `[V-CODE]`. Neither repo has a LICENSE file (404 for LICENSE, LICENSE.md, license, LICENCE.md) `[V-CODE]`. |
| Internal version | `hafs/README.md`: Version 0.18, 2021-10-25 `[V-CODE]`. The font in the same repo, `hafs/font/hafs.18.ttf`, has name table "Version 0.18" and the Complex's copyright and EULA `[V-CODE]`. |
| Two repos | `thetruetruth/quran-data-kfgqpc` and `ibnhazm/KFGQPC` serve byte-identical files (equal sha256 for the JSON, the CSV and the Hafs Smart JSON). They may be forks of each other, so this is weak evidence `[V-CODE]`. |
| Independent derivations | (a) Quranpedia mushaf 2 (S4) equals S1 on **6,236 of 6,236** ayat after removing kashida (U+0640) and normalising NBSP. (b) quran.ws v3.0 (S5), after mapping three code points (section 2.6), equals S1 exactly on 6,000 ayat and after NFC plus whitespace on 6,201; the other 35 differ only by kashida removal and two mark substitutions (U+06EA to U+065C, U+06DC to U+06E3). None of the 35 is among our 74 verses `[V-CODE]`. |
| Not available | A checksum of the Complex's own v18 zip. The Complex now serves v2-0, so S1 cannot be matched to an official hash `[NLC]`. |

Confidence: **high (about 95%) that S1 contains the Complex's text for Hafs; moderate that the file is byte-identical to a Complex release.** For the 74 verses the three KFGQPC-derived sources (S1, S4, S5) agree on every letter and mark except the encoding differences listed in section 2.6.

## 2. Task 1: text fidelity of the 74 verses

### 2.1 Match levels (all 74 verses, script `/tmp/claude-0/r4/compare_final.py`)

| Test | Result |
|---|---|
| Exact match with KFGQPC `aya_text` (S1), number included | **0 / 74** |
| Exact match after removing the end-of-ayah number (NBSP + Arabic-Indic digits) | **0 / 74** |
| Exact match with Quranpedia mushaf 2 (S4) | **0 / 74** |
| Match after encoding-only normalisation (drop number, NBSP to space, tatweel removed, U+0671 to U+0627, U+06E1 to U+0652, space before waqf sign dropped) | **2 / 74** (74:4 and 93:9, two short verses with no idgham mark, dagger alef, open tanween or small waw/yeh) |
| Letter skeleton equals KFGQPC `aya_text_emlaey` (marks, spaces and waqf removed, alef/yeh/hamza forms unified) | **72 / 74** (the two exceptions, 3:103 `نعمتَ` and 27:18 `وَادِ`, follow the Uthmani rasm in our text while `emlaey` is modernised) |
| Letter skeleton equals KFGQPC `aya_text` (rasm-aware: dagger alef counted as alef, `آ` as `ءا`) | **54 / 74** (20 verses differ in rasm, section 2.4) |
| Identical to Tanzil "Simple Plain" (NFC, waqf signs removed, Tanzil's prepended basmalah removed) | **74 / 74** |
| Quranpedia mushaf 2 equals KFGQPC v18 on our 74 verses | 67 exact; the other 7 differ only by an extra kashida (U+0640) in Quranpedia: 2:220, 4:36, 5:2, 5:8, 16:78, 17:34, 28:26 |
| Alef wasla U+0671 in our 74 `arabic_text` values | **0** (KFGQPC text for the same verses: 297) |

All `[V-CODE]`: `backend/session_moral_context/content/items/*.json` against S1, S4, S6.

### 2.2 Which script is our stored text?

Letter for letter it is Tanzil's "Simple Plain" (imlaei orthography, diacritics, no special idgham/ikhfa marking) with waqf signs added as separate space-delimited tokens and `۞` at hizb starts. I cannot say how Quranpedia produced it; the Quranpedia licence says the "digitization, structuring, verification, diacritical correction, linking, and metadata" are Quranpedia's own work (`https://api.quranpedia.net/dumps/LICENSE.md`, quoted in S6's `sources.json` `[V-DOCS]`). Tanzil texts are CC BY 3.0, verbatim only (`https://tanzil.net/docs/text_license` `[V-DOCS]` via `sources.json`); if the origin is Tanzil that licence's attribution would apply `[NLC]`.

### 2.3 What differs, by kind (74 verses)

"Verses" is how many of the 74 verses contain at least one such difference; "Occurrences" is the total count.

| Difference | Verses | Occurrences | Example (KFGQPC left, ours right) |
|---|---|---|---|
| End-of-ayah number glyph: KFGQPC `aya_text` ends with NBSP + Arabic-Indic digits (`... ١٢`); ours has none | 74 | 74 | `رَّحِيمٞ ١٢` vs `رَحِيمٌ` (49:12) |
| Sukun form: KFGQPC U+06E1 (small high dotless head of khah), ours U+0652 | 72 | 652 | `وَإِذۡ` vs `وَإِذْ` (2:83) |
| Alef wasla: KFGQPC U+0671 `ٱ`, ours plain alef `ا` | 66 | 297 | `ٱلدُّنۡيَا` vs `الدُّنْيَا` (2:220) |
| Open tanween: KFGQPC U+0657 / U+065E / U+0656 (reused code points), ours U+064B / U+064C / U+064D | 56 | 108 | `إِحۡسَانٗا` vs `إِحْسَانًا` (2:83) |
| Word division: KFGQPC joins what we split | 54 | 54 | `يَٰٓأَيُّهَا` vs `يَا أَيُّهَا` (2:153) |
| Waqf sign attached to the word (KFGQPC) vs a separate token with a space (ours) | 50 | 102 | `ٱلۡأٓخِرَةِۗ وَيَسۡـَٔلُونَكَ` vs `الْآخِرَةِ ۗ وَيَسْأَلُونَكَ` (2:220) |
| Maddah above U+0653 (KFGQPC) vs precomposed `آ` or nothing | 45 | 97 | `ٱلۡأٓخِرَةِ` vs `الْآخِرَةِ` (2:220) |
| Silent alef after waw marked (`وا` + mark) vs unmarked | 37 | 90 | `ءَامَنُواْ` vs `آمَنُوا` (2:153) |
| Extra shadda for assimilation (idgham) in KFGQPC | 29 | 47 | `مَّثَلُ` vs `مَثَلُ` (2:261) |
| Rasm (letter skeleton) differs | 20 | 20 | `ٱلصَّلَوٰةِ` vs `الصَّلَاةِ` (2:153) |
| Small waw / small yeh U+06E5 / U+06E6 | 20 | 24 | `بِهِۦ` vs `بِهِ` (4:1) |
| Tatweel U+0640 used as a seat for a mark (KFGQPC) | 7 | 9 | `يَسۡـَٔلُونَكَ` vs `يَسْأَلُونَكَ` (2:220) |
| Iqlab / small low meem U+06E2 / U+06ED | 5 | 6 | `أَنۢبَتَتۡ` vs `أَنْبَتَتْ` (2:261) |
| Code points only in ours: U+0622 `آ` (33) and U+06D9 `ۙ` (2) | | | |

`[V-CODE]` `/tmp/claude-0/r4/compare_final.py`, output saved as `compare_final_out.txt`. Whole-set inventory: ours uses 52 distinct code points over 11,935 characters, KFGQPC uses 63 over 12,082 for the same verses.

### 2.4 Verses whose rasm differs (20)

2:83, 2:153, 2:220, 4:36, 4:135, 5:2, 5:8, 9:71, 16:78, 17:34, 20:14, 20:131, 24:22, 28:25, 28:26, 29:45, 33:21, 39:9, 57:23, 98:5. Typical cases: `الصلاة / الزكاة / الحياة` written with alef in ours and `ٱلصَّلَوٰة / ٱلزَّكَوٰة / ٱلۡحَيَوٰة` (waw plus dagger alef) in KFGQPC; `إسرائيل` vs `إِسۡرَٰٓءِيلَ`; `أُولُو` vs `أُوْلُواْ`; `شَيْئًا` vs `شَيۡـٔٗا`; `ٱلَّيۡلِ` vs `اللَّيْلِ` (39:9). `[V-CODE]`.

### 2.5 Waqf (pause) signs that differ in content (5 verses)

| Verse | Ours | KFGQPC v18 |
|---|---|---|
| 2:261 | `ۗ` `ۗ` | `ۗ` `ۚ` |
| 2:262 | `ۙ` | none |
| 5:119 | `ۚ` `ۚ` `ۚ` | `ۚ` `ۖ` `ۚ` |
| 16:78 | `ۙ` | none |
| 24:22 | `ۖ` `ۗ` `ۗ` | `ۖ` `ۗ` `ۚ` |

The Madinah mushaf's pause signs are part of the printed text. Our signs follow a different convention. `[V-CODE]`. The hizb sign `۞` is in the same five verses in both (4:36, 4:58, 4:135, 7:31, 17:23).

### 2.6 The three KFGQPC encodings, and a mapping we need

The Complex has changed how it encodes "open tanween" (the doubled-vowel marks in `كَثِيرٗا`):

| Release | Open fathatan / dammatan / kasratan encoded as | Evidence |
|---|---|---|
| Hafs Smart v8 | Private Use glyph codes | `[V-CODE]` S2 |
| Hafs v18 (2021) and Quranpedia mushaf 2 (dump 2026-09-30) | U+0657, U+065E, U+0656 (reused marks: inverted damma, fatha with two dots, subscript alef) | counts 2,901 / 1,807 / 1,935 `[V-CODE]` S1, S4 |
| Hafs v3.0 (quran.ws, 2026) | U+08F0, U+08F1, U+08F2 (Unicode Arabic Extended-B "OPEN FATHATAN/DAMMATAN/KASRATAN") | counts 2,901 / 1,807 / 1,935 `[V-CODE]` S5 |

Mapping U+0657 to U+08F0, U+065E to U+08F1, U+0656 to U+08F2 turns S1 into S5 on 6,000 of 6,236 ayat exactly (all 74 of ours agree after NFC and whitespace normalisation). In `UthmanicHafs-v-3.0.ttf` the glyph for U+08F0 is the very glyph the v18 font draws for U+0657 (same outline hash), and the v3.0 font keeps both code-point sets `[V-CODE]`. So the v3.0 font draws both encodings the same way, the v18 font draws only the legacy one.

### 2.7 Rendering test (Pillow + HarfBuzz, KFGQPC v3.0 font as reference)

Rendered 49:12 and 2:153 in six ways (`/tmp/claude-0/r4/render_49_12.png`, `render_2_153.png`, script `render.py`) `[V-CODE]`:

| Text / font | Result |
|---|---|
| KFGQPC v18 text in KFGQPC Hafs v3.0 font | Correct Uthmani page look (reference) |
| KFGQPC v18 text (legacy code points) in **Amiri Quran** | **Empty boxes** where U+065E occurs (end of `إِثۡمٞ` and `تَوَّابٞ`); the other two legacy code points draw their ordinary Unicode meaning (inverted damma, subscript alef) instead of open tanween |
| Same text mapped to U+08F0 to U+08F2, in Amiri Quran | Renders correctly |
| Same, in Scheherazade New | Renders correctly |
| Legacy text in Noto Naskh Arabic | No boxes, but the legacy code points draw their ordinary Unicode glyphs (fatha with two dots, inverted damma, subscript alef) instead of open tanween |
| Our stored text in Amiri Quran | Clean, but visibly a different script: alef letters instead of wasla and dagger alef, no idgham shadda, spaced waqf signs |

Code-point coverage of all KFGQPC v18 text (6,236 ayat): Amiri Quran lacks only U+065E (1,807 occurrences) `[V-CODE]`. Visual check was by image only; Android and iOS system rendering is `[NLC]`.

### 2.8 What are Quranpedia's mushaf ids?

| Id | Name (Quranpedia) | Description | Evidence |
|---|---|---|---|
| 1 | "القرآن الكريم برواية حفص عن عاصم" (page `quranpedia.net/mushaf/1`); dump file `mushafs-1.json.gz` (394 KB) "مصحف حفص" | Not read. What `GET /v1/mushafs/1/{s}/{a}` returned for our 74 verses is the Tanzil-Simple-Plain-style text above (`fetch_verse.py` strips only BOM and whitespace and git history shows no edits) | titles `[NLC]` (search-result summary of `https://quranpedia.net/dumps` and `/mushaf/1`); returned text `[V-CODE]` |
| 2 | "مصحف حفص نسخة نصية" | "المصحف الكريم برواية حفص عن عاصم بالخط العثماني من إصدار مجمع الملك فهد لطباعة المصحف الشريف، غير موافق للمطبوع" (Uthmani script from the King Fahd Complex edition, not matching the printed pagination). Bismillah `بِسۡمِ ٱللَّهِ ٱلرَّحۡمَٰنِ ٱلرَّحِيمِ` (with U+0671, U+06E1). Dump file 405 KB | `[V-DOCS]` risan `data/meta/sources.json` (`source_metadata`, `mushaf_id: 2`) |
| 3 | "مصحف حفص نستعليق" | Hafs Nastaliq, "not matching the printed edition" | `[V-DOCS]` same file |
| 4, 6, 7, 9, 10 | Warsh, al-Duri, Qalun, Shu'bah, al-Susi | KFGQPC editions | `[V-DOCS]` same file |

So `tasks/02` ("Quran text (Uthmani, King Fahd Hafs) ... `GET /v1/mushafs/1/...`") assumed the wrong id. Quranpedia dumps are "official versioned files in the exact API schema" and must be kept current through `/api/v1/changes?since=` `[NLC]` (search summary of `https://quranpedia.net/dumps`); licence: free inside apps with no attribution; republishing as a downloadable dataset needs credit and dump version `[V-DOCS]` (quoted in `sources.json`, terms checked 2026-09-20 by risan).

### 2.9 Effect on search (`utils/arabic.py`)

`normalize_ar()` strips U+064B-U+065F, U+0670, U+0640, U+06D6-U+06ED and maps `أإآٱ` to `ا`, `ى` to `ي`, `ة` to `ه`. It does not strip U+08F0-U+08F2 and it cannot turn `ءَامَنُواْ` or `ٱلصَّلَوٰةِ` into the modern spelling. Test with the real data `[V-CODE]`:

| Query | In normalised ours | In normalised KFGQPC `aya_text` | In normalised KFGQPC `aya_text_emlaey` |
|---|---|---|---|
| `الصلاة` (2:153) | yes | **no** (`الصلوه`) | yes |
| `الوالدين` (17:23) | yes | **no** (`الولدين`) | yes |
| `يا ايها الذين` (49:12) | yes | no | no (joined as `ياايها`; token search still works) |
| `آمنوا` (49:12) | yes | yes | yes |

Replacing `arabic_text` without a separate search field would silently weaken retrieval for common modern spellings.

## 3. Display and the KFGQPC font

- **Font EULA, read from the TTF name table** (`hafs.18.ttf` and `UthmanicHafs-v-3.0.ttf`, nameID 0 and 13) `[V-CODE]`: "Permission is hereby granted, Free of Cost, to any person obtaining a copy of this Font accompanying this license, the rights to Use, Copy, Distribute, subject to ... 1. The Font Software cannot be Sold, Modified, Altered, Translated, Reverse Engineered, Decompiled, Disassembled, Reproduced ..." and "This Font is the property of King Fahd Glorious Quran Printing Complex, and may not be reproduced, modified without the express written approval of KFGQPC." Download page named in the font: `http://fonts.qurancomplex.gov.sa/`. This answers the "check its licence" note in `tasks/05-frontend-ui.md:46`: self-hosting the **unmodified TTF** is allowed; **converting to woff2 or subsetting is arguably "modified/altered"**, so ask (section 8). Third-party woff2 copies exist (`mustafa0x/qpc-fonts`, the GitHub mirror) but I would not ship them without the Complex's say.
- **Digital Mushaf terms** (separate from the font): the Complex says its digital Mushaf al-Madinah files may be used free "in all personal, individual businesses, works of governmental departments ..., websites, software" (`https://dm.qurancomplex.gov.sa/en/?p=138`, `https://qurancomplex.gov.sa/en/?p=4713`) `[NLC]` (search-result summary only; the font project README points at `http://dm.qurancomplex.gov.sa/copyright-2/` `[V-CODE]`, `nuqayah/qpc-fonts` README).
- **Version pairing:** the v18 font covers only the legacy open-tanween code points; v3.0 covers both; v2.0 (`uthmanic_hafs_v20.ttf`, official) is `[NLC]`. The Hafs Smart font maps its text through Private Use codes (2,737 of its 2,754 cmap entries; it has no U+0628). Ship the font **together with** the data release it was built for.
- **Fallback:** if the KFGQPC font fails to load, render with Amiri Quran after translating U+0657/U+065E/U+0656 to U+08F0/U+08F1/U+08F2 at display time only (stored text stays verbatim). Tested above.
- **Today's plan** (`tasks/05`): Amiri from Google Fonts. Amiri and Amiri Quran are SIL OFL `[NLC]`. With imlaei text (our current data) Amiri is fine. With KFGQPC Uthmani text Amiri Quran is acceptable only with the mapping above.
- **End-of-ayah ornament:** the KFGQPC font contains U+06DD; append U+06DD followed by Arabic-Indic digits if an ornament is wanted. Do not store the number in `arabic_text`.
- **Hafs Smart (S2) is not recommended** even though the Complex describes it as the verse-level display font for smart devices (`hafs-smart/README.md`, `https://raw.githubusercontent.com/thetruetruth/quran-data-kfgqpc/main/hafs-smart/README.md` `[V-DOCS]`): the text is unreadable without that one font and cannot be hashed meaningfully for review.

## 4. Task 3: audio

### 4.1 mp3quran.net API v3 (endpoints and fields)

Base: `https://mp3quran.net/api/v3` (clients also use `https://www.mp3quran.net/api/v3`). Free, no key, per the package (page 12) `[V-DOCS]`.

| Endpoint | Parameters | Response | Evidence |
|---|---|---|---|
| `GET /reciters` | `language` (ar, eng, fr, ru, de, es, tr, cn, th, ur, bn, bs, ug, fa, tg, ml, tl, id, pt, ha, sw), `reciter`, `rewaya`, `sura`, `last_updated_date` | `{ "reciters": [ { id, name, letter, (recent) date, moshaf: [ { id, name, server, surah_total, moshaf_type, surah_list } ] } ] }` | Usage `[V-CODE]`: `aramai7777-bit/QURAN--3` `lib/mp3quranApi.js` calls `reciters?language=ar`, filters `r.moshaf.length`, builds `server + NNN + ".mp3"` and tests `moshaf.surah_list.split(',')`; `Hamdoud-350/quran` README documents the same. Parameter list and `moshaf_type` `[NLC]` (search summary of `https://www.mp3quran.net/eng/api`). |
| `GET /suwar?language=` , `/riwayat`, `/languages`, `/moshaf` | | surah names, riwayat, language list | `[NLC]` (search summary). `/moshaf` I did not see documented. |
| `GET /ayat_timing?surah={1-114}&read={moshaf id}` | `surah`, `read` | JSON **list** of objects with `ayah` (int, entries with `ayah < 1` exist), `start_time` and `end_time` in **milliseconds**; snippets also show `polygon`, `x`, `y`, `page` (an SVG page URL) | `[V-CODE]` for `ayah`, `start_time`, `end_time`, ms units, `ayah < 1` entries: `ahmad1876/quraani` `src/recitation.py` (`MP3Q_TIMING = "https://www.mp3quran.net/api/v3/ayat_timing?surah={ch}&read={read}"`). Other fields `[NLC]`. |
| `GET /ayat_timing/reads` | none | list of reads that have timing: `{ id, name, rewaya, folder_url, soar_count, soar_link }` | `[NLC]` (search summary of `https://www.mp3quran.net/eng/api`) |
| Audio file | | whole surah: `{moshaf.server}{SSS}.mp3` | `[V-CODE]` three clients |

**Id scheme:** the `read` parameter is the **moshaf id**. In the flattened snapshot (`risan/quran-json` `data/audio/mp3quran.json`, 288 entries, ids `reciterId-moshafId`) all 17 `read` values used by `ahmad1876/quraani` match the second number and the `server` folder exactly (17 of 17) `[V-CODE]`.

### 4.2 Is Husary "Muallim" on mp3quran?

In the snapshot, Mahmoud Khalil Al-Hussary is reciter **118** with five moshafs: Hafs murattal `118-118` (`https://server13.mp3quran.net/husr/`), Mojawwad `118-119`, Warsh `118-120`, al-Duri `118-269`, Qalun `118-270`, all 114 surahs. **No "Almusshaf Al Mo'lim" for him.** Teaching ("Almusshaf Al Mo'lim") moshafs that do exist: Minshawi `112-114` (114 surahs, `https://server10.mp3quran.net/minsh/Almusshaf-Al-Mo-lim/`), Abdulbari Mohammad `50-169` (91 surahs), Alhusayni Al-Azazi `11-11` (57), Maher Al-Muaiqly `102-103` (38), Abdullah Al-Mousa `243-286` (38) `[V-CODE]` risan snapshot (date of capture unknown; mp3quran may have added files since `[NLC]`). Package page 12 says the library has "teaching recitations and recitations in the mujawwad style" `[V-DOCS]`. Which reads have timings is `[NLC]`: the 17 reads that `quraani` uses are all Hafs recitations (murattal, mojawwad or featured) of other reciters; none is Husary or a Mo'lim read (one is labelled "Featured Recitation").

### 4.3 Producing per-ayah clips from a surah file

mp3quran serves whole surahs; the 74 verses sit in **35 surahs**. Two ways:

1. **Pre-cut clips (recommended if we switch).** Download each surah once, cut by timing, write `SSSAAA.mp3` with the same names as today, so nothing else changes. Script tested offline with a synthetic two-ayah file: `/tmp/claude-0/r4/cut_ayah_clips.py` (Appendix B). Each cut is re-encoded (128 kbps, 44.1 kHz) with 50 ms of lead and 150 ms of tail; with `-ss/-to` on an mp3 the stream-copy variant drifted about 26 ms (frame granularity) in my test `[V-CODE]`. The mp3quran timing is a start/end marker per ayah, so the clip may include a breath of the neighbour; listen to a few.
2. **Play the surah with offsets (no copy).** `<audio src=".../049.mp3">`, `currentTime = start/1000`, pause at `end/1000`. Needs HTTP range support on `serverNN.mp3quran.net` `[NLC]`, downloads or buffers part of a 5 to 100 MB file for one ayah, and depends on their uptime during the demo. On the other hand it copies nothing, which is the posture `risan/quran-json` takes ("we link to its files and do not copy them").

### 4.4 Options compared

| | everyayah.com Husary Muallim (today) | mp3quran.net (cut by `ayat_timing`) | King Fahd Complex audio |
|---|---|---|---|
| Named in the package | No | **Yes** (page 12, "recommended" platform, free API, verse timings) | **Yes**, the Complex is the primary Quran authority (page 14), but audio is not described in the package `[V-DOCS]` |
| Per-ayah files | Yes (`Husary_Muallim_128kbps/SSSAAA.mp3`) `[V-CODE]` | No, timing only | **Yes**: "Complete Qur'an Verses (Ayat) Recitation" sets of about 6,350 files each, labelled by the archive Huthify (804 MB), Al-Muaiqly (726 MB), Ayyoub (917 MB), Muhanna (1.04 GB), Akhdar (1.19 GB), plus Shu'bah, Qaloon, Sousi and Douri riwayah sets and per-surah sets `[V-DOCS]` `https://raw.githubusercontent.com/quran-ws/kfgqpc-resources/main/metadata/quran-audios.json` (third-party archive of the Complex's pages, captured 2026-09-07) |
| Teaching style (Muallim) | **Yes, Husary** | Muallim exists for Minshawi (114 surahs) and others, not Husary in the snapshot | No: murattal sets |
| Timings | n/a | `ayat_timing` for some reads `[NLC]` | n/a (already per ayah) |
| Licence statement | None found: licence, terms and readme paths 404 and the homepage has no terms (risan's check) `[V-DOCS]` `https://raw.githubusercontent.com/risan/quran-json/main/data/meta/sources.json` | None found for redistribution (same file); package calls the API free and public | "All rights remain with the Complex; files stored unmodified" (archive README) `[V-DOCS]`; reuse terms for audio `[NLC]`; Digital Mushaf free-use statement is about the Mushaf files `[NLC]` |
| Reachability | Worked for the team | Open API; the `quraani` project runs it daily from GitHub Actions `[V-CODE]` | Official host `download.qurancomplex.gov.sa` reported to answer only from Saudi Arabia, mirror `cdn.quran.ws` `[NLC]` |
| Effort to adopt | none | write cut script (done), 35 surah downloads, re-listen | download 1 GB zip, pick 74 files, no cutting |

### 4.5 Is the current use a compliance risk?

- **Against the package:** the package's binding rules are about transmitted *text* and its sources. It does not forbid other audio hosts, but it names exactly one audio platform (mp3quran.net). A judge asking "where does the recitation come from" gets the answer "everyayah.com, which is not on your list". Low to medium risk (my judgement). `[V-DOCS]` package pp. 3, 5, 12.
- **Rights:** everyayah states no licence and we **redistribute**: `git ls-files backend/session_moral_context/static/quran | wc -l` gives 74 tracked mp3 files (46 MB, 49.5 minutes) in `https://github.com/96as/Alsadiq-Alsadouq`, and they are served at `/static/quran/`. The reciter's own copyright remains whatever the licence status is. `[V-CODE]` repo. Whether the repository is public is `[NLC]`.
- **Recommendation:** keep everayah for the demo build (it works, children get the teaching recitation, files are reviewed), add provenance and a disclosure line to the submission and the About page, and **do not add more verses from it until the lead has run the live checks in section 9**. If those show a Muallim read with timings on mp3quran (for example Minshawi, read 114), switch with the script in Appendix B; the cut files keep their names. If the lead can download the Complex's ayah set, that is the cleanest provenance but changes the reciter to a murattal recitation. Whatever is chosen, consider moving the mp3 files out of git (build-time download) so the repo itself does not host them.

## 5. Task 4: English translation

| Question | Answer |
|---|---|
| What do our items store? | `english_text` plus `translation_name = "Saheeh International"` on all 74 `[V-CODE]`. `fetch_verse.py` takes Quranpedia translation id 1947 and strips only the `(N) ` prefix, `[123]` footnote markers and the trailing footnote block. |
| Is it the same as QuranEnc? | Yes. The `(N) ` prefix, `[n]` markers and footnote block of QuranEnc `english_saheeh` (title "English Translation - Noor International Center", version 1.1.2) are exactly what `english()` removes. After the same cleaning, **73 of 74 `english_text` values are identical**; 74:4 differs only by an added full stop in ours (`And your clothing purify.` vs `And your clothing purify`). English texts were never edited in git `[V-CODE]`. |
| Does the Complex publish an English translation? | Not in the archive I read: 47 translation PDFs (Urdu, Persian, Indonesian, Bengali, Turkish, Spanish, German, Swahili, and others) with no English or French `[V-DOCS]` `https://raw.githubusercontent.com/quran-ws/kfgqpc-resources/main/metadata/quran-translations.json` (captured 2026-09-07; the live page `https://qurancomplex.gov.sa/quran-translations/` is `[NLC]`). |
| So is Saheeh International "approved"? | The package accepts "the King Fahd Complex edition, its translations, or those available at quranpedia.net" (page 3), and says "for approved translations, rely on the Association's platforms" (page 11). QuranEnc (Association) lists it as `english_saheeh`; Quranpedia lists it as id 1947; IslamHouse (Association) also hosts "English Translation - Saheeh International" (`https://islamhouse.com/en/books/78592/` `[NLC]`, search result). It is therefore acceptable on both routes, but it is not a Complex publication. |
| QuranEnc terms | Re-publication allowed on 7 conditions: no modification/addition/deletion; credit the publisher and QuranEnc; state the version; keep the transcript information; report notes back; keep up to date; no inappropriate advertising `[V-DOCS]` (quoted in risan `sources.json`; `https://quranenc.com/en/home/api` `[NLC]`). Our cleaning removes the verse-number prefix and footnotes (21 of the 74 verses have translator footnotes in QuranEnc) and one item has an added full stop. Whether the Quranpedia route is governed by the same terms is `[NLC]`. |
| Alternatives on QuranEnc | `english_rwwad` (Rowwad Translation Center, v1.0.19): simpler wording, no bracketed insertions, "Allah" without a macron: 49:12 "O you who believe, avoid much suspicion, for some suspicions are sin. Do not spy on one another, nor backbite one another." `english_hilali_khan`: long parenthetical glosses ("You would hate it (so hate backbiting)"). `[V-CODE]` S7. Saheeh uses bracketed insertions and "Allāh" with a macron, which a 6 to 9 year old may find harder to read; Rowwad reads more simply. All 74 reviews were done on Saheeh, so switching would mean re-review. |

**Recommendation for the translation:** keep Saheeh International for the demo (all 74 reviews were done on it, and the text is the same as QuranEnc's `english_saheeh`, an Association platform). Give the translator and platform credit, restore the exact source wording (74:4), and put Rowwad on the roadmap as a simpler-English option for ages 6 to 9, which would need its own review.

## 6. Recommended pipeline

**Decision summary:** store the Complex's Uthmani text verbatim, plus the Complex's own simple text for search; keep Quranpedia as visible source and link; display with the KFGQPC font; keep Saheeh International with credit; keep everayah for the demo and decide about the switch after live checks.

| Step | Recommendation |
|---|---|
| Text of record (`arabic_text`) | KFGQPC `aya_text` of **one pinned release**, minus the trailing NBSP + ayah number, otherwise byte-for-byte. Preferred: the Complex's own JSON (`UthmanicHafs_v2-0.zip` from `qurancomplex.gov.sa/quran-dev`, sha256 `a7b0e559...d72c` if it is still current). If the lead cannot download it: Quranpedia **mushaf 2** per ayah (`/v1/mushafs/2/{s}/{a}`), cross-checked against S1. Do not use mushaf 1, Hafs Smart, Tanzil or quran.ws as the text of record. |
| Field for search (new) | `arabic_text_search` = KFGQPC `aya_text_emlaey` (the Complex's "Emlaey text used for search purpose"). Compute `search_text_norm` from it instead of from `arabic_text` (`models.py` `save()`). Also add U+08F0-U+08F2 to the stripped range in `utils/arabic.py` in case v2/v3 encodings are used. Needs a migration: only task 01 may add it (AGENTS.md). |
| Provenance | Keep `source_site = quranpedia.net` and the Quranpedia ayah page as `source_url` (a human can open it; host check in `clean()` stays valid; package page 3 accepts quranpedia.net). Add a short `text_edition` string to each verse (for example `KFGQPC Hafs, UthmanicHafs_v2-0 (sha256 a7b0e559...)`, or `via Quranpedia mushaf 2, dump 2026-09-30`). If the organisers want the Complex as source of record, use `source_site = qurancomplex.gov.sa` with a Complex page as `source_url`; I found no per-ayah Complex URL `[NLC]`. Open one Quranpedia ayah page and check what script it shows; our current link may show a different script from the stored text `[NLC]`. |
| Normalisation on store | None. Do not apply NFC, do not drop kashida or waqf signs, do not map open-tanween code points. The ledger hash then proves the text is the source's. |
| Tooling | Rewrite `fetch_verse.py`: read the pinned JSON (`--kfgqpc path`), fail if the file's sha256 is not the pinned one, strip only the number, also emit `arabic_text_search` and `text_edition`; with `--cross-check` fetch Quranpedia mushaf 2 and report any difference other than kashida. Add `verify_arabic.py` (Appendix A) to CI next to `mark_reviewed.py --check`. |
| Display (web, mobile) | `lang="ar" dir="rtl"`, KFGQPC Hafs TTF **unmodified**, loaded with `font-display: swap`, matching the data release; fallback Amiri Quran with display-time mapping U+0657/065E/0656 to U+08F0/08F1/08F2. Size 28 px or more for children. Do not split or reflow the text; waqf signs are inside the words. |
| Search and retrieval | `normalize_ar(arabic_text_search)`; keep `arabic_text` for display and citation only. |
| Audio | Keep everayah Husary Muallim for the demo; show "Recitation: Mahmoud Khalil Al-Husary (Muallim), via everayah.com" on the card; run the live checks; if a Muallim read with timings exists on mp3quran, switch with `cut_ayah_clips.py` (35 surahs, about 1 to 2 hours including listening); otherwise leave as is and disclose. |
| Translation | Keep Saheeh International. Show credit "Saheeh International, via Quranpedia / QuranEnc (Noor International Center), v1.1.2" on the card or About page. Reproduce the source wording exactly (fix 74:4). Decide whether to keep translator footnotes for the 21 verses that have them (new optional field) after asking the organisers. |

## 7. Migration steps for the 74 verses

The review ledger is hash-based (`utils/review.py`: sha256 of the item dict minus the three status keys). Any change to `arabic_text` or any new field changes the hash, `seed_content` stores the item as `seeded` with `STALE REVIEW`, and `mark_reviewed.py --check` exits 1 for all 74. Only the Arabic text and provenance change; explanations, translation, values and audio are untouched, so the re-review is small.

1. **Choose and pin the release** (lead, 15 min). Download the Complex zip if reachable (section 9, check C) and note its sha256; otherwise use S1 or Quranpedia mushaf 2 and say so in `text_edition`.
2. **Run `verify_arabic.py` against the pin** to record the "before" state (expected: 74 mismatches).
3. **Task 01 migration:** add `arabic_text_search` (TextField, blank) and `text_edition` (CharField 200, blank) to `ContentItem`; no `seed_content` change is needed (its allowed keys come from the model fields, `seed_content.py:24-26`), but update the README "Other item keys" list; update `save()` and `normalize_ar`. Tests: a verse with `ٱلصَّلَوٰةِ` found by the query `الصلاة`.
4. **One-shot refresh script** (`content/tools/refresh_arabic.py`): for each `items/*.json`, replace only `arabic_text`, add `arabic_text_search` and `text_edition`, keep key order and JSON formatting, leave `verification_status`, `reviewed_by`, `reviewed_at` as they are (the hash makes them stale automatically). Commit the diff so reviewers see old vs new.
5. **Automatic proof:** `verify_arabic.py` must print `0 mismatching verse(s)` against the pinned file. This replaces most of the human reading: the lead no longer has to compare 74 Arabic strings with a website.
6. **Human review, scoped** (about 30 minutes): generate one HTML page with the 74 verses in the KFGQPC font, the Quranpedia link and the old text beside it; the lead checks (a) the font renders without boxes, (b) the five waqf-sign verses (2:261, 2:262, 5:119, 16:78, 24:22) against a printed or app Madinah mushaf, (c) a sample of 10 verses with rasm changes (for example 2:153, 20:14, 39:9). Then `python3 tools/mark_reviewed.py --by "Abdulrahman Salamah" --at <date> <files>`.
7. **Reseed and check:** `python3 manage.py seed_content --dry-run`, then real run; `mark_reviewed.py --check` must print `all reviews valid`. Update `reviewed.json` in the same commit.
8. **Update the docs that carry the wrong claim:** docstring of `fetch_verse.py` ("Uthmani, King Fahd Hafs" is wrong for mushaf 1), `tasks/02-content-curation.md:20` (mushaf 2), `content/README.md` (field list, "exact Uthmani"), and the frontend task font note.
9. **Frontend/mobile:** bundle the font, switch the verse card to `arabic_text` with the fallback mapping, test on one Android and one iOS device.
10. **Audio and translation notes:** add provenance strings; fix 74:4; leave the 74 mp3 files in place until the audio decision.

Effort: steps 1 to 5 about 1 to 1.5 hours, step 6 about 30 minutes, steps 7 to 9 about 1 hour.

## 8. Questions for the organisers

1. Is displaying the Qur'an in an imlaei script with diacritics acceptable, or do you expect the King Fahd Complex Uthmani script ("approved orthography and textual form", package page 3)? Will submissions be checked by exact comparison with the Complex's data, and against which release (v18 of 2021, v2.0 of Sept 2023, v3.0)?
2. Which release do you treat as canonical? The Complex changed how open tanween is encoded between releases (section 2.6).
3. May we self-host the KFGQPC Hafs font in our web and mobile builds, and may we convert it to woff2? The embedded EULA allows use, copy and distribute but not modification or reproduction.
4. Is recitation audio from `everyayah.com` acceptable? May we cut and host per-ayah clips from `mp3quran.net` surah files (derived works)? Does the Complex allow reuse of its own recitation sets, and do you have a mirror, since `download.qurancomplex.gov.sa` is reported to answer only from Saudi Arabia?
5. Is Saheeh International via Quranpedia or QuranEnc acceptable as the English translation, given that the Complex publishes none? May we drop footnote markers and verse-number prefixes (QuranEnc's "no modification/addition/deletion")?
6. When the text of record is the Complex's, is a Quranpedia ayah page an acceptable `source_url`, or is a Complex page expected? Is there a per-ayah Complex URL?
7. Does the Association's MCP server (`mcp.islamiccontent.org`) expose Qur'an Arabic text and ayah verification we can call at runtime to check a quoted verse?
8. Is there an agreed grader for "child-friendly" use of waqf signs and rasm (for example may we hide waqf signs for young readers), or must the text be shown exactly as in the Madinah mushaf?

## 9. Live checks for the lead's laptop

Run on a machine that can reach the hosts. Each block is independent.

**A. Quranpedia: what are mushaf 1 and 2, and what does the API return?**

```bash
UA='AlSadiq-curation/0.1'
curl -s -A "$UA" https://api.quranpedia.net/v1/mushafs \
 | python3 -c "import sys,json; [print(m['id'], m.get('name'), '|', m.get('description'), '|', m.get('font_file')) for m in json.load(sys.stdin)]"
for id in 1 2; do
  curl -s -A "$UA" https://api.quranpedia.net/v1/mushafs/$id/49/12 \
   | python3 -c "import sys,json; t=json.load(sys.stdin)['text']; print($id, 'wasla:', chr(0x671) in t, '|', t)"
done
```

Expected from this research: mushaf 1 text has no U+0671; mushaf 2 text equals `بِسۡمِ ٱللَّهِ ...` style (with `ٱ` and U+06E1) and for 49:12 equals the KFGQPC string in section 2.1. Then open `https://quranpedia.net/tafsir/al-hujurat/12` and note which script it shows.

**B. Cross-check mushaf 2 with the KFGQPC mirror for the 74 verses**

```bash
cd backend/session_moral_context/content
curl -sL -o /tmp/hafsData_v18.json https://raw.githubusercontent.com/thetruetruth/quran-data-kfgqpc/main/hafs/data/hafsData_v18.json
sha256sum /tmp/hafsData_v18.json   # expect 5d8bb91726e482839d0057633cb1973031e4d706fa9604eea5e08892f20ba140
python3 verify_arabic.py /tmp/hafsData_v18.json items    # script in Appendix A; today: 74 mismatching verse(s)
```

**C. The Complex's own package (needs a Saudi-reachable route or a VPN the organisers accept)**

```bash
curl -L -o UthmanicHafs_v2-0.zip https://download.qurancomplex.gov.sa/resources_dev/UthmanicHafs_v2-0.zip
sha256sum UthmanicHafs_v2-0.zip   # archive says a7b0e5591945712ec5e4d6142938ae4d1e9b49bdc89dff06222789bfebdfd72c
unzip -o UthmanicHafs_v2-0.zip && ls "UthmanicHafs_v2-0 data" "UthmanicHafs_v2-0 font"
python3 verify_arabic.py "UthmanicHafs_v2-0 data/hafsData_v2-0.json" items
python3 - <<'EOF'
import json, collections
d = json.load(open('UthmanicHafs_v2-0 data/hafsData_v2-0.json', encoding='utf-8-sig'))
cnt = collections.Counter(''.join(r['aya_text'] for r in d))
print({hex(cp): cnt.get(chr(cp), 0) for cp in (0x657, 0x65e, 0x656, 0x8f0, 0x8f1, 0x8f2, 0x671)})   # which open-tanween encoding does v2-0 use?
EOF
```

Also open `https://qurancomplex.gov.sa/quran-dev/` and note whether a newer Hafs package than v2-0 is listed. Check the font in `fonts.qurancomplex.gov.sa/wp02/en/?p=25` (Uthmanic Script License) and `http://dm.qurancomplex.gov.sa/copyright-2/`; send the terms text back to the main session.

**D. mp3quran: Husary Muallim, timings, range requests**

```bash
curl -s 'https://mp3quran.net/api/v3/reciters?language=eng&reciter=118' | python3 -m json.tool | grep -E '"(id|name|server|surah_total|moshaf_type)"'
curl -s 'https://mp3quran.net/api/v3/reciters?language=eng' \
 | python3 -c "import sys,json; [print(r['name'], m['id'], m['name'], m['surah_total'], m['server']) for r in json.load(sys.stdin)['reciters'] for m in r['moshaf'] if 'lim' in m['name'].lower()]"
curl -s 'https://mp3quran.net/api/v3/ayat_timing/reads' | python3 -c "
import sys,json
for r in json.load(sys.stdin):
    if any(k in (r['name']+r['rewaya']).lower() for k in ('hus','hussary','minsh','lim')): print(r)"
curl -s 'https://mp3quran.net/api/v3/ayat_timing?surah=49&read=114' | head -c 500; echo       # Minshawi Mo'lim (read = moshaf id)
curl -s 'https://mp3quran.net/api/v3/ayat_timing?surah=49&read=118' | head -c 500; echo       # Husary Hafs murattal
curl -sI 'https://server10.mp3quran.net/minsh/Almusshaf-Al-Mo-lim/049.mp3' | grep -i -E 'HTTP|accept-ranges|content-length'
```

Then test the cutter on one surah: `python3 cut_ayah_clips.py --read 114 --server https://server10.mp3quran.net/minsh/Almusshaf-Al-Mo-lim/ --out /tmp/clips 49:12` (Appendix B) and listen.

**E. EveryAyah and Complex audio terms**

```bash
curl -sI https://everyayah.com/data/Husary_Muallim_128kbps/049012.mp3 | head -5
for p in license LICENSE terms readme.txt; do echo $p; curl -s -o /dev/null -w '%{http_code}\n' https://everyayah.com/data/$p; done
curl -s https://qurancomplex.gov.sa/quran-audio-hafs-huthify/ | head -c 2000     # look for a rights/terms statement
```

**F. QuranEnc and Quranpedia translation**

```bash
curl -s https://quranenc.com/api/v1/translation/sura/english_saheeh/49 | python3 -m json.tool | head -30   # does it return arabic_text? which script?
curl -s -A "$UA" https://api.quranpedia.net/v1/translation/1947/74/4 | python3 -m json.tool               # trailing full stop in 74:4?
curl -s https://quranenc.com/en/home/api | grep -i -E 'condition|modif|credit|version' | head -20            # the 7 conditions
```

**G. Render check (30 seconds)**: save as `t.html` next to the unmodified `UthmanicHafs-v-3.0.ttf` (or v2.0) and open in Chrome, Safari and a phone:

```html
<meta charset="utf-8"><style>
@font-face{font-family:KFGQPC;src:url(UthmanicHafs-v-3.0.ttf)}
p{font:36px/2.2 KFGQPC;direction:rtl}</style>
<p>يَٰٓأَيُّهَا ٱلَّذِينَ ءَامَنُواْ ٱجۡتَنِبُواْ كَثِيرٗا مِّنَ ٱلظَّنِّ إِنَّ بَعۡضَ ٱلظَّنِّ إِثۡمٞۖ</p>
```

No empty boxes and open tanween marks (`ٗ`, `ٞ`) on `كَثِيرٗا` and `إِثۡمٞ` means the font and the data release match.

## 10. What I could not verify

- The text actually served by `api.quranpedia.net/v1/mushafs/1/...` and `/2/...` today (blocked); conclusions about ids come from the stored text, git history and Quranpedia's dump metadata as captured by `risan/quran-json`.
- Whether S1 equals a Complex release byte for byte; contents and open-tanween encoding of the Complex's `UthmanicHafs_v2-0` data; whether `UthmanicHafs-v-3.0` is published by the Complex.
- Whether mp3quran has `ayat_timing` for any Muallim read, and whether it added a Husary Muallim after the snapshot.
- The Complex's reuse terms for audio, and the exact text of its Digital Mushaf and font-site licences beyond what is embedded in the TTF.
- The licence of Quranpedia's translation id 1947 compared with QuranEnc's seven conditions.
- Rendering on real Android and iOS devices.

## Appendix A: per-verse comparison (74 verses)

Columns: word counts (ours / KFGQPC), counts in the KFGQPC text of alef wasla, U+06E1 and open-tanween code points (all absent from ours), whether the letter skeleton is the same, and other differences. Source: `compare_final.csv` (`/tmp/claude-0/r4/comparison_final.csv`) generated by `compare_final.py`. Every verse is "Exact: no".

| # | Ref | Words ours/KFGQPC | ٱ wasla (KFGQPC) | ۡ U+06E1 (KFGQPC) | Open tanween (KFGQPC) | Rasm same | Other differences |
|---|---|---|---|---|---|---|---|
| 1 | 2:83 | 29/29 | 7 | 16 | 3 | NO | maddah ×2; silent-alef واْ ×3; extra shadda ×2 |
| 2 | 2:153 | 12/10 | 6 | 2 | 0 | NO | maddah ×1; silent-alef واْ ×2; waqf spaced ×1 |
| 3 | 2:172 | 15/14 | 2 | 5 | 0 | yes | maddah ×1; silent-alef واْ ×3 |
| 4 | 2:220 | 32/26 | 8 | 19 | 3 | NO | maddah ×2; kashida ×1; extra shadda ×1; waqf spaced ×6 |
| 5 | 2:261 | 26/24 | 4 | 4 | 2 | yes | maddah ×1; iqlab/low meem ×2; extra shadda ×2; waqf spaced ×2 |
| 6 | 2:262 | 25/24 | 2 | 12 | 2 | yes | maddah ×2; silent-alef واْ ×1; extra shadda ×1; waqf spaced ×1 |
| 7 | 3:103 | 36/34 | 6 | 21 | 4 | yes | maddah ×2; silent-alef واْ ×3; small waw/yeh ×2; extra shadda ×2; waqf spaced ×2 |
| 8 | 3:134 | 14/13 | 9 | 6 | 0 | yes | maddah ×2; waqf spaced ×1 |
| 9 | 3:139 | 9/9 | 1 | 5 | 0 | yes | silent-alef واْ ×2; extra shadda ×1 |
| 10 | 3:159 | 34/30 | 9 | 21 | 1 | yes | silent-alef واْ ×1; extra shadda ×1; waqf spaced ×4 |
| 11 | 4:1 | 31/28 | 8 | 8 | 6 | yes | maddah ×3; silent-alef واْ ×2; small waw/yeh ×1; extra shadda ×2; waqf spaced ×2 |
| 12 | 4:36 | 35/33 | 15 | 21 | 3 | NO | silent-alef واْ ×2; small waw/yeh ×1; iqlab/low meem ×1; kashida ×1; waqf spaced ×2 |
| 13 | 4:58 | 28/26 | 6 | 9 | 1 | yes | maddah ×2; silent-alef واْ ×2; small waw/yeh ×1; iqlab/low meem ×1; waqf spaced ×2 |
| 14 | 4:86 | 16/15 | 1 | 4 | 1 | yes | maddah ×2; silent-alef واْ ×1; waqf spaced ×1 |
| 15 | 4:135 | 42/38 | 7 | 17 | 2 | NO | maddah ×5; silent-alef واْ ×5; small waw/yeh ×1; waqf spaced ×3 |
| 16 | 5:2 | 59/52 | 19 | 30 | 2 | NO | maddah ×5; silent-alef واْ ×7; kashida ×1; extra shadda ×2; waqf spaced ×6 |
| 17 | 5:8 | 31/26 | 6 | 10 | 0 | NO | maddah ×3; silent-alef واْ ×5; iqlab/low meem ×1; kashida ×1; waqf spaced ×4 |
| 18 | 5:119 | 27/24 | 6 | 14 | 2 | yes | maddah ×1; silent-alef واْ ×1; extra shadda ×1; waqf spaced ×3 |
| 19 | 6:38 | 24/22 | 2 | 9 | 3 | yes | maddah ×3; extra shadda ×1; waqf spaced ×2 |
| 20 | 7:26 | 22/19 | 2 | 10 | 3 | yes | maddah ×1; waqf spaced ×2 |
| 21 | 7:31 | 18/16 | 2 | 6 | 1 | yes | maddah ×2; silent-alef واْ ×3; small waw/yeh ×1; waqf spaced ×1 |
| 22 | 9:71 | 27/24 | 9 | 16 | 2 | NO | maddah ×3; small waw/yeh ×1; waqf spaced ×3 |
| 23 | 9:108 | 26/23 | 3 | 6 | 2 | yes | silent-alef واْ ×1; extra shadda ×1; waqf spaced ×3 |
| 24 | 9:119 | 9/8 | 4 | 0 | 0 | yes | maddah ×1; silent-alef واْ ×3 |
| 25 | 9:128 | 14/14 | 1 | 9 | 3 | yes | maddah ×1; extra shadda ×2 |
| 26 | 13:28 | 12/11 | 4 | 5 | 0 | yes | silent-alef واْ ×1; waqf spaced ×1 |
| 27 | 14:7 | 12/11 | 0 | 7 | 1 | yes | waqf spaced ×1 |
| 28 | 16:78 | 16/15 | 4 | 11 | 1 | NO | iqlab/low meem ×1; kashida ×2; extra shadda ×1; waqf spaced ×1 |
| 29 | 16:127 | 15/14 | 2 | 9 | 1 | yes | extra shadda ×1; waqf spaced ×1 |
| 30 | 17:23 | 27/26 | 2 | 10 | 3 | yes | maddah ×4; extra shadda ×2; waqf spaced ×1 |
| 31 | 17:24 | 12/12 | 4 | 5 | 1 | yes | extra shadda ×1 |
| 32 | 17:26 | 10/10 | 4 | 7 | 0 | yes | small waw/yeh ×1 |
| 33 | 17:34 | 19/17 | 4 | 10 | 1 | NO | silent-alef واْ ×2; small waw/yeh ×1; kashida ×1; waqf spaced ×2 |
| 34 | 17:37 | 14/13 | 3 | 8 | 1 | yes | waqf spaced ×1 |
| 35 | 17:53 | 18/16 | 3 | 6 | 2 | yes | silent-alef واْ ×1; extra shadda ×2; waqf spaced ×2 |
| 36 | 18:95 | 12/12 | 0 | 8 | 1 | yes |  |
| 37 | 20:14 | 11/11 | 3 | 3 | 0 | NO | maddah ×4 |
| 38 | 20:46 | 8/7 | 0 | 1 | 0 | yes | maddah ×2; waqf spaced ×1 |
| 39 | 20:114 | 19/17 | 4 | 12 | 1 | yes | maddah ×1; small waw/yeh ×1; extra shadda ×1; waqf spaced ×2 |
| 40 | 20:131 | 19/18 | 2 | 14 | 2 | NO | maddah ×1; small waw/yeh ×1; extra shadda ×1; waqf spaced ×1 |
| 41 | 21:107 | 5/5 | 0 | 4 | 1 | yes | maddah ×1; extra shadda ×1 |
| 42 | 23:8 | 5/5 | 1 | 4 | 0 | yes |  |
| 43 | 24:22 | 29/26 | 8 | 15 | 1 | NO | maddah ×2; silent-alef واْ ×2; extra shadda ×1; waqf spaced ×3 |
| 44 | 24:27 | 20/18 | 1 | 10 | 1 | yes | maddah ×2; silent-alef واْ ×4; extra shadda ×1; waqf spaced ×1 |
| 45 | 25:63 | 12/12 | 4 | 6 | 2 | yes | silent-alef واْ ×1 |
| 46 | 27:18 | 20/19 | 3 | 12 | 1 | yes | maddah ×3; silent-alef واْ ×1; small waw/yeh ×1 |
| 47 | 28:25 | 28/26 | 4 | 16 | 1 | NO | maddah ×3; small waw/yeh ×1; waqf spaced ×2 |
| 48 | 28:26 | 12/10 | 4 | 11 | 0 | NO | maddah ×1; kashida ×2; waqf spaced ×1 |
| 49 | 29:45 | 24/21 | 8 | 11 | 0 | NO | maddah ×2; waqf spaced ×3 |
| 50 | 31:12 | 20/18 | 3 | 11 | 1 | yes | small waw/yeh ×1; waqf spaced ×2 |
| 51 | 31:14 | 17/17 | 3 | 11 | 1 | yes | small waw/yeh ×2 |
| 52 | 31:18 | 17/16 | 2 | 5 | 2 | yes | waqf spaced ×1 |
| 53 | 33:21 | 17/17 | 5 | 7 | 2 | NO | maddah ×1; silent-alef واْ ×1; extra shadda ×2 |
| 54 | 33:41 | 8/7 | 3 | 2 | 2 | yes | maddah ×1; silent-alef واْ ×2 |
| 55 | 33:56 | 15/13 | 3 | 2 | 0 | yes | maddah ×2; silent-alef واْ ×3; small waw/yeh ×1; waqf spaced ×1 |
| 56 | 33:59 | 24/21 | 3 | 10 | 2 | yes | maddah ×3; extra shadda ×2; waqf spaced ×2 |
| 57 | 39:9 | 26/24 | 5 | 13 | 2 | NO | maddah ×3; silent-alef واْ ×2; small waw/yeh ×1; waqf spaced ×2 |
| 58 | 39:10 | 25/21 | 5 | 7 | 2 | yes | silent-alef واْ ×3; waqf spaced ×3 |
| 59 | 41:34 | 18/17 | 5 | 7 | 2 | yes | small waw/yeh ×2; waqf spaced ×1 |
| 60 | 49:10 | 11/10 | 3 | 9 | 1 | yes | silent-alef واْ ×2; waqf spaced ×1 |
| 61 | 49:11 | 43/39 | 7 | 20 | 4 | yes | maddah ×7; silent-alef واْ ×3; extra shadda ×6; waqf spaced ×3 |
| 62 | 49:12 | 36/31 | 7 | 11 | 5 | yes | maddah ×1; silent-alef واْ ×4; extra shadda ×3; waqf spaced ×4 |
| 63 | 57:23 | 16/15 | 1 | 7 | 1 | NO | maddah ×1; silent-alef واْ ×1; extra shadda ×1; waqf spaced ×1 |
| 64 | 58:11 | 33/30 | 11 | 10 | 2 | yes | maddah ×2; silent-alef واْ ×6; waqf spaced ×2 |
| 65 | 65:3 | 24/21 | 3 | 11 | 2 | yes | maddah ×1; small waw/yeh ×2; waqf spaced ×3 |
| 66 | 68:4 | 4/4 | 0 | 0 | 1 | yes |  |
| 67 | 74:4 | 2/2 | 0 | 1 | 0 | yes |  |
| 68 | 76:8 | 7/7 | 1 | 2 | 2 | yes | small waw/yeh ×1 |
| 69 | 76:9 | 10/10 | 1 | 4 | 1 | yes | maddah ×1 |
| 70 | 90:14 | 6/6 | 0 | 4 | 3 | yes |  |
| 71 | 90:17 | 9/9 | 3 | 5 | 0 | yes | silent-alef واْ ×1 |
| 72 | 93:9 | 4/4 | 1 | 3 | 0 | yes |  |
| 73 | 98:5 | 17/16 | 5 | 4 | 0 | NO | maddah ×3; silent-alef واْ ×3; waqf spaced ×1 |
| 74 | 104:1 | 4/4 | 0 | 1 | 2 | yes | extra shadda ×2 |

### `verify_arabic.py` (run from `backend/session_moral_context/content`)

```python
#!/usr/bin/env python3
"""Compare knowledge-bank verse items with a KFGQPC UthmanicHafs data file (JSON).

Usage (from backend/session_moral_context/content):
    python3 verify_arabic.py hafsData_v18.json [items_dir]
Exit 1 if any verse is not an exact match (after dropping the end-of-ayah number)."""
import glob
import json
import re
import sys
import unicodedata

WASLA = chr(0x0671)            # alef wasla: used by KFGQPC Hafs, absent from simple/imlaei text
NBSP = chr(0x00A0)
AYAH_MARK = chr(0x06DD)        # optional end-of-ayah sign before the number
DIGITS = f'[{chr(0x0660)}-{chr(0x0669)}]'          # Arabic-Indic digits
END_NUMBER = re.compile(f'[{NBSP} ]*{AYAH_MARK}?[{NBSP} ]*{DIGITS}+$')

data = sys.argv[1]
items = sys.argv[2] if len(sys.argv) > 2 else 'items'

K = {}
for r in json.load(open(data, encoding='utf-8-sig')):
    K[(int(r.get('sura_no') or r['sora']), int(r['aya_no']))] = r['aya_text']


def strip_end(t):
    """Drop the ayah number (NBSP + optional U+06DD + Arabic-Indic digits) at the end."""
    return END_NUMBER.sub('', t).strip()


bad = 0
for f in sorted(glob.glob(f'{items}/*.json')):
    for it in json.load(open(f, encoding='utf-8')):
        if it['type'] != 'verse':
            continue
        k = (it['surah'], it['ayah'])
        want, have = strip_end(K[k]), it['arabic_text']
        if have == want:
            continue
        bad += 1
        nfc_equal = unicodedata.normalize('NFC', have) == unicodedata.normalize('NFC', want)
        print(f'{k[0]}:{k[1]} MISMATCH{" (NFC-equal)" if nfc_equal else ""}'
              f' wasla in file={WASLA in want} in item={WASLA in have}')
print(f'{bad} mismatching verse(s)')
sys.exit(1 if bad else 0)
```

## Appendix B: `cut_ayah_clips.py` (tested offline with a synthetic file; not tested against live mp3quran data)

```python
#!/usr/bin/env python3
"""Cut per-ayah mp3 clips out of an mp3quran.net surah file using its ayat_timing data.

  python3 cut_ayah_clips.py --read 114 --server https://server10.mp3quran.net/minsh/Almusshaf-Al-Mo-lim/ \
      --out ../static/quran 2:153 49:12 ...
Offline test: --timing-json t.json --surah-mp3 file.mp3 (skips the network).
Timing JSON (mp3quran v3): list of {"ayah": int, "start_time": ms, "end_time": ms, ...}; ayah 0 may be the intro.
Needs ffmpeg on PATH. Writes SSSAAA.mp3 (same names as the everyayah clips)."""
import argparse, json, re, subprocess, sys, urllib.request
from pathlib import Path

UA = 'AlSadiq-curation/0.1'
TIMING = 'https://mp3quran.net/api/v3/ayat_timing?surah={s}&read={r}'
PAD_BEFORE, PAD_AFTER = 0.05, 0.15          # seconds of air around an ayah

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--read', type=int); p.add_argument('--server')
    p.add_argument('--out', required=True); p.add_argument('--cache', default='/tmp/mp3quran-cache')
    p.add_argument('--timing-json'); p.add_argument('--surah-mp3')
    p.add_argument('refs', nargs='+', metavar='SURAH:AYAH')
    a = p.parse_args()
    out, cache = Path(a.out), Path(a.cache); out.mkdir(parents=True, exist_ok=True); cache.mkdir(parents=True, exist_ok=True)
    by_surah = {}
    for ref in a.refs:
        m = re.fullmatch(r'(\d{1,3}):(\d{1,3})', ref)
        if not m: sys.exit(f'bad reference {ref!r}')
        by_surah.setdefault(int(m[1]), []).append(int(m[2]))
    for s, ayat in sorted(by_surah.items()):
        timing = json.load(open(a.timing_json)) if a.timing_json else json.loads(get(TIMING.format(s=s, r=a.read)))
        t = {int(x['ayah']): (x['start_time'] / 1000, x['end_time'] / 1000) for x in timing if int(x['ayah']) >= 1}
        src = Path(a.surah_mp3) if a.surah_mp3 else cache / f'{a.read}_{s:03d}.mp3'
        if not src.exists():
            src.write_bytes(get(f'{a.server.rstrip("/")}/{s:03d}.mp3'))
        for n in ayat:
            if n not in t: sys.exit(f'no timing for {s}:{n}')
            start, end = max(0, t[n][0] - PAD_BEFORE), t[n][1] + PAD_AFTER
            dest = out / f'{s:03d}{n:03d}.mp3'
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{start:.3f}', '-to', f'{end:.3f}', '-i', str(src),
                            '-vn', '-c:a', 'libmp3lame', '-b:a', '128k', '-ar', '44100', '-map_metadata', '-1', str(dest)], check=True)
            dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(dest)],
                                       capture_output=True, text=True).stdout)
            print(f'ok {dest.name} {dur:.2f}s (expected {end - start:.2f}s)')

if __name__ == '__main__':
    main()
```

## Appendix C: file fingerprints

| File | sha256 |
|---|---|
| `hafsData_v18.json` (S1) | `5d8bb91726e482839d0057633cb1973031e4d706fa9604eea5e08892f20ba140` |
| `hafsData_v18.csv` | `e6a4df4f2dedf2ba432a3d10384a0fac30d1496e097ba21a70acec5e417bacf6` |
| `hafs_smart_v8.json` (S2) | `0f7fa7edfb99c7c2b46082efd02d896de35369bcea6f3043b1389d1dc2375d13` |
| `risan/quran-json data/quranpedia/qpc-hafs.json` (S4) | `0136b913aeb5a6a0389681f988215791ddd848c4347f7cf5e9d2574db7f1da49` |
| `quran_text_data/hafs.json` from PyPI `quran-text 0.1.0` (S5) | `31186b3ac554ea8d5db1dbc1f67ac5a6d3bd99a62091d04ff73f39be18bf2568` |
| `UthmanicHafs_v2-0.zip` (official, per the archive) | `a7b0e5591945712ec5e4d6142938ae4d1e9b49bdc89dff06222789bfebdfd72c` |
