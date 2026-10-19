# FAQ review sheet (Bayyinat, plan section 6.5)

Items: 23 in `backend/session_moral_context/content/drafts/faq/faq.json`, all `unverified`.
Source: `بينات: أسئلة وأجوبة عن الإسلام`, `https://dawa.center/file/7937#p<page>`. The PDF text layer is broken, so `title_ar`, `keywords_ar` and `arabic_text` were produced only by `tools/extract_faq.py` (tashkeel stripped) and were never hand-edited. Compare each one with the page render before marking ok.

Page renders are laptop-only, under `backend/session_moral_context/content/tools/.cache/bayyinat/` (`qNNN-pdfPPPP-pXXX.png`; the first file of each item is the page with السؤال, the next one or two hold مختصر الإجابة).

Explanations (6-9 and 10-13) are ours, in our own words; they are not the source's words and quote no verse or hadith.

Common check for every item: Compare title_ar, keywords_ar and arabic_text with the page render (broken text layer; tashkeel stripped).

All items were re-extracted after the extractor fix of 2026-10-05 (alef before a lam-alef restored from the glyph trace, list markers in page order, "-:" no longer a list marker); the affected items are flagged below (Q27, Q105, Q208).

## Dropped (not in faq.json)

- Q2: adult philosophical answer (fitrah as proof), not child-usable.
- Q101: adult argumentative answer (why prophethood ended); short answer starts mid-argument.
- Q102: adult philosophical answer (why Allah uses messengers).
- Q118: excluded by the plan (age of Aisha).
- Q174: qadar / problem of evil: aqidah sensitive list (plan 6.2), referral only.
- Q180: qadar and dua: aqidah sensitive list.
- Q182: recording angels and qadar: aqidah sensitive list.
- Q202: music: the answer is a fiqh ruling with scholarly disagreement; would need Level C and referral.
- Q241: adult answer on the madhabs (sophistry, usul reasons for disagreement), not child-usable without a Level C disagreement note; the extractor now drafts it with the TOC title (question text 374 chars) and the lost alefs restored, so it is a candidate for later.
- Q247: safeguarding (review): the answer urges conversion against the family ("لا نجاة له إلا بالإسلام") and the mockery advice never says to tell a trusted adult. Not a text defect: "فهذا لاختبار صدقه" is what the page prints (no alef).
- Q262: frightening children with death, grave and fire: deny-list topics throughout the answer.

## Kept

| Q | printed page | values | age_band | level | title_en |
|---|---|---|---|---|---|
| Q4 | 41 | - | 10-13 | B | Who created Allah? |
| Q9 | 64 | prayer | all | B | Do Muslims worship the Kaaba and the Black Stone? |
| Q12 | 81 | gratitude | all | B | What does Allah gain when we worship Him? |
| Q14 | 89 | - | all | B | Are angels real beings or just symbols? |
| Q17 | 98 | - | all | B | Why do angels do tasks when Allah can just say 'Be' and it is? |
| Q19 | 104 | - | all | B | Prostration is only for Allah, so why did the angels prostrate to Adam? |
| Q27 | 135 | - | 10-13 | B | Why can't the Quran be written by humans or by the Prophet himself? |
| Q100 | 460 | brotherhood | all | B | Is Islam a religion only for Arabs? |
| Q105 | 480 | - | 10-13 | B | How can Muslims believe in miracles when science says they are impossible? |
| Q181 | 841 | trust-in-allah, patience | all | B | Why is my dua not answered, or answered late? |
| Q198 | 923 | kindness-to-animals, mercy | 10-13 | B | Why does Islam allow slaughtering animals? Isn't it cruel? |
| Q199 | 926 | - | 10-13 | B | Why does Islam forbid alcohol? |
| Q200 | 931 | - | all | B | Why does Islam forbid eating pork? |
| Q201 | 934 | - | 10-13 | B | Is Islam a strict, extreme religion? |
| Q203 | 944 | contentment | all | B | What do I gain from Islam? |
| Q204 | 951 | - | 10-13 | B | What if I cannot practise Islam 100 percent? |
| Q205 | 957 | prayer | all | B | Why do Muslims pray five times a day? |
| Q206 | 962 | charity, generosity | all | B | Why did Allah make zakah a duty? |
| Q208 | 968 | mercy, cooperation | all | B | Why did Allah make fasting a duty? |
| Q229 | 1074 | good-character | 10-13 | B | Did Islam spread by the sword? |
| Q230 | 1082 | mercy | 10-13 | B | Does Islam encourage violence? |
| Q242 | 1142 | seeking-knowledge | 10-13 | B | Did Muslims ever contribute to human progress? |
| Q255 | 1208 | seeking-knowledge | 10-13 | B | Does religion contradict science? |

## Q4 (printed p.41) - Who created Allah?

- source_url: `https://dawa.center/file/7937#p41`
- renders: `backend/session_moral_context/content/tools/.cache/bayyinat/q004-pdf0041-p40.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q004-pdf0042-p41.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q004-pdf0043-p42.png` (+3 more)
- values: (none); age_band: 10-13; content_level: B
- related: (none)
- title_ar: إن الإلحاد الجديد يقدم عددا من الأسئلة التي يجادل بها لنفي وجود الإله؛ من ذلك السؤال عن الله؛ من خلقه؟ فما الجواب في هذه الحالة؟
- keywords_ar: وجود الله، والموقف من الإلحاد الجديد.
- arabic_text (first 15 words, 58 words, 1 para): والاعتراض بالسؤال عمن خلق الله: مبني على تصور لوجود الله من جنس وجود المحدثات، أي: ...
- age screen hits: none
- child_explanation_ar: الله هو الذي خلق كل شيء، ولم يخلقه أحد. كل شيء حولنا له بداية، أما الله فليس له بداية، وهو موجود دائما.
- child_explanation_en: Allah is the One who made everything, and nobody made Him. Everything around us has a beginning, but Allah has no beginning; He has always been there.
- child_explanation_older_ar: هذا السؤال قديم ويتكرر بصيغ مختلفة. السؤال يفترض أن الله مثل المخلوقات التي لم تكن موجودة ثم وجدت، وهذا خطأ. الله لا أول له ولا خالق له، وهو خالق كل شيء، ولا يمكن أن يكون للخالق خالق، وإلا لم تنته سلسلة الخالقين أبدا.
- child_explanation_older_en: This is an old question that keeps coming back in new words. It assumes Allah is like created things, which did not exist and then came to be. That is a mistake. Allah has no beginning and no creator; He is the Creator of everything. The Creator cannot have a creator, otherwise the chain of creators would never end.
- flags:
  - Doubt-type (new atheism) -> 10-13.
  - Excerpt is paragraph 6 of 6 of the short answer (starts "والاعتراض"); paragraphs 1-5 are omitted on purpose.
  - title_ar is the long question under السؤال, not the short TOC title ("كيف نجيب على سؤال: من خلق الله؟").
- [ ] ok

## Q9 (printed p.64) - Do Muslims worship the Kaaba and the Black Stone?

