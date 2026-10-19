# dorar sections review: tafsir, aqidah, fiqh, sirah

Script-generated from `backend/session_moral_context/content/items/{tafsir,aqidah,fiqh,sirah}.json` (X5 drafts from the 52 saved dorar pages, status `seeded`). 
Every `arabic_text` is a contiguous cut made by `tools/draft_from_page.py` and copied here by script; the explanations are ours. 
Check each item on the live page (URL given), tick `ok`, then mark:

```
cd backend/session_moral_context/content
python3 tools/mark_reviewed.py --by "Abdulrahman Salamah" items/tafsir.json
python3 tools/mark_reviewed.py --by "Abdulrahman Salamah" items/aqidah.json
python3 tools/mark_reviewed.py --by "Abdulrahman Salamah" items/fiqh.json
python3 tools/mark_reviewed.py --by "Abdulrahman Salamah" items/sirah.json
```

Checks already run: `seed_content --dry-run` (sqlite): 0 rejected; every `arabic_text` line is a verbatim substring of its saved page in `tools/.cache/`.

## Counts

| section | items | target | floor | pages used |
|---|---|---|---|---|
| tafsir | 23 | 20 | 10 | 21 |
| aqidah | 14 | 12 | 6 | 13 |
| fiqh | 8 | 8 | 4 | 8 |
| sirah | 5 | 8 | 4 | 5 |

## Skipped pages

| page | URL | reason |
|---|---|---|
| dorar-history/12.md | https://dorar.net/history/event/12 | first revelation: the only paragraph quotes 96:1-5 and 74:1-5 inline; neither is fully in the bank, so the tool would refuse the excerpt (and it describes the Prophet being frightened) |
| dorar-history/41.md | https://dorar.net/history/event/41 | Dar al-Nadwa plot: real deny-list content (plan to kill with swords, Iblis as an old man); brief says 10-13 or skip - skipped |
| dorar-history/127.md | https://dorar.net/history/event/127 | conquest of Makkah: mentions blood of some people declared lawful; no forgiveness wording - skipped per brief |
| dorar-history/44.md | https://dorar.net/history/event/44 | DROPPED (B2): with `--sentences`, the sentence that holds the land purchase and brick-carrying also holds the Prophet's rajaz inside straight quotes (the splitter never splits inside quotes), and the other sentences hold graves/swords or speech. No clean sentence range exists |
| dorar-feqhia/148.md | https://dorar.net/feqhia/148/... | DROPPED after review (B3): not pure agreement; cleanliness is covered by 258/260 |
| dorar-*/dorar-*-sample.md | (samples) | earlier sample captures, not in the manifest - ignored |

## Notes from the review round (applied)

- The browser captures lost dorar's ﴿﴾ marks, so on the card the verse words quoted inside a tafsir excerpt are not visually separated from the exegete's words. These excerpts are card-only and are never given to the LLM (B1 fix in retrieval.py).
- 9/40 and 49/4#v12 re-cut; 148 and sirah 44 dropped (see Skipped pages). Sirah 1, 8 and 45 were re-drafted with the new `draft --sentences A-B` option (sentence ranges of one cleaned line, exact substring asserted); sirah is back at 5 (floor 4).
- aqeeda/2449 is level C with a simplified-definition note; aqeeda/1664 kept at 10-13.
- Our explanations were rescanned for verse wording and paraphrased (4/18, 4/24, 5/1, 9/40, 9/47, 13/8, 17/9, 33/7, 49/3, 93/1); safeguarding sentences added to 3/41, 17/6#v24, 41/6, 49/4#v12.

## tafsir (23)

### 1. [tafsir] Tafsir of 2:261 / تفسير 2:261

- page: https://dorar.net/tafseer/2/45
- values: charity, generosity
- age: all | level: B | status: seeded | number: 2:261-265 | related: verse:2:261
- book: موسوعة التفسير - الدرر السنية

**arabic_text (verbatim from the page):**

> 2- أنَّ ثوابَ الله، وفضْلَه أكثرُ من عَمَلِ العاملِ؛ لأنَّه لو عُومِل العاملُ بالعدل لكانت الحسنة بمِثْلها، لكنَّ الله يُعامِله بالفضل والزِّيادة، فتكون الحبَّة الواحدة سبعمئة حبَّة، بل أَزيدَ؛ لقوله تعالى: وَاللهُ يُضَاعِفُ لِمَنْ يَشَاءُ وَاللهُ وَاسِعٌ عَلِيمٌ  ، ممَّا يَزيد رجاءَ العبدِ في ربِّه.

**our explanations:**

- 6-9 ar: عندما تعطي الصدقة لله، يكافئك الله أكثر بكثير مما أعطيت. الحبة الواحدة تصير سبعمئة حبة، وهذا يجعلنا نحب العطاء.
- 6-9 en: When you give charity for Allah, He rewards you with much more than you gave. One seed becomes seven hundred seeds, and that makes us love giving.
- 10-13 ar: يوضح التفسير أن الله يعامل من ينفق بالفضل والزيادة، لا بالعدل فقط، فيضاعف الحسنة إلى سبعمئة وأكثر. هذا يزيد أمل المسلم في ربه ويشجعه على الصدقة.
- 10-13 en: The tafsir explains that Allah treats the one who gives with generosity and increase, not just fairness: one good deed is multiplied to seven hundred or more. This grows a Muslim's hope in his Lord and encourages charity.

**flags:**

- page group 261-265 also covers 262-265 (charity followed by hurt, hypocrisy); excerpt is on 261 only
- excerpt quotes words of 2:261 inline (bank verse, in related)

- [x] ok

### 2. [tafsir] Tafsir of 3:134 / تفسير 3:134

- page: https://dorar.net/tafseer/3/41
- values: controlling-anger, forgiveness
- age: all | level: B | status: seeded | number: 3:133-136 | related: verse:3:134
- book: موسوعة التفسير - الدرر السنية

**arabic_text (verbatim from the page):**

> 5- كَظْمُ الغيظِ وإخفاؤه- بالصَّبر عن إمضائِه مع القُدرة، فلا يَظهَر له أثرٌ- من الأخلاقِ الفاضلة، ومِن أعظمِ العبادة؛ قال تعالى وَالْكَاظِمِينَ الْغَيْظَ  .
> 6- الحثُّ على العفوِ عن النَّاس فيما أساؤوا؛ وذلك في قوله تعالى: وَالْعَافِينَ عَنِ النَّاسِ  ، لكنَّه مُقيَّدٌ بما إذا كان أَصلَحَ  .

**our explanations:**

- 6-9 ar: عندما تغضب وتستطيع أن ترد، لكنك تهدأ وتمسك نفسك، فهذا خلق جميل يحبه الله. والعفو عن من أخطأ عليك خير. وإذا استمر أحد في إيذائك فأخبر شخصا كبيرا تثق به.
- 6-9 en: When you feel angry and could hit back but you stay calm and hold yourself, that is a beautiful manner Allah loves. Forgiving someone who wronged you is good. And if someone keeps hurting you, tell a trusted adult.
- 10-13 ar: يبين التفسير أن كظم الغيظ، أي حبس الغضب مع القدرة على الرد، من أفضل الأخلاق ومن أعظم العبادة. ويحث على العفو عن الناس إذا كان العفو يصلح الأمور. وإذا استمر أحد في إيذائك فأخبر شخصا كبيرا تثق به.
- 10-13 en: The tafsir explains that holding back anger when you are able to react is one of the finest manners and a great act of worship. It also encourages forgiving people when forgiveness makes things better. And if someone keeps hurting you, tell a trusted adult.

**flags:**

- excerpt quotes words of 3:134 inline (bank verse, in related); two lesson lines 5-6 taken together

- [x] ok

### 3. [tafsir] Tafsir of 4:36 / تفسير 4:36

- page: https://dorar.net/tafseer/4/13
- values: good-neighbour
- age: all | level: B | status: seeded | number: 4:36-42 | related: verse:4:36
- book: موسوعة التفسير - الدرر السنية

**arabic_text (verbatim from the page):**

> وَالْجَارِ الْجُنُبِ: أي: الَّذي ليس بينه وبين جارِه قَرابة، أو مَن يقرُبُ مسكنُه مِن الجارِ، أو الغريبُ، وأصْل الجوار: الميل؛ وسُمِّي الجار جارًا لميلِه إلى جاره، والجنابة: البُعد؛ يُقال: رجلٌ جُنُب، أي: غريبٌ  .

**our explanations:**

- 6-9 ar: الجار هو من يسكن قريبا منك، حتى لو لم يكن من عائلتك أو كان غريبا. الله يأمرنا أن نحسن إلى كل جار.
- 6-9 en: A neighbour is someone who lives near you, even if they are not family or are a stranger. Allah tells us to be kind to every neighbour.
- 10-13 ar: يشرح التفسير معنى الجار الجنب في الآية: هو الجار الذي لا تربطك به قرابة، أو من بيته قريب من بيتك، أو الغريب. فالإحسان إلى الجار مطلوب مع القريب والغريب.
- 10-13 en: The tafsir explains the words 'the neighbour who is a stranger' in the verse: the neighbour who is not your relative, whose home is near yours, or who is a stranger. So kindness to neighbours is asked of us whether they are relatives or strangers.

**flags:**

- age screen [marriage_relations]: excerpt contains "والجنابه" (word-meaning line: الجنابة = البعد, linguistic sense)
- page group 36-42 also covers miserliness/hypocrisy verses; excerpt is the word-meaning line for الجار الجنب (4:36) only
- deny-list hit is a false positive (الجنابة explained as distance)

- [x] ok

### 4. [tafsir] Tafsir of 4:58 / تفسير 4:58

- page: https://dorar.net/tafseer/4/18
- values: trustworthiness, justice
- age: all | level: B | status: seeded | number: 4:58-59 | related: verse:4:58
- book: موسوعة التفسير - الدرر السنية

**arabic_text (verbatim from the page):**

> يأمُر الله عباده بردِّ الأمانات إلى أصحابها، وأن يحكُموا بالعدل إذا حكَموا بين النَّاس، ونِعْم ما يأمرهم اللهُ به من أداء الأمانات والحُكم بالعَدْل بين النَّاس، إنَّ الله كان سميعًا بصيرًا.

**our explanations:**

- 6-9 ar: الله يأمرنا أن نرد الأمانة إلى صاحبها، وأن نكون عادلين عندما نحكم بين الناس. الله يسمع ويرى كل شيء.
- 6-9 en: Allah tells us to return what we are trusted with to its owner, and to be fair when we judge between people. Allah hears and sees everything.
- 10-13 ar: يبين التفسير أن الآية تأمر برد الأمانات إلى أصحابها وبالحكم بالعدل بين الناس، ويصف ذلك بأنه من أحسن ما يأمر به الله. وتذكرنا أن الله يسمع ويرى، فهو يعلم كيف نتعامل مع الأمانة والعدل.
- 10-13 en: The tafsir explains that the verse commands returning trusts to their owners and judging fairly between people, and describes this as among the best of what Allah commands. It ends by reminding us that Allah hears and sees, so He knows how we handle trust and fairness.

**flags:**

- المعنى الإجمالي line for 4:58 only; page also covers 4:59 (obedience to rulers)

- [x] ok

### 5. [tafsir] Tafsir of 4:86 / تفسير 4:86

- page: https://dorar.net/tafseer/4/24
- values: spreading-salam, kind-words
- age: all | level: B | status: seeded | number: 4:85-87 | related: verse:4:86
- book: موسوعة التفسير - الدرر السنية

**arabic_text (verbatim from the page):**

> ثمَّ يأمر اللهُ تعالى مَن حُيِّي بتحيَّةٍ أن يرُدَّ بتحيةٍ أحسَنَ ممَّا حُيِّيَ بها، أو يكون الرَّدُّ بمثلها، إنَّ اللهَ كان على كلِّ شيءٍ مِن طاعةٍ أو معصيةٍ حفيظًا ومحصيًا حتَّى يجازيَ فاعلَها عليها.

**our explanations:**

- 6-9 ar: عندما يسلم عليك أحد، رد عليه بسلام أجمل أو بنفس السلام. الله يحفظ كل كلمة طيبة نقولها.
- 6-9 en: When someone greets you with salam, answer with a better greeting or the same. Allah keeps count of every kind word we say.
- 10-13 ar: يوضح التفسير أن الآية تأمر من سلم عليه أحد أن يرد بتحية أفضل أو مساوية، وأن الله يحفظ كل عمل من طاعة أو غيرها ويجازي عليه. فرد السلام بأجمل منه عمل يراه الله.
- 10-13 en: The tafsir explains that the verse tells whoever is greeted to answer with a better greeting or an equal one, and that Allah records every deed and rewards it. Returning a greeting warmly is a deed Allah sees.

**flags:**

- المعنى الإجمالي line for 4:86 only; page also covers 4:85 (intercession), 4:87

- [x] ok

### 6. [tafsir] Tafsir of 5:2 / تفسير 5:2

