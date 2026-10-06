# Content structure plan: using ALL approved sections (for discussion, not implementation)

> **Superseded in part (5 Oct 2026).** `content-approach-plan.md` supersedes this file's source and access parts: the reachability table (section 1), the allowed-site table (section 2), each "Source and access" line (section 3) and the tafsir whitelist question (section 10). Where the two disagree, follow `content-approach-plan.md` §3 and §8.
> This file's schema ideas, section layout, stories and review process still hold.
> Known corrections: sirah is never cited from islamic-content.com (that site is for terms only); tafsir is cited from dorar.net/tafseer (early books only, pending the Tabari question); the Quran text is Quranpedia mushaf 2, not mushaf 1.

Status: draft for the lead. Date: 4 Oct 2026. Nothing here is built yet. It extends task 02 (curation), and touches 01 (schema), 03 (retrieval) and 04 (parent sources).

## 0. The short answer

Today the bank holds only `verse` items (74, in `items/<value>.json`). The `ContentItem` model and `seed_content` already know all nine types, so most sections need **no new table and few new fields**. The proposal:

- **4 small schema additions** (one migration, owned by the task 01 branch): `title_ar/title_en`, `keywords_ar/keywords_en`, and a self M2M `related`. Everything else reuses existing fields (`book`, `number`, `source_url#fragment`, `arabic_text`, `english_text`, `child_explanation_*`, `age_band`).
- **Layout:** `items/<value>.json` stays for verses and hadith. New flat files `sections/<type>.json` for tafsir, aqidah, fiqh, sirah, faq, term. One file per story in `stories/<slug>.json`, with the team's `stories/candidates/` beside them (not seeded).
- **Principle for every section:** the bank stores a **verbatim excerpt** of an approved source in `arabic_text` (copied by a script or by hand, never typed from memory). The child-facing wording sits in `child_explanation_*`. No excerpt, no item.
- **Stories** are retold from bank verses plus approved early tafsir, in short beats the voice agent can say one at a time. They link to their verses (for recitation audio) and to the tafsir lines they rely on through `related`.
- **Hardest access problems:** dorar.net (403 from here: manual browser only), Bayyinat PDF and the dictionary (manual by hand). Quranpedia (tafsir, Quran) is the only fully scriptable source.

## 1. What is realistically reachable (probed 4 Oct 2026, a handful of polite `curl -A 'AlSadiq-curation/0.1'` requests)

