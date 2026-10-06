# Terms review (Al-Jamhara)

32 items in `backend/session_moral_context/content/items/terms.json`, status `seeded`. Source text is copied from the saved page with a hash check. The explanations are ours. Dropped: 2038 البر (its title is "The Beneficent", a divine name) and 12075 (duplicate of 1366).

English title: per the organisers (5 Oct: "Tawhid" and "Monotheism" are both correct; show both), it is the common transliteration, then the dictionary's own English in brackets, verbatim. Terms whose dictionary English is already the common word keep it alone.

Per item: open the link, check the definition matches, and read our explanation. Tick `ok`, or write the fix under it. Then run `cd backend/session_moral_context/content && python3 tools/mark_reviewed.py --by "Abdulrahman Salamah" terms.json`.

## الْمَلَائِكة | Mala'ikah (Angels) (word 9961)

- Page: https://islamic-content.com/dictionary/word/9961 · EN: https://islamic-content.com/dictionary/word/9961/en
- values: - · age: all · level: A
- Source AR: مخلوقات خلقها الله تعالى من نور، وجعل لهم قدرة على التشكل والتنقل، وسخرهم لعبادته
- Source EN: Creatures whom Allah created from light. He created them to serve and worship Him and granted them the ability to transform in shape and move quickly.
- Ours, AR: الملائكة مخلوقات خلقها الله من نور، وهم يعبدونه ويطيعونه.
- Ours, EN: Angels are creatures Allah made from light; they worship and obey Him.
- **Flag:** cut before the clause that echoes 66:6, so no Quran wording is read by TTS
- [ ] ok

## صَدَقَةٌ | Sadaqah (Charity) (word 11880)

- Page: https://islamic-content.com/dictionary/word/11880 · EN: https://islamic-content.com/dictionary/word/11880/en
- values: ['charity', 'generosity'] · age: all · level: A
- Source AR: العَطِيَّةُ التي يُخرِجُها الإنْسانُ مِن مالِهِ على وجْهِ القُرْبةِ وابْتِغاءِ الـمَثُوبةِ مِن اللهِ تعالى.
- Source EN: The donation that a person gives from his own wealth as an act of worship and in pursuit of reward from Allah.
- Ours, AR: الصدقة عطية نعطيها من مالنا لله ونرجو ثوابه.
- Ours, EN: Sadaqah is something we give from what we own, to please Allah and hoping for His reward.
- [ ] ok

## الْإِحْسَان | Ihsan (Excellence) (word 363)

- Page: https://islamic-content.com/dictionary/word/363 · EN: https://islamic-content.com/dictionary/word/363/en
- values: ['good-character'] · age: all · level: A
- Source AR: مُعامَلَةُ الإنسانِ غَيْرَهُ بِالحُسْنَى في القَوْلِ أو العَمَلِ أو الاعتِقَادِ ظاهِراً وباطِناً.
- Source EN: Treating others kindly, in words, actions or belief, both outwardly and inwardly
- Ours, AR: الإحسان أن نعامل الناس بالحسنى في القول والعمل.
- Ours, EN: Ihsan means treating others kindly in what we say and do.
- **Flag:** uses the "treating others kindly" sense; the page's primary sense (worship as if you see Him) is not used
- [ ] ok

## الْإِيمَان | Iman (Faith) (word 1952)

- Page: https://islamic-content.com/dictionary/word/1952 · EN: https://islamic-content.com/dictionary/word/1952/en
- values: - · age: all · level: A
- Source AR: قول باللسان واعتقاد بالقلب وعمل بالجوارح.
- Source EN: Statement by the tongue, belief in the heart, and action by the body parts.
- Ours, AR: الإيمان أن نصدّق بقلوبنا ونقول بألسنتنا ونعمل بجوارحنا.
- Ours, EN: Iman means believing in our hearts, saying it with our tongues and showing it through our actions.
- [ ] ok

## الصَّوْمُ | Sawm (Fasting) (word 6393)

