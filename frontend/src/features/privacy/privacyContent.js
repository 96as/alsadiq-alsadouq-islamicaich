// cards-spec (05) section 5: the parent-facing privacy policy as { en, ar } data.
// Source: docs/hackathon/privacy-policy-draft.md (v0.1). English and Arabic must say the same thing; change both together.
// The draft's [bracket] blanks are written as plain "to be confirmed" sentences, because the page must show no bracket.
// Voice: ElevenLabs only (the draft's "xAI or ElevenLabs" row is reduced to the one provider in use).
// Block types: p (text), lead (bold lead-in + text), ul (items), table (caption, head, rows), lines (one per line).

export const LAST_UPDATED = '2026-10-05';

export const PRIVACY_CONTENT = {
  en: {
    dir: 'ltr',
    lang: 'en',
    title: 'Privacy policy: Al-Sadiq Al-Sadouq',
    subtitle: 'For parents',
    draft: 'Draft, pending legal review',
    switchTo: 'العربية',
    switchLabel: 'Show this page in Arabic',
    back: 'Back',
    sections: [
      {
        heading: '1. About this policy',
        blocks: [
          { t: 'p', text: 'Al-Sadiq Al-Sadouq is an app where children aged 6 to 13 talk with an AI companion called Al-Sadiq about Islamic values. A parent creates the account and the child\'s profile.' },
          { t: 'p', text: 'This policy tells you, the parent, what data we use and why. We wrote it in short, plain sentences on purpose.' },
        ],
      },
      {
        heading: '2. What the app is, and what it is not',
        blocks: [
          {
            t: 'ul',
            items: [
              'Al-Sadiq is an AI. It is not a person.',
              'Al-Sadiq is not a scholar. It does not give fatwas. It does not give rulings about your family\'s own situation. For those, please ask a qualified scholar.',
              'Al-Sadiq can make mistakes.',
              'When Al-Sadiq shows a verse or a hadith, it comes from an approved source, and the source card names it. The explanation next to it is written by AI in simple words.',
              'In our library, "reviewed" means our team checked the text against its source. It does not mean a scholar reviewed it.',
            ],
          },
        ],
      },
      {
        heading: '3. What data we collect',
        blocks: [
          { t: 'lead', lead: 'Parent account.', text: 'Your name and email address, and your phone number if you give one.' },
          { t: 'lead', lead: 'Child profile.', text: 'Your child\'s nickname, gender, birth year or age band, language, and when your child last used the app.' },
          { t: 'lead', lead: 'Conversations.', text: 'What your child says (speech is turned into text) and what Al-Sadiq replies.' },
          { t: 'lead', lead: 'Safety flags.', text: 'If a message suggests that a child may be in danger, or may hurt themselves or someone else, we mark it and send you an alert.' },
          { t: 'lead', lead: 'Reports.', text: 'After each session we make a short report. It has a summary, the topics, key moments, and facts your child told Al-Sadiq (for example a favourite subject). We also make a weekly summary for you. We keep a short running memory, so that Al-Sadiq can remember what your child shared.' },
          { t: 'lead', lead: 'Questions to discuss.', text: 'When Al-Sadiq asks your child to talk with you about a question, we keep the topic of the question. We do not keep the child\'s words for this list.' },
          { t: 'lead', lead: 'Technical data.', text: 'Our server logs record technical IDs. They do not record what your child says.' },
          { t: 'lead', lead: 'Voice recordings.', text: 'We do not keep recordings of your child\'s voice.' },
        ],
      },
      {
        heading: '4. Why we use this data',
        blocks: [
          {
            t: 'ul',
            items: [
              'So that your child can talk with Al-Sadiq and get answers.',
              'To show Al-Sadiq\'s answers together with their sources.',
              'To keep your child safe, and to alert you when needed.',
              'To give you short reports, so you can follow along and talk together.',
              'To keep your account secure, and to send the emails you ask for, such as a password reset.',
            ],
          },
        ],
      },
      {
        heading: '5. What we do not do',
        blocks: [
          {
            t: 'ul',
            items: [
              'We do not use your child\'s data for advertising. The app shows no ads.',
              'We do not sell your data.',
              'We do not draw conclusions about your child\'s or your family\'s religion, belief, level of practice or prayer habits. Reports note topics your child raised. They do not judge your child.',
              'We do not use your child\'s conversations to train our own models.',
            ],
          },
        ],
      },
      {
        heading: '6. Who helps us process data',
        blocks: [
          { t: 'p', text: 'We use other companies to run the app. Each one receives only what it needs for its job.' },
          {
            t: 'table',
            caption: 'Companies that process data for us, what each one does, and what it receives',
            head: ['Company', 'What it does', 'What it receives'],
            rows: [
              ['OpenAI', 'Speech recognition. The language model that writes Al-Sadiq\'s replies. The session reports.', 'Your child\'s speech and messages, Al-Sadiq\'s replies, and for the report the conversation text with the child\'s nickname and age.'],
              ['ElevenLabs', 'Turns Al-Sadiq\'s replies into voice.', 'The text of Al-Sadiq\'s replies.'],
              ['LiveKit', 'The live audio connection between the app and Al-Sadiq.', 'The live audio and data stream of a session.'],
              ['Mailtrap', 'Sends emails, such as password resets.', 'Your email address and the text of the email.'],
              ['Our hosting provider (name to be confirmed)', 'Stores our database.', 'All data in section 3.'],
            ],
          },
          { t: 'p', text: 'These companies may handle data outside your country.' },
        ],
      },
      {
        heading: '7. How long we keep data',
        blocks: [
          {
            t: 'table',
            caption: 'How long each kind of data is kept',
            head: ['Data', 'How long we keep it'],
            rows: [
              ['Conversation messages', 'Deleted when the session report is made, right after the session ends.'],
              ['Flagged messages and safety notes', 'Kept for a short, fixed number of days (to be confirmed). Then they are deleted.'],
              ['Session reports, weekly summaries and Al-Sadiq\'s memory', 'While the account is active, or until you delete your child\'s data.'],
              ['Parent and child profiles', 'Until you delete the account.'],
              ['Server logs', 'To be confirmed.'],
            ],
          },
        ],
      },
      {
        heading: '8. Your rights as a parent',
        blocks: [
          {
            t: 'ul',
            items: [
              'See. In the parent area you can see your child\'s profile, reports and alerts. You see summaries. You do not see your child\'s conversations.',
              'Correct. You can edit your child\'s profile.',
              'Delete. You can ask us to delete your child\'s data, or your whole account. Write to us at the address in section 12.',
              'Ask or complain. Write to us at the address in section 12.',
            ],
          },
        ],
      },
      {
        heading: '9. Children',
        blocks: [
          { t: 'p', text: 'Only a parent can create a child\'s profile. The app is made for children aged 6 to 13 to use with their parents\' knowledge. If you think a child made an account without a parent, please contact us.' },
        ],
      },
      {
        heading: '10. Security',
        blocks: [
          { t: 'p', text: 'We take reasonable steps to protect data. The detailed measures are still to be confirmed. No system is perfectly safe, so we cannot promise that nothing will ever go wrong.' },
        ],
      },
      {
        heading: '11. Changes to this policy',
        blocks: [
          { t: 'p', text: 'We may change this policy. When we do, we will change the date below. If the change is important, we will tell you in the app.' },
        ],
      },
      {
        heading: '12. Contact',
        blocks: [
          {
            t: 'lines',
            lines: [
              'Organisation: the Al-Sadiq Al-Sadouq team (full name to be confirmed)',
              'Contact email: to be confirmed before launch',
              'Postal address or country: to be confirmed',
              'Last updated: 5 October 2026 (draft v0.1)',
            ],
          },
        ],
      },
    ],
  },
  ar: {
    dir: 'rtl',
    lang: 'ar',
    title: 'سياسة الخصوصية: الصديق الصدوق',
    subtitle: 'للوالدين',
    draft: 'مسودة بانتظار المراجعة القانونية',
    switchTo: 'English',
    switchLabel: 'عرض هذه الصفحة بالإنجليزية',
    back: 'رجوع',
    sections: [
      {
        heading: '1. عن هذه السياسة',
        blocks: [
          { t: 'p', text: 'الصديق الصدوق تطبيق يتحدث فيه الأطفال من عمر 6 إلى 13 سنة مع رفيق ذكي اسمه «الصديق» عن القيم الإسلامية. يُنشئ أحد الوالدين الحساب وملف الطفل.' },
          { t: 'p', text: 'توضح لك هذه السياسة، بصفتك وليّ الأمر، ما البيانات التي نستخدمها ولماذا. كتبناها بجمل قصيرة وبسيطة عن قصد.' },
        ],
      },
      {
        heading: '2. ما هو التطبيق وما ليس هو',
        blocks: [
          {
            t: 'ul',
            items: [
              'الصديق ذكاء اصطناعي، وليس إنسانًا.',
              'الصديق ليس عالمًا. لا يُصدر فتاوى، ولا يُصدر أحكامًا في حالة أسرتك الخاصة. اسأل عالمًا مؤهلًا في هذه الأمور.',
              'قد يخطئ الصديق.',
              'حين يعرض الصديق آية أو حديثًا فهو من مصدر معتمد، وتذكر بطاقة المصدر اسمه. أما الشرح الذي بجانبه فيكتبه الذكاء الاصطناعي بكلمات بسيطة.',
              'في مكتبتنا، كلمة «مُراجَع» تعني أن فريقنا طابق النص مع مصدره. ولا تعني أن عالمًا راجعه.',
            ],
          },
        ],
      },
      {
        heading: '3. ما البيانات التي نجمعها',
        blocks: [
          { t: 'lead', lead: 'حساب الوالد.', text: 'اسمك وبريدك الإلكتروني، ورقم هاتفك إن أدخلته.' },
          { t: 'lead', lead: 'ملف الطفل.', text: 'الاسم المستعار لطفلك، والجنس، وسنة الميلاد أو الفئة العمرية، واللغة، ووقت آخر استخدام لطفلك للتطبيق.' },
          { t: 'lead', lead: 'المحادثات.', text: 'ما يقوله طفلك (يُحوَّل كلامه إلى نص) وما يردّ به الصديق.' },
          { t: 'lead', lead: 'تنبيهات السلامة.', text: 'إذا دلّت رسالة على أن الطفل قد يكون في خطر، أو قد يؤذي نفسه أو غيره، نضع عليها علامة ونرسل إليك تنبيهًا.' },
          { t: 'lead', lead: 'التقارير.', text: 'بعد كل جلسة نُعدّ تقريرًا قصيرًا. فيه ملخص، وموضوعات، ولحظات مهمة، وحقائق ذكرها طفلك للصديق (مثل مادته المفضلة). ونُعدّ لك أيضًا ملخصًا أسبوعيًا. ونحتفظ بذاكرة قصيرة متجددة، ليتذكر الصديق ما شاركه طفلك.' },
          { t: 'lead', lead: 'أسئلة للنقاش.', text: 'حين يطلب الصديق من طفلك أن يناقش سؤالًا معك، نحفظ موضوع السؤال. ولا نحفظ كلام الطفل في هذه القائمة.' },
          { t: 'lead', lead: 'بيانات تقنية.', text: 'تسجّل سجلات خوادمنا معرّفات تقنية. ولا تسجّل ما يقوله طفلك.' },
          { t: 'lead', lead: 'التسجيلات الصوتية.', text: 'لا نحتفظ بتسجيلات لصوت طفلك.' },
        ],
      },
      {
        heading: '4. لماذا نستخدم هذه البيانات',
        blocks: [
          {
            t: 'ul',
            items: [
              'ليتحدث طفلك مع الصديق ويحصل على إجابات.',
              'لنعرض إجابات الصديق مع مصادرها.',
              'لنحافظ على سلامة طفلك ونُنبّهك عند الحاجة.',
              'لنعطيك تقارير قصيرة تساعدك على المتابعة والحوار مع طفلك.',
              'لنحمي حسابك ونرسل إليك الرسائل التي تطلبها، مثل إعادة تعيين كلمة المرور.',
            ],
          },
        ],
      },
      {
        heading: '5. ما الذي لا نفعله',
        blocks: [
          {
            t: 'ul',
            items: [
              'لا نستخدم بيانات طفلك في الإعلانات. ولا يعرض التطبيق إعلانات.',
              'لا نبيع بياناتك.',
              'لا نستنتج شيئًا عن دين طفلك أو أسرتك، ولا عن عقيدتهم أو مستوى التزامهم أو عادات الصلاة عندهم. تذكر التقارير موضوعات أثارها طفلك، ولا تحكم عليه.',
              'لا نستخدم محادثات طفلك لتدريب نماذجنا الخاصة.',
            ],
          },
        ],
      },
      {
        heading: '6. من يساعدنا في معالجة البيانات',
        blocks: [
          { t: 'p', text: 'نستعين بشركات أخرى لتشغيل التطبيق. وكل شركة تتلقى فقط ما تحتاج إليه لأداء عملها.' },
          {
            t: 'table',
            caption: 'الشركات التي تعالج البيانات لأجلنا، وما تفعله كل شركة، وما تتلقاه',
            head: ['الشركة', 'ماذا تفعل', 'ماذا تتلقى'],
            rows: [
              ['OpenAI', 'التعرّف على الكلام. والنموذج اللغوي الذي يكتب ردود الصديق. وتقارير الجلسات.', 'كلام طفلك ورسائله، وردود الصديق، وللتقرير نص المحادثة مع الاسم المستعار للطفل وعمره.'],
              ['ElevenLabs', 'تحويل ردود الصديق إلى صوت.', 'نص ردود الصديق.'],
              ['LiveKit', 'الاتصال الصوتي المباشر بين التطبيق والصديق.', 'البث المباشر للصوت والبيانات في الجلسة.'],
              ['Mailtrap', 'إرسال الرسائل الإلكترونية، مثل إعادة تعيين كلمة المرور.', 'بريدك الإلكتروني ونص الرسالة.'],
              ['مزوّد الاستضافة (الاسم بانتظار التأكيد)', 'تخزين قاعدة بياناتنا.', 'كل البيانات المذكورة في البند 3.'],
            ],
          },
          { t: 'p', text: 'قد تعالج هذه الشركات البيانات خارج بلدك.' },
        ],
      },
      {
        heading: '7. كم نحتفظ بالبيانات',
        blocks: [
          {
            t: 'table',
            caption: 'مدة الاحتفاظ بكل نوع من البيانات',
            head: ['البيانات', 'مدة الاحتفاظ'],
            rows: [
              ['رسائل المحادثة', 'تُحذف عند إعداد تقرير الجلسة، بعد انتهاء الجلسة مباشرة.'],
              ['الرسائل المُعلَّمة وملاحظات السلامة', 'تُحفظ عددًا قصيرًا محددًا من الأيام (بانتظار التأكيد). ثم تُحذف.'],
              ['تقارير الجلسات والملخصات الأسبوعية وذاكرة الصديق', 'ما دام الحساب فعّالًا، أو حتى تحذف أنت بيانات طفلك.'],
              ['ملفا الوالد والطفل', 'حتى تحذف الحساب.'],
              ['سجلات الخوادم', 'بانتظار التأكيد.'],
            ],
          },
        ],
      },
      {
        heading: '8. حقوقك بصفتك وليّ أمر',
        blocks: [
          {
            t: 'ul',
            items: [
              'الاطلاع. في منطقة الوالدين ترى ملف طفلك وتقاريره وتنبيهاته. ترى ملخصات، ولا ترى محادثات طفلك.',
              'التصحيح. يمكنك تعديل ملف طفلك.',
              'الحذف. يمكنك أن تطلب منا حذف بيانات طفلك أو حسابك كله. راسلنا على العنوان المذكور في البند 12.',
              'السؤال أو الشكوى. راسلنا على العنوان المذكور في البند 12.',
            ],
          },
        ],
      },
      {
        heading: '9. الأطفال',
        blocks: [
          { t: 'p', text: 'لا ينشئ ملف الطفل إلا أحد الوالدين. التطبيق مصمَّم للأطفال من 6 إلى 13 سنة ليستخدموه بعلم والديهم. إذا ظننت أن طفلًا أنشأ حسابًا دون والد، فتواصل معنا.' },
        ],
      },
      {
        heading: '10. الأمان',
        blocks: [
          { t: 'p', text: 'نتخذ خطوات معقولة لحماية البيانات. وتفاصيل الإجراءات بانتظار التأكيد. لا يوجد نظام آمن تمامًا، لذلك لا نستطيع أن نعد بأن شيئًا لن يحدث أبدًا.' },
        ],
      },
      {
        heading: '11. تغييرات هذه السياسة',
        blocks: [
          { t: 'p', text: 'قد نغيّر هذه السياسة. وعند ذلك نغيّر التاريخ أدناه. وإذا كان التغيير مهمًا أخبرناك به داخل التطبيق.' },
        ],
      },
      {
        heading: '12. التواصل',
        blocks: [
          {
            t: 'lines',
            lines: [
              'الجهة: فريق الصديق الصدوق (الاسم الكامل بانتظار التأكيد)',
              'البريد الإلكتروني للتواصل: يُحدَّد قبل الإطلاق',
              'العنوان البريدي أو الدولة: بانتظار التأكيد',
              'آخر تحديث: 5 أكتوبر 2026 (مسودة 0.1)',
            ],
          },
        ],
      },
    ],
  },
};