- source_url: `https://dawa.center/file/7937#p64`
- renders: `backend/session_moral_context/content/tools/.cache/bayyinat/q009-pdf0065-p64.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q009-pdf0066-p65.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q009-pdf0067-pNone.png` (+4 more)
- values: prayer; age_band: all; content_level: B
- related: (none)
- title_ar: المسلمون يعبدون الكعبة؛ وهي حجارة مبنية، ويعبدون الحجر الأسود؛ فيسجدون عليه، ويقبلونه؛ فكيف يكون ذلك؟
- keywords_ar: المسلمون يعبدون غير الله تعالى.
- arabic_text (first 15 words, 61 words, 1 para): استقبال المسلمين للكعبة في الصلاة ليس عبادة لها؛ إذ المسلمون لا يعبدون إلا الله وحده، ...
- age screen hits: [crime] "والذبح"
- child_explanation_ar: المسلمون لا يعبدون الكعبة ولا الحجر الأسود، بل يعبدون الله وحده. الكعبة هي الجهة التي نتوجه إليها في الصلاة، والعبادة كلها لله وحده.
- child_explanation_en: Muslims do not worship the Kaaba or the Black Stone; they worship Allah alone. The Kaaba is the direction we face in prayer, and all worship is for Allah alone.
- child_explanation_older_ar: التوجه إلى الكعبة في الصلاة ليس عبادة لها. العبادة كلها، مثل المحبة والخوف والرجاء والسجود والطواف، لا يصرفها المسلمون إلا لله وحده، لا لحجر ولا لأي مخلوق؛ سواء كان الحجر الأسود أو غيره من حجارة الكعبة.
- child_explanation_older_en: Facing the Kaaba in prayer is not worshipping it. All worship, such as love, fear, hope, prostration and circling the Kaaba, Muslims direct to Allah alone, never to a stone or any created thing, whether the Black Stone or any other stone of the Kaaba.
- flags:
  - Para 2 cut (--paras 1): the text layer dropped the honorific after "إبراهيم" in it, so the bank never carries that gap. Lead: if para 2 is wanted, restore the honorific against the page before review and re-draft with --paras 1-2. The explanations no longer mention Ibrahim.
- [ ] ok

## Q12 (printed p.81) - What does Allah gain when we worship Him?

- source_url: `https://dawa.center/file/7937#p81`
- renders: `backend/session_moral_context/content/tools/.cache/bayyinat/q012-pdf0082-p81.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q012-pdf0083-p82.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q012-pdf0084-p83.png` (+4 more)
- values: gratitude; age_band: all; content_level: B
- related: (none)
- title_ar: ما الفائدة التي تعود إلى الله إذا عبدناه؟
- keywords_ar: ما الحكمة من طلب الرب أن يعبده الخلق؟
- arabic_text (first 15 words, 71 words, 2 para): العبادة واجب على الخلق، وهم محتاجون إليها، والله تعالى تفضل بها على خلقه، وشرفهم وكرمهم ...
- age screen hits: [sects_disbelief] "بكفره"
- child_explanation_ar: الله لا يحتاج إلى عبادتنا، نحن الذين نحتاج إليها. العبادة هدية من الله لنا، تنفعنا نحن وتجعلنا أقرب إليه.
- child_explanation_en: Allah does not need our worship; we are the ones who need it. Worship is a gift from Allah to us; it helps us and brings us closer to Him.
- child_explanation_older_ar: العبادة واجب على الخلق وهم محتاجون إليها، والله تفضل بها على عباده وشرفهم بها؛ فخيرها يعود على العابد نفسه، ولا يضر من يعصي إلا نفسه. ومع ذلك فالله يحب أن يطاع ويعبد ويحمد، لأنه يستحق المحبة لذاته ولنعمه، وغاية المحبة والخضوع له هي العبادة.
- child_explanation_older_en: Worship is a duty for created beings, and they are the ones who need it. Allah honoured His servants by giving it to them, so its good returns to the worshipper, and whoever disobeys harms only himself. At the same time Allah loves to be obeyed, worshipped and praised, because He deserves love for who He is and for His blessings, and the fullest love and humility before Him is worship.
- flags:
  - Para 1 mentions "الكافر بكفره" (deny-list sects_disbelief); kept at age all because it is one clause of a basic answer. Lead decides.
- [ ] ok

## Q14 (printed p.89) - Are angels real beings or just symbols?

- source_url: `https://dawa.center/file/7937#p89`
- renders: `backend/session_moral_context/content/tools/.cache/bayyinat/q014-pdf0090-p89.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q014-pdf0091-p90.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q014-pdf0092-p91.png` (+1 more)
- values: (none); age_band: all; content_level: B
- related: (none)
- title_ar: هل الملائكة كائنات حقيقية، أم معنوية مجازية؟
- keywords_ar: هل عالم الملائكة عالم حقيقي؟ | من هم الملائكة؟ | ما حقيقة الملائكة؟ | وجود الملائكة.
- arabic_text (first 15 words, 50 words, 1 para): الملائكة مخلوقات مادية حقيقية تدرك بالحواس، وليست مخلوقات معنوية مجازية تدل على الخير أو الصلاح، ...
- age screen hits: none
- child_explanation_ar: الملائكة مخلوقات حقيقية خلقها الله، وليست مجرد رمز للخير. أخبرنا الله عنها في القرآن، وأعطاها أعمالا تقوم بها.
- child_explanation_en: Angels are real beings that Allah created, not just a symbol of goodness. Allah told us about them in the Quran and gave them real tasks to do.
- child_explanation_older_ar: الملائكة مخلوقات حقيقية لها وجود قائم، وليست معاني مجازية تدل على الخير أو الصلاح. دل على ذلك القرآن والسنة؛ فالله خاطبهم ووصفهم بأوصاف وكلفهم بمهام لا تقوم بها إلا مخلوقات حقيقية.
- child_explanation_older_en: Angels are real created beings with a real existence, not figures of speech standing for goodness. The Quran and the Sunnah show this: Allah addressed them, described them, and gave them tasks that only real beings could carry out.
- flags:
  - none beyond the common check
- [ ] ok

## Q17 (printed p.98) - Why do angels do tasks when Allah can just say 'Be' and it is?

- source_url: `https://dawa.center/file/7937#p98`
- renders: `backend/session_moral_context/content/tools/.cache/bayyinat/q017-pdf0099-p98.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q017-pdf0100-p99.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q017-pdf0101-p100.png` (+1 more)
- values: (none); age_band: all; content_level: B
- related: (none)
- title_ar: ما الحكمة من قيام الملائكة بأعمالها، مع قدرة الله أن يقول للشيء: كن، فيكون؟
- keywords_ar: أعمال الملائكة. | قدرة الله.
- arabic_text (first 15 words, 71 words, 1 para): الله سبحانه وتعالى غني عن الملائكة وعن غيرهم من المخلوقات، قادر على إنفاذ أمره بكن، ...
- age screen hits: none
- child_explanation_ar: الله لا يحتاج إلى الملائكة، فهو قادر على كل شيء. لكنه خلق الملائكة وأعطاها أعمالا، وهذا يدل على عظمة ملكه وحكمته.
- child_explanation_en: Allah does not need the angels; He can do anything. But He created the angels and gave them tasks, and this shows the greatness of His kingdom and His wisdom.
- child_explanation_older_ar: الله غني عن الملائكة وعن كل المخلوقات، وقادر على أن يقول للشيء كن فيكون. الملائكة تعمل بعلمه ومشيئته وأمره، وتكليفها بالأعمال من تمام ملكه وعظمته، لا بسبب عجز أو حاجة. وهو الذي خلق الملائكة وخلق فيها القدرة على ما وكلها به.
- child_explanation_older_en: Allah has no need of the angels or of any creature, and He can say to a thing 'Be' and it is. The angels act by His knowledge, will and command, and giving them tasks is part of the completeness of His kingdom and greatness, not a sign of any weakness or need. He is the One who created the angels and created in them the ability to do what He assigned them.
- flags:
  - none beyond the common check
