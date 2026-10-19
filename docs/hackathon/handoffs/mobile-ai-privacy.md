# Handoff to mobile: AI chip, privacy sheet, Arabic strings, source card parity

- **For:** whoever owns the Expo app (`mobile/`). Read `mobile/AGENTS.md` first: Expo SDK 56 has changed, so check https://docs.expo.dev/versions/v56.0.0/ before writing code.
- **Written by:** WP6 (documentation reconciliation), 5 Oct 2026, from `content-approach-plan.md` (§7.4, §7.5), `research/r5-compliance-gap.md` (G3, H3, K1, K2) and `handoffs/05-cards-ai-privacy.md` (the web spec; the wording is identical).
- **Priority:** P0 for the AI chip, the info sheet, the registration line and the Terms clause. P1 for the privacy sheet and Arabic strings. Source card parity comes later (section 5).
- **Plan slot:** Day 2, 14:00 (`mobile-dev` does "the chip and sheet").

The judges use the web version, but parents and children will use the phone app, and the AI disclosure and privacy rules apply there too (package p.5: transparency and privacy). Nothing below needs a backend change.

## 1. AI chip and info sheet (P0)

Files: `mobile/src/features/child/session/SessionScreen.jsx` (the chip), a new `mobile/src/features/child/session/AiInfoSheet.jsx` (the sheet, built on `components/Sheet.jsx` like `TermsSheet.jsx`).

- A permanent chip with the visible text **"AI"** in the session header. It stays visible in every state (connecting, connected, ended) and in both chat and voice mode. It cannot be hidden.
- Touch target at least 44 pt (the app uses 56 for primary targets). `accessibilityRole="button"`, `accessibilityLabel` from `session.aiChipLabel`.
- Tapping opens the info sheet. Its content is the same as the web (handoff 05, section 4.2). A "Got it" button closes it, and a "Privacy information" link opens the privacy sheet.
- **Nested modal warning:** `Sheet` is built on React Native `Modal`. On iOS, opening a second modal while the first is closing fails silently. Close the info sheet first, then open the privacy sheet in its `onDismiss` or after a short timeout (about 350 ms), and test it on a real iPhone.
- Keep line 5 of the sheet ("Your parents can see short summaries of our chats") only after task 04 has removed the raw message `preview`. Otherwise drop that line.

## 2. Registration line and Terms clause (P0)

- `mobile/src/features/auth/RegisterScreen.jsx`, step 1: add the notice under the step title, from `auth.aiNotice`, followed by a link `auth.privacyLink` that opens the privacy sheet.
- `mobile/src/features/auth/TermsSheet.jsx`: the `TERMS` array is hard-coded English ("the same 10 clauses as the web Register terms modal"). Add clause 11 (below) and change clause 3 so it points to the privacy sheet. Keep it identical to the web modal, which gets the same change (handoff 05, section 4.3). Moving the clauses into i18n keys is welcome but not required.

## 3. Privacy sheet (P1)

- New `mobile/src/features/auth/PrivacySheet.jsx` (beside `TermsSheet.jsx`, so both settings screens and the registration screen can import it), a `Sheet` with a `ScrollView`, like `TermsSheet`. Content is the final text of `docs/hackathon/privacy-policy-draft.md`, stored as `privacy.sections` (array of `{ heading, body }`, read with `t('privacy.sections', { returnObjects: true })`). The processor and retention tables become lists of short lines ("OpenAI: speech recognition, replies and reports").
- Reachable from: registration step 1 and step 3, the child `SettingsScreen.jsx`, the parent `SettingsScreen.jsx`, and the AI info sheet.
- Do not ship while a `[bracket]` placeholder from the draft is left in the text, and show "Draft, pending legal review" at the top until the team's legal check is done.
- Show Arabic text with `writingDirection: 'rtl'` and `textAlign: 'right'` when the language is `ar`.

## 4. Arabic strings (P1)

`mobile/src/i18n/locales/ar.json` is an empty stub (`{}`), and `en.json` has no AI or privacy keys. Add these to both files. The wording matches the web exactly. Language is chosen in the child and parent settings (`settings.language`); `fallbackLng` stays `en`, so a missing Arabic key shows English, never a blank.

```jsonc
// en.json (merge into the existing objects)
{
  "session": {
    "aiChip": "AI",
    "aiChipLabel": "Sadiq is an AI. Tap to learn more.",
    "aiSheetTitle": "Sadiq is an AI",
    "aiLine1": "I am Sadiq, an AI friend. I am not a real person.",
    "aiLine2": "I can make mistakes. I am not a scholar and I do not give fatwas.",
    "aiLine3": "When I show a verse or a hadith, it comes from a trusted source. The card tells you where.",
    "aiLine4": "The part called \"In simple words\" is my own explanation. Ask your parents or a teacher about anything important.",
    "aiLine5": "Your parents can see short summaries of our chats.",
    "aiGotIt": "Got it"
  },
  "auth": {
    "aiNotice": "Al-Sadiq is an AI companion. It is not a person and not a scholar. It can make mistakes and it does not give fatwas.",
    "privacyLink": "How we handle data",
    "termsAiTitle": "11. AI Companion",
    "termsAiBody": "Al-Sadiq is an AI tool. It is not a person, not a scholar and not a source of fatwas. Verses and hadith shown on a source card come from approved sources. Explanations are AI-generated and simplified, so they can contain mistakes. Parents should ask a qualified scholar about important religious matters. By accepting these terms you confirm that you understand this."
  },
  "privacy": {
    "title": "Privacy information",
    "draftNote": "Draft, pending legal review",
    "sections": []
  }
}
```

