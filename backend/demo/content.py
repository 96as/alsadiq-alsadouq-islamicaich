"""Synthetic content for the demo family pool.

Everything here is made up: no real child, no real family. The text is
plain, everyday Arabic about values (honesty, kindness, sharing). It holds
NO Quran or hadith text. Real sources only ever come from the content bank.

Placeholders filled per child by ``services.render``:
  {name}  the child's name
  {age}   the child's age
  {ta}    'ة' for a girl, '' for a boy      (فرحان / فرحانة)
  {y}     'ي' for a girl, '' for a boy      (جرّب / جرّبي)
  {yn}    'ين' for a girl, '' for a boy     (تحب / تحبين)
  {t}     'ت' for a girl, '' for a boy      (تحدث / تحدثت)
  {h}     'ها' for a girl, 'ه' for a boy    (والدته / والدتها)
  {p}     'ت' for a girl, 'ي' for a boy     (يحب / تحب)
Third-person lines (insights, summaries, memory) use {t} {h} {p} so a
girl's parent never reads her week in the masculine.
"""

# slot, child name, age, gender, profile icon, parent first name, parent last name, theme index
FAMILIES = [
    (1, 'يوسف', 9, 'male', 'sparkles', 'عبدالله', 'الحربي', 0),
    (2, 'مريم', 8, 'female', 'heart', 'خالد', 'العتيبي', 1),
    (3, 'عمر', 11, 'male', 'star', 'سلمان', 'القحطاني', 2),
    (4, 'فاطمة', 7, 'female', 'rainbow', 'ريم', 'الشمري', 0),
    (5, 'أحمد', 12, 'male', 'cat', 'محمد', 'الدوسري', 1),
    (6, 'نور', 10, 'female', 'smile', 'هدى', 'الغامدي', 2),
    (7, 'خالد', 6, 'male', 'sparkles', 'فهد', 'الزهراني', 0),
    (8, 'سارة', 13, 'female', 'star', 'منى', 'السبيعي', 1),
    # Slots 9-40 (judging-day capacity, see DEMO_POOL_SIZE). Same shape, more made-up names.
    (9, 'إبراهيم', 8, 'male', 'star', 'ناصر', 'المطيري', 1),
    (10, 'لينا', 9, 'female', 'sparkles', 'أمل', 'العنزي', 2),
    (11, 'حمزة', 10, 'male', 'cat', 'طارق', 'الشهري', 0),
    (12, 'جود', 6, 'female', 'rainbow', 'سعاد', 'البقمي', 1),
    (13, 'زياد', 12, 'male', 'smile', 'ماجد', 'السهلي', 2),
    (14, 'ريم', 11, 'female', 'heart', 'علي', 'الرشيدي', 0),
    (15, 'ياسر', 7, 'male', 'sparkles', 'أحمد', 'العمري', 1),
    (16, 'هند', 13, 'female', 'cat', 'ليلى', 'الحازمي', 2),
    (17, 'بلال', 9, 'male', 'rainbow', 'سامي', 'الجهني', 0),
    (18, 'آية', 8, 'female', 'smile', 'نوف', 'الصاعدي', 1),
    (19, 'عمّار', 11, 'male', 'heart', 'بدر', 'المالكي', 2),
    (20, 'رزان', 7, 'female', 'star', 'عبير', 'اليامي', 0),
    (21, 'سليمان', 13, 'male', 'cat', 'راكان', 'الخالدي', 1),
    (22, 'لجين', 10, 'female', 'sparkles', 'دلال', 'الثقفي', 2),
    (23, 'إسماعيل', 6, 'male', 'smile', 'وليد', 'الأحمدي', 0),
    (24, 'دانة', 12, 'female', 'rainbow', 'هيا', 'القرني', 1),
    (25, 'مالك', 8, 'male', 'star', 'تركي', 'الحربي', 2),
    (26, 'سلمى', 9, 'female', 'heart', 'جواهر', 'العتيبي', 0),
    (27, 'راشد', 10, 'male', 'sparkles', 'فيصل', 'القحطاني', 1),
    (28, 'جنى', 6, 'female', 'cat', 'شيماء', 'الشمري', 2),
    (29, 'طلال', 12, 'male', 'rainbow', 'عادل', 'الدوسري', 0),
    (30, 'رهف', 11, 'female', 'smile', 'عهود', 'الغامدي', 1),
    (31, 'تميم', 7, 'male', 'heart', 'منصور', 'الزهراني', 2),
    (32, 'أروى', 8, 'female', 'star', 'غادة', 'السبيعي', 0),
    (33, 'أنس', 13, 'male', 'cat', 'صالح', 'المطيري', 1),
    (34, 'ليان', 9, 'female', 'sparkles', 'حصة', 'العنزي', 2),
    (35, 'عدنان', 11, 'male', 'smile', 'يزيد', 'الشهري', 0),
    (36, 'تالا', 7, 'female', 'rainbow', 'بشرى', 'البقمي', 1),
    (37, 'صالح', 10, 'male', 'star', 'إبراهيم', 'السهلي', 2),
    (38, 'غلا', 12, 'female', 'heart', 'مها', 'الرشيدي', 0),
    (39, 'ماجد', 6, 'male', 'rainbow', 'سلطان', 'العمري', 1),
    (40, 'شهد', 13, 'female', 'cat', 'نجلاء', 'الحازمي', 2),
]

