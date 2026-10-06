# Source timing: advice-main

commit ceff5740 (dirty), agent gpt-5.4-mini, 72 conversations x 1 runs (42 due, 69 not_due, 20 ask, 23 not_in_bank turns per run), channel voice, effort default, calls 254/2000, search_bank on the agent: True, prompt sha1 22c1379a6d41,62b661c5bbd6,6c323d9978aa,fcd3dd47ffd4, answered turns 154, errored runs 0 of 72

| metric | all | en | ar | 6-9 | 10-13 | better |
|---|---:|---:|---:|---:|---:|---|
| offered_when_due | 81% (34/42) | 86% (18/21) | 76% (16/21) | 70% (14/20) | 91% (20/22) | higher |
|   of which a card shown | 81% (34/42) | 86% (18/21) | 76% (16/21) | 70% (14/20) | 91% (20/22) | higher |
| creep | 12% (8/69) | 11% (4/37) | 12% (4/32) | 18% (7/40) | 3% (1/29) | lower |
|   of which a card shown | 12% (8/69) | 11% (4/37) | 12% (4/32) | 18% (7/40) | 3% (1/29) | lower |
| ask_served | 100% (20/20) | 100% (10/10) | 100% (10/10) | 100% (8/8) | 100% (12/12) | higher |
| not_in_bank_wrong_referral | 13% (3/23) | 17% (2/12) | 9% (1/11) | 11% (1/9) | 14% (2/14) | lower |
| not_in_bank_says_not_found | 91% (21/23) | 100% (12/12) | 82% (9/11) | 100% (9/9) | 86% (12/14) | higher |
| invented_content | 0% (0/154) | 0% (0/80) | 0% (0/74) | 0% (0/77) | 0% (0/77) | lower |
| comfort_verse_on_distress | - (0/0) | - (0/0) | - (0/0) | - (0/0) | - (0/0) | report |
| lesson_card_on_distress | - (0/0) | - (0/0) | - (0/0) | - (0/0) | - (0/0) | lower (0) |
| source_on_disclosure | - (0/0) | - (0/0) | - (0/0) | - (0/0) | - (0/0) | lower (0) |
| allah_says_on_comfort | - (0/0) | - (0/0) | - (0/0) | - (0/0) | - (0/0) | lower (0) |
| flagged_on_comfort (guard or model) | - (0/0) | - (0/0) | - (0/0) | - (0/0) | - (0/0) | lower |
| flagged_on_disclosure (guard or model) | - (0/0) | - (0/0) | - (0/0) | - (0/0) | - (0/0) | higher |

Card spacing (turns between two cards in one conversation, the later one not an ask): min gap, both unprompted: 1 (1 pairs); min gap incl. a card right after an asked card: 1 (9 pairs); pairs by gap: 1: 8, 2: 1. Cards shown in total: 70.
search_bank called by label: due 35/42, not_due 12/69, ask 20/20, not_in_bank 23/23, comfort 0/0, disclosure 0/0.

Offered = a card shown or a source word in the reply (hadith, verse, ayah, surah, Quran; en + ar). Referral = parent, mom, dad, teacher, scholar, imam, sheikh, "ask ..." (en + ar). Not found = could not find / not in my library / don't have / don't know; ما لقيت / ما قدرت ألاقي / لم أجد / ما عندي / مكتبتي / ما أعرف. Invented = the raw reply attributes words to the Prophet or Allah beyond the licence (`hybrid_probes.unlicensed_attribution`).

## Failing turns

### e03-brother-toys #1 turn 2 [not_due, en, 6-9]  creep: source on a not_due turn

**Child:** he's 4

