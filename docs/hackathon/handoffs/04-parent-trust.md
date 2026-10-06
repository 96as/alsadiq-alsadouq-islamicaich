# Handoff to task 04 (parent sources): trust wording, AI labels, no transcripts

- **For:** the owner of task 04 (`hk/04-parent-sources`).
- **Written by:** WP6 (documentation reconciliation), 5 Oct 2026, from `content-approach-plan.md` (§7.4, §7.5), `research/r5-compliance-gap.md` (A6, G5, H2, H6, H7, J1 to J5, D7, D8) and `tasks/04-parent-sources.md`.
- **Priority:** P0 for items 1, 2, 4 and 6. P1 for items 3 and 5 (they depend on task 03's `TurnAudit`).
- **Why:** parents are the trust audience. Today the dashboard shows unlabelled LLM text, an absolute claim about sources, and the first 120 characters of the child's last message. The hackathon standard (package p.5) requires source traceability, a clear split between source text and generated explanation, AI disclosure, and privacy.

This file changes the wording in `tasks/04-parent-sources.md`. Where the two differ, this file wins.

## 1. The trust line (replaces the one in the task file)

Show it once, directly above the sources cards on the Insights page.

- English: **Verses and hadith shown on a source card come from approved sources; explanations are AI-generated and simplified.**
- Arabic: **الآيات والأحاديث المعروضة في بطاقات المصدر مأخوذة من مصادر معتمدة، أما الشروح فيولّدها الذكاء الاصطناعي بصورة مبسّطة.**

Do not use the old wording ("Every verse and hadith Al-Sadiq uses comes from approved sources: ..."). It is an absolute claim. The model can still speak freely outside a card, so only cited cards can be called sourced. Do not list the approved sources in the line; the card names its own source.

## 2. Label the weekly summary as AI-written

Directly above the summary text on `InsightsPage.jsx` (and on the mobile `InsightsScreen.jsx` if you build it), visible text, 14px or larger, not a tooltip:

- English: **Written by AI from the week's sessions; may contain mistakes**
- Arabic: **كُتب بواسطة الذكاء الاصطناعي من جلسات الأسبوع، وقد يحتوي على أخطاء**

Apply the same label to any per-session summary shown to the parent, and to the "suggested topics" list ("Suggested by AI" / "اقتراحات من الذكاء الاصطناعي").

## 3. What "reviewed" means

The bank marks items `reviewed` after one team member compares the text with its source page. No scholar signs off (r5 A6). Say so wherever "reviewed" can be read by a parent.

- On a source card in the parent view, a `reviewed` item shows: **"Checked against the source by our team"** (Arabic: **طابقه فريقنا مع المصدر**). The title text or footnote adds: **"Not reviewed by a scholar"** (Arabic: **لم يراجعه عالم**).
- In the footer of the sources section, one line: **"Reviewed means checked against the source by our team, not reviewed by a scholar."** (Arabic: **«مُراجَع» يعني أن فريقنا طابقه مع المصدر، ولا يعني أن عالمًا راجعه.**)
- Never use "verified by scholars", "approved" or "authentic" for the review state. A hadith's grade ("graded sahih (al-Bukhari)") is the grader's grade, not ours; show it as such.
- Items that are only `seeded` (verses fetched by script) show no review line.

## 4. No raw transcripts reach the parent

This is the privacy fix already in the task file (`ParentSessionSummarySerializer.preview`), tightened:

- Remove `preview` from `backend/conversation/serializers.py` (lines about 173 to 180), or replace it with the session report's summary. No field may carry the first characters of a child message.
- Remove its use in `frontend/src/pages/parent/ChildConversationSummaryPage.jsx` (about lines 114 to 115) and `mobile/src/features/parent/children/ChildSummaryScreen.jsx` (about lines 71 to 73).
- Grep every parent-facing serializer and view for fields that read `Message.content` and confirm none returns it. Alerts: show the category and a neutral description, not the child's words (check what `Alert` stores).
- Test: the parent API response for a session contains none of the child's message text (use a unique marker string in a test message and assert it is absent from the whole JSON body).
- The privacy page and the child's AI info sheet say parents see summaries, not conversations. Keep that true.

## 5. "Questions to discuss" list

A short list on Insights: "Questions Sadiq asked you to discuss" / "أسئلة طلب منك الصديق مناقشتها مع طفلك". It comes from task 03's `TurnAudit` rows (level, mode, topic label, no text). Skip this item (hide the section) if `TurnAudit` is not merged.

- **Include** rows whose mode is REFER, DISAGREE_AND_REFER or DECLINE_NO_SOURCE (the agent sent the child to a parent or teacher).
- **Exclude every safety-flagged item.** Family-dispute or harm patterns (fighting, divorce, hitting, fear at home) go through the existing `flag_safety_concern` flow and the alert path. They are never listed here, never shown with a topic label, and the child is referred to "a trusted adult or a teacher" (plan §7.2). Agree with the 03 owner how `TurnAudit` marks these turns (a safety boolean, or a separate mode value); the field is not defined in the plan yet. Filter on that marker, and as a second guard drop any row from a session that has a `SafetyFlag` or `Alert` raised in the same turn window. Test with one flagged and one unflagged row.
- Show only the topic label (a value name or a fixed topic such as "fasting"), the date, and the level in plain words ("a question about your family's own situation", "scholars differ on the details"). No text from the child.
- Cap the list at the latest 5 for the week.

## 6. `sources_used` comes from `ServedReference`, not from the LLM

- In `post_session_pipeline`, read `ServedReference` rows for the session and store `sources_used` as item ids plus snapshot fields. The report's LLM output must not contain or alter the sources; the sources come from the database only.
- Snapshot fields: `id`, `type`, `kind`, `arabic_text`, `english_text`, `translation_name`, `translation_source_url`, `surah`, `ayah`, `book`, `number`, `grade`, `grader`, `source_site`, `source_url`, `content_level`, `title`, `disagreement_note`, `verification_status`, `value_name`, `times_discussed`. The snapshot keeps the report correct if an item is edited later.
- Insights API: `sources[]` is this week's unique items. Do not include the child explanation text (it is the child's tier); parents see the source text, citation and links.
- Card wording reuses the child card labels from `handoffs/05-cards-ai-privacy.md` (section 1): "From <source>:", the hadith citation line "Sahih al-Bukhari <n> · graded sahih (al-Bukhari) · source: الدرر السنية", "Translation: HadeethEnc.com #<id>" or "Saheeh International via Quranpedia", and the separate tafsir card "Tafsir encyclopedia (al-Durar al-Saniyya) says:". Import the 05 owner's `sourceLabels.js` when it exists; until then copy the strings, do not reword them.
- A report with no sources still works and shows "No sources were used this week" / "لم تُستخدم مصادر هذا الأسبوع".