- page: https://dorar.net/tafseer/5/1
- values: cooperation, helping-others
- age: all | level: B | status: seeded | number: 5:1-2 | related: verse:5:2
- book: موسوعة التفسير - الدرر السنية

**arabic_text (verbatim from the page):**

> 7- نَدَبَ اللهُ سبحانَه إلى التَّعاونِ على البِرِّ، وقَرَنَه بالتَّقوى له، فقال تعالى: وَتَعَاوَنُوا عَلَى الْبِرِّ وَالتَّقْوَى؛ لأنَّ في التَّقوى رِضا اللهِ تعالى، وفي البِرِّ رِضا النَّاسِ، ومَن جَمَعَ بين رِضا الله تعالى ورِضا النَّاسِ؛ فقد تمَّتْ سَعادَتُه، وعَمَّتْ نِعمَتُه  .

**our explanations:**

- 6-9 ar: الله يحب أن نساعد بعضنا على فعل الخير وطاعة الله. من يفعل الخير ويطيع الله يكون سعيدا.
- 6-9 en: Allah loves it when we help each other do good and obey Him. Whoever does good and obeys Allah becomes happy.
- 10-13 ar: يبين التفسير أن الله دعا إلى التعاون على فعل الخير وربطه بتقوى الله، لأن في التقوى رضا الله وفي فعل الخير رضا الناس، ومن جمع بينهما تمت سعادته.
- 10-13 en: The tafsir explains that Allah calls us to cooperate in doing good and links it to taqwa (being mindful of Allah): taqwa brings Allah's pleasure and good deeds bring people's goodwill, and whoever combines both finds complete happiness.

**flags:**

- page group 1-2 also covers ihram/hunting rules; excerpt is lesson 7 on cooperation (5:2) and quotes its words inline (bank verse, in related)

- [x] ok

### 7. [tafsir] Tafsir of 9:108 / تفسير 9:108

- page: https://dorar.net/tafseer/9/40
- values: cleanliness, prayer
- age: all | level: B | status: seeded | number: 9:107-110 | related: verse:9:108
- book: موسوعة التفسير - الدرر السنية

**arabic_text (verbatim from the page):**

> أي: في مسجدِ قُباءٍ رِجالٌ من أصحابِ مُحمَّدٍ صلَّى الله عليه وسلَّم يُحبُّونَ أن يتطهَّروا مِن النَّجاساتِ ومِنَ الذُّنوبِ  .

**our explanations:**

- 6-9 ar: في مسجد قباء كان أصحاب النبي صلى الله عليه وسلم يحبون أن يكونوا نظيفين في أجسادهم وطاهرين في قلوبهم من الذنوب. وهذا عمل يحبه الله.
- 6-9 en: In the mosque of Quba, the Prophet's companions (peace be upon him) loved to keep their bodies clean and their hearts clean from sins. This is something Allah loves.
- 10-13 ar: يوضح التفسير أن في مسجد قباء رجالا من أصحاب النبي صلى الله عليه وسلم يحبون أن يتطهروا من النجاسات ومن الذنوب. فالطهارة تشمل نظافة الجسد وطهارة القلب، وهذا عمل يحبه الله.
- 10-13 en: The tafsir explains that in the mosque of Quba were men from the Prophet's companions (peace be upon him) who loved to purify themselves from dirt and from sins. So purity includes a clean body and a clean heart, and this is something Allah loves.

**flags:**

- re-cut after review to the Quba line (page line 86) on 9:108; page is mainly the Dirar-mosque story - not taken; age all

- [ ] ok
FIX: values lists `prayer`, but neither the excerpt nor our explanations mention prayer. Remove `prayer` from values (keep `cleanliness`).

### 8. [tafsir] Tafsir of 9:119 / تفسير 9:119

- page: https://dorar.net/tafseer/9/43
- values: honesty, sincerity
- age: all | level: B | status: seeded | number: 9:117-119 | related: verse:9:119
- book: موسوعة التفسير - الدرر السنية

**arabic_text (verbatim from the page):**

> 7- قَولُ اللهِ تعالى: يَا أَيُّهَا الَّذِينَ آمَنُوا اتَّقُوا اللَّهَ وَكُونُوا مَعَ الصَّادِقِينَ دالٌّ على فَضلِ الصِّدقِ، وكمالِ دَرَجتِه  .
> 8- قال الله تعالى: يَا أَيُّهَا الَّذِينَ آمَنُوا اتَّقُوا اللَّهَ وَكُونُوا مَعَ الصَّادِقِينَ حَقُّ مَن فَهِمَ عن الله وعَقَلَ عنه، أن يُلازِمَ الصِّدقَ في الأقوالِ، والإخلاصَ في الأعمالِ، والصَّفاءَ في الأحوالِ، فمَن كان كذلك لَحِقَ بالأبرارِ، ووصَلَ إلى رِضا الغفَّارِ  .

**our explanations:**

- 6-9 ar: الصدق خلق عظيم. الله يحب أن نقول الصدق دائما وأن نكون مخلصين في أعمالنا.
- 6-9 en: Honesty is a great quality. Allah loves us to always tell the truth and to be sincere in what we do.
- 10-13 ar: يبين التفسير أن الآية تدل على فضل الصدق وعلو درجته، وأن من فهم عن الله يلازم الصدق في الأقوال والإخلاص في الأعمال والصفاء في الأحوال، فيلحق بالأبرار ويصل إلى رضا الله.
- 10-13 en: The tafsir explains that the verse shows the high rank of truthfulness, and that whoever truly understands Allah's message keeps to honesty in words, sincerity in deeds and purity in their state, joining the righteous and reaching Allah's pleasure.

**flags:**

- page covers Tabuk and the three who stayed behind; excerpt is lessons 7-8 on 9:119 and quotes its words inline (bank verse, in related)

- [x] ok

### 9. [tafsir] Tafsir of 9:128 / تفسير 9:128

- page: https://dorar.net/tafseer/9/47
- values: mercy, love-of-the-prophet
- age: all | level: B | status: seeded | number: 9:128-129 | related: verse:9:128
- book: موسوعة التفسير - الدرر السنية

**arabic_text (verbatim from the page):**

> يقولُ اللهُ تعالى مُخاطِبًا العَرَبَ: قد جاءَكم رسولٌ- هو محمَّدٌ صلَّى اللهُ عليه وسلَّم- مِنكم، يَشُقُّ عليه ما يشُقُّ عليكم ويُؤذِيكم، حريصٌ على هِدايتِكم، وإيصالِ الخَيرِ لكم، بالمُؤمِنينَ رؤوفٌ رَحيمٌ.

**our explanations:**

- 6-9 ar: النبي صلى الله عليه وسلم كان يحزن إذا تعب الناس، ويحب لهم الخير، وكان رحيما رفيقا بالمؤمنين.
- 6-9 en: The Prophet (peace be upon him) felt sad when people suffered, wanted good for them, and was gentle and merciful to the believers.
- 10-13 ar: يوضح التفسير أن الآية تصف النبي صلى الله عليه وسلم بأنه من قوم العرب، يشق عليه ما يشق عليهم، يهتم بهدايتهم وإيصال الخير لهم، شديد الرحمة والرفق بالمؤمنين. هذه صفات نحبها فيه ونتعلم منها.
- 10-13 en: The tafsir explains that the verse describes the Prophet (peace be upon him) as one of his people, pained by whatever pains them, eager to guide them and bring them good, and gentle and merciful to the believers. These are qualities we love in him and learn from.

**flags:**

- المعنى الإجمالي line for 9:128 only

- [x] ok

### 10. [tafsir] Tafsir of 13:28 / تفسير 13:28

- page: https://dorar.net/tafseer/13/8
- values: remembering-allah
- age: all | level: B | status: seeded | number: 13:28-30 | related: verse:13:28
- book: موسوعة التفسير - الدرر السنية

**arabic_text (verbatim from the page):**

> 1- قال الله تعالى: أَلَا بِذِكْرِ اللَّهِ تَطْمَئِنُّ الْقُلُوبُ فالقُلوبُ حَقيقٌ بها وحَرِيٌّ ألَّا تطمَئِنَّ لشَيءٍ سِوى ذِكرِه؛ فإنَّه لا شيءَ ألَذُّ للقُلوبِ ولا أشهَى ولا أحلَى مِن محبَّةِ خالِقِها، والأُنسِ به ومَعرفتِه، وعلى قَدرِ مَعرفتِها باللهِ ومَحبَّتِها له، يكونُ ذِكرُها له  .

**our explanations:**

- 6-9 ar: القلب يرتاح ويهدأ عندما نذكر الله. ليس هناك شيء أجمل للقلب من حب الله والأنس به.
- 6-9 en: The heart feels calm and at rest when we remember Allah. Nothing is sweeter for the heart than loving Allah and feeling close to Him.
- 10-13 ar: يبين التفسير أن القلوب لا تجد راحتها الحقيقية إلا عندما تذكر الله، لأن أحب شيء إلى القلب وأحلاه محبة خالقه ومعرفته، وكلما عرف الإنسان الله أكثر وأحبه أكثر زاد ذكره له.
- 10-13 en: The tafsir explains that hearts only truly find rest in remembering Allah, because nothing is dearer or sweeter to the heart than loving and knowing its Creator; the more a person knows and loves Allah, the more they remember Him.

**flags:**

- excerpt quotes words of 13:28 inline (bank verse, in related); page group 28-30

- [x] ok

### 11. [tafsir] Tafsir of 16:127 / تفسير 16:127

- page: https://dorar.net/tafseer/16/27
- values: patience, trust-in-allah
- age: all | level: B | status: seeded | number: 16:124-128 | related: verse:16:127
- book: موسوعة التفسير - الدرر السنية

**arabic_text (verbatim from the page):**

> 6- قال الله تعالى: وَاصْبِرْ لَمَّا كان الصَّبرُ في هذا المقامِ شاقًّا شديدًا؛ ذكَرَ بَعدَه ما يُفيدُ سُهولتَه، فقال: وَمَا صَبْرُكَ إِلَّا بِاللَّهِ، أي: بتَوفيقِه ومَعونتِه، وهذا هو السَّبَبُ الكُلِّيُّ الأصليُّ المُفيدُ في حُصولِ الصَّبرِ، وفي حُصولِ جميعِ أنواعِ الطَّاعاتِ  .

**our explanations:**

- 6-9 ar: الصبر قد يكون صعبا، لكن الله يساعدنا عليه. عندما نصبر نطلب العون من الله فيصبح الصبر أسهل.
- 6-9 en: Being patient can be hard, but Allah helps us with it. When we are patient we ask Allah for help, and patience becomes easier.
- 10-13 ar: يوضح التفسير أن الله لما أمر بالصبر في موقف صعب، ذكر بعده ما يسهله: أن الصبر لا يكون إلا بتوفيق الله وعونه. فالاستعانة بالله هي السبب الأصلي في حصول الصبر وكل الطاعات.
- 10-13 en: The tafsir explains that when Allah commanded patience in a hard situation, He then mentioned what makes it easier: patience comes only with Allah's help and guidance. Seeking Allah's help is the root cause of gaining patience and every other good deed.

**flags:**

- page group 124-128 (Sabbath, dawah, retaliation); excerpt is lesson 6 on 16:127 and quotes its words inline (bank verse, in related)

- [x] ok

### 12. [tafsir] Tafsir of 17:23 / تفسير 17:23

- page: https://dorar.net/tafseer/17/6#v23
- values: honouring-parents
- age: all | level: B | status: seeded | number: 17:22-25 | related: verse:17:23
- book: موسوعة التفسير - الدرر السنية

**arabic_text (verbatim from the page):**

> 3- قال تعالى: وَبِالْوَالِدَيْنِ إِحْسَانًا؛ لأنَّهما سببُ وجودِ العبدِ، ولهما مِن المحبةِ للولدِ والإحسانِ إليه والقربِ ما يقتضي تأكُّدَ الحقِّ، ووجوبَ البرِّ؛ لذا أمَر بالإحسانِ إليهما بجميعِ وجوهِ الإحسانِ القوليِّ والفعليِّ  .

**our explanations:**

- 6-9 ar: والداك هما سبب وجودك، وهما يحبانك ويحسنان إليك. لذلك أمرنا الله أن نحسن إليهما بالكلام الطيب والأفعال الطيبة.
- 6-9 en: Your parents are the reason you exist, and they love you and care for you. That is why Allah tells us to treat them well with kind words and kind actions.
- 10-13 ar: يبين التفسير سبب الأمر بالإحسان إلى الوالدين: أنهما سبب وجود الإنسان، ولهما من المحبة والإحسان والقرب ما يؤكد حقهما ويوجب برهما. لذلك جاء الأمر بالإحسان إليهما بكل وجوه الإحسان القولي والفعلي.
- 10-13 en: The tafsir explains why we are commanded to be good to parents: they are the reason we exist, and their love, care and closeness confirm their right and make honouring them a duty. So the command covers every kind of goodness, in words and in deeds.

**flags:**