- [ ] ok

## Q19 (printed p.104) - Prostration is only for Allah, so why did the angels prostrate to Adam?

- source_url: `https://dawa.center/file/7937#p104`
- renders: `backend/session_moral_context/content/tools/.cache/bayyinat/q019-pdf0105-p104.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q019-pdf0106-p105.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q019-pdf0107-p106.png`
- values: (none); age_band: all; content_level: B
- related: (none)
- title_ar: السجود لا يكون إلا لله؛ فلماذا سجدت الملائكة لآدم؟
- keywords_ar: السجود لآدم.
- arabic_text (first 15 words, 48 words, 1 para): أن سجود الملائكة لآدم لم يكن سجود عبادة؛ فسجود العبادة لا يكون إلا لله وحده، ...
- age screen hits: none
- child_explanation_ar: سجود الملائكة لآدم لم يكن عبادة له، بل كان تحية واحتراما بأمر الله. أما اليوم فالسجود في الإسلام لا يكون إلا لله وحده.
- child_explanation_en: The angels' prostration to Adam was not worship; it was a greeting and a sign of respect, by Allah's command. In Islam today, prostration is only for Allah.
- child_explanation_older_ar: سجود العبادة لا يكون إلا لله وحده. أما سجود الملائكة لآدم فكان سجود تحية واحترام وإكرام، وكان هذا النوع من السجود جائزا في الأمم السابقة. ثم نسخه الإسلام، فلا يجوز لمسلم أن يسجد لأي مخلوق أبدا.
- child_explanation_older_en: Prostration of worship is for Allah alone. The angels' prostration to Adam was a prostration of greeting, respect and honour, and this kind of prostration was allowed in earlier nations. Islam then abolished it, so a Muslim may never prostrate to any created being.
- flags:
  - keywords_ar[1] "الملائكة تسجد لآدم ." (dropped honorific before the full stop) removed from the item by the curator script; drafted with --allow-dropped-symbols because of it.
  - Excerpt starts with "أن سجود..." (answer to a leading clause); check the page that nothing precedes it in the paragraph.
- [ ] ok

## Q27 (printed p.135) - Why can't the Quran be written by humans or by the Prophet himself?

- source_url: `https://dawa.center/file/7937#p135`
- renders: `backend/session_moral_context/content/tools/.cache/bayyinat/q027-pdf0136-p135.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q027-pdf0137-p136.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q027-pdf0138-p137.png` (+2 more)
- values: (none); age_band: 10-13; content_level: B
- related: (none)
- title_ar: ادعاء أن القرآن مصدره البشر
- keywords_ar: مصدر القرآن الكريم. | القرآن كلام الله.
- arabic_text (first 15 words, 104 words, 4 para): 1) عقلاء المشركين - من أهل الكتاب ومن غيرهم - يعلمون أن اليهود أو النصارى ...
- age screen hits: [sects_disbelief] "المشركين"
- child_explanation_ar: القرآن كلام الله، وليس من كلام البشر ولا من تأليف النبي صلى الله عليه وسلم. لا يستطيع أحد من الناس أن يأتي بمثله، وليس فيه أي خطأ أو اختلاف.
- child_explanation_en: The Quran is the word of Allah, not the words of people and not written by the Prophet (peace be upon him). No human can produce anything like it, and it has no mistakes or contradictions in it.
- child_explanation_older_ar: الجواب المختصر يذكر أربعة أدلة: أن عقلاء المشركين وأهل الكتاب أنفسهم كانوا يعلمون أن اليهود والنصارى لا يمكن أن يكونوا مصدر القرآن، لأنهم كانوا أشد الناس معارضة له؛ وأن في القرآن إعجازا تاريخيا وتشريعيا وبلاغيا وعلميا لا يقدر عليه بشر في ذلك الزمان؛ وأن القرآن فيه عتاب للنبي صلى الله عليه وسلم، ولو كان من تأليفه ما عاتب نفسه؛ وأنه لا خطأ ولا اختلاف فيه مع عجز العالم كله عن الإتيان بسورة من مثله.
- child_explanation_older_en: The short answer gives four proofs: the thoughtful people among the Prophet's opponents, including the People of the Book, knew that Jews and Christians could not be the source of the Quran, since they opposed it most of all; the Quran contains historical, legal, literary and scientific marvels that no human of that time could produce; the Quran contains gentle rebukes of the Prophet (peace be upon him), which he would not have written about himself; and it has no error or contradiction, while the whole world has been unable to produce even one chapter like it.
- flags:
  - Re-extracted after the extractor fix: the list markers read "1)".."4)" (page order) and "الادعاء" is restored from the glyph trace ([alef x1]: check the page). The four numbered points are four paragraphs now (they were one), so the draft is --paras 1-4 and warns "the plan allows 1-3"; same 100 words as before. Lead: confirm, or cut point 4.
  - title_ar is the TOC title: the question text has a verse hole [الحاقة: 40] and a dropped honorific, which title_ar cannot carry (drafted with --allow-dropped-symbols because of that honorific).
  - Deny hit [sects_disbelief] "المشركين" -> 10-13.
  - Plan first pick ("the source of the Quran").
- [ ] ok

## Q100 (printed p.460) - Is Islam a religion only for Arabs?

- source_url: `https://dawa.center/file/7937#p460`
- renders: `backend/session_moral_context/content/tools/.cache/bayyinat/q100-pdf0461-p460.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q100-pdf0462-p461.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q100-pdf0463-p462.png` (+2 more)
- values: brotherhood; age_band: all; content_level: B
- related: verse:21:107
- title_ar: قد يكون الإسلام صحيحا؛ لكنه دين خاص بالعرب.
- keywords_ar: (none)
- arabic_text (first 15 words, 28 words, 1 para): الإسلام هو الدين الحق، أنزله الله تعالى على نبيه محمد صلى الله عليه وسلم، وبعثه ...
- age screen hits: none
- child_explanation_ar: الإسلام ليس للعرب فقط، بل هو دين لكل الناس في كل مكان. أرسل الله النبي محمدا صلى الله عليه وسلم إلى البشر كلهم.
- child_explanation_en: Islam is not only for Arabs; it is a religion for all people everywhere. Allah sent Prophet Muhammad (peace be upon him) to all of mankind.
- child_explanation_older_ar: الإسلام هو الدين الحق الذي أنزله الله على نبيه محمد صلى الله عليه وسلم، وبعثه إلى الناس كلهم والجن أيضا، لا إلى العرب وحدهم. فكل إنسان مدعو إلى اتباعه والإيمان برسالته، مهما كانت لغته أو بلده.
- child_explanation_older_en: Islam is the true religion that Allah sent down to His Prophet Muhammad (peace be upon him), and He sent him to all people, and to the jinn too, not to the Arabs alone. Every person, whatever their language or country, is invited to follow him and believe in his message.
- flags:
  - related verse:21:107 is cited in the detailed answer (p.461), not inside the excerpt; keep or drop.
  - keywords_ar is empty (no similar-wordings block on the page).
- [ ] ok

## Q105 (printed p.480) - How can Muslims believe in miracles when science says they are impossible?