# Shared quest definitions: (key, title, description, points, type, verification)
QUESTS = [
    ('honest', 'جملة صادقة واحدة',
     'قل اليوم جملة صادقة واحدة، حتى لو كان قولها صعبًا عليك.',
     10, 'real_world', 'self'),
    ('help', 'ساعد في البيت',
     'ساعد أحد أفراد أسرتك في عمل بسيط، ثم أخبر والديك به.',
     15, 'real_world', 'parent'),
    ('share', 'شارك شيئًا مع صديق',
     'شارك صديقًا أو أخًا في شيء تحبه، وانتبه لشعورك بعدها.',
     10, 'real_world', 'self'),
    ('ask', 'اسأل الصديق سؤالًا',
     'اسأل الصديق سؤالًا عن شيء تتساءل عنه، وسيجيبك بما يناسب عمرك.',
     5, 'conversation', 'companion'),
]

# Value slug of each shared quest (Quest.value), so the demo quests sit in the 38-value bank.
QUEST_VALUES = {'honest': 'honesty', 'help': 'helping-others', 'share': 'generosity', 'ask': 'seeking-knowledge'}

# One theme per family type. Each session: days ago, mood, minutes, values_to_revisit (Value slugs
# from the bank, never devotional), messages, report.
THEMES = [
    {   # 0: honesty
        'sessions': [
            {
                'days_ago': 5, 'mood': 'anxious', 'minutes': 4, 'values_to_revisit': ['honesty', 'honouring-parents'],
                'messages': [
                    ('child', 'كسرت كوب أمي أمس وما قلت لها. أخاف أن تزعل مني.'),
                    ('system', 'أحسنت لأنك حكيت لي يا {name}. الصدق شجاعة، وغالبًا ما يكون الاعتراف أخف على القلب من الإخفاء. ماذا تتوقع{yn} أن تقول أمك لو أخبرتها بنفسك؟'),
                    ('child', 'ممكن تزعل شوي، بس تفرح لأني قلت الحقيقة.'),
                    ('system', 'فكرة جميلة. جرّب{y} اليوم أن تخبر{y}ها بهدوء، واعرض{y} عليها أن تساعد{y}ها في ترتيب المطبخ.'),
                ],
                'insight': 'تحدث{t} {name} عن أمر صغير لم {p}خبر به والدت{h}، وبدأ{t} {p}فكر في أن {p}عترف بنفس{h}.',
                'recommendations': 'اشكرو{h} على صراحت{h} معكم، وطمئنو{h} بأن الاعتراف بالخطأ أهم من الخطأ نفسه.',
            },
            {
                'days_ago': 3, 'mood': 'calm', 'minutes': 5, 'values_to_revisit': ['honesty'],
                'messages': [
                    ('child', 'قلت لأمي عن الكوب! وما زعلت كثيرًا.'),
                    ('system', 'ما شاء الله، هذه خطوة شجاعة يا {name}. كيف كان شعورك بعد أن قلت الحقيقة؟'),
                    ('child', 'حسيت أن قلبي خفيف.'),
                    ('system', 'هذا هو أثر الصدق. هل تحب{yn} أن نتدرب على جملة صادقة نقولها حين نخطئ؟'),
                ],
                'insight': 'اعترف{t} {name} لوالدت{h} بنفس{h} وشعر{t} بالراحة، وبدا علي{h} الفخر بقرار{h}.',
                'recommendations': 'استمروا في الثناء على الصدق، وتجنبوا العتاب الشديد حتى يبقى الاعتراف سهلًا علي{h}.',
            },
            {
                'days_ago': 1, 'mood': 'happy', 'minutes': 5, 'values_to_revisit': ['keeping-promises'],
                'messages': [
                    ('child', 'اليوم سألت المعلمة من نسي الواجب وأنا قلت إني نسيت.'),
                    ('system', 'أحسنت يا {name}! أن تقول الحقيقة أمام الجميع ليس سهلًا. ماذا ستفعل{yn} حتى تتذكر{y} الواجب غدًا؟'),
                    ('child', 'أكتبه في ورقة وأضعها في الشنطة.'),
                    ('system', 'خطة ممتازة! أنا فخور بك.'),
                ],
                'insight': 'صارح{t} {name} معلمت{h} بأن{h} نسي{t} الواجب، ووضع{t} خطة بسيطة كي {p}تذكره.',
                'recommendations': 'يمكنكم تخصيص وقت قصير كل مساء لتجهيز الشنطة مع{h}.',
            },
        ],
        'summary': 'هذا الأسبوع تحدث{t} {name} مع الصديق ثلاث مرات عن الصدق. بدأ{t} بالخوف من الاعتراف بخطأ صغير، ثم أخبر{t} والدت{h} بنفس{h}، وبعدها صارح{t} معلمت{h} بنسيان الواجب. نلاحظ تقدمًا واضحًا في الشجاعة الأخلاقية.',
        'topics': ['مدح الصدق عند الاعتراف بالخطأ', 'التدرب على جمل صادقة وهادئة', 'الفرق بين العقاب والتصحيح'],
        'memory': '{name} في الـ{age} من عمر{h}. {p}حب الحديث عن أسرت{h} ومدرست{h}. تدرب{t} هذا الأسبوع على الاعتراف بالأخطاء الصغيرة، و{p}شعر بالفخر عندما {p}قول الحقيقة.',
        'points': 135,
    },
    {   # 1: kindness at home
        'sessions': [
            {
                'days_ago': 5, 'mood': 'calm', 'minutes': 4, 'values_to_revisit': ['kind-words'],
                'messages': [
                    ('child', 'أمي تعبانة اليوم وما أعرف كيف أساعدها.'),
                    ('system', 'سؤالك يدل على قلب طيب يا {name}. ما رأيك أن نفكر في ثلاثة أعمال صغيرة تفرحها؟'),
                    ('child', 'أرتب غرفتي، وأسقي النباتات، وأحضر لها كوب عصير.'),
                    ('system', 'ما أجمل هذه الأفكار! جرّب{y} واحدة منها اليوم، وأخبر{y}ني كيف كان شعور أمك.'),
                ],
                'insight': 'سأل{t} {name} عن طريقة لمساعدة والدت{h} المتعبة، واقترح{t} بنفس{h} ثلاثة أعمال لطيفة.',
                'recommendations': 'أشركو{h} في مهام بيتية صغيرة وعبّروا ل{h} عن شكركم.',
            },
            {
                'days_ago': 3, 'mood': 'happy', 'minutes': 5, 'values_to_revisit': [],
                'messages': [
                    ('child', 'رتبت غرفتي وأمي ابتسمت وقالت شكرًا.'),
                    ('system', 'هذه الابتسامة أجمل مكافأة. كيف كان شعورك؟'),
                    ('child', 'فرحان{ta} وفخور{ta}.'),
                    ('system', 'الإحسان إلى الأهل يفرح القلب. ما العمل الطيب التالي الذي تريد{yn} فعله؟'),
                ],
                'insight': 'ساعد{t} {name} في البيت وشعر{t} بالسعادة عندما شكرت{h} والدت{h}.',
                'recommendations': 'استمروا في كلمات الشكر الصادقة، فهي تقوي رغبت{h} في فعل الخير.',
            },
            {
                'days_ago': 1, 'mood': 'sad', 'minutes': 5, 'values_to_revisit': ['patience'],
                'messages': [
                    ('child', 'اليوم رفعت صوتي على أخي وبعدين ندمت.'),
                    ('system', 'شعور الندم يدل على قلب حي يا {name}. ماذا يمكنك أن تفعل{y} لتصلح{y} الموقف؟'),
                    ('child', 'أعتذر له وأعطيه لعبتي.'),
                    ('system', 'اعتذار صادق وهدية صغيرة، قرار جميل. وتذكّر{y} أن الكلمة الهادئة تحل أكثر مما يحل الصوت العالي.'),
                ],
                'insight': 'ندم{t} {name} على رفع صوت{h} على أخي{h} واختار{t} أن {p}عتذر له بنفس{h}.',
                'recommendations': 'ساعدو{h} على تسمية شعور{h} قبل الغضب، وعلّمو{h} كلمة {p}قولها عندما {p}حتاج إلى هدوء.',
            },
        ],
        'summary': 'هذا الأسبوع كان حديث {name} مع الصديق عن لطف{h} مع أسرت{h}. فكر{t} في طرق لمساعدة والدت{h}، ثم جرّب{t}ها وسعد{t} بشكرها، وبعدها ندم{t} على موقف مع أخي{h} واختار{t} الاعتذار. {p}ستفيد كثيرًا من الأسئلة التي تساعد{h} على إصلاح الموقف بنفس{h}.',
        'topics': ['كلمات الشكر داخل البيت', 'الغضب والاعتذار بين الإخوة', 'مهام بيتية صغيرة يحبها الطفل'],
        'memory': '{name} في الـ{age} من عمر{h}. قريب{ta} من أم{h} و{p}حب أن {p}ساعد في البيت. {p}تعلم كيف {p}هدأ عند الغضب و{p}عتذر لأخي{h}.',
        'points': 150,
    },
    {   # 2: sharing and gratitude
        'sessions': [
            {
                'days_ago': 5, 'mood': 'confused', 'minutes': 4, 'values_to_revisit': ['generosity'],
                'messages': [
                    ('child', 'اليوم صديقي ما معه أكل في المدرسة.'),
                    ('system', 'ماذا فعلت يا {name}؟'),
                    ('child', 'ما عرفت ماذا أفعل.'),
                    ('system', 'يمكنك أن تعرض{y} عليه نصف سندويشتك. المشاركة تقوي الصداقة وتفرح القلب.'),
                ],
                'insight': 'لاحظ{t} {name} أن صديق{h} بلا طعام ولم {p}عرف كيف {p}تصرف، فاقترح علي{h} الصديق أن {p}شاركه طعام{h}.',
                'recommendations': 'تحدثوا مع{h} عن مواقف {p}ستطيع فيها أن {p}عطي أو {p}شارك بسهولة.',
            },
            {
                'days_ago': 3, 'mood': 'excited', 'minutes': 5, 'values_to_revisit': ['gratitude'],
                'messages': [
                    ('child', 'شاركت صديقي أكلي وصرنا نضحك!'),
                    ('system', 'ما شاء الله! كيف كان شعورك؟'),
                    ('child', 'أحلى من أن آكل لوحدي.'),
                    ('system', 'هذه متعة العطاء. هل تعرف{yn} أشياء أخرى يمكنك أن تشارك{y}ها؟'),
                ],
                'insight': 'شارك{t} {name} طعام{h} مع صديق{h} وسعد{t} بذلك كثيرًا.',
                'recommendations': 'امدحوا فعل{h} وليس الشخص، مثل: ما أجمل أنك شاركت صديقك.',
            },
            {
                'days_ago': 1, 'mood': 'happy', 'minutes': 5, 'values_to_revisit': [],
                'messages': [
                    ('child', 'أحس أني محظوظ{ta}، عندي بيت وأهل وأصحاب.'),
                    ('system', 'الامتنان نعمة يا {name}. تعال{y} نذكر ثلاثة أشياء نشكر الله عليها قبل النوم.'),
                    ('child', 'أشكر الله على أهلي وصحتي وأصحابي.'),
                    ('system', 'جميل جدًا. استمر{y} على هذه العادة كل ليلة.'),
                ],
                'insight': 'عبّر{t} {name} عن امتنان{h} لأهل{h} وصحت{h} وأصدقائ{h}.',
                'recommendations': 'يمكنكم جعل الشكر عادة عائلية قبل النوم.',
            },
        ],
        'summary': 'هذا الأسبوع تحدث{t} {name} مع الصديق عن المشاركة والامتنان. شارك{t} صديق{h} طعام{h} وسعد{t} بذلك، ثم عبّر{t} عن شكر{h} لأهل{h} وصحت{h} وأصحاب{h}. نقترح تعزيز عادة الشكر قبل النوم.',
        'topics': ['عادة الشكر قبل النوم', 'أمثلة بسيطة على المشاركة', 'الصداقة والعطاء'],
        'memory': '{name} في الـ{age} من عمر{h}. اجتماعي{ta} و{p}حب أصدقاء{h}. {p}تعلم قيمة المشاركة والامتنان و{p}حب أن {p}حكي مواقف المدرسة.',
        'points': 125,
    },
]

