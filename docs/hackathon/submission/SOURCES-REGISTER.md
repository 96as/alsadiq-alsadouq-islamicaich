# Register of sources, tools and licences
# سجل المصادر والأدوات والرخص

- **Status:** template, written on 4 Oct 2026. Per-item rows are filled by task 02 (content bank sources) and generated from the bank at code freeze. / قالب كُتب في 4 أكتوبر 2026. تملأ المهمة 02 صفوف البنود، وتُولَّد من البنك عند تجميد الشيفرة.
- **Rule:** no scripture appears in this file. It holds source names, links to sources, and metadata only. Verse and hadith text lives in the content bank and nowhere else. / لا يوجد في هذا الملف أي نص شرعي. فهو يحوي أسماء المصادر وروابطها وبيانات وصفية فقط، ونص الآيات والأحاديث مكانه بنك المحتوى وحده.

## 1. Approved sources (names only)

These are the only sources the content bank may use. They come from the shared instructions (`AGENTS.md`) and from the challenge's reference pack (المرجعية والحزمة العلمية والبيانات). A source not on this list cannot be used, and an item without an approved source cannot be marked `seeded` or `reviewed`.

| # | Content type | Approved source (name) | Public site | Notes |
|---|---|---|---|---|
| S1 | Quran text | King Fahd Complex for the Printing of the Holy Quran (مجمع الملك فهد لطباعة المصحف الشريف) | qurancomplex.gov.sa; `[task 02: exact page URL per item]` | Exact Uthmani text. Surah and ayah recorded for each verse. The reference pack also approves the Complex's translations. |
| S2 | Quran text (alternative) | Quranpedia (قرآنبيديا) | quranpedia.net | Use when the King Fahd Complex page lacks the needed view. |
| S3 | Hadith | Sahih al-Bukhari (صحيح البخاري) | `[task 02: URL per item]` | Collection grade is the authority. Book, number and URL recorded. |
| S4 | Hadith | Sahih Muslim (صحيح مسلم) | `[task 02: URL per item]` | Same fields as S3. |
| S5 | Hadith (other collections) | Other collections, **only with a grade** from Dorar al-Saniyyah (الدرر السنية) | dorar.net/hadith | Grade, grader and URL are mandatory. No grade, no use. |
| S6 | Hadith grading (alternative) | Al-Maktaba al-Shamela (المكتبة الشاملة), as the grade reference | shamela.ws | Same rule as S5. |
| S7 | Tafsir, aqidah, fiqh, sirah | Dorar al-Saniyyah sections (الدرر السنية) | dorar.net | The section used is recorded for each item. Sections named in the reference pack: dorar.net/tafseer, dorar.net/aqeeda, dorar.net/feqhia, dorar.net/history. |
| S8 | Tafsir, aqidah, fiqh, sirah (alternative) | Works from the first three Islamic centuries (مصادر القرون الثلاثة الأولى) | `[task 02: title, author, edition, page]` | Each work named with author, edition and page. |
| S9 | Frequently asked questions | Bayyinat (بيّنات), the Dawa Center | dawa.center (the reference pack's FAQ entry: dawa.center/file/7937) | Used for child-level FAQ wording and topics. |
| S10 | Terminology | Al-Jamhara, the Islamic content portal (الجمهرة) | islamic-content.com (terms: islamic-content.com/dictionary) | Used for terms and wording, not for rulings. |

### Flags for task 02

1. **English translation of the Quran.** The shared instructions name no approved Quran translation. The challenge reference pack approves the King Fahd Complex translations, and says to verify a translation before quoting it. One planned decision (PLAN, decision 4) names the Saheeh International translation, which neither list names. Treat it as **not approved**. The simplest fix is to use the Complex's English translation instead. Until then, no English Quran translation goes into the bank. `[decision pending]`
2. **Recitation audio.** Verses play as recitation audio, never as synthesised speech. The source and licence of the recordings is not on the approved list. `[confirm with the lead, task 05]`
3. **Capstone fixture.** The 19 old references in the capstone fixture have no grading metadata and no recorded translation source. They must not be served as sources unless re-verified against S1 to S10. `[task 01 or task 02]`
4. **Arabic is the primary text.** Each item carries the Arabic text from the source, and a child-level explanation written by the team (not a copy of the source) with a human reviewer recorded.

## 2. Required fields per item

The content bank table in section 3 carries these fields. They follow the shared rules.

| Item type | Required fields |
|---|---|
| Verse | Surah, ayah, exact Uthmani text, source (S1 or S2), URL, recitation audio reference |
| Hadith | Book, number, grade, grader, source URL, collection (S3 to S6) |
| Explanation (tafsir, aqidah, fiqh, sirah) | Source (S7 or S8), section or work, page or URL, content level (A to C), reviewer |
| FAQ | Source (S9), question reference, URL |
| Term | Source (S10), term, URL |
| Any item | Status (`draft`, `seeded`, `reviewed`), date added, who added it |

Content levels used in the product: **A** direct answer with source, **B** explanation with reference, **C** disputed (say only what is agreed, or refer), **D** fatwa or personal case (refer to a parent or scholar, never answer).

## 3. Per-item register (to be filled by task 02, then generated from the bank)

| ID | Source (from section 1) | URL | Grade or authority | What it is used for | Licence or terms of use | Status | Reviewer |
|---|---|---|---|---|---|---|---|
| `[CI-001]` | `[S#]` | `[url]` | `[grade, grader]` | `[value and child question it supports]` | `[terms of the site]` | `[draft / seeded / reviewed]` | `[name]` |
| `[CI-002]` | `[S#]` | `[url]` | `[grade, grader]` | `[...]` | `[...]` | `[...]` | `[...]` |
| `[...]` | | | | | | | |

How to read the "Grade or authority" column: for a verse, the authority is the printing body (S1) or portal (S2). For a hadith, it is the collection (S3 or S4) or the named grader and grade (S5, S6). For an explanation, it is the named work or section (S7, S8).

At code freeze this table is generated from the bank by a script (task 02 owns the script). A row count and a count by source go at the top of this section, so a judge can see coverage at a glance: `[N items, by source: ...]`.

## 4. Tools and services register

| Name | Kind | What it does in the project | Licence or terms | Where described |
|---|---|---|---|---|
| OpenAI API | Service | Speech-to-text, answer model, parent summary | Commercial API terms | `DISCLOSURE.md` section 4 |
| ElevenLabs | Service | Text-to-speech (`eleven_flash_v2_5`), never for verses | Commercial API terms | `DISCLOSURE.md` section 4 |
| LiveKit Cloud and Agents | Service and framework | Realtime audio and the voice agent | Apache-2.0 SDKs, commercial cloud | `DISCLOSURE.md` section 4 |
| DigitalOcean, Caddy | Hosting | Live demo | Commercial terms, Apache-2.0 | `DISCLOSURE.md` section 4 |
| Claude Code (Anthropic) | Development assistant | Building the code, with sub-agents | Commercial terms | `DISCLOSURE.md` section 5, `docs/AI_TOOLS.md` |
| Libraries (Django, React, three.js and others) | Open source | See `THIRD_PARTY.md` | Per package, verified by a scanner | `DISCLOSURE.md` section 2.5 |
| Tripo | Service | Origin of the avatar mesh (pre-existing) | `[confirm terms]` | `DISCLOSURE.md` section 2.3 |
| World Labs (Marble) | Service | The painted meadow `fantasy-meadow.webp`, generated by the team lead with World Labs (pre-existing; the sizes made from it are listed in README section 8) | World Labs terms, https://www.worldlabs.ai/terms-of-service ; which plan the lead's account is on is `[confirm with the lead]` | `DISCLOSURE.md` section 2.4, README section 8 |
| OpenAI Codex | Development assistant | Used by some team members, with `codex-plugin-cc` | Commercial terms | `DISCLOSURE.md` section 5, `docs/AI_TOOLS.md` |

Licence column rule: write what the terms are, from the vendor page, and the date checked. Do not write "free" or "open" without checking the page.