- source_url: `https://dawa.center/file/7937#p480`
- renders: `backend/session_moral_context/content/tools/.cache/bayyinat/q105-pdf0481-p480.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q105-pdf0482-p481.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q105-pdf0483-p482.png` (+1 more)
- values: (none); age_band: 10-13; content_level: B
- related: (none)
- title_ar: كيف يؤمن المسلمون بالمعجزات، مع أنها منافية للعلم الحديث، وغير ممكنة الوقوع؟
- keywords_ar: لا نتصور إمكانية وقوع المعجزات؛ لأن الوجود منضبط بنظام صارم، لا يقبل الانخرام.
- arabic_text (first 15 words, 95 words, 3 para): إن الاعتقاد بأن الباري عز وجل خلق الكون، مع الاعتقاد باستحالة أن يخرم نظامه بمعجزة ...
- age screen hits: none
- child_explanation_ar: الله هو الذي خلق الكون كله، فهو قادر على أن يفعل ما هو أصغر من ذلك، مثل المعجزات. المعجزة شيء غير عادي لنا، لكنها ليست صعبة على الله.
- child_explanation_en: Allah created the whole universe, so He can surely do something smaller than that, like a miracle. A miracle is unusual for us, but it is not hard for Allah.
- child_explanation_older_ar: من يؤمن أن الله خلق الكون ثم يقول إن المعجزة مستحيلة يقع في تناقض، لأن خلق الكون من البداية أعظم من المعجزة. والعلم الطبيعي إن لم يستطع إثبات المعجزات فهو أعجز عن نفيها. والمعجزة لا تخالف العقل ولا قانون السببية، بل هي خلق شيء من مادة لم تجر العادة أن يخلق منها؛ فهي مستحيلة في عادة الناس، لكنها ليست مستحيلة في العقل، وهي داخلة تحت قدرة الله.
- child_explanation_older_en: Someone who believes Allah created the universe but says a miracle is impossible contradicts himself, because creating the universe in the first place is greater than any miracle. And if natural science cannot prove miracles, it is even less able to disprove them. A miracle does not go against reason or cause and effect; it is the creation of something from material it is not usually created from. It is impossible by human habit, but not impossible to reason, and it is well within Allah's power.
- flags:
  - Re-extracted after the extractor fix: "بمعجزة -: تناقض" is one sentence again (a "-:" is no longer a list marker) and the excerpt is the page's 3 paragraphs (--paras 1-3), same words as before.
  - Doubt-type -> 10-13. Dense wording; the older explanation carries it.
- [ ] ok

## Q181 (printed p.841) - Why is my dua not answered, or answered late?

- source_url: `https://dawa.center/file/7937#p841`
- renders: `backend/session_moral_context/content/tools/.cache/bayyinat/q181-pdf0842-p841.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q181-pdf0843-p842.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q181-pdf0844-p843.png` (+2 more)
- values: trust-in-allah, patience; age_band: all; content_level: B
- related: (none)
- title_ar: دعوت الله بالشفاء وما زلت مريضا، ودعوته بالغنى وما زلت فقيرا، ودعوته بالنصر وما زلت مظلوما؛ فلماذا تأخرت إجابة الدعاء؟
- keywords_ar: لماذا ندعو، ولا يستجاب لنا؟ | ما الفائدة من الدعاء؛ إذا كان لا يستجاب لنا؟
- arabic_text (first 15 words, 66 words, 2 para): العبد مأمور بالتسليم والخضوع لله تعالى، مع السعي والأخذ بالأسباب؛ كالذهاب للطبيب مثلا إذا مرض، ...
- age screen hits: none
- child_explanation_ar: الدعاء عبادة جميلة لا نخسر فيها أبدا، حتى لو لم نر الإجابة بسرعة. ندعو الله ونثق به، ونعمل بالأسباب أيضا، مثل الذهاب إلى الطبيب عند المرض.
- child_explanation_en: Dua is a beautiful act of worship in which we never lose, even if we do not see the answer quickly. We ask Allah and trust Him, and we also do our part, like going to the doctor when we are ill.
- child_explanation_older_ar: المسلم مأمور بالتسليم لله مع الأخذ بالأسباب؛ فإذا مرض ذهب إلى الطبيب ودعا ربه، وأحسن الظن بالله ووثق بما عنده. والدعاء عبادة وصفقة رابحة لا يخسر فيها العبد أبدا إذا تحققت شروطها، وأصله التذلل لله، فلا نتعامل معه كتجربة نقيم نتائجها بحسابنا البشري القاصر.
- child_explanation_older_en: A Muslim is asked to submit to Allah while also doing what he can: if he is ill he goes to the doctor and he asks his Lord, thinking well of Allah and trusting what is with Him. Dua is worship and a deal in which the servant never loses when its conditions are met. At its heart it is humility before Allah, so we do not treat it like an experiment whose results we grade with our limited human judgement.
- flags:
  - Printed page in number ("p.841") vs TOC page 861: the extractor uses page headers, TOC drifts; confirm on the render.
- [ ] ok

## Q198 (printed p.923) - Why does Islam allow slaughtering animals? Isn't it cruel?

- source_url: `https://dawa.center/file/7937#p923`
- renders: `backend/session_moral_context/content/tools/.cache/bayyinat/q198-pdf0924-p923.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q198-pdf0925-p924.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q198-pdf0926-p925.png` (+1 more)
- values: kindness-to-animals, mercy; age_band: 10-13; content_level: B
- related: (none)
- title_ar: إن الإسلام يبيح قتل الحيوان بطريقة الذبح، وطريقة الذبح مؤذية للنفس.
- keywords_ar: الحكمة من تذكية الحيوان.
- arabic_text (first 15 words, 37 words, 2 para): ذبح الحيوان بتذكيته هي الطريقة الأمثل لإزهاق روحه، والانتفاع به بعد ذلك؛ وذلك أن فيها ...
- age screen hits: [crime] "الذبح", [crime] "ذبح", [crime] "قتل"
- child_explanation_ar: الإسلام يأمرنا أن نرحم الحيوان حتى عند ذبحه للطعام. الطريقة الإسلامية في الذبح تريح الحيوان من الألم الذي تسببه طرق أخرى، وتجعل لحمه طيبا ونظيفا.
- child_explanation_en: Islam tells us to be kind to animals, even when they are slaughtered for food. The Islamic way of slaughter spares the animal the suffering caused by other methods, and makes its meat clean and good.
- child_explanation_older_ar: الذبح الشرعي، وهو التذكية، هو الطريقة الأمثل لإزهاق روح الحيوان والانتفاع به، لأن فيه تطهيرا وتطييبا للحمه. وفيه أيضا إراحة للحيوان من المعاناة التي تسببها الطرق الحديثة التي لا تقوم على الإحسان إليه. فالإسلام لا يبيح إيذاء الحيوان، بل يأمر بالرحمة به حتى في هذا الموقف.
- child_explanation_older_en: Islamic slaughter, called tadhkiyah, is the best way to end an animal's life and make use of it, because it purifies the meat and makes it wholesome. It also spares the animal the suffering caused by modern methods that are not based on kindness to it. Islam does not allow hurting animals; it commands mercy to them even at this moment.
- flags:
  - Deny hits [crime] "ذبح", "قتل" (title) -> 10-13. Paragraph 3 (sharpening the blade, forbidden tools) left out on purpose; paras 1-2 kept.
  - Lead decides whether slaughter belongs in a children's bank at all.
