// cards-spec (05) section 4: the AI disclosure strings, exactly as the spec words them. { en, ar } objects, no i18n library.
// Pure data, no React.

export const AI_STRINGS = {
  en: {
    chipText: 'AI',
    chipLabel: 'Al-Sadiq is an AI. Tap to learn more.',
    title: 'Al-Sadiq is an AI',
    line1: 'I am Al-Sadiq, an AI friend. I am not a real person.',
    line2: 'I can make mistakes. I am not a scholar and I do not give fatwas.',
    line3: 'When I show a verse or a hadith, it comes from a trusted source. The card tells you where.',
    line4: 'The part called "In simple words" is my own explanation. Ask your parents or a teacher about anything important.',
    line5: 'Your parents can see short summaries of our chats.',
    button: 'Got it',
    link: 'Privacy information',
    toggleTo: 'العربية',
    toggleLabel: 'Show this in Arabic',
  },
  ar: {
    chipText: 'AI',
    chipLabel: 'الصديق ذكاء اصطناعي. اضغط لمعرفة المزيد',
    title: 'الصديق ذكاء اصطناعي',
    line1: 'أنا الصديق، ذكاء اصطناعي ولست إنسانًا.',
    line2: 'قد أخطئ. لست عالمًا ولا أُصدر فتاوى.',
    line3: 'حين أعرض آية أو حديثًا فهو من مصدر موثوق، والبطاقة تبيّن لك مصدره.',
    line4: 'جزء «بكلمات بسيطة» شرحٌ مني أنا. اسأل والديك أو معلّمك عن كل أمر مهم.',
    line5: 'يرى والداك ملخصات قصيرة عن حديثنا.',
    button: 'فهمت',
    link: 'معلومات الخصوصية',
    toggleTo: 'English',
    toggleLabel: 'عرض هذا بالإنجليزية',
  },
};

/**
 * Line 5 says parents see short summaries. It is only true while the parent API sends no raw message text.
 * cards-spec (05) judge r2: true now. Since caa2d65 (merged with the knowledge bank) ParentSessionSummarySerializer
 * .get_preview returns '' and the parent alerts carry a description, not the child's words. check:cards asserts
 * the empty preview, so this line goes red if the raw preview ever comes back.
 */
export const SHOW_PARENT_SUMMARY_LINE = true;

/** Registration and Terms wording (section 4.3), same { en, ar } shape. */
export const REGISTRATION_STRINGS = {
  en: {
    notice: 'Al-Sadiq is an AI companion. It is not a person and not a scholar. It can make mistakes and it does not give fatwas.',
    dataLink: 'How we handle data',
    privacyPolicy: 'Privacy policy',
    terms11: '11. AI Companion. Al-Sadiq is an AI tool. It is not a person, not a scholar and not a source of fatwas. Verses and hadith shown on a source card come from approved sources. Explanations are AI-generated and simplified, so they can contain mistakes. Parents should ask a qualified scholar about important religious matters. By accepting these terms you confirm that you understand this.',
  },
  ar: {
    notice: 'الصديق الصدوق رفيق يعمل بالذكاء الاصطناعي، وليس إنسانًا ولا عالِمًا. قد يخطئ ولا يُصدر فتاوى.',
    dataLink: 'كيف نتعامل مع البيانات',
    privacyPolicy: 'سياسة الخصوصية',
    terms11: '11. الرفيق الذكي. الصديق الصدوق أداة تعمل بالذكاء الاصطناعي، وليس إنسانًا ولا عالمًا ولا مصدرًا للفتوى. الآيات والأحاديث المعروضة في بطاقة المصدر مأخوذة من مصادر معتمدة. أما الشروحات فيولّدها الذكاء الاصطناعي بصورة مبسّطة، وقد تحتوي على أخطاء. على أولياء الأمور سؤال عالم مؤهل في الأمور الدينية المهمة. بقبولك هذه الشروط تقرّ بأنك فهمت ذلك.',
  },
};

/** The privacy link label used on settings rows, the Login footer and the landing footer. */
export const PRIVACY_LINK = { en: 'Privacy', ar: 'الخصوصية' };