- Page: https://islamic-content.com/dictionary/word/6393 · EN: https://islamic-content.com/dictionary/word/6393/en
- values: - · age: all · level: A
- Source AR: الإِمْساكُ عَن سائِرِ الـمُفَطِّراتِ مِنْ طُلوعِ الفَجْرِ إلى غُروبِ الشَّمْسِ مع النِّيَّةِ.
- Source EN: To abstain from whatever breaks the fast from the break of dawn until sunset while having this intention .
- Ours, AR: الصوم أن نمتنع عن المفطرات من الفجر إلى غروب الشمس بنية العبادة.
- Ours, EN: Fasting means staying away from eating and drinking from dawn until sunset, with the intention of worshipping Allah.
- [ ] ok

## الْحَرَامُ | Haram (Forbidden) (word 4169)

- Page: https://islamic-content.com/dictionary/word/4169 · EN: https://islamic-content.com/dictionary/word/4169/en
- values: - · age: 10-13 · level: A
- Source AR: ما نهى الشارع عنه نهياً جازماً، ورتب على فعله العقاب.
- Source EN: Whatever God has categorically forbidden and attached punishment for committing it.
- Ours, AR: الحرام هو ما نهانا الله عنه نهيًا جازمًا.
- Ours, EN: Haram is what Allah has clearly told us not to do.
- **Flag:** age 10-13 (mentions punishment)
- [ ] ok

## التَّقْوَى | Taqwa (God-fearing) (word 3269)