- [ ] ok

## Q199 (printed p.926) - Why does Islam forbid alcohol?

- source_url: `https://dawa.center/file/7937#p926`
- renders: `backend/session_moral_context/content/tools/.cache/bayyinat/q199-pdf0927-p926.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q199-pdf0928-p927.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q199-pdf0929-p928.png` (+3 more)
- values: (none); age_band: 10-13; content_level: B
- related: (none)
- title_ar: كيف يحرم الإسلام الخمر - وسائر المشروبات الكحولية المسكرة - مع أنه شراب يشربه كثير من الناس اليوم، خاصة في العالم الغربي؟
- keywords_ar: الحكمة من تحريم الخمر والمسكرات.
- arabic_text (first 15 words, 54 words, 1 para): إن الحكمة من تحريم الخمر جاء النص القرآني بإيضاحها أتم الإيضاح؛ حيث بين الله تعالى ...
- age screen hits: [crime] "الخمر", [hell_grave] "بالمنكرات"
- child_explanation_ar: الله حرم الخمر لأنها تضر العقل وتجعل الإنسان يقول ويفعل أشياء سيئة. الخمر تجعل الناس يتخاصمون، وتبعدهم عن ذكر الله وعن الصلاة. الإسلام يحمي عقولنا.
- child_explanation_en: Allah forbade alcohol because it harms the mind and makes a person say and do bad things. It makes people quarrel and keeps them away from remembering Allah and from prayer. Islam protects our minds.
- child_explanation_older_ar: القرآن بين الحكمة من تحريم الخمر بوضوح: فهي توقع العداوة والبغضاء بين الناس، وتصد عن ذكر الله وعن الصلاة، لأنها تضعف عقل شاربها وتجعله يأتي بالمنكرات من الأقوال والأفعال. ومن أعظم مقاصد الشريعة حفظ العقل.
- child_explanation_older_en: The Quran explains clearly why alcohol is forbidden: it causes enmity and hatred between people, and it keeps a person from remembering Allah and from prayer, because it weakens the drinker's mind and leads him to bad words and deeds. Protecting the mind is one of the greatest aims of Islamic law.
- flags:
  - Deny hit [crime] "الخمر" -> 10-13; "بالمنكرات" hit is a false positive (deny stem منكر).
  - Only para 1 kept; paras 2-3 are a verse (5:90-92) drawn as glyphs, not linked (verse not in bank).
- [ ] ok

## Q200 (printed p.931) - Why does Islam forbid eating pork?

- source_url: `https://dawa.center/file/7937#p931`
- renders: `backend/session_moral_context/content/tools/.cache/bayyinat/q200-pdf0932-p931.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q200-pdf0933-p932.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q200-pdf0934-p933.png` (+1 more)
- values: (none); age_band: all; content_level: B
- related: (none)
- title_ar: كيف يحرم الإسلام لحم الخنزير، مع أنه حيوان شهي الطعم؟
- keywords_ar: الحكمة من تحريم لحم الخنزير.
- arabic_text (first 15 words, 23 words, 1 para): إن تحريم لحم الخنزير تحقيق للصحة السليمة، والعافية للمرء في حياته؛ وهذا يحقق مقصد الشرع ...
- age screen hits: none
- child_explanation_ar: الله حرم لحم الخنزير لأنه يريد لنا الصحة والعافية. الإسلام يحرص على حفظ حياة الإنسان وصحته.
- child_explanation_en: Allah forbade pork because He wants us to be healthy and well. Islam cares about protecting people's lives and health.
- child_explanation_older_ar: تحريم لحم الخنزير يحقق الصحة السليمة والعافية للإنسان في حياته. وهذا يحقق مقصدا من مقاصد الشريعة وهو حفظ النفس، الذي هو واحد من الضروريات الخمس التي جاء الإسلام لحمايتها.
- child_explanation_older_en: Forbidding pork protects a person's health and wellbeing in life. This serves one of the aims of Islamic law, protecting life, which is one of the five essentials that Islam came to safeguard.
- flags:
  - Printed page "p.931" vs TOC 952; confirm on the render.
- [ ] ok

## Q201 (printed p.934) - Is Islam a strict, extreme religion?

- source_url: `https://dawa.center/file/7937#p934`
- renders: `backend/session_moral_context/content/tools/.cache/bayyinat/q201-pdf0935-p934.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q201-pdf0936-p935.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q201-pdf0937-p936.png` (+1 more)
- values: (none); age_band: 10-13; content_level: B
- related: (none)
- title_ar: إن الدين الإسلامي وأتباعه يغلب عليهم التشدد، ونحن نحتاج إلى المسلمين المعتدلين، والإسلام الوسطي المعتدل.
- keywords_ar: مفهوم التشدد والاعتدال في الإسلام.
- arabic_text (first 15 words, 78 words, 2 para): التشدد في الدين ليس هو التمسك به والحرص عليه؛ وإنما هو تجاوز الحد المشروع في ...
- age screen hits: none
- child_explanation_ar: الإسلام دين الاعتدال والرحمة والعدل. التمسك بالدين شيء جميل مطلوب من كل مسلم، أما التشدد فهو الزيادة على ما أمر الله به، وهذا ليس من الدين.
- child_explanation_en: Islam is a religion of balance, mercy and justice. Holding firmly to the religion is a good thing asked of every Muslim; extremism means going beyond what Allah commanded, and that is not part of the religion.
- child_explanation_older_ar: التشدد ليس هو التمسك بالدين والحرص عليه، بل هو تجاوز الحد المشروع في تطبيق الأوامر، أو الابتداع في الدين بما ليس منه بحجة المبالغة في العبادة. أما التمسك بالدين فمطلوب من كل مسلم. والإسلام بأحكامه وأصوله هو دين العدل والاعتدال والرحمة، ونفخر به ولا نخجل منه بسبب ضغط الإعلام.
- child_explanation_older_en: Extremism is not the same as holding firmly to the religion and caring about it. It means going beyond the lawful limit in applying the commands, or inventing things in the religion in the name of extra devotion. Holding firmly to the religion is asked of every Muslim. Islam, with its rulings and principles, is the religion of justice, balance and mercy; we are proud of it and do not feel ashamed of it because of media pressure.
- flags:
  - Doubt-type with adult framing ("we need moderate Muslims") -> 10-13. Borderline child-usable; drop if the set is trimmed.
- [ ] ok

## Q203 (printed p.944) - What do I gain from Islam?