- two items from this page (#v23, #v24); excerpt quotes words of 17:23 inline (bank verse, in related)

- [x] ok

### 13. [tafsir] Tafsir of 17:24 / تفسير 17:24

- page: https://dorar.net/tafseer/17/6#v24
- values: honouring-parents, gratitude
- age: all | level: B | status: seeded | number: 17:22-25 | related: verse:17:24
- book: موسوعة التفسير - الدرر السنية

**arabic_text (verbatim from the page):**

> 6- قَولُ الله تعالى: وَاخْفِضْ لَهُمَا جَنَاحَ الذُّلِّ مِنَ الرَّحْمَةِ وَقُلْ رَبِّ ارْحَمْهُمَا كَمَا رَبَّيَانِي صَغِيرًا يُفهَمُ منه أنَّه كُلَّما ازدادَت التَّربيةُ ازداد الحَقُّ، وكذلك مَن تولَّى تربيةَ الإنسانِ في دينِه ودُنياه تَربيةً صالِحةً غيرُ الأبوَينِ؛ فإنَّ له على مَن رَبَّاه حَقَّ التَّربيةِ  .

**our explanations:**

- 6-9 ar: كلما تعب والداك في تربيتك أكثر، صار حقهما عليك أكبر. ومن رباك تربية حسنة، مثل الجد أو الجدة، يستحق شكرك ودعاءك أيضا.
- 6-9 en: The more your parents work hard to raise you, the greater their right over you. Anyone who raised you well, like a grandparent, deserves your thanks and dua too.
- 10-13 ar: يستفيد التفسير من الآية أن الحق يزداد كلما ازدادت التربية، وأن من تولى تربية إنسان تربية صالحة في دينه ودنياه له حق التربية على من رباه. فمن رباك تربية حسنة، مثل الجد أو الجدة، يستحق شكرك ودعاءك أيضا.
- 10-13 en: The tafsir draws from the verse that the right owed grows with the amount of upbringing given, and that whoever raises a person well in faith and life has a right of upbringing over them. Anyone who raised you well, like a grandparent, deserves your thanks and dua too.

**flags:**

- age screen [crime]: excerpt contains "رباه"; check against the deny-list before use
- deny-list hit "رباه" is a false positive (ربّى = raised, not ربا); excerpt quotes words of 17:24 inline (bank verse, in related)

- [x] ok

### 14. [tafsir] Tafsir of 17:26 / تفسير 17:26

- page: https://dorar.net/tafseer/17/7
- values: not-wasting
- age: all | level: B | status: seeded | number: 17:26-31 | related: verse:17:26
- book: موسوعة التفسير - الدرر السنية

**arabic_text (verbatim from the page):**

> 4- أنَّ الإنسانَ ليس له أنْ يَصْرِفَ المالَ إلَّا فيما ينفَعُه في دينِه أو دُنياه، وما سِوى ذلك سَفَهٌ وتبذيرٌ نهى اللهُ عنه بقَولِه: وَآتِ ذَا الْقُرْبَى حَقَّهُ وَالْمِسْكِينَ وَابْنَ السَّبِيلِ وَلَا تُبَذِّرْ تَبْذِيرًا، وقال بعضُ السلفِ: (لو أنفقتَ درهمًا في معصيةِ الله كنتَ مبذِّرًا، ولو أنفقتَ ملءَ الأرضِ في طاعةِ الله لم تكنْ مبذِّرًا)  .

**our explanations:**

- 6-9 ar: المال نعمة من الله، فلا نصرفه إلا في شيء ينفعنا. إنفاق المال في ما لا فائدة فيه تبذير نهى الله عنه.
- 6-9 en: Money is a gift from Allah, so we only spend it on things that benefit us. Spending money on what has no good in it is wasting, and Allah told us not to.
- 10-13 ar: يبين التفسير أن الإنسان لا يصرف ماله إلا في ما ينفعه في دينه أو دنياه، وما سوى ذلك سفه وتبذير نهى الله عنه. وينقل عن بعض السلف أن إنفاق درهم واحد في معصية تبذير، بينما الإنفاق الكثير في طاعة الله ليس تبذيرا.
- 10-13 en: The tafsir explains that a person should spend money only on what benefits their faith or their life; anything else is foolish wasting that Allah forbade. It also quotes early scholars: spending even one coin in disobedience is wasting, while spending a great deal in obedience to Allah is not.

**flags:**

- page group 26-31 also covers 17:31 (killing children for fear of poverty) - not in excerpt; excerpt quotes words of 17:26 inline (bank verse, in related) and a saying of "بعض السلف" in parentheses

- [x] ok

### 15. [tafsir] Tafsir of 17:37 / تفسير 17:37

- page: https://dorar.net/tafseer/17/9
- values: humility
- age: all | level: B | status: seeded | number: 17:36-39 | related: verse:17:37
- book: موسوعة التفسير - الدرر السنية

**arabic_text (verbatim from the page):**

> ثم ينهَى الله عن التفاخرِ والتكبرِ والإعجابِ بالنفسِ، فيقولُ: ولا تمشِ في الأرضِ مُختالًا مُتكبِّرًا؛ فإنَّك لن تُؤَثِّرَ في الأرضِ فتَخرِقَها بشِدَّةِ وطءِ قدَميك عليها، ولن تَبلُغَ الجِبالَ طُولًا باختيالِك وتكَبُّرِك.

**our explanations:**

- 6-9 ar: الله لا يحب أن نمشي متكبرين ونظن أننا أفضل من الناس. الإنسان المتكبر صغير مهما ظن أنه كبير.
- 6-9 en: Allah does not like us to walk proudly thinking we are better than others. A proud person is small no matter how big they think they are.
- 10-13 ar: يوضح التفسير أن الآية تنهى عن التفاخر والتكبر والإعجاب بالنفس، وتذكر المتكبر أنه لن يصنع شيئا بقوة مشيه ولن يصير أعلى من الجبال بتكبره، فالتكبر لا يزيد الإنسان شيئا.
- 10-13 en: The tafsir explains that the verse forbids showing off, arrogance and self-admiration, reminding the proud person that he will neither split the earth with his heavy steps nor reach the height of the mountains by his pride; arrogance adds nothing to a person.

**flags:**

- المعنى الإجمالي line for 17:37 only; the next line on the page (17:39) mentions Hell - not taken

- [x] ok

### 16. [tafsir] Tafsir of 31:12 / تفسير 31:12

- page: https://dorar.net/tafseer/31/4
- values: gratitude, seeking-knowledge
- age: all | level: B | status: seeded | number: 31:12-13 | related: verse:31:12
- book: موسوعة التفسير - الدرر السنية

**arabic_text (verbatim from the page):**

> 1- قولُه تعالى: وَلَقَدْ آَتَيْنَا لُقْمَانَ الْحِكْمَةَ أَنِ اشْكُرْ لِلَّهِ تَنْبيهٌ منه سُبحانه على أنَّ الحِكمةَ الأصليَّةَ والعِلْمَ الحقيقيَّ هو العمَلُ بهما، أو عِبادةُ اللهِ والشُّكرُ له؛ حيث فسَّرَ إيتاءَ الحِكمةِ بالبعثِ على الشُّكرِ  .

**our explanations:**

- 6-9 ar: الحكمة الحقيقية هي أن نعمل بما نعرف، وأن نعبد الله ونشكره على نعمه. الشكر من علامات الحكمة.
- 6-9 en: True wisdom is to act on what we know, and to worship Allah and thank Him for His gifts. Being thankful is a sign of wisdom.
- 10-13 ar: يبين التفسير أن الله لما ذكر إعطاء لقمان الحكمة فسرها بالدعوة إلى الشكر، وهذا تنبيه على أن الحكمة الأصلية والعلم الحقيقي هما العمل بهما، أي عبادة الله وشكره.
- 10-13 en: The tafsir explains that when Allah mentioned giving Luqman wisdom, He described it as a call to be thankful. This shows that real wisdom and true knowledge mean acting on them, that is, worshipping Allah and thanking Him.

**flags:**

- lesson 1 on 31:12; quotes its words inline (bank verse, in related). Lesson 2 was dropped because of كفر/كافر (ingratitude sense) deny hits

- [x] ok

### 17. [tafsir] Tafsir of 31:18 / تفسير 31:18

- page: https://dorar.net/tafseer/31/6
- values: humility, good-character
- age: all | level: B | status: seeded | number: 31:16-19 | related: verse:31:18
- book: موسوعة التفسير - الدرر السنية

**arabic_text (verbatim from the page):**

> 10- في قَولِه تعالى: وَلَا تُصَعِّرْ خَدَّكَ لِلنَّاسِ وَلَا تَمْشِ فِي الْأَرْضِ مَرَحًا إِنَّ اللَّهَ لَا يُحِبُّ كُلَّ مُخْتَالٍ فَخُورٍ زَجْرٌ عن احتِقارِ النَّاسِ، ومِشْيةِ الخُيَلاءِ؛ وحثٌّ على التَّواضُعِ، وأخْذِ السَّكينةِ والوَقارِ  .

**our explanations:**

- 6-9 ar: لا تحتقر الناس ولا تمش بتكبر. كن متواضعا وهادئا، فالله يحب المتواضعين.
- 6-9 en: Do not look down on people or walk proudly. Be humble and calm, for Allah loves the humble.
- 10-13 ar: يوضح التفسير أن الآية تزجر عن احتقار الناس ومشية الخيلاء، وتحث على التواضع والسكينة والوقار. فالمتواضع يعرف أن النعم من الله فلا يتعالى على أحد.
- 10-13 en: The tafsir explains that the verse warns against looking down on people and walking with a show of pride, and encourages humility, calmness and dignity. The humble person knows that blessings come from Allah and does not look down on anyone.

**flags:**

- page group 16-19; excerpt is lesson 10 on 31:18 and quotes its words inline (bank verse, in related)

- [x] ok

### 18. [tafsir] Tafsir of 33:21 / تفسير 33:21

- page: https://dorar.net/tafseer/33/7
- values: love-of-the-prophet, good-character
- age: all | level: B | status: seeded | number: 33:21-24 | related: verse:33:21
- book: موسوعة التفسير - الدرر السنية

**arabic_text (verbatim from the page):**

> 4- قَولُ الله تعالى: لَقَدْ كَانَ لَكُمْ فِي رَسُولِ اللَّهِ أُسْوَةٌ حَسَنَةٌ لِمَنْ كَانَ يَرْجُو اللَّهَ وَالْيَوْمَ الْآَخِرَ وَذَكَرَ اللَّهَ كَثِيرًا فيه دَلالةٌ على فَضلِ الاقتِداءِ بالنَّبيِّ صلَّى الله عليه وسلَّم، وأنَّه الأُسوةُ الحَسَنةُ لا مَحالةَ  .

**our explanations:**

- 6-9 ar: النبي صلى الله عليه وسلم هو أفضل قدوة لنا. نحبه ونتعلم من أخلاقه وأفعاله.
- 6-9 en: The Prophet (peace be upon him) is the best example for us. We love him and learn from his manners and actions.
- 10-13 ar: يبين التفسير أن الآية تدل على فضل الاقتداء بالنبي صلى الله عليه وسلم، وأنه هو القدوة الحسنة بلا شك. فمحبته تظهر في اتباع هديه في الأخلاق والعبادة.
- 10-13 en: The tafsir explains that the verse shows the virtue of following the Prophet (peace be upon him) and that he is, without doubt, the finest example. Love for him shows in following his way in manners and worship.

**flags:**

- المعنى الإجمالي line was avoided (mentions جهاد); excerpt is lesson 4 on 33:21 and quotes its words inline (bank verse, in related)

- [x] ok

### 19. [tafsir] Tafsir of 41:34 / تفسير 41:34

- page: https://dorar.net/tafseer/41/6
- values: good-character, forgiveness, patience
- age: all | level: B | status: seeded | number: 41:30-36 | related: verse:41:34
- book: موسوعة التفسير - الدرر السنية

**arabic_text (verbatim from the page):**

> ثمَّ يُرشِدُ اللهُ تعالى إلى ما يُؤدِّي إلى إشاعةِ المحَبَّةِ، فيقولُ: ولا تَستوي الخَصلةُ الحَسَنةُ مع الخَصلةِ السَّيِّئةِ في الجَزاءِ؛ فادفَعْ -يا مُحمَّدُ- السَّيِّئةَ بالخَصلةِ الَّتي هي أحسَنُ؛ فأحسِنْ إلى مَن أساء إليك، وادْعُه بالحِكمةِ والرِّفقِ، واصفَحْ عنه، واصبِرْ على أذاه؛ فإنَّك إنْ فعَلْتَ ذلك صار مَن هو عدوٌّ لك كأنَّه صَديقٌ شَديدُ المحبَّةِ لك.

**our explanations:**

- 6-9 ar: إذا أساء إليك أحد، فرد عليه بالإحسان والكلمة الطيبة واصبر. قد يصير من كان يعاديك صديقا محبا لك. وإذا استمر أحد في إيذائك فأخبر شخصا كبيرا تثق به.
- 6-9 en: If someone is unkind to you, answer with kindness and good words, and be patient. The one who was against you may become a loving friend. And if someone keeps hurting you, tell a trusted adult.
- 10-13 ar: يوضح التفسير أن الآية ترشد إلى ما ينشر المحبة بين الناس: رد الإساءة بما هو أحسن منها، أي الإحسان إلى من أساء، والدعوة بالحكمة والرفق، والصفح والصبر على الأذى. ومن فعل ذلك صار عدوه كأنه صديق شديد المحبة له. وإذا استمر أحد في إيذائك فأخبر شخصا كبيرا تثق به.
- 10-13 en: The tafsir explains that the verse guides us to what spreads love among people: repelling bad behaviour with something better, that is, being good to the one who wronged you, speaking with wisdom and gentleness, pardoning and bearing hurt patiently. Whoever does this finds that his enemy becomes like a devoted friend. And if someone keeps hurting you, tell a trusted adult.

**flags:**

- المعنى الإجمالي line for 41:34 only (pure paraphrase)

- [x] ok

### 20. [tafsir] Tafsir of 49:10 / تفسير 49:10

- page: https://dorar.net/tafseer/49/3
- values: brotherhood, forgiveness
- age: all | level: B | status: seeded | number: 49:9-10 | related: verse:49:10
- book: موسوعة التفسير - الدرر السنية

**arabic_text (verbatim from the page):**

> 6- الواجبُ على المسلمِ نحْوَ أخيهِ أنْ يُزِيلَ ما بيْنَه وبيْنَ أخيه مِن الأحقادِ، وأنْ يَجعَلَ بدَلَ هذه الأحقادِ أُلْفَةً ومَحبَّةً؛ لأنَّ اللهَ تعالى قال: إِنَّمَا الْمُؤْمِنُونَ إِخْوَةٌ، والأُخُوَّةُ يُنافيها الحِقْدُ والعَداوةُ والبَغضاءُ  .

**our explanations:**

- 6-9 ar: المسلمون مثل الإخوة. إذا حصل بينك وبين أخيك خلاف، أزل الغضب من قلبك واجعل مكانه محبة.
- 6-9 en: Muslims are like brothers and sisters. If there is a quarrel between you and your brother, remove the anger from your heart and put love in its place.
- 10-13 ar: يبين التفسير أن الواجب على المسلم أن يزيل ما بينه وبين أخيه من الأحقاد ويجعل بدلها ألفة ومحبة، لأن الله جعل المسلمين كالإخوة، والأخوة لا تجتمع مع الحقد والعداوة والبغضاء.
- 10-13 en: The tafsir explains that a Muslim must remove any grudges between himself and his brother and replace them with closeness and love, because Allah made Muslims like brothers, and brotherhood cannot live alongside grudges, enmity and hatred.

**flags:**

- page 9-10 also covers fighting between two believing groups (v9) - not in excerpt; lesson 6 on 49:10 quotes its words inline (bank verse, in related)

- [x] ok

### 21. [tafsir] Tafsir of 49:11 / تفسير 49:11

- page: https://dorar.net/tafseer/49/4#v11
- values: brotherhood, kind-words
- age: all | level: B | status: seeded | number: 49:11-13 | related: verse:49:11
- book: موسوعة التفسير - الدرر السنية

**arabic_text (verbatim from the page):**

> يَنْهى اللهُ عِبادَه المؤمنينَ أنْ يَسخَرَ قومٌ منهم مِن قومٍ آخَرينَ مؤمنينَ؛ عَسى أنْ يكونوا خَيرًا منهم، وأعظَمَ قدْرًا، ولا يَسخَرْ كذلك نِساءٌ مِن نِساءٍ؛ عَسى أنْ يكُنَّ خيرًا منهنَّ، وأعظَمَ قدْرًا، ويَنْهاهم أنْ يَطعُنَ بعضُهم بعضًا ويَعيبَه، ويَنهاهم أنْ يَتنادَوا بالألقابِ القَبيحةِ الَّتي يَكرَهُها المُنادَى بها، بِئسَ الاسمُ الَّذي تَنالونَه اسمُ الفسوقِ بعْدَ اتِّصافِكم بالإيمانِ، ومَن لم يَتُبْ مِن ذلك فأولئك هم الظَّالِمون.

**our explanations:**

- 6-9 ar: لا تسخر من أحد ولا تناد أحدا بلقب يكرهه. ربما يكون من تسخر منه أفضل منك عند الله.
- 6-9 en: Do not make fun of anyone or call them a name they dislike. The person you mock may be better than you in Allah's sight.
- 10-13 ar: يوضح التفسير أن الآية تنهى المؤمنين، رجالا ونساء، عن السخرية من بعضهم، لأن المسخور منه قد يكون خيرا وأعظم قدرا، وتنهى عن عيب بعضهم بعضا والتنادي بالألقاب القبيحة، وتدعو إلى التوبة من ذلك.
- 10-13 en: The tafsir explains that the verse forbids believers, men and women, from mocking one another, because the one mocked may be better and of higher worth, and forbids finding fault with each other and calling each other hurtful nicknames, calling for repentance from all of this.

**flags:**

- two items from this page (#v11, #v12); المعنى الإجمالي paraphrase of 49:11

- [x] ok

### 22. [tafsir] Tafsir of 49:12 / تفسير 49:12

- page: https://dorar.net/tafseer/49/4#v12
- values: avoiding-backbiting
- age: all | level: B | status: seeded | number: 49:11-13 | related: verse:49:12
- book: موسوعة التفسير - الدرر السنية

**arabic_text (verbatim from the page):**

> وَلَا يَغْتَبْ: الغِيبةُ: أنْ يُذكَرَ الإنْسانُ في غَيْبَتِه بسُوءٍ وإنْ كانَ فيه، وأصْلُ (غيب): يدُلُّ على تَستُّرِ الشَّيءِ عن العُيونِ، والغِيبةُ مِن هذا؛ لأنَّها لا تُقالُ إلَّا في غَيْبَةٍ  .

**our explanations:**

- 6-9 ar: الغيبة هي أن تتكلم عن شخص غائب بشيء يكرهه، حتى لو كان صحيحا. وإخبار والديك أو معلمك عندما يؤذيك أحد أو يؤذي غيرك ليس غيبة، بل هو التصرف الصحيح.
- 6-9 en: Backbiting means saying something about a person who is not there that they would hate, even if it is true. Telling a parent or teacher when someone is hurting you or others is not backbiting; it is the right thing to do.
- 10-13 ar: يشرح التفسير معنى الغيبة في الآية: أن يذكر الإنسان في غيابه بسوء وإن كان فيه، وسميت غيبة لأنها لا تقال إلا في غياب الشخص. وإخبار والديك أو معلمك عندما يؤذيك أحد أو يؤذي غيرك ليس غيبة، بل هو التصرف الصحيح.
- 10-13 en: The tafsir explains the meaning of backbiting in the verse: mentioning a person in their absence with something bad, even if it is true of them; it is called ghibah because it is only said when the person is absent. Telling a parent or teacher when someone is hurting you or others is not backbiting; it is the right thing to do.

**flags:**

- re-cut after review to the غريب الكلمات line for وَلَا يَغْتَبْ (page line 55): the requested sub-line cut of the المعنى الإجمالي paragraph is not possible with --lines, so the word-meaning line (no simile) was taken instead; age all; explanations carry the safeguarding sentence

- [x] ok

### 23. [tafsir] Tafsir of 93:9 / تفسير 93:9

- page: https://dorar.net/tafseer/93/1
- values: caring-for-orphans, gratitude, kind-words
- age: all | level: B | status: seeded | number: 93:1-11 | related: verse:93:9
- book: موسوعة التفسير - الدرر السنية

**arabic_text (verbatim from the page):**

> ثمَّ أمَرَ اللهُ تعالى رَسولَه صلَّى اللهُ عليه وسلَّم بشُكْرِ هذه النِّعَمِ، فقال: فأمَّا اليَتيمَ فلا تُهِنْه ولا تَظْلِمْه، وأمَّا السَّائِلُ فلا تَنهَرْه وتَزجُرْه، وحَدِّثِ النَّاسَ بما أنعَمَ اللهُ به عليك.

**our explanations:**

- 6-9 ar: الله أمر نبيه أن يشكر نعمه بأن يعطف على اليتيم ولا يظلمه، ولا يرد السائل بكلام قاس، ويحدث الناس بنعم الله.
- 6-9 en: Allah told His Prophet to show thanks for His gifts by being gentle to the orphan and never wronging him, never turning away someone who asks with harsh words, and telling people about Allah's gifts.
- 10-13 ar: يوضح التفسير أن الله بعد أن ذكر نعمه على رسوله أمره بشكرها: فلا يهين اليتيم ولا يظلمه، ولا يرد السائل بقسوة ولا يزجره، ويحدث الناس بما أنعم الله عليه. وهذا يعلمنا أن شكر النعمة يكون بالإحسان إلى الضعفاء.
- 10-13 en: The tafsir explains that after Allah listed His blessings on His Messenger, He commanded him to show gratitude for them: never humiliate or wrong the orphan, never rebuke or turn away the one who asks, and speak of Allah's blessings. This teaches us that thanking Allah is shown by kindness to the weak.

**flags:**

- whole surah on one page; المعنى الإجمالي line for 93:9-11 (orphan, asker, blessings); 93:9 is the bank verse

- [x] ok

## aqidah (14)

### 24. [aqidah] What is iman (faith)? / ما هو الإيمان؟

- page: https://dorar.net/aqeeda/15/%D8%A7%D9%84%D9%81%D8%B1%D8%B9-%D8%A7%D9%84%D8%AB%D8%A7%D9%86%D9%8A-%D8%AA%D8%B9%D8%B1%D9%8A%D9%81-%D8%A7%D9%84%D8%A5%D9%8A%D9%85%D8%A7%D9%86-%D8%A7%D8%B5%D8%B7%D9%84%D8%A7%D8%AD%D8%A7
- values: (none)
- age: all | level: A | status: seeded | number: 15
- book: الموسوعة العقدية - الدرر السنية

**arabic_text (verbatim from the page):**

> الإيمانُ في الاصطِلاح هو: التَّصديقُ الجازمُ بكلِّ ما أخبَرَ به اللهُ ورسولُهُ مع الإقرارِ والطُّمأنينةِ، والقَبولُ والانقيادُ له .

**our explanations:**

- 6-9 ar: الإيمان هو أن نصدق بقلوبنا كل ما أخبرنا به الله ورسوله، ونقبله ونطيعه بسعادة.
- 6-9 en: Iman means believing in our hearts everything Allah and His Messenger told us, accepting it and obeying it gladly.
- 10-13 ar: تعرف الموسوعة الإيمان بأنه التصديق الجازم بكل ما أخبر به الله ورسوله، مع الإقرار والطمأنينة والقبول والانقياد. فالإيمان ليس كلمة فقط، بل تصديق في القلب يتبعه قبول وطاعة.
- 10-13 en: The encyclopedia defines iman as firm belief in everything Allah and His Messenger told us, together with acknowledging it, feeling at peace with it, accepting it and following it. So iman is not just a word; it is belief in the heart followed by acceptance and obedience.

**flags:**

- trailing " ." (footnote remnant) stays: a --lines re-cut cannot trim inside a line
- short definition; values left empty (no value truly fits iman itself)

- [x] ok

### 25. [aqidah] What is tawhid? / ما هو التوحيد؟

- page: https://dorar.net/aqeeda/20/%D8%A7%D9%84%D9%81%D8%B1%D8%B9-%D8%A7%D9%84%D8%AB%D8%A7%D9%86%D9%8A-%D8%AA%D8%B9%D8%B1%D9%8A%D9%81-%D8%A7%D9%84%D8%AA%D9%88%D8%AD%D9%8A%D8%AF-%D8%A7%D8%B5%D8%B7%D9%84%D8%A7%D8%AD%D8%A7
- values: sincerity
- age: all | level: A | status: seeded | number: 20
- book: الموسوعة العقدية - الدرر السنية

**arabic_text (verbatim from the page):**

> التَّوحيدُ اصطِلاحًا: إفرادُ اللهِ سُبحانَه بما يختصُّ به من الرُّبوبيَّةِ والألوهيَّةِ والأسماءِ والصِّفاتِ .

**our explanations:**

- 6-9 ar: التوحيد هو أن نعرف أن الله واحد، هو الخالق وحده، ونعبده وحده، وله أسماء وصفات لا يشبهه فيها أحد.
- 6-9 en: Tawhid means knowing that Allah is One: He alone is the Creator, we worship Him alone, and His names and attributes belong to Him alone.
- 10-13 ar: تعرف الموسوعة التوحيد بأنه إفراد الله بما يختص به: فهو وحده الرب الخالق المدبر، وهو وحده المستحق للعبادة، وله الأسماء والصفات الكاملة. التوحيد أكثر من مجرد العد، فهو أن نعطي الله وحده كل ما يخصه.
- 10-13 en: The encyclopedia defines tawhid as singling Allah out in what belongs to Him alone: He alone is the Lord who creates and controls, He alone deserves worship, and His are the perfect names and attributes. Tawhid is more than just counting one; it means giving Allah alone everything that is His.

**flags:**

- trailing " ." (footnote remnant) stays: a --lines re-cut cannot trim inside a line

- [x] ok

### 26. [aqidah] Knowing Allah exists is natural / وجود الله أمر فطري

- page: https://dorar.net/aqeeda/234/%D8%A7%D9%84%D9%81%D8%B5%D9%84-%D8%A7%D9%84%D8%AB%D8%A7%D9%86%D9%8A-%D9%88%D8%AC%D9%88%D8%AF-%D8%A7%D9%84%D9%84%D9%87
- values: (none)
- age: all | level: A | status: seeded | number: 234
- book: الموسوعة العقدية - الدرر السنية

**arabic_text (verbatim from the page):**

> إنَّ وجودَ الله عزَّ وجلَّ أمرٌ فِطْريٌّ، مغروزٌ في النَّفسِ البَشَريَّةِ.

**our explanations:**

- 6-9 ar: الإنسان يعرف في قلبه أن الله موجود. هذا شيء خلقنا الله به من البداية.
- 6-9 en: Deep in the heart, a person knows that Allah exists. Allah created us with this knowledge from the start.
- 10-13 ar: تذكر الموسوعة أن وجود الله أمر فطري مغروز في النفس البشرية، أي أن الإنسان خلق وفي داخله معرفة بوجود ربه قبل أي تعليم أو دليل.
- 10-13 en: The encyclopedia says that knowing Allah exists is innate, planted in the human soul: a person is created with an awareness of his Lord's existence before any teaching or proof.

**flags:**

- only the first sentence of a long page; the rest (hadith, kalam arguments, Jahmiyya) is not taken

- [x] ok

### 27. [aqidah] Worshipping Allah alone (tawhid al-uluhiyya) / توحيد الألوهية: عبادة الله وحده

- page: https://dorar.net/aqeeda/281/%D8%A7%D9%84%D9%85%D8%A8%D8%AD%D8%AB-%D8%A7%D9%84%D8%A3%D9%88%D9%84-%D8%AA%D8%B9%D8%B1%D9%8A%D9%81-%D8%AA%D9%88%D8%AD%D9%8A%D8%AF-%D8%A7%D9%84%D8%A3%D9%84%D9%88%D9%87%D9%8A%D8%A9#def
- values: sincerity
- age: all | level: A | status: seeded | number: 281
- book: الموسوعة العقدية - الدرر السنية

**arabic_text (verbatim from the page):**

> توحيدُ الأُلوهيَّةِ هو: إفرادُ اللهِ عزَّ وجَلَّ بالعِبادةِ في جميعِ أنواعِها .

**our explanations:**

- 6-9 ar: نعبد الله وحده، فلا ندعو غيره ولا نسجد لغيره ولا نتوكل إلا عليه. كل أنواع العبادة لله وحده.
- 6-9 en: We worship Allah alone: we pray to no one else, bow to no one else, and rely on no one else. Every kind of worship is for Allah alone.
- 10-13 ar: تعرف الموسوعة توحيد الألوهية بأنه إفراد الله بالعبادة في جميع أنواعها: الدعاء والصلاة والخوف والرجاء والتوكل وغيرها، فلا يصرف شيء منها لغير الله.
- 10-13 en: The encyclopedia defines tawhid al-uluhiyya as devoting every kind of worship to Allah alone: prayer, supplication, fear, hope, reliance and more, none of which is directed to anyone but Allah.

**flags:**

- trailing " ." (footnote remnant) stays: a --lines re-cut cannot trim inside a line
- two items from this page (#def, #conditions)

- [x] ok

### 28. [aqidah] The two conditions of worship / شرطا العبادة

- page: https://dorar.net/aqeeda/281/%D8%A7%D9%84%D9%85%D8%A8%D8%AD%D8%AB-%D8%A7%D9%84%D8%A3%D9%88%D9%84-%D8%AA%D8%B9%D8%B1%D9%8A%D9%81-%D8%AA%D9%88%D8%AD%D9%8A%D8%AF-%D8%A7%D9%84%D8%A3%D9%84%D9%88%D9%87%D9%8A%D8%A9#conditions
- values: sincerity, love-of-the-prophet
- age: all | level: A | status: seeded | number: 281
- book: الموسوعة العقدية - الدرر السنية

**arabic_text (verbatim from the page):**

> والعِبادةُ لها شَرْطانِ:
> 1- الإخلاصُ لله تعالى فيها.
> 2- المتابَعةُ فيها، أي: أن تكونَ وَفْقَ ما جاء به الرَّسولُ صلَّى اللهُ عليه وسلَّم.

**our explanations:**

- 6-9 ar: لكي يقبل الله عبادتنا نحتاج شيئين: أن نفعلها لله وحده بقلب مخلص، وأن نفعلها كما علمنا النبي صلى الله عليه وسلم.
- 6-9 en: For Allah to accept our worship we need two things: to do it for Allah alone with a sincere heart, and to do it the way the Prophet (peace be upon him) taught us.
- 10-13 ar: تذكر الموسوعة أن للعبادة شرطين: الإخلاص لله تعالى فيها، والمتابعة، أي أن تكون موافقة لما جاء به الرسول صلى الله عليه وسلم. فالعبادة الصحيحة تجمع بين نية خالصة وطريقة صحيحة.
- 10-13 en: The encyclopedia lists two conditions for worship: sincerity to Allah in it, and following the way of the Messenger (peace be upon him). Correct worship combines a pure intention with the right method.

**flags:**

- none

- [x] ok

### 29. [aqidah] Why did Allah create us? / لماذا خلقنا الله؟

- page: https://dorar.net/aqeeda/283/%D8%A7%D9%84%D9%85%D8%A8%D8%AD%D8%AB-%D8%A7%D9%84%D8%AB%D8%A7%D9%86%D9%8A-%D9%85%D9%86%D8%B2%D9%84%D8%A9-%D8%AA%D9%88%D8%AD%D9%8A%D8%AF-%D8%A7%D9%84%D8%A3%D9%84%D9%88%D9%87%D9%8A%D8%A9#purpose
- values: sincerity
- age: all | level: A | status: seeded | number: 283
- book: الموسوعة العقدية - الدرر السنية

**arabic_text (verbatim from the page):**

> 2- توحيدُ الأُلوهيَّةِ يُحَقِّقُ الغايةَ مِن خَلْقِ الإنسانِ، وهي عِبادةُ اللهِ وَحْدَه.

**our explanations:**

- 6-9 ar: الله خلقنا لنعبده وحده. عندما نصلي ونذكر الله ونحسن إلى الناس لوجه الله فنحن نعيش لما خلقنا له.
- 6-9 en: Allah created us to worship Him alone. When we pray, remember Allah and do good for His sake, we are living for what we were created for.
- 10-13 ar: تبين الموسوعة أن توحيد الألوهية يحقق الغاية من خلق الإنسان، وهي عبادة الله وحده. فالهدف من حياتنا ليس اللعب فقط ولا جمع المال، بل عبادة الله في كل ما نقول ونفعل.
- 10-13 en: The encyclopedia explains that worshipping Allah alone fulfils the purpose for which humans were created. The aim of our life is not only play or collecting money but worshipping Allah in all we say and do.

**flags:**

- only point 2 taken; point 1 (shahadatan are the first duty) left out

- [x] ok

### 30. [aqidah] The meaning of la ilaha illa Allah / معنى لا إله إلا الله

- page: https://dorar.net/aqeeda/302/%D8%A7%D9%84%D9%85%D8%B7%D9%84%D8%A8-%D8%A7%D9%84%D8%A3%D9%88%D9%84-%D9%85%D8%B9%D9%86%D9%89-%D8%B4%D9%87%D8%A7%D8%AF%D8%A9-%D9%84%D8%A7-%D8%A5%D9%84%D9%87-%D8%A5%D9%84%D8%A7-%D8%A7%D9%84%D9%84%D9%87
- values: sincerity
- age: all | level: A | status: seeded | number: 302
- book: الموسوعة العقدية - الدرر السنية

**arabic_text (verbatim from the page):**

> معنى لا إلهَ إلَّا اللهُ: لا معبودَ بحَقٍّ إلَّا اللهُ.

**our explanations:**

- 6-9 ar: لا إله إلا الله معناها: لا أحد يستحق أن نعبده إلا الله وحده.
- 6-9 en: La ilaha illa Allah means: no one deserves to be worshipped except Allah alone.
- 10-13 ar: تذكر الموسوعة أن معنى لا إله إلا الله: لا معبود بحق إلا الله. فالكلمة تنفي استحقاق العبادة عن كل شيء سوى الله، وتثبتها لله وحده.
- 10-13 en: The encyclopedia explains that la ilaha illa Allah means: there is none rightfully worshipped except Allah. The phrase denies that anything besides Allah deserves worship and affirms it for Allah alone.

**flags:**

- none

- [x] ok

### 31. [aqidah] The meaning of 'Muhammad is the Messenger of Allah' / معنى شهادة أن محمدا رسول الله

- page: https://dorar.net/aqeeda/348/%D8%A7%D9%84%D9%85%D8%B7%D9%84%D8%A8-%D8%A7%D9%84%D8%A3%D9%88%D9%84-%D9%85%D8%B9%D9%86%D9%89-%D8%B4%D9%87%D8%A7%D8%AF%D8%A9-%D8%A3%D9%86-%D9%85%D8%AD%D9%85%D8%AF%D8%A7-%D8%B1%D8%B3%D9%88%D9%84-%D8%A7%D9%84%D9%84%D9%87
- values: love-of-the-prophet
- age: all | level: A | status: seeded | number: 348
- book: الموسوعة العقدية - الدرر السنية

**arabic_text (verbatim from the page):**

> وقال مُحَمَّدُ بنُ عَبدِ الوَهَّابِ: (معنى شَهادةِ أنَّ مُحمَّدًا رَسولُ اللهِ: طاعتُه فيما أمَرَ، وتصديقُه فيما أخبَرَ، واجتِنابُ ما عنه نهى وزَجَر، وأنْ لا يُعبَدَ اللهُ إلَّا بما شَرَع) .

**our explanations:**

- 6-9 ar: عندما نقول إن محمدا رسول الله، فنحن نصدق كل ما أخبرنا به، ونطيعه في ما أمر، ونبتعد عما نهى عنه، ونعبد الله كما علمنا.
- 6-9 en: When we say Muhammad is the Messenger of Allah, we believe everything he told us, obey what he commanded, stay away from what he forbade, and worship Allah the way he taught.
- 10-13 ar: تبين الموسوعة أن معنى شهادة أن محمدا رسول الله: طاعته فيما أمر، وتصديقه فيما أخبر، واجتناب ما نهى عنه، وأن لا يعبد الله إلا بما شرع. فالشهادة التزام عملي لا كلمة فقط.
- 10-13 en: The encyclopedia explains that the testimony that Muhammad is the Messenger of Allah means obeying what he commanded, believing what he told us, avoiding what he forbade, and worshipping Allah only in the way he taught. The testimony is a practical commitment, not just words.

**flags:**

- excerpt is a quoted scholar (Muhammad ibn Abd al-Wahhab) on the dorar page, not the encyclopedia's own sentence (name removed from our explanations per review). Alternative: lines 38-39 or 51-52 of the page (encyclopedia wording, but each is only half the definition)

- [x] ok

### 32. [aqidah] What is worship (ibadah)? / ما هي العبادة؟

- page: https://dorar.net/aqeeda/360/%D8%A7%D9%84%D9%85%D8%B7%D9%84%D8%A8-%D8%A7%D9%84%D8%AB%D8%A7%D9%86%D9%8A-%D8%AA%D8%B9%D8%B1%D9%8A%D9%81-%D8%A7%D9%84%D8%B9%D8%A8%D8%A7%D8%AF%D8%A9-%D8%A7%D8%B5%D8%B7%D9%84%D8%A7%D8%AD%D8%A7
- values: sincerity
- age: all | level: A | status: seeded | number: 360
- book: الموسوعة العقدية - الدرر السنية

**arabic_text (verbatim from the page):**

> العِبادةُ في الاصطِلاحِ: اسمٌ جامِعٌ لكُلِّ ما يحِبُّه اللهُ ويَرْضاه مِنَ الأقوالِ والأعمالِ؛ الباطِنةِ والظَّاهِرةِ .

**our explanations:**

- 6-9 ar: العبادة هي كل ما يحبه الله من أقوالنا وأفعالنا، في الظاهر وفي القلب. الصلاة عبادة، والصدق عبادة، ومساعدة الناس عبادة.
- 6-9 en: Worship is everything Allah loves from our words and actions, outside and inside the heart. Prayer is worship, honesty is worship, and helping people is worship.
- 10-13 ar: تعرف الموسوعة العبادة بأنها اسم جامع لكل ما يحبه الله ويرضاه من الأقوال والأعمال الباطنة والظاهرة. فهي أوسع من الصلاة والصيام؛ تشمل أعمال القلب كالمحبة والخوف، وأعمال الجسد كالصلاة والإحسان إلى الناس.
- 10-13 en: The encyclopedia defines worship as a comprehensive name for everything Allah loves and is pleased with, in words and deeds, inner and outer. It is wider than prayer and fasting; it includes acts of the heart like love and fear of Allah, and acts of the body like prayer and kindness to people.

**flags:**

- trailing " ." (footnote remnant) stays: a --lines re-cut cannot trim inside a line

- [x] ok

### 33. [aqidah] Belief in the angels / الإيمان بالملائكة

- page: https://dorar.net/aqeeda/1068/%D8%A7%D9%84%D9%85%D8%A8%D8%AD%D8%AB-%D8%A7%D9%84%D8%AB%D8%A7%D9%86%D9%8A-%D9%85%D8%B9%D9%86%D9%89-%D8%A7%D9%84%D8%A5%D9%8A%D9%85%D8%A7%D9%86-%D8%A8%D8%A7%D9%84%D9%85%D9%84%D8%A7%D8%A6%D9%83%D8%A9
- values: (none)
- age: all | level: A | status: seeded | number: 1068
- book: الموسوعة العقدية - الدرر السنية

**arabic_text (verbatim from the page):**

> الإيمانُ بالمَلائِكةِ يتضَمَّنُ أربعةَ أُمورٍ:
> 1- الإيمانُ بوُجودِهم إيمانًا جازمًا لا يتطَرَّقُ إليه شَكٌّ.
> 2- الإيمانُ بما عَلِمْنا من أسمائِهم (كجِبريلَ عليه السَّلامُ)، وأمَّا من لم نعلَمْ أسماءَهم فنُؤمِنُ بهم إجمالًا.
> 3- الإيمانُ بما عَلِمْنا من صفاتِهم الخِلْقيَّةِ والخُلُقيَّةِ.
> 4- الإيمانُ بما عَلِمْنا من أعمالِهم .

**our explanations:**

- 6-9 ar: الملائكة خلق من خلق الله، نؤمن أنهم موجودون، ونعرف أسماء بعضهم مثل جبريل، ونؤمن بما أخبرنا الله عن صفاتهم وأعمالهم.
- 6-9 en: Angels are creatures Allah created. We believe they exist, we know some of their names like Jibril, and we believe what Allah told us about their qualities and their work.
- 10-13 ar: تذكر الموسوعة أن الإيمان بالملائكة يتضمن أربعة أمور: الإيمان بوجودهم إيمانا جازما، والإيمان بمن علمنا أسماءهم كجبريل عليه السلام وبالباقين إجمالا، والإيمان بما علمنا من صفاتهم، والإيمان بما علمنا من أعمالهم.
- 10-13 en: The encyclopedia says belief in the angels includes four things: firm belief that they exist, belief in those whose names we know such as Jibril (peace be upon him) and in the rest generally, belief in what we know of their qualities, and belief in what we know of their work.

**flags:**

- trailing " ." (footnote remnant) stays: a --lines re-cut cannot trim inside a line
- values left empty

- [x] ok

### 34. [aqidah] Belief in Allah's books / الإيمان بكتب الله

- page: https://dorar.net/aqeeda/1320/%D8%A7%D9%84%D9%81%D8%B5%D9%84-%D8%A7%D9%84%D8%AB%D8%A7%D9%86%D9%8A-%D8%AD%D9%83%D9%85-%D8%A7%D9%84%D8%A5%D9%8A%D9%85%D8%A7%D9%86-%D8%A8%D8%A7%D9%84%D9%83%D8%AA%D8%A8
- values: seeking-knowledge
- age: all | level: A | status: seeded | number: 1320
- book: الموسوعة العقدية - الدرر السنية

**arabic_text (verbatim from the page):**

> الإيمانُ بكُتُبِ اللهِ التي أنزلها على رُسُلِه عليهم السَّلامُ ركنٌ عظيمٌ من أركانِ الإيمانِ، فلا يتحقَّقُ الإيمانُ مِن دُونِه.

**our explanations:**

- 6-9 ar: الله أنزل كتبا على رسله ليعلم الناس الخير. الإيمان بكتب الله ركن من أركان الإيمان لا يكتمل الإيمان بدونه.
- 6-9 en: Allah sent down books to His messengers to teach people what is good. Believing in Allah's books is a pillar of faith, and faith is not complete without it.
- 10-13 ar: تبين الموسوعة أن الإيمان بالكتب التي أنزلها الله على رسله ركن عظيم من أركان الإيمان، ولا يتحقق الإيمان من دونه. فطلب العلم من كتاب الله جزء من إيماننا به.
- 10-13 en: The encyclopedia explains that belief in the books Allah sent down to His messengers is a great pillar of faith, and faith is not achieved without it. Seeking knowledge from Allah's book is part of believing in it.

**flags:**

- only the opening sentence; page later has takfir rulings - not taken

- [x] ok

### 35. [aqidah] Belief in the prophets and messengers / الإيمان بالأنبياء والرسل

- page: https://dorar.net/aqeeda/1429/%D8%A7%D9%84%D9%85%D8%A8%D8%AD%D8%AB-%D8%A7%D9%84%D8%A3%D9%88%D9%84-%D8%AD%D9%83%D9%85-%D8%A7%D9%84%D8%A5%D9%8A%D9%85%D8%A7%D9%86-%D8%A8%D8%A7%D9%84%D8%A3%D9%86%D8%A8%D9%8A%D8%A7%D8%A1-%D9%88%D8%A7%D9%84%D8%B1%D8%B3%D9%84-%C2%A0
- values: love-of-the-prophet
- age: all | level: A | status: seeded | number: 1429
- book: الموسوعة العقدية - الدرر السنية

**arabic_text (verbatim from the page):**

> الإيمانُ بأنبياءِ اللهِ تعالى ورُسُلِه رُكنٌ من أركانِ الإيمانِ، وأصلٌ من أصولِه، لا يصحُّ إيمانُ العبدِ إلَّا به.

**our explanations:**

- 6-9 ar: الله أرسل أنبياء ورسلا ليعلموا الناس الخير. الإيمان بهم جميعا ركن من أركان الإيمان.
- 6-9 en: Allah sent prophets and messengers to teach people what is good. Believing in all of them is a pillar of faith.
- 10-13 ar: تبين الموسوعة أن الإيمان بأنبياء الله ورسله ركن من أركان الإيمان وأصل من أصوله، ولا يصح إيمان العبد إلا به. فمحبة النبي صلى الله عليه وسلم واتباعه جزء من هذا الإيمان.
- 10-13 en: The encyclopedia explains that belief in Allah's prophets and messengers is a pillar and foundation of faith, and a person's faith is not valid without it. Loving and following the Prophet (peace be upon him) is part of this belief.

**flags:**

- only the opening sentence

- [x] ok

### 36. [aqidah] Belief in the Last Day / الإيمان باليوم الآخر

- page: https://dorar.net/aqeeda/1664/%D8%A7%D9%84%D9%81%D8%B5%D9%84-%D8%A7%D9%84%D8%A3%D9%88%D9%84-%D9%85%D8%B9%D9%86%D9%89-%D8%A7%D9%84%D8%A5%D9%8A%D9%85%D8%A7%D9%86-%D8%A8%D8%A7%D9%84%D9%8A%D9%88%D9%85-%D8%A7%D9%84%D8%A2%D8%AE%D8%B1
- values: (none)
- age: 10-13 | level: A | status: seeded | number: 1664
- book: الموسوعة العقدية - الدرر السنية

**arabic_text (verbatim from the page):**

> وقال ابنُ عُثَيمين: (اليومُ الآخِرُ: يومُ القيامةِ الذي يُبعَثُ النَّاسُ فيه للحِسابِ والجزاءِ. وسمِّي بذلك لأنَّه لا يومَ بَعْدَه؛ حيث يستقِرُّ أهلُ الجنَّةِ في منازِلِهم، وأهلُ النَّارِ في منازِلِهم) .

**our explanations:**

- 6-9 ar: اليوم الآخر هو يوم القيامة، يبعث الله فيه الناس ليحاسبهم ويجزيهم على أعمالهم. من عمل الخير يفرح في ذلك اليوم.
- 6-9 en: The Last Day is the Day of Judgement, when Allah brings people back to life to judge them and reward them for their deeds. Whoever did good will be happy on that day.
- 10-13 ar: تنقل الموسوعة عن ابن عثيمين أن اليوم الآخر هو يوم القيامة الذي يبعث الناس فيه للحساب والجزاء، وسمي كذلك لأنه لا يوم بعده، حيث يستقر أهل الجنة وأهل النار في منازلهم. الإيمان به يجعلنا نحرص على العمل الصالح.
- 10-13 en: The encyclopedia quotes Ibn Uthaymin: the Last Day is the Day of Resurrection, when people are raised for judgement and reward, and it is called the last because no day comes after it, when the people of Paradise and the people of Hell settle in their places. Believing in it makes us careful to do good.

**flags:**

- age screen [hell_grave]: excerpt contains "النار"; check against the deny-list before use
- real deny-list hit: النار (people of Hell settle in their places). Kept at age 10-13 per review; excerpt is a quoted scholar (Ibn Uthaymin)

- [ ] ok
FIX: age 10-13 -> all, per the lead's decision (Decisions log 2026-10-04 17:10: age_band "all" for every item). Values: none of the 38 values fits; keep empty. Note: the excerpt mentions Hell (flagged deny-list hit); our 6-9 explanation stays gentle.

### 37. [aqidah] The meaning of qadar (divine decree) / معنى القضاء والقدر

- page: https://dorar.net/aqeeda/2449/%D8%A7%D9%84%D9%85%D8%A8%D8%AD%D8%AB-%D8%A7%D9%84%D8%AB%D8%A7%D9%86%D9%8A-%D9%85%D8%B9%D9%86%D9%89-%D8%A7%D9%84%D9%82%D8%B6%D8%A7%D8%A1-%D9%88%D8%A7%D9%84%D9%82%D8%AF%D8%B1-%D8%A7%D8%B5%D8%B7%D9%84%D8%A7%D8%AD%D8%A7
- values: trust-in-allah, patience
- age: 10-13 | level: C | status: seeded | number: 2449
- book: الموسوعة العقدية - الدرر السنية

**arabic_text (verbatim from the page):**

> القَضاءُ والقَدَرُ في الاصطلاحِ: هو تقديرُ اللهِ تعالى الأشياءَ منذُ القِدَمِ، وعِلْمُه سُبحانَه أنها ستقعُ في أوقاتٍ معلومةٍ عنده، وعلى صفاتٍ مخصوصةٍ، وكتابتُه سُبحانَه لذلك، ومشيئتُه له، ووقوعُها على حَسَبِ ما قدَّرها، وخَلْقُه لها( .

- disagreement_note_ar: هذا تعريف مبسط، والأسئلة الأعمق نسأل عنها العلماء.
- disagreement_note_en: This is a simplified definition; deeper questions are for the scholars.

**our explanations:**

- 6-9 ar: الله يعلم كل شيء قبل أن يحدث، وكتبه، وكل ما يحدث فهو بإرادة الله وخلقه. هذا يجعلنا نثق بالله ونصبر.
- 6-9 en: Allah knows everything before it happens and has written it, and everything that happens is by Allah's will and creation. This helps us trust Allah and be patient.
- 10-13 ar: تعرف الموسوعة القضاء والقدر بأنه تقدير الله للأشياء منذ القدم، وعلمه أنها ستقع في أوقات وصفات معلومة عنده، وكتابته لذلك، ومشيئته له، ووقوعها كما قدرها وخلقه لها. وهذا تعريف أساسي، وما وراءه من مسائل يرجع فيها إلى العلماء.
- 10-13 en: The encyclopedia defines qadar as Allah's decreeing of all things from eternity: His knowledge that they will happen at known times and in known ways, His writing of that, His will for it, and their happening as He decreed and created them. This is the basic definition; deeper questions should be taken to scholars.

**flags:**

- qadar pillar: basic definition only; level C with the simplified-definition note, age 10-13 per review; excerpt ends with a stray "( ." from the page - a --lines re-cut cannot trim it (single line), left and flagged

- [ ] ok
FIX: age 10-13 -> all, per the lead's decision (Decisions log 2026-10-04 17:10: age_band "all" for every item).

## fiqh (8)

### 38. [fiqh] The five daily prayers are obligatory / حكم الصلوات الخمس

- page: https://dorar.net/feqhia/677/%D8%A7%D9%84%D9%85%D8%A8%D8%AD%D8%AB-%D8%A7%D9%84%D8%A3%D9%88%D9%84-%D8%AD%D9%83%D9%85-%D8%A7%D9%84%D8%B5%D9%84%D8%A7%D8%A9
- values: prayer
- age: all | level: B | status: seeded | number: 677
- book: الموسوعة الفقهية - الدرر السنية

**arabic_text (verbatim from the page):**

> الصلواتُ الخمسُ فرضُ عينٍ على كلِّ مُسلمٍ مكلَّفٍ.

**our explanations:**

- 6-9 ar: الصلوات الخمس واجبة على كل مسلم بالغ عاقل. تعلم الصلاة مع والديك أو معلمك حتى تؤديها بالطريقة الصحيحة.
- 6-9 en: The five daily prayers are a duty on every adult Muslim who is of sound mind. Learn to pray with your parents or your teacher so they can help you do it the right way.
- 10-13 ar: تذكر الموسوعة أن الصلوات الخمس فرض عين على كل مسلم مكلف، أي واجبة على كل مسلم بالغ عاقل بنفسه. وهذا مما اتفق عليه العلماء. وتفاصيل كيفية الصلاة وأوقاتها اسأل عنها والديك أو معلمك.
- 10-13 en: The encyclopedia states that the five daily prayers are an individual obligation on every Muslim who is adult and of sound mind. Scholars agree on this. For the details of how and when to pray, ask your parents or a teacher.

**flags:**

- agreement wording is on the page (نقل الإجماع: ابن حزم، ابن رشد، النووي، ابن تيمية) but on a separate line, so the excerpt is the ruling sentence only; page also has a section on one who leaves prayer - not taken

- [x] ok

### 39. [fiqh] Facing the qibla in prayer / استقبال القبلة في الصلاة

- page: https://dorar.net/feqhia/857/%D8%A7%D9%84%D9%85%D8%B7%D9%84%D8%A8-%D8%A7%D9%84%D8%A3%D9%88%D9%84-%D8%AD%D9%83%D9%85-%D8%A7%D8%B3%D8%AA%D9%82%D8%A8%D8%A7%D9%84-%D8%A7%D9%84%D9%82%D8%A8%D9%84%D8%A9-%D9%81%D9%8A-%D8%A7%D9%84%D8%B5%D9%84%D8%A7%D8%A9
- values: prayer
- age: all | level: B | status: seeded | number: 857
- book: الموسوعة الفقهية - الدرر السنية

**arabic_text (verbatim from the page):**

> استقبالُ القِبلةِ شرطٌ في صحَّةِ الصَّلاةِ.

**our explanations:**

- 6-9 ar: عندما نصلي نتجه إلى الكعبة في مكة، وهذا اسمه استقبال القبلة. اطلب من والديك أن يعلماك اتجاه القبلة في بيتكم.
- 6-9 en: When we pray we face the Kaaba in Makkah; this is called facing the qibla. Ask your parents to show you the direction of the qibla in your home.
- 10-13 ar: تذكر الموسوعة أن استقبال القبلة شرط في صحة الصلاة، أي أن الصلاة لا تصح بدونه في الحال المعتاد. وهذا مما اتفق عليه العلماء. ولمعرفة اتجاه القبلة والحالات الخاصة اسأل والديك أو معلمك.
- 10-13 en: The encyclopedia states that facing the qibla is a condition for the prayer to be valid, meaning that normally prayer is not valid without it. Scholars agree on this. To find the qibla direction and learn about special cases, ask your parents or a teacher.

**flags:**

- agreement on the page: ابن حزم، ابن عبد البر، ابن رشد، النووي (separate line)

- [x] ok

### 40. [fiqh] Washing the face in wudu / غسل الوجه في الوضوء

- page: https://dorar.net/feqhia/258/%D8%A7%D9%84%D9%85%D8%A8%D8%AD%D8%AB-%D8%A7%D9%84%D8%A3%D9%88%D9%84-%D8%BA%D8%B3%D9%84-%D8%A7%D9%84%D9%88%D8%AC%D9%87
- values: cleanliness, prayer
- age: all | level: B | status: seeded | number: 258
- book: الموسوعة الفقهية - الدرر السنية

**arabic_text (verbatim from the page):**

> غَسلُ الوجهِ فرضٌ من فروضِ الوضوء.

**our explanations:**

- 6-9 ar: في الوضوء نغسل وجهنا، وهذا جزء واجب من الوضوء. اطلب من والديك أن يعلماك كيف تتوضأ.
- 6-9 en: In wudu we wash our face, and this is a required part of wudu. Ask your parents to teach you how to do wudu.
- 10-13 ar: تذكر الموسوعة أن غسل الوجه فرض من فروض الوضوء، أي من أجزائه الواجبة التي لا يصح الوضوء بدونها. وهذا مما اتفق عليه العلماء. ولتعلم صفة الوضوء كاملة اسأل والديك أو معلمك.
- 10-13 en: The encyclopedia states that washing the face is one of the obligatory parts of wudu, without which wudu is not valid. Scholars agree on this. To learn the full way of doing wudu, ask your parents or a teacher.

**flags:**

- agreement on the page: الطحاوي، الماوردي، ابن حزم، ابن عبد البر، ابن رشد، ابن قدامة، النووي (separate line); later sections (beard, mouth/nose) have disagreement - not taken

- [x] ok

### 41. [fiqh] Washing the arms to the elbows in wudu / غسل اليدين إلى المرفقين في الوضوء

- page: https://dorar.net/feqhia/260/%D8%A7%D9%84%D9%85%D8%A8%D8%AD%D8%AB-%D8%A7%D9%84%D8%AB%D8%A7%D9%86%D9%8A-%D8%BA%D8%B3%D9%84-%D8%A7%D9%84%D9%8A%D8%AF%D9%8A%D9%86-%D8%A5%D9%84%D9%89-%D8%A7%D9%84%D9%85%D8%B1%D9%81%D9%82%D9%8A%D9%86
- values: cleanliness, prayer
- age: all | level: B | status: seeded | number: 260
- book: الموسوعة الفقهية - الدرر السنية

**arabic_text (verbatim from the page):**

> غَسْل اليدين إلى المِرفقَينِ، فرضٌ من فروضِ الوضوء.

**our explanations:**

- 6-9 ar: في الوضوء نغسل يدينا من أطراف الأصابع إلى المرفقين، وهذا جزء واجب من الوضوء. اطلب من والديك أن يعلماك كيف تتوضأ.
- 6-9 en: In wudu we wash our arms from the fingertips up to the elbows, and this is a required part of wudu. Ask your parents to teach you how to do wudu.
- 10-13 ar: تذكر الموسوعة أن غسل اليدين إلى المرفقين فرض من فروض الوضوء. وهذا مما اتفق عليه العلماء. ولتعلم صفة الوضوء كاملة اسأل والديك أو معلمك.
- 10-13 en: The encyclopedia states that washing the arms up to the elbows is one of the obligatory parts of wudu. Scholars agree on this. To learn the full way of doing wudu, ask your parents or a teacher.

**flags:**

- agreement on the page: الشافعي، الطبري، ابن المنذر، الطحاوي، ابن حزم، ابن عبد البر، ابن رشد، النووي (separate line); four schools agree elbows included

- [x] ok

### 42. [fiqh] Fasting Ramadan is obligatory / حكم صوم رمضان

- page: https://dorar.net/feqhia/2666/%D8%A7%D9%84%D9%85%D8%A8%D8%AD%D8%AB-%D8%A7%D9%84%D8%A3%D9%88%D9%84-%D8%AD%D9%83%D9%85-%D8%B5%D9%88%D9%85-%D8%B4%D9%87%D8%B1-%D8%B1%D9%85%D8%B6%D8%A7%D9%86
- values: (none)
- age: all | level: B | status: seeded | number: 2666
- book: الموسوعة الفقهية - الدرر السنية

**arabic_text (verbatim from the page):**

> صَومُ شَهرِ رمضانَ فريضةٌ، وركنٌ مِن أركانِ الإسلامِ.

**our explanations:**

- 6-9 ar: صوم شهر رمضان واجب على المسلمين، وهو ركن من أركان الإسلام. اسأل والديك متى تبدأ الصوم وكيف.
- 6-9 en: Fasting the month of Ramadan is a duty for Muslims and one of the pillars of Islam. Ask your parents when and how you should start fasting.
- 10-13 ar: تذكر الموسوعة أن صوم شهر رمضان فريضة وركن من أركان الإسلام. وهذا مما اتفق عليه العلماء. ومن يجب عليه الصوم ومن يعذر وتفاصيل الصيام اسأل عنها والديك أو معلمك.
- 10-13 en: The encyclopedia states that fasting Ramadan is an obligation and one of the pillars of Islam. Scholars agree on this. For who must fast, who is excused and the details of fasting, ask your parents or a teacher.

**flags:**

- agreement on the page: ابن قدامة، النووي، ابن تيمية (separate line); values left empty (no fasting value in values.json)

- [ ] ok
FIX: values (none) -> add `patience` (fasting trains patience).

### 43. [fiqh] Zakah is obligatory / حكم الزكاة

- page: https://dorar.net/feqhia/2094/%D8%A7%D9%84%D9%85%D8%B7%D9%84%D8%A8-%D8%A7%D9%84%D8%A3%D9%88%D9%84-%D8%AD%D9%83%D9%85-%D8%A7%D9%84%D8%B2%D9%83%D8%A7%D8%A9
- values: charity, generosity
- age: all | level: B | status: seeded | number: 2094
- book: الموسوعة الفقهية - الدرر السنية

**arabic_text (verbatim from the page):**

> الزَّكاة فريضةٌ مِنْ فرائض الدِّينِ، وهي الرُّكنُ الثَّالثُ مِن أركانِ الإسلامِ الخمسةِ.

**our explanations:**

- 6-9 ar: الزكاة هي جزء من المال يعطيه المسلم الذي يملك مالا كثيرا للفقراء كل سنة، وهي ركن من أركان الإسلام. والداك يعرفان تفاصيلها فاسألهما.
- 6-9 en: Zakah is a share of money that a Muslim who owns enough wealth gives to the poor every year, and it is one of the pillars of Islam. Your parents know its details, so ask them.
- 10-13 ar: تذكر الموسوعة أن الزكاة فريضة من فرائض الدين، وهي الركن الثالث من أركان الإسلام الخمسة. وهذا مما اتفق عليه العلماء. وتفاصيل من تجب عليه وكم يخرج اسأل عنها والديك أو معلمك.
- 10-13 en: The encyclopedia states that zakah is one of the religion's obligations and the third of the five pillars of Islam. Scholars agree on this. For the details of who must pay it and how much, ask your parents or a teacher.

**flags:**

- agreement on the page: ابن حزم، ابن رشد، ابن قدامة، النووي (separate line)

- [x] ok

### 44. [fiqh] Voluntary charity is recommended / حكم صدقة التطوع

- page: https://dorar.net/feqhia/2607/%D8%A7%D9%84%D9%85%D8%A8%D8%AD%D8%AB-%D8%A7%D9%84%D8%A3%D9%88%D9%84-%D8%AD%D9%83%D9%85-%D8%B5%D8%AF%D9%82%D8%A9-%D8%A7%D9%84%D8%AA%D8%B7%D9%88%D8%B9
- values: charity, generosity
- age: all | level: B | status: seeded | number: 2607
- book: الموسوعة الفقهية - الدرر السنية

**arabic_text (verbatim from the page):**

> صدقة التطوُّع مُستحبَّةٌ.

**our explanations:**

- 6-9 ar: الصدقة هي أن تعطي من مالك للمحتاج من غير أن يكون واجبا عليك، وهي عمل يحبه الله ويستحب فعله. تحدث مع والديك عن كيف تتصدق.
- 6-9 en: Sadaqah is giving from what you have to someone in need, even when it is not required of you; it is something Allah loves and encourages. Talk with your parents about how you can give.
- 10-13 ar: تذكر الموسوعة أن صدقة التطوع مستحبة، أي أنها عمل مرغوب فيه يثاب عليه المسلم وليس واجبا. وهذا مما اتفق عليه العلماء. ولمعرفة أفضل طرق الصدقة اسأل والديك أو معلمك.
- 10-13 en: The encyclopedia states that voluntary charity is recommended: a praiseworthy deed a Muslim is rewarded for, though not obligatory. Scholars agree on this. To learn the best ways to give, ask your parents or a teacher.

**flags:**

- agreement on the page: النووي، ابن حجر الهيتمي، البهوتي (separate line)

- [x] ok

### 45. [fiqh] Kindness to parents is their right / بر الوالدين من حقوقهما

- page: https://dorar.net/feqhia/5390/%D8%A7%D9%84%D9%85%D8%A8%D8%AD%D8%AB-%D8%A7%D9%84%D8%A3%D9%88%D9%84-%D9%85%D9%86-%D8%AD%D9%82%D9%88%D9%82-%D8%A7%D9%84%D9%88%D8%A7%D9%84%D8%AF%D9%8A%D9%86-%D8%B9%D9%84%D9%89-%D8%A7%D9%84%D8%A3%D9%88%D9%84%D8%A7%D8%AF-%D8%A8%D8%B1-%D8%A7%D9%84%D9%88%D8%A7%D9%84%D8%AF%D9%8A%D9%86
- values: honouring-parents, family-ties
- age: all | level: B | status: seeded | number: 5390
- book: الموسوعة الفقهية - الدرر السنية

**arabic_text (verbatim from the page):**

> من حُقوقِ الوالِدَينِ على الأولاد: بِرُّهما.

**our explanations:**

- 6-9 ar: من حق والديك عليك أن تبرهما: تطيعهما في الخير وتتكلم معهما بأدب وتساعدهما. اسأل والديك كيف تكون بارا بهما أكثر.
- 6-9 en: Your parents have a right over you: to treat them well, obey them in what is good, speak to them politely and help them. Ask your parents how you can be even kinder to them.
- 10-13 ar: تذكر الموسوعة أن من حقوق الوالدين على الأولاد برهما، أي الإحسان إليهما بالقول والفعل. ولمعرفة كيف تبر والديك في المواقف المختلفة اسأل والديك أو معلمك.
- 10-13 en: The encyclopedia states that among the rights parents have over their children is kindness to them, meaning goodness in word and deed. To learn how to honour your parents in different situations, ask your parents or a teacher.

**flags:**

- no إجماع wording on the page; plain general statement, level B

- [x] ok

## sirah (5)

### 46. [sirah] The birth of the Prophet (peace be upon him) / ولادة النبي صلى الله عليه وسلم

- page: https://dorar.net/history/event/1
- values: love-of-the-prophet
- age: all | level: C | status: seeded | number: 1
- book: الموسوعة التاريخية - الدرر السنية

**arabic_text (verbatim from the page):**

> اختلفَ أهلُ السِّيَر والتَّاريخِ في تحديدِ يومِ وشهرِ وِلادتِه صلى الله عليه وسلم واتَّفقوا على أنَّ مِيلادَه صلى الله عليه وسلم كان يومَ الاثنينِ من عامِ الفيلِ.

- disagreement_note_ar: اتفق العلماء أن النبي صلى الله عليه وسلم ولد يوم الاثنين في عام الفيل، واختلفوا في الشهر واليوم بالضبط.
- disagreement_note_en: Scholars agree the Prophet (peace be upon him) was born on a Monday in the Year of the Elephant; they differ on the exact month and day.

**our explanations:**

- 6-9 ar: ولد النبي صلى الله عليه وسلم يوم الاثنين في عام الفيل. العلماء متفقون على ذلك، لكنهم مختلفون في الشهر واليوم بالضبط.
- 6-9 en: The Prophet (peace be upon him) was born on a Monday in the Year of the Elephant. Scholars agree on this, but they differ on the exact month and day.
- 10-13 ar: تذكر الموسوعة أن أهل السير والتاريخ اختلفوا في تحديد يوم وشهر ولادة النبي صلى الله عليه وسلم، واتفقوا على أن ميلاده كان يوم الاثنين من عام الفيل. فالعام واليوم من الأسبوع متفق عليهما، والتاريخ الدقيق مختلف فيه.
- 10-13 en: The encyclopedia says the biographers and historians differ on the exact day and month of the Prophet's birth (peace be upon him), but agree that he was born on a Monday in the Year of the Elephant. So the year and the weekday are agreed; the precise date is not.

**flags:**

- sentence cut (--lines 43 --sentences 1): first sentence only; page notes disagreement on the day/month: level C with disagreement note. The rest of the paragraph (quoted narrations, orphanhood) is not taken

- [x] ok

### 47. [sirah] Hilf al-Fudul: the pact to help the wronged / حلف الفضول

- page: https://dorar.net/history/event/8
- values: justice, helping-others, cooperation
- age: all | level: A | status: seeded | number: 8
- book: الموسوعة التاريخية - الدرر السنية

**arabic_text (verbatim from the page):**

> وهذا الحِلفُ تُنافي رُوحهُ الحَميَّة الجاهليَّة التي كانت العصبيَّة تُثيرها، ويُقال في سببِ هذا الحِلفِ: إنَّ رجلًا من زُبَيْد قَدِم مكَّةَ ببِضاعةٍ، واشتراها منه العاصُ بنُ وائلٍ السَّهميُّ، وحَبس عنه حقَّه، فاستعدى عليهِ الأَحلافَ عبدَ الدَّارِ ومَخزومًا، وجُمَحًا, وسَهْمًا وعَدِيًّا فلم يَكترِثوا له، فَعَلَا جبلَ أبي قُبَيْسٍ، ونادى بأشعارٍ يصِف فيها ظلامتَه رافعًا صوتَه، فمشى في ذلك الزُّبيرُ بنُ عبدِ المطَّلب، وقال: ما لهذا مَتْرَكٌ. حتَّى اجتمعوا فعقدوا الحِلفَ الذي عُرف بحِلفِ الفُضولِ, ثمَّ قاموا إلى العاصِ بنِ وائلٍ فانتزعوا منه حَقَّ الزُّبيديِّ.

**our explanations:**

- 6-9 ar: جاء تاجر إلى مكة فأخذ رجل بضاعته ولم يعطه حقه، ولم يساعده أحد. فنادى بصوت عال يشكو ظلمه، فقام ناس من قريش واتفقوا على عهد يساعدون فيه المظلوم، وأرجعوا له حقه.
- 6-9 en: A merchant came to Makkah, and a man took his goods without paying him, and no one helped him. He called out loudly about the wrong done to him, so some people of Quraysh made a pact to help the wronged, and they got his right back for him.
- 10-13 ar: تذكر الموسوعة أن روح حلف الفضول تخالف العصبية الجاهلية، وأن سببه أن رجلا من زبيد باع بضاعة للعاص بن وائل فحبس عنه حقه، واستنجد بالأحلاف فلم يهتموا، فصعد جبل أبي قبيس ينادي بظلامته، فقام الزبير بن عبد المطلب وقال إن هذا لا يترك، حتى اجتمعوا وعقدوا الحلف، ثم أخذوا من العاص حق الرجل. فالعدل يعني أن نقف مع المظلوم حتى يرجع له حقه.
- 10-13 en: The encyclopedia says the spirit of Hilf al-Fudul was the opposite of tribal partisanship, and that it began when a man from Zubayd sold goods to al-As ibn Wa'il, who withheld his payment; the man appealed to the clans, who ignored him, so he climbed Mount Abu Qubays calling out his grievance. Al-Zubayr ibn Abd al-Muttalib said this could not be left, people gathered and made the pact, and then they recovered the man's right from al-As. Justice means standing with the wronged until their right is restored.

**flags:**

- sentence cut (--lines 43 --sentences 3-4): the story of the wronged Zubaydi merchant and the pact. Sentences 1-2 (tribes, meeting at Ibn Jud'an's house, the pledge, the Prophet's witnessing) were not taken because sentence 2 ends with his quoted saying; no prophetic speech in the cut (al-Zubayr's "ما لهذا مترك" is a companion-era remark, not hadith)

- [x] ok

### 48. [sirah] The trustworthy one places the Black Stone / النبي الأمين يضع الحجر الأسود

- page: https://dorar.net/history/event/11
- values: trustworthiness, justice, cooperation
- age: all | level: A | status: seeded | number: 11
- book: الموسوعة التاريخية - الدرر السنية

**arabic_text (verbatim from the page):**

> عن مُجاهدٍ، عن مَولاهُ أنَّه حدَّثه: أنَّه كان فيمن يَبني الكعبةَ في الجاهليَّةِ... قال: فَبَنَيْنا حتَّى بلغنا موضعَ الحَجَرِ وما يَرى الحَجَرَ أحدٌ، فإذا هو وَسْطَ حِجارتِنا مِثلَ رأسِ الرَّجلِ، يَكادُ يَتراءى منه وجهُ الرَّجلِ، فقال بطنٌ من قُريشٍ: نحن نَضعهُ. وقال آخرون: نحن نَضعهُ. فقالوا: اجعلوا بينكم حَكَمًا. قالوا: أوَّلُ رجلٍ يَطلُعُ مِنَ الفَجِّ. فجاء النَّبيُّ صلى الله عليه وسلم، فقالوا: أتاكمُ الأَمينُ. فقالوا له، فوضعهُ في ثوبٍ ثمَّ دعا بُطونَهم فأخذوا بنواحيه معهُ، فوضعهُ هو صلَّى الله عَليهِ وسلَّم.

**our explanations:**

- 6-9 ar: عندما بنت قريش الكعبة تخاصموا من يضع الحجر الأسود. فاختاروا أول من يدخل، فجاء النبي صلى الله عليه وسلم فقالوا: جاء الأمين، فوضع الحجر في ثوب وحمله كلهم معه.
- 6-9 en: When Quraysh rebuilt the Kaaba they argued over who should place the Black Stone. They chose the first person to come in, and it was the Prophet (peace be upon him). They said: the trustworthy one has come. He put the stone in a cloth and they all carried it together.
- 10-13 ar: تذكر الموسوعة أن قريشا لما بنت الكعبة قبل الإسلام اختلفت القبائل في من يضع الحجر الأسود، فاتفقوا على تحكيم أول من يطلع عليهم، فكان النبي صلى الله عليه وسلم، فقالوا: أتاكم الأمين. فوضع الحجر في ثوب ودعا القبائل فأخذوا بنواحيه معه، ثم وضعه هو بيده. فحل الخلاف بالعدل وأشرك الجميع.
- 10-13 en: The encyclopedia tells how, when Quraysh rebuilt the Kaaba before Islam, the clans disagreed over who should set the Black Stone in place. They agreed to let the first person to arrive decide, and it was the Prophet (peace be upon him); they said: the trustworthy one has come to you. He placed the stone on a cloth, called the clans to hold its edges together, then set it in place himself, solving the dispute fairly and including everyone.

**flags:**

- whole event paragraph; narration in Ahmad (from Mujahid's mawla); only speech is Quraysh's «أتاكم الأمين»

- [x] ok

### 49. [sirah] Building the mosque of Quba / بناء مسجد قباء

- page: https://dorar.net/history/event/43
- values: prayer
- age: all | level: A | status: seeded | number: 43
- book: الموسوعة التاريخية - الدرر السنية

**arabic_text (verbatim from the page):**

> لَبِثَ رسولُ الله صلى الله عليه وسلم في بني عَمرِو بنِ عَوفٍ بِقُباءٍ بِضعَ عشرةَ ليلةً، وأسَّسَ فيها المسجدَ الذي أُسِّسَ على التَّقوىَ، وصلَّى فيه رسولُ الله صلى الله عليه وسلم.

**our explanations:**

- 6-9 ar: عندما وصل النبي صلى الله عليه وسلم إلى قباء قرب المدينة، بقي هناك أياما وبنى مسجدا وصلى فيه.
- 6-9 en: When the Prophet (peace be upon him) reached Quba near Madinah, he stayed there some days, built a mosque and prayed in it.
- 10-13 ar: تذكر الموسوعة أن النبي صلى الله عليه وسلم أقام في بني عمرو بن عوف بقباء بضع عشرة ليلة، وأسس فيها المسجد الذي أسس على التقوى وصلى فيه. فكان من أول أعماله بعد الهجرة بناء مكان للصلاة.
- 10-13 en: The encyclopedia says the Prophet (peace be upon him) stayed with Banu Amr ibn Awf in Quba for a little over ten nights, founded there the mosque built on taqwa, and prayed in it. One of his first acts after the migration was building a place for prayer.

**flags:**

- none

- [x] ok

### 50. [sirah] Brotherhood between the Muhajirun and the Ansar / المؤاخاة بين المهاجرين والأنصار

- page: https://dorar.net/history/event/45
- values: brotherhood, helping-others
- age: all | level: A | status: seeded | number: 45
- book: الموسوعة التاريخية - الدرر السنية

**arabic_text (verbatim from the page):**

> كان مِن آثارِ هِجرتِه صلى الله عليه وسلم وأصحابِه إلى المدينةِ تلك المُؤاخاةُ التي حَدثت بين المُهاجرين والأنصارِ رضي الله عنهم، حتَّى كان يَرِثُ بعضُهم بعضًا في أوَّلِ الأمرِ.

**our explanations:**

- 6-9 ar: عندما هاجر النبي صلى الله عليه وسلم وأصحابه إلى المدينة، جعل بين المهاجرين والأنصار أخوة خاصة، حتى صاروا كالإخوة الحقيقيين.
- 6-9 en: When the Prophet (peace be upon him) and his companions moved to Madinah, he made a special brotherhood between the Muhajirun and the Ansar, so they became like real brothers.
- 10-13 ar: تذكر الموسوعة أن من آثار هجرة النبي صلى الله عليه وسلم وأصحابه إلى المدينة المؤاخاة التي حدثت بين المهاجرين والأنصار، حتى كان بعضهم يرث بعضا في أول الأمر. فالأخوة في الدين كانت قوية إلى درجة أنها شبهت أخوة النسب في البداية.
- 10-13 en: The encyclopedia says that one result of the migration of the Prophet (peace be upon him) and his companions to Madinah was the brotherhood made between the Muhajirun and the Ansar, so strong that at first they even inherited from one another. Brotherhood in faith was treated, at the start, like family ties.

**flags:**

- sentence cut (--lines 43 --sentences 1): the context sentence only; the rest of the line carries inline Quran (4:33, not in the bank) and the Anas/Ibn Awf narrations - not taken

- [x] ok