## 7. Related P0 work already assigned to 04 (do not drop)

- **No religious conclusions about the child (r5 H2):** add to all four reporting prompts: never infer, rate or describe belief, piety, prayer habits or the family's religious practice. Record religion-related content only as a neutral topic the child raised. Keep family religious practice out of memory facts. The privacy policy promises this, so it must be true before launch.
- **No scripture or rulings in generated parent text (r5 J1):** the weekly summary and suggested topics contain no verse, no hadith, no ruling. Islamic framing only by naming values that appear in `sources_used`. Add a post-filter that rejects output containing scripture markers (﴿ ﴾, the dense Quranic marks U+06D6 to U+06ED, "قال تعالى", "قال رسول الله", "the Prophet said") and falls back to a plain summary.
- **Memory (r5 D7):** the rolling memory keeps only facts the child stated, never religious claims made by the companion.
- **Quests (r5 D8):** the quest prompt adds no scripture and no attributed ruling.
- **Honesty score (r5 H7, lead decision 8):** keep it internal and never show it on any parent or child screen, or drop it. Do not show it in this dashboard either way.

## 8. Acceptance checks

1. The Insights page shows the trust line exactly as in section 1, in English and Arabic, and the old wording appears nowhere (`grep -r "Every verse and hadith"` finds nothing).
2. The weekly summary has the visible AI label from section 2.
3. A `reviewed` card shows "Checked against the source by our team" and the sources footer has the "not reviewed by a scholar" line; no screen says "verified by scholars".
4. A test session with a unique marker string produces a parent API response without that string anywhere, and no screen shows a message preview.
5. With one flagged and one unflagged `TurnAudit` row, "Questions to discuss" lists only the unflagged one, and shows no child text.
6. After a test session about honesty, `sources[]` matches the `ServedReference` rows (compare ids), and the report's `sources_used` was not written by the LLM.
7. A summary generated from a transcript that contains a Quranic phrase is rejected by the post-filter and replaced by the plain fallback.
8. Backend tests pass (`cd backend && python3 manage.py test --settings=config.settings_sqlite_test`) and `npm run lint && npm run build` pass.