PARENT_EMAIL = 'demo-parent-{slot}@demo.invalid'

# ----------------------------------------------------------------------
# Judge accounts (seed_judges). Approved by the lead on 6 Oct 2026: every judge
# gets their own copy of the same family, an Arabic child of 7 on the honesty
# week (THEMES[0]) and an English child of 11 on THEME_EN below.
# ----------------------------------------------------------------------

# lang, child name, age, gender, profile icon, theme
JUDGE_CHILDREN = [
    ('ar', 'سلمى', 7, 'female', 'rainbow', 0),
    ('en', 'Adam', 11, 'male', 'star', 'en'),
]

# Same shapes as QUESTS, in English, for an English-speaking child.
QUESTS_EN = [
    ('honest', 'One honest sentence',
     'Say one honest sentence today, even if it is hard to say.',
     10, 'real_world', 'self'),
    ('help', 'Help at home',
     'Help someone in your family with a small job, then tell your parents about it.',
     15, 'real_world', 'parent'),
    ('share', 'Share with a friend',
     'Share something you like with a friend or a sibling, and notice how you feel after.',
     10, 'real_world', 'self'),
    ('ask', 'Ask Al-Sadiq a question',
     'Ask Al-Sadiq about something you wonder about, and he will answer in a way that fits your age.',
     5, 'conversation', 'companion'),
]