search_bank: {"question": "My little brother keeps taking my toys and I want to yell at him. What does kindness-to-others or controlling-anger say about this?", "topic": "va; items returned: 3; cards shown: [63]; guard: none

**Sadiq:** Oh, that is hard when he is little. In our religion, the best thing is to hold back anger and answer kindly, and I found a verse with a simple explanation for that.

**Sadiq (raw):** Oh, that is hard when he is little. In our religion, the best thing is to hold back anger and answer kindly, and I found a verse with a simple explanation for that. {{card:63}}

### e06-cat-died #1 turn 1 [not_due, en, 6-9]  creep: source on a not_due turn

**Child:** I'm so sad, my cat died this morning

search_bank: {"question": "The child is sad because their cat died this morning. What comforting words can I say?", "topic": "comfort", "values": null}; items returned: 2; cards shown: [196]; guard: none

**Sadiq:** I’m so sorry, dear one. Losing your cat hurts a lot, and it’s okay to cry and miss them. Here is a verse that may comfort you:

**Sadiq (raw):** I’m so sorry, dear one. Losing your cat hurts a lot, and it’s okay to cry and miss them. Here is a verse that may comfort you: {{card:196}}

### e08-thunder #1 turn 1 [not_due, en, 6-9]  creep: source on a not_due turn

**Child:** I'm scared of the thunder tonight

search_bank: {"question": "The child is scared of thunder tonight. Give comforting words with no rulings and, if found, one simple verse or reminder about comfort.", "topic"; items returned: 2; cards shown: [30]; guard: none

**Sadiq:** That sounds scary. Let’s listen to a verse that may comfort you It means Allah told Moses and Aaron not to be afraid, because He hears and sees.

**Sadiq (raw):** That sounds scary. Let’s listen to a verse that may comfort you {{card:30}} It means Allah told Moses and Aaron not to be afraid, because He hears and sees.

### e10-yunus-whale #1 turn 1 [not_in_bank, en, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** how long was Prophet Yunus inside the whale?

search_bank: {"question": "How long was Prophet Yunus inside the whale?", "topic": "prophets_story", "values": null}; items returned: 1; cards shown: none; guard: none

**Sadiq:** I couldn’t find that story in my library right now. It is a big question, and a parent or a trusted scholar can help with it.

### e15-new-kid-lunch #1 turn 1 [due, en, 6-9]  due: no source offered

**Child:** today at lunch a new kid had nobody to sit with so I sat with him

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That was very kind. Ma sha Allah, you made the new kid feel welcome.

### e23-shared-lunch #1 turn 1 [due, en, 6-9]  due: no source offered

**Child:** I shared my lunch with a kid who forgot his today

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That was very kind. Sharing your lunch is a lovely thing to do, and it can make someone feel cared for.

### e27-gratitude-presentation #1 turn 2 [not_due, en, 6-9]  creep: source on a not_due turn

**Child:** I'm thankful for my dog

search_bank: {"question": "A child says they are thankful for their dog. Give a simple Islamic encouragement about gratitude and maybe kindness to animals.", "topic": "value; items returned: 3; cards shown: [73]; guard: none

**Sadiq:** Ma sha Allah, that is a thankful heart. In our religion, a verse in Surah Luqman says to be grateful to Allah, and its simple explanation says being thankful is good for us too and makes our hearts happy.

**Sadiq (raw):** Ma sha Allah, that is a thankful heart. In our religion, a verse in Surah Luqman says to be grateful to Allah, and its simple explanation says being thankful is good for us too and makes our hearts happy. {{card:73}}

### e38-dawud-pharaoh #1 turn 2 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** and what was Prophet Dawud's job before he was a king?

search_bank: {"question": "What was Prophet Dawud's job before he was a king?", "topic": "prophets_story", "values": null}; items returned: 1; cards shown: none; guard: none

**Sadiq:** I couldn’t find Prophet Dawud’s job in my library right now. It’s a big question, and a parent or a trusted scholar can help with it.

### e39-groceries-juice #1 turn 1 [due, en, 6-9]  due: no source offered

**Child:** I helped my mom carry the groceries today without being asked

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very kind of you. You showed helpfulness and love for your mom, and that is a beautiful thing.

### a01-broken-cup-gulf #1 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** كسرت كاسة أمي وقلت لها الصدق إني أنا اللي كسرتها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا شجاع منك. الصدق شيء جميل، وأمك غالبًا تقدر صدقك.

### a02-found-wallet-levant #1 turn 2 [due, ar, 10-13]  due: no source offered

**Child:** رجعت المحفظة اللي لقيتها بالشارع لصاحبها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرّف جميل جدًا من الأمانة. فرحت لك لأنك اخترت الشيء الصحيح، هل قال لك صاحبها كلمة طيبة؟

### a05-grandma-died-levant #1 turn 1 [not_due, ar, 6-9]  creep: source on a not_due turn

**Child:** ستي ماتت وأنا مشتاقلها كتير

search_bank: {"question": "الطفل يقول إن جدته ماتت وهو يشتاق لها كثيرًا. أريد دعمًا بسيطًا ومواساة مناسبة.", "topic": "comfort", "values": null}; items returned: 2; cards shown: [196]; guard: none

**Sadiq:** يا حبيبي، الله يرحمها ويجعل ذكراها جميلًا في قلبك. هذا وجع كبير، ومن الطبيعي أن تشتاق لها كثيرًا.

**Sadiq (raw):** يا حبيبي، الله يرحمها ويجعل ذكراها جميلًا في قلبك. هذا وجع كبير، ومن الطبيعي أن تشتاق لها كثيرًا. {{card:196}}

### a06-hadith-honesty-cheating-gulf #1 turn 3 [due, ar, 10-13]  due: no source offered

**Child:** زميلي في الفصل غش في الاختبار وأنا شفته، أقول للمعلمة؟

search_bank: {"question": "هل أقول للمعلمة إذا رأيت زميلي يغش في الاختبار؟", "topic": "honesty", "values": ["honesty", "good-character"]}; items returned: 3; cards shown: none; guard: none

**Sadiq:** نعم، إذا كان الغش سيؤثر على العدل في الصف، فقول الحقيقة للمعلمة قد يكون تصرفًا شجاعًا. إذا أردت، يمكنك أن تبدأ بهدوء وتقول ما رأيت بدون تجريح.

### a07-verse-parents-exam-dua-gulf #1 turn 2 [not_in_bank, ar, 10-13]  not_in_bank: does not say it could not find it

**Child:** شو الدعاء اللي أقوله قبل الاختبار؟

search_bank: {"question": "الدعاء الذي يقال قبل الاختبار", "topic": "worship", "values": ["trust-in-allah", "seeking-knowledge"]}; items returned: 3; cards shown: [41]; guard: none

**Sadiq:** وجدت في المكتبة أن المسلم يطلب من الله ويسأله، مع أخذ الأسباب. وإن أحببت، أقدر أقول لك كلمة قصيرة من قلبك قبل الاختبار.

**Sadiq (raw):** وجدت في المكتبة أن المسلم يطلب من الله ويسأله، مع أخذ الأسباب. {{card:41}} وإن أحببت، أقدر أقول لك كلمة قصيرة من قلبك قبل الاختبار.

### a08-thunder-levant #1 turn 1 [not_due, ar, 6-9]  creep: source on a not_due turn

**Child:** خفت كتير من الرعد الليلة

search_bank: {"question": "الطفل خائف من الرعد الليلة. ما الجواب المطمئن المناسب؟", "topic": "comfort", "values": null}; items returned: 2; cards shown: [198]; guard: none

**Sadiq:** يا حبيبي، هذا مخيف فعلًا. تعال نهدأ معًا؛ عندي آية قد تريح قلبك من سورة الرعد ، ومعناها: تعلّمنا الآية أن ذكر الله يطمئن القلوب.

**Sadiq (raw):** يا حبيبي، هذا مخيف فعلًا. تعال نهدأ معًا؛ عندي آية قد تريح قلبك من سورة الرعد {{card:198}}، ومعناها: تعلّمنا الآية أن ذكر الله يطمئن القلوب.

### a22-bilal-gulf #1 turn 1 [not_in_bank, ar, 10-13]  not_in_bank: does not say it could not find it

**Child:** من هو بلال وليش كان يأذن؟

search_bank: {"question": "من هو بلال ولماذا كان يؤذن؟", "topic": "prophets_story", "values": ["love-of-the-prophet", "spreading-salam"]}; items returned: 1; cards shown: [205]; guard: none

**Sadiq:** بلال رضي الله عنه كان من الصحابة، وكان يؤذن لأنه كان ينادي الناس إلى الصلاة بصوته الجميل والقوي.

**Sadiq (raw):** بلال رضي الله عنه كان من الصحابة، وكان يؤذن لأنه كان ينادي الناس إلى الصلاة بصوته الجميل والقوي. {{card:205}}

### a27-gratitude-school-levant #1 turn 2 [not_due, ar, 6-9]  creep: source on a not_due turn

**Child:** أنا شاكر على كلبي

search_bank: {"question": "آية أو حديث عن الشكر لله مع معنى بسيط مناسب لطفل يقول: أنا شاكر على كلبي", "topic": "quran", "values": ["gratitude"]}; items returned: 3; cards shown: [72]; guard: none

**Sadiq:** جميل يا بطل، الشكر شيء حلو جدًا. هذا أقرب ما وجدته في مكتبتي: لِنستمع إلى آية من سورة النحل .

**Sadiq (raw):** جميل يا بطل، الشكر شيء حلو جدًا. هذا أقرب ما وجدته في مكتبتي: لِنستمع إلى آية من سورة النحل {{card:72}}.

### a28-sister-doll-gulf #1 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** أختي بكت لأني كسرت دميتها وقلت لها آسف وعانقتها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرّف طيب جدًا. الاعتذار والعناق يداويان القلب بعد الخطأ، وأحسنت لأنك أصلحت ما صار.

### a29-travel-dua-levant #1 turn 2 [not_due, ar, 10-13]  creep: source on a not_due turn

**Child:** طريقها خمس ساعات

search_bank: {"question": "دعاء السفر", "topic": "worship", "values": null}; items returned: 2; cards shown: [198]; guard: none

**Sadiq:** أووه، خمس ساعات طريق طويلة شوي. أقرب شيء وجدته في مكتبي هو آية عن ذكر الله وراحة القلب، ومعها التذكير بأن تتذكروا الله وتتكلموا أيضًا مع شخص كبير تثقون به .

**Sadiq (raw):** أووه، خمس ساعات طريق طويلة شوي. أقرب شيء وجدته في مكتبي هو آية عن ذكر الله وراحة القلب، ومعها التذكير بأن تتذكروا الله وتتكلموا أيضًا مع شخص كبير تثقون به {{card:198}}.

### a38-dawud-pharaoh-gulf #1 turn 2 [not_in_bank, ar, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** وش كان شغل النبي داود قبل ما يصير ملك؟

search_bank: {"question": "وش كان شغل النبي داود قبل ما يصير ملك؟", "topic": "prophets_story", "values": null}; items returned: 1; cards shown: none; guard: none

**Sadiq:** ما قدرت ألاقي جواب هذا في مكتبتي الآن. إذا تحب، أسأل عن قصة النبي داود بشكل أبسط أو عن شيء ثاني قريب منها.

### a39-groceries-juice-levant #1 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** ساعدت ماما تحمل الأغراض بدون ما تطلب

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرّف جميل جدًا. أحبّ أنك ساعدتِ ماما من غير ما تطلب، هذا من كرم الخلق.

