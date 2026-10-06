# R2: Encyclopedias, terminology and FAQ sources

Research agent 2 of 5. Date: 4 Oct 2026. Branch at time of writing: `hk/01-knowledge-bank`. Nothing here was committed. Scope: islamenc.com, terminologyenc.com, Al-Jamhara (islamic-content.com), icadb.com, byenah.com, IslamHouse, the Bayyinat FAQ, risala.prh.gov.sa, and the package's sample-terms table.

## 0. Findings that change the plan (read this first)

1. **There is a children's curriculum inside the Association's own platforms**: «ما لا يسع أطفال المسلمين جهله» ("What Muslim Children Must Know"), by the Association's scientific team, as questions and answers. It has nine sections: creed, fiqh, sirah, tafsir, hadith, etiquette, morals, dhikr, miscellaneous. It sits at `kids.islamenc.com`, on IslamHouse and on Byenah (section 3). It is the closest thing to a ready-made source for our `aqidah`, `faq`, and parts of `fiqh`, `sirah` and morals content. It contains one sensitive answer ("Where is Allah?") that needs sign-off.
2. **icadb has a public, keyless JSON export of 543 approved Q&A cards** (202 "questions of non-Muslims", 341 "questions of Muslims"), Arabic only, one card per question. It covers three of the package's test questions almost verbatim (Kaaba worship, Islam and the sword, why Muslims face Mecca). This is a scriptable second source for `faq` (section 2.4). It needs the organisers' OK, because AGENTS.md names only Bayyinat for FAQ.
3. **Bayyinat PDF facts from another team's working extractor** (section 2.8): 1,259 pages, 263 questions, five fixed blocks per question, a repairable-but-broken text layer, verses drawn in font glyphs with no text. **Our plan's `pdftotext` step will not be enough.** Also: the package's page 12 "Bayyinat" Tafsir-Center app is a different thing (a Ramadan Quran programme).
4. **The dictionary (Jamhara) and terminologyenc both give "Monotheism" for tawhid**, while the package table (p.7) says "Tawhid / Oneness of God". Same kind of gap for fatwa ("Legal opinion" vs "Fatwa"). These are for the organisers (section 8).
5. **Schema impact:** `SOURCE_SITE_CHOICES` has no `islamenc.com`, `terminologyenc.com` or `islamhouse.com`. Changing `choices` makes a migration, so it must ride on the task-01 migration (section 6.4).
6. **Access:** every target host is blocked from this container. Everything below comes from third-party code, public READMEs and web-search extracts, and is tagged. Nothing was fetched from the target sites.

## 1. Evidence tags and method

| Tag | Meaning |
|---|---|
| **VC** | Verified from third-party code or SDK source that I read. The code was written against the live service by someone else; I did not run it. |
| **VD** | Verified from published docs, a README, a PR text or a repo note. |
| **SNIP** | Seen only in a web-search result extract (URL and page title are real index entries; exact wording must be checked on the live page). Treat as NEEDS-LIVE-CHECK for wording. |
| **NLC** | NEEDS-LIVE-CHECK. Not seen anywhere. |

Network: `curl` to all target hosts returns `CONNECT tunnel failed, response 403`; `WebFetch` returns `EGRESS_BLOCKED` for them (islamenc, terminologyenc, s.islamcontent.com, documenter.getpostman.com, glama.ai, dawa.center, ar.islamway.net). I did not try mirrors of the blocked sites (no web.archive.org etc.). What worked: `WebSearch`, GitHub code search (MCP), `raw.githubusercontent.com`, `registry.npmjs.org`, `pypi.org`, and `WebFetch` on `github.com` PR pages.

Third-party sources used (all public, none has a licence file that lets us copy code, so treat them as reading material only):