| Source | Result | Plan |
|---|---|---|
| `api.quranpedia.net/v1/ayah/{s}/{a}/tafsir` | 200. Lists ~100 tafsir books for the ayah, with author and **death year (`year`)**. Good for filtering to early books. | Script. |
| `.../ayah/{s}/{a}/book/4` (al-Tabari, *Jami' al-Bayan*, d. 310 H) | 200. Returns the Tabari section for the ayah as HTML text (isnads, `<br />`, `<h3>`). 12:92 was about 28 KB. | Script fetch, curator picks lines by index. |
| Other early books in the same list | `149` Ibn Abi Hatim (d. 327), `348`/`27769` Abu Ubayda, *Majaz al-Quran* (d. 209/210), `27771` al-Akhfash (d. 215), `341` Ibn Qutayba, *Gharib* (d. 276), `27755` Muqatil (d. 150). | See open question 1. |
| `quranpedia.net` pages, robots.txt | Allows all agents. Ayah pages return 200. | OK for source links. |
| `dorar.net` | 403 Cloudflare, confirmed again. | **Manual in a browser**, saved to the gitignored cache. No workaround planned. |
| `dawa.center/file/7937` | 200, title "بينات: أسئلة وأجوبة عن الإسلام". The PDF sits at `/storage/files/...pdf` (~17 MB), and **robots.txt disallows `/storage/files/` and `/*/download`**. | Human downloads it once in a browser. Pages `?lang=ar|en|fr` exist. We copy only the pages we use. |
| `islamic-content.com` | robots.txt blocks some crawlers entirely and `/dictionary/` for some. Pages are heavy (dictionary term ~1.7 MB). Found sections: `/dictionary/term/{id}` (Quranic terms), `/allah-names` and `/t/{id}` (Names of Allah, Arabic), `/historical-events` (history events), `/terms-index`. | **By hand**, one page at a time, 5+ seconds apart. |
| `shamela.ws` | Home page 200, no robots.txt. Book-level grading only. | Manual reading. Backup for early sirah or aqidah texts. |

Consequence: tafsir is the only section a script can fetch in bulk. All other sections are **human-in-browser → saved text → agent wraps into JSON**.

## 2. Schema: the smallest change

One migration on the task 01 branch (the only one allowed to create it, per AGENTS.md). All fields are optional, so existing rows and files stay valid.

| Change | Why |
|---|---|
| `title_ar`, `title_en` (CharField 200) | One generic label: FAQ question, term word, story title, topic name, sirah event, "Tafsir of 12:92". Cards, parent UI and retrieval need a short label that is not scripture. |
| `keywords_ar`, `keywords_en` (JSON list, like `Value`) | Deterministic detection for items with no value (term, FAQ, aqidah, fiqh) and for story figures. Also joins `search_text_norm`. |
| `related` (M2M to `self`, `symmetrical=False`, `related_name='cited_by'`) | Story, tafsir, aqidah, fiqh and FAQ point at their evidence items (verses, hadith, tafsir). In files: a list of the existing ledger labels, e.g. `["verse:12:92", "hadith:Sahih Muslim:8"]`. |

**Deliberately not added:** a madhhab flag, an author field, a verse-range field, a story-text field. Instead:

- `book` = the work (with author and death year, e.g. "جامع البيان — الطبري (ت 310هـ)"), `number` = the locator ("12:92", "p. 34", "term/1063", "12:89-92").
- The hadith unique constraint is conditional on `type='hadith'`, so reusing `book`/`number` for other types is safe.
- Natural key for every non-verse, non-hadith type stays `(type, source_url)` (already implemented). Several items on one page are told apart by a `#fragment` (e.g. `#book-4`, `#p34`, `#story-yusuf-forgiveness`).
- Fiqh "general information only" is a rule in `clean()` and the prompt, not a flag (see 3.4).

**New `clean()` rules** (all only when status is `seeded` or `reviewed`):

| Type | Required | Allowed `source_site` |
|---|---|---|
| tafsir | `arabic_text`, `book`, `number`, `title_*`, and at least one verse in `related` (checked in `seed_content`) | dorar.net, quranpedia.net, shamela.ws |
| aqidah, fiqh, sirah | `arabic_text`, `book`, `title_*` | dorar.net, shamela.ws (islamic-content.com is for terms only, not sirah) |
| faq | `title_*` (the question), `arabic_text` (the Bayyinat answer excerpt), `number` (page) | dawa.center |
| term | `title_*`, `arabic_text` (the dictionary definition) | islamic-content.com |
| story | `title_*`, `number` (the verse range), `child_explanation_ar` and `_en`, `related` with at least one verse, **`arabic_text` must be blank** | quranpedia.net |

`english_text` is filled only if the source itself publishes English (Bayyinat has `?lang=en`); put its name in `translation_name`. Otherwise leave it blank. We do not publish our own translation as if it were the source's.

## 3. Section by section

Common to all: every item has `child_explanation_ar/en` (2 short sentences) and, where useful, `child_explanation_older_*` (ages 10-13), `age_band`, `values` and `related`. Review: the lead reads the item next to its `source_url`, then `tools/mark_reviewed.py`. Counts are in section 8.

### 3.1 Tafsir (`tafsir`)

- **Purpose:** lets the agent answer "what does this verse mean?" from a classical source, and backs stories.
- **Source and access:** Quranpedia tafsir API (scripted). Whitelist of books in open question 1. The excerpt is chosen from Tabari's own conclusion (the passage after "قال أبو جعفر") or a Companion/Tabi'i report on the ayah. **Skip isnad-only blocks and any Israiliyyat report.**
- **One item:** `arabic_text` = verbatim excerpt (no HTML, isnads trimmed only by cutting whole sentences), `book` = Tabari with death year, `number` = "12:92", `title_*` = "Tafsir of 12:92", `related` = the verse it explains, `source_site` = quranpedia.net, `source_url` = `https://quranpedia.net/tafsir/yusuf/92#book-4`. The child explanation is a plain 2-sentence summary.
- **Natural key:** `(tafsir, source_url)`; the fragment carries the book id, so two books on one ayah do not collide.
- **Links:** to its verse through `related`. Values come through the verse; set `values` too so it can be found without the verse.
- **Safety:** never a stand-alone item for an unseeded verse; no verdicts on disputed issues; if the excerpt contains a ruling, do not seed it (FAQ or fiqh handles rulings).
- **Tool:** new `tools/fetch_tafsir.py S:A --book 4 [--list]` (cached, 2 s delay). It prints numbered lines, and `--lines 3-5` writes the draft item. The curator selects line numbers; it never retypes text. Same pattern as `fetch_verse.py`.
- **Review:** compare against the Quranpedia page. Check the excerpt is contiguous and complete.

### 3.2 Aqidah (`aqidah`)

- **Purpose:** the beliefs a child asks about: Allah is one, the pillars of faith, angels, the Prophet, "who created Allah?", "where is Allah?".
- **Source and access:** dorar.net aqidah section (**manual browser**) and shamela.ws for early texts (see open question 2). The Names of Allah pages on islamic-content.com are Arabic and could fit here, but that site is approved for terms only (open question 3). The pillars-of-faith hadith (Jibril) comes from the hadith plan.
- **One item:** `title_*` = the topic, `arabic_text` = verbatim excerpt, `book` = work, `number` = page or section, `source_url` = the dorar.net page, `keywords_*`, `related` = supporting verses or hadith.
- **Natural key:** `(aqidah, source_url)`.
- **Safety:** basics only. No sectarian or theological controversy (attributes debates, takfir, other groups, qadar arguments); where the source discusses these, take only the simple opening statement. "Where is Allah?" is on a **sensitive list**: use only Quran verses that state closeness and the source's own simple answer, and have the lead (or a scholar) approve the exact words. If the child pushes deeper: "a good question for your parents or a teacher".
- **Review:** lead; a scholar check for the sensitive list (open question 4).

### 3.3 Faq (`faq`)

- **Purpose:** direct answers to child-sized doubts ("Why do we pray?", "Why can't I see Allah?").
- **Source and access:** Bayyinat, dawa.center/file/7937. The human downloads the PDF **once, by hand** into `tools/.cache/` (gitignored). A script converts PDF pages to text locally (`pdftotext`), and nothing touches the site again.
- **One item:** `title_ar/en` = the question (in the source's wording, shortened only by cutting), `arabic_text` = the answer excerpt (verbatim, 1-3 short paragraphs from the source), `english_text` only if the English edition has it, `number` = "p. 34", `source_url` = `https://dawa.center/file/7937#p34-q2`, `keywords_*`, `related` = any verse or hadith the answer cites **only if it is in the bank** (never copy cited verses from the PDF), `child_explanation_*` = the child-sized answer.
- **Natural key:** `(faq, source_url)`; the fragment holds page and question number.
- **Links:** `values` if the question maps to one (prayer, honesty); otherwise none (found by keywords).
- **Safety:** pick child-relevant questions. Skip debate with other religions, sectarian questions, anything graphic, or hard theodicy. Items that read as a ruling are re-labelled `fiqh` or dropped. If an answer in the PDF quotes a verse or hadith that is not in the bank, the child explanation must not repeat it.
- **Review:** lead reads the PDF page next to the item.

### 3.4 Fiqh (`fiqh`)

- **Purpose:** simple general information about worship and etiquette (how many daily prayers, what wudu is, what Ramadan fasting is) that parents expect a companion to get right.
- **Source and access:** dorar.net fiqh pages (**manual browser**), or an early source (the Muwatta of Malik, d. 179, or al-Umm, d. 204, through shamela.ws). Hadith evidence is linked through `related`, not retyped.
- **One item:** `title_*` = topic, `arabic_text` = verbatim excerpt, `book`/`number`/`source_url`, `related` = evidence hadith or verse, `child_explanation_*` = general explanation. `age_band` is set on purpose (many topics are 10-13 only).
- **Natural key:** `(fiqh, source_url)`.
- **Safety, non-negotiable:** general information only; **never a personal fatwa**; only matters on which the schools agree (the count of daily prayers, the basic pillars, wudu essentials); no madhhab-specific details; no questions of purity or marriage for young children; every fiqh item's child text ends with a referral ("your parents or a scholar can tell you exactly"). Because retrieval always appends the referral for `type=fiqh` (section 5), the rule does not depend on item wording.
- **Review:** lead, strictly; every item is "consensus / basics" or it is dropped.

### 3.5 Sirah (`sirah`)

- **Purpose:** the Prophet's life as short stories (his honesty before revelation, his kindness to a neighbour, the Hijra), to feed the value "love of the Prophet".
- **Source and access:** dorar.net sirah (**manual**); Sahih al-Bukhari and Muslim for authentic episodes (linked as hadith); early sirah (Ibn Hisham, d. 218) via shamela.ws. islamic-content.com is not an approved source for history (it is approved for dawah topics and terminology only), so its "الموسوعة التاريخية" pages are not used. For authentic episodes prefer a hadith item plus a sirah item that points to it.
- **One item:** `title_*`, `arabic_text` = verbatim excerpt, `book`, `number`, `source_url`, `keywords_*`, `values`, `related` = hadith or verse that supports it, `child_explanation_*` in short beats (as stories, section 6).
- **Natural key:** `(sirah, source_url)`.
- **Safety:** no episode with graphic violence or battles, no unauthentic report; honorific after the Prophet's name; no images or invented dialogue.
- **Review:** lead.

### 3.5b Hadith (placeholder)

Discussed separately. Only constraint from here: aqidah, fiqh, faq and sirah items point at hadith through `related` using the label `hadith:<book>:<number>`, so hadith needs no change for this plan.

### 3.6 Term (`term`)

- **Purpose:** the "what is zakah / sadaqah / hadith / sunnah?" answer, and the vocabulary rule (use the right Arabic term, and teach it).
- **Source and access:** islamic-content.com dictionary, `/dictionary/term/{id}` (**by hand**, one page at a time, 5 s apart). The human copies the short definition into the item; the page is large (about 1.7 MB), so no automation. We keep to the most common terms.
- **One item:** `title_ar` = the term (with tashkeel as in the source), `title_en` = a transliteration or common English name ("Zakah"), `arabic_text` = the definition excerpt, `keywords_ar/en` (spellings, plural, English), `child_explanation_*`, `source_url` = `https://islamic-content.com/dictionary/term/1063`.
- **Natural key:** `(term, source_url)`; the URL id is unique per term, so no fragment is needed.
- **Links:** `values` where natural (zakah → charity); `related` is usually empty.
- **Safety:** child explanation avoids detailed rulings (nisab, rates). It says what the thing is and why, then refers on.
- **Review:** lead, quick (the check is the definition's wording against the page).

### 3.7 Story (`story`)

See section 6.

## 4. File layout and seeding

```
content/
  values.json
  reviewed.json                  one ledger for all sections (see risk 3)
  items/<value>.json             verse + hadith, per value (today)
  sections/tafsir.json           flat list, one file per type
  sections/aqidah.json  fiqh.json  sirah.json  faq.json  term.json
  stories/<slug>.json            one finished story item per file (list of 1)
  stories/candidates/<slug>.json the team's catalogue (NOT read by seed_content)
  tools/ fetch_verse.py fetch_audio.py (today) + fetch_tafsir.py, extract_faq.py (new)
  tools/.cache/                  gitignored: PDF, saved dorar pages, API cache
```

Why `sections/<type>.json` and not `items/<section>/...`: faq, term, aqidah, fiqh and sirah are not owned by a value (many have none), so a per-value file does not fit. One file per type keeps a diff readable and lets two people work on different types without conflicts. The `items/*.json` glob is non-recursive, so putting folders under `items/` would also be invisible to today's code.

**Changes to existing tooling (all small):**

1. `seed_content`: read `items/*.json`, then `sections/*.json`, then `stories/*.json` (not `candidates/`), in that order. Pass 1 creates or updates each item without `related`. Pass 2 resolves `related` labels (`verse:12:92`) to rows, with an "unknown related item" rejection like the existing "unknown value slug" one.
2. `ITEM_KEYS` already derives from the model, so the new fields are accepted automatically. `related` is added next to `values` as a list key. The hash covers `related`, so editing evidence invalidates the review.
3. `mark_reviewed.py` / `show_items.py`: REF lookup also searches `sections/` and `stories/`. A REF can be a file name (`faq.json`), a value slug, or a label (`faq:https://dawa.center/file/7937#p34-q2`).
4. `content/README.md`: add the "Required fields by type" table from section 2, the `title_*`/`keywords_*`/`related` descriptions, and the layout above.
5. `reviewed.json`: unchanged format. Keys for sections are `type:source_url`, so they are long but stable.

Tests: a seeding test per type (rejects a story with `arabic_text`, a tafsir with no related verse, a term from the wrong site).

## 5. How the agent uses each section (task 03)

Retrieval stays deterministic. `match_values()` is extended to a second index of item `keywords_*` (term, faq, aqidah, fiqh, story figures). No network and under 10 ms, as designed.

| Child says | Sections injected | Notes |
|---|---|---|
| "Why is lying bad?" | verses and hadith of the value (as now) | the value index, unchanged |
| "Where is Allah?", "Who made Allah?" | faq, then aqidah, then their `related` verses | sensitive list: if no `reviewed` item matches, the answer is the gentle general one plus a referral |
| "What is zakah?" "What does sadaqah mean?" | term, then `related` evidence | one short definition, then a one-line value tie-in |
| "Do I have to pray now?" "Is X haram?" | fiqh (general), plus its `related` evidence | the prompt rule is always appended for `type=fiqh`: "this is general information; for your own situation ask your parents or a scholar" |
| "What does this verse mean?" (after a verse was served) | tafsir whose `related` includes that verse | never injected on its own for an unrelated turn |
| "Tell me a story" / "tell me about Yusuf" | story by figure keyword or value | `get_story(slug_or_figure, part)`; one beat per turn (35-word limit) |
| "Tell me about the Prophet" | sirah, plus the hadith it points to | |

Rules for injection:

- Cap: **3 items per turn**, ordered faq or term (exact intent) > aqidah/fiqh > verse/hadith > tafsir > sirah > story. A story is only injected if the child asked for one or the turn has no stronger match.
- Only `seeded` and `reviewed` items are served; `reviewed` first. `related` items are served only if they are also seeded or reviewed.
- Quote only items served. For `faq`/`term`/`tafsir`/`aqidah`/`fiqh`/`sirah` the agent says the **child explanation** and names the source ("according to Bayyinat"), and does not read the Arabic excerpt aloud. Verses are only played, never read.
- No match: gentle general answer, no scripture, suggest a parent (existing rule).
- The `reference` event carries `type`, `title_*`, `book`, `number`, `source_site`, `source_url`, `related` card ids. The web source card renders by type.
- Task 09 eval cases to add: "where is Allah", "what is zakah", a personal fiqh question (expect a referral), a story request (expect beats and a verse played), a question with no matching item (expect no invented scripture).

**Parent UI (task 04):** `sources_used` stores a snapshot of each served item. Cards grouped by type:

| Type | Card shows |
|---|---|
| verse | Arabic, translation, surah:ayah, audio, link (unchanged) |
| hadith | text, book, number, grade and grader, link |
| tafsir | "Tafsir al-Tabari on 12:92", excerpt, link to the Quranpedia page |
| faq | question, "Bayyinat p. 34", link to dawa.center page |
| term | the term, definition, link to the dictionary page |
| aqidah, sirah | title, source, link |
| fiqh | title, source, link, and a visible line "General information, not a ruling" |
| story | title, verse range, chips for the verses it retold, tafsir source |

The trust line is extended with Bayyinat (dawa.center) and islamic-content.com. A story logs a `ServedReference` for the story and for each verse beat played.

## 6. Stories in detail

### 6.1 The candidate file (the team)

```json
{"slug":"yusuf-forgiving-his-brothers","title_ar":"...","title_en":"Yusuf forgives his brothers",
 "figures":["Yusuf"],"verse_ranges":["12:89-92"],"bank_verses":["12:92"],"values":["forgiveness"],
 "summary_ar":"...","summary_en":"...",           // own words, planning only, never shown as scripture
 "tafsir_sources":[{"site":"quranpedia.net","book":"Tafsir al-Tabari","url":"..."}],
 "notes":"","status":"candidate"}
```

`status` flow: `candidate` → `approved` (lead) or `rejected` → `drafted` (item exists) → seeded in the DB. The file is never seeded and never served; it is the audit trail for why a story exists. One extra optional key is proposed: `"age_band"`, so unsuitable material is flagged early.

### 6.2 Candidate to bank item

| Candidate key | Becomes in the story item |
|---|---|
| `slug` | the fragment of `source_url`: `https://quranpedia.net/tafsir/yusuf/89#story-yusuf-forgiving-his-brothers`. The first verse's Quranpedia page is used. Natural key `(story, source_url)`. |
| `title_ar`, `title_en` | `title_ar`, `title_en` |
| `figures` | `keywords_en` plus the Arabic name in `keywords_ar` (so "tell me about Yusuf" matches), together with story words ("قصة", "story") added by retrieval, not the file |
| `verse_ranges` | `number` = "12:89-92" (several ranges joined by "; "). Shown on cards. |
| `bank_verses` | `related`, as `["verse:12:92"]`. Seeding **rejects** the story if any is missing from the bank. |
| (the tafsir lines used) | `related` also holds the tafsir items (`tafsir:<url>`) the narration relies on |
| `values` | `values` |
| `summary_*` | **not copied**. It is only the drafting brief. |
| `tafsir_sources`, `notes` | stay in the candidate file; the draft step turns the chosen tafsir lines into `tafsir` items |

### 6.3 Drafting rules for the narration (`child_explanation_ar/en`, older versions for 10-13)

- **Grounding rule:** every sentence must be traceable to (a) the story's verses (all verses in `verse_ranges`, whether or not they are bank items), or (b) a tafsir item in `related`. No other source. **No Israiliyyat, no invented names, places, numbers, feelings or dialogue.** A sentence with no ground is cut.
- The draft carries a **grounding table** in the candidate file (`beats`: each beat → verse/tafsir label). The lead reviews against it. It is not seeded.
- Format: 3-6 beats, separated by a blank line; each beat at most about 35 words (the voice limit), and no beat reads or quotes the Arabic. The last beat ties to the value and invites the child to listen to a verse.
- The narrator names a prophet with the honorific ("عليه السلام"). No pictures, no impersonating a prophet's voice.
- Age bands: `child_explanation_*` is the 6-9 version (short, concrete); `_older_*` is the 10-13 version (adds a reason or a lesson from the tafsir).
- Stories with frightening or mature material (Nuh and the flood, Pharaoh's end, Lut, parts of Yusuf and the wife of al-Aziz, the Ibrahim sacrifice) are `age_band=10-13` and told only through the verses' safe scenes, or excluded. Good starters:
  Yusuf and forgiveness (12:89-92); the ant and Sulayman (27:18-19); the hoopoe's report (27:22-26); Musa's mother and trust (28:7-13); Ibrahim and the idols (21:51-67); Companions of the Cave (18:9-26, courage, 10-13); Luqman's advice (31:12-19); the garden owners (68:17-33, generosity); Qabil and Habil (5:27-31, anger); Yunus and repentance (21:87-88); the people of the elephant (105).
- Target: 15 candidates, 10 approved, 6 drafted, 6 reviewed by the end of Day 2.

### 6.4 Audio

- The story narration is the agent's own spoken retelling (normal TTS). It is not scripture and may be synthesised.
- **Verses are never synthesised.** After the beat that retells a verse, the agent triggers the recitation of the bank verse (existing `audio_url`, Husary Muallim, in `static/quran/`). If the verse is not yet a bank item, it must first be added with `fetch_verse.py` and `fetch_audio.py`. The candidate's `bank_verses` therefore lists the verses that will be played, typically 1-3 per story.
- Rough cost: 10 stories times 2-3 new verses, about 25 new verse items (all need review) and as many mp3s. This is the reason the target is 6 stories first.

### 6.5 Review

Two gates, both by the lead:

1. **Candidate gate:** is the story suitable and on topic, are the verse ranges right, is a tafsir source cited?
2. **Item gate:** read the narration beat by beat against the verses and the tafsir excerpt using the grounding table. Any later edit changes the hash and `STALE REVIEW` appears, which forces a re-check. A `reviewer` agent can pre-screen (only for "does a sentence lack a ground?"), but never marks reviewed.

## 7. Child safety rules (summary)

| Rule | Where it applies |
|---|---|
| No source, no answer: an item exists only with a verbatim excerpt plus source link | all |
| Fiqh = general information, consensus basics only, always referred to parent or scholar | fiqh (item, prompt, parent card) |
| No personal fatwa, ever; "is it halal/haram for me?" → referral | agent prompt |
| Aqidah: basics only; sensitive-topic list approved by lead (and a scholar if possible) | aqidah, faq |
| Stories: no Israiliyyat, no invention, honorifics, age-banded, verses played not synthesised | story, sirah |
| Never read the Arabic excerpt aloud; say the source and give the child explanation | all but verse |
| Only `seeded` and `reviewed` items are served | retrieval |

## 8. Targets for the hackathon

Reviewing is the bottleneck: about 2-5 minutes per item for the lead. "Floor" is what we promise if time is short.

| Section | Target | Floor | Notes |
|---|---|---|---|
| tafsir | 20 | 10 | scripted, best value for effort; one per most-used verse |
| faq | 25 | 15 | PDF pages |
| term | 25 | 12 | by hand |
| story | 10 | 5 | plus ~25 extra verse items and audio |
| aqidah | 12 | 6 | dorar.net by hand |
| fiqh | 8 | 4 | |
| sirah | 8 | 4 | cut first if time is short |
| Total (non-verse, non-hadith) | ~108 | ~56 | about 6.5 h versus 3.5 h of lead review |

Cut order if the lead is short of time: sirah, then fiqh, then aqidah (keep the sensitive FAQs), then terms.

## 9. Work plan

Dates follow PLAN.md. Freeze is Day 2 21:00.

| # | Step | Owner | When | Notes |
|---|---|---|---|---|
| 0 | Lead answers the open questions in section 10 | Abdulrahman Salamah | before step 1 | blocks tafsir whitelist and aqidah source |
| 1 | Task 01 branch: migration with `title_*`, `keywords_*`, `related`; `clean()` rules; `seed_content` layout and two-pass related; `mark_reviewed`/`show_items`/README; seeding tests | `backend-dev` (Sonnet), task 01 owner merges | Day 1 evening | only task 01 may add the migration. 03's `pg_trgm` migration comes after. |
| 2 | Tools: `fetch_tafsir.py`, `extract_faq.py` (local PDF to text) | `content-curator` | Day 1 evening or Day 2 am | reuse `fetch_verse.py` caching |
| 3 | Manual access batch: lead saves into `tools/.cache/` the Bayyinat PDF, the dorar.net aqidah, fiqh and sirah pages he wants, and the dictionary pages for the term list | Abdulrahman Salamah (or whoever has a normal browser; no scripted access) | Day 2 am | one sitting, about 1 h |
| 4 | Story catalogue to `stories/candidates/` | the team | Day 1-2 | needs `figures`, `verse_ranges`, `bank_verses`, tafsir link per story |
| 5 | Drafts: tafsir (scripted), faq, term | `content-curator` (agents, run as a batch) | Day 2 | never `reviewed`; unsourced goes to `unverified` |
| 6 | Drafts: aqidah, fiqh, sirah from the saved dorar.net pages; story narrations from approved candidates + tafsir items + a grounding table | `content-curator`, one story per run | Day 2 | the verses a story needs are fetched first (fetch_verse, fetch_audio) |
| 7 | Review blocks: tafsir and faq first, then terms, stories, aqidah/fiqh | Abdulrahman Salamah | Day 2 | `reviewer` agent spot-checks 10 items per section first |
| 8 | Task 03: second keyword index, type caps, `get_story`, fiqh referral line, `reference` event fields | `voice-agent-dev` | Day 2 | follows step 1 |
| 9 | Task 04: card rendering by type and the extended trust line | `frontend-dev` | Day 2 | follows step 8 |
| 10 | Task 09: eval cases for each section | eval owner | Day 2 to 3 | |
| 11 | Brain: record in `Decisions log` (layout, schema additions, tafsir whitelist), `Task board` rows per section | main session only | after step 0 and 1 | |

Migrations: only step 1. Nothing else here touches the database schema.

## 10. Risks and open questions for the lead

**Open questions**

1. **Tafsir whitelist.** "First three Islamic centuries" strictly means up to 300 H. Al-Tabari died 310 H (lived 224-310), Ibn Abi Hatim 327. Pre-300 books on Quranpedia are mostly lexical (*Majaz*, *Gharib*, al-Akhfash) or Muqatil (d. 150, weak in narration). Proposal: Tabari as the main book (he is a third-century scholar), Ibn Abi Hatim for Companion reports, and *Gharib* only for word meanings. Is this acceptable?
2. **Aqidah and fiqh early sources.** Is a dorar.net section page enough as a source, or must the excerpt also name an early book (for example Malik's *Muwatta*)? Does shamela.ws count as a source for them?
3. **Names of Allah on islamic-content.com** (`/allah-names`): file them as `term` (site approved for terms) or allow them as `aqidah`? They are very useful for "Who is Ar-Rahman?".
4. **Sensitive list sign-off.** Can a scholar read the sensitive FAQ and aqidah items ("where is Allah", qadar, why evil, other religions, hell) before the demo? If not, we leave them out and the agent refers the child to a parent.
5. **Story scope.** Do we include prophets' stories that mix in mature themes (Yusuf and the wife of al-Aziz, Lut) in an age-banded form, or exclude them? Proposal: exclude.
6. **`related` generality.** Is a general self-M2M acceptable, or do we limit it to verses only? Proposal: general (evidence for fiqh and aqidah is often a hadith).
7. **Keywords:** put `keywords_*` on the item (proposed), or create "topic" `Value` rows for terms and aqidah topics so task 03's existing index handles them? The second needs no schema change but adds 30-50 values.

**Risks**

1. **Access is the schedule.** dorar.net, the Bayyinat PDF and the dictionary are all manual. If the manual sitting slips, aqidah, fiqh, sirah and terms slip. Tafsir and stories do not depend on it.
2. **Review load** (~6.5 h for the full target). The floor keeps it near 3.5 h.
3. **One `reviewed.json`** will collide when several branches add reviews. Mitigation: sort entries by key, merge by hand; split per section only if it hurts.
4. **Tabari text** is long, has chains, and includes Israiliyyat. The script must output numbered lines and the curator picks by number, and the reviewer checks that no excerpt carries an unsound report.
5. **Excerpts copied from a PDF or from HTML** can pick up diacritic or whitespace noise. Mitigation: store exactly what the source shows, trim only outer whitespace and markup, as `fetch_verse.py` does.
6. **Hash churn.** Adding `title_*`/`keywords_*` later changes hashes of items already reviewed. Add all fields before the review block starts.
7. **Voice limit.** A story that needs 6 turns may lose a child's attention. Keep beats short, and let the child stop at any beat.
8. **Source rules can change.** robots.txt files were read on 4 Oct 2026; re-check before any additional access.