```jsonc
// ar.json
{
  "session": {
    "aiChip": "AI",
    "aiChipLabel": "الصديق ذكاء اصطناعي. اضغط لمعرفة المزيد",
    "aiSheetTitle": "الصديق ذكاء اصطناعي",
    "aiLine1": "أنا الصديق، ذكاء اصطناعي ولست إنسانًا.",
    "aiLine2": "قد أخطئ. لست عالمًا ولا أُصدر فتاوى.",
    "aiLine3": "حين أعرض آية أو حديثًا فهو من مصدر موثوق، والبطاقة تبيّن لك مصدره.",
    "aiLine4": "جزء «بكلمات بسيطة» شرحٌ مني أنا. اسأل والديك أو معلّمك عن كل أمر مهم.",
    "aiLine5": "يرى والداك ملخصات قصيرة عن حديثنا.",
    "aiGotIt": "فهمت"
  },
  "auth": {
    "aiNotice": "الصديق الصدوق رفيق يعمل بالذكاء الاصطناعي، وليس إنسانًا ولا عالِمًا. قد يخطئ ولا يُصدر فتاوى.",
    "privacyLink": "كيف نتعامل مع البيانات",
    "termsAiTitle": "11. الرفيق الذكي",
    "termsAiBody": "الصديق الصدوق أداة تعمل بالذكاء الاصطناعي، وليس إنسانًا ولا عالمًا ولا مصدرًا للفتوى. الآيات والأحاديث المعروضة في بطاقة المصدر مأخوذة من مصادر معتمدة. أما الشروحات فيولّدها الذكاء الاصطناعي بصورة مبسّطة، وقد تحتوي على أخطاء. على أولياء الأمور سؤال عالم مؤهل في الأمور الدينية المهمة. بقبولك هذه الشروط تقرّ بأنك فهمت ذلك."
  },
  "privacy": {
    "title": "معلومات الخصوصية",
    "draftNote": "مسودة بانتظار المراجعة القانونية",
    "sections": []
  }
}
```

(The `//` comment lines above are for reading only; the real files are plain JSON.)

Notes:
- Fill `privacy.sections` in both files from the final privacy text. Section headings and bodies are in `docs/hackathon/privacy-policy-draft.md`, English and Arabic.
- Keep the parent-facing labels from `handoffs/04-parent-trust.md` (trust line, "Written by AI ...", the "reviewed" line) as keys too when you build the mobile Insights section.
- Keep layouts on start/end styles (`i18n/index.js` already says so). You do not need to force a global RTL layout for the hackathon; the Arabic text blocks above set their own direction.
- Add a jest test (`cd mobile && npm test`) that every key under `session.ai*`, `auth.aiNotice`, `auth.privacyLink`, `auth.termsAi*` and `privacy.*` exists in both `en.json` and `ar.json`.

## 5. Source card parity (later, P1)

Mobile has no source card today, and `mobile/src/hooks/useLiveKitSession.js` (about lines 109 to 110) listens only to the `gamification` topic. So on a phone a child hears "let's listen" and nothing is shown or played (r5 K2). Until parity lands, say so in the submission as a known limitation. When you build it:

- Subscribe to the `reference` topic and keep the last 3 cards, with the same payload and the same validation as the web (`handoffs/05-cards-ai-privacy.md`, sections 1 and 2): `kind`, the two tiers ("From <source>:" and "In simple words, for children (our explanation, not the source's words):"), the hadith citation line, the translation line, the separate tafsir card, the recitation credit from the payload (`audio_credit`, with `audio_source_url` as its link: "Recitation: Mahmoud Khalil Al-Husary, everyayah.com"), and both hadith links (`source_url` and `translation_source_url`). Port `normalizeReference` by copying it; there is no shared package.
- Quran font: bundle the unmodified KFGQPC TTF with `expo-font`, the same release as the pinned text. Fallback Amiri Quran with the display-time mapping `U+0657` to `U+08F0`, `U+065E` to `U+08F1`, `U+0656` to `U+08F2`; size 28 or larger; never store ayah numbers in the text. Test on one Android and one iOS device (r4 §7, step 9).
- Audio: play the verse `audio_url` as recitation only, never TTS. Use the audio library that the SDK 56 docs recommend.
- Open source links with `Linking.openURL`, after the same host allow-list as the web.

## 6. Acceptance checks

1. The AI chip is visible in the session header while connecting, connected and ended, in chat and voice mode, on iOS and Android. Tapping it opens the sheet with the five lines and a working "Got it".
2. Switching the language to Arabic shows the sheet, the registration notice and the Terms clause 11 in Arabic, with right-to-left text. Switching to English shows them in English. No key shows its raw name.
3. Registration step 1 shows the AI notice and a link that opens the privacy sheet. The Terms sheet has clause 11.
4. The privacy sheet opens from registration, both settings screens and the AI info sheet, including the iOS nested-sheet case, and contains no `[bracket]` text.
5. `cd mobile && npm test` passes, including the key-parity test.
