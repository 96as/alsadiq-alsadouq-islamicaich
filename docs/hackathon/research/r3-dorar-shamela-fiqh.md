# R3: Dorar, Shamela, Kuwaiti Fiqh Encyclopedia, early sources, hadith routes

Research agent 3 of 5. Date of research: 4 Oct 2026 (container), updated with the lead's Cowork pages saved on 5 Oct 2026. Nothing in this file is committed scripture or hadith text. Short quotes only, URLs for everything else.

## 0. Summary (read this first)

1. **Dorar's official hadith API is tiny and undocumented beyond one parameter.** The only documented request is `https://dorar.net/dorar_api.json?skey=<text>` with optional `&callback=?` (JSONP). No filters, no terms, no rate limit are written on the page (V-SAVED). Filters (`s[]`, `m[]`, `d[]`, `t`, `st`, `page`, `xclude`, `rawi[]`) come from third-party wrappers and are NOT confirmed server-side (LIVE?).
2. **The real response shape is `{"ahadith":{"result":"<HTML string>"}}`**, not the array-with-`.th` shown in Dorar's own jQuery example (V-CODE, real capture of 2 Nov 2025). The HTML carries narrator, grader, source book, page/number and grade. **It carries no hadith id and no URL.**
3. **A stable per-hadith URL is `https://dorar.net/h/<8-char id>`.** The id exists only in the site-search HTML (`tag="..."` attribute), not in the API. `https://dorar.net/hadith/sharh/<numeric id>` exists only for hadith that have a sharh (V-CODE).
4. **For Bukhari and Muslim, Dorar prints the compiler as grader and a bracketed grade**, for example grader "البخاري", book "صحيح البخاري", number "2989", grade "[صحيح]" (V-CODE capture). Dorar's book cards say its Muslim is the Fuad Abd al-Baqi edition (Isa al-Halabi, 1374 H) and its Bukhari is the Salafiyya edition (Muhibb al-Din al-Khatib, 1400 H).
5. **The Dorar API is treated as UNAVAILABLE.** On 5 Oct the lead reported that `dorar_api.json` is blocked even in a normal Chrome browser on the lead's home network, and a direct request returned 403 (V-SAVED Cowork README plus the lead's update). Dorar encyclopedia pages, however, load fine in a browser. So "script or JSONP against the API" (routes A and A2) is demoted to an optional bonus, and the hadith route is built on **pages that a human can open**: the site's hadith search page (a plain GET form at `/hadith/search`) and `/h/<id>` pages (still LIVE?, check L3).
6. **dorar.net/tafseer is approved by name** for tafsir (V-SAVED, resource package row "or dorar.net/tafseer"). That settles the al-Tabari question in practice: use Dorar's tafsir text (which cites Ibn Jarir with volume/page) as the primary route; direct Tabari quotes (d. 310 H) stay optional and need an organiser answer.
7. **Shamela is a heavy, offline route and gives no per-hadith grade.** Shamela hadith URLs use internal page ids, not hadith numbers (V-SEARCH). The desktop download is an "empty" build plus a separate full data folder (V-SAVED). Good as a verbatim backup and for early sources; bad as the main hadith route.
8. **Shamela mirrors Dorar's own fiqh and creed encyclopedias** (book 38056 and 38058) and the Kuwaiti Fiqh Encyclopedia (book 11430). That gives a second, scriptable-offline way to reach Dorar content if dorar.net stays blocked.
9. **Recommended hadith route (revised after the lead's update):** the lead runs about 35 filtered searches in the Dorar hadith search page (Bukhari and Muslim only, graded sahih) and saves each results page (HTML, or text if only text can be saved). An offline parser, written from the known page structure, turns the saved pages into candidate items. The lead and the curator pick 2 to 3 per value, and each pick is cited with a search permalink or `https://dorar.net/h/<id>`. Fallback: manual copy of single `/h/<id>` pages. Backup for text: Shamela. Optional discovery and possible alternative source: HadeethEnc (section 8).

## 1. Evidence legend

| Tag | Meaning (maps to the labels the lead asked for) |
|---|---|
| **V-SAVED** | VERIFIED-FROM-SAVED-PAGE: read in `backend/session_moral_context/content/tools/.cache/cowork/*.md`, saved by the lead's Cowork browser on 2026-10-05 |
| **V-CODE** | VERIFIED-FROM-CODE/DOCS: read in open-source code, docs or captured fixtures (URL given) |
| **V-SEARCH** | VERIFIED-FROM-SEARCH-RESULT: the URL and page title were returned by web search. The page itself was not fetched (dorar.net, shamela.ws and bohoth.awqaf.gov.kw are blocked here) |
| **LIVE?** | NEEDS-LIVE-CHECK: plausible, not verified. Section 11 lists the exact check |
| **RECALL** | My own background knowledge. Treat as LIVE? |

Core sources I read: the dorar API doc and four encyclopedia samples saved by Cowork; the Dart package `dorar_hadith` 0.4.0 (MIT) downloaded from `https://pub.dev/api/archives/dorar_hadith-0.4.0.tar.gz`, including its `test/fixtures/api_snapshots/*.json` (real HTTP responses captured 2 Nov 2025); the Node wrapper README `https://raw.githubusercontent.com/AhmedElTabarani/dorar-hadith-api/main/README.md` and its `data/*.json`; the npm package `shamela` 1.5.3 (MIT, source in the tarball); READMEs of `alhoqbani/shamela-mcp`, `ammusto/shamela-extractor`, `yshalsager/shamela-epub-exporter`; the npm client `@wursha/ngx-hadeethenc-api`.

## 2. Dorar hadith API (dorar.net/article/389)

### 2.1 What the official page says (V-SAVED, `dorar-api-doc.md`)

| Item | Content |
|---|---|
| Purpose | "a service for site and forum owners to show Hadith Encyclopedia search results on their sites using JSON" |
| Method 1 | JSONP with jQuery: `https://dorar.net/dorar_api.json?skey=<text>&callback=?` |
| Method 2 | PHP: `file_get_contents("https://dorar.net/dorar_api.json?skey=" . $k)` then `json_decode` |
| Ready-made code | `https://dorar.net/files/dorar_json_api.js.zip` and `https://dorar.net/files/dorar_api.zip` (not downloaded) |
| Support | by email (address obfuscated on the saved page) |
| Terms, limits, filters, attribution | **none written on the page** |
| Footer | all rights reserved to Al-Durar al-Saniyyah Foundation, 1421-1448 H |
| Stale example | the jQuery code iterates `data.ahadith` and reads `item.th`. The captured real response (2.3) has `ahadith` as an object with one key `result`, so the example no longer matches. LIVE? |

### 2.2 Parameters

| Param | Meaning | Values | Evidence |
|---|---|---|---|
| `skey` | search text (API endpoint). The site endpoint uses `q` | Arabic, URL-encoded | V-SAVED |
| `callback` | JSONP wrapper | `?` or a function name | V-SAVED |
| `page` | page number, about 15 results per page | 1... | V-CODE (Dart `HadithService.apiPageSize = 15`; wrapper README) |
| `st` | match mode | `w` all words, `a` any word, `p` exact phrase | V-CODE (wrapper `data/method-search.json`, Dart `search_method.dart`) |
| `t` | zone | `*` all, `0` marfu', `1` qudsi, `2` athar of Companions, `3` sharh | V-CODE (`data/zone-search.json`) |
| `d[]` | grade class | `0` all, `1` hadith graded sahih, `2` chain graded sahih, `3` hadith graded weak, `4` chain graded weak | V-CODE (`data/degree.json`) |
| `m[]` | muhaddith id (the grader) | see 2.2a | V-CODE (`data/mohdith.json`, 197 entries) |
| `s[]` | source book id | see 2.2a | V-CODE (`data/book.json`, 685 entries) |
| `rawi[]` | narrator id | `data/rawi.json` | V-CODE |
| `xclude` | words to exclude | text | V-CODE |

The Dart client sends exactly these keys to `dorar_api.json` (`lib/src/http/endpoints.dart`, `query_serializer.dart`). Whether the server honours each filter on the API endpoint (not only on the HTML search page) is **LIVE?**. Arrays use the form `s[]=6216&s[]=3088`.

The human-facing search page uses the same keys. Its form is a plain GET form `action="/hadith/search"` with fields `q`, `st`, `t[]`, `d[]`, `m[]`, `s[]`, `rawi[]`, `xclude` (V-CODE, captured `hadith_search_site.json`). So any filtered search the lead builds in the UI can be reproduced and shared as a permalink URL, for example `https://www.dorar.net/hadith/search?q=<word>&s[]=6216&s[]=3088`.

Wrapper rate numbers (100 searches per IP per day, 5 s cache) are the wrapper's own limits, not Dorar's.

**2.2a Ids we need** (V-CODE, `data/book.json` and `data/mohdith.json` in the Node wrapper repo; ids 6216 and 3088 also confirmed by captured book cards):

| Filter | Id | Name |
|---|---|---|
| `s[]` | 6216 | Sahih al-Bukhari (Salafiyya ed., Muhibb al-Din al-Khatib) |
| `s[]` | 3088 | Sahih Muslim (Fuad Abd al-Baqi ed.) |
| `s[]` | 13457 | al-Arba'in al-Nawawiyya |
| `s[]` | 11155 | Riyad al-Salihin |
| `s[]` | 2463 | Sahih al-Adab al-Mufrad (Albani) |
| `s[]` | 531 / 3741 / 561 | Sahih al-Targhib / Sahih al-Jami' / al-Silsila al-Sahiha |
| `s[]` | 6267 / 13509 / 13508 | Sunan Abi Dawud / Tirmidhi / Nasa'i |
| `m[]` | 256 / 261 | al-Bukhari / Muslim |
| `m[]` | 1420 | al-Albani |
| `m[]` | 179 / 204 / 241 | Malik / al-Shafi'i / Ahmad |

### 2.3 Response format (V-CODE, real capture `test/fixtures/api_snapshots/hadith_search_api.json`, 2025-11-02, Cloudflare in front, `content-type: application/json`)

```
{"ahadith":{"result":"<head>...canonical link...</head>
<div class=\"hadith\" style=...>1 -  <span class=\"search-keys\">word</span> ... </div>
<div class=\"hadith-info\">
  <span class=\"info-subtitle\">الراوي:</span> NARRATOR
  <span class=\"info-subtitle\">المحدث:</span> GRADER
  <span class=\"info-subtitle\">المصدر:</span>  BOOK
  <span class=\"info-subtitle\">الصفحة أو الرقم:</span>  PAGE-OR-NUMBER
  <span class=\"info-subtitle\">خلاصة حكم المحدث:</span>  <span>GRADE TEXT</span>
</div>
--------------
<br/>  ...next hadith... "}}
```

Notes that matter for a parser:
- HTML is not always well-formed (a stray `</span>` after the narrator). The Dart client uses a regex `<span class="info-subtitle">LABEL:</span>\s*([^<]+)` on `.hadith-info`, with the hadith text taken from the previous sibling `div.hadith` and the `N -` list prefix removed.
- Highlight markup `<span class="search-keys">` wraps matched words and must be unwrapped, not deleted.
- **Some entries are partial quotations** ending in ". . ." or "... الحديث" (visible in the capture, from commentary books). A completeness check is needed before an entry is accepted.
- The same hadith appears many times, once per citing book. Filtering by `s[]=6216&s[]=3088` is meant to cut this (LIVE?).
- No hadith id, no URL, no `takhrij` in the API (the "specialist" fields exist only on the site endpoint).

### 2.4 Site endpoint (richer, the only source of the hadith id)

`https://www.dorar.net/hadith/search?q=<text>&page=N&s[]=...&m[]=...&d[]=...` returns an HTML page with about 30 results (V-CODE, wrapper README and capture `hadith_search_site.json`). Each result block (`div.border-bottom`) contains:

| Data | Where in the HTML (V-CODE) |
|---|---|
| hadith text | `h5` |
| grade | `خلاصة حكم المحدث` strong tag, bracketed for Sahihayn |
| narrator, grader, book, number | strong tags; grader link `/hadith/mhd/<id>`, book link `/hadith/book-card/<id>` |
| thematic categories | `التصنيف الموضوعي`, links `/hadith-category/cat/<hash>` |
| **hadith id** | `<a tag="<id>" href="https://dorar.net/h/<id>">` (share button) |
| sharh id | `<a xplain="<numeric id>">` (absent or `0` when no sharh) |
| similar / sources / alternate | `/h/<id>?sims=1`, `?osoul=1`, `?alts=1` |
| citation helper | copy button `data-clipboard-text="<ref>الراوي: ... | المحدث: ... المصدر: ... | الصفحة أو الرقم: ... خلاصة حكم المحدث: ... موقع الدرر السنية</ref>"` |

The copy string ends with the credit "موقع الدرر السنية": Dorar's own citation convention, which we should mirror in the parent card.

### 2.5 Mapping to our schema

Examples are metadata only, taken from the 2025-11-02 capture `sharh_search.json` (V-CODE). Hadith texts are deliberately not reproduced.

| Our field | Dorar source | Example | Notes |
|---|---|---|---|
| `type` | constant | `hadith` | |
| `arabic_text` | `div.hadith` / `h5` text | (verbatim, with tashkeel) | strip the `N -` prefix and unwrap `search-keys` only. Reject entries with ". . ." fragments |
| `book` | المصدر | `صحيح البخاري` / `صحيح مسلم` | our README example uses English ("Sahih al-Bukhari"). Pick **one** canonical string per book (a dict keyed by Dorar book id 6216 / 3088), because the unique key is `(book, number)` |
| `number` | الصفحة أو الرقم | `2989` (Bukhari), `720`, `1009`, `1552` (Muslim) | see 2.6 on numbering and collisions |
| `narrator` | الراوي | `أبو هريرة`, `أبو ذر الغفاري`, `جابر بن عبدالله` | brackets such as `[عمر بن الخطاب]` are Dorar editorial marks (V-CODE capture) |
| `grade` | خلاصة حكم المحدث | `[صحيح]` | keep or strip the brackets: decision for the lead (section 10, Q1) |
| `grader` | المحدث | `البخاري` / `مسلم` | for Sahihayn Dorar lists the compiler |
| `source_site` | constant | `dorar.net` | allowed by `HADITH_SITES` |
| `source_url` | `https://dorar.net/h/<id>` | ids seen: `Tszg5ZRJ` (Bukhari 2989), `wGEIpaDL` (Muslim 720), `kUZHQv3G` (Muslim 1009), `xXI2P2Zv` (Muslim 1552) | needs the site HTML. `www.dorar.net` also passes the host check in `ContentItem.clean()` |
| `english_text`, `translation_name` | none | blank | Dorar publishes no English. Leave blank (rule: English only if the source publishes it) |

Field-length risk: `grade` is `max_length=100`. Dorar grade strings for non-Sahihayn books can be long sentences (the capture has one of about 70 characters). Do not truncate silently.

### 2.6 Numbering and uniqueness

- **Dorar:** Bukhari = book 6216, Salafiyya edition (Muhibb al-Din al-Khatib, al-Maktaba al-Salafiyya, Cairo, 1st ed. 1400 H). Muslim = book 3088, Fuad Abd al-Baqi (Dar Ihya al-Kutub al-Arabiyya, Isa al-Babi al-Halabi, 1st ed. 1374 H). Both from captured book cards `book_sahih_bukhari.json` and `book_sahih_muslim.json` (V-CODE).
- **Which numbering:** the lead's brief says Bukhari follows Fath al-Bari numbering (1-7563) and Muslim follows Fuad Abd al-Baqi (1-3033). The Dorar tafsir page for Surat al-Fatiha cites "رواه البخاري (756)، ومسلم (394)" for the Fatiha-in-prayer hadith, consistent with those schemes (V-SAVED for the citation; the equivalence itself is RECALL). **Cross-check one number on both sites before relying on it (section 11, L9).**
- **Collision risk (LIVE?):** in Abd al-Baqi's Muslim, several variant narrations can share one main number. The unique constraint `uniq_hadith_book_number` would then reject the second. Decide a suffix convention (for example `1009`, `1009-2`) before the first import.

### 2.7 Is Dorar's grading the "approved authenticity grading"?

- The package row for hadith says: Sahih al-Bukhari and Sahih Muslim; other books only after verification; "Consult dorar.net/hadith or approved editions ... in the Shamela Library"; "Do not attribute a hadith without including its source and an approved authenticity grading in the data" (V-SAVED via the repo's resource package, page 3).
- Page 15 of the package describes Dorar's Hadith Encyclopedia as having "scholars' authenticity judgments, their sources".
- So Dorar is the **named reference for gradings**, and each grade there is attributed to a named muhaddith. That is a strong argument for "approved", but the package never defines the phrase. **Ask the organisers (Q1).**
- Bracketed grades: a search snippet of Dorar's methodology says the compilers put paraphrases of the muhaddith's wording in square brackets, and that "it is authentic" statements are recorded as `[صحيح]` (V-SEARCH, `https://dorar.net/article/56` and `/article/77`; full text not read). For Sahihayn entries the bracket therefore appears to mean "Dorar's wording of the compiler's condition", not a separate verdict. LIVE?: read both articles (L5).

### 2.8 Terms, rate, attribution

| Question | Finding | Evidence |
|---|---|---|
| Written API terms | none on `article/389` | V-SAVED |
| Rate limit | none written. The Dart client handles HTTP 429, so some limiter may exist | V-CODE |
| Copyright | footer "all rights reserved"; a search snippet of `https://dorar.net/article/111` says non-downloadable material such as the Hadith Encyclopedia may not be copied for use outside the site, but copying a search result and publishing it for benefit is fine | V-SAVED (footer), V-SEARCH (article 111, snippet only) |
| Attribution | Dorar's own copy button appends "موقع الدرر السنية" | V-CODE |
| Free widget for sites | the "search window" for site owners is free | V-SEARCH (`https://dorar.net/article/2107`) |
| Bot protection | Cloudflare. A third-party wrapper stopped because of it (`https://github.com/AhmedElTabarani/dorar-hadith-api/issues/29`). From the lead's Mac: Chrome blocked the API URL and a direct request returned 403 (V-SAVED, Cowork README). **Update from the lead, 5 Oct: the API URL is blocked even in a normal Chrome browser on the lead's home network; encyclopedia pages still load.** So the API is UNCONFIRMED and likely unavailable to us | V-CODE, V-SAVED, lead's report |

Whether `/hadith/search` and `/h/<id>` (same site, different paths) are reachable is not yet known (L3 and L4). Practical rules for us: human-paced browsing, cache every saved page, a total of a few hundred page views, credit "الدرر السنية" on the card, and email Dorar support once as a courtesy. Do not try to get round the block.

## 3. Dorar encyclopedias (tafsir, aqidah, fiqh, history)

No API is documented for any of them. The only official API is the hadith one (2.1). Each encyclopedia has an HTML search form on the site (V-SAVED). Dorar also sells or distributes PDFs, for example "التفسير المحرر 1-44" at `store.dorar.net` (V-SEARCH, titles only; price and licence LIVE?).

| | Tafsir | Aqidah | Fiqh | History |
|---|---|---|---|---|
| URL pattern | `https://dorar.net/tafseer/<surah>` = surah introduction (V-SAVED: `/tafseer/1` is al-Fatiha). `/tafseer/<surah>/<n>` = nth verse-group page of that surah, **n is not an ayah number** (V-SEARCH: `/tafseer/4/18` = al-Nisa 58-59, `/tafseer/98/1` = al-Bayyina 1-5) | `https://dorar.net/aqeeda/<id>[/<slug>]` (V-SAVED `/aqeeda/8`; V-SEARCH slugs) | `https://dorar.net/feqhia/<id>[/<slug>]` (V-SAVED `/feqhia/6`; V-SEARCH `/feqhia/669` = Book of Prayer) | `https://dorar.net/history/event/<id>` (V-SAVED `/history/event/1`) |
| Granularity | one page per verse group; intro page per surah | very fine: `/aqeeda/8` is a single "branch" page of one sentence | medium to long: `/feqhia/6` is a whole "mabhath" on types of water | one event per page, hijri and Gregorian year in the header |
| Sections (V-SAVED) | غريب الكلمات، مشكل الإعراب، المعنى الإجمالي، تفسير الآيات، الفوائد التربوية، الفوائد العلمية واللطائف، بلاغة الآيات (the intro page also has names, virtues, Makki/Madani, aims) | definition then footnotes ("عرض الهوامش"), "انظر أيضا" links | disagreement with 2 opinions and evidence, hadith with takhrij, plus a block "المادة في سؤال وجواب" (undiacritised Q and A) | "تنويه: سرد تاريخي مختصر، مجرد من التعليق والتحليل" |
| How it cites | inline name with volume/page, for example Ibn Jarir (1/105), numbered footnotes `[n]`, hadith as "رواه البخاري (756)، ومسلم (394)" | footnotes with author, title, volume/page (for example Ibn Faris 4/86) | scholars quoted with title and volume/page, hadith with graders ("صححه البخاري ...") | inline attribution ("قال ابن القيم", "روى ابن إسحاق") but **no volume/page footnotes in the sample** (0 footnote markers) |
| Reviewers shown on the methodology panel (V-SAVED) | named professors (Khalid al-Sabt, Ahmad Saad al-Khatib approved; al-Shahri, al-Tayyar, al-Aydi) | **none shown** in the panel | methodology approved by the Saudi Fiqh Association chaired by Sa'd al-Khuthlan | named history professors |
| Suitable for short child excerpts | **High** for "المعنى الإجمالي", "غريب الكلمات", "الفوائد التربوية" (lessons per verse, close to our values). Not verified on a verse page yet: only the surah intro was saved (LIVE?) | **Medium.** Fine-grained pages give 1 to 3 sentence excerpts. Many topics are sensitive (names and attributes, qadar, sects); stay on pillars of faith | **Low to medium.** Pages are adult-level, list disagreements and often favour one view (the encyclopedia states its aim as "knowing the preponderant view", V-SEARCH). Quote only statements of agreement | **Medium.** Short and readable, but weaker traceability and some reports of mixed strength (event 1 itself notes disagreement on the birth date) |
| Which package row | tafsir ("or dorar.net/tafseer") | aqidah ("or dorar.net/aqeeda") | general fiqh ("or dorar.net/feqhia") | sirah and history ("or dorar.net/history") |

Other observations:
- Every encyclopedia page has an "الرابط المختصر" (short link) control (V-SAVED). What URL it yields is LIVE? (L7).
- A toggle "بدون تشكيل" removes diacritics (V-SAVED). Save the diacritised version as the source text.
- Dorar also has ethics (`https://dorar.net/alakhlaq/<id>`) and etiquette encyclopedias (V-SEARCH). They fit our values very well, but the package approves only /tafseer, /aqeeda, /feqhia and /history by URL. Package page 15 mentions "ethics, Islamic etiquette" as part of Dorar. **Ask (Q3).**
- Source-site constraint: `content-structure-plan.md` allows tafsir only from quranpedia.net and shamela.ws. Because the package names dorar.net/tafseer, **dorar.net must be added to the tafsir allow-list.**

### 3.1 The al-Tabari (d. 310 H) question

- Package text: tafsir = "Any Islamic sources from the first three Islamic centuries, or dorar.net/tafseer".
- Strictly, the third century ends in 300 H, so Tabari (d. 310) and Ibn Abi Hatim (d. 327) are outside under a "died by 300 H" reading. A looser reading ("works of authors who lived and wrote in those centuries") would include Tabari. Unknown which one the organisers mean (Q2).
- Practical answer: the "or dorar.net/tafseer" alternative is explicit. Excerpts from Dorar's tafsir pages are compliant on their own, and they carry Tabari quotations with volume/page. Use Dorar as primary. Keep direct Quranpedia/Shamela Tabari excerpts as optional, flagged "pending organiser answer".
- Note on what Dorar's own prose is: a modern compilation (the "Tafsir al-Muharrar", about 44 volumes, V-SEARCH) that also cites later scholars (Ibn Kathir, Ibn Ashur). The package rule still holds: show it as the encyclopedia's words and keep the Quran text separate.

## 4. Shamela (shamela.ws)

### 4.1 What `shamela.ws/page/download` offers (V-SAVED, `shamela-download.md`)

| Item | Fact |
|---|---|
| Windows | iso, 150 MB, Windows 7 and later, 32 and 64 bit |
| macOS | dmg, 266 MB, Mojave 10.14 and later, Intel and Apple Silicon |
| Linux | tar, 160 MB, CentOS 7 and later, tested on Fedora, Mint, Arch |
| What it is | the downloadable program is an **empty build** ("النسخة المفرغة"). A separate **full data folder** ("مجلد البيانات التام") converts it to the complete library. Size of that folder is not on the saved page (LIVE?) |
| Storage | all books, notes, settings and sessions live in **one folder named `database`**, portable between Windows, Mac, Linux. Mac path `~/Library/Application Support/Shamela` |
| Site search | content, book names, author names; scoped search by section, author, book, **century (القرون)**; operators `"..."`, `+`, `-`, parentheses |
| Footer | links to Terms (الشروط) and Privacy (الخصوصية). Texts not saved (LIVE?) |
| Project statement | free, non-profit, takes nothing from authors for publishing |

Size of the full library: a Internet Archive upload titled "المكتبة الشاملة الرسمية 4" is described as 8,400 text books and 1,300 image books, 55.5 GB in total, an "Muharram 1446" build (V-SEARCH, search summary of `https://archive.org/details/shamela4_official`, not fetched; LIVE?). The package itself says about 8,000 books, 3,000 authors, 7 million pages.

### 4.2 Internal format

| Layer | Fact | Evidence |
|---|---|---|
| Install layout | `shamela4/database/master.db` (metadata), `shamela4/database/book/` (one SQLite file per book), `shamela4/database/store/` (Lucene indices used by the search) | V-CODE (`https://raw.githubusercontent.com/ammusto/shamela-extractor/main/README.md`) |
| Search engine | Java and Lucene, bundled with the app | V-CODE (`alhoqbani/shamela-mcp` README) |
| Full extraction cost | about 40 GB of disk, about 17 GB CSV and 18 GB JSON, 30+ minutes | V-CODE (`ammusto/shamela-extractor`) |
| Book DB tables | `page(id, content, part, page, number, services, is_deleted)`, `title(id, content, page, parent, is_deleted)` | V-CODE (npm `shamela` 1.5.3, `dist/index.js`) |
| Master tables | `author(id, name, biography, death_text, death_number, ...)`, `book(id, name, category, type, date, author, printed, bibliography, hint, pdf_links, metadata, ...)`, `category(id, name, order)` | V-CODE (same) |
| v4 API | `.../api/master_patch`, `.../api/books/<id>`; **needs an API key by email to mail@shamela.ws**; returns zipped SQLite (`author.sqlite`, `book.sqlite`, `category.sqlite`, plus per-book `.db`) | V-CODE (npm `shamela` README) |
| Text conventions | honorific phrases are stored as single glyphs that tools expand; footnotes follow a separator; hadith wrapped in `<hadeeth-N>` tags; page markers in ⦗ ⦘ | V-CODE (`dist/utils/constants.js`, `content.js`) |

Consequence for "verbatim": any Shamela extraction applies replacements (honorific expansion, tag stripping). The exact expansion strings are the tool's choice (for example one glyph becomes "صلى الله عليه وآله وسلم" in the npm library), which may differ from the printed text. A Shamela-sourced excerpt needs a diff against the web page.

### 4.3 Open-source tools

| Tool | What it does | Licence / access | Fit for us |
|---|---|---|---|
| `ragaeeb/shamela` (npm 1.5.3) | download master and book DBs via the v4 API, parse content | MIT; **API key required** | only if the key arrives (no time) |
| `alhoqbani/shamela-mcp` | 34 read-only tools over a **local Shamela 4 install**: page search, TOC, citation formatting, Quran/tafsir lookup, hadith search | MIT; Windows tested, Mac untested | useful if the lead installs Shamela; also has `shamela_verify_quote` |
| `ammusto/shamela-extractor` | Lucene to CSV to JSON for the whole library | MIT; Java 8+ and Python | overkill for 2 to 10 books |
| `yshalsager/shamela-epub-exporter` | browser extension and desktop app: book to EPUB, also opens `.bok` | open source, personal and educational use | manual per-book export |
| `OpenShamela/shamela_crawler`, `OpenShamela/data` | Scrapy crawler; scraped category/author/book lists | open; `books.json`, `authors.json`, `categories.json` exist in `main` but are **2 bytes (empty) when fetched** | no help |
| `ojuba-org/thawab-lite`, `shaybix/mdb2json`, `boussouira/albahhet` | old `.bok` readers and Lucene searcher | open | legacy |

Do not use the "Golden" Shamela editions or unofficial added books: the package says they are not affiliated with the institution (V-SAVED via the repo package, page 15).

### 4.4 Licence and terms

Shamela states it is free and non-profit (V-SAVED) and that it respects authors' IP under Saudi copyright law (V-SEARCH, `old.shamela.ws` About page snippet). Its API needs a key. The Terms page text is not captured (L8). We are quoting short passages with citation, not redistributing a database. **Never commit a Shamela database or book dump to the repo.**

### 4.5 Book ids and URL patterns for Bukhari and Muslim

URL pattern: `https://shamela.ws/book/<book id>` for the book and `https://shamela.ws/book/<book id>/<page id>` for a page (V-SEARCH). **The last number is an internal page id, not the printed page and not the hadith number.** Evidence from result titles: `book/1727/489` is "ج1 - ص205" and `book/1727/6159` is "ص1873" (V-SEARCH). It is the `page.id` of the book DB (LIVE?, L8).

| Work | Shamela id | Edition per Shamela title | Evidence |
|---|---|---|---|
| Sahih al-Bukhari, Sultaniyya | **1681** | ط السلطانية (Bulaq 1311 H lineage); a search summary says 9 parts and Fuad Abd al-Baqi numbering | V-SEARCH |
| Sahih al-Bukhari, Ta'sil | 1284 | ط التأصيل, 10 parts | V-SEARCH |
| Sahih al-Bukhari, al-Bugha | 735 | ت البغا, 7 parts | V-SEARCH |
| Sahih al-Bukhari with Saharanpuri notes | 907 | ت الندوي | V-SEARCH |
| Sahih Muslim | **1727** | ت عبد الباقي, Isa al-Halabi, Cairo 1374 H | V-SEARCH |
| al-Adab al-Mufrad (Bukhari) | 12991 (ت عبد الباقي, Albani's comments added electronically), 9647 (بأحكام الألباني), 1341 (Sahih), 1346 (Daif) | | V-SEARCH |

Author pages: Bukhari `shamela.ws/author/215`, Muslim `/author/242` (V-SEARCH).

**Mapping a hadith number to a Shamela URL:** no number-addressed URL was found. Options: (a) read the book DB and map number to `page.id` (the `page.number` column and the `<hadeeth-N>` tags may help; semantics LIVE?), (b) use Shamela's site search and copy the page URL by hand. This is the main reason Shamela is a poor primary hadith route.

**Numbering:** Dorar's Muslim (book 3088) and Shamela's Muslim (1727) are the same Abd al-Baqi / Isa al-Halabi 1374 H edition, so numbers should match. For Bukhari, Shamela 1681 follows Fuad Abd al-Baqi's numbering (the Fath al-Bari numbering with repeats, 7,563 hadith) per search summaries, and Dorar uses the Salafiyya edition, which should follow the same numbering. Cross-check on one hadith (L9).

## 5. Kuwaiti Fiqh Encyclopedia (الموسوعة الفقهية الكويتية)

| Question | Finding | Evidence |
|---|---|---|
| Publisher | Ministry of Awqaf and Islamic Affairs, Kuwait, Department of Research and Islamic Encyclopedias | V-SAVED (resource package, page 13) |
| Size | 45 volumes, about 18,500 pages; published 1404 to 1427 H | V-SEARCH (sifatusafwa.com listing; Shamela summary) |
| Structure | alphabetical by term, about 3,000 fiqh terms, covers the four schools plus earlier jurists, with sourced and graded evidence | V-SEARCH (publisher and bookseller snippets) |
| Entry template | each entry typically has definition, related terms, general ruling and where discussed | RECALL, LIVE? |
| Portal | `https://bohoth.awqaf.gov.kw/ar/الموسوعة%20الفقهية` lists parts 1 to 45; **volumes downloadable as Word and PDF** (package says the same) | V-SEARCH, V-SAVED |
| Other formats | mobile app "الموسوعة الفقهية" (iOS and Android), CD | V-SEARCH |
| Shamela | **book 11430**; page URLs such as `shamela.ws/book/11430/17359` (entry "ركن الصوم") | V-SEARCH |
| Suitable for kids' basics (wudu, prayer) | **Medium to low.** Good for cross-school statements and exact terminology, but adult-level and long. The pages that matter are entries like الوضوء، الصلاة، الصوم. Use only sentences that state agreement ("اتفق الفقهاء ...") and add the referral line | RECALL on style, LIVE? |
| `source_site` | `awqaf.gov.kw` is **not** in `SOURCE_SITE_CHOICES`. The Shamela mirror (`shamela.ws/book/11430/<page id>`) fits the current allow-list | V-CODE (`models.py`) |

Dorar's own fiqh encyclopedia is on Shamela as **book 38056** and its creed encyclopedia as **book 38058** (V-SEARCH, titles "الموسوعة الفقهية - الدرر السنية" and "الموسوعة العقدية الدرر السنية"). The Shamela summary for 38058 says it was loaded by automatic digitisation (V-SEARCH, summary), so wording may lag the live site. LIVE?: compare one page. Whether a Shamela copy counts as "dorar.net/aqeeda" is Q4.

## 6. Early sources (first three centuries) per field

All Shamela ids from search-result URLs (V-SEARCH). "Kid fit" is my judgement from titles and snippets (RECALL). Authors outside 300 H are marked.

| Field | Work (author, d. H) | Shamela id | Kid-level verbatim excerpt? |
|---|---|---|---|
| Tafsir | Jami' al-Bayan, al-Tabari (**310**) | 43 (Dar al-Tarbiya wa al-Turath); 7798 (ت التركي, Hajr, 26 vols) | Possible, but isnad-heavy and contains Israiliyyat-type reports. Outside 300 H |
| Tafsir | Tafsir Ibn Abi Hatim (**327**) | 8658 (As'ad al-Tayyib ed.) | Isnad-heavy; outside 300 H |
| Tafsir | Tafsir Abd al-Razzaq (211) | 21791 | A page titled "حديث نمروذ" shows story material (V-SEARCH); careful selection |
| Tafsir | Tafsir Mujahid (104) | 12810 | **Best early fit:** short, mostly word-level glosses, arranged by surah |
| Tafsir | Muqatil (150), al-Akhfash, Abu Ubayda | not looked up here (the content plan lists Quranpedia ids) | lexical |
| Creed | Usul al-Sunna, Ahmad (241) | 6418 (63 pp.; commentary at 11525) | A few simple statements possible, but the text addresses many disputed points. Use with scholar sign-off only |
| Creed | al-Iman, Abu Ubayd al-Qasim b. Sallam (224) | 11316, 1269, 1275 (three editions) | Technical (nature of iman); low |
| Creed | al-Sunna, Abdullah b. Ahmad (290) | 323 | **No.** The index shows refutations and criticism of named scholars (V-SEARCH snippet) |
| Creed | Kitab al-Tawhid, Ibn Khuzayma (**311**) | 13011 | **No.** Attributes and refutations; outside 300 H |
| Sirah | Sirat Ibn Hisham (213 or 218; Shamela shows 213 per a search summary) | 23833 (ت السقا ورفاقه) | Episodes possible (Hijra, al-Amin before revelation), but reports are of mixed strength. Prefer Sahihayn episodes, cite Ibn Hisham as secondary |
| Sirah | al-Tabaqat al-Kubra, Ibn Sa'd (230) | 9351 (Sader), 1686 (Ilmiyya), 146 (Khanji), 7666 (supplement) | isnad-heavy; low |
| Fiqh / hadith | Muwatta', Malik (179), Yahya's recension | 1699 (Abd al-Baqi, one volume) | Organised by chapters (prayer, zakat ...), but mixes hadith, athar and Malik's reasoning; low to medium |
| Hadith / manners | al-Adab al-Mufrad, Bukhari (256) | 12991 and others (4.5) | **High for values** (manners). Not a Sahihayn book, so it needs a grade: Dorar has "Sahih al-Adab al-Mufrad" (`s[]=2463`, Albani) |
| Fiqh (not bound by the three-centuries rule) | Umdat al-Fiqh, Ibn Qudama (Hanbali, 620) | 11315 (154 pp.) | The package accepts "any approved book of jurisprudence following one of the four schools". Short and structured, medium |
| Fiqh | Matn Abi Shuja' (Shafi'i, 593) | 11370 (48 pp.) | same |

Hanafi and Maliki short texts (for example al-Quduri, Ibn Abi Zayd) were not looked up.

## 7. Hadith route options (Bukhari and Muslim first, 80 to 100 hadith for 35 values)

**Premise (lead's update, 5 Oct):** `dorar_api.json` is blocked even in a normal Chrome browser on the lead's home network, and direct requests get 403. Treat "Dorar API usable from our laptops" as UNCONFIRMED and likely unavailable. What still works is reading Dorar pages by hand in a browser (the encyclopedia pages loaded). Whether the hadith search page and `/h/<id>` pages load too is the one question that decides the route (checks L3 and L4).

Time figures are my estimates, not sourced. "Review" is the lead's per-item check and is the same in every route (about 2 to 3 minutes each, 3 to 4 hours for 100).

| Rank | Route | How | Pros | Cons / risks | Build | Capture |
|---|---|---|---|---|---|---|
| **1** | **C2. Dorar hadith search page, results pages saved, parsed offline** | the lead opens `https://www.dorar.net/hadith/search`, picks the books "صحيح البخاري" and "صحيح مسلم" and the grade filter, types a topic word (one search per value, about 35), and saves each results page (Chrome "Webpage, HTML only", about 30 results each). An offline parser (section 7.1) reads the saved files. Search permalinks look like `https://www.dorar.net/hadith/search?q=<word>&s[]=6216&s[]=3088` | no API and no scripting against Cloudflare; one saved page holds about 30 candidates with narrator, grader, source, number, grade, categories and the hadith id, so about 35 pages give about 1,000 candidates; the page structure is known from the 2025 capture (V-CODE); `source_url` is a permalink or `/h/<id>` | **LIVE?** the search page may be blocked like the API (L3). Saving needs a human click (Cowork could not use the native Save dialog, V-SAVED README); a text-only save loses the hadith ids (then use the permalink as `source_url`) | 1.5 to 2 h (parser plus tests) | about 1 h (35 searches) |
| 2 | C. Manual copy of single hadith pages | open `https://dorar.net/h/<id>`, use the page's copy button, paste into one text file; the parser reads the clipboard format (`الراوي: ... | المحدث: ... المصدر: ... | الصفحة أو الرقم: ... خلاصة حكم المحدث: ...`, ending "موقع الدرر السنية", V-CODE) | needs only that `/h/<id>` pages load; the URL is in hand | 2 to 3 min per item and ids must be found first; typo risk if the text is retyped; whether the copy button copies the hadith text or only the reference is LIVE? (L4) | 30 min | 3.5 to 5 h for 100; cut the target to about 60 |
| 3 | D. HadeethEnc API (`hadeethenc.com`) | `https://hadeethenc.com/api/v1/categories/roots/?language=ar`, `.../hadeeths/list/?language=ar&category_id=<id>&page=1&per_page=20`, `.../hadeeths/one/?language=ar&id=<id>` (V-CODE: third-party client `@wursha/ngx-hadeethenc-api`) | listed in the package as an approved Association platform with a developer API (page 9); fields `title`, `hadeeth`, `attribution`, `grade`, `explanation`, `hints`, `reference`; child-friendly explanations; topic categories; scriptable | untested from here and from our laptops (host blocked in this container). **`hadeethenc.com` is not in `HADITH_SITES`/`SOURCE_SITE_CHOICES`**, and adding it needs a migration owned by task 01 plus an organiser or lead decision. Without that it can only be used for discovery | 1 to 1.5 h | 30 min if reachable |
| 4 | B. Shamela offline | install the empty build, add the full data folder (or download only the 2 books inside the app), read `database/book/*.db` | verbatim printed text with edition numbering; no network afterwards; also serves early sources and the Dorar mirrors (books 38056, 38058) | no grade or grader per hadith; no number-to-URL mapping; honorific and tag normalisation; unknown schema details; large download if the full folder is used (tens of GB); Windows-first tooling | 3 to 6 h | extraction 30 min to 1 h |
| 5 | E. Topic seeds | Riyad al-Salihin (Dorar book 11155) and Arba'in (13457) chapter titles as keywords; Dorar's thematic categories (`/hadith-category/cat/<hash>`, V-CODE) | quick candidate lists per value | candidates still have to be matched to their Sahihayn entry | 15 min | 1 h |
| 6 | A / A2. Dorar API by script or by browser JSONP | `dorar_api.json?skey=...&s[]=6216&s[]=3088`, direct or as a script tag with `&callback=cb` | would be the cheapest | **UNAVAILABLE as of 5 Oct** per the lead; no hadith id in the response anyway. Keep the code path optional only | 1.5 to 2 h | not applicable |

### 7.1 What the parser/fetch tool needs, compared with `fetch_verse.py`

Name suggestion: `tools/fetch_hadith.py` (offline-first). Same house rules as `fetch_verse.py`: cache directory `tools/.cache` (gitignored), a descriptive User-Agent, fail loudly on any unexpected shape, no fallback text, `verification_status: 'seeded'`, never `reviewed`.

| `fetch_verse.py` piece | Needed change |
|---|---|
| `cached(url)` network fetch with 2 s delay | **make files the primary input:** `--from-file PATH_OR_GLOB` reads pages the lead saved in `tools/.cache/dorar/`. Live mode (`--live`, 5 s delay, off by default) is optional and must stop on 403 with a message saying "save the page from a browser" |
| `checked(url, ok)` verifies the shape | per input type, verify that every candidate has all five labels (narrator, grader, book, number, grade) non-empty and a non-empty text; otherwise skip and report the file and position |
| JSON in | accept three formats: (1) **saved site-search HTML** (`div.border-bottom` blocks, V-CODE structure in 2.4): text, labels, `tag` id, sharh id, categories; (2) **saved text** (label-based lines such as `الراوي : ... | المحدث : ... | المصدر : ... الصفحة أو الرقم : ...`); (3) API JSON or JSONP `cb({...})` if a sample is ever saved (2.3) |
| `english()` strips markup only | `clean_hadith()`: unwrap `search-keys` spans, drop the `N -` list prefix, decode entities, collapse whitespace; **never touch diacritics** |
| no parser library | backend `requirements.txt` has no BeautifulSoup or lxml (grep found none), so use stdlib `html.parser` or regexes as the Dart client does |
| one item per reference | `--book bukhari|muslim` (keeps entries whose المصدر is "صحيح البخاري" or "صحيح مسلم"), `--list` prints numbered candidates, `--pick N` writes the chosen item, dedupe by `(book, number)`, reject entries ending in ". . ." or "... الحديث" |
| `source_url` from a HEAD redirect | `https://dorar.net/h/<id>` from the HTML `tag` attribute when present; otherwise the search permalink recorded by the lead in the file name or a sidecar line (`# url: ...`). Host check: `dorar.net` or `www.dorar.net` both pass |
| tests | small synthetic HTML and text samples modelled on 2.3 and 2.4. Do not commit real Dorar pages |

Rule reminder: search words may be typed by an agent or the lead, but the stored hadith text must come from a saved Dorar (or Shamela) page. No hadith words from memory in code, prompts or seed data.

## 8. Recommended route

**Hadith (about 80 to 100 items, realistically 60 to 100 depending on the gate)**
1. **Gate check, 15 minutes, lead's laptop:** L3 (does the hadith search page with the Bukhari and Muslim filters load, and can it be saved?) and L4 (does a `/h/<id>` page load?). L1 and L2 (the API) are expected to fail; record the exact error and move on.
   - Both load: go on with route C2 (steps 2 to 6).
   - Only `/h/<id>` loads: route C, target about 60.
   - Neither loads (only encyclopedia pages): see step 7.
2. **Build (agent, 1.5 to 2 h):** the offline-first tool of 7.1 with tests on synthetic samples.
3. **Capture (lead, about 1 h):** one search per value (about 35). Use a topic word, not a hadith quotation; restrict to Sahihayn and the "graded sahih" class. Save each results page into `tools/.cache/dorar/` with the value slug in the file name. Optionally also save a text-only copy.
4. **Triage (agent plus lead, about 1 h):** list candidates per value, drop partial quotations and long or mature hadith, keep 2 to 3 per value. Riyad al-Salihin and Arba'in chapter titles, Dorar's thematic categories and (if reachable) HadeethEnc categories only help choose the search words.
5. **Metadata:** `book` canonical string per Dorar book id, `number`, `narrator`, `grader` and `grade` exactly as Dorar prints them, `source_site` `dorar.net`, `source_url` = `/h/<id>` when the id is known, otherwise the permalink.
6. **Review:** the lead compares each item with its Dorar page (open the URL), then `mark_reviewed.py`. Credit "الدرر السنية" on the card.
7. **If Dorar hadith pages are blocked too:** (a) HadeethEnc (route D) if the lead approves adding `hadeethenc.com` as a hadith source site (Q9); (b) otherwise Shamela 1681 and 1727 (route B) for text and numbers, with `grader` = the compiler and `grade` = "صحيح" by Sahihayn convention **only after the organisers confirm** (Q1), `source_site` `shamela.ws`, and `source_url` = the page URL copied by hand (the internal page id). Expect a larger share of the lead's time.

**Tafsir:** use `dorar.net/tafseer` as the approved primary source (sections المعنى الإجمالي، غريب الكلمات، الفوائد التربوية). One saved page per verse group by the lead (this path works, V-SAVED), an agent wraps each excerpt. Keep Quranpedia/Shamela Tabari optional, flagged. Add `dorar.net` to the tafsir allow-list.

**Aqidah:** `dorar.net/aqeeda/<id>` fine-grained pages for the pillars of faith only; Shamela book 38058 as an offline fallback (check it against the live page). No early-source excerpts for kids.

**Fiqh:** `dorar.net/feqhia` pages that state agreement only (for example the number of daily prayers, parts of wudu), the Kuwaiti Encyclopedia through Shamela 11430 as cross-school confirmation. Always the referral line.

**Sirah:** episodes in the two Sahihayn first (so they carry a grade), `dorar.net/history/event/<id>` for short context, Ibn Hisham (Shamela 23833) as the first-three-centuries anchor where an organiser rule demands it.

## 9. Risks specific to my area

| Risk | Mitigation |
|---|---|
| Cloudflare blocks the API even in a normal browser (lead, 5 Oct) | do not depend on the API; human-saved pages (C2, C); lower the target if needed |
| Dorar hadith search and `/h/<id>` pages may be blocked as well (unknown) | gate check L3/L4 first; fallback HadeethEnc (needs Q9) or Shamela (needs Q1) |
| A text-only save loses the hadith ids | prefer HTML saves; otherwise cite a search permalink |
| Dorar copy/redistribution terms are strict ("all rights reserved") | copy individual results with credit only; no bulk mirroring; email support; show "الدرر السنية" on the card |
| Partial-quote hadith entries in results (seen in the 2025 API capture; the site page may differ) | reject entries with ". . ." and "... الحديث" |
| `(book, number)` collisions in Muslim variants | suffix convention agreed before import |
| `book` string inconsistency (Arabic vs English) breaking uniqueness | one dict keyed by Dorar book id |
| Shamela text normalisation breaks "verbatim" | diff against the web page; use Shamela only as backup |
| Dorar fiqh favours one opinion (tarjih) | quote only agreement sentences; never choose between opinions ourselves |
| Mirror staleness (Shamela 38056 / 38058 vs live Dorar) | compare one page before using |

## 10. Questions for the organisers

1. **Grading:** is the grade printed by Dorar's Hadith Encyclopedia ("خلاصة حكم المحدث" with a named muhaddith, and a bracketed "[صحيح]" for hadith of the two Sahihs) what the package calls an "approved authenticity grading"? If a hadith comes straight from a Shamela edition of Bukhari or Muslim, is "grader = the compiler, grade = صحيح" enough?
2. **"First three Islamic centuries":** does it mean authors who died by 300 H, or works written in that period? Is al-Tabari (d. 310 H) accepted? Does "or dorar.net/tafseer" mean Dorar's tafsir text alone is sufficient for every tafsir item?
3. **Dorar ethics and etiquette encyclopedias** (`dorar.net/alakhlaq`, `/adab`): package page 15 lists them as part of Dorar but approves only /tafseer, /aqeeda, /feqhia, /history by URL. May we cite them for values content?
4. **Mirrors:** does a Shamela copy of Dorar's fiqh and creed encyclopedias (books 38056, 38058), or the Kuwaiti Fiqh Encyclopedia on Shamela (book 11430), count as "dorar.net/feqhia", "dorar.net/aqeeda" and a fiqh source? May `source_site` be `shamela.ws` for them?
5. **Dorar access:** the hadith API is blocked even for a normal browser on our network and the page example no longer matches the real response shape. Is there a sanctioned way for hackathon teams to use the hadith API or the Hadith Encyclopedia data (an official contact, a data export, or a key)?
6. **Quotation limits:** how much verbatim text from a Dorar encyclopedia page is acceptable per item (a sentence, a paragraph) given the "all rights reserved" notice?
7. **Fiqh basics:** for consensus matters (five daily prayers, wudu essentials), is a statement of agreement taken from Dorar or the Kuwaiti Encyclopedia sufficient, without naming the four schools?
8. **Sensitive aqidah topics:** the methodology panel shows no named reviewers for Dorar's creed encyclopedia (unlike tafsir, fiqh, history). Does the jury expect an additional scholar check for aqidah items?
9. **HadeethEnc as a hadith source:** the package lists HadeethEnc (`hadeethenc.com`, API at `hadeethenc.com/api-docs`) among the approved Association platforms, with graded, attributed hadith. May we use it as a `source_site` for hadith items (our app currently allows only dorar.net and shamela.ws)? If yes, is its `grade` and `attribution` field an "approved authenticity grading"?

## 11. Live and Cowork checks for the lead's laptop

Save everything under `backend/session_moral_context/content/tools/.cache/cowork/` (gitignored). Use a normal browser tab, one page every few seconds. Do not try to bypass any block; if a page is refused, record the exact message and stop. **Updated after the lead's report that the API is blocked: L3 and L4 are now the gate checks; L1 and L2 are low priority.**

| # | Open (exact URL) | Save as | What I need to learn |
|---|---|---|---|
| L1 (low priority) | `https://dorar.net/dorar_api.json?skey=إنما الأعمال بالنيات` (the pending file in the Cowork README; known blocked from the lead's network) | if it ever opens: `dorar-api-sample.json`; otherwise write the exact browser error into `dorar-api-error.txt` | the real top-level shape today (`ahadith.result` vs array); the block message |
| L2 (only if L1 opens) | `https://dorar.net/dorar_api.json?skey=الصدق&s[]=6216&s[]=3088&d[]=1` and the same without `s[]` and `d[]` | `dorar-api-filtered-sample.json`, `dorar-api-unfiltered-sample.json` | are the filters honoured; results per page (about 15); partial entries |
| **L3 (gate)** | `https://www.dorar.net/hadith/search?q=الصدق&s[]=6216&s[]=3088` (if the permalink form is refused, open `https://www.dorar.net/hadith/search` and fill the form: search word, books "صحيح البخاري" and "صحيح مسلم", then tick the "graded sahih" class) | **two saves:** page as "Webpage, HTML only" -> `dorar-site-search-sample.html`, and the visible text -> `dorar-site-search-sample.md`. Also write the address-bar URL after filtering into `dorar-site-search-url.txt` | does the hadith search page load at all; are the Bukhari/Muslim filters honoured; number of results per page (about 30); the `tag="..."` hadith ids (HTML only); layout of grader/grade/number for Sahihayn entries (bracketed grade); is the grade filter label as in the capture; partial entries |
| **L4 (gate)** | `https://dorar.net/h/Tszg5ZRJ` (id from the 2025 capture, may have changed; otherwise use any id from L3) | `dorar-hadith-page-sample.md`, plus the text from the page's copy button in `dorar-copy-sample.txt` | does the `/h/<id>` page load; does it show text, source, number and grade; what exactly does the copy button put on the clipboard (reference only, or hadith text too) |
| L5 | `https://dorar.net/article/56`, `https://dorar.net/article/77`, `https://dorar.net/article/111`, `https://dorar.net/article/1987`, `https://dorar.net/article/1740` | one `.md` each | meaning of bracketed `[صحيح]`; the copyright and copying rules; creed encyclopedia method and reviewers; tafsir method |
| L6 | `https://dorar.net/tafseer/98/1` (al-Bayyina 1-5, short) and `https://dorar.net/tafseer/4/18` (al-Nisa 58-59) | `dorar-tafseer-verse-sample.md` | verse-page layout, what "المعنى الإجمالي" and "الفوائد التربوية" look like, how Tabari is cited, link to "المراجع المعتمدة" |
| L7 | `https://dorar.net/aqeeda/8`: click "الرابط المختصر" | paste the URL into `dorar-short-link.txt` | form of the short link (stable permalink or not) |
| L8 | `https://shamela.ws/book/1681`, `https://shamela.ws/book/1727`, `https://shamela.ws/book/1727/489`, the footer "الشروط" and "الخصوصية" pages, and the link behind "مجلد البيانات التام" on `https://shamela.ws/page/download` (do not download) | `shamela-book-1681.md`, `shamela-book-1727.md`, `shamela-page-1727-489.md`, `shamela-terms.md`; write file name and size of the data folder in `shamela-data-folder.txt` | edition and numbering note on the book cards; whether `/book/<id>/<n>` is the DB `page.id`; how hadith numbers appear inside the text; terms text; size of the full data folder |
| L9 | find Bukhari 6094 and Muslim 2607 (expected numbers for honesty hadith, RECALL) on Dorar (via L3) and on Shamela (via its site search restricted to book 1681 / 1727) | `numbering-crosscheck.md`: the same hadith, the number on each site | do Dorar and Shamela use the same numbers; collision cases in Muslim variants |
| L10 | `https://dorar.net/feqhia/669` and one consensus-topic page (for example the prayer chapter) | `dorar-feqhia-prayer-sample.md` | whether pages state "ijma'" clearly enough to quote an agreement sentence |
| L11 | `https://bohoth.awqaf.gov.kw/ar/الموسوعة%20الفقهية` | `kuwait-fiqh-index.md` (list of volumes, formats, sizes; do not download all 45) | confirmation of Word/PDF per volume; file names |
| L12 | `https://hadeethenc.com/api/v1/categories/roots/?language=ar`, then `https://hadeethenc.com/api/v1/hadeeths/list/?language=ar&category_id=<one id>&page=1&per_page=5`, then `https://hadeethenc.com/api/v1/hadeeths/one/?language=ar&id=<one id>` | `hadeethenc-roots.json`, `hadeethenc-list.json`, `hadeethenc-one.json` | field names and values of `attribution`, `grade`, `reference`; whether it is a good discovery index |
| L13 | **dropped:** the JSONP-from-a-local-page test is no longer worth running now that the API is blocked even in a normal browser | | |

Order of value: **L3 and L4 first** (they decide the hadith route), then L8 and L9 (Shamela backup and numbering), L12 (HadeethEnc, the other possible hadith source), L5 and L6 (rules and tafsir), the rest as time allows. L1 and L2 only take a minute and only need the error text. Allow about 45 to 60 minutes for L3 to L9.

## 12. Source list (URLs)

- Saved pages (V-SAVED): `.../content/tools/.cache/cowork/dorar-api-doc.md` (`https://dorar.net/article/389`), `dorar-tafseer-sample.md` (`https://dorar.net/tafseer/1`), `dorar-aqeeda-sample.md` (`https://dorar.net/aqeeda/8`), `dorar-feqhia-sample.md` (`https://dorar.net/feqhia/6`), `dorar-history-sample.md` (`https://dorar.net/history/event/1`), `shamela-download.md` (`https://shamela.ws/page/download`).
- Dorar wrappers and captures: `https://github.com/AhmedElTabarani/dorar-hadith-api` (README and `data/*.json`, raw at `raw.githubusercontent.com/AhmedElTabarani/dorar-hadith-api/main/`), `https://github.com/MoathCodes/dorar_hadith` (package `https://pub.dev/packages/dorar_hadith`, archive `https://pub.dev/api/archives/dorar_hadith-0.4.0.tar.gz`), issue `https://github.com/AhmedElTabarani/dorar-hadith-api/issues/29`.
- Shamela tools: `https://github.com/ragaeeb/shamela` (npm `shamela` 1.5.3), `https://github.com/alhoqbani/shamela-mcp`, `https://github.com/ammusto/shamela-extractor`, `https://github.com/yshalsager/shamela-epub-exporter`, `https://github.com/OpenShamela/data`.
- HadeethEnc client: `https://github.com/WurshaApps/ngx-hadeethenc-api` (npm `@wursha/ngx-hadeethenc-api` 0.0.4).
- Shamela book pages seen in search results: `https://shamela.ws/book/1681`, `/1284`, `/735`, `/907`, `/1727`, `/12991`, `/43`, `/7798`, `/8658`, `/21791`, `/12810`, `/1699`, `/23833`, `/9351`, `/6418`, `/13011`, `/323`, `/11316`, `/11315`, `/11370`, `/11430`, `/38056`, `/38058`.
- Dorar pages seen in search results: `https://dorar.net/article/56`, `/77`, `/111`, `/1740`, `/1987`, `/2107`, `https://dorar.net/tafseer/4/18`, `https://dorar.net/tafseer/98/1`, `https://dorar.net/feqhia/669`, `https://dorar.net/alakhlaq/3248`.
- Repo documents: `docs/hackathon/resource-package-en.md`, `docs/hackathon/content-structure-plan.md`, `docs/hackathon/tasks/02-content-curation.md`, `backend/session_moral_context/content/README.md`, `models.py`, `tools/fetch_verse.py`.