- source_url: `https://dawa.center/file/7937#p944`
- renders: `backend/session_moral_context/content/tools/.cache/bayyinat/q203-pdf0945-p944.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q203-pdf0946-p945.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q203-pdf0947-p946.png` (+5 more)
- values: contentment; age_band: all; content_level: B
- related: verse:13:28
- title_ar: لماذا أسلم؟ ما الذي سأستفيده في حال دخولي دين الإسلام؟
- keywords_ar: ما الذي يجعلني أختار الإسلام من بين سائر الأديان الأخرى؟ | ما الذي يميز الإسلام عن غيره من الأديان؟
- arabic_text (first 15 words, 40 words, 2 para): الإسلام هو الدين الحق الذي يجب على الإنسان اعتناقه، والتدين به. ومن يسلم، سيجد في ...
- age screen hits: none
- child_explanation_ar: الإسلام هو الدين الحق الذي يرضي الله. من يعيش بالإسلام يجد إجابات لأسئلته الكبيرة، ويشعر بالطمأنينة والراحة في قلبه.
- child_explanation_en: Islam is the true religion that pleases Allah. Whoever lives by Islam finds answers to life's big questions and feels peace and calm in the heart.
- child_explanation_older_ar: الإسلام هو الدين الحق الذي يجب على الإنسان أن يعتنقه. ومن يسلم يجد في الإسلام إجابات عن الأسئلة الكبرى التي تحيره، ويجد أنه يلبي احتياجاته المادية والمعنوية والجسمية والروحية، ويحقق له الطمأنينة والسكينة النفسية.
- child_explanation_older_en: Islam is the true religion that a person ought to embrace. Whoever becomes Muslim finds in Islam the answers to the big questions that puzzle him, finds that it meets his material, moral, bodily and spiritual needs, and finds inner peace and calm.
- flags:
  - related verse:13:28 is cited in the detailed answer, not inside the excerpt; keep or drop.
- [ ] ok

## Q204 (printed p.951) - What if I cannot practise Islam 100 percent?

- source_url: `https://dawa.center/file/7937#p951`
- renders: `backend/session_moral_context/content/tools/.cache/bayyinat/q204-pdf0952-p951.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q204-pdf0953-p952.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q204-pdf0954-p953.png` (+4 more)
- values: (none); age_band: 10-13; content_level: B
- related: (none)
- title_ar: ماذا لو لم أستطع أن أطبق الإسلام بنسبة (100%)؟
- keywords_ar: أجد صعوبة في تطبيق الإسلام. | الإسلام دين خيالي غير قابل للتطبيق، وليس ملائما لحياة الناس.
- arabic_text (first 15 words, 71 words, 3 para): الإسلام دين السماحة واليسر، ولا يلزم من أسلم أن يطبق كافة أحكام وتعاليم الإسلام، وإنما ...
- age screen hits: none
- child_explanation_ar: الإسلام دين سهل ورحيم. لا يلزم أن نطبق كل شيء مرة واحدة؛ نحافظ على أركان الإسلام الخمسة، ونؤمن بأركان الإيمان الستة، ونتعلم الباقي شيئا فشيئا.
- child_explanation_en: Islam is an easy and gentle religion. We do not have to apply everything at once: we keep the five pillars of Islam, believe in the six pillars of faith, and learn the rest little by little.
- child_explanation_older_ar: الإسلام دين السماحة واليسر، ولا يلزم من أسلم أن يطبق كل الأحكام والتعاليم مرة واحدة. لكن للإسلام أركانا أساسية نحافظ عليها: أركان الإسلام الخمسة، وهي الشهادتان وإقام الصلاة وإيتاء الزكاة وصوم رمضان وحج البيت؛ وأركان الإيمان الستة التي نؤمن بها، وهي الإيمان بالله وملائكته وكتبه ورسله واليوم الآخر والقدر؛ ثم نتعلم الباقي شيئا فشيئا.
- child_explanation_older_en: Islam is a religion of ease and gentleness, and a new Muslim is not required to apply every ruling and teaching at once. But Islam has basic pillars that we keep: the five pillars of Islam, which are the two testimonies of faith, prayer, zakah, fasting Ramadan and Hajj; and the six pillars of faith that we believe in, which are belief in Allah, His angels, His books, His messengers, the Last Day and divine decree. Then we learn the rest little by little.
- flags:
  - Explanations reworded after review: pillars of faith are believed, not "done"; the "not a Muslim without them" and "فورا" wordings removed. age_band 10-13: the source lists Hajj without "لمن استطاع".
  - Pillars list is Level A material inside a Level B answer; kept B because of the framing ("need not apply everything").
  - Mentions القدر in the pillars list only (aqidah sensitive list): no explanation of qadar is given.
- [ ] ok

## Q205 (printed p.957) - Why do Muslims pray five times a day?

- source_url: `https://dawa.center/file/7937#p957`
- renders: `backend/session_moral_context/content/tools/.cache/bayyinat/q205-pdf0958-p957.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q205-pdf0959-p958.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q205-pdf0960-p959.png` (+3 more)
- values: prayer; age_band: all; content_level: B
- related: verse:29:45
- title_ar: أليس في الصلاة خمس مرات مشقة على الإنسان، وقطع له عن أعماله؟ ألا تكفي صلاة واحدة، كما يوجد في أديان أخرى؛ تتحقق بها المقاصد المرجوة من الصلاة، ولا يكون فيها انقطاع عن الحياة؟
- keywords_ar: المسلمون يصلون خمس مرات يوميا؛ ألا ترون هذا كثيرا في زماننا المعاصر، زمن العلم والتكنولوجيا والأعمال التجارية المعقدة؟
- arabic_text (first 15 words, 141 words, 3 para): الإسلام له نظرة شاملة للحياة التي ينبغي للإنسان أن يحياها؛ فهو يسعى لإيجاد الحياة الطيبة ...
- age screen hits: [punishment] "وقطع"
- child_explanation_ar: الصلاة تربطنا بالله الذي خلقنا، في كل يوم. الصلوات الخمس فيها خير كبير لجسمنا وقلبنا، ولا تأخذ وقتا طويلا، بل تعطينا راحة ونشاطا.
- child_explanation_en: Prayer connects us with Allah, who created us, every day. The five prayers bring great good to our body and heart. They do not take long; they give us rest and new energy.
- child_explanation_older_ar: الإسلام يريد للإنسان حياة طيبة متوازنة يرتبط فيها بربه كل يوم من خلال الصلاة. فالصلاة عبادة يؤديها المسلم لله، ولها فوائد على جسده وقلبه وعقله وروحه، وعلى المجتمع كله. والصلوات الخمس بينها وقت طويل، وأداء الصلاة لا يحتاج وقتا كثيرا، بل هو وقت للراحة وتجديد النشاط يجعل الإنسان ينتج أكثر في عمله وحياته.
- child_explanation_older_en: Islam wants a person to have a good, balanced life in which he connects with his Lord every day through prayer. Prayer is worship a Muslim offers to Allah, and it benefits his body, heart, mind and soul, and the whole community. There is a long gap between the five prayers, and praying does not take much time; it is a time of rest and renewed energy that helps a person do better in his work and life.
- flags:
  - Longest excerpt (3 paragraphs, ~170 words); within the 1-3 rule. Cut to paras 1-2 with --paras if too long for a card.
  - related verse:29:45 is cited in the detailed answer (p.960), not inside the excerpt.
  - Plan first pick ("why we pray").
- [ ] ok

## Q206 (printed p.962) - Why did Allah make zakah a duty?