| Id | Source | What it gave |
|---|---|---|
| E1 | npm `islamic-content-sdk` 1.0.7, README ([npm](https://registry.npmjs.org/islamic-content-sdk/-/islamic-content-sdk-1.0.7.tgz), [GitHub](https://github.com/2yousefreda/islamic-content-sdk-npm)). Unofficial author; says it is "developed for" the Association. | Exact HTTP endpoints for QuranEnc, HadeethEnc, IslamHouse v3, Risalat al-Haramayn, Byenah. **No** islamenc, terminologyenc or icadb. |
| E2 | [ibrashdev/qatra-app](https://github.com/ibrashdev/qatra-app): `docs/Source-acquisition.md`, `references/source-acquisition/mcp-evidence.json`, `backend/app/workflow/{mcp_client,editions}.py` | The Islamic Content MCP: URL, 11 tool names, Cloudflare block, observed response layout. |
| E3 | [mushari44/Islam-hackthon](https://github.com/mushari44/Islam-hackthon): `scripts/ingest_icadb.py`, `scripts/ingest_bayyinat.py`, `data/corpus/qa.jsonl`, `tasks/mushari.md`, PRs #1 and #5 | The icadb export endpoint and card schema; the Bayyinat PDF layout; the real list of 543 cards. |
| E4 | [TarteelAI/quranic-universal-library `lib/importer/islam_enc.rb`](https://github.com/TarteelAI/quranic-universal-library/blob/main/lib/importer/islam_enc.rb) | `saadi.islamenc.com/{lang}/browse/sura/{n}`: islamenc runs per-book subdomains. |
| E5 | [farhadhossain001/QuranApp `api-doc.md`](https://github.com/farhadhossain001/QuranApp/blob/main/api-doc.md) | Partial mirror of the IslamHouse v3 Postman docs (overview, parameters, three endpoints). |
| E6 | [IslamHouse-API hub README](https://github.com/IslamHouse-API/multilingual-quran-hadith-islamic-content-database-api-hub) | Use and attribution conditions for IslamHouse, QuranEnc, HadeethEnc content. |
| E7 | Repo notes: `docs/hackathon/content-structure-plan.md` §1 (the lead's probe of 4 Oct 2026) | robots.txt and page-weight facts for dawa.center and islamic-content.com. |

## 2. Source by source

### 2.1 islamenc.com (Encyclopedia of Islamic Content in Multiple Languages)

**What it is.** A family of sites, not one site. The package (p.10) describes cards "with defined fields and sentences, and unified identifiers linking each card to its translations", connected to icadb "through a documented REST API" (VD).

| Fact | Evidence |
|---|---|
| Main site has three areas: Holy Quran, Materials/Books, Encyclopedias. 100+ languages. | SNIP [islamenc.com/en/](https://islamenc.com/en/) |
| Hub of all sub-projects: `s.islamenc.com` (EN `/lang/en`): Byenah encyclopedia, Quran encyclopedia, hadith encyclopedia, terminology encyclopedia, kids curriculum. | SNIP [s.islamenc.com/lang/en](https://s.islamenc.com/lang/en) |
| **Card viewer URL**: `https://islamenc.com/{lang}/enc-cards/{encyclopedia_id}/card/{card_id}` (used as the citation link by a working ingest script). A second prefix also exists: `/{lang}/enc/{id}/card/{card_id}`. | VC (E3) for `ar/enc-cards/…`; SNIP for [`en/enc-cards/116/card/17113`](https://islamenc.com/en/enc-cards/116/card/17113) and [`en/enc/101/card/8272`](https://islamenc.com/en/enc/101/card/8272) |
| Encyclopedia ids seen: **101** (hadith cards, title suffix "Specialized Scientific Explanation"), **102** (Q&A for Muslims), **110** (Q&A for non-Muslims), **116** (a fiqh-ruling card, "أحكام التيمم"). Ids for Names of Allah, terms, places, figures are **not known**. | VC (E3) for 102 and 110; SNIP for 101 and 116; NLC for the rest |
| **Card schema** (as served by icadb): `external_id` (the unified id), `latest_version{version_str, is_approved}`, `sentences[]{field_name, text}`, `lookup_items[]{name, lookup_table_external_id}`. For the two Q&A encyclopedias the Arabic `field_name`s are `العنوان` (title), `السؤال` (question), `الجواب` (answer), `المصدر` (section). The value `--` means empty. | VC (E3 `ingest_icadb.py`) |
| Quran pages: `islamenc.com/{lang}/quran/{surah}` and `…/quran/{surah}/{ayah}`. The MCP's `get_quran_verses` returns `Source: https://islamenc.com/ar/quran/112` and interleaves the Muyassar tafsir line after each verse. | VC (E2) and SNIP [islamenc.com/en/quran/30/49](https://islamenc.com/en/quran/30/49) |
| Per-book subdomains: `saadi.islamenc.com` (Tafsir al-Saadi, `/{lang}/browse/sura/{n}`), `riyadh.islamenc.com/en/page/{n}` (a Riyad al-Salihin-style book), **`anees.islamenc.com/en/page/{n}` (Names of Allah)**, **`kids.islamenc.com` (children's curriculum)**, `browse.islamenc.com/lite/index.php/item/{id}` (IslamHouse-style item viewer). | VC (E4) for `saadi`; SNIP for the rest |
| Language prefix is `{ui}{content}` on some paths (`islamenc.com/enml`, `/enam/books`, `/aram/books/182`). | SNIP |
| **No separate REST API for islamenc itself** was found. The API is icadb's (section 2.4). | VD (package p.10) |

**Names of Allah (`anees.islamenc.com`)** (SNIP): pages seen in English: 4 Allah, 5 As-Samad, 6 Ar-Rahman Ar-Rahim, 8 Al-Qayyum, 18 Al-Khaliq, 40 Al-Latif, 45 Ar-Ra'uf, 46 Al-Qarib, 54 Al-Muqit, 76 Ar-Rafiq (e.g. [page 76](https://anees.islamenc.com/en/page/76), [page 6](https://anees.islamenc.com/en/page/6)). A page has the name, a short explanation, and quotes a prophetic saying (for Ar-Rafiq). Whether Arabic pages exist at `/ar/page/{n}`, and how verses and hadith are cited on each page, is NLC. Each page that quotes a verse or hadith must be treated like any other source: we never copy the quotation, we link to bank items.

**Usable for our sections?** `faq` (via the Q&A cards, section 2.4), `aqidah` (Names of Allah, kids creed section), `term` (a terms encyclopedia exists but its id is unknown; terminologyenc is the better route). Needs `islamenc.com` added to `SOURCE_SITE_CHOICES` (host check in `ContentItem.clean()` accepts subdomains, so `kids.` and `anees.` pass with `source_site='islamenc.com'`).

### 2.2 terminologyenc.com (Encyclopedia of Translated Islamic Terms)

| Fact | Evidence |
|---|---|
| Stated goals: authenticated translations of recurring Islamic terms with definitions; a free electronic reference; translations "with various electronic formats for portals and apps". Whether an export or API button exists: **NLC**. | SNIP (search extract of the site description) |
| **Four top categories** (term counts from the site extract): The Creed (**445**), Jurisprudence and Juristic Principles (**1,325**), Virtues and Manners (**280**), Hadith Terminology (**42**). Category URLs: `/en/browse/category/3` (Creed), `/4` (Fiqh and principles), `/5` (Virtues and Manners), `/43` (Hadith Terminology), `/6` (Da'wah and Hisbah), `/59` (Belief in Allah), `/74` (Oneness of Names and Attributes), `/69` (People of the Sunnah), `/81` (Our Prophet ﷺ), `/66` (Companions), `/762` (Persons). | SNIP [category 3](https://terminologyenc.com/en/browse/category/3), [43](https://terminologyenc.com/en/browse/category/43), [5](https://terminologyenc.com/en/browse/category/5) |
| **Stable term URL**: `https://terminologyenc.com/{lang}/browse/term/{id}`. The numeric id is language-independent (same id appears under `/en/`, `/fr/`, `/id/`, `/ar/`, `/ur/`). | SNIP, e.g. [`/en/browse/term/10482`](https://terminologyenc.com/en/browse/term/10482), [`/fr/browse/term/10482`](https://terminologyenc.com/fr/browse/term/10482) |
| **Term page title format**: "Term Explanation and Translation: *{English equivalent}* - *{Arabic}*". Page body: terminological definition, linguistic definition, longer explanation, translations. | SNIP |
| Languages seen on term pages: English, French, Spanish, Turkish, Urdu, Indonesian, Bosnian, Russian, Portuguese, Bengali, Chinese, Persian, Tagalog, Hindi, Malayalam, Telugu, Thai, Arabic. Not every term has every language. | SNIP |
| Arabic-only terms also exist as plain entries (e.g. persons, sects, places). | SNIP |
| Other projects reuse it by scraping (two Flutter apps carry a "not affiliated, cloned by web scraping" notice), which suggests there is **no public API**. | SNIP (GitHub code search: `Elresala-V2`, `El-mensaje-eterno-`) |

**English equivalents seen** (all SNIP, exact wording to be confirmed): tawhid → "Monotheism" (id 10482); Islam → "Islam" (43613); worship → "Worship" (15008); the Sunnah → "The Sunnah" (10811); Hadith → "Hadīth" (71790); Sharia → "Islamic law" (47755; FR "La Charia", ES "Al-Shari'a"); fatwa → "Legal opinion" (id 65, term *fatya* فتيا); calling to Allah → "Calling to Allah" (72440); the Qur'an → "The Qur’an" (53650). Prophethood (نبوة, Arabic id 7365) sits in the Creed category. **No "Revelation - الوحي" entry surfaced** (found تنزيل 10476, إلهام 1184, كتاب الوحي 11049 instead).

**Usable for `term`?** Yes, as the second source (cross-check) after Jamhara. It is the same Association's data, has stable per-term ids, and the pages are far lighter than Jamhara's (NLC). Add `terminologyenc.com` to `SOURCE_SITE_CHOICES`. Do not mix its text into a Jamhara item (one item = one source; the two wordings differ, e.g. the prophethood definitions).

### 2.3 islamic-content.com (Al-Jamhara)

| Fact | Evidence |
|---|---|
| "Mu'jam al-Mustalahat al-Shar'iyya" (Islamic Dictionary), part of a larger site: dawah terminology, hadith explanations, Quran and hadith translation encyclopedias, narrators, notable figures, places, fiqh terms. Also `old.islamic-content.com`. Associated with Osoul Center in a tweet. | SNIP [islamic-content.com/dictionary](https://islamic-content.com/dictionary), [/page/about](https://islamic-content.com/page/about) |
| **Dictionary entry URL**: `/dictionary/word/{id}/{lang}`; title "معنى : *{EN}* - *{AR}* - الجمهرة". Without the language suffix the Arabic page opens (`/dictionary/word/5748`). Language list on [/en/l/dictionary](https://islamic-content.com/en/l/dictionary) is ~90 languages. | SNIP |
| Other URL families: `/t/{id}` (Arabic term/topic article, e.g. [`/t/1817`](https://islamic-content.com/t/1817) العبادة, [`/t/509`](https://islamic-content.com/t/509) السنة, [`/t/2002`](https://islamic-content.com/t/2002) الوحي), `/hadeeth/{id}/en` (translated hadith explanations), `/post/{id}` (articles, many languages), `/content/{id}`, `/content-download/{id}`, `/allah-names`, `/historical-events`, `/terms-index`. | SNIP; the last four also in E7 |
| Older notes: `/dictionary/term/{id}` for Quranic terms. | VD (E7) |
| **robots.txt / weight**: "blocks some crawlers entirely and `/dictionary/` for some"; a dictionary page is about 1.7 MB. The lead's rule: by hand, one page at a time, 5+ seconds apart. I could not read robots.txt myself. | VD (E7); NLC for the exact file |
| Entry content: Arabic definition, English equivalent in the page title, linguistic meaning, longer English text on `/en` pages. | SNIP |
| **Priority for sensitive terms** (package p.4): "Give this priority over automatic translation". The test question "Translate the word tawhid into English" → dictionary equivalent **"Monotheism"** ([`/dictionary/word/3529/en`](https://islamic-content.com/dictionary/word/3529/en), "معنى : Monotheism - التوحيد"). | VD (package) + SNIP |

The dictionary's definitions match the package's p.7 "usage guidance" text closely for Islam, ibadah, hadith, sunnah and fatwa (SNIP). That suggests the table was written from this dictionary, so a `term` item should quote the dictionary definition and carry the package guidance as a separate rule in the prompt, not as source text.

Usable for `term`: yes, primary. Site is already an allowed `source_site`. **Manual only** (heavy pages, robots).

### 2.4 icadb.com (Central Database for Islamic Content in Multiple Languages)

| Fact | Evidence |
|---|---|
| Package: central repository of approved translations; sentence-level alignment, unified ids, semantic embeddings "enabling retrieval by wording and meaning"; 30M+ approved words; docs at `icadb.com/api/docs`. | VD (package p.10) |
| **Base URL** `https://icadb.com/api/`. | VC (E3) |
| **Export endpoint (verified in working code)**: `GET https://icadb.com/api/encyclopedias/{enc}/cards/latest/?page={n}&page_size=1000`. Returns `{"cards":[…], "total_pages":N}` with approved versions. The script sends only `User-Agent: Sabeeli-ingest`; **no key, no header**. | VC (E3) |
| Result of that script: **543 approved Q&A items** (encyclopedia 110: 202; encyclopedia 102: 341), cards at version "1.0" (517) or "1.1" (26). Text is **Arabic only**; "the API carries no translations for these cards yet" (author's note). | VC/VD (E3 script, PR #1/#5, my analysis of `data/corpus/qa.jsonl`) |
| Semantic search endpoint, listing of encyclopedias, translation lookup by unified id, auth for non-export routes, rate limits, licence. | **NLC** (on `icadb.com/api/docs`) |
| icadb also holds *books* with many translations (e.g. «الإسلام دين الفطرة والعقل والسعادة», «من خلق الكون؟»). | VD (E3 `tasks/mushari.md`) |

**What encyclopedia 110 ("Q&A Encyclopedia for Non-Muslims", 202 cards) contains** (titles from E3's committed corpus; I did not copy answers):

| Test question in the package | Closest card | Card id | Length of answer |
|---|---|---|---|
| Why do Muslims worship the Kaaba? | «ما هي الكعبة؟ وهل يعبد المسلمون الكعبة؟» (+ «لماذا يُقبِّل المسلم الحجر الأسود…» 36243; «لماذا يصلي المسلمون باتجاه مكة؟» 36240) | **36130** | 1,131 chars, cites 4 verses |
| Did Islam spread by the sword? | «هل انتشر الإسلام بحد السيف؟…» (+ «ما هو الجهاد؟» 36193) | **36112** | 815 chars, 1 verse |
| Was the Quran authored by Muhammad? | no exact title; nearest: «هل يصح أن النبي محمدًا قد كتب القرآن ونسخه من الإنجيل؟» 36097, «هل نسخ النبي محمد القرآن من التوراة؟» 36180, «هل اقتبس النبي محمد ما جاء في القرآن من الحضارات السابقة؟» 36181 | 36097 / 36180 / 36181 | 2,059 / 569 / 176 |
| Why do scholars give different rulings? | no exact title; nearest: «لماذا ينقسم المسلمون إلى أحزاب ومذاهب فـي حين أنهم يتبعون كتابًا واحدًا؟» | 36083 | 2,828 |
| Hostile "Why does Islam prohibit X?" | e.g. «لماذا لا يتناول المسلم لحم الخنزير؟» 36234, «لماذا حرَّم الإسلام شرب الخمر؟» 36236 | | |
| Who created Allah? | «من الذي أوجد الخالق؟» | 36139 | 881 |
| Why do we pray / five times / what are the pillars? | 36238, 36239, 36127 | | 1,256 / 1,172 / 2,925 |
| Sensitive: Where is Allah? | encyclopedia 102, «أين الله عَزَّ وَجَلَّ؟» | 26015 | 97 chars; the answer states a location. Needs sign-off. |

Shape of the whole set: 366 of the 543 answers are 700 characters or shorter; 96 of the 202 cards in 110 are tagged «الشبهات والاعتراضات» (doubts and objections). Encyclopedia 102 is mostly adult fiqh (tags: الفقه 74, الطهارة 70, الحيض والنفاس والاستحاضة 55, الصيام 23, الصلاة 21, العقيدة 33); only its creed cards are of interest to us. **Filter out for children**: menstruation, marriage and polygamy, wife-beating, hijab arguments, apostasy, suicide operations, homosexuality, slavery, Shia/Sunni, hellfire-punishment questions, comparative-religion questions (Jesus, original sin).

Verses inside an answer are written ﴿…﴾ followed by a bracketed surah name and number. We never copy these (rule: verses come from the bank or not at all); an answer that cites a verse links to `verse:S:A` only if that verse is in the bank.

Usable for `faq`: **yes, as a second source** if the organisers accept it (section 8, Q2). Citation URL = the islamenc viewer link (so `source_site = islamenc.com`).

### 2.5 Islamic Content MCP (`mcp.islamiccontent.org`)

| Fact | Evidence |
|---|---|
| Endpoint `https://mcp.islamiccontent.org/mcp`, Streamable HTTP, no auth, free, read-only. Terms: `https://mcp.islamiccontent.org/terms.html` (no content-reuse grant found by the other team). | VD (E2) |
| **11 advertised tools**: `search`, `fetch`, `list_languages`, `get_quran_verses`, `list_quran_translations`, `get_quran_audio`, `get_hadith`, `browse_hadith_categories`, `browse_library`, `get_library_item`, `list_library_categories`. | VD (E2) |
| The public page lists **three source branches only**: QuranEnc, HadeethEnc, IslamHouse. The package (p.9) says the MCP serves "the first six platforms", which would include Byenah, islamenc and terminologyenc. The two statements disagree; only the page's list is evidenced. | VD (E2) vs package |
| Direct scripted HTTP gets Cloudflare **403, code 1010 `browser_signature_banned`**, "do not retry". | VD (E2) |
| A **claude.ai connector** "Islamic Content" exists and worked in another Claude Code cloud session (tools named `mcp__Islamic_Content__…`). Not available in this session. | VD (E2) |
| Observed layouts: `get_quran_verses` → header, `[EXACT]` block with `[S:A]` markers, verse line then tafsir line, `Source:` URL. `get_hadith` → title, `[EXACT]`, `[ATTRIBUTION]` (Narrator, Grade), `[COMMENTARY]`, `Source:`, language list. | VC (E2 `mcp_client.py`) |

Not useful for `term` or `faq` unless `search`/`browse_library` reach them (NLC). Worth one test from the lead's laptop (section 9, step L).

### 2.6 byenah.com (Bayan al-Islam)

| Fact | Evidence |
|---|---|
| 10,000+ publications in 120+ languages; "electronic encyclopedia of selected items introducing and teaching Islam"; API at `byenah.com/ar/api`. | VD (package p.9) + SNIP |
| **Endpoints (third-party SDK source)**: `GET https://byenah.com/{lang}/Api/languages/list`; `/Api/content/muslims/full_list?page=`; `/Api/content/non-muslims/full_list?page=`; `/Api/paginated-languages?name=&page=`; `/Api/recent-contents?lang=&init=&ids=`; `/Api/lookups`; `/Api/name_search?name=`. Response wrapper `{"data":[…],"meta":{current_page,total}}`. Field names inside items were **not** shown (SDK placeholders only). | VC (E1) |
| Official Postman collection and environment: `https://byenah.com/download-request?name=Bayan%20Al%20Islam.postman_collection.json` and `…name=Bayan%20al%20islam%20env.postman_environment.json` (browser download). | VD (E1) |
| Page URLs: `byenah.com/{lang}/discover-islam/{id}`, `/muslim-content/{id}`, PDFs at `cdn.byenah.com/contents//{id}/…pdf`. | SNIP |
| **Children's material: yes**: «ما لا يسع أطفال المسلمين جهله» as [`/en/discover-islam/5138`](https://byenah.com/en/discover-islam/5138) (also `/ak/discover-islam/22370`, `/de/discover-islam/21664` in other languages). | SNIP |
| Rights of Byenah content: not stated. The IslamHouse hub README (E6) covers IslamHouse, QuranEnc and HadeethEnc only. | NLC |

Usable for: leaflet-style dawah content, not for our atomic item types. Best use is a locator for the kids curriculum PDF.

### 2.7 IslamHouse (`islamhouse.com`, API v3)

| Fact | Evidence |
|---|---|
| Base `https://api3.islamhouse.com/v3/{key}/…`. The key is a **public key stated as "free to use"** in the Postman docs (I do not reproduce it; it is in the docs' `key` parameter and in E1/E5). `limit` max 50. `format` = `json` only. | VD (E5) |
| Concepts: item = one type (book, article, audio, video, fatwa…), one source language `slang`, one or more interface languages `flang`, authors, sources, categories. `slang` may be `showall`. | VD (E5) |
| Documented in the mirror (E5): `…/main/home/json`, `…/main/get-footer/{flang}/json`, `…/languages/get-social/{lang}/json`. **The mirror is partial**; the full Postman docs need a browser. | VD (E5) |
| Endpoint list from the SDK (E1): `main/sitecontent/{siteLang}/{contentLang}/json`, `categories/showall/{lang}/json`, `main/get-object-category-tree/{lang}/json`, `categories/viewcat/{categoryId}/{siteLang}/{contentLang}/json`, `main/get-sub-categories/{categoryId}/{lang}/json`, `main/{type}/{siteLang}/{slang}/{page}/{limit}/json`, `main/get-category-items/{categoryId}/{slang}/{siteLang}/{contentLang}/{page}/{limit}/json`, `main/get-item/{itemId}/{lang}/json`, `main/check-attachment/{itemId}/json`, `main/get-item-translations/{itemId}/{lang}/json`, `main/get-latest/{period}/…`, `main/get-highlights/…`, `main/get-language-items-count/…`, author routes (`get-author/{id}/{lang}/json`, `get-author-items/…`), `languages/get-language-details/json`, `quran/…` routes (reciters, recitations). | VC (E1) |
| **Use and attribution rules** (README of the IslamHouse API hub, which lists its contact as admin@islamhouse.com; official status of the repo is not confirmed): free to download, store, use in apps and RAG, commercially or not; **do not alter the original text, cite the source (and author/translator), keep version info**; summaries are your own work and must not be labelled as theirs; AI-generated text must not be presented as the original. | VD (E6) |
| **Children's material**: «ما لا يسع أطفال المسلمين جهله» [`islamhouse.com/ar/books/2829179/`](https://islamhouse.com/ar/books/2829179/) (Arabic, by the Association's scientific team), [`/en/books/2834695`](https://islamhouse.com/en/books/2834695) (English, Rowad Translation Center), PDF [en-what-muslim-children-must-know.pdf](https://d1.islamhouse.com/data/en/ih_books/single3/en-what-muslim-children-must-know.pdf); «منهاج المسلم الصغير» [`/ar/books/328241/`](https://islamhouse.com/ar/books/328241/); «I Play and Learn» [`/en/books/2831710/`](https://islamhouse.com/en/books/2831710/); a "Prophets’ Stories" category (id **5387**, [books page](https://islamhouse.com/en/category/5387/books/showall/1/)). | SNIP |

Usable: finding and downloading children's books and story material (another agent's scope: stories). Not a FAQ or term source. `islamhouse.com` is not in `SOURCE_SITE_CHOICES`.

### 2.8 Bayyinat FAQ (dawa.center/file/7937)

**What it is.** «بينات: أسئلة وأجوبة عن الإسلام». A **PDF book** (about 16.3 MB, listed as PDF), published by «جمعية الدعوة والإرشاد وتوعية الجاليات», 1445 H. Described as a collection of the most frequent questions about Allah, the Prophet ﷺ, the Qur'an and the fundamentals of Islam, "classified by scientific criteria", answers prepared by a specialised team. | SNIP (search extract of [dawa.center/file/7937](https://dawa.center/file/7937))

**Not the Tafsir Center "Bayyinat" app.** The package (p.12) lists "Bayyinat" among Tafsir Center apps. That app is a Ramadan Qur'an programme (guidance and reflections from the Qur'an, three presenters, Arabic and English) at [tafsir.net/application/5](https://tafsir.net/application/5/ttbyq-by-ynat) (SNIP). Different product, same name. The Q&A book was not found on byenah, IslamHouse or tafsir.net (NLC); it is mirrored on [ar.islamway.net/book/32051](https://ar.islamway.net/book/32051/) (not an approved site; useful only to cross-check metadata).

**Layout, from a working extractor written against the real PDF** (VC: E3 `ingest_bayyinat.py`, VD: PR #1 text "263 questions … 847 verses identified"):

| Property | Value |
|---|---|
| Pages | **1,259** |
| Questions | **263**, numbered; table of contents precedes the first question |
| TOC line format | `(n) title ….. page`; main sections "أولًا: …", sub-sections "- …" |
| Blocks inside each question (Arabic labels) | **السؤال** (question) · **عبارات مشابهة للسؤال** (similar wordings) · **مضمون السؤال** (gist) · **مختصر الإجابة** (short answer) · **الجواب التفصيلي** (detailed answer) |
| Average size | about 4.8 pages per question, so the detailed answer is long; the **short answer is the right excerpt unit** |
| Page number | The book prints its own page number in a running header (small font near the top). It can differ from the PDF page index. |
| Text layer | **Broken for plain extraction**: reversed ligatures (اإلسالم for الإسلام, اهلل for الله), spaces drawn over letters, punctuation moved, honorific signs drawn in a symbol font (no usable text). The other team rebuilds every line from glyph positions right to left with PyMuPDF. |
| Verses | **Typeset in King Fahd Complex page fonts (QCF) whose glyphs carry no text.** A verse is followed by a reference like `[يس: 40]`. So the PDF gives the *reference* but never the verse text. |
| Rights | The other team states the publisher reserves rights and keeps the PDF and extracted text out of git; it has an open question to its reviewers whether excerpts may be committed. |
| Language | Arabic. An English edition is **NLC** (our earlier note says the dawa.center page has `?lang=ar|en|fr`; that may only be the page UI). |

**Implications for our tooling** (`tools/extract_faq.py`; the lead's laptop has `dawa-7937-bayyinat.pdf`):

1. **`pdftotext` is not enough.** Test `pdftotext -layout` on two pages first; if the Arabic is reversed or ligature-broken, use PyMuPDF (`page.get_text("rawdict")`) and rebuild lines from character boxes (sort by right edge, attach vowel marks to the glyph they sit on, drop spaces that overlap a letter, keep numbers left-to-right). Read E3's script for the approach; **write our own** (no licence file there). Font names in E3 are a hint to verify with `pdffonts`/PyMuPDF on the real file.
2. **Citation page.** Read the running-header number (the printed page) and keep the PDF page index too. Cite the **printed** page in `number`, e.g. `"Q57 · p. 312"` (30-char limit). `source_url = https://dawa.center/file/7937#p312`. The server ignores the fragment, so it is a label only. If two items start on one page, use `#p312-q57`. Spot-check three pages by eye (render PNG next to the text) before trusting any page number.
3. **Item mapping:**

| Field | Value |
|---|---|
| `type` / `source_site` | `faq` / `dawa.center` |
| `title_ar` | the question line (السؤال) verbatim |
| `keywords_ar` | the "similar wordings" block, verbatim lines (a ready-made keyword list) |
| `arabic_text` | 1–3 whole paragraphs of **مختصر الإجابة** (short answer), cut on paragraph boundaries only |
| `number` / `source_url` | `Q<n> · p. <printed>` / `https://dawa.center/file/7937#p<printed>` |
| `related` | `verse:S:A` labels for each `[سورة: آية]` reference **only if that verse is already in the bank**; never put PDF-typed verse text anywhere |
| `english_text` | blank (Arabic source) |

4. **Verbatim integrity.** The extractor drops symbol-font honorifics (ﷺ, رحمه الله), so an extracted excerpt can differ from the printed page. The tool should render the page image beside the text; the lead compares and, if an honorific is missing, restores it by hand and notes it in the review. This is a reason the lead must read each FAQ excerpt next to the PDF page (already the plan).
5. **Rights:** keep the PDF, the full extraction and per-question JSON in `tools/.cache/` (gitignored). Commit only the short excerpt per item. Ask the organisers (section 8, Q1).
6. **Do not crawl dawa.center**: the lead's note says `/storage/files/` and `/*/download` are disallowed by robots (VD, E7). The manual browser download already done is the right route.

**Pages and sections to look for** (I could not read the TOC; numbers unknown, so the first task is to print it):

| Look for in the TOC / similar-wordings (Arabic keywords) | Why |
|---|---|
| الكعبة، القبلة، عبادة الأصنام، الحجر الأسود | Test question 1 (Kaaba) |
| مصدر القرآن، القرآن كلام الله، تأليف محمد، اقتباس من التوراة والإنجيل، تحريف | Test question 2 (authorship) |
| السيف، الجهاد، انتشار الإسلام، الإكراه في الدين | Test question 3 (sword) |
| اختلاف العلماء، المذاهب، الاجتهاد | Test question 4; **not likely in this book** (scope: Allah, the Prophet, the Qur'an, fundamentals), so expect to fall back to icadb card 36083 or dorar fiqh |
| من هو الله، لماذا لا نرى الله، من خلق الله، لماذا خلقنا، لماذا يعبد الله | Child-typical |
| من هو محمد ﷺ، صدق النبي، المعجزات | Child-typical |
| أركان الإسلام، لماذا نصلي | Child-typical |
| **Skip / needs sign-off:** أين الله، النار والعذاب، الشر والألم، القضاء والقدر، الأديان الأخرى، المرأة، الجهاد (graphic), الردة | Content rules |

The book's «مختصر الإجابة» (short answer) is also where the child explanation can be drafted from; the detailed answer is for adults.

### 2.9 risala.prh.gov.sa (Risalat al-Haramayn)

| Fact | Evidence |
|---|---|
| Purpose: guidance for visitors to the Two Holy Mosques; text, audio, video in 80+ languages; translated by the Association under the Presidency's supervision. | VD (package p.11) |
| **API docs page** `https://risala.prh.gov.sa/en/Api/content`. Endpoints: `GET https://risala.prh.gov.sa/{lang}/Api/get_full_contents?lang=`; `/Api/content?lang=`; `/Api/single-content?id=`; `/Api/fatwas?lang=&is_featured=`; `/Api/hadeeths?lang=&is_featured=`; `/Api/quran?lang=&is_featured=`; `/Api/search?query=&page=`; `/Api/langs?api_key=` (**a key parameter appears on this one**); `/Api/content-types`. | VC (E1) |
| Page URLs `risala.prh.gov.sa/{lang}/content/{id}` and `/contents/{id}`; PDF under `/storage/contents/{id}/…`. Example titles: "What A Muslim Must Know" (`/en/content/251`, `/fa/contents/511`), Umrah booklets, merit of the first ten days of Dhul-Hijjah. | SNIP |
| Child-specific content: none found. The content is pilgrim-oriented (rites, hajj, umrah, fatwas) and mostly fiqh for adults. | SNIP |

Verdict: not useful for children; at most a source for one or two parent-facing "visiting Makkah/Madinah" notes. Skip for the hackathon.

## 3. The children's curriculum: «ما لا يسع أطفال المسلمين جهله»

| Fact | Evidence |
|---|---|
| English title "What Muslim Children Must Know". Author: the Scientific Team of the Association (Arabic book on IslamHouse); English by Rowad Translation Center. | SNIP [islamhouse.com/ar/books/2829179](https://islamhouse.com/ar/books/2829179/), [/en/books/2834695](https://islamhouse.com/en/books/2834695) |
| "A simple and easy curriculum… suitable for young children in particular, for all ages, and newcomers to Islam", "arranged in sections by topic, in the form of questions and answers, to stimulate the mind and aid memorisation". | SNIP |
| **Web version**: `https://kids.islamenc.com/{lang}/home`; sections `…/browse/category/{id}`: **10 Creed, 20 Fiqh, 30 Prophetic Sirah, 40 Tafsir, 50 Hadith, 60 Islamic Etiquettes, 70 Morals, 80 Supplications and Dhikrs, 90 Miscellaneous**; a quiz at `/browse/quiz/rand`. Many languages (e.g. `/rw/`, `/az/`, `/am/`, `/yo/`, `/de/`, `/ff/`). | SNIP [kids.islamenc.com/en/home](https://kids.islamenc.com/en/home), [category 10](https://kids.islamenc.com/en/browse/category/10) |
| Other copies: [byenah.com/en/discover-islam/5138](https://byenah.com/en/discover-islam/5138), [enc.islamhouse.com/en/books/230/1](https://enc.islamhouse.com/en/books/230/1), PDF on d1.islamhouse.com (above). | SNIP |

**Creed section (category 10), ten Q/A pairs as extracted by the search tool** (wording NLC): Who is your Lord? · What is your religion? · Who is your prophet? · What are the words of Tawhid and its meaning? · **Where is Allah Almighty?** · What is the meaning of the testimony that Muhammad is the Messenger of Allah? · Why did Allah create us? · What is worship? · What is our greatest duty? · What are the types of Tawhid?

- The answer given to "Where is Allah Almighty?" states a location ("in the heaven, above the Throne…"). Our content plan already puts this question on the **sensitive list**: seed it only after the lead (or a scholar) approves the exact wording. The other nine are plain.
- The Morals section (70) covers truthfulness, mercy, cooperation, honouring parents, trustworthiness (SNIP). The Fiqh section (20) covers the five pillars and prayer pillars/conditions (SNIP): general information, but the prayer-conditions detail should go through the same "general information, ask your parents or a scholar" referral.
- Because it is child-written Q/A, items map one-to-one to `aqidah` (or `faq`). The same book also feeds `fiqh`, `sirah`, morals-tagged `hadith`, `term`-like answers (e.g. "What is worship?" matches the dictionary definition). **Tell the agents for the other sections.**

Open points: the exact Arabic wording (we need the Arabic source, since `arabic_text` is the verbatim excerpt) and whether the book quotes verses and hadith with references (NLC). Whether this curriculum counts as an approved source for `aqidah` under the p.3 field table (first three centuries / dorar.net) is a question for the organisers (section 8, Q3).

## 4. The package's 10 sample terms (p.7): where to source each

Dictionary column = Al-Jamhara `https://islamic-content.com/dictionary/word/{id}/en` (SNIP); terminologyenc column = `https://terminologyenc.com/en/browse/term/{id}` (SNIP). EN = the equivalent in the page title.

| Term | Package equivalent | Jamhara id and EN | terminologyenc id and EN | Notes |
|---|---|---|---|---|
| Islam | Islam | **1018**, "Islam" | 43613, "Islam" | Definition ("Surrendering to Allah through monotheism, submitting to Him through obedience, disowning polytheism and polytheists") matches the package. A separate "General Islam" entry (1023) exists; do not confuse. |
| Tawhid | Tawhid / Oneness of God | **3529**, "Monotheism" | 10482, "Monotheism"; sub-entries 10483 (worship), 10485 (lordship), 10484 (names and attributes) | **Conflict**: dictionary says "Monotheism". Recommended answer to "Translate tawhid into English": keep the term **Tawhid**, give the dictionary equivalent "Monotheism", and add the one-line explanation (package: not merely numerical oneness). Raise with organisers. |
| Ibadah | Worship | **6732**, "Worship" (+ Arabic article `/t/1817`) | 15008, "Worship" | Definition ("comprehensive name for all that Allah loves and is pleased with of words and deeds, hidden and apparent") matches package. |
| Nubuwwah | Prophethood | **10342**, "Prophethood" (Prophet: 10343) | Arabic page `ar/browse/term/7365` (نبوة); EN title likely "Prophethood" (NLC) | The two sources word the definition differently; pick one, do not merge. |
| Wahy | Revelation | **10849**, "Revelation" (+ `/t/2002`) | no EN entry found for وحي; related: تنزيل 10476, إلهام 1184 | Package: avoid "inspiration" senses; the dictionary has a separate "Manifest revelation" entry (10851). |
| Sharia | Sharia / Islamic law and guidance | **5979**, "the sharia" | 47755, "Islamic law" | Equivalents differ; package says keep "Sharia" and explain. |
| Hadith | Hadith | **4139**, "Hadith" | 71790, "Hadīth" (category 43) | Definition matches package ("statements, actions, approval, qualities"). |
| Sunnah | Sunnah | **5744**, "The sunnah" (also 5748 Arabic, `/t/509`) | 10811, "The Sunnah" | The sources give more than one sense; the package asks to state which. |
| Fatwa | Fatwa | No entry for الفتوى surfaced. Nearest: **1366** "Issuing a fatwa - الإفتاء" ("to inform of a ruling without obliging"), **12075** "Legal opinion - فتـيا" | 65, "Legal opinion - فتيا" | **Conflict**: sources say "Legal opinion"; package says "Fatwa". Entry for exactly الفتوى is NLC. |
| Dawah | Da'wah / Invitation to Islam | **4892** "الدعوة الإسلامية" (Arabic page only found); articles `/content/5510` | 72440, "Calling to Allah - الدعوة إلى الله" (category 6) | Package: choose equivalent by context. |

Plan: 10 `term` items from Jamhara (primary), each with `title_en` = the dictionary equivalent verbatim, then 15 child terms (salah, zakah, sadaqah, wudu, iman, ihsan, taqwa, halal, haram, amanah, sabr, dua, Ramadan, Hajj, Qur'an). The terminologyenc entry is the cross-check, not a second item.

## 5. Package test questions: where an approved answer can come from

| Test question (package p.6) | Best source in this research | Backup |
|---|---|---|
| Why do Muslims worship the Kaaba? | icadb card **36130** (and 36240/36241 on the qibla); Jamhara "The KaꜤbah" 8189, "The qiblah" 7670 | Bayyinat (search "الكعبة") |
| Was the Quran authored by Muhammad? | icadb 36097 / 36180 / 36181 (nearest, indirect); Bayyinat "مصدر القرآن" | Gentle level-A/B answer plus verse from bank |
| Did Islam spread by the sword? | icadb card **36112** (+ 36193 jihad); Bayyinat (check) | dawa.center has a separate booklet ([file/1721](https://dawa.center/file/1721), SNIP), but Bayyinat is the named FAQ |
| Why do scholars give different rulings? | icadb 36083 (nearest) | dorar.net fiqh pages; Level C answer |
| Tawhid for someone who never heard it | kids curriculum Creed Q4/Q10 + Jamhara 3529 | |
| Translate the word tawhid | Jamhara 3529 "Monotheism" (+ package guidance) | terminologyenc 10482 |
| Hostile "Why does Islam prohibit X?" | icadb 36234 / 36236 as models of tone | |
| Personal fatwa | no source needed; Jamhara fatwa entries (1366, 12075) support the definition | |

## 6. Recommended use per bank section (term, faq, aqidah)

### 6.1 `term`

- **Source:** Jamhara dictionary entries by hand (allowed site, priority per package p.4). Cross-check each against terminologyenc, but one item = one source.
- **Item:** `title_ar` = term with tashkeel as shown; `title_en` = the page-title English equivalent verbatim (e.g. "Monotheism"); `arabic_text` = Arabic definition verbatim; `english_text` = English definition verbatim from the `/en` page; `translation_name` = "Al-Jamhara Islamic Dictionary (en)"; `source_url` = the `/dictionary/word/{id}/en` URL; `keywords_*` = spellings and the English equivalent.
- **Agent behaviour:** for "translate X", return the dictionary equivalent first, then the package's usage guidance as a prompt rule (keep the Arabic term where the package says so).
- **Count:** 10 package terms + 15 child terms = 25 (the plan's target).
- **Manual cost:** about 25 pages at 5 s apart.

### 6.2 `faq`

- **Primary (mandated): Bayyinat** from the local PDF, 15–25 items, short-answer excerpts (section 2.8).
- **Proposed second source: icadb Q&A encyclopedia 110** (and a handful from 102), scripted from the keyless JSON export, ~30 child-suitable cards from the table in 2.4, `source_url` = `https://islamenc.com/ar/enc-cards/{enc}/card/{id}`, `book` = encyclopedia name (≤100 chars), `number` = `card {id}` (≤30 chars), `translation_name` = "icadb export 2026-10-04, card v1.0" (keeps the version, which the IslamHouse-hub README asks to keep). Needs organiser OK and `islamenc.com` in `SOURCE_SITE_CHOICES`.
- **Children's curriculum Q/A** (section 3) can go in as `faq` or `aqidah`.
- **Never copy** cited verses from either source; link bank verses.
- **Sensitive list**: icadb 26015 and kids creed Q5 ("Where is Allah?") stay out until signed off.

### 6.3 `aqidah`

- **Primary candidates:** the kids curriculum Creed section (9 safe items), Names of Allah pages (`anees.islamenc.com`, 6–10 child-friendly names such as Ar-Rahman Ar-Rahim, Al-Qarib, Ar-Rafiq, Ar-Ra'uf, Al-Khaliq, Al-Latif), and terminologyenc Creed terms as supporting vocabulary.
- **Constraint:** the package p.3 names "first three Islamic centuries" or dorar.net/aqeeda for creed; the Association platforms are modern. Treat as pending the organisers' answer (Q3); if refused, aqidah comes only from dorar.net (manual) and these sources stay `faq` or `term`.
- **Names of Allah:** one item per name; excerpt = the page's explanation; the quoted saying on the page is not copied.

### 6.4 Schema and tooling notes for task 01 (migration owner)

| Item | Detail |
|---|---|
| `SOURCE_SITE_CHOICES` | Add `islamenc.com`, `terminologyenc.com`; consider `islamhouse.com`. Django records `choices` in migrations, so this must ride on the task-01 migration with `title_*`, `keywords_*`, `related`. `clean()` already accepts subdomains (`kids.islamenc.com`). |
| `number` max 30 | Fits `Q57 · p. 312` and `card 36130`. |
| Version info | No field for a source-card version; use `translation_name` as free provenance. |
| `AGENTS.md` | "FAQ: Bayyinat" and "Terms: islamic-content.com" would need an amendment if the second sources are approved. |

## 7. Risks

| Risk | Mitigation |
|---|---|
| Bayyinat text layer garbles Arabic; page numbers drift | Glyph-level extractor, page-image side by side, three-page spot check |
| Publisher rights on Bayyinat | Gitignore PDF and full text; commit short excerpts only after the organisers answer |
| "Where is Allah?" appears in two candidate sources with a location-stating answer | Sensitive list, lead or scholar sign-off |
| Dictionary vs package equivalents differ (Monotheism/Tawhid, Legal opinion/Fatwa, the sharia/Sharia) | Ask organisers; meanwhile follow the package for the answer text and cite the dictionary as the equivalent |
| icadb and the MCP may block scripted clients (the MCP does: Cloudflare 1010) | Use a normal browser from the lead's laptop for first contact; send one request at a time, a plain User-Agent, no retries after a block |
| Search-extract wording differs from the live page | Every SNIP fact is re-checked in the browser step before any item is seeded |
| icadb Q&A is Arabic only | Fine for `arabic_text`; `english_text` stays blank |
| Third-party repos (E1–E6) may be wrong or stale | They are used for URLs and structure only; no text is taken from them |

## 8. Questions for the organisers

1. **Bayyinat rights.** May we commit short excerpts (1–3 paragraphs per question, with book title, question number and page) to our open repo and show them to parents in the dashboard? Which edition and printing should page numbers refer to?
2. **Scope of "approved".** The p.3–4 field table names dorar.net, dawa.center, islamic-content.com, Shamela. Pages 8–11 describe the Association's platforms. May we use the **icadb/islamenc Q&A cards** (543), **terminologyenc.com**, and **kids.islamenc.com** as approved sources for `faq`, `term` and `aqidah`, with the same attribution rules as the other sources?
3. **The children's curriculum.** Is «ما لا يسع أطفال المسلمين جهله» acceptable as the creed source (p.3 says early sources or dorar.net/aqeeda)? Is its answer to "Where is Allah?" the expected one, or should the agent give a gentler general answer and a referral (Level C)?
4. **Tawhid.** For "Translate the word tawhid into English", which is the approved output: the dictionary's "Monotheism", or the package table's "Tawhid / Oneness of God"? Same question for fatwa ("Legal opinion" vs "Fatwa") and sharia ("the sharia"/"Islamic law" vs "Sharia / Islamic law and guidance").
5. **Machine access to Jamhara and terminologyenc.** Is there an export or API for the dictionary and the terms encyclopedia (terminologyenc mentions "various electronic formats")? robots.txt limits bots on Jamhara; may participants fetch about 30 pages by hand, politely?
6. **icadb API.** Where are the docs reachable by hackathon participants? Is the `…/cards/latest/` export meant for public use, what are the rate limits and licence, are English translations of the Q&A cards coming, and is `external_id` guaranteed stable? Which attribution wording do you require?
7. **MCP.** Is there an allow-listed way for scripts to reach `mcp.islamiccontent.org` (it returns Cloudflare 1010)? Does it expose islamenc, terminologyenc or Byenah tools, as p.9 implies, or only QuranEnc, HadeethEnc and IslamHouse, as its page says?
8. **"Why do scholars give different rulings?"** Which source do you expect for this test question? It does not look like part of Bayyinat's scope.
9. **"Bayyinat" names.** Does p.12's Tafsir Center "Bayyinat" app refer to the Ramadan Qur'an programme, or to the Q&A book on p.4? (We read them as different.)
10. **English.** Is there an English edition of the Bayyinat book and of the Q&A cards with page or card numbers, so that English-speaking parents can be shown the source in English?

## 9. Manual / Cowork steps for the lead's laptop

Use a normal browser (Cowork browser is fine), one page at a time, 5+ seconds apart, no scripts against Jamhara or the MCP. Save everything into `backend/session_moral_context/content/tools/.cache/r2/` (gitignored; keep a `NOTES.txt` with URL, date and time of each save). Never paste keys into notes.

| Step | URL | What to do and save |
|---|---|---|
| **A. Bayyinat PDF** | the local `dawa-7937-bayyinat.pdf` | Record file size, SHA-256, page count (other team: 1,259). Open the colophon page: save publisher, year, edition, **copyright statement** (photo or text). Save the TOC pages (first ones before question 1) as images. Check 3 pages: PDF page index vs printed page number. Run `pdffonts` (or PyMuPDF) and note the font names (QCF, Manal, DINNext, KFGQPCArabicSymbols). Try `pdftotext -layout` on 2 pages; save the result to show whether the Arabic is garbled. |
| B. Bayyinat page | `https://dawa.center/file/7937?lang=en` | Is there an English file link? Save its URL and size only. |
| C. Jamhara | `https://islamic-content.com/robots.txt` and the 10 pages `https://islamic-content.com/dictionary/word/{1018,3529,6732,10342,10849,5979,4139,5744,1366,4892}/en` (+ `/12075/en`) | Save robots.txt. For each page copy: title, Arabic definition, English equivalent, English definition, URL. Look for the entry for **الفتوى** and **الدعوة** (use the site search) and record their ids. |
| D. terminologyenc | `https://terminologyenc.com/robots.txt`; `https://terminologyenc.com/en` (look for download, export, API, "for developers" links); term pages `/en/browse/term/{43613,10482,10483,15008,47755,71790,10811,65,72440}` and `/ar/browse/term/7365` | Save robots.txt and a screenshot of one term page showing the fields. Note any export link and its terms. Search for وحي and نبوة and record their ids. Save the four category pages (3, 4, 5, 43) for term counts. |
| E. icadb docs | `https://icadb.com/api/docs` | Save the page (PDF). Note: list of encyclopedias and ids, search endpoint, auth, rate limits, licence. |
| F. icadb export test | `https://icadb.com/api/encyclopedias/110/cards/latest/?page=1&page_size=5` | One request. Save the JSON. Confirm fields (`external_id`, `latest_version`, `sentences`, `lookup_items`). If it works, one request with `page_size=1000` for all 202 cards of encyclopedia 110 and one for 102; save to `r2/icadb-110.json`, `r2/icadb-102.json`. Record any `Retry-After`, or a block page. |
| G. islamenc cards | `https://islamenc.com/ar/enc-cards/110/card/36130` and the same with `/en/` | Does an English version exist? Save both. Open `https://s.islamenc.com/lang/en` and `https://islamenc.com/en/` and copy the list of encyclopedias with their ids (looking for Names of Allah, terms, places, figures). |
| H. Kids curriculum | `https://kids.islamenc.com/ar/home` and `…/ar/browse/category/{10,20,30,40,50,60,70,80,90}` | Save each category page as PDF. Copy the Arabic creed Q/A (10 items) to a text file and mark the "Where is Allah?" one. Note whether each answer cites verses or hadith and how. |
| I. Kids curriculum PDFs | `https://islamhouse.com/ar/books/2829179/`, `https://byenah.com/en/discover-islam/5138`, `https://d1.islamhouse.com/data/en/ih_books/single3/en-what-muslim-children-must-know.pdf` | Download the Arabic and English PDFs; save edition, year, publisher and licence line. |
| J. Names of Allah | `https://anees.islamenc.com/ar/page/6`, `/ar/page/46`, `/ar/page/76`, `/ar/page/45`, `/ar/page/18`, `/ar/page/40` (and the `/en/` versions) | Do Arabic pages exist? Save text; list every verse or hadith quoted on each. |
| K. Byenah API | `https://byenah.com/ar/api`; the Postman collection and environment links in section 2.6 | Download both JSON files; save the docs page. |
| L. IslamHouse API | `https://documenter.getpostman.com/view/7929737/TzkyMfPc` | Export the collection (JSON). Call `categories/showall/en/json` once and find "Prophets' Stories" (5387) and any "Muslim child" category; save the ids. |
| M. Risala | `https://risala.prh.gov.sa/en/Api/content`, `https://risala.prh.gov.sa/en/content/251` | Save the API doc; note whether `api_key` is needed. Low priority. |
| N. MCP | `https://mcp.islamiccontent.org/` and `/terms.html`; add `https://mcp.islamiccontent.org/mcp` as a connector in claude.ai | Save both pages. Ask the connector to list its tools and run `search` for "tawhid" and "Kaaba"; save which source branches answer. |
| O. robots.txt | `https://{islamenc.com,icadb.com,byenah.com,dawa.center,risala.prh.gov.sa}/robots.txt` | Save all. |

After step A the lead can tell the agents: (1) TOC text, (2) 3 verified page numbers, (3) the extractor test result. After steps C, D, F, H the `term`, `faq` and `aqidah` drafts can start.

## 10. URL pattern cheat sheet

| Site | Pattern | Tag |
|---|---|---|
| islamenc card | `https://islamenc.com/{lang}/enc-cards/{enc}/card/{id}` · `https://islamenc.com/{lang}/enc/{enc}/card/{id}` | VC / SNIP |
| islamenc Quran | `https://islamenc.com/{lang}/quran/{surah}[/{ayah}]` | VC / SNIP |
| kids | `https://kids.islamenc.com/{lang}/home` · `/browse/category/{10..90}` · `/browse/quiz/rand` | SNIP |
| Names of Allah | `https://anees.islamenc.com/{lang}/page/{n}` | SNIP |
| icadb export | `https://icadb.com/api/encyclopedias/{enc}/cards/latest/?page={n}&page_size=1000` | VC |
| terminologyenc | `https://terminologyenc.com/{lang}/browse/term/{id}` · `/browse/category/{id}` | SNIP |
| Jamhara | `https://islamic-content.com/dictionary/word/{id}[/{lang}]` · `/t/{id}` · `/hadeeth/{id}/en` · `/post/{id}` | SNIP |
| Byenah | `https://byenah.com/{lang}/Api/…` · `/{lang}/discover-islam/{id}` | VC / SNIP |
| IslamHouse API | `https://api3.islamhouse.com/v3/{key}/…/json` | VD / VC |
| Risala | `https://risala.prh.gov.sa/{lang}/Api/…` · `/{lang}/content/{id}` | VC / SNIP |
| MCP | `https://mcp.islamiccontent.org/mcp` | VD |
| Bayyinat | `https://dawa.center/file/7937` (page) · `#p<N>` (our label) | VD |
