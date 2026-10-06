# Content approach plan: sources, hadith route and compliance

Status: **complete, for the lead's decision; reviewed by an Opus reviewer against the package and corrected.** Written 5 Oct 2026 (Day 2, early morning) by the cloud session on branch `hk/01-knowledge-bank`. The research it rests on is in `docs/hackathon/research/` (r1 to r5), and the rules are in `docs/hackathon/resource-package-en.md` (the "package").

> **Note for the paused local session:** this is the plan you were going to write after your five research agents finished. It is done and pushed. Run `git pull origin hk/01-knowledge-bank`, read this file, and do not redo the research or the plan. If your local `docs/hackathon/research/compliance-gap.md` has something that `r5-compliance-gap.md` lacks, add only that.

This plan supersedes the source and access parts of `content-structure-plan.md`. That file's schema and section ideas still hold, except where section 8 below changes them.

---

## 0. The plan on one page

1. **Every item is copied from a source the package approves, and the item names that source.** Our own wording is only ever the "in simple words" explanation, labelled as ours. No source, no answer.
2. **Hadith (the hardest part) has one recommended route, with two fallbacks that both comply** (section 4):
   - **Recommended (route H, "find on HadeethEnc, prove on dorar"):** a script pulls Bukhari and Muslim hadith graded `صحيح` from the HadeethEnc API (an Association platform in the package, whose published reuse policy permits AI and RAG use; r1 §2.7, confirmation asked). It filters by our 38 values. The lead checks each pick's book, number and grade on dorar.net in a browser. The item cites dorar.net for the Arabic, and HadeethEnc's English is shown only with its own link (`translation_source_url`), pending organiser question 13.
   - **Fallback 1 (route D, "dorar only"):** the lead saves dorar.net hadith-search result pages, filtered to Bukhari and Muslim, about 38 searches (one per value). An offline parser turns them into draft items.
   - **Fallback 2 (route S, "Shamela offline"):** text and numbers come from the Shamela desktop library. Its grade and grader come from the compilers' condition (Bukhari and Muslim only). This needs an organiser OK.
   - **Who does what:** a script does the API pulls (on the lead's laptop, or in the cloud once the domains are allowed, see 0.5). Cowork or the lead does the dorar browser pages. Cloud agents build the tools and draft the items. The lead reviews every item.
3. **The 74 verses need re-fetching (section 5).** Their Arabic is the "simple" (imlaei) spelling, not the King Fahd Complex Uthmani text the package requires. 0 of 74 match KFGQPC; 20 differ in rasm, and 5 carry different pause signs. The cause: we fetched Quranpedia mushaf 1, but the KFGQPC text is mushaf 2. The fix:
   - switch the id, or use the Complex's own JSON;
   - add a search field, so Arabic search keeps working;
   - verify all 74 automatically, then a 30-minute scoped re-review.

   About 2 to 3 hours in total (r4 §7).
4. **Every other section has an approved, reachable route (section 6):**
   - tafsir: dorar.net/tafseer, which the package names (verse-page layout still to confirm, check L6);
   - aqidah, fiqh and sirah: dorar.net encyclopedias, pages saved from the browser;
   - FAQ: the Bayyinat PDF, already downloaded;
   - terms: the Al-Jamhara dictionary, by hand;
   - stories: retold only from bank verses plus dorar tafsir.
5. **Unblock the cloud agents:** add these domains to the cloud environment's allowed list:
   - `hadeethenc.com`
   - `quranenc.com`
   - `api.quranpedia.net` and `quranpedia.net`
   - `mp3quran.net` (plus its `server*.mp3quran.net` audio hosts)
   - `icadb.com`
   - `islamenc.com` and `kids.islamenc.com`

   Then every scripted step can run in the cloud while you do the browser-only steps. dorar.net and islamic-content.com stay browser-only whatever we do: Cloudflare blocks dorar, and Al-Jamhara's robots.txt limits bots.
6. **The agent is not compliant yet, whatever the bank holds (section 7, from r5).** It must:
   - say it is an AI;
   - stop quoting scripture or telling prophet stories from memory;
   - apply content levels A to D (answer, explain, flag disagreement and refer, or refer for any fatwa);
   - decline when it has no source;
   - run the same guard for typed chat, which today skips the grounding hook.

   These are prompt and agent changes for task 03, plus a few fields for task 01.
7. **The lead decides 10 things today (section 11), and we send the organisers 17 questions (section 12).** Every section except hadith has a route that is compliant without the answers. **Hadith is the exception:** if dorar hadith pages are blocked (gates L3 and L4 both fail), no hadith route is compliant until question 1 or 2 is answered. Hadith then ships as 0 items, and the agent uses DECLINE_NO_SOURCE for hadith requests.

---

## 1. The rules, and how this plan meets each one

From the package, pages 2 to 6. "Mechanism" is where the rule is enforced.

| Package rule | What it means for a children's app | Mechanism in this plan |
|---|---|---|
| Content levels A-D (p.2) | A: answer with source. B: explain with source and hedging. C: say scholars differ, give agreed basics, refer. D (personal case or fatwa): no ruling, general info, refer. | `content_level` on every item (section 8). A turn guard classifies each question (section 7.2). Six answer modes. |
| Quran: approved orthography and translations (p.3) | Exact KFGQPC Uthmani text; translation from the Complex, Quranpedia or the Association | Re-fetch from Quranpedia's KFGQPC mushaf (section 5). `translation_name` on every item. Verses are never spoken by TTS. |
| Tafsir: first three centuries or dorar.net/tafseer; keep the exegete's words apart from the Quran (p.3) | Tafsir card separate from the verse card | dorar.net/tafseer as primary (section 6.1). Tabari only if organisers accept d. 310 H. |
| Hadith: Bukhari and Muslim; others only with verified grading; dorar.net/hadith or Shamela; never attribute without source and approved grading (p.3) | Every hadith carries book, number, grade, grader, URL, verbatim Arabic | Route H, D or S (section 4). `clean()` also requires `arabic_text`, and accepts only exact grade `صحيح` (section 8). |
| Creed: first three centuries or dorar.net/aqeeda (p.3) | Pillars of faith, simple statements | dorar.net/aqeeda pages (section 6.2). Sensitive list held back. |
| Fiqh: four-school books or dorar.net/feqhia; no personal fatwa, no automated tarjih (p.4) | Agreed basics only, always "ask your parents or a scholar" | Agreement sentences only (section 6.3). Level C or D guard. |
| Sirah and history: early sources or dorar.net/history; show caution where needed (p.4) | Established episodes only | Bukhari/Muslim episodes first, dorar history for context (section 6.4) |
| FAQ: Bayyinat (p.4) | Doubts and child questions | Bayyinat PDF short answers (section 6.5) |
| Terms: Al-Jamhara dictionary, priority over machine translation (p.4) | Keep the term, give the approved equivalent | 25 `term` items (section 6.6) |
| Reliability: traceable source; never attribute text to a source that lacks it; separate scripture from generated explanation; say when information is insufficient (p.5) | "From <source>: …" versus "In simple words: …" | Card labels (section 7.4). `arabic_text` must come from the page in `source_url`. DECLINE_NO_SOURCE mode. |
| Definitive versus ijtihad (p.5) | Never present a disputed point as settled | `disagreement_note_*` required for level C |
| No fatwas (p.5) | The child gets referral, not verdicts | Level D guard on voice **and** text paths |
| Prevent hallucination (p.5) | Decline or refer rather than guess | No scripture, hadith, story or ruling unless served this turn. TTS filter on Quranic marks. |
| Quality of dawah (p.5) | Age-appropriate, foundations first | Pass `age_band` to the agent; 6-9 and 10-13 explanations |
| Translation (p.5, p.7) | Keep "Tawhid", "Salah" and so on, with the approved gloss | Term items plus a prompt rule |
| Transparency (p.5) | Disclose AI | Persona rewrite, first-meeting line, AI chip in the UI |
| Privacy (p.5) | Minimum data, a disclosed policy, no religious profiling | Privacy page, processor list, report prompts forbid religious inference (section 7.5) |

---

## 2. What we found (short)

Full detail and evidence tags are in the research files.

| Finding | Source | Effect |
|---|---|---|
| Every source host is blocked from the cloud container, and dorar.net's hadith API is blocked even in the lead's own Chrome | proxy log; Cowork README; lead's report | dorar hadith comes only from pages a human opens. Scripted sources need the laptop or the domain allow-list. |
| HadeethEnc API: about 3,574 curated hadith, 72 languages, Arabic and English together, categories, `grade`, `attribution` and `reference`. **No number field, no named grader, no per-record URL field.** A regex on the Arabic `reference` recovers book and number for 55% of Bukhari/Muslim records across the whole corpus. For our values the pool is 277 English Bukhari/Muslim records, 116 with an extractable number. Kindness-to-animals has none (r1 Appendix B). Page URL: `hadeethenc.com/<lang>/browse/hadith/<id>`. One record is graded `ضعيف`. | r1 §2 | Good for finding hadith and for the English translation. Number and grade still need a check on dorar or Shamela. |
| The Association's reuse policy allows storage, indexing, "RAG and AI assistants", with no permission needed, if the text is unchanged, the source and version are cited, and AI text is never presented as theirs | r1 §2.7 | Our design (verbatim text, labelled explanation) already fits. |
| `mcp.islamiccontent.org/mcp`: real, keyless, Streamable HTTP, 11 tools; does not return hadith numbers; one team hit Cloudflare 1010 | r1 §4 | Use while building only, never in the child's voice turn. |
| dorar API real shape `{"ahadith":{"result":"<HTML>"}}`, with no id. Stable hadith page `dorar.net/h/<id>`, id only in the site-search HTML. For Bukhari/Muslim dorar prints grader = the compiler and grade `[صحيح]`. Book ids: Bukhari 6216, Muslim 3088. | r3 §2 | Route D design; gate checks L3/L4 |
| dorar encyclopedias load in a browser; tafsir pages have المعنى الإجمالي, غريب الكلمات and الفوائد التربوية, and cite Ibn Jarir by volume and page | Cowork samples; r3 §3 | Tafsir route avoids the Tabari question. Section layout confirmed on the surah intro page only; verse pages are still to check (L6). |
| Shamela: desktop app (150-266 MB) plus a separate full data folder; no per-hadith grade; Bukhari 1681, Muslim 1727, Kuwaiti Fiqh Encyclopedia 11430, dorar fiqh 38056, dorar creed 38058 | r3 §4-5 | Offline backup |
| Bayyinat PDF: 1,259 pages, 263 questions, five blocks each; broken text layer; verses drawn as glyphs with no text | r2 §2.8 | FAQ needs a glyph-aware extractor and a side-by-side check |
| Children's curriculum «ما لا يسع أطفال المسلمين جهله» on kids.islamenc.com (Association) | r2 §3 | Strong candidate for aqidah and FAQ, pending organiser OK |
| icadb public JSON export: 543 approved Arabic Q&A cards, including the Kaaba, the sword and the qibla | r2 §2.4 | Second FAQ source, pending organiser OK |
| The dictionaries say "Monotheism" for tawhid and "Legal opinion" for fatwa; the package table says "Tawhid / Oneness of God" and "Fatwa" | r2 §4 | Organiser question; our answer keeps the term and gives both |
| Our 74 verses are imlaei, not KFGQPC Uthmani: 0 of 74 match exactly; all 74 equal the Tanzil "simple" text | r4 | Re-fetch and re-review (section 5) |
| everyayah.com (our audio) is not in the package; mp3quran.net is | r4, r5 §2 | Audio decision (section 5.3) |
| The agent claims to be a 16-year-old human, quotes from memory, has no fatwa guard, and typed chat bypasses the grounding hook | r5 §1 | Section 7 |

---

## 3. Source map: every section, its approved source, and how we reach it

"Who" values: **script** (an API, run by a cloud agent once the domain is allowed, otherwise on the lead's laptop), **Cowork** (browser on the lead's Mac, saves pages to `~/Documents/alsadiq-sources/`), **lead** (a human in a browser), **agent** (a cloud subagent building tools or drafting). All saved pages go in the gitignored `content/tools/.cache/`. Only the curated items are committed.

| Section | Approved source (package page) | Alternatives (pending where marked) | Access | Who | Target (floor) |
|---|---|---|---|---|---|
| verse | KFGQPC Uthmani via Quranpedia (p.3) | KFGQPC developer files (p.14); QuranEnc Arabic (pending, Q10) | Quranpedia API | script | 74 now, plus about 8 for the test questions (2:144, 2:256, 112, 2:163, 53:3-4, the forbidden-foods verses), plus about 25 for stories |
| verse translation | Saheeh International via Quranpedia (p.3); QuranEnc `english_saheeh` (p.9) | either | API | script | all verses |
| recitation audio | not ruled; mp3quran.net is the package's audio library (p.12) | everyayah.com (current, not listed) | API + files | script | all verses |
| hadith | Bukhari/Muslim via dorar.net/hadith or Shamela (p.3) | HadeethEnc for discovery (p.9); its English only with its own link (pending, Q13); as the cited source only after Q1 | section 4 | script + lead + second human checker + Cowork | floor 40 is the plan; 76 (2 per value) is stretch |
| tafsir | dorar.net/tafseer (p.3) | early books via Quranpedia or Shamela (Mujahid d.104 fits; Tabari d.310 pending) | browser pages | Cowork/lead + agent | 20 (10) |
| aqidah | dorar.net/aqeeda (p.3) | kids.islamenc.com curriculum (pending, Q7); Shamela 38058 mirror (pending, Q15; automatically digitised) | browser pages | Cowork/lead + agent | 12 (6) |
| fiqh | dorar.net/feqhia or a four-school book (p.4) | Kuwaiti Fiqh Encyclopedia (Shamela 11430) | browser pages | Cowork/lead + agent | 8 (4) |
| sirah | dorar.net/history or early sources (p.4) | Bukhari/Muslim episodes (as hadith items) | browser pages | Cowork/lead + agent | 8 (4) |
| faq | Bayyinat PDF (p.4) | icadb Q&A cards (pending OK) | local PDF + extractor | agent + lead | 25 (15) |
| term | Al-Jamhara dictionary (p.4) | terminologyenc.com as cross-check | by hand, 5 s apart | lead or Cowork + agent | 25 (12) |
| story | verses + dorar tafsir only (our rule) | none | built from bank items | agent + the team | 6 (3) |

Not used for child content: the fatwa sites (islamqa, binbaz, binothaimeen: Level D material), risala.prh.gov.sa (pilgrim fiqh), the modern tafsirs al-Muyassar and al-Mukhtasar (pending r1 Q4), Hugging Face or GitHub dumps of any platform (no provenance).

---

## 4. Hadith plan (the main question)

### 4.1 What a hadith item must carry

The package says (p.3) "do not attribute a hadith without including its source and an approved authenticity grading in the data". Our item therefore needs:

- `arabic_text`, copied verbatim from the page in `source_url`;
- `book`, `number`, `narrator` if shown;
- `grade` (exact `صحيح` for anything we serve) and `grader`;
- `source_site` and `source_url`.

`english_text` is optional, and only from an approved translation (HadeethEnc). It is copied byte for byte, with `translation_name` and its own `translation_source_url`, because the English does not appear on the dorar page that `source_url` points to (p.5: never attribute text to a reference that lacks it). The child explanation is ours, and labelled as ours.

### 4.2 The options, and who does each

| Route | Steps and who | Complies? | Cost | Risk |
|---|---|---|---|---|
| **H. HadeethEnc find + dorar prove (recommended)** | (1) **script**: pull HadeethEnc categories mapped to our 38 values (r1 Appendix B), `language=ar` and `en`, keep only grade `صحيح` with a Bukhari/Muslim attribution. Store raw JSON, its SHA-256 and the date. (2) **agent**: rank candidates per value (short, child-suitable, not in the deny-list of r1 §2.6) and extract the number from `reference`. (3) **lead or Cowork**: open the dorar.net hadith page for each pick (search the first words, or `dorar.net/h/<id>`) and confirm book, number and grade. Save the page; the item cites it. (4) **agent**: write the item, with `arabic_text` from the dorar page. HadeethEnc's English is used **only if** the two matns are equal after removing tashkeel, tatweel, punctuation and whitespace, with the narrator clause stripped on both sides or neither. It is copied byte for byte, with `translation_source_url` = the HadeethEnc page, and the id, `retrieved_at` and JSON sha256 go in `provenance.json`. Otherwise the English stays blank. (5) **lead or second checker**: the dorar check (step 3) and `mark_reviewed.py` in one pass. | Yes for the Arabic: dorar is named in p.3. The English beside it is pending Q13 (p.9, p.11: "for approved translations rely on the Association's platforms"); until then it can be left blank. | script 1 h, triage 1 h, then dorar check and review in one pass, about 3-4 min per item (2.5 h for the floor of 40) | Gate L4: dorar hadith pages must load. If they don't, go to route S for the proof step. |
| **D. dorar only** | (1) **lead or Cowork**: about 38 searches on `dorar.net/hadith/search` filtered to Bukhari (6216) and Muslim (3088), saving each results page as HTML. (2) **agent**: offline parser `fetch_hadith.py --from-file` (r3 §7.1) lists candidates. (3) **agent + lead**: pick 2 per value. (4) **lead**: review. | Yes, fully (p.3 names dorar). No English text (the child explanation covers it). | parser 1.5-2 h, capture 1 h, review 2.5 h | Gate L3: the search page must load and save. Cowork could not use the native Save dialog last night, so the lead may need to click Save. |
| **S. Shamela offline** | (1) **lead**: install Shamela, add Bukhari (1681) and Muslim (1727). (2) **agent or script**: read `database/book/*.db` and extract text and number. (3) grade `صحيح`, grader = the compiler, by the Bukhari/Muslim convention. (4) **lead**: review against the Shamela page. | Yes for text and numbers (p.3 names Shamela). The grading by convention needs organiser confirmation (r3 Q1). | 3-6 h of tooling | Format unknown; large download |
| **HE. HadeethEnc as the cited source** | as H, but cite `hadeethenc.com` and skip the dorar step | Only if the organisers confirm HadeethEnc is an approved hadith source and its `grade` is an approved grading (r1 Q1). The package's hadith row names only dorar and Shamela. | cheapest | Rule risk until answered. Needs a schema change. |
| **MCP** | Ask `mcp.islamiccontent.org` per topic while curating | Discovery only (no numbers) | low | Cloudflare 1010 |

**Recommendation:** start route H's script step now, and run gate checks L3 and L4 (section 10) first thing in the morning.

- **If dorar pages load,** H is the main route. D's parser is a cheap second input, for values where HadeethEnc has too few hadith.
- **If dorar pages are blocked too,** route S still needs organiser question 2, and route HE needs question 1. Until one is answered, ship 0 hadith and decline hadith requests (DECLINE_NO_SOURCE). Send both questions first thing.
- **Never** cite a hadith whose text we did not copy from the cited page.

### 4.3 Numbers and rules for the hadith batch

- **Target:** floor 40 (2 each for the 20 most used values) is the plan; 76 (2 per value) is stretch.
- **Selection:**
  - Bukhari or Muslim only.
  - Short (at most about 60 Arabic words).
  - Not in any category of r1 §2.6's deny-list. Check **every** category a record belongs to: 139 jihad, 128 punishments, 127 crimes, 124/191/581 marriage, 205/607 relations between men and women, 63/84 portents of the Hour, 324 Paradise and Hell descriptions, 323 grave, 83 barzakh, 65/71 sects and disbelief.
  - At least 10 hadith that answer the package's test questions. Candidates: lying and honesty, mercy, anger, cleanliness and faith (for the misquote test), the judge who strives (ijtihad), parents, smiling and kind words.
- **Numbering:** dorar's Bukhari is the Salafiyya edition and Shamela 1681 is the Sultaniyya edition. The same numbering is expected, but that is not yet verified: confirm with check L9. Muslim uses Fuad Abd al-Baqi; agree a suffix (`1009-2`) for variants sharing one number before the first import (r3 §2.6). Check one hadith on both dorar and Shamela first (check L9).
- **`grader`:** `البخاري` or `مسلم`, exactly as dorar prints it. dorar shows one entry per book, so an agreed-upon hadith becomes one item per book entry (or one item, with "agreed upon" in the review note).
- **`grade`:** `صحيح` only. dorar prints it in brackets as `[صحيح]`; we store it without the brackets, which is a lead decision (r3 Q1). `clean()` rejects anything else for `seeded` or `reviewed`.
- **Provenance:** store `retrieved_at` and the SHA-256 of the raw response or page in a sidecar `content/provenance.json`, keyed like the review ledger. This keeps the item hash and schema unchanged.
- **Tools** (agents build them; none contains hadith text):
  - `tools/fetch_hadeethenc.py`: pull, filter, rank, extract numbers, and print candidates.
  - `tools/fetch_hadith.py`: an offline parser for saved dorar HTML or text, plus the copy-button format.
  - Both write drafts as `unverified` until a human confirms against the cited page.
- **Card:** "Sahih al-Bukhari <n> · graded sahih (al-Bukhari) · source: الدرر السنية". English line: "Translation: HadeethEnc.com #<id> (retrieved <date>)", with a link to the HadeethEnc page.
- **Second checker:** give the dorar number and grade checks to a second team member (Majd, as r1 §6 suggests). The lead then only signs off.

---

## 5. Quran text and recitation

### 5.1 The text problem (r4 §2)

- **Against the KFGQPC Hafs data (v18):** 0 of our 74 stored verses match exactly. 2 match after trivial normalisation, and none contains alef wasla (the same verses have 297 in KFGQPC).
- **What we actually have:** all 74 equal Tanzil's "Simple Plain" text once waqf signs are removed. That is an imlaei (dictation) spelling with diacritics.
- **More than spelling:**
  - 20 verses differ in rasm (the letter skeleton), for example `الصَّلَاة` versus `ٱلصَّلَوٰة`.
  - 5 verses carry different waqf (pause) signs from the Madinah mushaf: 2:261, 2:262, 5:119, 16:78, 24:22.
- **The package's requirement:** "the Quranic text in its approved orthography and textual form" (p.3). As it stands, this fails.
- **Cause:** `fetch_verse.py` reads Quranpedia **mushaf 1**. Quranpedia's own metadata puts the KFGQPC Uthmani text at **mushaf 2**, which equals KFGQPC v18 on all 6,236 ayat (apart from kashida placement). Git history shows no hand edits; the wrong id was used from the start.
- **Translation is fine:** 73 of 74 English texts equal QuranEnc `english_saheeh`. 74:4 has one extra full stop to remove.

### 5.2 Fix (about 2.5 to 3 hours, mostly scoped re-review; r4 §6-7)

1. **Pin one text release.** First choice is the Complex's own `UthmanicHafs_v2-0` JSON from `qurancomplex.gov.sa/quran-dev`, which the lead downloads; record its sha256. Otherwise use Quranpedia mushaf 2, and say so in `text_edition`.
2. **Migration (task 01):**
   - Add `arabic_text_search`, filled from KFGQPC's own `aya_text_emlaey`, and build `search_text_norm` from it. If `arabic_text` is replaced without this field, searches for `الصلاة` and `الوالدين` stop matching.
   - Add `text_edition`.
   - Add U+08F0-08F2 to `normalize_ar`.
3. **`fetch_verse.py`:**
   - Read the pinned file, or mushaf 2.
   - Fail on a sha mismatch.
   - Strip only the ayah-number suffix.
   - Emit the search text and the edition.
   - Fix the docstring.
   - Add `verify_arabic.py` (r4 Appendix A) to the checks.
4. **`refresh_arabic.py`:** replaces only `arabic_text` in `items/*.json` and adds the two new keys. Every review hash then goes stale, as designed.
5. **Automatic proof:** `verify_arabic.py` must report 0 mismatches. The lead's re-review then shrinks to about 30 minutes:
   - the font renders with no empty boxes;
   - the 5 waqf-sign verses, checked against a Madinah mushaf;
   - 10 sampled rasm-change verses.

   Then run `mark_reviewed.py` again.
6. **Display:**
   - Use the KFGQPC Hafs font, unmodified TTF; converting it to woff2 counts as "modification" under its EULA, so ask the organisers.
   - Fallback: Amiri Quran, with open-tanween code points mapped at display time only.
   - Size at least 28 px.
   - Never store the ayah number inside `arabic_text`.

### 5.3 Audio (r4 §4)

| Option | In the package? | Teaching (Muallim) style | Per-ayah files | Effort |
|---|---|---|---|---|
| everyayah.com Husary Muallim (today) | No | Yes (Husary) | Yes | none |
| mp3quran.net, cut by the `ayat_timing` API | **Yes** (p.12, the only audio platform named) | Minshawi Muallim (read 114) exists; **no Husary Muallim** in the snapshot read | No: cut surah files with `cut_ayah_clips.py` (written and tested offline) | 1-2 h for 35 surahs, plus listening |
| King Fahd Complex ayah sets | the Complex is the Quran authority (p.14); audio is not described | No (murattal: Hudhaifi, al-Muaiqly and others) | Yes (about 6,350 files per set) | download about 1 GB; the host may answer only from KSA |

**Recommendation:** keep everyayah for the demo, which already works and has been reviewed.

- Disclose it on the card: "Recitation: Mahmoud Khalil Al-Husary, everyayah.com" (switched from the Muallim read to normal pace on 2026-10-06, lead decision).
- Ask the organisers (question 9).
- Decide the audio source **before** fetching new verses. The about 8 test-question verses and the story verses need recitation, and until then they would have none. The live check: does mp3quran have a Muallim read with ayah timings?
- If yes, switch everything to mp3quran with the cut script. The file names stay the same, so nothing else changes.
- Either way, consider moving the 46 MB of mp3s out of git into a build-time download. The repo should not redistribute files whose licence is unstated.

---

## 6. The other sections

Common rules:

- The excerpt in `arabic_text` is a contiguous, verbatim cut from the page in `source_url`.
- The child explanation (6-9) and the older one (10-13) are ours.
- Every item gets `content_level`.
- Pages are saved by the lead or Cowork in a normal browser, one every few seconds, into `content/tools/.cache/` (gitignored).
- Agents never fetch dorar or Al-Jamhara by script.
- **Age screen for every excerpt** (Bayyinat, tafsir, sirah, aqidah, as well as hadith): run the same deny-list topics as §4.3. Doubt-type FAQs (the sword, other religions) default to `age_band` 10-13.

### 6.1 Tafsir (target 20)

- **Source:** `dorar.net/tafseer/<surah>/<n>` (n is the verse-group page, not the ayah). The section layout below was confirmed on the surah intro page; confirm it on a verse page with check L6 before drafting. The sections to use are **المعنى الإجمالي** (overall meaning), **غريب الكلمات** (word meanings) and **الفوائد التربوية** (educational lessons), which suit our values well.
- **Pages:** one tafsir item per most-used bank verse. The lead or Cowork saves the verse-group page for each (list prepared by an agent from `items/*.json`).
- **Item:** `title_*` = "Tafsir of S:A-B", `book` = "موسوعة التفسير - الدرر السنية", `number` = "S:A-B" (dorar pages cover a group of verses), `related` = every bank verse in the group, and the card header says "Tafsir encyclopedia (al-Durar al-Saniyya) says:".
- **Tabari:** direct Tabari excerpts stay optional until the organisers rule on d. 310 H. dorar already quotes Ibn Jarir with volume and page.
- **Allow-list:** dorar.net must be added to the tafsir allow-list in `clean()`.

### 6.2 Aqidah (target 12)

- **Source:** `dorar.net/aqeeda/<id>` pages for the six pillars of faith, tawhid, why Allah created us, and the meaning of the shahada. These pages are short (1-3 sentences), which suits excerpts.
- **If the organisers approve:** the kids curriculum on kids.islamenc.com (creed section, nine plain questions).
- **Sensitive list (held back, Level C, referral only, unless a scholar signs off):** where is Allah, qadar, the fate of others, sects, the attributes debate.

### 6.3 Fiqh (target 8)

- **Source:** `dorar.net/feqhia` pages, taking **only sentences that state agreement** (for example the five daily prayers, facing the qibla, the parts of wudu). The Kuwaiti Fiqh Encyclopedia (Shamela 11430) cross-checks agreement.
- **Level:** every fiqh item is at least B, and gets the referral line.
- **Disagreement:** where a dorar page lists two opinions, the item is Level C. Its `disagreement_note_*` says scholars differ, and it never picks a side. The types-of-water sample shows this pattern.

### 6.4 Sirah (target 8; cut first if short of time)

- Episodes narrated in Bukhari/Muslim, stored as hadith items, so they carry a grade.
- `dorar.net/history/event/<id>` for short context lines (for example the birth in the Year of the Elephant).
- Mark caution where the page itself notes disagreement (the birth date).

### 6.5 FAQ (target 25)

- **Source:** the Bayyinat PDF (`dawa-7937-bayyinat.pdf`, already on the lead's Mac).
- **Extraction:** an agent writes `tools/extract_faq.py` using PyMuPDF glyph-order rebuilding, because the PDF's text layer is broken (r2 §2.8).
  - The PDF stays local and gitignored. To let a cloud agent run the extractor, the lead uploads it into the session; it lands in the gitignored cache.
  - The extractor renders each page image next to the text, so the lead can check honorifics.
- **Item:** `title_ar` = السؤال; `keywords_ar` = the "similar wordings" block; `arabic_text` = 1-3 paragraphs of **مختصر الإجابة** (the short answer); `number` = `Q<n> · p.<printed page>`; `source_url` = `https://dawa.center/file/7937#p<page>`.
- **Verses:** verses inside Bayyinat are glyphs, never text. Link them through `related` only if the verse is already in the bank.
- **First picks:** the Kaaba and qibla, the source of the Quran, the sword, who is Allah, why we pray, the Prophet's honesty.
- **Second source:** icadb cards 36130, 36112, 36240 and 36083 only if the organisers approve.

### 6.6 Terms (target 25)

- **Source:** Al-Jamhara dictionary pages by hand (`islamic-content.com/dictionary/word/<id>/en`). Ids for the package's 10 sample terms are in r2 §4: 1018, 3529, 6732, 10342, 10849, 5979, 4139, 5744, 1366 or 12075, 4892.
- **Child terms (15 more):** salah, zakah, sadaqah, wudu, iman, ihsan, taqwa, halal, haram, amanah, sabr, dua, Ramadan, Hajj, Quran.
- **Item:**
  - `title_en` = the dictionary's English equivalent, verbatim;
  - `arabic_text` and `english_text` = its definitions, verbatim, with `translation_name` = "Al-Jamhara (en)";
  - `keywords_*` = spelling variants (namaz, salat, solat).
- **Agent rule:** keep the Arabic term, give the dictionary equivalent, and add one plain sentence. For tawhid it also notes "more than just counting one", per the package's p.7 guidance.

### 6.7 Stories (target 6)

- Unchanged from `content-structure-plan.md` §6: the team's candidate files, grounding table, no Israiliyyat, verses played as recitation.
- **One change:** the tafsir items a story relies on come from dorar.net/tafseer (section 6.1), not Tabari.
- **Until reviewed stories exist,** the agent must not tell prophet stories at all (r5 D2).

---

## 7. Agent and app behaviour (the compliance work outside the bank)

These are from r5. The ten P0 fixes are in r5 §5, with acceptance tests.

### 7.1 Prompt and persona (task 03, P0)

- **Disclose AI:**
  - Answer "are you a person?" honestly.
  - Add one AI line at the first meeting.
  - Never claim to pray, eat, have a family, or be a scholar.
  - Keep the warm tone. Remove "a 16-year-old friend".
- **Grounding:**
  - No verse, hadith, tafsir line, ruling, date or story unless it is in VERIFIED SOURCES this turn. "The Prophet taught…" counts as a hadith attribution.
  - Remove the "offer a prophet story" quirk.
- **Verdicts:** no verdicts on validity, permissibility or disputed matters. Moral direction on everyday behaviour stays.
- **Hostile questions:** do not mirror; find the real question; answer kindly.
- **Insufficient source:** "I don't have a trusted source for that, so I won't guess", then refer.
- **Spoken hadith paraphrase:** say "in simple words, the hadith on your screen means…", never "the Prophet said" followed by our words (r1 §2.7).
- **Retire the legacy path:** switch off the 19 English paraphrases and the `get_islamic_reference` tool.

### 7.2 Turn guard (task 03, P0)

- **One code path for voice and text:** a single `prepare_turn(text, lang, age_band)` called from **both** `on_user_turn_completed` and the typed-text handler. In livekit-agents 1.5.1, typed text never reaches the hook.
- **Checks, deterministic first:**
  1. **Safety first:** family-dispute or harm patterns (fighting, divorce, hitting, fear at home) do **not** go to the parent route. They call the existing `flag_safety_concern` flow, and the reply refers the child to "a trusted adult or a teacher". They are never listed on the parent dashboard's "questions to discuss".
  2. Level D patterns: first person plus permission or validity.
  3. Level C topic list.
  4. A religious question with no served item becomes DECLINE_NO_SOURCE.
  5. Otherwise the highest `content_level` of the served items decides.
- **Modes:** ANSWER, EXPLAIN, DISAGREE_AND_REFER, REFER, DECLINE_NO_SOURCE, CLARIFY.
- **Rules file:** `content/turn_rules.json`, editable by the lead, Arabic and English.
- **Audit:** a `TurnAudit` row (level, mode, item ids, no text) feeds the eval and the parent's "questions to discuss" list, excluding the safety patterns in check 1.
- **Misquoted verses (test Q11):** load the pinned KFGQPC JSON into memory as a read-only lookup, used only by `verify_quote` (by surah and ayah, and normalised text). It needs no model and no migration. If it is skipped, the submission states the limitation.

### 7.3 Never speak scripture (tasks 03 and 07, P0)

- No Arabic scripture text in the LLM context. Send it only in the `reference` event for the card.
- `tts_node` drops ﴿…﴾ and dense Quranic-mark runs.
- **Output check, not just the prompt:** a reply that contains "the Prophet said", "Allah says", "قال رسول الله" or "قال الله تعالى" in a turn where nothing was served is replaced with the DECLINE template, and the event is logged.
- Verses play only as recitation audio.

### 7.4 Cards and labels (tasks 04 and 05, P0)

- "From <source>: <verbatim>" versus "In simple words, for children (our explanation, not the source's words): <ours>".
- Hadith cards show the grade and grader; every translation card shows the translator.
- The tafsir card is separate from the verse card.
- The parent trust line becomes: "Verses and hadith shown on a source card come from approved sources; explanations are AI-generated and simplified."

### 7.5 Privacy and transparency surface (tasks 04, 05 and 10, P0)

- A `/privacy` page and a mobile sheet, in Arabic and English, listing the processors: OpenAI, xAI or ElevenLabs, LiveKit, Mailtrap.
- An AI chip on the conversation screen, and an AI clause in the Terms.
- Report prompts never infer or rate the child's or family's religiosity.
- Remove the raw 120-character message preview shown to parents.
- The privacy page states retention: flagged messages kept N days, then a sweep (r5 H5).
- Weekly parent summaries contain no scripture, no rulings and no religious judgement of the child (r5 J1, P0). Memory keeps only facts the child stated (r5 D7).
- Say plainly, on the parent page and in the submission, that "reviewed" means checked against the source by our team, not reviewed by a scholar (r5 A6).
- Lead decides: keep the honesty score internal, or drop it.

### 7.6 The 12 test questions

r5 §4 rephrases each one for children, with the expected answer shape, its level, and the items it needs. Section 9's day plan seeds exactly those items first:

- the qiblah (Q1);
- revelation of the Quran (Q2);
- the sword (Q3, age 10-13);
- ijtihad (Q4);
- the tawhid term and verses 112 and 2:163 (Q7, Q8);
- the FAQ on prohibitions, plus the forbidden-foods verses (Q9);
- two Level C fiqh items (Q10);
- the misquote hadith and verse 9:108, plus `verify_quote` (Q11);
- the salah term with its namaz and salat variants, and the "in sha Allah" term (Q12).

Q5 (personal case) and Q6 (an invented hadith) need no items, only the guard.

---

## 8. Schema changes (one task-01 migration, before the next review block)

Every new field is optional, so the existing 74 rows stay valid. Add them all at once: any later file key changes item hashes and forces re-review.

| Change | Why |
|---|---|
| `title_ar/en`, `keywords_ar/en`, `related` (self M2M) | From `content-structure-plan.md` §2 (unchanged) |
| `content_level` (A/B/C) with a default by type; `disagreement_note_ar/en` (required for C) | Package levels (r5 §3.2) |
| `SOURCE_SITE_CHOICES` adds `hadeethenc.com`, `quranenc.com`, `islamenc.com`, `terminologyenc.com`, `mp3quran.net`. Type matrix: dorar.net allowed for tafsir; hadith cited site stays dorar or Shamela until organisers OK HadeethEnc; `islamic-content.com` for terms only (not sirah, not hadith); `islamenc.com` and `terminologyenc.com` are **not citable for any type** until the organisers approve them | Reconcile the whitelists (r5 §2). Fix `content-curator.md`, `AGENTS.md`, README and `content-structure-plan.md` to match. |
| `translation_source_url` (URL, blank) | The English translation's own source link (route H); this migration is the only window, because a later key changes every hash |
| `clean()`: a hadith needs `arabic_text` and grade exactly `صحيح`; `english_text` needs `translation_name`; every non-verse type except story needs `arabic_text`; level C needs a disagreement note and `reviewed` before it is served | r5 A4, A5 |
| `arabic_text_search` (KFGQPC `aya_text_emlaey`, the source of `search_text_norm` for verses) and `text_edition`; U+08F0-08F2 in `normalize_ar` | Verse text fix without breaking search (r4 §6) |
| `audio_url` host check: mp3quran.net or everyayah.com, per the section 5.3 decision | r5 §2 |
| Retrieval serves verses `seeded` or `reviewed`, and every other type `reviewed` only | r5 A7. A human picks every non-verse excerpt. |
| `TurnAudit` model (task 03's migration) | r5 §3.3 |

---

## 9. Day 2 work plan (Mon 5 Oct; feature freeze 21:00)

Times are Riyadh time. Agents run in parallel in separate worktrees, in the cloud, once the domains are allowed. **The floor targets are the plan; the full targets are stretch.** The lead's time is the bottleneck, so number and grade checks go to a second human checker (Majd), and Cowork only saves page text (it cannot use the native Save dialog). Owners for tasks 03, 04, 05 and the eval are still TBD on the task board, and the lead assigns them at 08:00.

| When | Step | Who | Depends on |
|---|---|---|---|
| 08:00 | Allow the domains in the cloud environment (0.5). Read section 11 and decide. Send section 12 to the organisers. | lead | none |
| 08:15 | Gate checks L3, L4, L9 in Chrome (section 10). Upload the Bayyinat PDF into the session. | lead or Cowork | none |
| 08:30 | **Migration** (section 8) plus `clean()` rules plus whitelist reconciliation plus tests | `backend-dev` agent (task 01) | lead decisions 2-4 |
| 08:30 | **Verse fix:** `fetch_verse.py` on the pinned KFGQPC text, `refresh_arabic.py`, `verify_arabic.py` showing 0 mismatches (section 5.2) | `content-curator` agent (+ `backend-dev` for the search field) | domains or the Complex JSON |
| 08:30 | **Hadith script:** `fetch_hadeethenc.py`, pull, filter and rank per value | `content-curator` agent | domains |
| 08:30 | **Agent P0:** persona and prompt rewrite, legacy path off, `prepare_turn` on both paths, level guard, TTS scripture filter, output check | `voice-agent-dev` agent (task 03) | prompt work now; its TurnAudit and pg_trgm migrations only **after the 01 migration is merged** (pg_trgm now indexes the new search field) |
| 10:30 | Hadith proof and review in one pass: open the dorar page for each pick, confirm number and grade, then `mark_reviewed.py` (route H steps 3 and 5) | second checker (Majd) + lead sign-off | gate L4, script and triage done |
| 09:30 | FAQ extractor on the uploaded PDF; first 15 short answers | `content-curator` agent | PDF upload |
| 10:00 | Tafsir, aqidah, fiqh and history pages saved from dorar (lists prepared by an agent) | Cowork or lead | none |
| 10:00 | Terms: the 25 Al-Jamhara pages by hand | Cowork or lead | none |
| 11:00 | Draft tafsir, aqidah, fiqh and term items from the saved pages | `content-curator` agents (one per section) | saved pages |
| 12:00-18:00 | **Review blocks:** verses (scoped re-review, 30 min), then the test-question items (FAQ, terms, two fiqh C items), then tafsir and aqidah | lead | drafts |
| 14:00 | Cards and labels, AI chip, privacy page | `frontend-dev` agent (+ `mobile-dev` for the chip and sheet) | event shape from 03 |
| 16:00 | Eval cases for the 12 test questions (text **and** voice path) | eval owner | 03 |
| 19:00 | `seed_content` with 0 rejections, `mark_reviewed.py --check` clean, reviewer agent spot-checks 10 items per section | agents + lead | all |
| 21:00 | Freeze | | |

**The floor (the plan):** verses fixed, about 8 test-question verses, 40 hadith, 15 FAQ, 12 terms, 10 tafsir, 6 aqidah, 4 fiqh (two of them Level C), no sirah, 3 stories. Cut order: sirah, then stories beyond 3, then fiqh beyond 4, then tafsir beyond 10.

---

## 10. Checks for the lead's laptop (in this order)

Save results into `~/Documents/alsadiq-sources/` (then upload them here) or the gitignored cache. If a page shows a CAPTCHA or a block, record the message and stop. Never work around a block.

| # | Open | Decides |
|---|---|---|
| **L3 (gate)** | `https://www.dorar.net/hadith/search?q=الصدق&s[]=6216&s[]=3088`. Save as "Webpage, HTML only" and also as text. | Route D works; the parser can be built from it |
| **L4 (gate)** | any `https://dorar.net/h/<id>` from L3. Save it, and paste what the copy button copies. | Route H's proof step works |
| L9 | Bukhari 6094 and Muslim 2607 (honesty) on dorar and on Shamela (`shamela.ws/book/1681`, `/1727`) | The numbering schemes match |
| R1 | `https://hadeethenc.com/api/v1/hadeeths/one/?language=ar&id=2962` and `language=en`. Save the JSON. Only needed if the cloud domain allow-list is not set. | API shape and the `reference` field today |
| Q1 | `https://qurancomplex.gov.sa/quran-dev` (download `UthmanicHafs_v2-0.zip` if offered, and note its sha256) and `https://api.quranpedia.net/v1/mushafs/2/2/153` | The pinned text release (section 5.2) |
| A1 | `https://mp3quran.net/api/v3/ayat_timing/reads` and `https://mp3quran.net/api/v3/reciters?language=eng&reciter=118` | Is there a Muallim read with timings? (section 5.3) |
| L6 | `https://dorar.net/tafseer/98/1`, saved | Tafsir verse-page layout |
| L5 | `https://dorar.net/article/111` (copying rules) and `/article/56` (bracketed grade) | Quotation limits; the meaning of `[صحيح]` |
| T1 | Two Al-Jamhara pages (`islamic-content.com/dictionary/word/3529/en`, `/1018/en`) | Term item format |

The full lists are in r1 §8, r2 §9, r3 §11 and r4 §9. If the domains in 0.5 are allowed, the cloud agents run R1, Q1 (the Quranpedia part) and A1 themselves. Only the dorar and Al-Jamhara pages need you.

---

## 11. Decisions for the lead (recommendation first)

1. **Hadith route:** H with D as a second input (recommended), or D only, or S. Decide after L3 and L4.
2. **Verse text:** re-fetch all 74 as KFGQPC Uthmani and re-review (recommended, required by p.3). Keeping the imlaei text is not compliant. Also pick the pinned release: the Complex's v2.0 JSON (recommended) or Quranpedia mushaf 2.
3. **Audio:** keep everyayah Husary Muallim for the demo with a disclosure, and switch to mp3quran only if a Muallim read with timings exists (recommended). Also decide whether to move the mp3s out of git.
4. **Serve only `reviewed` for non-verse items** (recommended) or also `seeded`.
5. **Tabari:** use dorar.net/tafseer only until the organisers answer (recommended).
6. **Sensitive aqidah list** (where is Allah, qadar and the others): leave them at REFER until a scholar signs off (recommended).
7. **Stories with mature themes:** exclude (recommended).
8. **Honesty score:** drop it, or keep it internal and never shown (recommended: drop the score; award badges from explicit events).
9. **Gender:** make it optional, and keep `girls_note` only as general, referral-style text (recommended).
10. **Font:** the unmodified KFGQPC TTF (recommended), or Amiri Quran with display-time mapping until the organisers allow woff2.

---

## 12. Questions for the organisers (send today; questions 1 and 2 first, because hadith depends on them if dorar is blocked)

1. Is HadeethEnc (hadeethenc.com) an approved **hadith** source we may cite, and is its `grade` an approved grading for Bukhari/Muslim items? (r1 Q1, r3 Q9)
   - **Answered by the organisers (5 Oct):** HadeethEnc English + dorar Arabic accepted; show both links.
2. For a Bukhari or Muslim hadith, is "grade صحيح, grader = the compiler" enough when the text comes from a Shamela edition? (r1 Q2, r3 Q1)
3. Does "first three Islamic centuries" include al-Tabari (d. 310 H)? Is dorar.net/tafseer alone enough for every tafsir item? (r3 Q2)
4. Is there a sanctioned way to use dorar's hadith API? It is blocked even in a normal browser on our network. (r3 Q5)
5. How much verbatim text may we quote from a dorar encyclopedia page per item? Its pages say "all rights reserved". (r3 Q6)
   - **Answered by the organisers (5 Oct):** Short paragraph with link plus our simplification for children is allowed.
6. May we commit short Bayyinat excerpts (1-3 paragraphs, with question number and page) and show them to parents? (r2 Q1)
   - **Answered by the organisers (5 Oct):** 1-3 paragraphs allowed with Q number, page and book name/link.
7. May we use the Association's kids curriculum (kids.islamenc.com), the icadb Q&A cards and terminologyenc.com for aqidah, FAQ and terms? (r2 Q2, Q3)
8. "Translate tawhid": the dictionary says "Monotheism", but your table says "Tawhid / Oneness of God". Which is the expected output? The same question applies to fatwa and sharia. (r2 Q4)
   - **Answered by the organisers (5 Oct):** Both Monotheism and Tawhid are correct; prefer whichever fixes meaning for non-Arabic speakers.
9. Is everyayah.com acceptable for recitation audio, or must audio come from mp3quran.net or the King Fahd Complex? May we cut per-ayah clips from mp3quran surah files? (r4 Q4)
   - **Answered by the organisers (5 Oct):** everyayah recitation accepted; state source name and link clearly.
10. Which KFGQPC text release is canonical (v18, v2.0 or v3.0; open tanween is encoded differently)? Is a Quranpedia ayah page an acceptable `source_url` for KFGQPC text? Does QuranEnc's Arabic count too? May we self-host the KFGQPC font converted to woff2? (r4 Q1-3, Q6; r1 Q5)
   - **Answered by the organisers (5 Oct):** small waqf-sign differences between digital mushafs are normal and do not affect the verse text; Quranpedia as our main source is accepted; cite it by name in documentation and display.
11. Is server-to-server access to `mcp.islamiccontent.org` and the Association APIs from cloud IPs allowed (one team saw Cloudflare 1010)? (r1 Q3)
12. For "why do scholars give different rulings?", which source do you expect? It is outside Bayyinat's scope. (r2 Q8)
13. May we show HadeethEnc's English translation beside Arabic hadith text cited from dorar.net, each with its own link? (route H)
   - **Answered by the organisers (5 Oct):** HadeethEnc English excellent with dorar Arabic; show both links.
14. May we cite dorar's ethics and etiquette encyclopedias (`dorar.net/alakhlaq`, `/adab`) for values content? (r3 Q3)
15. Do Shamela copies of dorar's fiqh and creed encyclopedias (books 38056, 38058) and the Kuwaiti Fiqh Encyclopedia on Shamela (11430) count as approved sources? (r3 Q4)
16. Do you expect an extra scholar check for aqidah items? dorar's creed encyclopedia names no reviewers. (r3 Q8)
   - **Answered by the organisers (5 Oct):** dorar aqidah verbatim quotes are reliable; no dedicated scholar reviewer needed.
17. How should the voice agent label a spoken paraphrase of a hadith versus its original text? (r1 Q8)
   - **Answered by the organisers (5 Oct):** Separation of explanation from prophetic wording is sufficient.

Also answered (5 Oct): citing published fatwas as open source is allowed with clear attribution to the author and approved source. The organisers' main point: document every source.

---

## 13. Risks

| Risk | Mitigation |
|---|---|
| dorar hadith pages blocked like the API | No compliant hadith route until question 1 or 2 is answered. Ship 0 hadith, decline hadith requests, send both questions at 08:00. |
| A child discloses conflict or harm at home | Safety pattern goes to `flag_safety_concern`, refers to a trusted adult or teacher, and is never shown on the parent dashboard (section 7.2) |
| Lead time (about 11-13 h at full targets) | The floor is the plan; a second checker does the number and grade checks |
| Re-review of the 74 verses eats the morning | The diff is mechanical (orthography only). The reviewer checks surah, ayah and the KFGQPC source, not every letter. |
| HadeethEnc Arabic differs from dorar's narration | English kept only when the Arabic matches; otherwise blank |
| Bayyinat extraction garbles text | Side-by-side page image; honorifics restored by hand and noted |
| A late organiser answer contradicts a choice | Every item records its source; a whole source can be switched off by `source_site` in retrieval |
| Typed chat skips the guard | `prepare_turn` on both paths, with a test |

---

## Appendix: research files

| File | Scope |
|---|---|
| `research/r1-hadeethenc-quranenc-mcp.md` | HadeethEnc API, licence, value-to-category map, QuranEnc, the MCP server, laptop curl commands |
| `research/r2-encyclopedias-terms-faq.md` | islamenc, terminologyenc, Al-Jamhara ids, icadb export, Byenah, IslamHouse, Bayyinat PDF layout, kids curriculum |
| `research/r3-dorar-shamela-fiqh.md` | dorar API and site structure, Shamela, Kuwaiti Fiqh Encyclopedia, early sources, hadith routes and parser spec |
| `research/r4-quran-text-audio.md` | KFGQPC text comparison of our 74 verses, mp3quran, translations |
| `research/r5-compliance-gap.md` | Every rule against our code, levels A-D design, 12 test questions for children, top-10 P0 fixes |
| `resource-package-en.md` | The hackathon's rules and sources (English) |
