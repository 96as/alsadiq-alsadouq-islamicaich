# R1: HadeethEnc, QuranEnc and the Islamic Content MCP server

Research agent 1 of 5. Branch `hk/01-knowledge-bank`. Date: 4 Oct 2026. Nothing in the repo was changed except this file.

## 0. Bottom line (read this first)

1. **HadeethEnc does not give a full citation by itself.** Per record it gives `attribution` ("Narrated by Bukhari", "متفق عليه"), a bare `grade` ("Authentic", "صحيح") and a bibliography field `reference`. It gives **no hadith number field, no named grader, and no per-record URL field**. But the Arabic `reference` field contains `صحيح البخاري (9/ 2) (6864)` style strings for many records, so **book + number can be extracted by regex for about 55% of the Sahihayn-attributed records** (1,392 of 2,508 in a 26 Sep 2026 snapshot). The per-hadith page URL is `https://hadeethenc.com/<lang>/browse/hadith/<id>` (confirmed for `ar`).
2. **`grader` cannot come from HadeethEnc** except by convention. For Bukhari/Muslim hadiths the compiler is the grader (the same convention our `content/README.md` example already uses: `"grader":"البخاري"`). For the other 30% of the corpus (non-Sahihayn), only about 10 of 1,066 records name a grader. So **restrict HadeethEnc-sourced hadith to Sahihayn items**, and send the rest to dorar.net by hand.
3. **"Authentic only" is not guaranteed.** The snapshot contains one record graded `ضعيف` (id 65065, Tirmidhi) and one mixed grade (id 10877). Gate on an exact grade, never on the platform name.
4. **Our schema rejects HadeethEnc today.** `ContentItem.clean()` forces hadith `source_site` to `dorar.net` or `shamela.ws`, and verse `source_site` to `quranpedia.net` or `qurancomplex.gov.sa`. Using HadeethEnc/QuranEnc as the cited source needs a task-01 migration (new `source_site` choices) *and* an organiser answer (question Q1).
5. **The Association's own usage policy allows exactly our use** (store, index, "RAG and AI assistants", commercial or not, no prior permission) on conditions: do not alter the text, cite the source and version, keep metadata, do not present summaries or AI text as the original (section 2.7).
6. **`mcp.islamiccontent.org/mcp` is a real remote MCP server** (Streamable HTTP, free, read-only, no auth, 11 tools). Two other hackathon teams already use it. It does **not** return hadith numbers (`reference` is missing), so for curation use the REST API with `language=ar` for numbers and the MCP for topic search. One team got Cloudflare error 1010 on a direct POST, so server-to-server use from our LiveKit container is **untested and risky** (section 4.4).
7. **Do not call it from the child-facing voice agent at runtime.** It would bypass our reviewed bank ("no source, no answer" means only `seeded`/`reviewed` items). Use it at build time to fill the bank (section 6).
8. **Network reality:** every Association host is blocked from this container (403 on CONNECT). No live call was made by me. Everything below comes from package sources, public GitHub repos and measured third-party data, and is marked accordingly. Section 8 has the exact commands for the lead's laptop.

## 1. Method, legend, and what was unreachable

Evidence marks used in tables:

- **VERIFIED** = read by me in package source code, official docs text, or a data snapshot I downloaded and analysed. The source ID in brackets is listed in Appendix A.
- **VERIFIED (3P)** = verified in a third-party repo's code or measured data (not Association first-party). Strong evidence, still check live.
- **NEEDS-LIVE-CHECK** = inferred, from a search snippet only, or contradicted between sources.

Unreachable from this container (all returned `403 CONNECT tunnel failed` or `EGRESS_BLOCKED`; I did not try to get around it): `hadeethenc.com`, `quranenc.com`, `mcp.islamiccontent.org`, `islamiccontent.sa`, `documenter.getpostman.com`, `glama.ai`, `huggingface.co`, `app.alphaneural.io`. Reachable: `pypi.org`, `registry.npmjs.org`, `raw.githubusercontent.com`, `github.com` pages through WebFetch, WebSearch.

Most useful finds, all downloadable from here:

- The Association's Python and npm SDKs (`islamic-content-sdk`) and the npm `islamic-content-mcp-server` (exact endpoints and tool schemas).
- The HadeethEnc Postman collection exported as markdown (`islamhouse-dev/hadith-api`), with sample responses.
- A **measured pull of the whole HadeethEnc corpus** (ar 3,574, en 2,328, bn 1,925 hadiths) committed by an unrelated project on 26 Sep 2026. I analysed it in a scratch directory only; none of that text is copied into this repo.
- The Association's usage policy (its GitHub hub README).
- Two hackathon teams' notes on the remote MCP.

## 2. HadeethEnc (hadeethenc.com)

### 2.1 Endpoints

Base: `https://hadeethenc.com/api/v1`. No API key. All GET, JSON. [S2, S3, S4]