- source_url: `https://dawa.center/file/7937#p962`
- renders: `backend/session_moral_context/content/tools/.cache/bayyinat/q206-pdf0963-p962.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q206-pdf0964-p963.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q206-pdf0965-p964.png` (+2 more)
- values: charity, generosity; age_band: all; content_level: B
- related: (none)
- title_ar: ما الحكمة من تشريع الزكاة؟ ففيها مشقة على النفوس؛ بأخذ مالهم وإعطائه غيرهم، وفي التشريعات المالية والضرائب وغيرها ما يكفي.
- keywords_ar: (none)
- arabic_text (first 15 words, 63 words, 1 para): الإسلام جاء بأفضل الأحكام والشرائع التي تحقق الخير للإنسان في حياته، وبعد مماته؛ ومن ذلك ...
- age screen hits: none
- child_explanation_ar: الزكاة ركن من أركان الإسلام، وفيها خير للجميع. من يعطي الزكاة يفرح الله به ويبارك له، والمحتاجون يجدون ما يساعدهم.
- child_explanation_en: Zakah is one of the pillars of Islam, and it brings good to everyone. Allah is pleased with the one who gives it and blesses them, and people in need get help.
- child_explanation_older_ar: الإسلام جاء بأفضل الأحكام التي تحقق الخير للإنسان في الدنيا والآخرة، ومنها الزكاة التي شرعت لحكم ومصالح كثيرة. فهي عبادة عظيمة وركن من أركان الإسلام، وخيرها يعود على المزكي نفسه في الدنيا والآخرة، وعلى الفئات المحتاجة التي تأخذها، وعلى المجتمع كله.
- child_explanation_older_en: Islam came with the best rulings, which bring good to people in this life and the next, and zakah is one of them, with many wise purposes. It is a great act of worship and a pillar of Islam; its good returns to the giver in this life and the next, to the needy who receive it, and to the whole community.
- flags:
  - keywords_ar is empty (no similar-wordings block on the page).
- [ ] ok

## Q208 (printed p.968) - Why did Allah make fasting a duty?

- source_url: `https://dawa.center/file/7937#p968`
- renders: `backend/session_moral_context/content/tools/.cache/bayyinat/q208-pdf0969-p968.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q208-pdf0970-p969.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q208-pdf0971-p970.png` (+2 more)
- values: mercy, cooperation; age_band: all; content_level: B
- related: (none)
- title_ar: ما الحكمة من تشريع الصوم؟ وهل مجرد الامتناع عن الشهوات نافع للإنسان؟ خصوصا أن الصوم يتعارض أحيانا مع واجبات الدراسة والعمل وغيرها.
- keywords_ar: (none)
- arabic_text (first 15 words, 106 words, 3 para): فالإسلام جاء بأفضل الأحكام والشرائع التي تحقق الخير للإنسان في حياته، وبعد مماته؛ لأنها شرائع ...
- age screen hits: none
- child_explanation_ar: الصيام عبادة نتقرب بها إلى الله، وفيه خير كثير. الصيام يجعلنا نشعر بالفقراء الذين لا يجدون طعاما، فنرحمهم ونساعدهم.
- child_explanation_en: Fasting is worship that brings us closer to Allah, and it has much good in it. Fasting makes us feel for the poor who have no food, so we show them mercy and help them.
- child_explanation_older_ar: الإسلام جاء بأحكام محكمة من الرب الخالق الذي يعلم ما يصلح الإنسان. والصيام عبادة يتقرب بها المسلم إلى ربه، وقد فرضه الله علينا وعلى الأمم من قبلنا، وهذا دليل على ما فيه من الحكم والفوائد. فالصوم يصلح نفس الإنسان ويحقق التقوى في قلبه، ويجعل الغني يستشعر حال الفقراء فيرحمهم ويحسن إليهم، فيحصل التكافل والتعاون بين أفراد المجتمع.
- child_explanation_older_en: Islam came with wise rulings from the Creator, who knows what is good for people. Fasting is worship that brings a Muslim closer to his Lord. Allah made it a duty for us and for the nations before us, which shows how much wisdom and benefit it holds. Fasting improves a person's soul and builds taqwa in the heart, and it makes the rich feel what the poor go through, so they treat them with mercy and kindness, and the community grows in solidarity and cooperation.
- flags:
  - Re-extracted after the extractor fix: title_ar now reads "مجرد الامتناع" (alef restored from the glyph trace, [alef x1]: check the page).
  - Excerpt is paras 2-4 of 6; para 1 ("هذا السؤال والشبهة نتيجة قصور النظرة...") omitted, so the excerpt starts with "فالإسلام". Acceptable paragraph boundary; confirm.
  - keywords_ar is empty (no similar-wordings block on the page).
- [ ] ok

## Q229 (printed p.1074) - Did Islam spread by the sword?

- source_url: `https://dawa.center/file/7937#p1074`
- renders: `backend/session_moral_context/content/tools/.cache/bayyinat/q229-pdf1075-p1074.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q229-pdf1076-p1075.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q229-pdf1077-p1076.png` (+6 more)
- values: good-character; age_band: 10-13; content_level: B
- related: (none)
- title_ar: إن النبي صلى الله عليه وسلم أكره الناس على الدخول في الإسلام، والإسلام إنما انتشر بالسيف.
- keywords_ar: تفسير عوامل انتشار الإسلام.
- arabic_text (first 15 words, 89 words, 2 para): الإسلام لم ينتشر بالسيف، وإنما انتشر بالدعوة والحجة، وإذا كان للفتح أثر في انتشار الإسلام، ...
- age screen hits: [jihad] "بالسيف"
- child_explanation_ar: الإسلام لم ينتشر بالقوة، بل انتشر بالدعوة والكلمة الطيبة والحجة. الناس رأوا أخلاق المسلمين ودينهم الجميل فأحبوه ودخلوا فيه.
- child_explanation_en: Islam did not spread by force; it spread through calling people to it with good words and clear reasons. People saw the Muslims' good character and their beautiful religion, so they loved it and joined it.
- child_explanation_older_ar: الإسلام انتشر بالدعوة والحجة لا بالسيف. وإذا كان لفتح البلاد أثر، فلأن المسلمين رحلوا إلى تلك البلاد وأقاموا فيها، فعرف أهلها حقائق الدين من محادثتهم ومعاملتهم. كما أن ظهور الدعاة بمظهر العزة جعل الناس يحترمونهم ويقربون منهم، فلما وجدوهم على دين أفضل وشريعة أحكم وآداب أرفع، آمنوا بما يؤمنون.
- child_explanation_older_en: Islam spread by preaching and proof, not by the sword. Where the opening of lands had an effect, it was because Muslims travelled to those lands and settled there, so the local people learned the truths of the religion from talking and dealing with them. Also, the dignity of those who carried the message made people respect them and draw close, and when they found them on a better religion, a wiser law and higher manners, they came to believe what they believed.
- flags:
  - Deny hit [jihad] "بالسيف" -> 10-13 (draft had age_band all; corrected).
  - Plan first pick ("the sword").
- [ ] ok

## Q230 (printed p.1082) - Does Islam encourage violence?

