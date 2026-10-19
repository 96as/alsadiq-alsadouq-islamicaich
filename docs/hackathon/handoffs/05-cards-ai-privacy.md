# Handoff to task 05 (web UI): source card labels, AI disclosure, privacy

- **For:** the owner of task 05 (`hk/05-web-ui`). Code lives on that branch, so this file is the spec; nothing here was built.
- **Written by:** WP6 (documentation reconciliation), 5 Oct 2026, from `content-approach-plan.md` (§5.2, §7.4, §7.5), `research/r5-compliance-gap.md` (A2, A3, G3, H3, K1, K3), `research/r4-quran-text-audio.md` (§3, §6) and `research/r1-hadeethenc-quranenc-mcp.md` (§2.7).
- **Priority:** P0 for verse and hadith cards, the AI chip, the registration line, the Terms clause and `/privacy`. P1 for the other card types.
- **Plan slot:** Day 2, 14:00 ("Cards and labels, AI chip, privacy page"). Feature freeze 21:00.
- **Depends on:** the `reference` event shape from task 03 (section 2 is the proposed contract; confirm with the 03 owner), and the final privacy text in `docs/hackathon/privacy-policy-draft.md` (section 6).

## 0. Why this matters

The hackathon's binding standard (package p.5) says:
- every religious quotation must be traceable to its source, and a text must not be attributed to a reference where it does not appear;
- the solution must distinguish authoritative text from generated explanation;
- the solution must disclose that it is AI;
- personal data must be collected under a disclosed policy.

The UI is where judges and parents see all four. So the rules below are strict and testable. When in doubt, show less text, never invent a label.

Code today (on `hk/05-web-ui`), all under `frontend/src/features/child/sources/`:
- `SourceCard.jsx` shows verse and hadith only, with "Graded by <grader>" and "Translation: <name>".
- `useSourceCards.js` whitelists `KEYS`, allows only `type` verse or hadith, and allows hadith only from dorar.net and shamela.ws.
- `safeUrl.js` has the approved-host allow-list.
- `mockReference.js` has placeholder payloads. Keep every text field a placeholder. Never type real scripture.

## 1. Card label spec (exact strings)

All labels come from one new file, `frontend/src/features/child/sources/sourceLabels.js`, exporting `{ en: {...}, ar: {...} }`. Choose the language from the child's profile language (the same `ar` or `en` the agent session uses), default `en`. The labels are constants in the UI. They never come from the payload. The parent view (task 04) imports the same file, so the wording stays identical.

### 1.1 Two tiers on every card

Every card has up to two clearly different blocks, in this order:

1. **The source block.** Verbatim text copied from the source, under the header "From <source>:". Shown in a quote style (the `Card` surface, a start-edge accent bar, the Arabic in its own `dir="rtl" lang="ar"` element).
2. **The explanation block.** Our own words, under the header **"In simple words, for children (our explanation, not the source's words):"**. Shown in a visibly different style (a tinted surface, dashed border, a small AI glyph, regular body font). It is never inside the quote block, never in the Quran font, never before the source block in the DOM.