| Endpoint | Params | Returns | Status |
|---|---|---|---|
| `/languages` | none | `[{"code":"ar","native":"عربي"}, ...]` | VERIFIED [S2]. Sample in the Postman export lists 17 languages (old). A 26 Sep 2026 pull saw **72** codes (VERIFIED 3P [S6]). Third-party script calls it with a trailing slash `/languages/`. Both forms probably work (NEEDS-LIVE-CHECK). |
| `/categories/list/` | `language` (required) | flat array of every category: `{id, title, hadeeths_count, parent_id}`; `parent_id` is `null` for roots | VERIFIED [S2, S3, S6] |
| `/categories/roots/` | `language` | only the 7 root categories, same shape | VERIFIED [S2] |
| `/hadeeths/list/` | `language`, `category_id` (both required), `page` (default 1), `per_page` (default 20; **100 is honoured**) | `{"data":[{id,title,translations[]}], "meta":{current_page,last_page,total_items,per_page}}`. A category's list **includes its sub-categories' hadiths** (a root's `total_items` equals its `hadeeths_count`). | VERIFIED [S2]; `per_page=100` and the sub-category rule are VERIFIED (3P) [S6] |
| `/hadeeths/one/` | `id`, `language` | the full record (2.2) | VERIFIED [S2, S3] |

Notes:

- There is **no documented search endpoint**. Discovery is by category tree, then filtering `title` client-side. (The remote MCP has a `search` tool, section 4.)
- There is no documented bulk endpoint. Bulk = list every category page, then one call per id (2.8).
- `meta.current_page` and `meta.per_page` are strings, `last_page` and `total_items` are numbers [S3].
- Error bodies and status codes are undocumented. The SDKs just raise on any non-2xx (NEEDS-LIVE-CHECK).

### 2.2 Record fields (`/hadeeths/one/`)

Typed from the Angular client and checked against measured data [S3, S6]:

| Field | Type | Meaning | Notes |
|---|---|---|---|
| `id` | string | HadeethEnc id (stable key) | Ranges seen: 1751 to 66541 |
| `title` | string | short title (a clause of the hadith) | |
| `hadeeth` | string | the matn (text) in the requested language | Arabic includes full tashkeel and usually the narrator lead-in ("عن أبي هريرة رضي الله عنه قال..."). |
| `hadeeth_intro` | string, optional | the narrator lead-in split out ("Abu Hurayrah (may Allah be pleased with him) reported that the Messenger of Allah said:") | Present on about 840 of 2,328 English records. Not in the official docs; found in measured data [S6]. |
| `attribution` | string | takhrij: who recorded it | e.g. `Narrated by Bukhari`, `متفق عليه`, `Agreed upon` |
| `grade` | string | ruling | e.g. `Authentic`, `Authentic hadith`, `صحيح` |
| `explanation` | string | scholarly explanation (**commentary, not scripture**) | |
| `hints` | string[] | "fawaed" (benefits and lessons) | often `[]` in English |
| `categories` | string[] | category ids | |
| `translations` | string[] | language codes available for this id | |
| `words_meanings` | `[{word, meaning}]` | glossary | **Arabic request only** |
| `reference` | string | bibliography, newline separated | **Arabic request only**. Often holds `book (vol/page) (hadith number)`. |
| `hadeeth_ar`, `explanation_ar`, `hints_ar`, `words_meanings_ar`, `attribution_ar`, `grade_ar` | | Arabic parallel fields | Returned alongside a **non-Arabic** request, so one `language=en` call gives English and Arabic together (VERIFIED (3P) [S6]: script comment "hadeeth_ar in every translated pull (measured)"). |

Difference by language (official doc text [S2]): with `language=ar` you get everything (including `words_meanings` and `reference`); with another language you get the translated parts only and **no `reference`** (the English records in the measured data have no `reference` key). So to get numbers you must call `language=ar` for the same id.

Category record: `{id, title, hadeeths_count, parent_id}` [S2].

### 2.3 Does each record give book, number, grade, grader and a stable URL? (the key question)

Our rule (resource package p.3): "Do not attribute a hadith without including its source and an approved authenticity grading in the data." Our `ContentItem` needs `book`, `number`, `grade`, `grader`, `source_url`, `source_site` for a seeded hadith.

| Our field | What HadeethEnc gives | How to fill it | Reliability |
|---|---|---|---|
| `book` | `attribution` (Arabic: `رواه البخاري`, `رواه مسلم`, `متفق عليه`, ...) and the leading name in `reference` | Map by exact-match table: `رواه البخاري` to "Sahih al-Bukhari", `رواه مسلم` to "Sahih Muslim". For `متفق عليه` (both books) pick the book whose number you extract, default Bukhari, and record the Muslim number in review notes. Some `attribution` values are long prose (e.g. id 66511 names both imams and their books); map those by hand. | Good for Sahihayn |
| `number` | **No field.** But `reference` often contains `صحيح البخاري (9/ 2) (6864)` (volume/page, then **hadith number**). Examples from the snapshot: id 2962 gives Bukhari 6864 and Muslim 1678; id 66521 gives Muslim 1955 (I did not verify these against a numbered edition, that is the reviewer's job). Numbering follows Muhammad Fuad Abd al-Baqi (stated in the `reference` of id 2962: "بإضافة ترقيم: محمد فؤاد عبد الباقي"). | Regex on the **Arabic** record (below). Accept only a pure integer in the last parentheses; skip lists like `2788 و 2789`. | See coverage table below |
| `grade` | `grade` ("صحيح", "Authentic hadith"). 3,205 of 3,574 Arabic records are exactly `صحيح`. | Copy as-is for the Arabic; keep English alongside. Accept only `صحيح` for seeded hadith. | Gate on exact value |
| `grader` | **Not provided.** Only ~10 of the 1,066 non-Sahihayn records name one (e.g. "An-Nawawi said: It is a Hasan (sound) Hadīth"). Others say "No judgment by Shaykh Al-Albaani is available". | Sahihayn items: the compiler(s), `البخاري` / `مسلم` / `البخاري ومسلم` (matches `content/README.md`). All others: **do not use HadeethEnc**; take grade and grader from dorar.net by hand. | Convention, needs lead sign-off |
| `source_url` | **No field**, but the canonical page is `https://hadeethenc.com/<lang>/browse/hadith/<id>` (regex in the qatra-app code accepts `ar`; the remote MCP prints this as its `Source:` line). | Build from `id`. | `ar` VERIFIED (3P) [S9]; `en` NEEDS-LIVE-CHECK |
| `source_site` | n/a | would be `hadeethenc.com`. **Not an allowed choice today** (`HADITH_SITES = dorar.net, shamela.ws`). | schema change (Q1) |
| `narrator` | `hadeeth_intro` (English, 840 records) or the first clause of `hadeeth` / `hadeeth_ar` ("عن جابر رضي الله عنه قال:") | parse; or leave blank (field is optional) | semi-manual |

Regex used on the snapshot (tested; it found the numbers above):

```python
import re
PAT = re.compile(r'(صحيح البخاري|صحيح مسلم)\s*\(\s*(\d+)\s*/\s*[^)]*\)\s*\(([^)]*)\)')
# for m in PAT.finditer(record["reference"]): book, _vol, num = m.groups(); keep only if num.strip().isdigit()
```

Measured coverage in the 26 Sep 2026 snapshot (third-party pull, my analysis) [S6]:

| Set | Count |
|---|---|
| Arabic base hadiths | 3,574 |
| with an English translation | 2,328 (65%) |
| with a Bengali translation | 1,925 |
| Arabic records mentioning the Sahihayn in `attribution` | 2,508 (70%) |
| ... of which a Bukhari/Muslim number is extractable | 1,392 (55%); by id band: ids at or above 60000: 965 of 1,265 (76%); under 5000: 256 of 665; 5000 to 9999: 171 of 578 |
| English-available and Sahihayn | 1,680, of which extractable: 622 (37%) |
| Candidate pool for our 38 values (25 relevant categories, English, Sahihayn) | 277, of which extractable: 116 |
| Records graded exactly `صحيح` | 3,205 |
| Records with a non-authentic grade | 1 weak (id 65065), 1 mixed (id 10877) |

Caveat: the Postman sample record 2962 had a bibliography with no numbers, while the Sep 2026 snapshot of the same id has them. The `reference` field is being enriched over time, so re-pull before curating.

The `reference` numbers are the Association's own citation. They must still be checked against a numbered source (dorar.net / shamela.ws page) during human review, because the package says a hadith needs "an approved authenticity grading" and our review ledger needs a human check.

### 2.4 How "attribution" and "grade" are phrased (real values)

From the snapshot [S6]. Counts are records.

English `attribution`: `Narrated by Bukhari & Muslim` 533; `Narrated by Muslim` 453; `Agreed upon` 335; `Narrated by Bukhari` 156 (+ `Narrated by Al-Bukhāri` 65); then Abu Daoud, Ahmad, At-Termedhy/At-Tirmidhi, Ibn Majah, An-Nasaa'i, and many combinations joined by ` - `. Spelling varies for the same book, so **normalise by a mapping table, not by string equality**.

Arabic `attribution`: `متفق عليه` 1,253; `رواه مسلم` 675; `رواه البخاري` 396; `رواه أبو داود` 131; `رواه الترمذي` 95; `رواه أحمد` 80; many combinations. **No number inside the attribution** in the normal case (9 records have digits, in prose).

English `grade`: `Authentic hadith` 1,347; `Authentic` 767; `Good hadith` 98; `Hasan` 49; and long free-text variants ("Sahih/Authentic with its two versions", "An-Nawawi said: ..."). Arabic `grade`: `صحيح` 3,205; `حسن` 275; `حسن لغيره` 13; `صحيحان` 9; `ضعيف` 1; long free text for the rest.

So the grade is a short label, not a "grade + grader" pair.

### 2.5 English and Arabic together

Yes. One call `language=en&id=X` returns English fields plus `*_ar` Arabic fields. English coverage is 65% of the base set, so the pipeline must handle "Arabic only" records (our bank wants both languages for the child UI; use `english_text` blank or skip). 72 languages exist overall; the "50,000+ translated hadiths" in the package is consistent with about 3.6K base hadiths times many languages (NEEDS-LIVE-CHECK: `stats.hadeethenc.com`).

### 2.6 Categories useful for children's values

Tree: 7 roots, 452 categories in English (493 in Arabic). Root titles and English hadith counts (overlapping; a hadith can sit in several): The Noble Qur'an 81; Hadith Sciences 10; The Creed 471; Jurisprudence 1,150; **Virtues and Manners 751**; Da'wah and Hisbah 100; **Seerah and History 213** [S6].

Most useful (English counts from the snapshot; ids are category ids):

- 5/266 Jurisprudence of Ethics: **282 Praiseworthy Morals (83)**, **283 Blameworthy Morals (47)**
- 5/265 Virtues: 273 Dutiful to Parents (10), 274 Kinship Ties (2), 277 Merits of Good Deeds (33), 278 Remembering Allah (25), 280 Heart Acts (13), 270 Knowledge (16)
- 5/267 Manners: 286 Greeting (24), 287 Speaking and Silence (32), 636 Tongue Evils (9), 290 Eating and Drinking (35), 297 Visiting the Sick (9), 296 Sneezing and Yawning, 293 Sleeping, 298 Dressing
- 5/268 Dhikr: 301 Morning and Evening (7), 299/300/302
- 5/269 Heart-Softeners: 314 Acts of Heart (27), 321 Repentance (15), 322 Purification of Souls (21)
- 7/367/406/646 Moral Attributes (55): 648 Generosity (6), 650 Humility (7), 652 Gentleness (5), 653 Forgiveness (2), **654 Mercy (17)**, 659 Compassion, 661 Justice, 662 Forbearance
- 6/325: **341 Animal Rights (10)**, 340 Human Rights (5)
- 4/121: 457 Virtue of Prayer (17), 511 Voluntary Charity (27), 513 Virtue of Fasting (6), 436 Natural Cleanliness Practices (9)
- 3/62: 81 Our Prophet (20)

Suggested starting map from our 38 value slugs to categories is in Appendix B. Treat it as a first filter; confirm by reading titles.

**Deny-list for a children's product** (hadith in these categories need a human age check or should be skipped): 139 Jihad, 128 Prescribed Punishments, 127 Crimes, 124/191 Marriage and 581 Marital Relations, 205/607 Men-Women relations, 63/84 Portents of the Hour, 324 Descriptions of Paradise and Hell, 323 Terrors of the Graves, 83 Barzakh, and the sect/disbelief categories (65, 71). (Category ids and titles are from the Postman sample and the snapshot; counts differ between them.)

### 2.7 Licensing and terms of use

| Statement | Source | Status |
|---|---|---|
| "Contents of the project can be used, with the following terms and conditions: 1. No modification, addition, or deletion of the content. 2. Clearly referring to the publisher and the source (HadeethEnc.com)." | Quoted in the Angular client README [S3] and, as "its own published API terms", in a third-party pull script [S6] | VERIFIED (3P). The original text on hadeethenc.com NEEDS-LIVE-CHECK. |
| The Association's hub policy: you may download, republish, store offline, use in apps and websites, **commercial or non-commercial**, and "for search, indexing, RAG, and AI assistants". No prior permission needed if conditions are met. | `IslamHouse-API/multilingual-quran-hadith-islamic-content-database-api-hub` README (contact admin@islamhouse.com); text identical to the snapshot in [S8] | VERIFIED. Appears first-party: it links the same IslamHouse Postman docs that the package lists on p.9, and gives an IslamHouse contact address. Ask the organisers to confirm (Q9). [S7] |
| Conditions: (1) do not alter the original text; (2) cite IslamHouse/QuranEnc/HadeethEnc and author/translator/publisher; (3) keep version information; (4) update your copy when a newer version is released; (5) send corrections to the platform; (6) no inappropriate ads next to Quran or Hadith. | same [S7] | VERIFIED |
| "A summary, explanation, or AI-generated text must not be presented as the original text issued by our platforms." Summaries are allowed but become your own work and must not be labelled "adapted by HadeethEnc". | same [S7] | VERIFIED |
| Written confirmation for app stores or institutions: email admin@islamhouse.com | same [S7] | VERIFIED |

What this means for us:

- `arabic_text` and `english_text` must be the record's `hadeeth` / `hadeeth_ar` / `hadeeth` (English) **byte for byte** (including diacritics and punctuation). No trimming, no "fixing". A third-party team hashed every field at pull time to prove this.
- `child_explanation_*` is **our** text. Label it as ours in the UI and never as HadeethEnc's.
- Store the retrieval date and API response hash with each item (condition 3 and 4: version and updates). HadeethEnc has no version number in the record, so store `retrieved_at` + SHA-256 of the raw JSON.
- The voice agent paraphrasing a hadith aloud is "AI-generated text". The spoken output must make clear what is the hadith's wording and what is the explanation (this also matches package p.5).
- The package (p.8) says the Association's content is free for individuals and organisations via APIs, the central DB and the MCP server, so there is also an organiser-side permission signal.

### 2.8 Rate limits and bulk download

| Item | Finding | Status |
|---|---|---|
| Rate limit | **Not documented.** Third-party pull of about 7.8K records used 120 ms between requests, 4 concurrent workers, and retry/backoff on HTTP 429 (so 429s are anticipated). The MCP package's tool text says "No strict rate limits" but that text was written by a community developer, not the platform. | NEEDS-LIVE-CHECK. Be polite: at most 4 concurrent, 100 to 200 ms gap, back off on 429. |
| Bulk via API | Fully possible: for each root category call `/hadeeths/list/?per_page=100` until `last_page`, then `/hadeeths/one/` per id, once with `language=ar` (for `reference`, `words_meanings`) and once with `en`. The third-party run produced ar+en+bn (7,827 records, 31 MB) on 26 Sep 2026. | VERIFIED (3P) [S6] |
| Website downloads | The package says "Browse and download: hadeethenc.com". A search snippet says Excel and PDF per language in several parts. | NEEDS-LIVE-CHECK |
| Dataset mirrors | A Hugging Face dataset `quranlab/hadith` is said to include a graded HadeethEnc selection ("3,574 hadith, 72 languages"). Blocked from here; third-party redistribution, licence unknown. | Do not use. Pull from the source for provenance. |
| Offline snapshot | Pull once from the lead's laptop, keep the raw JSON in the gitignored cache (`content/tools/.cache/`), commit only curated items. Re-pull before final curation. | recommendation |

### 2.9 Consequences for our schema and tools

- Add `hadeethenc.com` to `SOURCE_SITE_CHOICES` and `HADITH_SITES` (migration in task 01 only, per AGENTS.md), **if** the organisers confirm HadeethEnc is an approved hadith source (Q1). Otherwise keep dorar/shamela as the cited source and use HadeethEnc only for discovery.
- Natural key `(type, book, number)` fits: `("hadith", "Sahih al-Bukhari", "6864")`.
- Suggest a new tool `tools/fetch_hadeethenc.py <id>...` beside `fetch_verse.py`: calls `ar` and `en`, prints a draft item with `verification_status: "unverified"`, the extracted number, the raw-JSON SHA-256 and `retrieved_at`, and refuses to emit `seeded` unless `grade == "صحيح"`, the book maps cleanly and the number is an integer. Human review then upgrades to `reviewed` through the ledger.

## 3. QuranEnc (quranenc.com)

### 3.1 Endpoints

Base: `https://quranenc.com/api/v1`. No key. [S4, S8, S12]

| Endpoint | Returns | Status |
|---|---|---|
| `GET /translations/list[/{language}]?localization={iso}` | translations catalogue. Official docs (search snippet) say fields `key`, `language_iso_code`, `version`, `last_update`, `title`, `description`. The Python SDK README guesses a different shape (`translation_number`, `translation_key`, ...). | URL VERIFIED [S4]; **field names NEEDS-LIVE-CHECK** (two sources disagree) |
| `GET /translation/sura/{translation_key}/{sura}` | `{"result":[{id, sura, aya, translation, footnotes, ...}]}`; sura 1 to 114 | VERIFIED (3P): a build script reads `json['result']` and `r['sura'], r['aya'], r['translation'], r.get('footnotes')` [S8] |
| `GET /translation/aya/{translation_key}/{sura}/{aya}` | `{"result":{...same fields...}}` | VERIFIED [S4] (SDK README); docs snippet shows the example `/translation/aya/english_saheeh/1/1` |
| `GET https://quranenc.com/en/home/d/csv/{translation_key}` | full translation as CSV, with a metadata header block that includes the version (e.g. `v1.0.0-...`) | VERIFIED (3P) [S8] |
| `GET https://quranenc.com/en/home` | HTML cards with `V<version>` and `/browse/<key>` links (used to read versions) | VERIFIED (3P) [S8] |
| `POST /translations/note` | send a correction (name, email, sura, aya, note, translation_key, ...) | VERIFIED [S4] |
| Browse pages | `https://quranenc.com/<lang>/browse/<translation_key>[/<sura>]` | VERIFIED [S8, S12] |
| Audio | `https://d.quranenc.com/data/audio/<translation_key>/<SSS><AAA>.mp3` | VERIFIED [S4] (SDK code). It is keyed by *translation*, so it is audio of the translation, **not Arabic recitation**. Not usable for our recitation rule. |

The `result` wrapper is not in the docs snippet (which says "an array / object with sura, aya, translation, footnotes"), but both the SDKs and a working build script use `result`. Treat as VERIFIED (3P).

### 3.2 Translations vs tafsir, keys

From a catalogue of 32 QuranEnc editions published 2026-10-02 with versions and credits [S8]:

| `translation_key` | Kind | Credit on QuranEnc | Version |
|---|---|---|---|
| `english_saheeh` | translation of meanings (the Saheeh International text) | Noor International Center | 1.1.2 |
| `english_rwwad` | translation of meanings | Rowwad Translation Center | 1.0.19 |
| `arabic_moyassar` | **tafsir** (Al-Tafsir Al-Muyassar) | catalogue gives only the title; a search snippet of the QuranEnc page says it is issued by the King Fahd Complex (NEEDS-LIVE-CHECK) | 1.0.0 |
| `arabic_mokhtasar` | **tafsir** (Al-Mukhtasar in Interpreting the Noble Quran) | publisher not stated in the catalogue (NEEDS-LIVE-CHECK) | 1.0.0 |
| `arabic_yaseer` | tafsir (Al-Yaseer) | | 1.0.22 |
| `arabic_nafahat` | tafsir (An-Nafahat Al-Makkiyyah, al-Shawi) | | 1.0.0 |

The same catalogue lists 28 more editions in about 19 languages (French `french_hameedullah`, Spanish, German, Turkish, Urdu, etc.). Versions change; read the live list.

Important for our content rules:

- `arabic_moyassar` and `arabic_mokhtasar` are **modern (contemporary) tafsirs** by their titles and publication, not works of the first three centuries (my reading; confirm with Q4). The package (p.3) allows tafsir only from "any Islamic sources from the first three Islamic centuries, or dorar.net/tafseer". So they probably **cannot be seeded as `tafsir` items** (Q4). They are fine as reviewer aids.
- The English translations are "translations of meanings", approved by the package (p.3 and the note on p.11: for approved translations rely on the Association's platforms).
- Our bank's 74 verses use "Saheeh International" via quranpedia.net. QuranEnc `english_saheeh` is the same translation published by Noor International Center; use it as an **independent cross-check** of `english_text` (expect small orthographic differences, e.g. "Allāh" vs "Allah"), not as a replacement.

### 3.3 Uthmani Arabic text?

- The remote MCP's `get_quran_verses` with `language=ar` returned "the Uthmani Arabic verse line, then a Muyassar tafsir line" for each ayah (observed by a team using the Claude connector) [S9]. The npm MCP client code reads `aya.arabic_text` from `translation/sura` results [S5]. This suggests the sura JSON contains an `arabic_text` field. **NEEDS-LIVE-CHECK** (the official snippet lists only `sura, aya, translation, footnotes`).
- Which edition that Arabic is (King Fahd Complex Hafs?) is **not documented** in anything I could read. A third-party team treats the King Fahd text only as a verification tool.
- Our rule: verse `arabic_text` must be the exact Uthmani text from quranpedia.net or qurancomplex.gov.sa. **So keep verse text from those two sites, and use QuranEnc only for translations and as a cross-check.**

### 3.4 Terms

Same Association policy as HadeethEnc, plus the QuranEnc special rules [S7]: do not modify, add to or delete from the translation text; name QuranEnc.com as publisher and source; **include the translation version number** when republishing; keep version metadata; send notes to QuranEnc; update when a new version is released; no inappropriate ads next to translations. The site pages say the same ("Contents of the translations can be downloaded and re-published, with the following terms and conditions ...", from search snippets of `quranenc.com/*/browse/*`). Another team displays: "QuranEnc.com · الإصدار [version] · النص معروض دون تعديل".

Rate limit: undocumented. One team got HTTP 429 when fetching the docs page [S9]. A build script used 150 ms between sura calls without issue [S8]. NEEDS-LIVE-CHECK.

### 3.5 Use in our project

- Fill `translation_name` with the exact QuranEnc title and **store the version** (for example "Saheeh International (QuranEnc english_saheeh v1.1.2)").
- Cross-check: for each of the 74 verses, compare `english_text` to QuranEnc `english_saheeh` and list differences for the lead. Do not overwrite reviewed items.
- Footnotes: QuranEnc `footnotes` are the translator's notes, not Quran text; if shown they must be labelled as notes.

## 4. The Islamic Content MCP server

### 4.1 There are two different things called "Islamic Content MCP"

| | **Remote server** `https://mcp.islamiccontent.org/mcp` | **npm package** `islamic-content-mcp-server` 1.1.11 |
|---|---|---|
| Who | Operated by the Association (named in the resource package, p.9: "An MCP server for AI models is available for the first six platforms: mcp.islamiccontent.org") | Community developer "2yousefreda" "for the Association" (README says "official"; maintainer email is a personal address). ISC licence in README, MIT in `glama.json`. Repo `github.com/2yousefreda/islamic-content-mcp`. |
| Transport | Streamable HTTP, stateless, read-only, **no auth** [S9, S10] | **stdio** only (`npx -y islamic-content-mcp-server`) [S5] |
| Tools | 11: `search`, `fetch`, `list_languages`, `get_quran_verses`, `list_quran_translations`, `get_quran_audio`, `get_hadith`, `browse_hadith_categories`, `browse_library`, `get_library_item`, `list_library_categories` | 7 consolidated tools with an `action` parameter: `quran_services`, `islamhouse_quran`, `hadeethenc_services`, `islamhouse_library`, `bayan_al_islam`, `risalat_al_haramain`, `al_montaka`. It is a wrapper over the SDK (so it just calls the REST APIs). |
| Branches | QuranEnc, HadeethEnc, IslamHouse (service page lists 3) | QuranEnc, HadeethEnc, IslamHouse, Bayan al-Islam, Risalat al-Haramain, Al-Montaka |
| Status | VERIFIED (3P) from two teams' notes; **we have not touched it** | VERIFIED by reading the package [S5] |
| Pages | service/docs `https://mcp.islamiccontent.org/`, terms `https://mcp.islamiccontent.org/terms.html` [S9] | none |

The package says the MCP covers "the first six platforms"; the live service page (as read by another team) lists only three branches. **Mismatch, ask (Q6).**

The npm server's tool descriptions were clearly written by an LLM and contain errors. Example: it advertises `translationKey` "en_sahih" and says hadith details return `translations: []`, while the real key is `english_saheeh` and the real field is `translations` of language codes. Do not trust the schema text; read `tools/list` from the live server.

### 4.2 Remote server facts

| Fact | Source | Status |
|---|---|---|
| Endpoint `https://mcp.islamiccontent.org/mcp`, protocol Streamable HTTP, "stateless, read-only, no authentication", free | Two independent repos: qatra-app `Source-acquisition.md`/`mcp-evidence.json` [S9] and mazann `SOURCE_CONNECTOR_NOTES.md` [S10] | VERIFIED (3P) |
| Works with a plain stateless JSON-RPC `tools/call` POST (no `initialize`), headers `accept: application/json, text/event-stream`, `content-type: application/json`; answer is JSON or SSE `data:` lines | mazann `mcp-client.mjs` (Node `fetch`, 12 s timeout) [S10] | VERIFIED (3P) |
| Full handshake also works in a Claude connector (qatra's Claude Code cloud session had tools `mcp__Islamic_Content__*`) | [S9] | VERIFIED (3P) |
| Calls observed: `get_hadith {"id":66511,"language":"ar"}`, `get_quran_verses {"surah":112,"language":"ar"}`, `get_hadith` for id 3016, `search` for "الأمانة" | [S9, S10] | VERIFIED (3P) |
| Tool argument schemas | nobody captured `tools/list` | **NEEDS-LIVE-CHECK** (Q: capture and commit it) |

### 4.3 Output format (text, not JSON)

Observed for `get_hadith` [S9]: a title line; an `[EXACT] ... [/EXACT]` block (the matn, with the narrator chain); an `[ATTRIBUTION] ... [/ATTRIBUTION]` block with lines `Narrator: <takhrij>` and `Grade: <grade>`; a `[COMMENTARY] ... [/COMMENTARY]` block (explanation and benefits); a `Source: https://hadeethenc.com/ar/browse/hadith/<id>` line; a sentence listing the published languages (60 for id 66511).

Mapping to the REST fields: `[EXACT]` = `hadeeth`; `Narrator:` = `attribution` (it is the takhrij such as "متفق عليه", **not a narrator name**: a team noticed this); `Grade:` = `grade`; `[COMMENTARY]` = `explanation` + `hints`.

Observed for `get_quran_verses` (`language=ar`) [S9]: header `[Surah 112, translation "arabic_moyassar"]`, one `[EXACT]` block with per ayah a marker line `[112:1]`, the Uthmani verse line, then a Muyassar tafsir line, and `Source: https://islamenc.com/ar/quran/112`.

Good design: the platform itself separates scripture (`[EXACT]`) from commentary, which matches the package's rule to "distinguish authoritative religious text from generated explanation".

### 4.4 Known problems

1. **Cloudflare error 1010 `browser_signature_banned`** (HTTP 403) on a direct `initialize` POST from one team's Codex environment ("do not retry", [S9]). Another team's Node `fetch` works [S10]. LiveKit uses `httpx` (default `python-httpx` user agent). It is **unknown** whether our container will be blocked. Do not fake a browser signature. Test with the real client, and if blocked ask the organisers to allowlist or to tell us the intended client identity (Q3).
2. `search` is a federated search; one team saw the Quran branch time out after 5 seconds while the hadith branch answered [S10]. Partial results are possible. Latency is unsuited to live voice.
3. `list_quran_translations` with `language: ar` returned "No translations found" [S10]. Do not rely on it to find tafsir keys.
4. `get_hadith` output has **no `reference`/number** and no upstream version [S10 notes: "the connector does not return the upstream version in the record"]. For numbers use the REST API with `language=ar`.
5. MCP terms: one team read `terms.html` as "programmatic, read-only, free access" without an explicit grant of reuse rights for source texts [S9]. NEEDS-LIVE-CHECK. The Association's hub policy (2.7) is the reuse grant.

### 4.5 How to use it

**Claude Code (curation sessions).** Same format as the repo's existing `.mcp.json` entry for `second-brain` (`"type": "http"`):

```json
{
  "mcpServers": {
    "islamic-content": {
      "type": "http",
      "url": "https://mcp.islamiccontent.org/mcp"
    }
  }
}
```

or `claude mcp add --transport http islamic-content https://mcp.islamiccontent.org/mcp`. No headers or keys. (Not added by me; `.mcp.json` untouched.) NEEDS-LIVE-CHECK: whether it connects from the lead's laptop.

**Cloud sessions.** This container cannot reach the host, but another team reports a connector working in a Claude Code cloud session. If the lead adds the server as a custom connector at https://claude.ai/customize/connectors (URL above) and starts a new session, tools like `mcp__Islamic_Content__get_hadith` may appear without opening the container's egress. NEEDS-LIVE-CHECK.

**LiveKit agent (if ever wanted).** `livekit-agents==1.5.1` (the version pinned in `backend/requirements.agent.txt`) has built-in support, verified in `livekit/agents/llm/mcp.py` [S11]. Needs the extra: `livekit-agents[mcp]` (adds `mcp>=1.24,<2`).

```python
from livekit.agents import Agent, mcp

agent = Agent(
    instructions=...,
    mcp_servers=[
        mcp.MCPServerHTTP(
            "https://mcp.islamiccontent.org/mcp",       # '/mcp' suffix auto-selects streamable HTTP
            transport_type="streamable_http",
            allowed_tools=["get_hadith", "get_quran_verses"],  # never expose search/library to a child
            timeout=5, client_session_timeout_seconds=8,
        )
    ],
)
```

Signature (VERIFIED in source): `MCPServerHTTP(url, transport_type=None, allowed_tools=None, headers=None, timeout=5, sse_read_timeout=300, client_session_timeout_seconds=5, *, tool_result_resolver=None)`. The default `tool_result_resolver` returns the raw MCP content as a JSON string to the LLM.

**SDK instead of MCP (build-time scripts).** `pip install islamic-content-sdk` (PyPI 1.0.7, `requests` only) wraps the same REST endpoints (`sdk.hadeethenc.hadithDetails({"id":..., "language":"ar"})`). The SDK sends a desktop-browser User-Agent string, so I would not copy that; a small `requests` script with an honest User-Agent is enough.

### 4.6 Should the live voice agent call it?

No, for four reasons: (a) our hard rule is that scripture quoted by the agent comes from reviewed bank items; a live tool would feed unreviewed text straight to a child; (b) the `search` tool can return fatwas and library items unsuitable for ages 6 to 13; (c) 5-second sub-branch timeouts and Cloudflare risk are poor for a voice loop; (d) the Association's policy requires the original text unmodified with source, which the bank guarantees through the stored raw record. Use it as a **build-time source and a parent-dashboard "more from the Association" link-out**, not in the child's turn.

## 5. HadeethEnc vs dorar.net for our use

Dorar API facts below come from the lead's saved copy of `https://dorar.net/article/389` (retrieved by the lead's browser) [S13]; deeper dorar detail is Agent 3's scope.

| Criterion | HadeethEnc | dorar.net (Al-Durar Al-Saniyyah) |
|---|---|---|
| Size | about 3,574 curated base hadiths (2,328 with English), 72 languages | about 300,000 hadiths (package p.15) |
| Selection | Curated "authentic" set with explanations and benefits; thematic category tree (452 categories), good for values | Everything, with rulings and sources; also a section for widely circulated hadiths that are not authentic |
| Grade | one label per record (`صحيح`), grader mostly **not named** | per-hadith ruling by a named scholar with source and "tracing" (package p.15: "scholars' authenticity judgments, their sources"); field details NEEDS-LIVE-CHECK (Agent 3) |
| Book + number | Arabic `reference` often has `book (vol/page) (number)`; 55% of Sahihayn items by regex | source book and page/number are part of each result (per package p.15); format NEEDS-LIVE-CHECK |
| Stable URL per hadith | `hadeethenc.com/<lang>/browse/hadith/<id>` | documented API gives **no ids or per-hadith URLs** (lead's note); item links exist on the site (`dorar.net/hadith/sharh/<id>` is used in our README example) |
| API | REST, JSON, categories, paging, per-id fetch, 72 languages, no key | one search endpoint `https://dorar.net/dorar_api.json?skey=<text>`, optional `&callback=` JSONP; returns `ahadith[]` whose `th` is **HTML** to parse; no filters documented [S13] |
| Languages | Arabic + 71 | Arabic (English section exists on the site) |
| Child-friendliness | words-meanings, benefits, simple English; but explanations are scholarly | none; adult scholarly tool |
| Terms | explicit reuse policy for AI/RAG (2.7) | site content terms not reviewed here (Agent 3) |
| Access from a cloud server | the only hurdles known are the sandbox egress policy and possible Cloudflare; third-party Node scripts pulled the whole corpus | **blocks cloud IPs (Cloudflare)**; browser-only [lead's note] |
| Access from a laptop | works (third-party pull) | works in a browser |
| Fit for "Bukhari/Muslim first" | 70% of the corpus is Sahihayn-attributed | complete coverage of both books |
| Approved by the package | listed as an Association platform (p.9); but **p.3 names dorar.net/hadith and Shamela** as the hadith grading sources | named explicitly (p.3) |

Verdict: use HadeethEnc to **find and fetch** child-suitable Sahihayn hadith in Arabic + English with their metadata and a candidate number; use dorar.net/shamela.ws (manual, in a browser) to **confirm book, number and grade** for each item before it becomes `reviewed`. If the organisers confirm HadeethEnc is an approved source (Q1), HadeethEnc can be the cited `source_site` and dorar becomes the reviewer's cross-check.

## 6. Recommended use in our project

1. **Build-time pipeline from the lead's laptop** (the cloud container cannot reach these hosts).
   - Step 1: pull `categories/list` (en, ar), then for the selected categories (Appendix B) list ids with `per_page=100`; save to the gitignored cache.
   - Step 2: for each id call `/hadeeths/one/` with `language=ar` and `language=en`; save raw JSON and its SHA-256 and the retrieval date.
   - Step 3: filter automatically: grade exactly `صحيح`; `attribution` maps to Bukhari/Muslim/both; number extractable; English present; category not on the deny-list.
   - Step 4: emit draft items with `verification_status: "unverified"`, `source_site` per decision Q1, `source_url` = HadeethEnc page.
   - Step 5: the lead (or Majd) checks each draft against dorar/shamela for the number, then runs `mark_reviewed.py`.
2. **Authoring our own child explanations** in `child_explanation_*` from the hadith's `explanation` and `hints` as *reference material only*; never copy their wording, to respect "no modification" and "do not present summaries as the platform's text".
3. **Verses stay as they are** (quranpedia.net, Uthmani text, Husary audio). Use QuranEnc `english_saheeh` only as a cross-check, and record `translation_name` with the QuranEnc version if we ever switch.
4. **Do not seed `arabic_moyassar`/`arabic_mokhtasar` as tafsir** until Q4 is answered.
5. **MCP**: add `islamic-content` to the lead's Claude Code config for curation (topic search, spot checks of ids). Capture and commit `tools/list` output as evidence. Keep it out of the voice agent. If a runtime link-out is wanted for the parent dashboard (task 04), store the HadeethEnc URL on the item and let the browser open it; no runtime MCP.
6. **Provenance fields.** Keep `retrieved_at`, `api_sha256`, `hadeethenc_id` somewhere (a JSON sidecar next to `reviewed.json` avoids a schema change). Show "Source: HadeethEnc.com" with the link wherever the original text is displayed, and label our explanation as ours.
7. **Starting target**: 100 to 150 hadith across the 38 values from the 277-record English Sahihayn pool (116 with auto numbers), plus manual number lookup for the remainder.

## 7. Questions for the organisers

| # | Question | Why it matters |
|---|---|---|
| Q1 | Is HadeethEnc (and QuranEnc) an approved source for hadith (and verses) in the sense of package p.3, so that we may cite `hadeethenc.com` as `source_site`? Does HadeethEnc's `grade` count as an "approved authenticity grading" for Bukhari/Muslim items? | Decides the schema change and whether dorar/shamela is still mandatory |
| Q2 | For a Sahihayn hadith with no named grader, is "Sahih (compiler: al-Bukhari / Muslim)" enough as grade + grader? | Fills `grader` honestly |
| Q3 | Is server-to-server access to `https://mcp.islamiccontent.org/mcp` (and the REST APIs) from cloud IPs allowed? One team got Cloudflare 1010. Which client identity or allowlist should we use? Any rate limit? | Reliability of the demo |
| Q4 | Are modern tafsirs published by the King Fahd Complex (`arabic_moyassar`) or the Tafsir Center (`arabic_mokhtasar`) acceptable as tafsir sources, given the package says first three centuries or dorar.net/tafseer? | Avoids a content-rule violation |
| Q5 | Which Arabic Quran edition is the `arabic_text` served by QuranEnc/MCP (King Fahd Hafs?), and does QuranEnc `arabic_text` count as approved Uthmani text? | Could let us drop manual verse fetching |
| Q6 | The package says the MCP covers the first six platforms; the live page lists QuranEnc, HadeethEnc and IslamHouse only. Which tools exist for Byenah, IslamEnc/icadb and Terminology? Where is `tools/list` documented? | Planning terms/FAQ sections |
| Q7 | Can records include the hadith number and edition explicitly (a `reference` that is structured), and a version/date per hadith? | The `reference` field is free text, and records carry no version |
| Q8 | Our child-facing agent speaks paraphrases of hadith. What wording or labelling do you want to see for "original text" versus "explanation"? | The Association's policy forbids presenting AI text as original |
| Q9 | Does the written permission requirement for app stores (admin@islamhouse.com) apply to a hackathon demo? | Process |

## 8. Live checks for the lead's laptop

Run from a normal network. Use an honest User-Agent (replace `<team-contact>`); do not spoof a browser. Save outputs under `content/tools/.cache/` (gitignored). Add `-D -` to see headers (rate-limit, cache, server).

```bash
cd backend/session_moral_context            # run everything from here
UA='AlSadiq-AlSadouq-hackathon/0.1 (<team-contact>)'
H=https://hadeethenc.com/api/v1
Q=https://quranenc.com/api/v1
mkdir -p content/tools/.cache/r1 && cd content/tools/.cache/r1

# --- HadeethEnc: shapes, counts, headers ---
curl -sS -A "$UA" -D h-lang.txt  "$H/languages"                                  -o languages.json
curl -sS -A "$UA"                "$H/categories/roots/?language=en"              -o roots-en.json
curl -sS -A "$UA"                "$H/categories/list/?language=en"               -o cats-en.json
curl -sS -A "$UA" -D h-list.txt  "$H/hadeeths/list/?language=en&category_id=282&page=1&per_page=100" -o list-282-en.json
curl -sS -A "$UA"                "$H/hadeeths/one/?language=en&id=5790"          -o one-5790-en.json
curl -sS -A "$UA"                "$H/hadeeths/one/?language=ar&id=2962"          -o one-2962-ar.json   # expect reference with (6864)/(1678)
curl -sS -A "$UA"                "$H/hadeeths/one/?language=ar&id=66521"         -o one-66521-ar.json  # expect Muslim (1955)
curl -sS -A "$UA"                "$H/hadeeths/one/?language=en&id=66511"         -o one-66511-en.json  # big id works over REST?
python3 - <<'EOF'
import json
print('languages:', len(json.load(open('languages.json'))))
print('roots:', [(c['id'], c['hadeeths_count']) for c in json.load(open('roots-en.json'))])
print('meta:', json.load(open('list-282-en.json'))['meta'])
print('en keys:', sorted(json.load(open('one-5790-en.json'))))
a = json.load(open('one-2962-ar.json')); print('ar keys:', sorted(a)); print(a['attribution'], a['grade']); print(a['reference'][:200])
EOF
grep -i -E 'ratelimit|retry-after|x-ratelimit|cf-ray|server' h-lang.txt h-list.txt

# per-hadith web page URL pattern (expect 200 for both)
curl -sS -A "$UA" -o /dev/null -w "ar %{http_code}\n" https://hadeethenc.com/ar/browse/hadith/5790
curl -sS -A "$UA" -o /dev/null -w "en %{http_code}\n" https://hadeethenc.com/en/browse/hadith/5790

# is a hadith graded other than Authentic present? (checks my finding on ids 65065 and 10877)
curl -sS -A "$UA" "$H/hadeeths/one/?language=ar&id=65065" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['grade'],'|',d['attribution'])"
curl -sS -A "$UA" "$H/hadeeths/one/?language=ar&id=10877" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['grade'])"

# --- QuranEnc ---
curl -sS -A "$UA" "$Q/translations/list/en?localization=en" | python3 -m json.tool | head -40   # field names: key/title/version?
curl -sS -A "$UA" "$Q/translations/list"                    | python3 -c "import sys,json;d=json.load(sys.stdin);print(len(d))"
curl -sS -A "$UA" "$Q/translation/aya/english_saheeh/9/119" | python3 -m json.tool               # 'result' wrapper? 'arabic_text'?
curl -sS -A "$UA" "$Q/translation/sura/english_saheeh/112"  | python3 -c "import sys,json;d=json.load(sys.stdin);print(sorted(d['result'][0]))"
curl -sS -A "$UA" "$Q/translation/aya/arabic_moyassar/9/119"| python3 -m json.tool
curl -sS -A "$UA" -D h-q.txt "https://quranenc.com/en/home/d/csv/english_saheeh" | head -12      # metadata block with version
grep -i -E 'ratelimit|retry-after|server' h-q.txt
# compare Arabic text of QuranEnc with our verse 9:119
python3 - <<'EOF'
import json,urllib.request
ours = [i for f in __import__('glob').glob('../../../items/*.json') for i in json.load(open(f)) if i.get('surah')==9 and i.get('ayah')==119][0]
r = json.load(urllib.request.urlopen(urllib.request.Request('https://quranenc.com/api/v1/translation/aya/english_saheeh/9/119', headers={'User-Agent':'AlSadiq-AlSadouq-hackathon/0.1'})))
print(r)
print('arabic equal:', r.get('result', r).get('arabic_text') == ours['arabic_text'])
EOF

# --- Remote MCP (Streamable HTTP, no key) ---
M=https://mcp.islamiccontent.org/mcp
HDR=(-H 'content-type: application/json' -H 'accept: application/json, text/event-stream' -A "$UA")
curl -sS -D h-mcp-init.txt "${HDR[@]}" -X POST $M -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"alsadiq-check","version":"0.1"}}}' | tee mcp-init.txt
cat h-mcp-init.txt | head -20         # status, content-type, any Mcp-Session-Id
SID=$(grep -i '^mcp-session-id:' h-mcp-init.txt | awk '{print $2}' | tr -d '\r')
curl -sS "${HDR[@]}" ${SID:+-H "Mcp-Session-Id: $SID"} -X POST $M -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
curl -sS "${HDR[@]}" ${SID:+-H "Mcp-Session-Id: $SID"} -X POST $M -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | tee mcp-tools-list.txt    # COMMIT this as evidence
curl -sS "${HDR[@]}" ${SID:+-H "Mcp-Session-Id: $SID"} -X POST $M -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_hadith","arguments":{"id":5790,"language":"en"}}}' | tee mcp-get-hadith.txt
curl -sS "${HDR[@]}" ${SID:+-H "Mcp-Session-Id: $SID"} -X POST $M -d '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"search","arguments":{"query":"honesty"}}}' | tee mcp-search.txt
curl -sS -A "$UA" https://mcp.islamiccontent.org/terms.html -o mcp-terms.html          # read the terms text
curl -sS -A "$UA" https://mcp.islamiccontent.org/ -o mcp-home.html                      # the tool docs

# Does our actual LiveKit client get through? (do not change its identity; if it is blocked, report to the organisers, Q3)
pip install 'livekit-agents[mcp]==1.5.1' >/dev/null && python3 - <<'EOF'
import asyncio
from livekit.agents import mcp
async def main():
    s = mcp.MCPServerHTTP("https://mcp.islamiccontent.org/mcp", transport_type="streamable_http", timeout=10, client_session_timeout_seconds=15)
    await s.initialize()
    print([t.info.name for t in await s.list_tools()])
    await s.aclose()
asyncio.run(main())
EOF
```

Also check, in a browser: `https://stats.hadeethenc.com`, `https://stats.quranenc.com` (counts), the footer or "terms" text on `hadeethenc.com/en/home` (original wording of the terms), and `https://hadeethenc.com/en/browse/hadith/66511` to see how the page displays attribution, grade and any reference/number.

Decision after the checks: if `reference` numbers are present in the live `language=ar` output for the ids above and the page URL returns 200, proceed with section 6 step 1. If the MCP returns 403 1010 for the LiveKit client, drop all runtime MCP plans (already the recommendation) and tell the organisers (Q3).

## Appendix A: Sources

| ID | What | URL / location |
|---|---|---|
| S1 | Hackathon resource package (English) | `docs/hackathon/resource-package-en.md` (pp. 3, 5, 8, 9, 11, 15) |
| S2 | HadeethEnc API, official Postman export as markdown (self-described "HadeethEnc.com official API") with sample responses | `https://raw.githubusercontent.com/islamhouse-dev/hadith-api/main/README.md`; Postman docs `https://documenter.getpostman.com/view/5211979/TVev3j7q` (blocked here; found via search) |
| S3 | `@wursha/ngx-hadeethenc-api` 0.0.4 (npm; MIT): response types and the terms quote | `npm pack @wursha/ngx-hadeethenc-api` |
| S4 | `islamic-content-sdk` 1.0.7 (PyPI, author "The Association for Multi-lingual Islamic Content"; npm 1.0.7): all endpoints for QuranEnc and HadeethEnc | `pip download islamic-content-sdk`; `npm pack islamic-content-sdk` |
| S5 | `islamic-content-mcp-server` 1.1.11 (npm): README, `dist/index.js` tool text, `dist/client.js`, `glama.json` | `npm pack islamic-content-mcp-server`; repo `github.com/2yousefreda/islamic-content-mcp` |
| S6 | Third-party measured HadeethEnc pull (26 Sep 2026): script and committed output (ar 3,574, en 2,328, bn 1,925); my analysis of the data (counts above) | `Madrasatul-Muslimeen/Madrasatul-Muslimeen.github.io` `tools/hadith-data-pull/` (`hadeethenc-pull.mjs`, `output/hadeethenc/manifest.json`, `output/hadeethenc/{ar,en}/cat-*.json`); PRs #308, #310; issue #306 |
| S7 | Association usage policy | `https://github.com/IslamHouse-API/multilingual-quran-hadith-islamic-content-database-api-hub` (README; contact admin@islamhouse.com) |
| S8 | QuranEnc catalogue (32 editions, versions), policy snapshot (retrieved 2026-10-02), `build_catalog.py` showing the API and CSV URLs | `m-alhamry/Quran-text-assets` (`api/v1/catalog.json`, `SOURCE_POLICY.md`, `scripts/build_catalog.py`) |
| S9 | Remote MCP evidence and client code from team "qatra-app" | `ibrashdev/qatra-app` (`docs/Source-acquisition.md`, `docs/Content-and-sources.md`, `backend/app/workflow/mcp_client.py`, `backend/app/workflow/editions.py`; `references/source-acquisition/mcp-evidence.json`) |
| S10 | Remote MCP connector notes and client from team "mazann" | `zenkri-ux/mazann` (`SOURCE_CONNECTOR_NOTES.md`, `packages/connectors/islamic-content/src/mcp-client.mjs`, `.env.example`) |
| S11 | `livekit-agents==1.5.1` source | `livekit/agents/llm/mcp.py`, `voice/agent.py` (wheel from PyPI) |
| S12 | Search snippets for the official QuranEnc API page and browse pages | `https://quranenc.com/en/home/api/`, `https://quranenc.com/en/browse/arabic_moyassar`, `https://quranenc.com/en/browse/english_saheeh` (blocked here) |
| S13 | dorar API doc saved by the lead | `backend/session_moral_context/content/tools/.cache/cowork/dorar-api-doc.md` (source `https://dorar.net/article/389`) |
| S14 | Our schema and rules | `backend/session_moral_context/models.py`, `content/README.md`, `.mcp.json`, `AGENTS.md` |

Scratch material (not in repo): `/tmp/claude-0/-home-user-Alsadiq-Alsadouq/8d3f27d3-a7e1-51f5-857a-adba6db41ac3/scratchpad/r1/` (downloaded packages and the snapshot used for the statistics). The snapshot is someone else's copy of HadeethEnc text; it was used for counting only.

## Appendix B: Suggested map from our 38 value slugs to HadeethEnc categories

Starting points only. English counts from the 26 Sep 2026 snapshot. Filter titles by keyword after pulling (there is no search endpoint).

| Value slug(s) | HadeethEnc category ids (English hadith count) |
|---|---|
| prayer | 457 Virtue of Prayer (17) |
| honesty, trustworthiness, keeping-promises | 282 Praiseworthy Morals (83) and 283 Blameworthy Morals (47), keyword filter (truth, honest, lie, trust, promise) |
| honouring-parents, respecting-elders | 273 Dutiful to Parents (10); 282 keyword "elder" |
| family-ties | 274 Kinship Ties (2) |
| mercy | 654 Prophet's Mercy (17); 282 |
| patience, gratitude, contentment, controlling-anger, sincerity, trust-in-allah | 282, 283, 314 Acts of Heart (27), 280 Heart Acts (13), 316 Asceticism and Piety (14), 319 (26), keyword filters |
| kindness-to-animals | 341 Animal Rights in Islam (10); none has an auto-extractable number, plan manual lookup |
| cleanliness | 436 Natural Cleanliness Practices (9) |
| modesty | 649 Prophet's Modesty (1); 282 keyword "modest" |
| good-character | 282 (83), 646 Moral Attributes (55) |
| good-neighbour | 150 Neighbourhood Rulings (4); 282 |
| seeking-knowledge | 270 Excellence of Knowledge (16), 284 Manners of Scholars and Learners (12) |
| humility | 650 Prophet's Humility (7) |
| justice | 661 Prophet's Justice (2) |
| generosity, charity | 648 Prophet's Generosity (6), 511 Voluntary Charity (27) |
| forgiveness | 653 Prophet's Forgiveness (2); 321 Repentance (15) |
| kind-words, avoiding-backbiting | 287 Speaking and Keeping Silent (32), 636 Tongue Evils (9), 283 |
| caring-for-orphans, helping-others, cooperation | 277 Merits of Good Deeds (33), 204 Muslim Society (7), keyword "orphan" |
| brotherhood | 204 Muslim Society (7), 282 |
| remembering-allah | 278 (25), 299 to 302 Dhikr (8 to 15 each) |
| visiting-the-sick | 297 (9) |
| spreading-salam | 286 Greeting (24) |
| table-manners | 290 Eating and Drinking (35) |
| courage | 651 Prophet's Courage (1), 646 |
| not-wasting | 283, 290 keyword "waste" |
| love-of-the-prophet | 81 Our Prophet Muhammad (20) |

Pool size for the union of 25 of these categories: 277 English Sahihayn records, 116 with an auto-extractable Bukhari/Muslim number.

## Appendix C: How the statistics were computed

The 26 Sep 2026 third-party output (`ar/cat-*.json`, `en/cat-*.json`, `categories.json`) was loaded into Python. "Sahihayn-attributed" = Arabic `attribution` contains `البخاري`, `مسلم` or `متفق`. "Extractable number" = the regex in 2.3 finds a pure-integer hadith number for Bukhari or Muslim in the Arabic `reference`. English-available = id present in the `en` shards. Grader named = the Arabic `grade` contains a scholar's name (النووي, الألباني, ابن حجر, الترمذي, ...). The numbers are lower bounds on what the live API can give, because the regex ignores other formats (for example number lists). Recompute on a fresh pull.