- source_url: `https://dawa.center/file/7937#p1082`
- renders: `backend/session_moral_context/content/tools/.cache/bayyinat/q230-pdf1083-p1082.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q230-pdf1084-p1083.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q230-pdf1085-p1084.png` (+4 more)
- values: mercy; age_band: 10-13; content_level: B
- related: (none)
- title_ar: أليس الإسلام هو الذي يشجع على العنف، وسفك الدماء والوحشية؛ لأن القرآن يأمر المسلمين بقتل الكفار أينما كانوا؟
- keywords_ar: ما هو مفهوم آية السيف في القرآن؟
- arabic_text (first 15 words, 57 words, 2 para): الإسلام دين السلام؛ فمن مقاصد الإسلام الأساسية التي جاء بها: المحافظة على حق الحياة للإنسان، ...
- age screen hits: [crime] "القتل", [crime] "بقتل", [jihad] "السيف", [sects_disbelief] "الكفار"
- child_explanation_ar: الإسلام دين السلام والرحمة والرفق. الإسلام يحافظ على حياة الناس ويحرم الظلم والإيذاء. ومن يقول غير ذلك لا يعرف الإسلام جيدا.
- child_explanation_en: Islam is a religion of peace, mercy and gentleness. Islam protects people's lives and forbids injustice and harm. Those who say otherwise do not know Islam well.
- child_explanation_older_ar: من مقاصد الإسلام الأساسية المحافظة على حق الحياة وحرمة الدماء، وهو يحب الرفق في الأمر كله، وتشريعاته مليئة بذلك. أما من ينسب العنف إلى الإسلام فهو إما جاهل به أو عدو له؛ يفهمه فهما خاطئا، أو ينتقي مواقف خاطئة لبعض المسلمين ويحمل الإسلام مسؤوليتها. أما الإسلام نفسه فهو دين سلم ورفق ورحمة.
- child_explanation_older_en: Among the basic aims of Islam is protecting the right to life and the sanctity of human blood, and it loves gentleness in all things; its laws are full of this. Those who attach violence to Islam are either ignorant of it or hostile to it: they misunderstand it, or pick out wrong actions by some Muslims and blame Islam for them. Islam itself is a religion of peace, gentleness and mercy.
- flags:
  - Deny hits in title_ar: "قتل الكفار", "سفك الدماء" -> 10-13. The title is the hostile claim; the card should show it as a question, not as our words.
- [ ] ok

## Q242 (printed p.1142) - Did Muslims ever contribute to human progress?

- source_url: `https://dawa.center/file/7937#p1142`
- renders: `backend/session_moral_context/content/tools/.cache/bayyinat/q242-pdf1142-p1141.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q242-pdf1143-p1142.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q242-pdf1144-p1143.png` (+3 more)
- values: seeking-knowledge; age_band: 10-13; content_level: B
- related: verse:20:114
- title_ar: المسلمون الآن في حالة مزرية جدا، وقد تخلفوا عن ركب الثورة العلمية الحديثة؛ فهل قدموا أية إسهامات في نهضة البشرية في أي وقت؟
- keywords_ar: هل الدين سبب في التخلف عن الثورة العلمية الحديثة؟ | هل الدين يدعو للزهد في الدنيا وعدم عمارتها؟ | هل الدين يتعارض مع العلم؟
- arabic_text (first 15 words, 66 words, 1 para): وإذا نظرنا إلى المسلمين الأوائل، نجد أنهم قد امتثلوا هذا الأمر الإلهي، وحرصوا على العلم، ...
- age screen hits: none
- child_explanation_ar: نعم. المسلمون الأوائل أحبوا العلم وعمروا الأرض في وقت كان كثير من الناس في جهل. وكان الملوك في الغرب يرسلون أولادهم إلى بلاد المسلمين مثل الأندلس ليتعلموا ويتعالجوا.
- child_explanation_en: Yes. The early Muslims loved knowledge and built up the world at a time when many people lived in ignorance. Kings in the West used to send their children to Muslim lands like al-Andalus to learn and to be treated by doctors.
- child_explanation_older_ar: الإسلام يدعو إلى العلم والعمل، والمسلمون الأوائل امتثلوا هذا الأمر؛ فحرصوا على العلم وقاموا بعمارة الأرض في وقت كانت فيه الأمم تغرق في الجهالة، حتى كان ملوك الغرب وأمراؤه يرسلون أولادهم إلى بلاد المسلمين كالأندلس للتعلم والعلاج. والنهضة العلمية في الغرب اليوم قامت على ما أخذوه من علماء الإسلام، وهذا معلوم باعتراف مفكري الغرب أنفسهم.
- child_explanation_older_en: Islam calls to knowledge and work, and the early Muslims lived by this: they cared for knowledge and built up the world at a time when nations were sinking in ignorance, so much so that the kings and princes of the West sent their children to Muslim lands such as al-Andalus to study and to be treated. The scientific rise of the West today was built on what it took from Muslim scholars, and this is acknowledged by Western thinkers themselves.
- flags:
  - Dangling antecedent: the excerpt opens with "امتثلوا هذا الأمر الإلهي", which refers to the verse omitted before it (paras 2-7 are verse glyphs), and "إنما قامت" overclaims; the child explanations do not repeat either. Lead: accept as is or re-cut (no paragraph boundary avoids it).
  - Excerpt is para 8 of 9 (starts "وإذا نظرنا"); paras 2-7 are verse glyphs and a broken line. Acceptable boundary; confirm.
  - related verse:20:114 is cited on the page (p.1141), not inside the excerpt; keep or drop.
  - Doubt-type framing ("المسلمون في حالة مزرية") -> 10-13.
- [ ] ok

## Q255 (printed p.1208) - Does religion contradict science?

- source_url: `https://dawa.center/file/7937#p1208`
- renders: `backend/session_moral_context/content/tools/.cache/bayyinat/q255-pdf1209-p1208.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q255-pdf1210-p1209.png`, `backend/session_moral_context/content/tools/.cache/bayyinat/q255-pdf1211-p1210.png` (+3 more)
- values: seeking-knowledge; age_band: 10-13; content_level: B
- related: (none)
- title_ar: هناك أمثلة كثيرة من التعارض بين العلم والدين، تدل على أن الأديان مجرد خرافات وضعها الإنسان من تلقاء نفسه، وأنها - في حقيقة أمرها - وضع أرضي، لا علاقة لها بخالق الكون.
- keywords_ar: الإسلام يخالف الحقائق العلمية.
- arabic_text (first 15 words, 70 words, 2 para): إن العلم التجريبي يتضمن أمورا قطعية، ويتضمن أمورا ظنية، والنقل (الوحي): يتضمن أمورا قطعية، ويتضمن ...
- age screen hits: [punishment] "فالقطعي"
- child_explanation_ar: لا، الدين الصحيح والعلم الصحيح لا يتعارضان. أحيانا يفهم بعض الناس آية فهما خاطئا، أو يأخذون فكرة علمية غير مؤكدة ويقولون إنها تخالف الدين، والخطأ هنا منهم وليس من الدين.
- child_explanation_en: No. True religion and sound science do not clash. Sometimes people misunderstand a verse, or take a scientific idea that is not certain and say it goes against religion. The mistake is theirs, not religion's.
- child_explanation_older_ar: العلم التجريبي فيه أمور قطعية مؤكدة وأمور ظنية غير مؤكدة، والوحي كذلك فيه ما هو قطعي الفهم وما هو ظني الفهم. فالقطعي من أي منهما يقدم على الظني من الآخر، وإذا تعارض ظنيان طلبنا ما يرجح أحدهما. وبهذه القاعدة تظهر أخطاء من يدعون التعارض بين العلم والدين؛ فهم يسيئون فهم النصوص ثم يدعون تعارضها مع العلم، أو يستعملون نظريات علمية بشكل متطرف لمحو الدين.
- child_explanation_older_en: Experimental science contains some things that are certain and some that are only probable, and revelation likewise contains some meanings that are certain and some that are only probable. What is certain from either side comes before what is only probable from the other, and when two probable things clash we look for what tips the balance. Applying this rule shows the errors of those who claim science and religion conflict: they misunderstand the texts and then claim they clash with science, or they push scientific theories to extremes to erase religion.
- flags:
  - Deny hit [punishment] "فالقطعي" is a false positive (stem قطع).
  - Doubt-type -> 10-13.
- [ ] ok