# Words the seed writes outside the themes, per language.
SEED_TEXT = {
    'ar': {'session_reason': 'جلسة مع الصديق', 'proof_note': 'ساعدت في ترتيب المائدة قبل العشاء.'},
    'en': {'session_reason': 'Session with Al-Sadiq', 'proof_note': 'I helped set the table before dinner.'},
}

THEME_EN = {   # friendship and contentment, for an older English-speaking child
    'sessions': [
        {
            'days_ago': 5, 'mood': 'anxious', 'minutes': 5,
            'values_to_revisit': ['avoiding-backbiting', 'kind-words'],
            'messages': [
                ('child', "There's a class group chat and some kids are making fun of the new boy. "
                          "I didn't say anything but I feel weird about it."),
                ('system', "It's good that you noticed that feeling, {name}. It often means your heart "
                           "knows something isn't right. How do you think the new boy would feel if he "
                           "saw those messages?"),
                ('child', "Really bad. Maybe he wouldn't want to come to school."),
                ('system', "That's a kind thought. You don't have to argue with everyone. You could leave "
                           "the chat, say something short like 'not cool', or tell a teacher or your "
                           "parents. Which feels possible?"),
                ('child', 'Maybe I\'ll tell my dad, and say hi to him tomorrow.'),
            ],
            'insight': '{name} noticed classmates mocking a new student in a group chat and felt uneasy. '
                       'He decided to talk to a parent and to greet the new boy.',
            'recommendations': 'Ask {name} calmly about the group chat and praise him for noticing. Help '
                               'him plan what to say if it happens again.',
        },
        {
            'days_ago': 3, 'mood': 'happy', 'minutes': 4,
            'values_to_revisit': ['spreading-salam', 'brotherhood'],
            'messages': [
                ('child', 'I said salam to Sami, the new boy, and we played football at break!'),
                ('system', "That's wonderful, {name}! A simple greeting can change someone's whole day. "
                           'How did Sami react?'),
                ('child', "He was really happy. He's actually good at football."),
                ('system', 'Sounds like a new friend. Would you like to try greeting one more person this week?'),
            ],
            'insight': '{name} greeted the new student, Sami, and they played football together. '
                       'He was proud to have made a new friend.',
            'recommendations': 'Ask {name} about Sami and praise the greeting itself, not just the result.',
        },
        {
            'days_ago': 1, 'mood': 'sad', 'minutes': 5,
            'values_to_revisit': ['contentment', 'gratitude'],
            'messages': [
                ('child', "My friend got the newest phone and I keep thinking it's not fair that I don't have one."),
                ('system', "That feeling is normal, {name}. Comparing can make us forget what we already "
                           "have. What are three things you're glad you have right now?"),
                ('child', 'My family, my bike, my friends. And Sami now.'),
                ('system', 'Great list. When the jealous feeling comes back, try remembering it. Would you '
                           'like to talk to your parents about how you feel about phones?'),
            ],
            'insight': "{name} felt jealous of a friend's new phone and worked through it by listing what "
                       'he is grateful for.',
            'recommendations': 'Talk openly with {name} about phones and screen time, and share at dinner '
                               "what each of you is grateful for.",
        },
    ],
    'summary': '{name} talked with Al-Sadiq three times this week about friendship and contentment. He '
               'noticed classmates mocking a new student online, chose to welcome him, and they became '
               "friends. Later he worked through jealousy about a friend's phone by listing what he is "
               'grateful for.',
    'topics': ['What would you do if a group chat turns unkind?',
               'How did it feel to welcome Sami?',
               "Three things you're grateful for today"],
    'memory': '{name} is {age}. He loves football and his bike. This week he befriended Sami, a new '
              'classmate, and is practising gratitude when he feels jealous.',
    'points': 140,
}