- Page: https://islamic-content.com/dictionary/word/3269 · EN: https://islamic-content.com/dictionary/word/3269/en
- values: - · age: 10-13 · level: A
- Source AR: أن يجعل الإنسان بينه وبين عذاب الله تعالى وسخطه وقاية؛ بفعل أوامره واجتناب نواهيه.
- Source EN: Placing a barrier between oneself and Allah’s anger and punishment, by fulfilling His commandments, and avoiding His prohibitions.
- Ours, AR: التقوى أن نحذر غضب الله فنفعل ما أمر به ونترك ما نهى عنه.
- Ours, EN: Taqwa means being careful about Allah's displeasure, so we do what He commanded and stay away from what He forbade.
- **Flag:** age 10-13 (mentions Allah's anger and punishment)
- [ ] ok

## الحَدِيْث | Hadith (word 4139)

- Page: https://islamic-content.com/dictionary/word/4139 · EN: https://islamic-content.com/dictionary/word/4139/en
- values: ['love-of-the-prophet'] · age: all · level: A
- Source AR: ما أضيف إلى النبي محمد -صَلَّى اللهُ عَلَيهِ وَسَلَّمَ- من قول، أو فعل، أو تقرير، أو صفة خُلقية، أو خِلقية. وهو بهذا المعنى الخاص مرادف لمصطلح "السُّنَّة" عند المحدثين.
- Source EN: whatever is attributed to prophet Muhammad (peace be upon him) of a verbal statement, action, approval, moral quality and physical description. In this particular sense it is synonymous with the term ‘sunnah’ as used by hadith scholars.
- Ours, AR: الحديث هو ما نُقل عن النبي محمد ﷺ من قول أو فعل أو تقرير.
- Ours, EN: A hadith is something the Prophet Muhammad ﷺ said or did, passed down to us.
- [ ] ok

## الْجَنَّة | Jannah (Heaven) (word 3911)

- Page: https://islamic-content.com/dictionary/word/3911 · EN: https://islamic-content.com/dictionary/word/3911/en
- values: - · age: all · level: A
- Source AR: دار الجزاء العظيم والثواب الجزيل الذي أعده الله تعالى لأوليائه وأهل طاعته يوم القيامة.
- Source EN: The Abode of magnificent recompense and abundant reward that Allah Most High prepared for His allies and obedient slaves on the Day of Judgement.
- Ours, AR: الجنة دار النعيم التي أعدها الله لعباده المطيعين يوم القيامة.
- Ours, EN: Jannah is the home of lasting happiness that Allah prepared for people who obey Him.
- [ ] ok

## الْإِسْلَام | Islam (word 1018)

- Page: https://islamic-content.com/dictionary/word/1018 · EN: https://islamic-content.com/dictionary/word/1018/en
- values: - · age: 10-13 · level: A
- Source AR: الاستسلام لله بالتوحيد، والانقياد له بالطاعة، والبراءة من الشرك وأهله.
- Source EN: Surrendering to Allah through monotheism, submitting to Him through obedience, and disowning polytheism and polytheists.
- Ours, AR: الإسلام أن نسلّم أمرنا لله وحده ونطيعه.
- Ours, EN: Islam means giving ourselves to Allah alone and obeying Him.
- **Flag:** age 10-13 because the definition says "disowning polytheism and polytheists"; you decide the age band (no shorter definition on the page)
- [ ] ok

## الدَّعْوَةُ الْإِسْلَامِيَّةُ | Da'wah (Islamic advocacy) (word 4892)

- Page: https://islamic-content.com/dictionary/word/4892 · EN: https://islamic-content.com/dictionary/word/4892/en
- values: - · age: all · level: A
- Source AR: علم به تعرف كافة المحاولات الرامية إلى تبليغ الناس جميعاً دعوة الإسلام. وتعريفهم بما حوى من عقيدة، وشريعة، وأخلاق، وهدايتهم إليه قولاً وعملاً، في كل زمان ومكان، بأساليب، ووسائل خاصة تتناسب مع المدعويين على مختلف أصنافهم، وعصورهم.
- Source EN: A discipline that looks at all attempts aiming to deliver the message of Islam to all mankind so that they would know its creed, law, morality and manners, and that they may be guided to it. This includes all means to deliver the Islamic message, by word and deed, in all times and places, using special ways and means that are suitable to the different groups and times of the addressees.
- Ours, AR: الدعوة الإسلامية هي تعريف الناس بالإسلام بلطف.
- Ours, EN: Islamic advocacy (dawah) means telling people about Islam and inviting them to it kindly.
- [ ] ok

## الإِفْتَاء | Ifta' (Issuing a fatwa) (word 1366)

- Page: https://islamic-content.com/dictionary/word/1366 · EN: https://islamic-content.com/dictionary/word/1366/en
- values: - · age: all · level: A
- Source AR: الإخبار بالحكم الشرعي لمن سأل عنه دون إلزام به.
- Source EN: Informing someone of a religious ruling that he has asked about, without enforcing it.
- Ours, AR: الإفتاء أن يُجيب العالم من يسأله عن حكم الدين، وإذا أردت حكمًا في شأن يخصك فاسأل والديك أو عالمًا.
- Ours, EN: Giving a fatwa means a scholar answers a person's question about what the religion says. For a ruling about your own life, ask your parents or a scholar.
- [ ] ok

## الرَّسُول | Rasul (Messenger) (word 5216)

- Page: https://islamic-content.com/dictionary/word/5216 · EN: https://islamic-content.com/dictionary/word/5216/en
- values: ['love-of-the-prophet'] · age: all · level: A
- Source AR: إنسان ذكر حر يوحي الله إليه بوحيه المتضمن أمره، ونهيه، وخبره، ويأمره -سُبْحَانَهُ- بتبليغه إلى أقوامٍ يقابلون دعوته بالتكذيب، والمخالفة، فلا يصدقونه، ولا يوافقونه، ويقع بينه، وبينهم منازعة في ذلك.
- Source EN: A male person who receives God’s revelations containing his commandments, prohibitions and other information. God commands him to deliver that to people who will inevitably reject his address and not believe him. He will thus be in conflict with them.
- Ours, AR: الرسول إنسان يوحي الله إليه ويأمره أن يبلّغ رسالته إلى الناس.
- Ours, EN: A messenger is a person Allah sends revelation to and commands to deliver it to the people.
- [ ] ok

## التَّوْحِيد | Tawhid (Monotheism) (word 3529)

- Page: https://islamic-content.com/dictionary/word/3529 · EN: https://islamic-content.com/dictionary/word/3529/en
- values: - · age: all · level: A
- Source AR: إفراد الله -تعالى- بالربوبية، والألوهية، والأسماء والصفات.
- Source EN: The belief that Godhood, lordship, names and attributes belong to God alone.
- Ours, AR: التوحيد أن نؤمن بأن الله وحده الخالق، وأنه وحده من نعبده، وأن له أسماء وصفات لا يشبهه فيها أحد. وليس معناه مجرد أن الله واحد في العدد.
- Ours, EN: Tawhid means believing that Allah alone is the Creator, that He alone is worshipped, and that no one is like Him in His names and attributes. It is more than just counting one.
- **Flag:** uses the page's short التعريف line (the long one says "disowning polytheists")
- [ ] ok

## الصَّبْرُ | Sabr (Patience in adversity) (word 6128)

- Page: https://islamic-content.com/dictionary/word/6128 · EN: https://islamic-content.com/dictionary/word/6128/en
- values: ['patience'] · age: all · level: A
- Source AR: حبس النفس عن الجزع والتسخط، واللسان عن التشكي، والجوارح عن التشويش. والصبر على الطاعات حتى يؤديها، وعن المناهي حتى يجتنبها، وعلى أقدار الله المؤلمة.
- Source EN: To stop oneself from worry and anger, one’s tongue from uttering complaints, and one’s body from being irritable. To persevere in obedience of God, refrain from all sinful actions and show patience when enduring affliction.
- Ours, AR: الصبر أن نحبس أنفسنا عن الجزع عند الشدة، ونثبت على الطاعة، ونبتعد عما نهى الله عنه.
- Ours, EN: Sabr means holding ourselves together when things are hard, sticking to what is right and staying away from what is wrong.
- **Flag:** explanation rewritten after review (the old one said "do not complain": safeguarding risk)
- [ ] ok

## الْحَلاَلُ | Halal (Permissible) (word 4469)

- Page: https://islamic-content.com/dictionary/word/4469 · EN: https://islamic-content.com/dictionary/word/4469/en
- values: - · age: all · level: A
- Source AR: الْجَائِزُ الْمَأْذُونُ بِهِ شَرْعًا، الذي وسع الله في إتيانه، وهو نقيض الحرام.
- Source EN: What is permitted and acceptable in the shariah, as God has given permission to do it. It is the opposite of ‘forbidden’.
- Ours, AR: الحلال هو ما أذن الله لنا فيه.
- Ours, EN: Halal is what Allah has allowed us to do or to have.
- [ ] ok

## الصَلاةُ | Salah (Prayer) (word 6327)

- Page: https://islamic-content.com/dictionary/word/6327 · EN: https://islamic-content.com/dictionary/word/6327/en
- values: ['prayer'] · age: all · level: A
- Source AR: أقْوالٌ وأفْعالٌ مُفْتَتَحَةٌ بِالتَّكبِيرِ ومُخْتَتَمَةٌ بِالتَّسْلِيمِ.
- Source EN: A set of statements and actions that starts with "takbeer" (saying "Allahu Akbar") and ends with "tasleem" (saying "as-salāmu ‘alaykum").
- Ours, AR: الصلاة عبادة نبدؤها بالتكبير وننهيها بالتسليم، نتقرب بها إلى الله.
- Ours, EN: Salah is the worship we begin by saying "Allahu Akbar" and end with the salam, to get close to Allah.
- [ ] ok

## النَّبِيّ | Nabi (Prophet) (word 10343)

- Page: https://islamic-content.com/dictionary/word/10343 · EN: https://islamic-content.com/dictionary/word/10343/en
- values: ['love-of-the-prophet'] · age: all · level: C
- Source AR: إنسان ذكر أوحي إليه بشرع، ولم يؤمر بتبليغه.
- Source EN: A male human being to whom God revealed some legislation, but he was not commanded to deliver it.
- Ours, AR: النبي إنسان اختاره الله وأوحى إليه بشرع.
- Ours, EN: A prophet is a person Allah chose and sent revelation to.
- Disagreement note: اختلف العلماء في الفرق بين النبي والرسول، وهذا أحد الأقوال. / Scholars differ on the difference between a prophet and a messenger; this is one of the views.
- **Flag:** level C: the page itself notes scholars differ on prophet vs messenger
- [ ] ok

## النُّبُوَّة | Nubuwwah (Prophethood) (word 10342)

- Page: https://islamic-content.com/dictionary/word/10342 · EN: https://islamic-content.com/dictionary/word/10342/en
- values: ['love-of-the-prophet'] · age: all · level: A
- Source AR: خطاب سمعي يوحيه الرب -سُبْحَانَهُ- بواسطة ملك من الملائكة إلى من أكرمه الله بذلك. وهي مقام شريف يمنحه الله من يشاء، ولا يناله أي أحد بسعي منه.
- Source EN: An audible address revealed by God, the glorious, through an angel to one whom God honours with this status. It is a noble status granted by God to whomever he chooses. No one can achieve it through endeavour.
- Ours, AR: النبوة مكانة شريفة يمنحها الله لمن يشاء من عباده ويوحي إليهم.
- Ours, EN: Prophethood is a noble position that Allah gives to the people He chooses, and He sends revelation to them.
- [ ] ok

## رَمَضَانُ | Ramadan (word 5295)

- Page: https://islamic-content.com/dictionary/word/5295 · EN: https://islamic-content.com/dictionary/word/5295/en
- values: - · age: all · level: A
- Source AR: الشهر التاسع من السنة الهجرية، يجب صوم نهاره، ويستحب قيام ليله على المسلمين.
- Source EN: The ninth month of the Hijri year. Muslims have the duty of fasting throughout its days and are recommended to spend time at night in worship.
- Ours, AR: رمضان هو الشهر التاسع من السنة الهجرية، وفيه يصوم المسلمون.
- Ours, EN: Ramadan is the ninth month of the Hijri year, the month in which Muslims fast.
- [ ] ok

## الذِّكْر | Dhikr (Remembrance) (word 5023)

- Page: https://islamic-content.com/dictionary/word/5023 · EN: https://islamic-content.com/dictionary/word/5023/en
- values: ['remembering-allah'] · age: all · level: A
- Source AR: كُلُّ قَوْلٍ يَشْتَمِلُ على تَعْظِيمِ اللهِ تعالى ومَـحَـبَّتِهِ.
- Source EN: Any statement that includes glorification of Allah and expressing love for Him.
- Ours, AR: الذكر هو كل قول فيه تعظيم لله ومحبة له.
- Ours, EN: Dhikr is any words that glorify Allah and show our love for Him.
- [ ] ok

## الْوَحْي | Wahy (Revelation) (word 10849)

- Page: https://islamic-content.com/dictionary/word/10849 · EN: https://islamic-content.com/dictionary/word/10849/en
- values: - · age: all · level: A
- Source AR: إعلام الله -تعالى- لأنبيائه بما شاء من أحكامه، وأخباره.
- Source EN: That God informs the prophets of whatever he wishes to impart to them of his rulings and other information.
- Ours, AR: الوحي هو أن يُعلِم الله أنبياءه بما يريد.
- Ours, EN: Revelation is how Allah tells His prophets what He wants them to know.
- [ ] ok

## الدُّعَاء | Du'a (Supplication) (word 4887)

- Page: https://islamic-content.com/dictionary/word/4887 · EN: https://islamic-content.com/dictionary/word/4887/en
- values: ['remembering-allah', 'trust-in-allah'] · age: all · level: A
- Source AR: مناداة العبد لله -تعالى- لما يريد من جلب منفعة، أو دفع مضرة، مع إظهار الافتقار إليه سبحانه، والتبرؤ من الحول، والقوة، واستشعار الذلة البشرية. وهو على قسمين؛ دعاء عبادة، ودعاء مسألة.
- Source EN: A person’s appeal to God to grant whatever one needs of benefit or harm prevention, stating one’s need of God’s help and admitting one’s helplessness and human weakness. It is of two types: a worship supplication and request supplication.
- Ours, AR: الدعاء أن نطلب من الله ما نحتاجه، ونُظهر أننا نحتاج إليه.
- Ours, EN: Dua is when we ask Allah for what we need, showing that we depend on Him.
- [ ] ok

## الصِّدْق | Sidq (Telling the truth) (word 6197)

- Page: https://islamic-content.com/dictionary/word/6197 · EN: https://islamic-content.com/dictionary/word/6197/en
- values: ['honesty'] · age: all · level: A
- Source AR: وصف المخبر عنه بما يطابق الواقع.
- Source EN: To describe something as it really is.
- Ours, AR: الصدق أن نقول الأمر كما هو في الواقع.
- Ours, EN: Truthfulness means saying things exactly as they really are.
- [ ] ok

## الْحَجُّ | The hajj, the pilgrimage (word 4049)

- Page: https://islamic-content.com/dictionary/word/4049 · EN: https://islamic-content.com/dictionary/word/4049/en
- values: - · age: all · level: A
- Source AR: عبادة مخصوصة تؤدّى بمكة المكرمة، وما حولها في زمن مخصوص. من أهم شعائرها الوقوف بعرفة، وطواف الإفاضة بالكعبة المعظمة.
- Source EN: A special type of worship that is performed at Makkah and its surrounding area at a particular time. It includes several rituals, the most important of which are attendance at Arafat and the ṭawāf al-ifāḍah, which is a walk around the KaꜤbah.
- Ours, AR: الحج عبادة نؤديها في مكة المكرمة وما حولها في وقت معين.
- Ours, EN: Hajj is a special worship done in Makkah and the places around it at a particular time.
- [ ] ok

## الْقُرآن | The Qur’an (word 7771)

- Page: https://islamic-content.com/dictionary/word/7771 · EN: https://islamic-content.com/dictionary/word/7771/en
- values: - · age: all · level: A
- Source AR: كلام الله تعالى المنزل على رسوله محمد صلى الله عليه وسلم المتعبد بتلاوته المكتوب في المصاحف المنقول إلينا بالتواتر .
- Source EN: The speech of Allah, revealed to His Messenger Muhammad, may Allah's peace and blessings be upon him, which one worships Allah by reciting it, and which is written in mus-hafs and transmitted contiguously.
- Ours, AR: القرآن كلام الله الذي أنزله على نبينا محمد ﷺ، ونتعبد الله بتلاوته.
- Ours, EN: The Quran is the words of Allah that He sent down to the Prophet Muhammad ﷺ, and reciting it is worship.
- [ ] ok

## الشَّرِيْعَةُ | The sharia (word 5979)

- Page: https://islamic-content.com/dictionary/word/5979 · EN: https://islamic-content.com/dictionary/word/5979/en
- values: - · age: all · level: A
- Source AR: كل ما نزل به الوحي من الدين على رسول الله صلى الله عليه وسلم من العقائد والأحكام.
- Source EN: All beliefs and rulings that have been revealed to the Messenger of Allah, may Allah"s peace and blessings be upon him.
- Ours, AR: الشريعة هي ما أنزله الله من عقائد وأحكام لنهتدي بها في حياتنا.
- Ours, EN: The sharia is the beliefs and rules Allah sent down to guide how we live.
- [ ] ok

## السُّنَّة | The sunnah (word 5744)

- Page: https://islamic-content.com/dictionary/word/5744 · EN: https://islamic-content.com/dictionary/word/5744/en
- values: ['love-of-the-prophet'] · age: all · level: A
- Source AR: ما يثاب على فعله، ولا يعاقب على تركه. وهي ما استفيد من قوله -صَلَّى اللهُ عَلَيْهِ وَسَلَّم- أو فعله، أو همه، أو تقريره.
- Source EN: What gains reward when done, but incurs no punishment if undone. It includes what is understood from the prophet’s action, intended action or approval.
- Ours, AR: السنة هي طريقة النبي ﷺ التي نتبعها ونُثاب على فعلها.
- Ours, EN: The sunnah is the way of the Prophet ﷺ that we follow, and we are rewarded for doing it.
- **Flag:** source text is the usul sense (rewarded if done, not punished if left); our explanation uses the general "way of the Prophet" sense
- [ ] ok

## الأمَانَةُ | Amanah (Trust) (word 1592)

- Page: https://islamic-content.com/dictionary/word/1592 · EN: https://islamic-content.com/dictionary/word/1592/en
- values: ['trustworthiness'] · age: all · level: A
- Source AR: كل ما يؤتمن عليه من أسْرار، وحُرمات، وأموال، وهي ضد الخيانة.
- Source EN: All that one may hold in trust including secrets, private matters, property, etc.
- Ours, AR: الأمانة أن نحفظ ما يأتمننا الناس عليه، مثل أغراضهم وأموالهم، ونردّه إليهم، وهي عكس الخيانة.
- Ours, EN: Amanah means taking care of what people trust us with, like their things or money, and giving it back; it is the opposite of betraying them.
- **Flag:** explanation rewritten after review (the old one said "like secrets": grooming risk)
- [ ] ok

## الْعِبَادَةُ | 'Ibadah (Worship) (word 6732)

- Page: https://islamic-content.com/dictionary/word/6732 · EN: https://islamic-content.com/dictionary/word/6732/en
- values: ['prayer', 'remembering-allah'] · age: all · level: A
- Source AR: اسم جامع لكل ما يحبه الله ويرضاه من الأقوال والأعمال الظاهرة والباطنة.
- Source EN: A comprehensive name for all that Allah loves and is pleased with of words and deeds, the hidden and apparent thereof.
- Ours, AR: العبادة هي كل ما يحبه الله من أقوالنا وأعمالنا، مثل الصلاة وقول الصدق وبر الوالدين.
- Ours, EN: Worship means everything we say and do that Allah loves, like praying, telling the truth and being kind to our parents.
- [ ] ok

## الْوُضُوءُ | Wudu, ablution (word 10922)

- Page: https://islamic-content.com/dictionary/word/10922 · EN: https://islamic-content.com/dictionary/word/10922/en
- values: ['cleanliness'] · age: all · level: A
- Source AR: اسْتِعْمالُ الـماءِ الطَّهُورِ في أَعْضاءٍ مَخْصُوصَةٍ على صِفَةٍ مَخْصُوصَةٍ بِقَصْدِ التَّعَبُّدِ.
- Source EN: Using pure water on particular body parts in a particular manner.
- Ours, AR: الوضوء أن نغسل أعضاء معينة بالماء الطاهر بطريقة معينة لنستعد للعبادة.
- Ours, EN: Wudu means washing certain parts of the body with clean water in a special way, to get ready for worship like prayer.
- [ ] ok

## الزَّكَاةُ | Zakat (word 5419)

- Page: https://islamic-content.com/dictionary/word/5419 · EN: https://islamic-content.com/dictionary/word/5419/en
- values: ['charity'] · age: all · level: A
- Source AR: حق مالي واجب معين، في مال معين، لأصناف مخصوصة، في وقت مخصوص.
- Source EN: A financial obligation levied on particular types of money and property, due at particular times.
- Ours, AR: الزكاة حق واجب في أموال معينة نعطيه لمن يستحقه في وقته.
- Ours, EN: Zakat is a set share of certain kinds of wealth that Muslims must give to those who deserve it at the right time.
- [ ] ok