## 9. Update to your task file

Replace the trust-line bullet in `tasks/04-parent-sources.md` ("Every verse and hadith Al-Sadiq uses comes from approved sources: ...") with the wording in section 1, and add the AI label, the "reviewed" line and the "Questions to discuss" list to the Steps. Do not tick any checkbox on someone else's behalf.

## 10. Final backend API shape (WP11, `GET /api/reporting/insights/<child_id>/`)

All new keys are database-only (`ServedReference`, `TurnAudit`); no child text, no LLM output. Existing keys are unchanged.

```json
{
  "sources": [
    {
      "id": 12, "type": "hadith", "kind": "scripture",
      "arabic_text": "...", "english_text": "...",
      "translation_name": "...", "translation_source_url": "https://...",
      "surah": null, "ayah": null,
      "book": "...", "number": "1", "grade": "sahih", "grader": "...",
      "source_site": "dorar.net", "source_url": "https://dorar.net/...",
      "content_level": "A", "title": "", "disagreement_note": "",
      "verification_status": "reviewed",
      "value_name": "Honesty", "value_names": ["Honesty"],
      "times_discussed": 2
    }
  ],
  "questions_to_discuss": [
    {
      "topic": "honesty", "topic_en": "Honesty", "topic_ar": "الصدق",
      "mode": "REFER", "level": "D",
      "description_en": "a question about your family's own situation",
      "description_ar": "سؤال عن وضع أسرتك الخاص",
      "date": "2026-10-05", "count": 2
    }
  ],
  "trust_line": {"en": "...", "ar": "..."},
  "summary_label": {"en": "...", "ar": "..."},
  "labels": {
    "suggested_topics": {"en": "...", "ar": "..."},
    "reviewed": {"en": "...", "ar": "..."},
    "not_scholar_reviewed": {"en": "...", "ar": "..."},
    "sources_footer": {"en": "...", "ar": "..."},
    "no_sources": {"en": "...", "ar": "..."},
    "questions_title": {"en": "...", "ar": "..."}
  }
}
```

Notes for web and mobile:
- Show every string from the response (`trust_line`, `summary_label`, `labels.*`) instead of hard-coding it, so both clients match.
- `kind` is `scripture` (verse, hadith) or `source_excerpt` (all other types). Child explanations are never included.
- `sources` is this week (Monday start, server local date), deduped by item id, sorted by `times_discussed` descending. An entry is kept only if its snapshot status is `reviewed`, or it is `seeded` and still servable; an item that is `unverified` now or at snapshot time is dropped.
- `questions_to_discuss`: latest 5 topic groups, grouped by value (`topic` is empty and names are empty when no value is linked; show `description_*` only). Rows with `safety=True`, mode `SAFETY`, and every row of a session with a safety Alert or SafetyFlag are excluded. Hide the section when the list is empty.
- `sources_used` is stored on `SessionReport` by `post_session_pipeline` (migration `reporting/0006`); it is written from the database after the LLM output and overrides anything the LLM returned.

`values_this_week` is `[{slug, name_en, name_ar, count}]` (or `[]`), sorted by count descending, then slug ascending; names come only from the bank.
`count` combines this week’s accepted source snapshots weighted by `times_discussed`, known `values_to_revisit` slugs once per report, and quests completed this week once each (Monday start, server local date).
Web/mobile show `labels.values_this_week` (`{"en": "Values this week", "ar": "قيم هذا الأسبوع"}`); these are neutral topic counts, with no child message text or assessment of religious practice.