| Key | English | Arabic |
|---|---|---|
| `explanationHeader` | In simple words, for children (our explanation, not the source's words): | بكلمات بسيطة للأطفال (شرحنا، وليس نص المصدر): |
| `fromQuran` | From the Quran: | من القرآن الكريم: |
| `fromBook` | From {book}: | من {book}: |
| `says` | {source} says: | {source} يقول: |

If the payload has no `explanation`, render no explanation block and no header. Render the explanation as a plain text node only (no HTML, no markdown). Set `lang` from `explanation_lang`.

### 1.2 Source names by type and site

The header names the source that the text was actually copied from (package p.5: never attribute a text to a reference that lacks it). Pick the header by `type` and `source_site`:

| `type` | `source_site` | English header | Arabic header |
|---|---|---|---|
| verse | quranpedia.net or qurancomplex.gov.sa | From the Quran: | من القرآن الكريم: |
| hadith | dorar.net or shamela.ws | From {book}: (for example "From Sahih al-Bukhari:") | من {book}: |
| tafsir | dorar.net | **Tafsir encyclopedia (al-Durar al-Saniyya) says:** | موسوعة التفسير (الدرر السنية) تقول: |
| tafsir | other (an early book) | {book} says: | {book} يقول: |
| aqidah | dorar.net | From the Creed encyclopedia (al-Durar al-Saniyya): | من الموسوعة العقدية (الدرر السنية): |
| fiqh | dorar.net | From the Fiqh encyclopedia (al-Durar al-Saniyya): | من الموسوعة الفقهية (الدرر السنية): |
| sirah | dorar.net | From the History encyclopedia (al-Durar al-Saniyya): | من الموسوعة التاريخية (الدرر السنية): |
| faq | dawa.center | From Bayyinat (Questions and Answers about Islam): | من «بينات: أسئلة وأجوبة عن الإسلام»: |
| term | islamic-content.com | From the Al-Jamhara dictionary: | من معجم الجمهرة: |

Any other type or site combination: do not render the card (log in DEV). `{book}` is the payload `book`, wrapped in `<bdi>`.

### 1.3 Verse card (top to bottom)

1. Pills: "Verse" / آية, then the value name (`value`).
2. Header `fromQuran`.
3. The Arabic `arabic_text`, `dir="rtl" lang="ar"`, Quran font, 28px or larger (section 3).
4. "سورة {surah_name} : {ayah}" as today. In English UI: "Surah {surah}:{ayah}".
5. If `english_text`: the text, then the translation line (section 1.5). If there is no `translation_name`, do not show the English at all.
6. Caption (small): "Text: King Fahd Complex (KFGQPC), via Quranpedia" / "النص: مجمع الملك فهد (KFGQPC)، عبر Quranpedia". Constant, shown only when `source_site` is quranpedia.net. For `qurancomplex.gov.sa` show "Text: King Fahd Complex (KFGQPC)".
7. The play button, then the recitation credit (section 1.6).
8. Explanation block, if any.
9. If `verification_status` is `reviewed`: a small line "Checked against the source by our team" / "طابقه فريقنا مع المصدر", with the title text "Not reviewed by a scholar" / "لم يراجعه عالم". Do not call it "verified" or "approved".
10. The open-source link (as today).

### 1.4 Hadith card (top to bottom)

1. Pills: "Hadith" / حديث, then `value`.
2. Header `fromBook` with the book, for example "From Sahih al-Bukhari:".
3. The Arabic `arabic_text`, verbatim. Use a normal Arabic reading font (Amiri regular or Noto Naskh Arabic), not the Quran font: the Quran font is for the Quran only. At least 22px.
4. **The citation line, exactly:**

   `Sahih al-Bukhari <n> · graded sahih (al-Bukhari) · source: الدرر السنية`

   Arabic UI: `صحيح البخاري <n> · الحكم: صحيح (البخاري) · المصدر: الدرر السنية`

   Rules for the pieces:
   - `Sahih al-Bukhari` = `book`. `<n>` = `number`.
   - `sahih` = the `grade`. Map `صحيح` or `sahih` to "sahih" (English) or "صحيح" (Arabic). Any other grade: **do not render the card.** The backend only serves `صحيح`; the UI refuses anything else as a second guard.
   - `(al-Bukhari)` = the `grader`. Map `البخاري` to "al-Bukhari" and `مسلم` to "Muslim" in English. Any other grader: show it as stored.
   - `الدرر السنية` = the display name of `source_site`: dorar.net is "الدرر السنية" and shamela.ws is "المكتبة الشاملة", in both languages.
   - Separator is " · " (middle dot), each piece in its own `<bdi>` so mixed directions do not scramble.
5. If `english_text`: the text, then the translation line (section 1.5).
6. Explanation block, if any.
7. Reviewed line (as in the verse card).
8. The open-source link: "View on الدرر السنية (dorar.net)".

### 1.5 Translation lines

A translation line appears directly under any `english_text`. Rules:
- No `translation_name` means no English text is rendered. This mirrors the `clean()` rule in task 01.
- Verse: `Translation: {translation_name} via Quranpedia` when `source_site` is quranpedia.net. Example: "Translation: Saheeh International via Quranpedia". Arabic UI: "الترجمة: {translation_name} عبر Quranpedia".
- Hadith from HadeethEnc: `Translation: HadeethEnc.com #<id>`, where `<id>` is the last numeric path segment of `translation_source_url` (a HadeethEnc page looks like `hadeethenc.com/<lang>/browse/hadith/<id>`). If no id can be parsed, show "Translation: HadeethEnc.com". Make the whole line a link to `translation_source_url`. Arabic UI: "الترجمة: HadeethEnc.com #<id>".
- Allowed hosts for `translation_source_url`: `hadeethenc.com`, `quranenc.com`, `quranpedia.net`. Add a separate `safeTranslationUrl()` to `safeUrl.js`. Any other host: show the translation name as plain text with no link.
- Never alter `english_text`. No trimming, no re-casing, no "fixing". HadeethEnc's terms forbid changes (r1 §2.7).

### 1.6 Recitation credit

Organiser ruling (2026-10-05): everyayah.com recitation is accepted "with the source name and link stated clearly". Directly under the play button, always, show the credit text from the payload and make "everyayah.com" a link to `audio_source_url`:

- English: `Recitation: Mahmoud Khalil Al-Husary, everyayah.com`
- Arabic: `التلاوة: محمود خليل الحصري، everyayah.com`

The backend now sends both strings (in the session language) in `audio_credit`, and the link in `audio_source_url` (`https://everyayah.com/`). The audio URL points at our own server or at the bank's everyayah.com URL (`https://everyayah.com/data/Husary_128kbps/SSSAAA.mp3`), so the UI cannot work the credit out from it. Keep a fallback constant `RECITATION_CREDIT` in `sourceLabels.js` with the same two strings and `https://everyayah.com/`, used only when a card has audio but an empty `audio_credit`. Never show a verse's audio button without the credit line and its link. A card with verse `segments` that play audio (FAQ, tafsir) shows the credit once per card. Verses are played as recitation only, never read by TTS.

The existing button labels need Arabic too: "Listen to the recitation" / استمع إلى التلاوة, "Playing recitation" / جارٍ تشغيل التلاوة, "Loading..." / جارٍ التحميل..., "Recitation unavailable" / التلاوة غير متاحة.

### 1.7 Tafsir card (separate from the verse card)

- It is its own `article`. It is never merged into the verse card and never uses the Quran font. The verse card (if shown) sits as a separate card; link them visually only by the `related` ids (an optional "About {surah}:{ayah}" pill).
- Header, exactly: **"Tafsir encyclopedia (al-Durar al-Saniyya) says:"** (Arabic: "موسوعة التفسير (الدرر السنية) تقول:").
- Body: `arabic_text`, the verbatim excerpt, in the regular Arabic reading font, with a different surface from the verse card so the exegete's words cannot be mistaken for the verse (package p.3).
- Below: `book` and `number` ("S:A-B") as the citation line, then the explanation block, then the open-source link ("View on dorar.net").
- Early-book tafsir (not dorar): header "{book} says:".

### 1.8 Other types (P1)

faq, term, aqidah, fiqh, sirah use the generic excerpt layout: header from the table in 1.2, the `title` (the question or term), the verbatim `arabic_text` (and `english_text` plus translation line if present, for example a term with "Al-Jamhara (en)"), the explanation block, the open-source link. Extra rules:
- fiqh: always add the line "General information, not a ruling. Ask your parents or a scholar." / "معلومات عامة وليست فتوى. اسأل والديك أو أحد أهل العلم."
- content_level C (any type): show `disagreement_note` under the label "Scholars may differ:" / "قد يختلف العلماء:". If `content_level` is C and `disagreement_note` is empty, do not render the card.

If time runs out, ship verse, hadith and tafsir, and drop the other types. Do not ship a type without its labels.

## 2. The `reference` event payload

Topic `reference`, one JSON object per served item. This is the proposed contract with task 03; field names follow the existing mock and the model fields. `normalizeReference()` must whitelist exactly these keys (add the new ones to `KEYS`) and drop everything else.

| Field | Type | Notes |
|---|---|---|
| `id` | string or number | Stable item id. Required. |
| `type` | string | `verse`, `hadith`, `tafsir`, `faq`, `term`, `aqidah`, `fiqh`, `sirah`. Required. |
| `kind` | string | `scripture` (verse, hadith) or `source_excerpt` (every other type). Required. The UI drops a card whose `kind` does not match its `type`. |
| `arabic_text` | string | The verbatim text, copied from the cited page. Required. Never edited by the UI. For an item with `{{verse:S:A}}` markers (FAQ), each marker is already replaced by the localized reference, for example `(سورة الحجرات 49:12)`: a plain-text fallback with no braces. `english_text`, `title`, `explanation` and `disagreement_note` get the same treatment (reference in the field's language). |
| `english_text` | string | Optional. Only with `translation_name`. |
| `translation_name` | string | "Saheeh International", "HadeethEnc.com", "Al-Jamhara (en)". |
| `translation_source_url` | string | The translation's own link (HadeethEnc, QuranEnc, Quranpedia). Optional. A hadith card shows it next to `source_url` (dorar.net, the Arabic source), so both links are visible (organiser ruling 2026-10-05). |
| `surah`, `ayah` | number | Verse only. Validated against `HAFS_AYAH_COUNTS` as today. |
| `surah_name` | string | Optional Arabic name. |
| `audio_url` | string | Verse only. Same-origin or https. |
| `audio_credit` | string | The recitation credit text, in the session language: reciter name plus "everyayah.com". Non-empty whenever the card (or one of its verse `segments`) has everyayah.com audio. Show it under the play button. |
| `audio_source_url` | string | New, additive. The recitation source link, `https://everyayah.com/`. Empty when `audio_credit` is empty. Render "everyayah.com" in the credit as a link to it (`safeSourceUrl()` host list must allow `everyayah.com`). |
| `book`, `number` | string | Hadith: required. Tafsir: `book` and `number` ("S:A-B"). |
| `grade`, `grader` | string | Hadith: required. `grade` must be `صحيح`. |
| `source_site`, `source_url` | string | Required. `source_url` host must pass `safeSourceUrl()`. |
| `content_level` | string | `A`, `B` or `C`. |
| `value` | string | The value's name in the session language, for the pill. |
| `title` | string | Non-verse types: the question, term or topic. Optional. |
| `explanation` | string | Our child explanation, already chosen for the child's age band. Optional. |
| `explanation_lang` | string | `ar` or `en`. |
| `explanation_origin` | string | `generated`. The UI ignores the value but must never render `explanation` without the header "In simple words, for children (our explanation, not the source's words):". |
| `disagreement_note` | string | Required for level C. |
| `verification_status` | string | `seeded` or `reviewed`. Only `reviewed` shows the "checked by our team" line. |
| `verse_refs` | string[] | `"S:A"` for every `{{verse:S:A}}` marker in the item's `arabic_text` (FAQ items: the source PDF drew a verse there). A list of references only; use `segments` to render. |
| `segments` | object[] | `[]` when `arabic_text` has no marker. Otherwise the ordered rendering of `arabic_text`, text and verse segments (section 2.1). |

### 2.1 Verse markers and `segments` (FAQ items, possibly tafsir and aqidah)

The source PDF of some items drew a verse as glyphs. The bank stores a machine marker `{{verse:S:A}}` there, and only when `S:A` is a servable bank verse (seeded or reviewed). The backend resolves the marker before the event is sent:

- **No payload field ever holds a raw marker or a brace.** The LLM and the TTS never receive one either (`format_sources_block`, the output filter in `scripture_guard.py`).
- **An item whose marker has no servable bank verse is not served at all.** It is excluded when the session's index is built, with a logged warning. The UI never sees such an item.
- **`segments`** is the structured rendering of `arabic_text`, in reading order. Each entry is one of:

```json
{"type": "text", "text": "..."}
{"type": "verse", "surah": 49, "ayah": 12, "ref": "49:12", "item_key": "verse:49:12",
 "id": 123, "surah_name": "الحجرات", "audio_url": "https://..."}
```

The values above are placeholders. Rules for the web `SourceCard` and the mobile card:

1. If `segments` is non-empty, render `segments` instead of `arabic_text`, in order, in the same reading font and `dir="rtl" lang="ar"` block as the rest of the excerpt. If it is empty, render `arabic_text` as before.
2. A **text segment** is a plain text node (no HTML), keeping its spaces.
3. A **verse segment** is a small inline **reference chip** plus a **play button**:
   - chip label: "سورة {surah_name} : {ayah}" (Arabic UI) or "Surah {surah}:{ayah}" (English UI), built from `surah`, `ayah` and `surah_name`. Never from `ref` text typed by us, never any verse text.
   - the play button plays `audio_url` (the bank recitation), with the recitation credit of section 1.6 once per card. If `audio_url` is empty, show the chip with no play button.
   - the verse text itself is **not** in the segment and not shown inline. If the verse also arrives as its own verse card (same `id`), the chip may scroll to it.
   - the verse is never read by TTS or synthesised: it is audio from the bank only.
4. **Never render braces.** If a client receives a verse segment it cannot render (unknown `type`, bad `surah` or `ayah`, no `audio_url` host it accepts), drop that segment; it must not fall back to a raw marker, because there is none. Drop the whole card only if `arabic_text` is empty.
5. `verse_refs` is a convenience list (for the parent sources view and for tests). Do not use it to render.

Parent sources (`_snapshot_item`) apply `replace_verse_markers`; `arabic_text`/`english_text` there are the plain-text fallback, no `segments`. Snapshots stored before this change keep raw text (no marker items are seeded yet).

Allowed `source_url` hosts by type (extend `safeUrl.js`; keep the existing subdomain-safe check):

| Type | Hosts |
|---|---|
| verse | quranpedia.net, qurancomplex.gov.sa |
| hadith | dorar.net, shamela.ws |
| tafsir, aqidah, fiqh, sirah | dorar.net, shamela.ws (tafsir also quranpedia.net) |
| faq | dawa.center |
| term | islamic-content.com |

hadeethenc.com is never a hadith `source_url`: dorar.net is the primary Arabic source and HadeethEnc is the English translation, shown with its own link (`translation_source_url`). The organisers accepted this on 2026-10-05, so a hadith card shows both links.

## 3. Quran font and display (r4 §3 and §6)

- **Font:** the King Fahd Complex (KFGQPC) Hafs font, the **unmodified TTF**. The Complex's licence (embedded in the font) allows use, copy and distribute, and forbids modifying or reproducing it. So: no woff2 conversion, no subsetting, no recompression, until the organisers say yes (plan question 10). Self-host the TTF as downloaded from `fonts.qurancomplex.gov.sa`. The lead downloads it, because the cloud container cannot reach that host. Load it with `font-display: swap`.
- **Version pairing:** ship the TTF from the same release as the pinned text (plan §5.2, step 1). The v18 font draws only the legacy open-tanween code points, the v3.0 font draws both. Ask the lead which release is pinned before you pick the file.
- **Fallback:** Amiri Quran. Amiri Quran draws empty boxes or wrong marks for the legacy code points. So, **at display time only**, map `U+0657` to `U+08F0`, `U+065E` to `U+08F1` and `U+0656` to `U+08F2`. Put this in a pure function `toDisplayArabic(text, usingFallbackFont)` in a new `quranText.js`.
  - The stored and received text is never changed. Do not apply the mapping to copy-to-clipboard or to anything sent back to the server.
  - Detect the fallback with `document.fonts.load('28px "KFGQPC Hafs"')`: if it rejects or does not load in 3 seconds, set a flag and use the fallback stack.
- **Size and layout:** at least **28px** for the verse text, line height about 2.2, `lang="ar" dir="rtl"`. Do not justify, do not add letter spacing, do not truncate or line-clamp, do not split or reflow the text (waqf signs sit inside words). Let the card scroll if a verse is long.
- **Ayah numbers:** never store them inside `arabic_text`. The number is shown on its own line ("سورة {name} : {ayah}"). If you want the end-of-ayah ornament, append `U+06DD` and the Arabic-Indic digits at render time only.
- **Other Arabic text** (hadith, tafsir, FAQ, terms): a normal reading font (Amiri regular or Noto Naskh Arabic), not the Quran font.
- Test the font with the real bank data at runtime. In code, tests and mocks use placeholder strings only. A test for the mapping function can use the three code points on their own, with no scripture.

## 4. AI disclosure on the conversation screen

### 4.1 The permanent AI chip

- In the header of `ConversationPage.jsx`, always visible in every state (connecting, connected, ended) and both modes (chat and voice). It must not scroll away or be hideable.
- A button with the visible text **"AI"**. Minimum target size as the other controls (`min-h-target`). `aria-label`: "Sadiq is an AI. Tap to learn more." / "الصديق ذكاء اصطناعي. اضغط لمعرفة المزيد".
- It opens the info sheet (4.2). Reuse `useDialogFocus` from `features/auth/` for focus trapping. Escape closes it, and focus returns to the chip.

### 4.2 The info sheet (`AiInfoSheet.jsx`)

Language: the child's language, with an EN/AR toggle inside the sheet. Keep sentences short, because the reader is 6 to 13.

| Part | English | Arabic |
|---|---|---|
| Title | Sadiq is an AI | الصديق ذكاء اصطناعي |
| Line 1 | I am Sadiq, an AI friend. I am not a real person. | أنا الصديق، ذكاء اصطناعي ولست إنسانًا. |
| Line 2 | I can make mistakes. I am not a scholar and I do not give fatwas. | قد أخطئ. لست عالمًا ولا أُصدر فتاوى. |
| Line 3 | When I show a verse or a hadith, it comes from a trusted source. The card tells you where. | حين أعرض آية أو حديثًا فهو من مصدر موثوق، والبطاقة تبيّن لك مصدره. |
| Line 4 | The part called "In simple words" is my own explanation. Ask your parents or a teacher about anything important. | جزء «بكلمات بسيطة» شرحٌ مني أنا. اسأل والديك أو معلّمك عن كل أمر مهم. |
| Line 5 | Your parents can see short summaries of our chats. | يرى والداك ملخصات قصيرة عن حديثنا. |
| Button | Got it | فهمت |
| Link | Privacy information | معلومات الخصوصية |

Keep line 5 only if task 04's removal of the raw message `preview` has merged; otherwise drop the line (it must be true).
The "Privacy information" link goes to `/privacy`.

### 4.3 Registration and Terms

- **Registration step 1:** under the step title, add one notice line.
  - English: "Al-Sadiq is an AI companion. It is not a person and not a scholar. It can make mistakes and it does not give fatwas."
  - Arabic: "الصديق الصدوق رفيق يعمل بالذكاء الاصطناعي، وليس إنسانًا ولا عالِمًا. قد يخطئ ولا يُصدر فتاوى."
  - Followed by a link: "How we handle data" / "كيف نتعامل مع البيانات" → `/privacy`.
- **Registration step 3:** the terms checkbox label keeps its Terms link, and gets a second link to `/privacy` ("Privacy policy" / "سياسة الخصوصية").
- **Terms modal:** add clause 11 and change clause 3's "described in our Privacy Policy" to a link to `/privacy`.
  - English: "11. AI Companion. Al-Sadiq is an AI tool. It is not a person, not a scholar and not a source of fatwas. Verses and hadith shown on a source card come from approved sources. Explanations are AI-generated and simplified, so they can contain mistakes. Parents should ask a qualified scholar about important religious matters. By accepting these terms you confirm that you understand this."
  - Arabic: "11. الرفيق الذكي. الصديق الصدوق أداة تعمل بالذكاء الاصطناعي، وليس إنسانًا ولا عالمًا ولا مصدرًا للفتوى. الآيات والأحاديث المعروضة في بطاقة المصدر مأخوذة من مصادر معتمدة. أما الشروحات فيولّدها الذكاء الاصطناعي بصورة مبسّطة، وقد تحتوي على أخطاء. على أولياء الأمور سؤال عالم مؤهل في الأمور الدينية المهمة. بقبولك هذه الشروط تقرّ بأنك فهمت ذلك."

The web app has no i18n library today (mobile uses `i18next`). Ship these strings in small `{ en, ar }` objects (`sourceLabels.js`, `aiStrings.js`) and pick by language; do not add a library for this. The rest of the UI can stay English (stretch goal in the task file); only the new pieces must exist in Arabic (r5 K1).

## 5. The `/privacy` page

- New public route `ROUTES.PRIVACY = '/privacy'`, added in `routes.js` and `App.jsx` **outside every guard**, next to the reset-password route ("always accessible"). The register page is inside `GuestRoute`, so a guard would bounce logged-in parents.
- New `frontend/src/pages/Privacy.jsx`. Content: the English and Arabic text of `docs/hackathon/privacy-policy-draft.md`, as `{ en, ar }` data with an EN/AR toggle (default to the browser language; `dir="rtl"` for Arabic). Sections as headings, the processor and retention tables as real tables with captions, readable on a phone.
- **Placeholders:** the draft contains `[brackets]`. Do not ship while any bracket is left. Ask the lead for the retention number N (r5 H5 suggests 90 days for flagged messages), the contact, and the confirmations listed at the end of the draft. Until the team's legal check is done, show a small line at the top: "Draft, pending legal review" / "مسودة بانتظار المراجعة القانونية".
- **Links to `/privacy`** (all five are required):
  1. Registration step 1 (the notice, 4.3).
  2. Registration step 3, next to the terms checkbox.
  3. Child `SettingsPage.jsx` and parent `SettingsPage.jsx`, a "Privacy" row.
  4. The Login footer.
  5. The AI info sheet.
- Links open in the same tab for settings and login; in a new tab (`rel="noopener noreferrer"`) from the registration form, so a half-filled form is not lost.

## 6. Acceptance checks

Extend `frontend/scripts/check-source-cards.mjs` for 1 to 6 (pure functions: `normalizeReference`, the label builders, `toDisplayArabic`). Do 7 to 10 by hand and keep screenshots for the submission (task 10).

1. **Verse card:** shows "From the Quran:", the Arabic at a computed font size of 28px or more, "Translation: Saheeh International via Quranpedia", the caption "Text: King Fahd Complex (KFGQPC), via Quranpedia", and under the play button exactly "Recitation: Mahmoud Khalil al-Husary, via everyayah.com".
2. **Two tiers:** a payload with `explanation` shows a separate block headed exactly "In simple words, for children (our explanation, not the source's words):", after the source block in the DOM. A payload without `explanation` shows no such header. Nothing from `explanation` appears inside the quote block.
3. **Hadith card:** the citation line equals `Sahih al-Bukhari <n> · graded sahih (al-Bukhari) · source: الدرر السنية` for a dorar payload. A hadith payload with `grade` other than `صحيح`, or missing book, number, grader or source_url, renders no card.
4. **Translation rule:** `english_text` with no `translation_name` renders no English. A HadeethEnc payload renders "Translation: HadeethEnc.com #<id>" as a link to `translation_source_url`. A `translation_source_url` on any other host renders no link.
5. **Tafsir card:** a tafsir payload renders its own card headed exactly "Tafsir encyclopedia (al-Durar al-Saniyya) says:", not in the Quran font, and no verse card appears unless a verse payload also arrived.
6. **Fallback font:** `toDisplayArabic('ٖٗٞ', true)` returns `ࣰࣱࣲ`, and with `false` it returns the input unchanged. The payload object is never mutated.
7. **Fallback in the browser:** block the TTF request in DevTools. The verse still renders in Amiri Quran with no empty boxes (check with the real bank data, including a verse with open tanween).
8. **AI chip:** visible on `/child` in connecting, connected and ended states, in chat mode and voice mode. Tab reaches it, Enter opens the sheet, Escape closes it, focus returns. The sheet reads correctly in Arabic (RTL).
9. **Registration and Terms:** step 1 shows the AI notice, the Terms modal has clause 11, and `/privacy` opens from all five places in section 5, logged out and logged in.
10. **Privacy page:** both languages render, the processor and retention tables are present, and no `[` placeholder remains in the visible text.
11. **Verse markers:** a payload with `segments` renders the text, then a reference chip and a play button per verse segment, in order, and the DOM text contains no `{` or `}`. A payload with no `segments` renders `arabic_text` unchanged. A verse segment with an empty `audio_url` shows the chip without a play button. Add to `check-source-cards.mjs`: a pure `segmentsToParts(payload)` (or equivalent) tested on a placeholder payload.

Also: `npm run lint && npm run build` passes, and every mock payload is placeholder text (a grep of `src/` for Arabic runs containing Quranic marks U+06D6 to U+06ED must find nothing).

## 7. Not in this handoff

- The consent record (`terms_version` and `consented_at`, r5 H4) is a backend task for 04. When the backend field exists, send it from the registration form.
- Mobile parity is in `handoffs/mobile-ai-privacy.md`.
- The parent Insights wording (trust line, "Written by AI" label) is in `handoffs/04-parent-trust.md`. It imports your `sourceLabels.js`, so create that file first and tell the 04 owner where it is.
