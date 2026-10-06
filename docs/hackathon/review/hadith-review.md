# Hadith review sheet (lead)

Branch `cloud/hadith-review`. Built from `backend/session_moral_context/content/drafts/hadith/` (104 drafts, 94 unique dorar pages after merging 10 duplicates). Output: `drafts/hadith/items-<value>.json`, status `unverified`, `content_level` A, `age_band` all. Nothing here is seeded: `seed_content` never reads `drafts/`.

**Integrity:** `arabic_text`, book, number, narrator, grade, grader, `source_site` and `source_url` are copied from the draft JSON by script and SHA-256-checked after writing (0 differences). Explanations are written without harakat (the file tool reorders combining marks), and none copies 5 or more consecutive words of the hadith. The Arabic excerpt below is copied programmatically.

**Explanations** were written by AI agents in our own words (6-9 and 10-13) and reviewed by an Opus reviewer. They are not scripture and must be shown under the "In simple words (AI-assisted)" header.

## How to review

1. For each item open the dorar link, check book, number and grade, and that the explanations are faithful and child-appropriate.
2. Tick `- [x] ok`, or write a note under the item. For flagged items decide: keep, rewrite the explanation, or drop.
3. Then move accepted items into `content/items/<value>.json` and mark them with `tools/mark_reviewed.py` (only the lead marks `reviewed`).

## Summary

- Suitability (agent suggestion): ok 57, caution 36, suggest_exclude 1.
- Flagged items: 63.
- Values covered: 38 of 38.

### Flagged items (decide these first)

| Ref | Values | Suitability | Flags |
|---|---|---|---|
| [B6472](#ffxwurix) | trust-in-allah | suggest_exclude | **sensitive_aqidah**: Mentions not believing in bad omens (tatayyur) and not seeking ruqya. Both are nuanced; I explained omens only as 'bad luck signs' and did not discuss ruqya at all, because children could wrongly conclude that seeking treatment or recitation for healing is bad.; **paradise_exclusion**: The 'seventy thousand without reckoning' wording can leave a child feeling they are not among them. I kept it positive in the older text and softened it to 'great generosity' for ages 6-9.; **fiqh_ruling**: The ruqya clause is debated by scholars, so I avoided giving any view. The older text adds that trusting Allah does not forbid seeking treatment or advice, which is not in the hadith text; it is a safety note and the lead should confirm or remove it.; **hard_to_explain**: Hard to explain without a scholar's commentary on ruqya and omens. Fallback if kept: show with caution. |
| [B1419](#n5bhcv9r) | charity | caution | **death**: The hadith refers to the soul reaching the throat (the moment of death) as the time when it is too late. I only said 'too late' and 'wait'.; **fear**: Mentions fear of poverty and hope for wealth. I framed it as the normal feeling that makes giving hard. |
| [B1442](#jeefxyso) | charity, generosity | caution | **curse**: The second angel's supplication is a prayer for loss or ruin for the one who withholds. I did not repeat it; the older text only says holding back is not good. |
| [B1477](#s8dlucam) | not-wasting | caution | **hard_to_explain**: The phrase about asking too much (kathrat al-su'al) is interpreted by scholars as either begging for money or asking needless or trouble-making questions. I kept it general so children are not discouraged from asking questions; please check. Same hadith as M593 (item LYu00ER7).; **other**: Duplicate teaching with Muslim 593 (LYu00ER7); consider keeping only one in the child-facing set.; **other**: Same hadith as M593 (LYu00ER7). Reviewer suggests keeping this one and dropping M593. |
| [B15](#oi2csit1) | love-of-the-prophet | caution | **sensitive_aqidah**: The hadith negates faith until the Prophet is dearer than parents and children. Phrased positively; do not use it to make a child doubt their own faith or love for their parents.; **fear**: The last sentence of the older explanation (loving him helps us treat our family better) is a gentle pastoral addition, not text of the hadith; please check you are comfortable with it. |
| [B2444](#efuzdeaq) | justice | caution | **other**: Could be misread as tribal loyalty or physical restraint; explanation frames it as gently stopping a friend from being unfair. The hadith's wording about restraining his hands is not repeated. |
| [B33](#okbhqvcn) | keeping-promises, trustworthiness | caution | **sensitive_aqidah**: The hadith calls these three traits the sign of a hypocrite (munafiq). The explanation avoids the label and focuses on the good habits.; **fear**: Risk of making a child feel condemned for lying or breaking a promise; keep tone gentle. |
| [B34](#ngdfwh3p) | keeping-promises | caution | **sensitive_aqidah**: Calls these traits a mark of hypocrisy (nifaq). The explanation leaves the word out and teaches the opposite traits, so no child is labelled a hypocrite.; **fear**: A child with a lying or promise-breaking habit might feel frightened or condemned; keep the tone about practising the good habit. |
| [B3472](#wq3kzaeq) | honesty | caution | **marriage_or_adult**: The wise man's solution is to marry the first man's boy to the other's girl and spend on them from the gold plus charity. Explanations omit the marriage and say only that the gold went to good and charity.; **other**: The Arabic text starts directly with the story (an account of earlier people) without a 'the Prophet said' intro; please confirm on the dorar page that this is the full Bukhari narration and that it is attributed to the Prophet. Explanations call it a story told in this hadith. |
| [B5641](#9wln0py9) | patience | caution | **other**: Links hardship with erasing sins. Risk that a sick or suffering child concludes that their pain is a punishment; the explanation presents it only as comfort and does not say why hardship happens. Please keep that framing. |
| [B5653](#gquvjjkf) | patience | caution | **other**: About blindness or loss of sight as a test. A child with a visual impairment or a blind relative might be affected; explanation says the reward is for patience and does not imply that the disability is a punishment. Please decide whether to show this item to a child with a disability.; **sensitive_aqidah**: This is a hadith qudsi (Allah speaking) about a divine promise; explanation kept to reward for patience only. |
| [B5984](#amxkzxia) | family-ties | caution | **paradise_exclusion**: Hadith says the one who cuts (family ties) will not enter Paradise. Explanation gives only the positive action and does not mention exclusion. Scholars read the word as the one who cuts kinship ties (Bukhari chapter context); the Arabic text itself does not say what is cut. |
| [B6094](#aoxeic09) | honesty | caution | **fire_or_punishment**: Second half says lying leads to wickedness and wickedness leads to the Fire. Explanations focus on truthfulness leading to goodness and Paradise and only say lying leads toward wrongdoing; the Fire is not mentioned. |
| [B6115](#ltmcgvb1) | controlling-anger | caution | **sensitive_aqidah**: Mentions Shaytan as the source of anger. Explained simply as asking Allah's protection. I did not quote the phrase; the lead may want to show it from the bank.; **other**: The story has two men insulting each other, and the angry man answers back 'I am not mad'. I left the ending out; it can sound like name-calling about mental health. |
| [B6117](#zulwpkpt) | modesty | caution | **other**: The Arabic text includes a side exchange where Imran rebukes Bushayr sharply for quoting a written saying. The explanation uses only the main teaching and the dignity and calm remark, and leaves the rebuke out. |
| [B6313](#gdqbrhef) | trust-in-allah | caution | **death**: The hadith ends with the promise about dying that night on the fitra. I left this out of both texts to avoid worrying children at bedtime and focused on trust and calm. If the card shows the full Arabic, a parent may want to be ready to answer questions. |
| [B6499](#zsak0gof) | sincerity | caution | **fear**: The hadith is a warning that Allah will expose the intentions of the one who shows off. The wording is a bit scary, so I focused on what to do (sincerity) and did not describe the consequence. I also read it with the standard commentary meaning, which the lead may want to check on dorar. |
| [B6953](#xwsltk8a) | sincerity | caution | **marriage_or_adult**: The hadith contains a clause about migrating to marry a woman. I left marriage out entirely and described it as 'something worldly'. The lead should decide whether the card should show the Arabic in full or only the first sentence. |
| [B71](#dmrsq583) | seeking-knowledge | caution | **hard_to_explain**: The second half (the Prophet only distributes while Allah gives, and this community will stay upright on Allah's command until His decree comes, unharmed by those who differ) is hard for children and touches the idea of the saved community. I explained only the first half and the giving-by-Allah point; the lead may want to quote only the first clause. |
| [M102](#mnim7gsx) | honesty | caution | **other**: Ends with a disowning phrase about the one who cheats (literally: not from me). Wording softened to 'does not fit a Muslim'; scholars discuss whether it means not following the Prophet's way. Explanation does not dwell on it. |
| [M105](#8c6iigij) | avoiding-backbiting | caution | **paradise_exclusion**: The hadith says the tale-bearer will not enter Paradise. I left the warning out and taught the positive action (make peace, speak well). |
| [M1631](#j8bvod7a) | seeking-knowledge | caution | **death**: The hadith is about what continues after a person dies. I used gentle wording ('a very long time' for ages 6-9, 'passed on from this world' for older) and kept the focus on lasting good. A child may worry about parents dying; the lead may want a parent-facing note. |
| [M1827](#uanc2wo9) | justice | caution | **sensitive_aqidah**: Mentions pulpits of light at the right of Allah and His two right hands. The explanation deliberately does not describe this; if the child asks, refer to a parent or teacher. |
| [M1956](#asyxndqh) | kindness-to-animals | caution | **violence_or_blood**: The hadith is about tying animals up to be killed or shot at for sport. The explanation says only: do not hurt or trap animals for fun.; **other**: Reviewer: rated caution to match M1958; wording fixed so it cannot be read as a ban on keeping pets. |
| [M1958](#yoxnxl0l) | kindness-to-animals | caution | **curse**: The hadith contains a curse (la'n) by Ibn Umar and the Prophet's curse on those who do this. Explanation avoids the curse and says only that Allah does not like it and that it was strongly disapproved.; **violence_or_blood**: Scene of young men shooting arrows at a tied bird. Described in softened terms only. |
| [M2020](#bra8od5d) | table-manners | caution | **sensitive_aqidah**: Mentions the Shaytan eating with his left hand. Gentle in the older text only; the younger text does not name him.; **fiqh_ruling**: Scholars differ on whether this is recommended or obligatory, and left-handed children may feel bad. I gave no ruling and added a line telling the older child to ask a parent or teacher; the lead may want a note on left-handed children. |
| [M2034](#jnf9gyef) | not-wasting | caution | **other**: Mentions Satan and the practical etiquette of eating fallen food and licking fingers. Hygiene is left to parents (I added: ask a grown-up if unsure it is clean); the explanation is about not wasting food and does not set any rule.; **fiqh_ruling**: Contains specific eating etiquette (adab); kept to the general principle only. |
| [M223](#tvssnrwa) | cleanliness | caution | **hard_to_explain**: A long hadith with many separate themes. Meaning of 'purity is half of faith' is also discussed by scholars (wudu, cleanliness or purity in general). I used only the cleanliness and wudu reading and the list of good deeds.; **fear**: The ending says the Quran is a proof for or against you and that each person either frees himself or destroys himself. I left it out entirely.; **sensitive_aqidah**: Mentions the scale of deeds and the Quran as proof for or against. Not explained to children. |
| [M233](#lshtdt24) | prayer | caution | **fiqh_ruling**: Scholars discuss what exactly is forgiven (minor sins) and what the condition of avoiding major sins means. The explanation keeps it general, without giving any ruling, and tells the child to ask elders.; **other**: Mentions major sins (kaba'ir) as a condition; the explanation refers to them only as big sins to avoid and does not list any. |
| [M2551](#bk5vx0fu) | honouring-parents, respecting-elders | caution | **curse**: Opens with an idiom of strong disapproval repeated three times (literally: may his nose be rubbed in dust). Not quoted or explained; explanation gives only the positive action.; **paradise_exclusion**: The one who reaches his parents in old age and still does not enter Paradise. Explanation says only that caring for old parents is a chance to earn Allah's pleasure and Paradise. |
| [M2553](#bq8mtkbl) | good-character | caution | **other**: The heart-unease test for sin could be over-applied by anxious or scrupulous children, and scholars treat it as applying to a sound heart and unclear matters, not as a replacement for knowledge. Explanations add a referral to parents, teacher or scholar. Not a fiqh ruling. |
| [M2558](#0wka5jtk) | family-ties | caution | **fire_or_punishment**: The Prophet's reply likens the relatives' situation to feeding them hot ashes. I left the simile out.; **hard_to_explain**: The simile (usually read as a reference to the relatives' own wrongdoing and the burden on them) needs scholarly commentary; I only used the positive guidance and the promise of Allah's help.; **other**: Sensitive for children whose relatives treat them badly or unsafely. The text could be read as 'put up with mistreatment'. Consider adding a note that a child should always tell a parent or trusted adult if someone hurts them.; **other**: Reviewer: added a safety line (tell a trusted grown-up if anyone hurts or frightens us). |
| [M2564](#zibotaby) | brotherhood | caution | **violence_or_blood**: The final sentence says a Muslim's blood, property and honour are sacred (haram) to another Muslim. I used 'life, belongings, good name are protected' in the older text only and left it out of the younger text.; **fiqh_ruling**: Contains trade rulings (najsh, bidding up a price; selling over another's sale). I did not explain them to children.; **hard_to_explain**: A long, multi-part hadith with many separate commands. The explanations only cover the shared theme of brotherhood. Consider using it as a short brotherhood reminder or excluding it. |
| [M2703](#tsyxeddj) | forgiveness | caution | **sensitive_aqidah**: Time limit is the sun rising from the west, a major sign of the Hour. Explanation leaves out the sign and only says repentance is open while there is time, to avoid end-times fear. |
| [M2759](#wmnhncdm) | forgiveness | caution | **sensitive_aqidah**: Text speaks of Allah stretching His hand (an attribute; risk of childish anthropomorphic imagery) and ends with the sun rising from the west (sign of the Hour). Explanation avoids both and says only that repentance is accepted day and night. |
| [M593](#lyu00er7) | not-wasting | caution | **hard_to_explain**: The phrase about asking too much (kathrat al-su'al) is interpreted by scholars as either begging for money or asking needless or trouble-making questions. I kept it general so children are not discouraged from asking questions, which matters for the seeking-knowledge value; please check. The same hadith is also in B1477 (item S8dLuCAM).; **other**: Duplicate teaching with Bukhari 1477 (S8dLuCAM); consider keeping only one in the child-facing set.; **other**: Same hadith as B1477 (S8dLuCAM). Reviewer suggests keeping only one, preferably B1477. |
| [M91](#at9rqqki) | humility | caution | **paradise_exclusion**: Opens with: no one who has an atom's weight of pride in his heart will enter Paradise. Explanations skip this and give the positive lesson (what pride is and is not). |
| [B12](#opjdwzhi) | spreading-salam | ok | **other**: Stranger safety: greeting people we do not know is framed as "when we are with our family". |
| [B1240](#kan2aebp) | visiting-the-sick | ok | **death**: One of the five items is following funerals. I omitted it for ages 6-9 and mentioned it briefly and neutrally for the older group; the lead may want to keep it out of both.; **fiqh_ruling**: The word 'right' (haqq) is explained by scholars as a recommended or communal duty, which varies by item. I gave no ruling and kept the focus on kindness. |
| [B13](#a3n67zet) | brotherhood | ok | **sensitive_aqidah**: The hadith says none of you truly believes until you love for your brother what you love for yourself. I did not explain how to read this (scholars usually say complete faith); I only said it links this quality with faith. |
| [B24](#9tkrxdvc) | modesty | ok | **hard_to_explain**: Context is a man admonishing his brother about shyness (apparently that it holds him back); the reading is mine, please confirm. Also be careful that modesty is not used to shame children who are quiet or shy. |
| [B2568](#x2imeezk) | humility | ok | **hard_to_explain**: The Arabic names two cheap cuts of an animal's leg (foreleg and lower leg). Explanations generalise to a modest meal or small gift. The hadith itself does not mention thanking; the 'say thank you' in the example is our practical addition. |
| [B2820](#jxvupeat) | courage | ok | **fear**: People of Madinah were alarmed (cause not stated in this wording). Mild.; **hard_to_explain**: His closing remark about the horse (that he found it like a sea) is an idiom for its speed; I left it out of the explanations. |
| [B2891](#2jhl7psd) | helping-others | ok | **other**: Hadith opens with every joint of the body owing charity each day (the Arabic term is a technical anatomical word). Explanations omit this framing and keep the list of good deeds. Mild. |
| [B3653](#hkzhkjjw) | trust-in-allah | ok | **fear**: The context is the Prophet and Abu Bakr hiding from pursuers. I kept the focus on Allah's reassurance and did not describe the enemy. I wrote 'those searching' for the older text; the hadith itself implies this but does not name them. |
| [B5027](#ymywjzdb) | seeking-knowledge | ok | **other**: The second part of the Arabic text is a narrator's remark about Abu Abd al-Rahman teaching in Uthman's time and al-Hajjaj, not the Prophet's words. I explained only the Prophet's statement; the lead may want to show only the first sentence. |
| [B5664](#jtfsxg7j) | humility, visiting-the-sick | ok | **hard_to_explain**: The text only says he was not on a mule or a (non-Arab breed) horse; reading it as 'he came simply, probably on foot, as a sign of humility' is an inference. Please check the dorar commentary. Explanations say 'came in a simple way'. |
| [B574](#imrmnm3g) | prayer | ok | **other**: The hadith says only al-bardayn (the two cool times). I explained it as Fajr and Asr, the standard scholarly reading; the lead may want to confirm the dorar commentary says the same. The reward is promised Paradise, not an exclusion threat. |
| [B5986](#ncwjt4pr) | family-ties | ok | **other**: Mentions lengthening of life (delay in one's term/trace). Explanation generalises to 'blessing in life' because scholars differ on the exact meaning (longer life vs lasting good name). Not frightening. |
| [B5997](#bzm4tbgy) | mercy | ok | **fear**: Closing line (the one who is not merciful will not be shown mercy) can sound like a threat. Framed as what to do: be merciful. |
| [B6005](#uppafekl) | caring-for-orphans | ok | **other**: Sensitive if the child using the app has lost a parent. Wording kept warm and positive. |
| [B6014](#qgsaingd) | good-neighbour | ok | **other**: Mentions inheritance (rhetorical emphasis, not a ruling). Explanation says it only shows the importance of neighbours; no fiqh claim that neighbours inherit. |
| [B6018](#hxe5ykjl) | good-neighbour, kind-words | ok | **other**: Each instruction is conditioned on believing in Allah and the Last Day. Mild; explanation presents it as faith linked to good manners, with no threat or exclusion. |
| [B6116](#ysuk7rds) | controlling-anger | ok | **other**: The hadith's meaning is commonly read as 'do not act on your anger' (and avoid its causes), not 'never feel anger'. I explained it that way to avoid making children feel guilty for having the feeling. |
| [B6407](#zmg5qhaf) | remembering-allah | ok | **death**: The comparison is the living and the dead. I kept it as 'with life' versus 'without life' and avoided the word dead for the younger text; the lead may prefer it that way or may want to keep the item only for older children. |
| [B887](#kl7q5sln) | cleanliness | ok | **fiqh_ruling**: The hadith touches the status of siwak at each prayer (encouraged, not obligatory, because the Prophet did not want to burden people). I gave no ruling, only the encouragement to keep the mouth clean. |
| [M2317](#a4xe6w8b) | mercy | ok | **other**: The hadith has a sharp line about Allah removing mercy from hearts. It could upset a child whose parent is not physically affectionate; the explanation avoids judging any parent.; **other**: Physical affection (hugs, kisses) is kept to family at home. |
| [M2319](#thhiya8s) | mercy | ok | **fear**: Closing clause (Allah will not show mercy to the one who does not) could sound threatening. The explanation focuses on the positive side. |
| [M2568](#hgjrlbz0) | visiting-the-sick | ok | **hard_to_explain**: The Arabic word khurfat al-janna is an unusual term; I used the common explanation that it means the gathered fruits or gardens of Paradise, expressed as 'great reward in Paradise'. The lead should check the dorar commentary and confirm this is what the page says. |
| [M2597](#zx5majzx) | kind-words | ok | **curse**: Concerns excessive cursing (la'n). The explanation avoids any curse wording and teaches kind speech instead. |
| [M2832](#1ktnzrlh) | love-of-the-prophet | ok | **other**: The Arabic wish to see him with family and wealth is read as: would gladly give up family and wealth just to see him. Wording is kept general to avoid suggesting children give up family; please verify the reading. |
| [M2963](#h30czibe) | contentment, gratitude | ok | **other**: Risk that a child might read 'look at those below you' as looking down on poor people. I stated clearly that it is not for that. 'In worldly things' follows the usual scholarly reading; the hadith itself is general. |
| [M2983](#qkxmpubh) | caring-for-orphans | ok | **other**: Sensitive if the child using the app has lost a parent. Wording kept warm and positive. Child age 'orphan' follows values.json (lost father or mother), though classical usage is lost father before puberty. |

### Merged duplicates (same dorar page, values merged)

- M2626 `J6s2MSMp`: brotherhood, good-character (from draft-brotherhood-J6s2MSMp.json, draft-good-character-J6s2MSMp.json)
- M2588 `5ny4Eh57`: charity, generosity (from draft-charity-5ny4Eh57.json, draft-generosity-5ny4Eh57.json)
- B1442 `JEeFXYSO`: charity, generosity (from draft-charity-JEeFXYSO.json, draft-generosity-JEeFXYSO.json)
- M2963 `h30CzibE`: contentment, gratitude (from draft-contentment-h30CzibE.json, draft-gratitude-h30CzibE.json)
- B6018 `HXe5YKJL`: good-neighbour, kind-words (from draft-good-neighbour-HXe5YKJL.json, draft-kind-words-HXe5YKJL.json)
- M2999 `NNRH8eQT`: gratitude, patience (from draft-gratitude-NNRH8eQT.json, draft-patience-NNRH8eQT.json)
- M2734 `oOabSoIV`: gratitude, table-manners (from draft-gratitude-oOabSoIV.json, draft-table-manners-oOabSoIV.json)
- M2551 `bK5vX0fu`: honouring-parents, respecting-elders (from draft-honouring-parents-bK5vX0fu.json, draft-respecting-elders-bK5vX0fu.json)
- B5664 `jTFsxG7j`: humility, visiting-the-sick (from draft-humility-jTFsxG7j.json, draft-visiting-the-sick-jTFsxG7j.json)
- B33 `oKBHqVCn`: keeping-promises, trustworthiness (from draft-keeping-promises-oKBHqVCn.json, draft-trustworthiness-oKBHqVCn.json)

## avoiding-backbiting: Avoiding Backbiting / ترك الغيبة

File: `drafts/hadith/items-avoiding-backbiting.json`

<a id="8c6iigij"></a>
### M105 · Sahih Muslim 105 · caution

- Values: avoiding-backbiting
- dorar: https://dorar.net/h/8c6iiGij · narrator: حذيفة بن اليمان · grade: صحيح (مسلم)
- First 10 words: «أنَّه بَلَغَه أنَّ رَجُلًا يَنِمُّ الحَديثَ، فقال حُذَيفةُ: سَمِعتُ رَسولَ …»
- Agent's reading: Hudhayfa reports hearing the Messenger of Allah say that a tale-bearer (one who carries people's words to cause trouble) will not enter Paradise.
- 6-9 AR: هذا الحديث يعلمنا أن لا ننقل كلام الناس من واحد إلى آخر ليتخاصموا. مثلا، إذا سمعنا كلاما لا يعجب صديقنا فلا نكرره له، ونقول كلاما طيبا بدلا منه.
- 6-9 EN: This hadith teaches us not to carry people's words from one person to another to make them quarrel. For example, if we hear something unkind about our friend, we don't repeat it to him, and we say something kind instead.
- 10-13 AR: هذا الحديث يبين أن النميمة خلق سيئ يجب أن نبتعد عنه، والنميمة هي أن ننقل كلام الناس بعضه إلى بعض ليقع بينهم الخلاف. كلمة واحدة تنقل قد تجعل صديقين يتخاصمان. فالأفضل أن نصلح بين الناس ونقول الخير أو نسكت.
- 10-13 EN: This hadith shows that tale-bearing is a bad habit we should stay away from. It means carrying people's words from one to another so that they fall out. One repeated sentence can turn two friends into enemies, so it is better to help people make peace and to say something good or stay quiet.
- ⚠️ Flag **paradise_exclusion**: The hadith says the tale-bearer will not enter Paradise. I left the warning out and taught the positive action (make peace, speak well).
- [ ] ok

<a id="dmrdwsfq"></a>
### B6484 · Sahih al-Bukhari 6484 · ok

- Values: avoiding-backbiting
- dorar: https://dorar.net/h/DmRdWSfQ · narrator: عبدالله بن عمرو · grade: صحيح (البخاري)
- First 10 words: «المُسلِمُ مَن سَلِمَ المُسلِمونَ مِن لسانِه ويَدِه، والمُهاجِرُ مَن هَجَرَ …»
- Agent's reading: A Muslim is the one from whose tongue and hand other Muslims are safe, and a muhajir is the one who abandons what Allah has forbidden.
- 6-9 AR: هذا الحديث يعلمنا أن المسلم الحقيقي لا يؤذي الناس بلسانه ولا بيده. مثلا، لا نشتم أحدا ولا نضرب أحدا، بل نتكلم بلطف.
- 6-9 EN: This hadith teaches that a true Muslim does not hurt others with his words or his hands. For example, we don't call anyone names or hit anyone, and we speak gently.
- 10-13 AR: هذا الحديث يبين أن المسلم الحقيقي هو من يسلم الناس من أذى لسانه ويده، فلا يغتاب ولا يسخر ولا يؤذي أحدا. ويبين أيضا أن المهاجر الحقيقي هو من يترك ما نهى الله عنه. فنتدرب كل يوم على أن نفكر قبل أن نتكلم ونترك الكلام الذي يجرح غيرنا.
- 10-13 EN: This hadith shows that a true Muslim is one whose words and hands never harm other people, so he doesn't gossip, mock or hurt anyone. It also says a true muhajir, one who leaves something behind, is the person who gives up what Allah has forbidden. We can practise every day by thinking before we speak and dropping words that would hurt someone.
- [ ] ok

<a id="mndctvnv"></a>
### M2589 · Sahih Muslim 2589 · ok

- Values: avoiding-backbiting
- dorar: https://dorar.net/h/MNdCTVnv · narrator: أبو هريرة · grade: صحيح (مسلم)
- First 10 words: «أتَدرونَ ما الغيبةُ؟ قالوا: اللهُ ورَسولُه أعلَمُ، قال: ذِكرُك أخاك …»
- Agent's reading: The Prophet defines backbiting as mentioning your brother with what he dislikes; if it is true about him it is backbiting, and if it is untrue it is slander.
- 6-9 AR: هذا الحديث يعلمنا أن الغيبة هي أن نتكلم عن شخص في غيابه بما يكره. مثلا، لا نقول لأصحابنا شيئا يحزن زميلنا لو سمعه، حتى لو كان صحيحا.
- 6-9 EN: This hadith teaches that backbiting means talking about someone when they are not there, saying things they would not like. For example, we don't tell our friends something that would upset a classmate if he heard it, even if it is true.
- 10-13 AR: هذا الحديث يوضح معنى الغيبة، وهي أن نذكر أخانا بما يكره في غيابه. وحتى لو كان ما نقوله صحيحا فهو غيبة، أما إن لم يكن فيه فهو كذب عليه وأسوأ. فقبل أن نتكلم عن أحد نسأل أنفسنا: هل سيفرح لو سمع كلامي؟
- 10-13 EN: This hadith explains what backbiting is: mentioning your brother in a way he would dislike when he is not there. Even if what you say is true, it is still backbiting, and if it is not true then it is worse, because it is a false accusation. Before we talk about someone, we can ask ourselves whether he would be happy to hear it.
- [ ] ok

## brotherhood: Brotherhood / الأخوة

File: `drafts/hadith/items-brotherhood.json`

<a id="j6s2msmp"></a>
### M2626 · Sahih Muslim 2626 · ok

- Values: brotherhood, good-character
- dorar: https://dorar.net/h/J6s2MSMp · narrator: أبو ذر الغفاري · grade: صحيح (مسلم)
- First 10 words: «لا تَحقِرَنَّ مِنَ المَعروفِ شيئًا، ولو أن تَلقى أخاك بوجهٍ …»
- Agent's reading: Do not belittle any act of goodness, even meeting your brother with a cheerful face.
- 6-9 AR: هذا الحديث يعلمنا أن أي عمل طيب مهم، حتى لو كان صغيرا. مثلا، أن نقابل صديقنا بوجه مبتسم فيفرح.
- 6-9 EN: This hadith teaches us that any good deed matters, even a small one. For example, meeting our friend with a smiling face makes him happy.
- 10-13 AR: هذا الحديث يعلمنا أن لا نستصغر أي معروف، حتى لو كان مجرد لقاء أخينا بوجه بشوش. فالابتسامة اللطيفة وكلمة التحية الطيبة أعمال طيبة نقدر عليها كل يوم. وهكذا يصبح حسن الخلق عادة جميلة عندنا.
- 10-13 EN: This hadith teaches us not to look down on any kindness, even something as simple as meeting our brother with a cheerful face. A friendly smile and a warm greeting are good deeds we can do every day. That is how good character becomes a lovely habit.
- [ ] ok

<a id="zibotaby"></a>
### M2564 · Sahih Muslim 2564 · caution

- Values: brotherhood
- dorar: https://dorar.net/h/ZiboTABY · narrator: أبو هريرة · grade: صحيح (مسلم)
- First 10 words: «لا تَحاسَدوا، ولا تَناجَشوا، ولا تَباغَضوا، ولا تَدابَروا، ولا يَبِعْ …»
- Agent's reading: Do not envy, bid up prices, hate, turn away from or undercut each other's sale; be brothers; a Muslim does not wrong, abandon or despise his brother; taqwa is in the heart; a Muslim's blood, property and honour are sacred to other Muslims.
- 6-9 AR: هذا الحديث يعلمنا أن نكون إخوة طيبين، فلا نحسد أحدا ولا نكرهه ولا نتجاهله. مثلا، نفرح لصديقنا إذا نجح ولا نسخر منه.
- 6-9 EN: This hadith teaches us to be good brothers and sisters, so we don't envy anyone, dislike them or ignore them. For example, we are happy for our friend when he succeeds and we never make fun of him.
- 10-13 AR: هذا الحديث يعلمنا أن المسلم أخو المسلم، فلا يظلمه ولا يتركه وحده ولا يستصغره. ويبين أن التقوى مكانها القلب، فنتدرب على ترك الحسد والكره ونتمنى الخير لإخواننا. ويبين أيضا أن نفس المسلم وماله وسمعته لها حرمة عند إخوانه، فنحرص على احترام الجميع.
- 10-13 EN: This hadith teaches that a Muslim is the brother of a Muslim, so he does not wrong him, leave him alone or look down on him. It reminds us that taqwa lives in the heart, so we practise letting go of envy and dislike and wishing good for our brothers. It also teaches that a Muslim's life, belongings and good name are protected and respected by other Muslims, so we take care to honour everyone.
- ⚠️ Flag **violence_or_blood**: The final sentence says a Muslim's blood, property and honour are sacred (haram) to another Muslim. I used 'life, belongings, good name are protected' in the older text only and left it out of the younger text.
- ⚠️ Flag **fiqh_ruling**: Contains trade rulings (najsh, bidding up a price; selling over another's sale). I did not explain them to children.
- ⚠️ Flag **hard_to_explain**: A long, multi-part hadith with many separate commands. The explanations only cover the shared theme of brotherhood. Consider using it as a short brotherhood reminder or excluding it.
- [ ] ok

<a id="a3n67zet"></a>
### B13 · Sahih al-Bukhari 13 · ok

- Values: brotherhood
- dorar: https://dorar.net/h/a3n67ZEt · narrator: أنس بن مالك · grade: صحيح (البخاري)
- First 10 words: «لا يُؤمِنُ أحَدُكُم حتَّى يُحِبَّ لأخيه ما يُحِبُّ لنَفسِه.»
- Agent's reading: A person's faith is not complete until he loves for his brother what he loves for himself.
- 6-9 AR: هذا الحديث يعلمنا أن نحب لأصدقائنا ما نحبه لأنفسنا. مثلا، كما نحب أن ننجح ونكون سعداء، نتمنى لصديقنا أن ينجح ويسعد.
- 6-9 EN: This hadith teaches us to want for our friends what we want for ourselves. For example, just as we want to do well and be happy, we hope our friend does well and is happy too.
- 10-13 AR: هذا الحديث يعلمنا أن الأخوة الصادقة أن نتمنى لإخواننا من الخير ما نتمناه لأنفسنا. وهذا يعني أن نفرح لنجاحهم ولا نحسدهم، وأن نعاملهم كما نحب أن يعاملونا. والحديث يربط هذا الخلق بالإيمان.
- 10-13 EN: This hadith teaches that true brotherhood means wishing for our brothers the same good things we wish for ourselves. That means being happy for their success instead of envying them, and treating them the way we like to be treated. The hadith links this good quality with faith.
- ⚠️ Flag **sensitive_aqidah**: The hadith says none of you truly believes until you love for your brother what you love for yourself. I did not explain how to read this (scholars usually say complete faith); I only said it links this quality with faith.
- [ ] ok

## caring-for-orphans: Caring for Orphans / رعاية اليتيم

File: `drafts/hadith/items-caring-for-orphans.json`

<a id="qkxmpubh"></a>
### M2983 · Sahih Muslim 2983 · ok

- Values: caring-for-orphans
- dorar: https://dorar.net/h/QkXMpubH · narrator: أبو هريرة · grade: صحيح (مسلم)
- First 10 words: «كافِلُ اليَتيمِ له أو لغَيرِه أنا وهو كَهاتَينِ في الجَنَّةِ، …»
- Agent's reading: The one who sponsors an orphan, whether the orphan is his relative or someone else's, will be as close to the Prophet in Paradise as these two fingers (the index and middle finger).
- 6-9 AR: هذا الحديث يعلمنا فضل من يرعى اليتيم، وهو طفل فقد أباه أو أمه. من يعطف على اليتيم ويهتم به يكون قريبا من النبي ﷺ في الجنة.
- 6-9 EN: This hadith teaches how special it is to look after an orphan, a child who has lost a parent. Someone who cares for an orphan will be close to the Prophet ﷺ in Paradise.
- 10-13 AR: هذا الحديث يبين مكانة من يكفل اليتيم، أي يرعاه وينفق عليه، سواء كان اليتيم من أقاربه أو من غيرهم. وفيه أن من يفعل ذلك يكون قريبا من النبي ﷺ في الجنة. ونحن الصغار نستطيع أن نكون لطفاء مع اليتيم ونطلب من أهلنا أن نساعده.
- 10-13 EN: This hadith shows the high rank of someone who sponsors an orphan, meaning he looks after him and spends on him, whether the orphan is a relative or not. It says that such a person will be close to the Prophet ﷺ in Paradise. Even as young people we can be kind to an orphan and ask our family to help him.
- ⚠️ Flag **other**: Sensitive if the child using the app has lost a parent. Wording kept warm and positive. Child age 'orphan' follows values.json (lost father or mother), though classical usage is lost father before puberty.
- [ ] ok

<a id="uppafekl"></a>
### B6005 · Sahih al-Bukhari 6005 · ok

- Values: caring-for-orphans
- dorar: https://dorar.net/h/UpPaFekl · narrator: سهل بن سعد الساعدي · grade: صحيح (البخاري)
- First 10 words: «أنا وكافِلُ اليَتيمِ في الجَنَّةِ هَكَذا، وقال بإصبَعَيه السَّبَّابةِ والوُسطى.»
- Agent's reading: The Prophet says that he and the one who sponsors an orphan will be together in Paradise like this, showing his index and middle fingers.
- 6-9 AR: هذا الحديث يعلمنا أن من يرعى اليتيم ويعطف عليه له مكانة عظيمة. اليتيم طفل فقد أباه أو أمه، ومن يحسن إليه يكون قريبا من النبي ﷺ في الجنة.
- 6-9 EN: This hadith teaches that someone who looks after an orphan and is kind to him has a great honour. An orphan is a child who has lost a parent, and whoever is good to him will be close to the Prophet ﷺ in Paradise.
- 10-13 AR: هذا الحديث يبين فضل كفالة اليتيم، وهي رعايته والإنفاق عليه. وقد أشار النبي ﷺ بإصبعيه ليبين قرب كافل اليتيم منه في الجنة. فنتعلم أن نكون لطفاء مع الأيتام، وأن نساعد من يرعاهم بقدر ما نستطيع.
- 10-13 EN: This hadith shows the reward of sponsoring an orphan, which means caring for him and spending on him. The Prophet ﷺ held up two fingers to show how close the sponsor will be to him in Paradise. We learn to be kind to orphans and to help those who look after them as much as we can.
- ⚠️ Flag **other**: Sensitive if the child using the app has lost a parent. Wording kept warm and positive.
- [ ] ok

## charity: Charity / الصدقة

File: `drafts/hadith/items-charity.json`

<a id="5ny4eh57"></a>
### M2588 · Sahih Muslim 2588 · ok

- Values: charity, generosity
- dorar: https://dorar.net/h/5ny4Eh57 · narrator: أبو هريرة · grade: صحيح (مسلم)
- First 10 words: «ما نَقَصَت صَدَقةٌ مِن مالٍ، وما زادَ اللهُ عَبدًا بعَفوٍ …»
- Agent's reading: Charity never decreases wealth, Allah increases in honour the servant who forgives, and Allah raises whoever humbles himself for His sake.
- 6-9 AR: هذا الحديث يعلمنا أن الصدقة لا تنقص المال، وأن من يسامح ويتواضع يرفعه الله. مثلا، نعطي جزءا من مصروفنا للمحتاج ونحن فرحون.
- 6-9 EN: This hadith teaches that giving charity does not make our money less, and that Allah raises the person who forgives and is humble. For example, we happily give some of our pocket money to someone in need.
- 10-13 AR: هذا الحديث يعلمنا أن الصدقة لا تنقص المال، فلا نخاف أن نعطي. ويبين أن من يعفو عن غيره يزيده الله عزا، وأن من يتواضع لله يرفعه الله. فالكرم والتسامح والتواضع أخلاق تجعلنا أحب إلى الناس وأقرب إلى الله.
- 10-13 EN: This hadith teaches that charity does not reduce wealth, so we don't need to be afraid to give. It also says that Allah increases the honour of the person who forgives, and raises the one who is humble for His sake. Generosity, forgiveness and humility are qualities that make us dearer to people and closer to Allah.
- [ ] ok

<a id="jeefxyso"></a>
### B1442 · Sahih al-Bukhari 1442 · caution

- Values: charity, generosity
- dorar: https://dorar.net/h/JEeFXYSO · narrator: أبو هريرة · grade: صحيح (البخاري)
- First 10 words: «ما مِن يَومٍ يُصبِحُ العِبادُ فيه إلَّا مَلَكانِ يَنزِلانِ، فيَقولُ …»
- Agent's reading: Every morning two angels descend; one prays that Allah replace what the spender spends, and the other prays that the one who withholds suffers loss.
- 6-9 AR: هذا الحديث يعلمنا أن ملكين ينزلان كل صباح، وأحدهما يدعو أن يعوض الله من ينفق في الخير. مثلا، نشارك طعامنا ونتصدق من مصروفنا بفرح.
- 6-9 EN: This hadith teaches that two angels come down every morning, and one of them prays that Allah will give back to the person who spends for good. For example, we happily share our food and give some of our pocket money to charity.
- 10-13 AR: هذا الحديث يبين أن ملكين ينزلان كل يوم، وأحدهما يدعو أن يعطي الله من ينفق في الخير عوضا عما أنفق. ويبين الحديث أن حبس المال عن الخير ليس أمرا جيدا. فنتعلم أن نكون كرماء بحسب قدرتنا ونعطي بنفس طيبة.
- 10-13 EN: This hadith shows that two angels come down every day, and one of them prays that Allah gives back to the one who spends for good. It also shows that holding back our money from good causes is not a good habit. So we learn to be generous as much as we can and to give with a happy heart.
- ⚠️ Flag **curse**: The second angel's supplication is a prayer for loss or ruin for the one who withholds. I did not repeat it; the older text only says holding back is not good.
- [ ] ok

<a id="n5bhcv9r"></a>
### B1419 · Sahih al-Bukhari 1419 · caution

- Values: charity
- dorar: https://dorar.net/h/N5bHcV9r · narrator: أبو هريرة · grade: صحيح (البخاري)
- First 10 words: «جاءَ رَجُلٌ إلى النَّبيِّ صلَّى اللهُ عليه وسلَّم، فقال: يا …»
- Agent's reading: The most rewarded charity is giving while you are healthy, stingy, afraid of poverty and hoping for wealth, not delaying until death approaches and then assigning your wealth to others.
- 6-9 AR: هذا الحديث يعلمنا أن أفضل صدقة هي التي نعطيها ونحن بصحة جيدة، حتى لو كنا نحب مالنا. مثلا، نتصدق من مصروفنا الآن ولا نقول: سأعطي في وقت آخر.
- 6-9 EN: This hadith teaches that the best charity is the kind we give while we are healthy, even if we like to keep our money. For example, we give some of our pocket money now and don't say, I will give later.
- 10-13 AR: هذا الحديث يبين أن أعظم الصدقة أجرا هي التي نعطيها ونحن بصحة جيدة، ونحب أن نحتفظ بمالنا ونخشى أن نحتاج. فلا ننتظر حتى يأتي وقت متأخر لنعطي، بل نتصدق من الآن ولو بشيء قليل. والعطاء المبكر يدل على أننا نقدم الخير بصدق.
- 10-13 EN: This hadith shows that the most rewarded charity is the one we give while we are healthy, when we like to hold on to our money and worry about needing it. So we shouldn't wait until it is too late to give, but start now, even with a small amount. Giving early shows we really mean to do good.
- ⚠️ Flag **death**: The hadith refers to the soul reaching the throat (the moment of death) as the time when it is too late. I only said 'too late' and 'wait'.
- ⚠️ Flag **fear**: Mentions fear of poverty and hope for wealth. I framed it as the normal feeling that makes giving hard.
- [ ] ok

## cleanliness: Cleanliness / النظافة

File: `drafts/hadith/items-cleanliness.json`

<a id="7pukapvo"></a>
### B245 · Sahih al-Bukhari 245 · ok

- Values: cleanliness
- dorar: https://dorar.net/h/7pUKaPVO · narrator: حذيفة بن اليمان · grade: صحيح (البخاري)
- First 10 words: «كان النَّبيُّ صلَّى اللهُ عليه وسلَّم إذا قامَ مِنَ اللَّيلِ …»
- Agent's reading: When the Prophet got up at night he would rub his mouth (teeth) with the siwak.
- 6-9 AR: هذا الحديث يخبرنا أن النبي ﷺ كان ينظف فمه بالسواك عندما يستيقظ في الليل. ونحن نحب أيضا نظافة أسناننا فننظفها بالفرشاة كل يوم.
- 6-9 EN: This hadith tells us that the Prophet ﷺ cleaned his mouth with a siwak when he woke up in the night. We also like to keep our teeth clean, so we brush them every day.
- 10-13 AR: هذا الحديث يخبرنا أن النبي ﷺ كان يهتم بنظافة فمه، حتى عندما يستيقظ في الليل. والسواك عود صغير تنظف به الأسنان. فنقتدي به ونحافظ على نظافة أسناننا كل يوم بالفرشاة والسواك.
- 10-13 EN: This hadith tells us that the Prophet ﷺ cared about keeping his mouth clean, even when he woke up in the night. A siwak is a small twig used to clean the teeth. We follow his example by looking after our teeth every day with a toothbrush or siwak.
- [ ] ok

<a id="kl7q5sln"></a>
### B887 · Sahih al-Bukhari 887 · ok

- Values: cleanliness
- dorar: https://dorar.net/h/Kl7q5SLn · narrator: أبو هريرة · grade: صحيح (البخاري)
- First 10 words: «لَولا أن أشُقَّ على أُمَّتي -أو على النَّاسِ- لَأمَرتُهم بالسِّواكِ …»
- Agent's reading: The Prophet said that if it were not hard on his community he would have commanded them to use the siwak with every prayer.
- 6-9 AR: هذا الحديث يعلمنا أن النبي ﷺ كان يحب السواك لتنظيف الأسنان وكان لا يريد أن يتعب الناس. مثلا، ننظف أسناننا قبل الصلاة بالفرشاة أو السواك.
- 6-9 EN: This hadith teaches that the Prophet ﷺ loved using the siwak to clean the teeth and did not want to make things hard for people. For example, we can clean our teeth with a brush or siwak before we pray.
- 10-13 AR: هذا الحديث يبين مكانة السواك وتنظيف الفم عند كل صلاة. ويبين أن النبي ﷺ كان حريصا على أن لا يشق على أمته. فنهتم بنظافة أفواهنا عندما نريد أن نصلي، ونتذكر لطف النبي ﷺ بنا.
- 10-13 EN: This hadith shows how important it is to use the siwak and clean the mouth for prayer. It also shows that the Prophet ﷺ was careful not to make things difficult for his community. So we take care to keep our mouths clean when we are about to pray, and we remember how kind he was to us.
- ⚠️ Flag **fiqh_ruling**: The hadith touches the status of siwak at each prayer (encouraged, not obligatory, because the Prophet did not want to burden people). I gave no ruling, only the encouragement to keep the mouth clean.
- [ ] ok

<a id="tvssnrwa"></a>
### M223 · Sahih Muslim 223 · caution

- Values: cleanliness
- dorar: https://dorar.net/h/TvSSnRwa · narrator: أبو مالك الأشعري · grade: صحيح (مسلم)
- First 10 words: «الطُّهورُ شَطرُ الإيمانِ، والحَمدُ للَّهِ تَملأُ الميزانَ، وسُبحانَ اللهِ والحَمدُ …»
- Agent's reading: Purity is half of faith; alhamdulillah fills the scale; tasbih and tahmid fill what is between heaven and earth; prayer is light, charity is proof, patience is radiance, the Quran is a proof for or against you; every person strives, either freeing or destroying himself.
- 6-9 AR: هذا الحديث يعلمنا أن النظافة جزء كبير من الإيمان، فنتوضأ ونغسل أيدينا ونهتم بنظافتنا. ويذكرنا أيضا بأعمال جميلة مثل الحمد لله والصلاة والصدقة.
- 6-9 EN: This hadith teaches that cleanliness is a big part of faith, so we make wudu, wash our hands and keep ourselves clean. It also reminds us of lovely deeds like saying alhamdulillah, praying and giving charity.
- 10-13 AR: هذا الحديث يبين أن الطهارة، أي النظافة والوضوء، جزء كبير من الإيمان، فنحرص عليها كل يوم. ويذكر الحديث أيضا أعمالا طيبة أخرى مثل الحمد لله والصلاة والصدقة والصبر. فنحاول أن نجعل هذه الأعمال جزءا من يومنا.
- 10-13 EN: This hadith shows that purity, meaning cleanliness and wudu, is a big part of faith, so we take care of it every day. The hadith also lists other good deeds like saying alhamdulillah, prayer, charity and patience. We can try to make these deeds a part of our day.
- ⚠️ Flag **hard_to_explain**: A long hadith with many separate themes. Meaning of 'purity is half of faith' is also discussed by scholars (wudu, cleanliness or purity in general). I used only the cleanliness and wudu reading and the list of good deeds.
- ⚠️ Flag **fear**: The ending says the Quran is a proof for or against you and that each person either frees himself or destroys himself. I left it out entirely.
- ⚠️ Flag **sensitive_aqidah**: Mentions the scale of deeds and the Quran as proof for or against. Not explained to children.
- [ ] ok

## contentment: Contentment / القناعة

File: `drafts/hadith/items-contentment.json`

<a id="h30czibe"></a>
### M2963 · Sahih Muslim 2963 · ok

- Values: contentment, gratitude
- dorar: https://dorar.net/h/h30CzibE · narrator: أبو هريرة · grade: صحيح (مسلم)
- First 10 words: «انظُروا إلى مَن أسفَلَ مِنكُم، ولا تَنظُروا إلى مَن هو …»
- Agent's reading: Look at those below you (in provision) and not at those above you, because that makes you less likely to belittle Allah's blessing on you.
- 6-9 AR: هذا الحديث يعلمنا أن ننظر إلى من عنده أقل منا، فنشكر الله على نعمه علينا ولا نحزن لأن غيرنا عنده أكثر. مثلا، نقول الحمد لله على بيتنا وطعامنا.
- 6-9 EN: This hadith teaches us to think about people who have less than we do, so we thank Allah for what we have and don't feel sad that others have more. For example, we say alhamdulillah for our home and our food.
- 10-13 AR: هذا الحديث يعلمنا أن ننظر إلى من هو أقل منا في أمور الدنيا ولا ننظر إلى من هو أكثر منا، حتى لا نستصغر نعمة الله علينا. وهذا ليس لنسخر ممن هو أقل منا، بل لنشكر الله ونقدر ما عندنا. وهو يساعدنا على الرضا والشكر.
- 10-13 EN: This hadith teaches us to look at those who have less than us in worldly things and not at those who have more, so that we don't treat Allah's blessings as small. This is not to look down on anyone, but to thank Allah and value what we already have. It helps us to feel content and grateful.
- ⚠️ Flag **other**: Risk that a child might read 'look at those below you' as looking down on poor people. I stated clearly that it is not for that. 'In worldly things' follows the usual scholarly reading; the hadith itself is general.
- [ ] ok

<a id="ohkwprkf"></a>
### M1054 · Sahih Muslim 1054 · ok

- Values: contentment
- dorar: https://dorar.net/h/ohKwprkF · narrator: عبدالله بن عمرو · grade: صحيح (مسلم)
- First 10 words: «قد أفلَحَ مَن أسلَمَ، ورُزِقَ كَفافًا، وقَنَّعَه اللهُ بما آتاه.»
- Agent's reading: The one who has become Muslim, been given just enough provision, and whom Allah has made content with what He gave him has truly succeeded.
- 6-9 AR: هذا الحديث يعلمنا أن الإنسان الناجح هو من يعيش بما يكفيه ويرضى بما أعطاه الله. مثلا، نفرح بطعامنا وثيابنا ولا نطلب كل ما نراه عند غيرنا.
- 6-9 EN: This hadith teaches that a successful person is one who has enough and is happy with what Allah has given him. For example, we enjoy our food and clothes and don't ask for everything we see others have.
- 10-13 AR: هذا الحديث يبين أن الفلاح لمن أسلم وكان رزقه يكفيه وجعل الله قلبه راضيا بما أعطاه. فالسعادة الحقيقية ليست في أن نملك الكثير، بل في أن نرضى بما عندنا. ونتدرب على ذلك بأن نشكر الله على ما لدينا قبل أن نطلب المزيد.
- 10-13 EN: This hadith shows that success belongs to the person who has submitted to Allah, has enough to live on, and whose heart Allah has made content with what he was given. Real happiness is not in owning a lot, but in being satisfied with what we have. We can practise by thanking Allah for what we have before asking for more.
- [ ] ok

<a id="yt26x1vz"></a>
### B6446 · Sahih al-Bukhari 6446 · ok

- Values: contentment
- dorar: https://dorar.net/h/yT26X1Vz · narrator: أبو هريرة · grade: صحيح (البخاري)
- First 10 words: «ليس الغِنى عن كَثرةِ العَرَضِ، ولَكِنَّ الغِنى غِنى النَّفسِ.»
- Agent's reading: Wealth is not having a lot of possessions; true wealth is the richness of the soul.
- 6-9 AR: هذا الحديث يعلمنا أن الغنى الحقيقي ليس كثرة الأشياء بل الرضا في القلب. مثلا، قد يكون عند طفل ألعاب كثيرة وهو غير سعيد، وعند طفل آخر القليل وهو راض وسعيد.
- 6-9 EN: This hadith teaches that real richness is not having lots of things but feeling content in our hearts. For example, one child may have many toys and still be unhappy, while another has only a few and feels happy and satisfied.
- 10-13 AR: هذا الحديث يبين أن الغنى ليس في كثرة المال والأشياء، بل في غنى النفس، أي أن نشعر بالرضا ولا نحتاج إلى كل ما نراه. فمن كان قلبه قانعا فهو غني حتى لو كان ما عنده قليلا. ونتدرب على ذلك بأن نشكر الله على ما عندنا.
- 10-13 EN: This hadith shows that richness is not in having a lot of money or things, but in the richness of the soul, which means feeling content and not needing everything we see. A person whose heart is content is rich even if he owns little. We can practise this by thanking Allah for what we already have.
- [ ] ok

## controlling-anger: Controlling Anger / كظم الغيظ

File: `drafts/hadith/items-controlling-anger.json`

<a id="ltmcgvb1"></a>
### B6115 · Sahih al-Bukhari 6115 · caution

- Values: controlling-anger
- dorar: https://dorar.net/h/LTmCGVB1 · narrator: سليمان بن صرد · grade: صحيح (البخاري)
- First 10 words: «استَبَّ رَجُلانِ عِندَ النَّبيِّ صلَّى اللهُ عليه وسلَّم ونَحنُ عِندَه …»
- Agent's reading: Two men insulted each other and one was red-faced with anger; the Prophet said he knew a phrase that would remove it, seeking refuge in Allah from Shaytan, and the man answered that he was not mad.
- 6-9 AR: هذا الحديث يعلمنا ماذا نفعل عندما نغضب: نستعيذ بالله من الشيطان فيذهب غضبنا. مثلا، إذا غضبت من أخيك فتوقف قليلا واطلب من الله أن يحميك.
- 6-9 EN: This hadith teaches us what to do when we get angry: we ask Allah to protect us from Shaytan, and our anger goes away. For example, if you are angry with your brother, stop for a moment and ask Allah to protect you.
- 10-13 AR: هذا الحديث يحكي موقفا غضب فيه رجل حتى احمر وجهه وأخذ يسب صاحبه. فعلمنا النبي ﷺ أن هناك كلمة لو قالها ذهب عنه غضبه، وهي الاستعاذة بالله من الشيطان. فعند الغضب نتوقف ونلجأ إلى الله ونهدأ بدل أن نسب أو نصرخ.
- 10-13 EN: This hadith tells of a man who became so angry that his face turned red and he began insulting his companion. The Prophet ﷺ taught that there is a phrase that would take his anger away, which is seeking Allah's protection from Shaytan. So when we are angry we pause, turn to Allah and calm down instead of insulting or shouting.
- ⚠️ Flag **sensitive_aqidah**: Mentions Shaytan as the source of anger. Explained simply as asking Allah's protection. I did not quote the phrase; the lead may want to show it from the bank.
- ⚠️ Flag **other**: The story has two men insulting each other, and the angry man answers back 'I am not mad'. I left the ending out; it can sound like name-calling about mental health.
- [ ] ok

<a id="sllc88xc"></a>
### B6114 · Sahih al-Bukhari 6114 · ok

- Values: controlling-anger
- dorar: https://dorar.net/h/SllC88XC · narrator: أبو هريرة · grade: صحيح (البخاري)
- First 10 words: «ليس الشَّديدُ بالصُّرَعةِ، إنَّما الشَّديدُ الذي يَملِكُ نَفسَه عِندَ الغَضَبِ.»
- Agent's reading: The strong person is not the one who defeats others in wrestling but the one who controls himself when angry.
- 6-9 AR: هذا الحديث يعلمنا أن القوي ليس من يغلب غيره في المصارعة، بل من يمسك نفسه عندما يغضب. مثلا، عندما يزعجنا أخونا نهدأ ولا نضربه ولا نصرخ.
- 6-9 EN: This hadith teaches that the strong person is not the one who beats others in wrestling, but the one who holds himself back when he is angry. For example, when our brother annoys us, we calm down and don't hit or shout.
- 10-13 AR: هذا الحديث يبين أن القوة الحقيقية ليست في قوة الجسم والمصارعة، بل في أن نملك أنفسنا عند الغضب. من يسيطر على غضبه أقوى ممن يغلب الناس بجسمه. ونتدرب على ذلك بأن نأخذ نفسا عميقا ونسكت حتى نهدأ.
- 10-13 EN: This hadith shows that real strength is not about a strong body or winning at wrestling, but about controlling ourselves when we are angry. Someone who controls his anger is stronger than someone who beats people with his body. We can practise by taking a deep breath and staying quiet until we calm down.
- [ ] ok

<a id="ysuk7rds"></a>
### B6116 · Sahih al-Bukhari 6116 · ok

- Values: controlling-anger
- dorar: https://dorar.net/h/YsUk7RDs · narrator: أبو هريرة · grade: صحيح (البخاري)
- First 10 words: «أنَّ رَجُلًا قال للنَّبيِّ صلَّى اللهُ عليه وسلَّم: أوصِني، قال: …»
- Agent's reading: A man asked the Prophet for advice, and he repeatedly told him, do not get angry.
- 6-9 AR: طلب رجل من النبي ﷺ نصيحة، فنصحه ألا يغضب. وكلما كرر الرجل طلبه أعاد عليه النبي ﷺ النصيحة نفسها. مثلا، عندما نشعر بالغضب نتوقف ونهدأ ولا نتصرف بسوء.
- 6-9 EN: A man asked the Prophet ﷺ for advice, and he advised him not to get angry. Each time the man asked again the answer stayed the same. For example, when we feel angry we pause and calm down and don't do anything unkind.
- 10-13 AR: هذا الحديث يبين أن رجلا طلب من النبي ﷺ وصية، فكانت نصيحته ألا يغضب، وكرر ذلك أكثر من مرة. وهذا يدل على أن التحكم في الغضب أمر مهم جدا. فنحاول عند الغضب أن لا نتصرف بسوء، ونهدأ ونطلب المساعدة من أهلنا إن احتجنا.
- 10-13 EN: This hadith tells of a man who asked the Prophet ﷺ for advice, and his advice was not to get angry, which he repeated more than once. This shows how important it is to control our anger. When we feel angry we try not to act badly, we calm down and ask our family for help if we need it.
- ⚠️ Flag **other**: The hadith's meaning is commonly read as 'do not act on your anger' (and avoid its causes), not 'never feel anger'. I explained it that way to avoid making children feel guilty for having the feeling.
- [ ] ok

## cooperation: Cooperation / التعاون

File: `drafts/hadith/items-cooperation.json`

<a id="gb3ii1rh"></a>
### B481 · Sahih al-Bukhari 481 · ok

- Values: cooperation
- dorar: https://dorar.net/h/GB3iI1RH · narrator: أبو موسى الأشعري · grade: صحيح (البخاري)
- First 10 words: «إنَّ المُؤمِنَ للمُؤمِنِ كالبُنيانِ يَشُدُّ بَعضُه بَعضًا. وشَبَّكَ أصابِعَه.»
- Agent's reading: A believer is to another believer like a building whose parts strengthen one another, and the Prophet interlaced his fingers to illustrate.
- 6-9 AR: هذا الحديث يعلمنا أن المؤمنين يقوي بعضهم بعضا مثل أجزاء البيت التي تسند بعضها بعضا. مثلا، عندما نتعاون في ترتيب الغرفة يصبح العمل أسهل.
- 6-9 EN: This hadith teaches that believers make each other strong, like the parts of a building that hold each other up. For example, when we tidy a room together the job becomes easier.
- 10-13 AR: هذا الحديث يشبه المؤمنين بالبناء الذي تشد أجزاؤه بعضها بعضا، وقد شبك النبي ﷺ أصابعه ليوضح الصورة. فكل واحد منا يقوي غيره ويقوى به، ولا يستطيع بناء أن يقف بحجر واحد. فنتعاون مع أصدقائنا وأسرتنا في العمل والمذاكرة وفعل الخير.
- 10-13 EN: This hadith compares believers to a building whose parts support one another, and the Prophet ﷺ interlaced his fingers to show the picture. Each of us makes others strong and is made strong by them, and a building cannot stand on one brick. So we cooperate with our friends and family in work, study and doing good.
- [ ] ok

<a id="uji2rlbr"></a>
### M2586 · Sahih Muslim 2586 · ok

- Values: cooperation
- dorar: https://dorar.net/h/uji2RLBR · narrator: النعمان بن بشير · grade: صحيح (مسلم)
- First 10 words: «مَثَلُ المُؤمِنينَ في تَوادِّهم وتَراحُمِهم وتَعاطُفِهم مَثَلُ الجَسَدِ، إذا اشتَكى …»
- Agent's reading: Believers in their mutual love, mercy and compassion are like one body: when one part is in pain the whole body responds with sleeplessness and fever.
- 6-9 AR: هذا الحديث يعلمنا أن المؤمنين في حبهم ورحمتهم لبعضهم مثل الجسد الواحد. إذا تألم عضو تأثر الجسد كله، وهكذا نحزن لحزن إخواننا ونساعدهم.
- 6-9 EN: This hadith teaches that believers, in their love and mercy for each other, are like one body. When one part hurts the whole body feels it, so we feel sad when our brothers and sisters are sad and we help them.
- 10-13 AR: هذا الحديث يشبه المؤمنين في محبتهم ورحمتهم وعطفهم بالجسد الواحد. فإذا اشتكى عضو واحد لم يرتح باقي الجسد، وعانى من السهر والحمى. وهكذا نهتم بمن حولنا ونسأل عنهم ونتعاون على مساعدة من يتألم.
- 10-13 EN: This hadith compares believers, in their love, mercy and kindness to one another, to a single body. When one part is in pain the rest of the body cannot rest and feels the sleeplessness and fever too. In the same way we care about the people around us, check on them and work together to help whoever is hurting.
- [ ] ok

## courage: Courage / الشجاعة

File: `drafts/hadith/items-courage.json`

<a id="jxvupeat"></a>
### B2820 · Sahih al-Bukhari 2820 · ok

- Values: courage
- dorar: https://dorar.net/h/JXvUpeaT · narrator: أنس بن مالك · grade: صحيح (البخاري)
- First 10 words: «كان النَّبيُّ صلَّى اللهُ عليه وسلَّم أحسَنَ النَّاسِ، وأشجَعَ النَّاسِ، …»
- Agent's reading: The Prophet was the best, bravest and most generous of people, and when Madinah was alarmed he rode out ahead of the others on a horse and said the horse was like a sea.
- 6-9 AR: هذا الحديث يخبرنا أن النبي ﷺ كان من أشجع الناس. مرة خاف أهل المدينة، فكان النبي ﷺ أسبقهم على فرس.
- 6-9 EN: This hadith tells us that the Prophet ﷺ was one of the bravest people. Once the people of Madinah got frightened, and the Prophet ﷺ rode out ahead of them on a horse.
- 10-13 AR: هذا الحديث يصف النبي ﷺ بأنه كان أحسن الناس وأشجعهم وأكرمهم. ويحكي أن أهل المدينة فزعوا مرة، فسبقهم هو على فرس. فنحب النبي ﷺ ونتعلم منه الشجاعة، ونطلب من الله أن يعيننا على مواجهة ما يخيفنا.
- 10-13 EN: This hadith describes the Prophet ﷺ as the best, bravest and most generous of people. It tells that the people of Madinah were once alarmed, and he rode out ahead of them on a horse. We love the Prophet ﷺ and learn courage from him, asking Allah to help us face what frightens us.
- ⚠️ Flag **fear**: People of Madinah were alarmed (cause not stated in this wording). Mild.
- ⚠️ Flag **hard_to_explain**: His closing remark about the horse (that he found it like a sea) is an idiom for its speed; I left it out of the explanations.
- [ ] ok

## family-ties: Family Ties / صلة الرحم

File: `drafts/hadith/items-family-ties.json`

<a id="0wka5jtk"></a>
### M2558 · Sahih Muslim 2558 · caution

- Values: family-ties
- dorar: https://dorar.net/h/0wka5jTk · narrator: أبو هريرة · grade: صحيح (مسلم)
- First 10 words: «أنَّ رَجُلًا قال: يا رَسولَ اللهِ، إنَّ لي قَرابةً أصِلُهم …»
- Agent's reading: A man says he keeps ties with relatives who cut him off and is kind to those who are unkind; the Prophet says if he is as he describes it is as if he is feeding them hot ashes, and he will keep a helper from Allah against them as long as he continues.
- 6-9 AR: هذا الحديث يعلمنا أن نبقى على صلة بأقاربنا حتى لو لم يكونوا لطفاء معنا دائما، وأن نبقى لطفاء وهادئين. مثلا، نتصل بقريبنا ونسأل عنه، والله يعين من يفعل ذلك. وإذا آذانا أحد أو أخافنا فنخبر أبانا أو أمنا أو شخصا كبيرا نثق به.
- 6-9 EN: This hadith teaches us to stay in touch with our relatives even when they are not always kind to us, and to stay kind and calm. For example, we call a relative and ask how he is, and Allah helps the one who does this. If anyone hurts or frightens us, we tell Mom, Dad or a grown-up we trust.
- 10-13 AR: هذا الحديث يعلمنا أن نصل أقاربنا ونحسن إليهم ونتحمل جهلهم، حتى لو قطعونا وأساؤوا إلينا. وفيه أن من يبقى على هذا الخلق يبقى معه عون من الله. فنتعلم أن لا نرد الإساءة بالإساءة، ونحافظ على صلتنا بأهلنا بلطف وصبر. وإذا آذانا أحد أو أخافنا فنخبر أبانا أو أمنا أو شخصا كبيرا نثق به.
- 10-13 EN: This hadith teaches us to keep ties with our relatives, be good to them and bear their rudeness, even if they cut us off or treat us badly. It says that Allah's help stays with the person who keeps to this. We learn not to answer bad treatment with bad treatment, and to keep our family ties with gentleness and patience. If anyone hurts or frightens us, we tell Mom, Dad or a grown-up we trust.
- ⚠️ Flag **fire_or_punishment**: The Prophet's reply likens the relatives' situation to feeding them hot ashes. I left the simile out.
- ⚠️ Flag **hard_to_explain**: The simile (usually read as a reference to the relatives' own wrongdoing and the burden on them) needs scholarly commentary; I only used the positive guidance and the promise of Allah's help.
- ⚠️ Flag **other**: Sensitive for children whose relatives treat them badly or unsafely. The text could be read as 'put up with mistreatment'. Consider adding a note that a child should always tell a parent or trusted adult if someone hurts them.
- ⚠️ Flag **other**: Reviewer: added a safety line (tell a trusted grown-up if anyone hurts or frightens us).
- [ ] ok

<a id="amxkzxia"></a>
### B5984 · Sahih al-Bukhari 5984 · caution

- Values: family-ties
- dorar: https://dorar.net/h/AmXkzXia · narrator: جبير بن مطعم · grade: صحيح (البخاري)
- First 10 words: «لا يَدخُلُ الجَنَّةَ قاطِعٌ.»
- Agent's reading: No one who cuts (kinship ties) will enter Paradise.
- 6-9 AR: هذا الحديث يعلمنا أن نحافظ على صلتنا بأقاربنا ولا نقاطعهم. مثلا، نتصل بجدتنا ونسأل عنها ونزور عمتنا.
- 6-9 EN: This hadith teaches us to stay close to our relatives and not to cut them off. For example, we call our grandmother, ask how she is, and visit our aunt.
- 10-13 AR: هذا الحديث يبين أن قطع الأقارب أمر كبير عند الله، ولهذا يحثنا الإسلام على صلتهم. نصل أقاربنا بالزيارة والاتصال والسؤال عنهم، وحتى لو حصل بيننا سوء فهم نبادر نحن بالسلام والكلمة الطيبة.
- 10-13 EN: This hadith shows that cutting off relatives is a serious matter, which is why Islam urges us to keep in touch with them. We do this by visiting, calling and asking about them. Even after a misunderstanding, we can be the first to say salam and speak kindly.
- ⚠️ Flag **paradise_exclusion**: Hadith says the one who cuts (family ties) will not enter Paradise. Explanation gives only the positive action and does not mention exclusion. Scholars read the word as the one who cuts kinship ties (Bukhari chapter context); the Arabic text itself does not say what is cut.
- [ ] ok

<a id="ncwjt4pr"></a>
### B5986 · Sahih al-Bukhari 5986 · ok

- Values: family-ties
- dorar: https://dorar.net/h/NCwjT4Pr · narrator: أنس بن مالك · grade: صحيح (البخاري)
- First 10 words: «مَن أحَبَّ أن يُبسَطَ له في رِزقِه، ويُنسَأَ له في …»
- Agent's reading: Whoever wants his provision widened and his life or legacy extended should keep his family ties.
- 6-9 AR: هذا الحديث يعلمنا أن صلة الأقارب سبب لبركة في الرزق والعمر. مثلا، نزور خالتنا ونتصل بجدنا لنسأل عنه.
- 6-9 EN: This hadith teaches us that keeping in touch with relatives brings blessing in our provision and life. For example, we visit our aunt and call our grandfather to ask how he is.
- 10-13 AR: يخبرنا هذا الحديث أن من يصل أقاربه يبارك الله له في رزقه وفي عمره. صلة الرحم ليست زيارة واحدة، بل هي سؤال واتصال ومساعدة كلما استطعنا، ونقوم بها لوجه الله.
- 10-13 EN: This hadith tells us that Allah puts blessing in the provision and life of someone who keeps ties with relatives. Keeping ties is more than one visit: it means asking about them, calling and helping whenever we can, and doing it for Allah's sake.
- ⚠️ Flag **other**: Mentions lengthening of life (delay in one's term/trace). Explanation generalises to 'blessing in life' because scholars differ on the exact meaning (longer life vs lasting good name). Not frightening.
- [ ] ok

## forgiveness: Forgiveness / العفو

File: `drafts/hadith/items-forgiveness.json`

<a id="vibpfcep"></a>
### B2078 · Sahih al-Bukhari 2078 · ok

- Values: forgiveness
- dorar: https://dorar.net/h/VIBpFCEP · narrator: أبو هريرة · grade: صحيح (البخاري)
- First 10 words: «كان تاجِرٌ يُدايِنُ النَّاسَ، فإذا رَأى مُعسِرًا قال لفِتيانِه: تَجاوزوا …»
- Agent's reading: A merchant used to lend to people and told his helpers to overlook the debts of those in difficulty hoping Allah would overlook his faults, and Allah forgave him.
- 6-9 AR: هذا الحديث يحكي عن تاجر كان يسامح من لا يستطيع أن يسدد دينه، فسامحه الله. مثلا، إذا استعار صديقنا منا ثمن حلوى ولم يستطع أن يرده نصبر عليه ونسامحه.
- 6-9 EN: This hadith tells about a merchant who forgave people who could not pay what they owed him, and Allah forgave him. For example, if a friend borrowed money for a snack and cannot pay it back, we are patient with him and forgive him.
- 10-13 AR: يحكي هذا الحديث عن تاجر كان يطلب من مساعديه أن يتسامحوا مع المدين الذي يعجز عن السداد، وكان يرجو أن يتسامح الله معه، فتسامح الله معه. فمن خفف عن غيره وصبر عليه رجا من الله مثل ذلك. وهكذا نتعلم أن نكون لطفاء مع من يمر بضيق.
- 10-13 EN: This hadith tells of a merchant who told his helpers to let go of the debts of people who could not pay, hoping Allah would pass over his own faults, and Allah did. Whoever eases things for others can hope for the same from Allah. So we learn to be gentle with people who are going through a hard time.
- [ ] ok

<a id="tsyxeddj"></a>
### M2703 · Sahih Muslim 2703 · caution

- Values: forgiveness
- dorar: https://dorar.net/h/tSYxEddJ · narrator: أبو هريرة · grade: صحيح (مسلم)
- First 10 words: «مَن تابَ قَبلَ أن تَطلُعَ الشَّمسُ مِن مَغرِبِها تابَ اللهُ …»
- Agent's reading: Whoever repents before the sun rises from the west, Allah accepts his repentance.
- 6-9 AR: هذا الحديث يعلمنا أن الله يقبل توبة من تاب إليه. مثلا، إذا أخطأنا نقول لله إننا آسفون ونطلب منه أن يسامحنا ونحاول ألا نكرر الخطأ، ولا نؤجل ذلك.
- 6-9 EN: This hadith teaches us that Allah accepts the repentance of anyone who turns back to Him. For example, if we do something wrong, we tell Allah we are sorry, ask Him to forgive us, and try not to do it again, without putting it off.
- 10-13 AR: يخبرنا هذا الحديث أن باب التوبة مفتوح، وأن الله يقبل توبة من تاب إليه ما دام الوقت متاحا. لذلك لا نؤجل التوبة إذا أخطأنا، بل نعترف بالخطأ ونندم عليه ونعزم ألا نعود إليه ونطلب المغفرة من الله.
- 10-13 EN: This hadith tells us that the door of repentance is open and that Allah accepts the repentance of whoever turns to Him while there is still time. So we do not delay when we make a mistake: we admit it, feel sorry, decide not to repeat it and ask Allah for forgiveness.
- ⚠️ Flag **sensitive_aqidah**: Time limit is the sun rising from the west, a major sign of the Hour. Explanation leaves out the sign and only says repentance is open while there is time, to avoid end-times fear.
- [ ] ok

<a id="wmnhncdm"></a>
### M2759 · Sahih Muslim 2759 · caution

- Values: forgiveness
- dorar: https://dorar.net/h/wMnHnCDm · narrator: أبو موسى الأشعري · grade: صحيح (مسلم)
- First 10 words: «إنَّ اللهَ عَزَّ وجَلَّ يَبسُطُ يَدَه باللَّيلِ ليَتوبَ مُسيءُ النَّهارِ، …»
- Agent's reading: Allah extends His hand at night for the one who did wrong in the day to repent, and by day for the one who did wrong at night, until the sun rises from the west.
- 6-9 AR: هذا الحديث يعلمنا أن الله يقبل توبة عباده ليلا ونهارا. مثلا، إذا أخطأنا في الصباح أو في المساء نطلب المغفرة من الله فورا.
- 6-9 EN: This hadith teaches us that Allah accepts His servants' repentance by night and by day. For example, if we do wrong in the morning or the evening, we can ask Allah for forgiveness right away.
- 10-13 AR: يبين هذا الحديث أن الله يفتح باب التوبة للناس في كل وقت، فمن أخطأ في النهار يتوب في الليل، ومن أخطأ في الليل يتوب في النهار. فلا نيأس من رحمة الله، ونسارع بالتوبة والرجوع إليه.
- 10-13 EN: This hadith shows that Allah keeps the door of repentance open for people at all times: someone who did wrong in the day can repent at night, and the other way round. So we never lose hope in Allah's mercy, and we hurry to turn back to Him.
- ⚠️ Flag **sensitive_aqidah**: Text speaks of Allah stretching His hand (an attribute; risk of childish anthropomorphic imagery) and ends with the sun rising from the west (sign of the Hour). Explanation avoids both and says only that repentance is accepted day and night.
- [ ] ok

## generosity: Generosity / الكرم

File: `drafts/hadith/items-generosity.json`

<a id="plvaywei"></a>
### B6 · Sahih al-Bukhari 6 · ok

- Values: generosity
- dorar: https://dorar.net/h/PlvayWEi · narrator: عبدالله بن عباس · grade: صحيح (البخاري)
- First 10 words: «كان رَسولُ اللهِ صلَّى اللهُ عليه وسلَّم أجودَ النَّاسِ، وكان …»
- Agent's reading: The Prophet was the most generous of people, most of all in Ramadan when Jibril met him nightly to review the Quran, and his giving was swifter than the blowing wind.
- 6-9 AR: هذا الحديث يخبرنا أن النبي ﷺ كان أكرم الناس، وكان يعطي أكثر في رمضان. مثلا، نشارك أصدقاءنا وجيراننا بتمر أو طعام في رمضان.
- 6-9 EN: This hadith tells us that the Prophet ﷺ was the most generous of people, and he gave even more in Ramadan. For example, in Ramadan we can share some dates or food with our friends and neighbours.
- 10-13 AR: يصف هذا الحديث كرم النبي ﷺ، فقد كان أكرم الناس وكان كرمه في رمضان أعظم، حين كان جبريل عليه السلام يدارسه القرآن كل ليلة. نتعلم منه أن نزيد من العطاء والخير في رمضان، فنتصدق ونطعم الصائمين ونشارك ما عندنا بفرح.
- 10-13 EN: This hadith describes the Prophet's ﷺ generosity: he was the most generous of people, and even more so in Ramadan, when the angel Jibril met him each night to review the Quran with him. We learn from him to give more in Ramadan, by giving to charity, feeding others and sharing what we have gladly.
- [ ] ok

## good-character: Good Character / حسن الخلق

File: `drafts/hadith/items-good-character.json`

<a id="toif2n8r"></a>
### B3559 · Sahih al-Bukhari 3559 · ok

- Values: good-character
- dorar: https://dorar.net/h/ToIF2N8R · narrator: عبدالله بن عمرو · grade: صحيح (البخاري)
- First 10 words: «لَم يَكُنِ النَّبيُّ صلَّى اللهُ عليه وسلَّم فاحِشًا ولا مُتَفَحِّشًا، …»
- Agent's reading: The Prophet was neither coarse nor affected in speech or conduct, and he said the best of you are those with the best character.
- 6-9 AR: هذا الحديث يخبرنا أن النبي ﷺ لم يكن يتكلم بكلام قبيح ولا يتصرف بوقاحة، وأن من أفضل الناس أحسنهم أخلاقا. مثلا، نقول «من فضلك» و«شكرا» ولا نقول كلمات سيئة.
- 6-9 EN: This hadith tells us that the Prophet ﷺ never spoke or behaved in a rude, ugly way, and that among the best people are those with the best character. For example, we say please and thank you and we do not use bad words.
- 10-13 AR: يعلمنا هذا الحديث أن النبي ﷺ لم يكن فاحشا ولا بذيئا، وأن من أفضل الناس أحسنهم أخلاقا. حسن الخلق يظهر في كلامنا وتصرفاتنا كل يوم، مع أهلنا وأصدقائنا والغرباء، ونتدرب عليه بأن نختار الكلمة الطيبة ونتجنب الكلام الجارح.
- 10-13 EN: This hadith teaches us that the Prophet ﷺ was never foul or vulgar, and that among the best of people are those with the best character. Good character shows in how we speak and act every day, with family, friends and strangers, and we practise it by choosing kind words and avoiding hurtful speech.
- [ ] ok

<a id="bq8mtkbl"></a>
### M2553 · Sahih Muslim 2553 · caution

- Values: good-character
- dorar: https://dorar.net/h/bq8mtkbl · narrator: النواس بن سمعان الأنصاري · grade: صحيح (مسلم)
- First 10 words: «سَألتُ رَسولَ اللهِ صلَّى اللهُ عليه وسلَّم عَنِ البِرِّ والإثمِ، …»
- Agent's reading: Righteousness is good character, and sin is what unsettles your heart and you dislike people finding out about.
- 6-9 AR: هذا الحديث يعلمنا أن البر هو حسن الخلق، أي أن نكون لطفاء ومؤدبين مع الناس. وإذا شعرنا أن شيئا لا يريحنا ولا نحب أن يعرفه الناس عنا نسأل أمنا أو أبانا.
- 6-9 EN: This hadith teaches us that goodness is good character, which means being kind and polite to people. If we feel uneasy about something and would not like others to find out about it, we can ask Mom or Dad.
- 10-13 AR: يبين هذا الحديث أن البر يظهر في حسن الخلق، وأن الإثم هو ما يضايق القلب ونكره أن يطلع عليه الناس. فنستمع إلى ضميرنا، وإذا لم نكن متأكدين هل هذا الفعل صواب أو خطأ نسأل والدينا أو معلمنا أو عالما نثق به.
- 10-13 EN: This hadith explains that goodness shows itself in good character, while wrongdoing is what troubles the heart and what we would hate for others to learn about. So we listen to our conscience, and when we are unsure whether something is right or wrong, we ask our parents, a teacher or a scholar we trust.
- ⚠️ Flag **other**: The heart-unease test for sin could be over-applied by anxious or scrupulous children, and scholars treat it as applying to a sound heart and unclear matters, not as a replacement for knowledge. Explanations add a referral to parents, teacher or scholar. Not a fiqh ruling.
- [ ] ok

## good-neighbour: Being Good to Neighbours / الإحسان إلى الجار

File: `drafts/hadith/items-good-neighbour.json`

<a id="g0t9hpet"></a>
### M2625 · Sahih Muslim 2625 · ok

- Values: good-neighbour
- dorar: https://dorar.net/h/G0t9hpEt · narrator: أبو ذر الغفاري · grade: صحيح (مسلم)
- First 10 words: «يا أبا ذَرٍّ إذا طَبَختَ مَرَقةً فأكثِرْ ماءَها، وتَعاهَدْ جيرانَك.»
- Agent's reading: The Prophet advised Abu Dharr that when he cooks broth he should add plenty of water and check on his neighbours (by sharing it).
- 6-9 AR: هذا الحديث يعلمنا أن نفكر في جيراننا عندما نطبخ. مثلا، إذا طبخت أمنا شوربة نعطي جيراننا منها طبقا صغيرا.
- 6-9 EN: This hadith teaches us to think of our neighbours when we cook. For example, if Mom makes soup, we take a small bowl of it to our neighbours.
- 10-13 AR: يوجه هذا الحديث إلى الاهتمام بالجيران وتفقد أحوالهم، حتى بأمر بسيط مثل الطعام الذي نطبخه. نجعل في طعامنا ما يكفينا ويكفي جيراننا فنشاركهم ونسأل عنهم. الإحسان إلى الجار لا يحتاج إلى مال كثير، بل إلى قلب يهتم.
- 10-13 EN: This hadith guides us to care about our neighbours and check on them, even through something simple like the food we cook. We can make our meal enough to share, and ask how they are. Being good to a neighbour does not take a lot of money, only a caring heart.
- [ ] ok

<a id="hxe5ykjl"></a>
### B6018 · Sahih al-Bukhari 6018 · ok

- Values: good-neighbour, kind-words
- dorar: https://dorar.net/h/HXe5YKJL · narrator: أبو هريرة · grade: صحيح (البخاري)
- First 10 words: «مَن كان يُؤمِنُ باللهِ واليَومِ الآخِرِ فلا يُؤذِ جارَه، ومَن …»
- Agent's reading: Whoever believes in Allah and the Last Day should not harm his neighbour, should honour his guest, and should speak good or keep silent.
- 6-9 AR: هذا الحديث يعلمنا ثلاثة آداب جميلة: ألا نؤذي جارنا، وأن نكرم ضيفنا، وأن نقول كلاما طيبا أو نسكت. مثلا، نلعب بهدوء عندما يكون جارنا نائما، ونرحب بضيفنا ونقول له كلمة طيبة.
- 6-9 EN: This hadith teaches three lovely manners: not to bother our neighbour, to honour our guest, and to say something good or else stay quiet. For example, we play quietly when a neighbour is resting, and we welcome a guest with a kind word.
- 10-13 AR: يربط هذا الحديث الإيمان بالأخلاق، فالمؤمن لا يؤذي جاره ويكرم ضيفه ويتكلم بالخير أو يصمت. قبل أن نتكلم نسأل أنفسنا هل هذا الكلام طيب ونافع، فإن لم يكن كذلك فالصمت أفضل. وهكذا نحمي جيراننا وأصدقاءنا من أذى ألسنتنا.
- 10-13 EN: This hadith links faith with good behaviour: a believer does not harm their neighbour, honours their guest, and speaks good words or stays silent. Before speaking we can ask ourselves, is this kind and useful? If not, silence is better. In this way we protect our neighbours and friends from the harm of our tongue.
- ⚠️ Flag **other**: Each instruction is conditioned on believing in Allah and the Last Day. Mild; explanation presents it as faith linked to good manners, with no threat or exclusion.
- [ ] ok

<a id="qgsaingd"></a>
### B6014 · Sahih al-Bukhari 6014 · ok

- Values: good-neighbour
- dorar: https://dorar.net/h/QgsAIngd · narrator: عائشة أم المؤمنين · grade: صحيح (البخاري)
- First 10 words: «ما زالَ يوصيني جِبريلُ بالجارِ، حتَّى ظَنَنتُ أنَّه سَيورِّثُه.»
- Agent's reading: Jibril kept urging the Prophet to treat the neighbour well until the Prophet thought he would make the neighbour an heir.
- 6-9 AR: هذا الحديث يخبرنا أن جبريل عليه السلام كان يوصي النبي ﷺ بالجار كثيرا، فحق الجار كبير. مثلا، نسلم على جارنا ونساعده إذا احتاج ولا نزعجه.
- 6-9 EN: This hadith tells us that the angel Jibril kept advising the Prophet ﷺ about neighbours, so a neighbour has a big right over us. For example, we greet our neighbour, help if they need us, and do not disturb them.
- 10-13 AR: تحكي عائشة رضي الله عنها أن جبريل ظل يوصي النبي ﷺ بالجار حتى ظن النبي ﷺ أن الجار سيكون له نصيب من الميراث. هذا يدل على مكانة الجار الكبيرة في الإسلام. فنحسن إلى جيراننا بالسلام والزيارة والمساعدة، ونتجنب إزعاجهم.
- 10-13 EN: Aisha, may Allah be pleased with her, reports that Jibril kept advising the Prophet ﷺ about the neighbour so much that the Prophet ﷺ thought neighbours might even be given a share of inheritance. This shows how important neighbours are in Islam. So we are good to our neighbours by greeting them, visiting and helping them, and not disturbing them.
- ⚠️ Flag **other**: Mentions inheritance (rhetorical emphasis, not a ruling). Explanation says it only shows the importance of neighbours; no fiqh claim that neighbours inherit.
- [ ] ok

## gratitude: Gratitude / الشكر

File: `drafts/hadith/items-gratitude.json`

<a id="nnrh8eqt"></a>
### M2999 · Sahih Muslim 2999 · ok

- Values: gratitude, patience
- dorar: https://dorar.net/h/NNRH8eQT · narrator: صهيب بن سنان الرومي · grade: صحيح (مسلم)
- First 10 words: «عَجَبًا لأمرِ المُؤمِنِ، إنَّ أمرَه كُلَّه خَيرٌ، وليسَ ذاك لأحَدٍ …»
- Agent's reading: A believer's affairs are all good: he is thankful in ease and patient in hardship, and both are good for him.
- 6-9 AR: هذا الحديث يعلمنا أن المؤمن يشكر الله عندما يفرح، ويصبر عندما يحزن أو يتعب، وفي الحالتين يكون الخير له. مثلا، نقول الحمد لله إذا نجحنا، ونصبر إذا مرضنا أو خسرنا لعبة.
- 6-9 EN: This hadith teaches us that a believer thanks Allah when something good happens and is patient when something hard happens, and either way it is good for them. For example, we say alhamdulillah when we succeed, and we stay patient when we are sick or lose a game.
- 10-13 AR: يخبرنا هذا الحديث أن حال المؤمن كله خير، فإن جاءته نعمة شكر الله، وإن أصابه أمر صعب صبر، وفي الحالتين يكسب الخير. فنتدرب على شكر الله بألسنتنا وأفعالنا عند الفرح، وعلى الهدوء وعدم الشكوى الكثيرة عند الصعوبة.
- 10-13 EN: This hadith tells us that everything in a believer's life turns out good: when a blessing comes they thank Allah, and when something hard comes they are patient, and in both cases they gain good. We practise thanking Allah in words and actions when we are happy, and staying calm and not complaining too much when things are hard.
- [ ] ok

<a id="ooabsoiv"></a>
### M2734 · Sahih Muslim 2734 · ok

- Values: gratitude, table-manners
- dorar: https://dorar.net/h/oOabSoIV · narrator: أنس بن مالك · grade: صحيح (مسلم)
- First 10 words: «إنَّ اللهَ لَيَرضى عَنِ العَبدِ أن يَأكُلَ الأَكلةَ فيَحمَدَه عليها، …»
- Agent's reading: Allah is pleased with the servant who praises Him after eating a meal or drinking a drink.
- 6-9 AR: هذا الحديث يعلمنا أن الله يرضى عن العبد الذي يحمده بعد أن يأكل أو يشرب. مثلا، بعد أن ننهي طعامنا أو نشرب الماء نقول الحمد لله.
- 6-9 EN: This hadith teaches us that Allah is pleased with a person who praises Him after eating or drinking. For example, after we finish our meal or drink some water, we say alhamdulillah.
- 10-13 AR: يبين هذا الحديث أن عبارة بسيطة مثل الحمد لله بعد الأكلة أو الشربة تنال رضا الله. وهي تذكرنا أن الطعام والماء نعمة من الله، فنأكل بأدب وهدوء ونشكر الله قبل أن نترك المائدة.
- 10-13 EN: This hadith shows that a simple phrase like alhamdulillah after a bite of food or a sip of water can win Allah's pleasure. It reminds us that food and water are gifts from Allah, so we eat politely and calmly and thank Him before we leave the table.
- [ ] ok

## helping-others: Helping Others / مساعدة الآخرين

File: `drafts/hadith/items-helping-others.json`

<a id="2jhl7psd"></a>
### B2891 · Sahih al-Bukhari 2891 · ok

- Values: helping-others
- dorar: https://dorar.net/h/2jhl7Psd · narrator: أبو هريرة · grade: صحيح (البخاري)
- First 10 words: «كُلُّ سُلامى عليه صَدَقةٌ كُلَّ يَومٍ؛ يُعينُ الرَّجُلَ في دابَّتِه، …»
- Agent's reading: Every joint of a person owes charity daily, and helping someone with his mount or load, a good word, each step to prayer and guiding on the road all count as charity.
- 6-9 AR: هذا الحديث يعلمنا أن الأعمال الطيبة التي نفعلها كل يوم تعد صدقة. مثلا، نساعد أحدا على حمل أغراضه، ونقول كلمة طيبة، ونرشد من ضاع إلى الطريق.
- 6-9 EN: This hadith teaches us that the good things we do every day count as charity. For example, we help someone carry their things, say a kind word, or show someone the way when they are lost.
- 10-13 AR: يخبرنا هذا الحديث أن الصدقة ليست بالمال فقط، فمساعدة الناس بحمل متاعهم، والكلمة الطيبة، والمشي إلى الصلاة، ودلالة الضائع على الطريق كلها صدقة. نستطيع كل يوم أن نجمع الكثير من هذه الصدقات الصغيرة بالمساعدة وحسن الكلام.
- 10-13 EN: This hadith tells us that charity is not only about money: helping people carry their things, a kind word, walking to prayer and showing someone the way are all charity. Every day we can collect many small acts of charity through helping and speaking kindly.
- ⚠️ Flag **other**: Hadith opens with every joint of the body owing charity each day (the Arabic term is a technical anatomical word). Explanations omit this framing and keep the list of good deeds. Mild.
- [ ] ok

<a id="dwpuenar"></a>
### B2472 · Sahih al-Bukhari 2472 · ok

- Values: helping-others
- dorar: https://dorar.net/h/dwpUenaR · narrator: أبو هريرة · grade: صحيح (البخاري)
- First 10 words: «أنَّ رَسولَ اللهِ صلَّى اللهُ عليه وسلَّم قال: بينَما رَجُلٌ …»
- Agent's reading: A man walking found a thorny branch on the road and removed it, so Allah appreciated this and forgave him.
- 6-9 AR: هذا الحديث يحكي عن رجل وجد غصن شوك في الطريق فأزاله، فشكر الله له وغفر له. مثلا، نرفع قشرة الموز أو حجرا من الطريق حتى يمر الناس بأمان.
- 6-9 EN: This hadith tells about a man who found a thorny branch on the road and took it away, so Allah thanked him and forgave him. For example, we pick up a banana peel or a stone from the path so people can walk safely.
- 10-13 AR: يحكي هذا الحديث عن رجل رأى غصنا فيه شوك قد يؤذي المارين، فأزاله من طريقهم، فكافأه الله بالمغفرة. كان فعلا بسيطا جدا، لكن الله شكره وغفر له. وهذا يشجعنا ألا نحتقر أي عمل صغير فيه نفع للناس، مثل إزالة ما يؤذي من طريقهم، ونفعله دون انتظار مدح من أحد.
- 10-13 EN: This hadith tells of a man who passed a thorny branch on the road and took it away, so Allah thanked him and forgave him. It was a very simple act, yet Allah rewarded it. This encourages us not to look down on any small act that helps people, like clearing something harmful from their way, and to do it without waiting for anyone's praise.
- [ ] ok

<a id="vjklwesl"></a>
### B6021 · Sahih al-Bukhari 6021 · ok

- Values: helping-others
- dorar: https://dorar.net/h/vJkLWESL · narrator: جابر بن عبدالله · grade: صحيح (البخاري)
- First 10 words: «كلُّ معروفٍ صَدَقةٌ»
- Agent's reading: Every act of kindness (ma'ruf) is charity.
- 6-9 AR: هذا الحديث يعلمنا أن كل عمل طيب نفعله لغيرنا هو صدقة. مثلا، نساعد أمنا في ترتيب البيت أو نعير زميلنا قلما.
- 6-9 EN: This hadith teaches us that every good deed we do for others is a charity. For example, we help Mom tidy the house or lend a classmate a pencil.
- 10-13 AR: يعلمنا هذا الحديث أن الصدقة أوسع من المال، فكل معروف نفعله لغيرنا صدقة. فلا نستصغر أي خير، مثل مساعدة صديق في واجبه أو إرشاد أحد أو مواساة حزين، ونعمل ذلك لوجه الله.
- 10-13 EN: This hadith teaches us that charity is wider than money, because every kind act we do for others is charity. So we never think a good act is too small, such as helping a friend with homework, guiding someone, or comforting someone who is sad, and we do it for Allah's sake.
- [ ] ok

## honesty: Honesty / الصدق

File: `drafts/hadith/items-honesty.json`

<a id="aoxeic09"></a>
### B6094 · Sahih al-Bukhari 6094 · caution

- Values: honesty
- dorar: https://dorar.net/h/aOxeIC09 · narrator: عبدالله بن مسعود · grade: صحيح (البخاري)
- First 10 words: «إنَّ الصِّدقَ يَهدي إلى البِرِّ ، وإنَّ البِرَّ يَهدي إلى …»
- Agent's reading: Truthfulness leads to righteousness and Paradise and a person keeps being truthful until recorded as very truthful, while lying leads to wickedness and the Fire and a person keeps lying until recorded as a liar.
- 6-9 AR: هذا الحديث يعلمنا أن الصدق طريق إلى الخير وإلى الجنة. مثلا، إذا كسرنا شيئا في البيت نقول الحقيقة لأمنا بدل أن نخفي الأمر.
- 6-9 EN: This hadith teaches us that telling the truth is a path to goodness and to Paradise. For example, if we break something at home, we tell Mom the truth instead of hiding it.
- 10-13 AR: يبين هذا الحديث أن الصدق يقود إلى الخير وإلى الجنة، وأن من يداوم على الصدق يصبح من الصادقين المعروفين بذلك عند الله. ولهذا نحرص على الصدق حتى في الأمور الصغيرة، ونبتعد عن الكذب لأنه يقود صاحبه إلى الأخطاء، ونطلب من الله أن يعيننا على أن نكون صادقين.
- 10-13 EN: This hadith explains that truthfulness leads to goodness and to Paradise, and that someone who keeps being truthful becomes known with Allah as a very truthful person. So we stay honest even in small matters, and we keep away from lying because it leads a person toward wrongdoing, asking Allah to help us be truthful.
- ⚠️ Flag **fire_or_punishment**: Second half says lying leads to wickedness and wickedness leads to the Fire. Explanations focus on truthfulness leading to goodness and Paradise and only say lying leads toward wrongdoing; the Fire is not mentioned.
- [ ] ok

<a id="mnim7gsx"></a>
### M102 · Sahih Muslim 102 · caution

- Values: honesty
- dorar: https://dorar.net/h/mnIM7GSX · narrator: أبو هريرة · grade: صحيح (مسلم)
- First 10 words: «أنَّ رَسولَ اللهِ صلَّى اللهُ عليه وسلَّم مَرَّ على صُبرةِ …»
- Agent's reading: The Prophet put his hand into a heap of food, felt dampness, asked the seller, heard it was rain, and said he should have put it on top so people could see, and that whoever cheats is not from us.
- 6-9 AR: هذا الحديث يحكي عن بائع أخفى طعاما مبللا تحت الطعام الجيد، فنبهه النبي ﷺ إلى أن يظهر العيب للناس. مثلا، إذا بعنا أو بادلنا لعبة قديمة لصديق نقول له عن أي عيب فيها ولا نخفيه.
- 6-9 EN: This hadith tells about a seller who left wet food hidden under the good food, and the Prophet ﷺ pointed out that he should show people the flaw. For example, if we swap or sell an old toy to a friend, we tell him about anything broken and do not hide it.
- 10-13 AR: يحكي هذا الحديث أن النبي ﷺ مر على كومة طعام فوجد في داخلها بللا، فأنكر على صاحبها إخفاءه عن الناس وبين أن الغش لا يليق بالمسلم. الصدق في التعامل أن نبين العيب في ما نبيعه أو نعطيه، فلا نخدع أحدا لنكسب أكثر، لأن ثقة الناس بنا أغلى من الربح.
- 10-13 EN: This hadith tells that the Prophet ﷺ passed a pile of food, found dampness inside it, and objected to the owner hiding it from buyers, making clear that cheating does not fit a Muslim. Being honest in dealings means showing the flaw in what we sell or give, and not tricking anyone to gain more, because people's trust in us is worth more than profit.
- ⚠️ Flag **other**: Ends with a disowning phrase about the one who cheats (literally: not from me). Wording softened to 'does not fit a Muslim'; scholars discuss whether it means not following the Prophet's way. Explanation does not dwell on it.
- [ ] ok

<a id="wq3kzaeq"></a>
### B3472 · Sahih al-Bukhari 3472 · caution

- Values: honesty
- dorar: https://dorar.net/h/wq3kzaeQ · narrator: أبو هريرة · grade: صحيح (البخاري)
- First 10 words: «اشتَرى رَجُلٌ مِن رَجُلٍ عَقارًا له، فوجَدَ الرَّجُلُ الذي اشتَرى …»
- Agent's reading: A man who bought land found a jar of gold in it, each man insisted the gold was not his, and a judge settled it by having the buyer's boy marry the seller's girl, with the gold spent on them and given in charity.
- 6-9 AR: هذا الحديث يحكي عن رجلين وجد أحدهما ذهبا في الأرض التي اشتراها، وكل منهما قال إن الذهب ليس له. مثلا، إذا وجدنا لعبة صديقنا في حقيبتنا نعيدها له ولا نخفيها.
- 6-9 EN: This hadith tells about two men: one found gold in the land he had bought, and each of them said the gold was not his. For example, if we find a friend's toy in our bag, we give it back and do not hide it.
- 10-13 AR: يحكي هذا الحديث قصة رجلين تنازعا بسبب جرة ذهب وجدت في أرض بيعت، وكان كل منهما يرفض أن يأخذها لأنه يرى أنها ليست من حقه. ثم احتكما إلى رجل حكيم أشار عليهما بحل جعل الذهب يستعمل في الخير والصدقة. نتعلم أن الصدق والأمانة أهم من المال، حتى لو كان المال سهل الأخذ.
- 10-13 EN: This hadith tells of two men who disputed over a jar of gold found in a piece of land that had been sold, each refusing to take it because he felt it was not his right. They took the matter to a wise man, who suggested a solution that sent the gold toward good and charity. We learn that honesty matters more than money, even when the money would be easy to take.
- ⚠️ Flag **marriage_or_adult**: The wise man's solution is to marry the first man's boy to the other's girl and spend on them from the gold plus charity. Explanations omit the marriage and say only that the gold went to good and charity.
- ⚠️ Flag **other**: The Arabic text starts directly with the story (an account of earlier people) without a 'the Prophet said' intro; please confirm on the dorar page that this is the full Bukhari narration and that it is attributed to the Prophet. Explanations call it a story told in this hadith.
- [ ] ok

## honouring-parents: Honouring Parents / بر الوالدين

File: `drafts/hadith/items-honouring-parents.json`

<a id="ev8mxnmk"></a>
### B5971 · Sahih al-Bukhari 5971 · ok

- Values: honouring-parents
- dorar: https://dorar.net/h/EV8mxnMk · narrator: أبو هريرة · grade: صحيح (البخاري)
- First 10 words: «جاءَ رَجُلٌ إلى رَسولِ اللهِ صلَّى اللهُ عليه وسلَّم فقال: …»
- Agent's reading: Asked who most deserves his good companionship, the Prophet answered the mother three times and then the father.
- 6-9 AR: هذا الحديث يعلمنا أن الأم لها حق كبير علينا في حسن الصحبة والمعاملة، ثم الأب. مثلا، نساعد أمنا ونكلمها بلطف ونشكرها على تعبها.
- 6-9 EN: This hadith teaches us that our mother has a great right to be treated well by us, and then our father. For example, we help Mom, speak gently to her and thank her for all her hard work.
- 10-13 AR: يبين هذا الحديث أن أحق الناس بحسن صحبتنا هي أمنا، وقد ذكرها النبي ﷺ ثلاث مرات قبل أن يذكر الأب. وحسن الصحبة يكون بالكلام الطيب والمساعدة والاحترام والوقت الذي نقضيه معها، ثم نعامل أبانا بالإحسان نفسه.
- 10-13 EN: This hadith explains that the person who most deserves our good company and treatment is our mother. The Prophet ﷺ mentioned her three times before mentioning the father. Treating parents well means speaking kindly, helping, showing respect and spending time with them, and treating our father with the same kindness.
- [ ] ok

<a id="bk5vx0fu"></a>
### M2551 · Sahih Muslim 2551 · caution

- Values: honouring-parents, respecting-elders
- dorar: https://dorar.net/h/bK5vX0fu · narrator: أبو هريرة · grade: صحيح (مسلم)
- First 10 words: «رَغِمَ أنفُ، ثُمَّ رَغِمَ أنفُ، ثُمَّ رَغِمَ أنفُ، قيلَ: مَن …»
- Agent's reading: Disgraced is the person who reaches one or both parents in their old age and does not enter Paradise (through serving them).
- 6-9 AR: هذا الحديث يعلمنا أن نعتني بأمنا وأبينا عندما يكبران في السن. مثلا، نساعدهما ونتكلم معهما بلطف ونصبر عليهما.
- 6-9 EN: This hadith teaches us to look after our mother and father when they grow old. For example, we help them, speak to them gently and are patient with them.
- 10-13 AR: يذكرنا هذا الحديث بأن كبر الوالدين فرصة عظيمة لنحسن إليهما ونكسب رضا الله ودخول الجنة. فنخدمهما بصبر ونتكلم معهما بأدب ولا نتضايق منهما، ومن هنا نتعلم أيضا أن نحترم كل كبير في السن ونساعده.
- 10-13 EN: This hadith reminds us that when our parents grow old, it is a great chance to be good to them and to earn Allah's pleasure and Paradise. We serve them with patience, speak to them politely and do not get annoyed with them. From this we also learn to respect and help every older person.
- ⚠️ Flag **curse**: Opens with an idiom of strong disapproval repeated three times (literally: may his nose be rubbed in dust). Not quoted or explained; explanation gives only the positive action.
- ⚠️ Flag **paradise_exclusion**: The one who reaches his parents in old age and still does not enter Paradise. Explanation says only that caring for old parents is a chance to earn Allah's pleasure and Paradise.
- [ ] ok

## humility: Humility / التواضع

File: `drafts/hadith/items-humility.json`

<a id="at9rqqki"></a>
### M91 · Sahih Muslim 91 · caution

- Values: humility
- dorar: https://dorar.net/h/AT9RQqKI · narrator: عبدالله بن مسعود · grade: صحيح (مسلم)
- First 10 words: «لا يَدخُلُ الجَنَّةَ مَن كانَ في قَلبِه مِثقالُ ذَرَّةٍ مِن …»
- Agent's reading: No one with even an atom's weight of pride in his heart will enter Paradise; liking good clothes is not pride, because Allah is beautiful and loves beauty, and pride is rejecting the truth and looking down on people.
- 6-9 AR: هذا الحديث يعلمنا ألا نتكبر على الناس. وليس من الكبر أن نلبس ثيابا جميلة، فالله جميل ويحب الجمال.
- 6-9 EN: This hadith teaches us not to be proud and look down on people. Wearing nice clothes is not pride, because Allah is beautiful and loves beauty.
- 10-13 AR: يبين هذا الحديث أن الكبر أمر خطير في القلب، وأنه ليس لبس الثياب الجميلة، بل هو رفض الحق وازدراء الناس. فنتواضع، ونقبل الحق إذا قاله لنا صغير أو كبير، ولا نحتقر أحدا، ونفرح بما أعطانا الله دون أن نتعالى على غيرنا.
- 10-13 EN: This hadith explains that pride is a serious thing in the heart, and that it is not wearing nice clothes but rejecting the truth and looking down on people. So we stay humble, accept the truth whether a younger or older person tells it to us, never despise anyone, and enjoy what Allah has given us without feeling above others.
- ⚠️ Flag **paradise_exclusion**: Opens with: no one who has an atom's weight of pride in his heart will enter Paradise. Explanations skip this and give the positive lesson (what pride is and is not).
- [ ] ok

<a id="x2imeezk"></a>
### B2568 · Sahih al-Bukhari 2568 · ok

- Values: humility
- dorar: https://dorar.net/h/X2IMEeZk · narrator: أبو هريرة · grade: صحيح (البخاري)
- First 10 words: «لَو دُعيتُ إلى ذِراعٍ أو كُراعٍ لَأجَبتُ، ولو أُهديَ إليَّ …»
- Agent's reading: The Prophet said that if he were invited to even a cheap cut of meat he would accept, and if one were given to him as a gift he would take it.
- 6-9 AR: هذا الحديث يعلمنا أن النبي ﷺ كان متواضعا، فكان يقبل الدعوة والهدية حتى لو كانت صغيرة. مثلا، إذا أعطانا صديق حلوى صغيرة نقبلها بفرح ونشكره.
- 6-9 EN: This hadith teaches us that the Prophet ﷺ was humble: he would accept an invitation or a gift even if it was small. For example, if a friend gives us a small sweet, we accept it happily and thank him.
- 10-13 AR: يبين هذا الحديث تواضع النبي ﷺ، فهو يخبر أنه لو دعي إلى قطعة لحم بسيطة جدا لأجاب، ولو أهدي إليه مثلها لقبلها. فلا نحتقر الهدية الصغيرة ولا الدعوة البسيطة، بل نقبلها بفرح ونقدر قلب صاحبها.
- 10-13 EN: This hadith shows the Prophet's ﷺ humility: he told us that if he were invited to a very modest meal, just a plain cut of meat, he would accept, and if he were given such a thing as a gift he would take it. So we do not look down on small gifts or simple invitations, but accept them happily and appreciate the kindness behind them.
- ⚠️ Flag **hard_to_explain**: The Arabic names two cheap cuts of an animal's leg (foreleg and lower leg). Explanations generalise to a modest meal or small gift. The hadith itself does not mention thanking; the 'say thank you' in the example is our practical addition.
- [ ] ok

<a id="jtfsxg7j"></a>
### B5664 · Sahih al-Bukhari 5664 · ok

- Values: humility, visiting-the-sick
- dorar: https://dorar.net/h/jTFsxG7j · narrator: جابر بن عبدالله · grade: صحيح (البخاري)
- First 10 words: «جاءَني النَّبيُّ صلَّى اللهُ عليه وسلَّم يَعودُني، ليس براكِبِ بَغلٍ …»
- Agent's reading: The Prophet came to visit Jabir in his illness, not riding a mule or a horse.
- 6-9 AR: هذا الحديث يخبرنا أن النبي ﷺ زار جابرا المريض ولم يأت راكبا بغلا ولا حصانا. وهذا يعلمنا التواضع وعيادة المريض، مثلا نزور صديقا مريضا ونسأل عنه بلطف.
- 6-9 EN: This hadith tells us that the Prophet ﷺ visited Jabir when he was sick, and he did not come riding a mule or a horse. This teaches us humility and visiting the sick: for example, we visit a sick friend and ask kindly how he is.
- 10-13 AR: يروي جابر رضي الله عنه أن النبي ﷺ جاء لزيارته وهو مريض، ولم يكن راكبا بغلا ولا حصانا، أي جاء بصورة بسيطة. فنتعلم التواضع وأن نزور المرضى ونسأل عنهم ونفرحهم، من غير تكلف أو استعلاء.
- 10-13 EN: Jabir, may Allah be pleased with him, reports that the Prophet ﷺ came to visit him when he was sick, and that he was not riding a mule or a horse, meaning he came in a simple way. So we learn humility and to visit the sick, ask about them and cheer them up, without showing off or acting superior.
- ⚠️ Flag **hard_to_explain**: The text only says he was not on a mule or a (non-Arab breed) horse; reading it as 'he came simply, probably on foot, as a sign of humility' is an inference. Please check the dorar commentary. Explanations say 'came in a simple way'.
- [ ] ok

## justice: Justice / العدل

File: `drafts/hadith/items-justice.json`

<a id="efuzdeaq"></a>
### B2444 · Sahih al-Bukhari 2444 · caution

- Values: justice
- dorar: https://dorar.net/h/eFUZdEAq · narrator: أنس بن مالك · grade: صحيح (البخاري)
- First 10 words: «انصُرْ أخاكَ ظالِمًا أو مَظلومًا، قالوا: يا رَسولَ اللهِ، هذا …»
- Agent's reading: We should support our brother whether he is wronged or the wrongdoer, and supporting the wrongdoer means holding him back from wrongdoing.
- 6-9 AR: هذا الحديث يعلمنا أن نساعد صديقنا حتى لو أخطأ، بأن نمنعه من الخطأ بلطف. مثلا، إذا رأيت صديقك يريد أن يأخذ لعبة أخيه، فقل له بهدوء أن هذا ليس عدلا.
- 6-9 EN: This hadith teaches us to help a friend even when he is about to do wrong, by gently stopping him. For example, if you see your friend about to take his brother's toy, you calmly tell him that is not fair.
- 10-13 AR: معنى هذا الحديث أن نصرة أخينا لا تعني أن نقف معه مهما فعل، بل أن نمنعه من الظلم. نتدرب على ذلك بأن ننصح أصدقاءنا بلطف وهدوء، ونقف مع الحق حتى لو كان الخطأ من أقرب الناس إلينا.
- 10-13 EN: The meaning of this hadith is that supporting our brother does not mean siding with him whatever he does, but helping him stop being unfair. We practise this by advising our friends kindly and calmly, and by standing with what is right even when the mistake comes from someone very close to us.
- ⚠️ Flag **other**: Could be misread as tribal loyalty or physical restraint; explanation frames it as gently stopping a friend from being unfair. The hadith's wording about restraining his hands is not repeated.
- [ ] ok

<a id="uanc2wo9"></a>
### M1827 · Sahih Muslim 1827 · caution

- Values: justice
- dorar: https://dorar.net/h/uAnC2Wo9 · narrator: عبدالله بن عمرو · grade: صحيح (مسلم)
- First 10 words: «إنَّ المُقسِطينَ عِندَ اللهِ على مَنابِرَ مِن نورٍ، عن يَمينِ …»
- Agent's reading: Those who are fair in their judgement, with their families and in what they are put in charge of will have an honoured place of light with Allah.
- 6-9 AR: هذا الحديث يخبرنا أن الله يكرم الذين يعدلون ويعطون كل واحد حقه. مثلا، حين توزع الحلوى على إخوتك بالتساوي فأنت تتدرب على العدل.
- 6-9 EN: This hadith tells us that Allah honours people who are fair and give everyone what is right. For example, when you share sweets equally between your siblings, you are practising fairness.
- 10-13 AR: العدل في هذا الحديث يشمل حكمنا بين الناس وتعاملنا مع أهلنا وكل أمر نتولاه، وأهل العدل لهم عند الله مكانة كريمة. نتدرب على ذلك حين نعامل إخوتنا وأصدقاءنا بإنصاف، ونكون عادلين في اللعب وفي الكلام حتى مع من نحبه أكثر.
- 10-13 EN: Fairness in this hadith covers how we judge between people, how we treat our families, and anything we are put in charge of. Those who are fair have an honoured place with Allah. We practise this by treating siblings and friends fairly, in games and in words, even toward the ones we love most.
- ⚠️ Flag **sensitive_aqidah**: Mentions pulpits of light at the right of Allah and His two right hands. The explanation deliberately does not describe this; if the child asks, refer to a parent or teacher.
- [ ] ok

## keeping-promises: Keeping Promises / الوفاء بالوعد

File: `drafts/hadith/items-keeping-promises.json`

<a id="ngdfwh3p"></a>
### B34 · Sahih al-Bukhari 34 · caution

- Values: keeping-promises
- dorar: https://dorar.net/h/NgdFWh3P · narrator: عبدالله بن عمرو · grade: صحيح (البخاري)
- First 10 words: «أربَعٌ مَن كُنَّ فيه كان مُنافِقًا خالِصًا، ومَن كانَت فيه …»
- Agent's reading: Four traits (betraying a trust, lying, breaking a covenant, behaving wickedly in a dispute) are marks of hypocrisy, and a person with even one has a trait of hypocrisy until he gives it up.
- 6-9 AR: هذا الحديث يعلمنا أن نكون صادقين وأمناء، وأن نوفي بوعودنا، وأن نبقى مؤدبين حتى حين نختلف مع غيرنا. مثلا، إذا وعدت صديقك أن ترجع له كتابه غدا فأرجعه في الموعد.
- 6-9 EN: This hadith teaches us to be truthful and trustworthy, to keep our promises, and to stay polite even when we disagree with someone. For example, if you promise to return your friend's book tomorrow, return it on time.
- 10-13 AR: هذا الحديث يذكرنا بأربعة أخلاق سيئة علينا أن نبتعد عنها: الخيانة والكذب ونقض العهد والإساءة في الخصام. ونتعلم منه أن نحرص على عكسها: نحفظ الأمانة، ونصدق في الكلام، ونفي بما عاهدنا عليه، ونبقى منصفين ومؤدبين حتى حين نختلف. ويمكننا أن نبدأ بخطوة صغيرة كل يوم.
- 10-13 EN: This hadith reminds us of four bad habits to stay away from: betraying a trust, lying, breaking an agreement, and behaving badly in an argument. We learn to practise the opposite: look after what we are trusted with, speak the truth, keep our agreements, and stay fair and polite even when we disagree. We can begin with one small step each day.
- ⚠️ Flag **sensitive_aqidah**: Calls these traits a mark of hypocrisy (nifaq). The explanation leaves the word out and teaches the opposite traits, so no child is labelled a hypocrite.
- ⚠️ Flag **fear**: A child with a lying or promise-breaking habit might feel frightened or condemned; keep the tone about practising the good habit.
- [ ] ok

<a id="okbhqvcn"></a>
### B33 · Sahih al-Bukhari 33 · caution

- Values: keeping-promises, trustworthiness
- dorar: https://dorar.net/h/oKBHqVCn · narrator: أبو هريرة · grade: صحيح (البخاري)
- First 10 words: «آيةُ المُنافِقِ ثَلاثٌ: إذا حَدَّثَ كَذَبَ، وإذا وعَدَ أخلَفَ، وإذا …»
- Agent's reading: The sign of the hypocrite is three things: when he speaks he lies, when he promises he breaks it, and when he is trusted he betrays.
- 6-9 AR: هذا الحديث يعلمنا ثلاثة أخلاق جميلة: أن نصدق في كلامنا، وأن نفي بوعدنا، وأن نحفظ الأمانة. مثلا، إذا قلت لأمك إنك سترتب غرفتك فرتبها.
- 6-9 EN: This hadith teaches us three beautiful habits: tell the truth, keep our promises, and take care of what we are trusted with. For example, if you tell your mother you will tidy your room, then tidy it.
- 10-13 AR: يبين هذا الحديث ثلاث علامات سيئة علينا أن نبتعد عنها: الكذب في الحديث، وإخلاف الوعد، وخيانة الأمانة. نتدرب على عكسها: نتأكد من صدق كلامنا، ونفكر قبل أن نعد حتى نستطيع الوفاء، ونحفظ ما ائتمننا عليه الناس، مثل سر صديق أو شيء استعرناه.
- 10-13 EN: This hadith points out three bad signs to stay away from: lying when we speak, breaking a promise, and betraying a trust. We practise the opposite: make sure our words are true, think before promising so that we can keep our word, and look after what people trust us with, like a friend's secret or something we borrowed.
- ⚠️ Flag **sensitive_aqidah**: The hadith calls these three traits the sign of a hypocrite (munafiq). The explanation avoids the label and focuses on the good habits.
- ⚠️ Flag **fear**: Risk of making a child feel condemned for lying or breaking a promise; keep tone gentle.
- [ ] ok

## kind-words: Kind Words / الكلمة الطيبة

File: `drafts/hadith/items-kind-words.json`

<a id="tszg5zrj"></a>
### B2989 · Sahih al-Bukhari 2989 · ok

- Values: kind-words
- dorar: https://dorar.net/h/Tszg5ZRJ · narrator: أبو هريرة · grade: صحيح (البخاري)
- First 10 words: «كُلُّ سُلامى مِنَ النَّاسِ عليه صَدَقةٌ كُلَّ يَومٍ تَطلُعُ فيه …»
- Agent's reading: Every day, for each of a person's joints there is charity, and fairness between two people, helping with a mount, a good word, steps to prayer and removing harm from the road all count as charity.
- 6-9 AR: هذا الحديث يعلمنا أن الكلمة الطيبة صدقة، وأن مساعدة الناس وإبعاد الأذى عن الطريق صدقات أيضا. مثلا، حين تقول لصديقك كلمة جميلة تفرحه فهذه صدقة.
- 6-9 EN: This hadith teaches us that a kind word is charity, and so is helping people and moving something harmful out of the road. For example, when you say a lovely word that makes your friend happy, that is charity.
- 10-13 AR: يبين هذا الحديث أن الصدقة ليست بالمال فقط، فالكلمة الطيبة والإصلاح بين اثنين ومساعدة إنسان في حمل شيء وإبعاد الأذى عن الطريق كلها صدقات. نتدرب عليها كل يوم بكلمة لطيفة، أو بمساعدة صغيرة، أو بأن نرفع عن طريق المدرسة شيئا قد يؤذي الناس.
- 10-13 EN: This hadith shows that charity is not only about money. A kind word, being fair between two people, helping someone carry something, and clearing harm from the road are all charity. We can practise each day with a kind word, a small help, or by picking up something on the school path that could hurt people.
- [ ] ok

<a id="zx5majzx"></a>
### M2597 · Sahih Muslim 2597 · ok

- Values: kind-words
- dorar: https://dorar.net/h/ZX5mAjzX · narrator: أبو هريرة · grade: صحيح (مسلم)
- First 10 words: «لا يَنبَغي لصِدِّيقٍ أن يَكونَ لَعَّانًا.»
- Agent's reading: It is not fitting for a truthful, upright person (siddiq) to be someone who curses a lot.
- 6-9 AR: هذا الحديث يعلمنا أن الإنسان الصادق الطيب لا يكثر من اللعن والدعاء على الناس بالسوء. مثلا، إذا غضبنا من أحد نختار كلاما لطيفا ونبتعد عن الكلام السيئ.
- 6-9 EN: This hadith teaches us that an honest, good person does not curse people or wish bad things for them again and again. For example, when we are upset with someone, we choose gentle words and stay away from bad words.
- 10-13 AR: يبين هذا الحديث أن الإنسان الصادق لا يليق به أن يكثر من اللعن، أي من الدعاء على الناس بالسوء عند الغضب. نتدرب على ضبط لساننا حين نغضب، فنتوقف قليلا ونتنفس بهدوء ثم نتكلم بكلام مهذب، حتى تبقى كلماتنا سببا في الخير.
- 10-13 EN: This hadith shows that it does not suit a truthful person to curse often, meaning to wish harm on people when angry. We practise controlling our tongue when we are upset: pause, breathe calmly, then speak politely, so our words stay a source of good.
- ⚠️ Flag **curse**: Concerns excessive cursing (la'n). The explanation avoids any curse wording and teaches kind speech instead.
- [ ] ok

## kindness-to-animals: Kindness to Animals / الرفق بالحيوان

File: `drafts/hadith/items-kindness-to-animals.json`

<a id="asyxndqh"></a>
### M1956 · Sahih Muslim 1956 · caution

- Values: kindness-to-animals
- dorar: https://dorar.net/h/AsyXNDQH · narrator: أنس بن مالك · grade: صحيح (مسلم)
- First 10 words: «نَهى رَسولُ اللهِ صلَّى اللهُ عليه وسلَّم أن تُصبَرَ البَهائِمُ.»
- Agent's reading: The Prophet ﷺ forbade tying up animals and then using them as targets to be killed.
- 6-9 AR: هذا الحديث يعلمنا ألا نربط الحيوانات لنرميها أو نؤذيها. مثلا، لا نخيف القطة ولا نضايقها، بل نعطيها ماء وطعاما.
- 6-9 EN: This hadith teaches us never to tie up animals to throw things at them or hurt them. For example, we do not scare or bother a cat, and instead we give it water and food.
- 10-13 AR: نهى النبي ﷺ في هذا الحديث عن حبس الحيوانات لتكون هدفا يؤذيها الناس، وهذا يعلمنا أن لها حقا في الرحمة. نتدرب على ذلك بأن نتعامل مع الحيوانات بلطف، ونمنع أنفسنا من اللعب القاسي معها، ونخبر الكبار إذا رأينا من يؤذيها.
- 10-13 EN: In this hadith the Prophet ﷺ forbade tying up animals so that people can harm them, which teaches us that animals have a right to be treated with mercy. We practise this by handling animals gently, avoiding rough play with them, and telling a grown-up if we see someone hurting one.
- ⚠️ Flag **violence_or_blood**: The hadith is about tying animals up to be killed or shot at for sport. The explanation says only: do not hurt or trap animals for fun.
- ⚠️ Flag **other**: Reviewer: rated caution to match M1958; wording fixed so it cannot be read as a ban on keeping pets.
- [ ] ok

<a id="yoxnxl0l"></a>
### M1958 · Sahih Muslim 1958 · caution

- Values: kindness-to-animals
- dorar: https://dorar.net/h/YOxNxl0L · narrator: عبدالله بن عمر · grade: صحيح (مسلم)
- First 10 words: «عن سَعيدِ بنِ جُبَيرٍ، قال: مَرَّ ابنُ عُمَرَ بفِتيانٍ مِن …»
- Agent's reading: Ibn Umar found young men shooting arrows at a tied bird, rebuked them, and reported that the Prophet ﷺ cursed whoever takes a living creature as a target.
- 6-9 AR: هذا الحديث يعلمنا أن النبي ﷺ نهى بشدة عن جعل الحيوانات والطيور هدفا نرميه للتسلية. مثلا، نترك العصفور يطير فوق الشجرة ولا نرميه بالحجارة.
- 6-9 EN: This hadith teaches that the Prophet ﷺ strongly forbade using animals and birds as targets for fun. For example, we leave a sparrow to fly in the tree and never throw stones at it.
- 10-13 AR: في هذا الحديث رأى ابن عمر شبابا يتسلون برمي طير، فأنكر عليهم بشدة وبين أن النبي ﷺ أنكر اتخاذ أي كائن حي هدفا للرمي. الرحمة بالحيوان خلق عظيم، ونتدرب عليه بأن لا نؤذي الحيوان للعب، ونحسن إليه ونذكر من حولنا بلطف إذا رأيناه يتأذى.
- 10-13 EN: In this hadith, Ibn Umar saw some young men amusing themselves by shooting at a bird. He strongly disapproved and explained that the Prophet ﷺ disapproved of using any living creature as a target. Mercy to animals is a great quality, and we practise it by never hurting an animal for play, being kind to it, and gently reminding people around us if we see one being harmed.
- ⚠️ Flag **curse**: The hadith contains a curse (la'n) by Ibn Umar and the Prophet's curse on those who do this. Explanation avoids the curse and says only that Allah does not like it and that it was strongly disapproved.
- ⚠️ Flag **violence_or_blood**: Scene of young men shooting arrows at a tied bird. Described in softened terms only.
- [ ] ok

<a id="axfm3htt"></a>
### B6009 · Sahih al-Bukhari 6009 · ok

- Values: kindness-to-animals
- dorar: https://dorar.net/h/aXFm3htt · narrator: أبو هريرة · grade: صحيح (البخاري)
- First 10 words: «بينَما رَجُلٌ يَمشي بطَريقٍ، اشتَدَّ عليه العَطَشُ، فوجَدَ بئرًا فنَزَلَ …»
- Agent's reading: A thirsty man gave water to a thirsty dog using his shoe, Allah thanked and forgave him, and the Prophet said there is reward in kindness to every living creature.
- 6-9 AR: هذا الحديث يحكي عن رجل عطشان شرب من بئر، ثم رأى كلبا عطشان فسقاه، فشكر الله له وغفر له. نتعلم أن نسقي الحيوان العطشان ونطعم الجائع.
- 6-9 EN: This hadith tells of a thirsty man who drank from a well, then saw a thirsty dog and gave it water. Allah thanked him and forgave him. We learn to give water to a thirsty animal and food to a hungry one.
- 10-13 AR: في هذا الحديث شعر رجل بعطش الكلب لأنه عاش مثله، فتعب في سقايته وجاء الجزاء الكريم من الله. وبين النبي ﷺ أن في الإحسان إلى كل كائن حي أجرا. نتدرب على ذلك بأن نضع الماء للقطط والطيور، ونفكر في احتياج الحيوان كما نفكر في احتياجنا.
- 10-13 EN: In this hadith a man understood the dog's thirst because he had just felt the same, so he took the trouble to give it water, and Allah rewarded him generously. The Prophet ﷺ explained that there is a reward for being kind to every living creature. We practise this by putting out water for cats and birds, and by thinking about an animal's need the way we think about our own.
- [ ] ok

## love-of-the-prophet: Love of the Prophet ﷺ / محبة النبي ﷺ

File: `drafts/hadith/items-love-of-the-prophet.json`

<a id="1ktnzrlh"></a>
### M2832 · Sahih Muslim 2832 · ok

- Values: love-of-the-prophet
- dorar: https://dorar.net/h/1KTNZRLH · narrator: أبو هريرة · grade: صحيح (مسلم)
- First 10 words: «مِن أشَدِّ أُمَّتي لي حُبًّا ناسٌ يَكونونَ بَعدي، يَودُّ أحَدُهم …»
- Agent's reading: Among the people who love the Prophet ﷺ most are people who will come after him, each wishing to see him even at the cost of his family and wealth.
- 6-9 AR: هذا الحديث يخبرنا أن بعض الناس سيأتون بعد النبي ﷺ ويحبونه حبا عظيما جدا. ونحن نحب النبي ﷺ أيضا ونتعلم من أخلاقه الجميلة.
- 6-9 EN: This hadith tells us that some people who come after the Prophet ﷺ will love him very, very much. We love the Prophet ﷺ too, and we learn from his beautiful character.
- 10-13 AR: يبين هذا الحديث أن من الناس من يحب النبي ﷺ حبا شديدا من غير أن يراه، حتى يتمنى لقاءه أكثر من أي شيء يملكه. نعبر عن حبنا له بأن نقرأ سيرته ونتعلم أخلاقه ونصلي عليه ونطبق ما علمنا من الخير.
- 10-13 EN: This hadith shows that some people love the Prophet ﷺ deeply without ever having seen him, so much that they would long to meet him more than anything they own. We show our love for him by reading his life story, learning his manners, sending blessings on him, and practising the good he taught.
- ⚠️ Flag **other**: The Arabic wish to see him with family and wealth is read as: would gladly give up family and wealth just to see him. Wording is kept general to avoid suggesting children give up family; please verify the reading.
- [ ] ok

<a id="6gukwolb"></a>
### M408 · Sahih Muslim 408 · ok

- Values: love-of-the-prophet
- dorar: https://dorar.net/h/6GuKwoLb · narrator: أبو هريرة · grade: صحيح (مسلم)
- First 10 words: «مَن صَلَّى عليَّ واحِدةً صَلَّى اللهُ عليه عَشرًا.»
- Agent's reading: Whoever sends blessings on the Prophet once, Allah will send blessings on him ten times.
- 6-9 AR: هذا الحديث يعلمنا أن الله يصلي عشر مرات على من يصلي على النبي ﷺ مرة واحدة. مثلا، نصلي على النبي ﷺ بعد أن نسمع قصة جميلة عنه.
- 6-9 EN: This hadith teaches us that when someone sends blessings on the Prophet ﷺ once, Allah sends blessings on that person ten times. For example, we send blessings on the Prophet ﷺ after hearing a lovely story about him.
- 10-13 AR: يبين هذا الحديث أن الصلاة على النبي ﷺ، أي الدعاء له وذكره بالخير، ثوابها عظيم، فمن فعلها مرة صلى الله عليه عشرا. نتدرب عليها بأن نصلي عليه كلما ذكر اسمه، وفي أوقات هادئة من يومنا، فتزداد محبته في قلوبنا.
- 10-13 EN: This hadith shows that sending blessings on the Prophet ﷺ, meaning making dua for him and mentioning him with good, has a great reward: whoever does it once, Allah sends blessings on him ten times. We practise it by sending blessings whenever his name is mentioned and at calm moments in our day, so our love for him grows.
- [ ] ok

<a id="oi2csit1"></a>
### B15 · Sahih al-Bukhari 15 · caution

- Values: love-of-the-prophet
- dorar: https://dorar.net/h/oI2cSIt1 · narrator: أنس بن مالك · grade: صحيح (البخاري)
- First 10 words: «لا يُؤمِنُ أحَدُكُم حتَّى أكونَ أحَبَّ إليه مِن والِدِه وولَدِه …»
- Agent's reading: A person's faith is not complete until the Prophet ﷺ is dearer to him than his father, his child and all people.
- 6-9 AR: هذا الحديث يعلمنا أن محبة النبي ﷺ يجب أن تكون كبيرة جدا في قلوبنا، أكثر من محبتنا لأقرب الناس إلينا. نظهر حبنا له حين نتعلم أخلاقه ونفعل ما علمنا.
- 6-9 EN: This hadith teaches us that our love for the Prophet ﷺ should be very big in our hearts, even more than our love for those closest to us. We show our love for him when we learn his manners and do what he taught.
- 10-13 AR: يبين هذا الحديث أن كمال الإيمان يرتبط بأن تكون محبة النبي ﷺ أعلى المحبات في القلب. وهذه المحبة تظهر في أفعالنا، مثل أن نتبع أخلاقه في الصدق واللطف، ونصلي عليه، ونتعلم سيرته. ومحبتنا له لا تقلل من حبنا لأهلنا بل تجعلنا أحسن معهم.
- 10-13 EN: This hadith shows that complete faith goes together with the Prophet ﷺ having the highest place in our hearts. This love shows in what we do: following his example in honesty and kindness, sending blessings on him, and learning his life story. Loving him does not take away from our love for our family; it helps us treat them better.
- ⚠️ Flag **sensitive_aqidah**: The hadith negates faith until the Prophet is dearer than parents and children. Phrased positively; do not use it to make a child doubt their own faith or love for their parents.
- ⚠️ Flag **fear**: The last sentence of the older explanation (loving him helps us treat our family better) is a gentle pastoral addition, not text of the hadith; please check you are comfortable with it.
- [ ] ok

## mercy: Mercy / الرحمة

File: `drafts/hadith/items-mercy.json`

<a id="a4xe6w8b"></a>
### M2317 · Sahih Muslim 2317 · ok

- Values: mercy
- dorar: https://dorar.net/h/A4Xe6w8B · narrator: عائشة أم المؤمنين · grade: صحيح (مسلم)
- First 10 words: «قدِمَ ناسٌ مِنَ الأعرابِ على رَسولِ اللهِ صلَّى اللهُ عليه …»
- Agent's reading: Some bedouin said they did not kiss their children, and the Prophet ﷺ replied that he could do nothing if Allah had taken mercy from their hearts.
- 6-9 AR: هذا الحديث يعلمنا أن الرحمة بالصغار خلق جميل، فنكون حنونين مع إخوتنا الصغار في البيت. الرحمة تظهر حين نكون لطفاء مع الناس حولنا.
- 6-9 EN: This hadith teaches that being tender with little ones is a beautiful quality, so we are gentle and loving with our younger brothers and sisters at home. Mercy shows when we are kind to the people around us.
- 10-13 AR: في هذا الحديث استغرب النبي ﷺ ممن لا يظهرون الحنان لأطفالهم. نتعلم أن نملأ قلوبنا رحمة، وأن نظهرها بالحضن والكلمة الطيبة والاهتمام. ونتدرب عليها مع إخوتنا الصغار في البيت ومع كل من يحتاج إلى لطفنا بالكلمة الطيبة والمساعدة.
- 10-13 EN: In this hadith the Prophet ﷺ was surprised at people who did not show tenderness to their children. We learn to fill our hearts with mercy and to show it through hugs, kind words and care. We practise it with our younger siblings at home, and with anyone who needs our gentleness through kind words and help.
- ⚠️ Flag **other**: The hadith has a sharp line about Allah removing mercy from hearts. It could upset a child whose parent is not physically affectionate; the explanation avoids judging any parent.
- ⚠️ Flag **other**: Physical affection (hugs, kisses) is kept to family at home.
- [ ] ok

<a id="bzm4tbgy"></a>
### B5997 · Sahih al-Bukhari 5997 · ok

- Values: mercy
- dorar: https://dorar.net/h/bZm4TbgY · narrator: أبو هريرة · grade: صحيح (البخاري)
- First 10 words: «قَبَّلَ رَسولُ اللهِ صلَّى اللهُ عليه وسلَّم الحَسَنَ بنَ عَليٍّ …»
- Agent's reading: The Prophet ﷺ kissed his grandson Al-Hasan, and when Al-Aqra said he never kissed any of his ten children, the Prophet replied that one who shows no mercy will not be shown mercy.
- 6-9 AR: هذا الحديث يحكي أن النبي ﷺ قبل حفيده الحسن بحب، ويعلمنا أن من يكون رحيما بغيره ينال الرحمة. مثلا، نحنو على أخينا الصغير ونعانقه.
- 6-9 EN: This hadith tells how the Prophet ﷺ lovingly kissed his grandson Al-Hasan, and teaches us that whoever is merciful to others receives mercy. For example, we are gentle with our little brother and give him a hug.
- 10-13 AR: في هذا الحديث قال أحد الجالسين إنه لا يقبل أولاده، فبين النبي ﷺ أن من لا يرحم لا ينال الرحمة. فالرحمة طريق إلى حب الناس ورحمة الله. نمارسها بالحنان مع أهلنا، والرفق بالصغار، ومساعدة من يحتاج.
- 10-13 EN: In this hadith one of those sitting there said he never kissed his children, and the Prophet ﷺ taught that whoever shows no mercy will not receive mercy. Mercy is a path to people's love and to Allah's mercy. We practise it through tenderness with our family, gentleness with younger children, and helping those in need.
- ⚠️ Flag **fear**: Closing line (the one who is not merciful will not be shown mercy) can sound like a threat. Framed as what to do: be merciful.
- [ ] ok

<a id="thhiya8s"></a>
### M2319 · Sahih Muslim 2319 · ok

- Values: mercy
- dorar: https://dorar.net/h/thHIyA8S · narrator: جرير بن عبدالله · grade: صحيح (مسلم)
- First 10 words: «مَن لا يَرحَمِ النَّاسَ لا يَرحَمْه اللهُ عَزَّ وجَلَّ.»
- Agent's reading: Whoever does not show mercy to people, Allah will not show mercy to him.
- 6-9 AR: هذا الحديث يعلمنا أن من يرحم الناس يرحمه الله. لذلك نكون لطفاء مع الجميع. مثلا، نساعد جارا كبيرا في حمل أغراضه.
- 6-9 EN: This hadith teaches us that Allah is merciful to those who are merciful to people. So we are kind to everyone. For example, we help an older neighbour carry his bags.
- 10-13 AR: يبين هذا الحديث أن رحمتنا بالناس ترتبط برحمة الله لنا. نتدرب على الرحمة بأن نلاحظ من حولنا، فنساعد من يتعب ونخفف عن الحزين ونتجنب القسوة في الكلام والتصرف. وكل عمل لطيف صغير هو خطوة في هذا الطريق.
- 10-13 EN: This hadith shows that our mercy toward people is linked to Allah's mercy toward us. We practise mercy by noticing the people around us: helping someone who is tired, comforting someone who is sad, and avoiding harshness in our words and actions. Every small kind act is a step on this road.
- ⚠️ Flag **fear**: Closing clause (Allah will not show mercy to the one who does not) could sound threatening. The explanation focuses on the positive side.
- [ ] ok

## modesty: Modesty / الحياء

File: `drafts/hadith/items-modesty.json`

<a id="9tkrxdvc"></a>
### B24 · Sahih al-Bukhari 24 · ok

- Values: modesty
- dorar: https://dorar.net/h/9TKrxdvC · narrator: عبدالله بن عمر · grade: صحيح (البخاري)
- First 10 words: «أنَّ رَسولَ اللهِ صلَّى اللهُ عليه وسلَّم مَرَّ على رَجُلٍ …»
- Agent's reading: The Prophet ﷺ passed a man from the Ansar who was admonishing his brother about modesty and told him to leave him alone, because modesty is part of faith.
- 6-9 AR: هذا الحديث يعلمنا أن الحياء من الإيمان وأنه خلق جميل. مثلا، نستحي أن نقول كلاما سيئا أو نفعل شيئا خطأ.
- 6-9 EN: This hadith teaches us that modesty is part of faith and is a beautiful quality. For example, we feel shy about saying a bad word or doing something wrong.
- 10-13 AR: في هذا الحديث مر النبي ﷺ على رجل ينصح أخاه بشأن حيائه، فطلب منه أن يتركه، لأن الحياء من الإيمان. فالحياء يمنعنا من الخطأ ويجعلنا أرق وأكثر أدبا. نتدرب عليه بأن نختار كلامنا بعناية ونحترم من حولنا.
- 10-13 EN: In this hadith the Prophet ﷺ passed by a man advising his brother about his modesty, and told him to leave his brother alone, because modesty is part of faith. Modesty keeps us from doing wrong and makes us gentler and more polite. We practise it by choosing our words carefully and respecting the people around us.
- ⚠️ Flag **hard_to_explain**: Context is a man admonishing his brother about shyness (apparently that it holds him back); the reading is mine, please confirm. Also be careful that modesty is not used to shame children who are quiet or shy.
- [ ] ok

<a id="ki7jdjqm"></a>
### B9 · Sahih al-Bukhari 9 · ok

- Values: modesty
- dorar: https://dorar.net/h/Ki7jDJqM · narrator: أبو هريرة · grade: صحيح (البخاري)
- First 10 words: «الإيمانُ بضعٌ وسِتُّونَ شُعبةً، والحَياءُ شُعبةٌ مِنَ الإيمانِ.»
- Agent's reading: Faith has more than sixty branches, and modesty is one branch of faith.
- 6-9 AR: هذا الحديث يعلمنا أن للإيمان فروعا كثيرة مثل أغصان الشجرة، والحياء واحد منها. مثلا، حين نستحي من الكذب أو من الكلام السيئ نكون قد تمسكنا بفرع جميل من الإيمان.
- 6-9 EN: This hadith teaches us that faith has many branches, like a tree, and modesty is one of them. For example, when we feel shy about lying or about saying something bad, we are holding on to a lovely branch of faith.
- 10-13 AR: يبين هذا الحديث أن الإيمان ليس شيئا واحدا، بل له أكثر من ستين فرعا من الأقوال والأعمال والأخلاق، ومنها الحياء. نتدرب على الحياء بأن نتجنب ما يخجل منه الإنسان الطيب، ونعتني بأدبنا في كلامنا وتصرفنا.
- 10-13 EN: This hadith shows that faith is not just one thing. It has more than sixty branches of words, deeds and character, and modesty is one of them. We practise modesty by avoiding what a good person would feel ashamed to do, and by taking care of our manners in how we speak and act.
- [ ] ok

<a id="zulwpkpt"></a>
### B6117 · Sahih al-Bukhari 6117 · caution

- Values: modesty
- dorar: https://dorar.net/h/zULWpkPt · narrator: عمران بن الحصين · grade: صحيح (البخاري)
- First 10 words: «الحَياءُ لا يَأتي إلَّا بخَيرٍ. فقال بُشيرُ بنُ كَعبٍ: مَكتوبٌ …»
- Agent's reading: Modesty brings nothing but good; when Bushayr said the books of wisdom say modesty brings dignity and calm, Imran rebuked him for opposing the Prophet's words with a book.
- 6-9 AR: هذا الحديث يعلمنا أن الحياء لا يأتي إلا بالخير. مثلا، حين نستحي ونتأدب في كلامنا نكون هادئين ومحترمين.
- 6-9 EN: This hadith teaches us that modesty brings only good. For example, when we feel shy about wrong and speak politely, we are calm and respected.
- 10-13 AR: يبين هذا الحديث أن الحياء لا يأتي إلا بالخير. نتدرب على الحياء بأن نمتنع عما لا يليق، ونتكلم بأدب، ونتصرف بهدوء واحترام.
- 10-13 EN: This hadith shows that modesty brings nothing but good. We practise modesty by holding back from what is not fitting, speaking politely, and acting with calm and respect.
- ⚠️ Flag **other**: The Arabic text includes a side exchange where Imran rebukes Bushayr sharply for quoting a written saying. The explanation uses only the main teaching and the dignity and calm remark, and leaves the rebuke out.
- [ ] ok

## not-wasting: Not Wasting / عدم الإسراف

File: `drafts/hadith/items-not-wasting.json`

<a id="lyu00er7"></a>
### M593 · Sahih Muslim 593 · caution

- Values: not-wasting
- dorar: https://dorar.net/h/LYu00ER7 · narrator: المغيرة بن شعبة · grade: صحيح (مسلم)
- First 10 words: «إنَّ اللَّهَ كَرِهَ لَكُم ثَلاثًا: قيلَ وقال، وإضاعةَ المالِ، وكَثرةَ …»
- Agent's reading: Allah dislikes three things for us: idle talk (he said, she said), wasting money, and asking too much.
- 6-9 AR: هذا الحديث يعلمنا أن الله لا يحب إضاعة المال. مثلا، نشتري ما نحتاجه ونحافظ على مصروفنا ولا نضيعه فيما لا ينفع.
- 6-9 EN: This hadith teaches us that Allah does not like wasting money. For example, we buy what we need, look after our pocket money, and do not waste it on things that are of no use.
- 10-13 AR: ذكر هذا الحديث ثلاثة أمور يكرهها الله لنا، منها إضاعة المال. والمال نعمة نحفظها ونصرفها فيما ينفع. نتدرب بأن نسأل أنفسنا قبل أن نصرف مصروفنا أو نرمي شيئا: هل أحتاج هذا فعلا؟
- 10-13 EN: This hadith names three things Allah dislikes for us, one of which is wasting money. Money is a blessing we look after and spend on what is useful. We practise by asking ourselves before spending our pocket money or throwing something away: do I really need this?
- ⚠️ Flag **hard_to_explain**: The phrase about asking too much (kathrat al-su'al) is interpreted by scholars as either begging for money or asking needless or trouble-making questions. I kept it general so children are not discouraged from asking questions, which matters for the seeking-knowledge value; please check. The same hadith is also in B1477 (item S8dLuCAM).
- ⚠️ Flag **other**: Duplicate teaching with Bukhari 1477 (S8dLuCAM); consider keeping only one in the child-facing set.
- ⚠️ Flag **other**: Same hadith as B1477 (S8dLuCAM). Reviewer suggests keeping only one, preferably B1477.
- [ ] ok

<a id="s8dlucam"></a>
### B1477 · Sahih al-Bukhari 1477 · caution

- Values: not-wasting
- dorar: https://dorar.net/h/S8dLuCAM · narrator: المغيرة بن شعبة · grade: صحيح (البخاري)
- First 10 words: «سَمِعتُ النَّبيَّ صلَّى اللهُ عليه وسلَّم يقولُ: إنَّ اللهَ كَرِهَ …»
- Agent's reading: The Prophet ﷺ said Allah dislikes three things for us: idle talk (he said, she said), wasting money, and asking too much.
- 6-9 AR: هذا الحديث يعلمنا أن الله لا يحب إضاعة المال. مثلا، نشتري ما نحتاجه ونحافظ على مصروفنا ولا نضيعه فيما لا ينفع.
- 6-9 EN: This hadith teaches us that Allah does not like wasting money. For example, we buy what we need, look after our pocket money, and do not waste it on things that are of no use.
- 10-13 AR: ذكر هذا الحديث ثلاثة أمور يكرهها الله لنا، منها إضاعة المال. والمال نعمة نحفظها ونصرفها فيما ينفع. نتدرب بأن نسأل أنفسنا قبل أن نصرف مصروفنا أو نرمي شيئا: هل أحتاج هذا فعلا؟
- 10-13 EN: This hadith names three things Allah dislikes for us, one of which is wasting money. Money is a blessing we look after and spend on what is useful. We practise by asking ourselves before spending our pocket money or throwing something away: do I really need this?
- ⚠️ Flag **hard_to_explain**: The phrase about asking too much (kathrat al-su'al) is interpreted by scholars as either begging for money or asking needless or trouble-making questions. I kept it general so children are not discouraged from asking questions; please check. Same hadith as M593 (item LYu00ER7).
- ⚠️ Flag **other**: Duplicate teaching with Muslim 593 (LYu00ER7); consider keeping only one in the child-facing set.
- ⚠️ Flag **other**: Same hadith as M593 (LYu00ER7). Reviewer suggests keeping this one and dropping M593.
- [ ] ok

<a id="jnf9gyef"></a>
### M2034 · Sahih Muslim 2034 · caution

- Values: not-wasting
- dorar: https://dorar.net/h/jnF9Gyef · narrator: أنس بن مالك · grade: صحيح (مسلم)
- First 10 words: «أنَّ رَسولَ اللهِ صلَّى اللهُ عليه وسلَّم كان إذا أكَلَ …»
- Agent's reading: The Prophet ﷺ licked his three fingers after eating, told us to clean and eat a morsel that falls rather than leave it for Satan, and to wipe the bowl, since we do not know in which food the blessing lies.
- 6-9 AR: هذا الحديث يعلمنا أن نحترم الطعام ولا نضيعه. مثلا، نأكل ما في صحننا حتى آخره ولا نرمي منه شيئا نافعا، لأننا لا نعرف في أي لقمة تكون البركة.
- 6-9 EN: This hadith teaches us to respect food and not waste it. For example, we finish what is on our plate and do not throw away good food, because we do not know which bite holds the blessing.
- 10-13 AR: يبين هذا الحديث أن النبي ﷺ كان يحرص على ألا يضيع من الطعام شيئا، فيأكل ما سقط منه بعد تنظيفه ويمسح الصحن، لأننا لا نعلم أين تكون البركة. نتدرب على ذلك بأن نأخذ بقدر حاجتنا، ونكمل ما في صحننا، ونسأل الكبار عن الأفضل إذا لم نكن متأكدين من نظافة ما سقط.
- 10-13 EN: This hadith shows that the Prophet ﷺ took care not to waste any food: he would clean and eat a morsel that fell, and wipe his bowl clean, because we do not know where the blessing lies. We practise this by taking only as much as we need, finishing what is on our plate, and asking a grown-up what is best if we are not sure a fallen bite is clean.
- ⚠️ Flag **other**: Mentions Satan and the practical etiquette of eating fallen food and licking fingers. Hygiene is left to parents (I added: ask a grown-up if unsure it is clean); the explanation is about not wasting food and does not set any rule.
- ⚠️ Flag **fiqh_ruling**: Contains specific eating etiquette (adab); kept to the general principle only.
- [ ] ok

## patience: Patience / الصبر

File: `drafts/hadith/items-patience.json`

<a id="9wln0py9"></a>
### B5641 · Sahih al-Bukhari 5641 · caution

- Values: patience
- dorar: https://dorar.net/h/9WLN0py9 · narrator: أبو هريرة · grade: صحيح (البخاري)
- First 10 words: «ما يُصيبُ المُسلِمَ مِن نَصَبٍ ولا وصَبٍ، ولا هَمٍّ ولا …»
- Agent's reading: Whatever hardship, illness, worry, sadness, harm or distress touches a Muslim, even a thorn that pricks him, Allah expiates some of his sins by it.
- 6-9 AR: هذا الحديث يعلمنا أن الله لا ينسى تعبنا. حين يصيبنا تعب أو حزن أو ألم، حتى لو كان شوكة صغيرة، يمحو الله بذلك بعضا من أخطائنا، فنصبر ونطمئن.
- 6-9 EN: This hadith teaches us that Allah never overlooks our tiredness. When we feel tired, sad or hurt, even from a small thorn, Allah wipes away some of our mistakes because of it, so we stay patient and feel reassured.
- 10-13 AR: يبين هذا الحديث أن كل ما يمر على المسلم من تعب وهم وحزن وأذى، حتى الشوكة الصغيرة، يمحو الله به من أخطائه. فنتعلم أن نصبر عند الصعوبات وألا نيأس، وأن الله يرى ما يصيبنا. نتدرب على ذلك بالهدوء حين نتألم، وبالدعاء، وبالتحدث مع من نثق به.
- 10-13 EN: This hadith shows that whatever a Muslim goes through, whether tiredness, worry, sadness or harm, even a small thorn, Allah wipes away some of his mistakes because of it. We learn to be patient in hard times and not to lose hope, knowing that Allah sees what happens to us. We practise by staying calm when we are in pain, making dua, and talking to someone we trust.
- ⚠️ Flag **other**: Links hardship with erasing sins. Risk that a sick or suffering child concludes that their pain is a punishment; the explanation presents it only as comfort and does not say why hardship happens. Please keep that framing.
- [ ] ok

<a id="gquvjjkf"></a>
### B5653 · Sahih al-Bukhari 5653 · caution

- Values: patience
- dorar: https://dorar.net/h/GQUvjJKf · narrator: أنس بن مالك · grade: صحيح (البخاري)
- First 10 words: «إنَّ اللهَ قال: إذا ابتَلَيتُ عَبدي بحَبيبَتَيه فصَبَرَ، عَوَّضتُه منهما …»
- Agent's reading: Allah says that if He tests His servant by taking his two beloved things (his eyes) and he is patient, He gives him Paradise in return.
- 6-9 AR: هذا الحديث يعلمنا أن من صبر على أمر صعب جدا مثل أن لا يرى بعينيه، وعده الله بأجر عظيم في الجنة. نتعلم أن نصبر ونثق بكرم الله.
- 6-9 EN: This hadith teaches us that someone who stays patient through something very hard, such as not being able to see with his eyes, is promised a great reward in Paradise by Allah. We learn to be patient and to trust Allah's generosity.
- 10-13 AR: في هذا الحديث وعد الله من مر بابتلاء كبير مثل فقد بصره وصبر، بأن يعوضه الجنة. فالصبر لا يضيع عند الله، وكل صعوبة نصبر عليها لها أجر. نتدرب على الصبر بالهدوء عند المشكلات الصغيرة، ونحترم الذين يواجهون صعوبات ونساعدهم بلطف.
- 10-13 EN: In this hadith Allah promises that someone who goes through a great test, such as losing his sight, and is patient, will be rewarded with Paradise. Patience is never wasted with Allah, and every difficulty we bear patiently has a reward. We practise patience by staying calm over small problems, and by respecting people who face difficulties and helping them kindly.
- ⚠️ Flag **other**: About blindness or loss of sight as a test. A child with a visual impairment or a blind relative might be affected; explanation says the reward is for patience and does not imply that the disability is a punishment. Please decide whether to show this item to a child with a disability.
- ⚠️ Flag **sensitive_aqidah**: This is a hadith qudsi (Allah speaking) about a divine promise; explanation kept to reward for patience only.
- [ ] ok

## prayer: Prayer / الصلاة

File: `drafts/hadith/items-prayer.json`

<a id="lshtdt24"></a>
### M233 · Sahih Muslim 233 · caution

- Values: prayer
- dorar: https://dorar.net/h/LsHTdt24 · narrator: أبو هريرة · grade: صحيح (مسلم)
- First 10 words: «الصَّلَواتُ الخَمسُ، والجُمعةُ إلى الجُمعةِ، ورَمَضانُ إلى رَمَضانَ: مُكَفِّراتٌ ما …»
- Agent's reading: The five prayers, Friday to Friday and Ramadan to Ramadan wipe out the sins committed between them, provided the major sins are avoided.
- 6-9 AR: هذا الحديث يعلمنا أن الصلوات الخمس وصلاة الجمعة وصيام رمضان تمحو أخطاءنا الصغيرة بين كل واحدة والتي بعدها، ما دمنا نبتعد عن الذنوب الكبيرة. فنحافظ على صلاتنا في وقتها.
- 6-9 EN: This hadith teaches us that the five daily prayers, the Friday prayer and the fasting of Ramadan wipe away our small mistakes between each one and the next, as long as we stay away from big sins. So we keep our prayers on time.
- 10-13 AR: يبين هذا الحديث أن العبادات المنتظمة، وهي الصلوات الخمس والجمعة ورمضان، تمحو ما بينها من الأخطاء ما دمنا نبتعد عن الذنوب الكبيرة. فهي فرصة متجددة لنبدأ من جديد. نتدرب على ذلك بالمحافظة على صلاتنا، ونتعلم من أهلنا ومعلمينا ما هي الذنوب الكبيرة لنبتعد عنها.
- 10-13 EN: This hadith shows that regular acts of worship, the five prayers, the Friday prayer and Ramadan, wipe away the mistakes between them as long as we stay away from major sins. They are a fresh chance to start again. We practise by keeping up our prayers, and we learn from our family and teachers what the major sins are so we can avoid them.
- ⚠️ Flag **fiqh_ruling**: Scholars discuss what exactly is forgiven (minor sins) and what the condition of avoiding major sins means. The explanation keeps it general, without giving any ruling, and tells the child to ask elders.
- ⚠️ Flag **other**: Mentions major sins (kaba'ir) as a condition; the explanation refers to them only as big sins to avoid and does not list any.
- [ ] ok

<a id="ncsbydvr"></a>
### B528 · Sahih al-Bukhari 528 · ok

- Values: prayer
- dorar: https://dorar.net/h/NCSBYdvR · narrator: أبو هريرة · grade: صحيح (البخاري)
- First 10 words: «أنَّه سَمِعَ رَسولَ اللهِ صلَّى اللهُ عليه وسلَّم يقولُ: أرَأيتُم …»
- Agent's reading: The Prophet compares the five daily prayers to bathing five times a day in a river at one's door, leaving no dirt, and says that is how Allah erases sins through them.
- 6-9 AR: هذا الحديث يشبه الصلوات الخمس بنهر نستحم فيه كل يوم، فلا يبقى علينا أي وسخ. وهكذا يمحو الله بصلاتنا أخطاءنا، فنحافظ عليها كل يوم.
- 6-9 EN: This hadith compares the five daily prayers to a river we wash in every day, so no dirt is left on us. In the same way, Allah wipes away our mistakes through prayer, so we try to pray every day.
- 10-13 AR: يضرب لنا هذا الحديث مثالا: لو كان عند باب بيتك نهر تغتسل فيه كل يوم خمس مرات، فلن يبقى على جسمك وسخ. كذلك الصلوات الخمس يمحو الله بها الخطايا. فكل صلاة فرصة جديدة لنبدأ من جديد، ولذلك نحرص على أدائها في وقتها.
- 10-13 EN: This hadith gives an example: if there were a river at your door and you washed in it five times a day, no dirt would stay on you. The five daily prayers are like that, because Allah wipes away mistakes through them. Each prayer is a fresh start during the day, so we try to pray each one on time.
- [ ] ok

<a id="imrmnm3g"></a>
### B574 · Sahih al-Bukhari 574 · ok

- Values: prayer
- dorar: https://dorar.net/h/iMRMNM3G · narrator: أبو موسى الأشعري · grade: صحيح (البخاري)
- First 10 words: «أنَّ رَسولَ اللهِ صلَّى اللهُ عليه وسلَّم قال: مَن صَلَّى …»
- Agent's reading: Whoever prays the two cool-time prayers (understood as Fajr and Asr) will enter Paradise.
- 6-9 AR: هذا الحديث يعلمنا أن لصلاتي الفجر والعصر مكانة كبيرة عند الله، وأن من صلاهما يدخل الجنة. مثلا، نستيقظ مع أبينا لصلاة الفجر، ونصلي العصر قبل أن ننشغل باللعب.
- 6-9 EN: This hadith teaches that the Fajr and Asr prayers are very special to Allah, and that whoever prays them is promised Paradise. For example, we wake up with Dad for Fajr and pray Asr before we get busy playing.
- 10-13 AR: هذا الحديث يبشر بالجنة من صلى صلاتي الفجر والعصر. وقد يكون من الصعب علينا أحيانا أن نقوم لهما، فالفجر وقت النوم والعصر وقت انشغال النهار، ولذلك يشجعنا الحديث على الاهتمام بهما. نستطيع أن نضبط المنبه للفجر، وأن نذكر أنفسنا بالعصر قبل أن ننشغل.
- 10-13 EN: This hadith gives the good news of Paradise to whoever prays the Fajr and Asr prayers. It can be hard to get up for them sometimes, since Fajr is sleeping time and Asr comes when the day is busy, so the hadith encourages us to take care of them. We can set an alarm for Fajr and remind ourselves about Asr before we get busy.
- ⚠️ Flag **other**: The hadith says only al-bardayn (the two cool times). I explained it as Fajr and Asr, the standard scholarly reading; the lead may want to confirm the dorar commentary says the same. The reward is promised Paradise, not an exclusion threat.
- [ ] ok

## remembering-allah: Remembering Allah / ذكر الله

File: `drafts/hadith/items-remembering-allah.json`

<a id="pbt76jn6"></a>
### B6406 · Sahih al-Bukhari 6406 · ok

- Values: remembering-allah
- dorar: https://dorar.net/h/PBT76jn6 · narrator: أبو هريرة · grade: صحيح (البخاري)
- First 10 words: «كَلِمَتانِ خَفيفَتانِ على اللِّسانِ، ثَقيلَتانِ في الميزانِ، حَبيبَتانِ إلى الرَّحمَنِ: …»
- Agent's reading: Two phrases of glorifying Allah are light on the tongue, heavy on the scale of deeds and beloved to Allah.
- 6-9 AR: هذا الحديث يخبرنا بعبارتين قصيرتين سهل جدا قولهما، لكنهما ثقيلتان في ميزان الحسنات ويحبهما الله. مثلا، نقول سبحان الله ونحن نمشي إلى المدرسة.
- 6-9 EN: This hadith tells us about two short phrases that are very easy to say, but they weigh a lot on the scale of good deeds, and Allah loves them. For example, we can say subhanallah while we walk to school.
- 10-13 AR: هذا الحديث يعلمنا عبارتين في تسبيح الله، قولهما سهل على اللسان لكن ثوابهما كبير يوم القيامة، ويحبهما الله. فلا نحتاج وقتا طويلا لنكسب الحسنات، إذ نستطيع أن نسبح الله ونحن في الطريق أو قبل النوم، ونعود ألسنتنا على ذكره.
- 10-13 EN: This hadith teaches two phrases of glorifying Allah that are easy to say but carry great reward on the Day of Judgement, and Allah loves them. We do not need a lot of time to earn good deeds, because we can glorify Allah on the way somewhere or before sleep, and get our tongues used to remembering Him.
- [ ] ok

<a id="zmg5qhaf"></a>
### B6407 · Sahih al-Bukhari 6407 · ok

- Values: remembering-allah
- dorar: https://dorar.net/h/ZMG5qhAf · narrator: أبو موسى الأشعري · grade: صحيح (البخاري)
- First 10 words: «مَثَلُ الذي يَذكُرُ رَبَّه والذي لا يَذكُرُ رَبَّه مَثَلُ الحَيِّ …»
- Agent's reading: The one who remembers his Lord and the one who does not are like the living and the dead.
- 6-9 AR: هذا الحديث يشبه من يذكر ربه بإنسان فيه حياة، ومن لا يذكر ربه بمن ليس فيه حياة. فنحب أن نذكر الله كل يوم، مثلا نقول بسم الله قبل الأكل ونقول الحمد لله بعده.
- 6-9 EN: This hadith compares someone who remembers their Lord to a person full of life, and someone who does not remember Him to a person without life. So we love to remember Allah every day, for example by saying bismillah before eating and alhamdulillah after.
- 10-13 AR: يضرب هذا الحديث مثلا ليبين قيمة ذكر الله: الإنسان الذي يذكر ربه كأنه حي نشيط، والذي ينسى ذكره كأنه بلا حياة. فكأن ذكر الله يعطي الإنسان حياة وطمأنينة. نستطيع أن نجعل لنا عادة بسيطة، مثل أذكار الصباح والمساء وقول بسم الله عند بدء كل عمل.
- 10-13 EN: This hadith uses a comparison to show how valuable remembering Allah is: a person who remembers their Lord is like someone alive and active, and a person who forgets Him is like someone without life. It is as if remembering Allah gives a person life and calm. We can build a simple habit, like morning and evening adhkar and saying bismillah before every task.
- ⚠️ Flag **death**: The comparison is the living and the dead. I kept it as 'with life' versus 'without life' and avoided the word dead for the younger text; the lead may prefer it that way or may want to keep the item only for older children.
- [ ] ok

<a id="ihf75mah"></a>
### B6405 · Sahih al-Bukhari 6405 · ok

- Values: remembering-allah
- dorar: https://dorar.net/h/ihf75Mah · narrator: أبو هريرة · grade: صحيح (البخاري)
- First 10 words: «مَن قال: سُبحانَ اللهِ وبحَمدِه، في يَومٍ مِائةَ مَرَّةٍ، حُطَّت …»
- Agent's reading: Whoever says the tasbih and tahmid phrase a hundred times in a day has his sins removed, even if they are like the foam of the sea.
- 6-9 AR: هذا الحديث يخبرنا أن من سبح الله وحمده مئة مرة في اليوم غفر الله له أخطاءه، حتى لو كانت كثيرة جدا. نستطيع أن نفعل ذلك قليلا قليلا، مع أمنا في الطريق أو قبل النوم.
- 6-9 EN: This hadith tells us that whoever glorifies and praises Allah a hundred times in a day has their mistakes forgiven, even if there are very many. We can do it little by little, with Mom on the way somewhere or before bed.
- 10-13 AR: هذا الحديث يعلمنا أن من سبح الله وحمده مئة مرة في اليوم حطت خطاياه ولو كانت كثيرة جدا. فهو يفتح لنا بابا واسعا لرحمة الله بذكر قصير وسهل. نستطيع أن نوزع المئة على اليوم، فنسبح بعد الصلوات وفي الطريق وقبل النوم.
- 10-13 EN: This hadith teaches that whoever glorifies and praises Allah a hundred times a day has their sins taken away, even if they are very many. It opens a wide door to Allah's mercy through a short, easy act of remembrance. We can spread the hundred through the day, after prayers, on the way somewhere and before sleep.
- [ ] ok

## respecting-elders: Respecting Elders / توقير الكبير

File: `drafts/hadith/items-respecting-elders.json`

<a id="vvpnsbdg"></a>
### B6231 · Sahih al-Bukhari 6231 · ok

- Values: respecting-elders
- dorar: https://dorar.net/h/vVpnSbdg · narrator: أبو هريرة · grade: صحيح (البخاري)
- First 10 words: «يُسَلِّمُ الصَّغيرُ على الكَبيرِ، والمارُّ على القاعِدِ، والقَليلُ على الكَثيرِ»
- Agent's reading: The younger person greets the older, the one passing greets the one sitting, and the few greet the many.
- 6-9 AR: هذا الحديث يعلمنا من يبدأ بالسلام: الصغير يسلم على الكبير، والماشي يسلم على الجالس، والقليلون يسلمون على الكثيرين. مثلا، نسلم على جدنا حين نراه.
- 6-9 EN: This hadith teaches who starts the greeting of salam: the younger person greets the older one, the person passing by greets the one sitting, and a small group greets a bigger group. For example, we greet Grandpa as soon as we see him.
- 10-13 AR: هذا الحديث يعلمنا ترتيبا جميلا في بدء السلام: الصغير يبدأ الكبير، والمار يبدأ الجالس، والمجموعة القليلة تبدأ المجموعة الكبيرة. وهو أدب يعلمنا احترام الكبار ويجعل السلام سهلا بين الناس في كل مكان. نتذكره في المدرسة وفي الشارع وفي المسجد.
- 10-13 EN: This hadith teaches a lovely order for who starts the greeting: the younger greets the older, the person passing greets the one sitting, and the smaller group greets the larger group. It is good manners that teaches us to respect older people and makes greeting easy everywhere. We can remember it at school, in the street and at the mosque.
- [ ] ok

## seeking-knowledge: Seeking Knowledge / طلب العلم

File: `drafts/hadith/items-seeking-knowledge.json`

<a id="dmrsq583"></a>
### B71 · Sahih al-Bukhari 71 · caution

- Values: seeking-knowledge
- dorar: https://dorar.net/h/dmrsq583 · narrator: معاوية بن أبي سفيان · grade: صحيح (البخاري)
- First 10 words: «سَمِعتُ النَّبيَّ صلَّى اللهُ عليه وسلَّم يقولُ: مَن يُرِدِ اللهُ …»
- Agent's reading: Whoever Allah wants good for, He gives deep understanding of the religion; the Prophet only distributes while Allah gives; and this community will remain upright on Allah's command, not harmed by those who oppose it, until Allah's command comes.
- 6-9 AR: هذا الحديث يخبرنا أن من يريد الله به خيرا يجعله يفهم دينه فهما جيدا. لذلك نحب أن نتعلم ديننا ونسأل أهلنا ومعلمينا عما لا نفهمه.
- 6-9 EN: This hadith tells us that when Allah wants good for someone, He helps them understand their religion well. So we love learning about our religion and asking our family and teachers about what we do not understand.
- 10-13 AR: يبشرنا هذا الحديث بأن فهم الدين علامة على أن الله أراد بصاحبه الخير، وهو يرفع قيمة طلب العلم. ويذكرنا بأن العلم نعمة يعطيها الله لمن يشاء. فنتعلم بجد، ونسأل المعلمين وأهلنا، ونحاول أن نفهم الشيء لا أن نحفظه فقط.
- 10-13 EN: This hadith gives good news that understanding the religion is a sign Allah wants good for a person, and it raises the value of seeking knowledge. It reminds us that knowledge is a gift Allah gives to whoever He wills. So we study hard, ask our teachers and family, and try to understand things rather than only memorise them.
- ⚠️ Flag **hard_to_explain**: The second half (the Prophet only distributes while Allah gives, and this community will stay upright on Allah's command until His decree comes, unharmed by those who differ) is hard for children and touches the idea of the saved community. I explained only the first half and the giving-by-Allah point; the lead may want to quote only the first clause.
- [ ] ok

<a id="j8bvod7a"></a>
### M1631 · Sahih Muslim 1631 · caution

- Values: seeking-knowledge
- dorar: https://dorar.net/h/j8bVoD7A · narrator: أبو هريرة · grade: صحيح (مسلم)
- First 10 words: «إذا ماتَ الإنسانُ انقَطَعَ عنه عَمَلُه إلَّا مِن ثَلاثةٍ: إلَّا …»
- Agent's reading: When a person dies his deeds stop except three: ongoing charity, knowledge that is benefited from, and a righteous child who prays for him.
- 6-9 AR: هذا الحديث يخبرنا أن هناك أعمالا طيبة يستمر ثوابها لصاحبها زمنا طويلا: صدقة تنفع الناس باستمرار، وعلم ينتفع به الناس، وولد صالح يدعو له. فنتعلم ونعلم غيرنا الخير.
- 6-9 EN: This hadith tells us that some good deeds keep bringing reward to a person for a very long time: charity that keeps helping people, knowledge that people benefit from, and a good child who prays for them. So we learn, and we teach others what is good.
- 10-13 AR: هذا الحديث يبين أن أعمال الإنسان تنقطع بعد أن ينتقل من الدنيا، إلا ثلاثة أعمال يبقى أجرها: صدقة جارية تنفع الناس، وعلم ينتفع به، وولد صالح يدعو له. فهو يشجعنا على أن نبني خيرا يدوم، مثل أن نتعلم ما ينفع ونعلمه، وأن نشارك في صدقة تستمر، وأن نكون أبناء صالحين ندعو لأهلنا.
- 10-13 EN: This hadith explains that a person's deeds stop once they have passed on from this world, except for three kinds whose reward continues: ongoing charity that keeps helping people, knowledge that people benefit from, and a good child who prays for them. It encourages us to build good that lasts, such as learning useful things and teaching them, taking part in charity that continues, and being good children who make dua for our family.
- ⚠️ Flag **death**: The hadith is about what continues after a person dies. I used gentle wording ('a very long time' for ages 6-9, 'passed on from this world' for older) and kept the focus on lasting good. A child may worry about parents dying; the lead may want a parent-facing note.
- [ ] ok

<a id="ymywjzdb"></a>
### B5027 · Sahih al-Bukhari 5027 · ok

- Values: seeking-knowledge
- dorar: https://dorar.net/h/ymYWjzdb · narrator: عثمان بن عفان · grade: صحيح (البخاري)
- First 10 words: «خَيرُكُم مَن تَعَلَّمَ القُرآنَ وعَلَّمَه. قال: وأقرَأ أبو عبدِ الرَّحمَنِ …»
- Agent's reading: The best of you is the one who learns the Quran and teaches it, followed by a narrator's note about a teacher who taught Quran for a long time because of this.
- 6-9 AR: هذا الحديث يعلمنا أن من أفضل الناس من يتعلم القرآن ويعلمه لغيره. مثلا، نتعلم سورة جديدة ثم نساعد أخانا الصغير على حفظها.
- 6-9 EN: This hadith teaches that some of the best people are those who learn the Quran and teach it to others. For example, we learn a new surah and then help our little brother or sister memorise it.
- 10-13 AR: هذا الحديث يعلمنا أن من أفضل الناس من يتعلم القرآن ويعلمه. فالمسلم لا يكتفي بأن يتعلم لنفسه، بل ينقل ما تعلمه إلى غيره. نستطيع أن نبدأ بما نعرف، فنقرأ مع أصدقائنا ونصحح لهم بلطف ونتعلم منهم أيضا.
- 10-13 EN: This hadith teaches that some of the best people are those who learn the Quran and teach it. A Muslim does not only learn for themselves but passes on what they have learned. We can start with what we know, reading with our friends, gently helping them and learning from them too.
- ⚠️ Flag **other**: The second part of the Arabic text is a narrator's remark about Abu Abd al-Rahman teaching in Uthman's time and al-Hajjaj, not the Prophet's words. I explained only the Prophet's statement; the lead may want to show only the first sentence.
- [ ] ok

## sincerity: Sincerity / الإخلاص

File: `drafts/hadith/items-sincerity.json`

<a id="xwsltk8a"></a>
### B6953 · Sahih al-Bukhari 6953 · caution

- Values: sincerity
- dorar: https://dorar.net/h/XwSlTK8a · narrator: عمر بن الخطاب · grade: صحيح (البخاري)
- First 10 words: «يا أيُّها النَّاسُ، إنَّما الأعمالُ بالنِّيَّةِ، وإنَّما لامرِئٍ ما نَوى، …»
- Agent's reading: Deeds are by intentions and each person gets what he intended; whoever migrated for Allah and His Messenger gets that reward, and whoever migrated for worldly gain or a woman to marry gets what he migrated for.
- 6-9 AR: هذا الحديث يعلمنا أن ثواب عملنا يتبع نيتنا. فإذا عملنا الخير لأجل الله نفرح بثوابه عند الله. مثلا، نساعد أمنا لأننا نحب رضا الله، لا لنأخذ هدية.
- 6-9 EN: This hadith teaches that the reward for what we do follows our intention. When we do good for Allah's sake, we are happy with the reward from Allah. For example, we help Mom because we want Allah to be pleased, not to get a present.
- 10-13 AR: يعلمنا هذا الحديث أن الأعمال تقاس بالنية، وأن لكل إنسان ما نواه. ويضرب مثلا بالهجرة: من هاجر لله ورسوله فهجرته لله ورسوله، ومن هاجر لأجل شيء من الدنيا فله ما نواه. فنراجع نيتنا قبل أن نبدأ أي عمل، ونسأل أنفسنا: هل أفعل هذا لله أم لأجل أن يمدحني الناس؟
- 10-13 EN: This hadith teaches that deeds are judged by their intentions, and that each person gets what they intended. It gives the example of hijra, moving for Allah and His Messenger versus moving for something worldly, where a person gets what they aimed for. So we check our intention before any action and ask ourselves: am I doing this for Allah, or so people will praise me?
- ⚠️ Flag **marriage_or_adult**: The hadith contains a clause about migrating to marry a woman. I left marriage out entirely and described it as 'something worldly'. The lead should decide whether the card should show the Arabic in full or only the first sentence.
- [ ] ok

<a id="zsak0gof"></a>
### B6499 · Sahih al-Bukhari 6499 · caution

- Values: sincerity
- dorar: https://dorar.net/h/ZsAK0GOF · narrator: جندب بن عبدالله · grade: صحيح (البخاري)
- First 10 words: «مَن سَمَّعَ سَمَّعَ اللهُ به، ومَن يُرائي يُرائي اللهُ به.»
- Agent's reading: Whoever does deeds to be heard by people, Allah will make his intention known, and likewise for the one who shows off.
- 6-9 AR: هذا الحديث يعلمنا أن نعمل الخير لله وحده، لا لنسمع الناس أو نريهم. مثلا، نتصدق أو نقرأ القرآن لأننا نحب الله، لا لنتفاخر أمام أصدقائنا.
- 6-9 EN: This hadith teaches us to do good for Allah alone, not so that people will hear about it or see it. For example, we give charity or read Quran because we love Allah, not to show off to our friends.
- 10-13 AR: يحذرنا هذا الحديث من أن نعمل الخير لنسمع الناس أو نريهم، فالله يعلم نياتنا. والإخلاص أن يكون هدفنا رضا الله لا مدح الناس. نتدرب على أن نعمل بعض الخير سرا، ونطلب الأجر من الله وحده.
- 10-13 EN: This hadith warns us against doing good so that people will hear or see it, because Allah knows our intentions. Sincerity means our goal is Allah's pleasure, not people's praise. We can practise doing some good in secret and asking for the reward from Allah alone.
- ⚠️ Flag **fear**: The hadith is a warning that Allah will expose the intentions of the one who shows off. The wording is a bit scary, so I focused on what to do (sincerity) and did not describe the consequence. I also read it with the standard commentary meaning, which the lead may want to check on dorar.
- [ ] ok

## spreading-salam: Spreading Salam / إفشاء السلام

File: `drafts/hadith/items-spreading-salam.json`

<a id="opjdwzhi"></a>
### B12 · Sahih al-Bukhari 12 · ok

- Values: spreading-salam
- dorar: https://dorar.net/h/OPJDwzHI · narrator: عبدالله بن عمرو · grade: صحيح (البخاري)
- First 10 words: «أنَّ رَجُلًا سَألَ النَّبيَّ صلَّى اللهُ عليه وسلَّم: أيُّ الإسلامِ …»
- Agent's reading: A man asked which Islam is best, and the Prophet answered: feeding food and giving salam to those you know and those you do not know.
- 6-9 AR: سأل رجل النبي ﷺ عن أفضل عمل في الإسلام، فعلمنا هذا الحديث أن إطعام الطعام والسلام على الناس خير. مثلا، نسلم على الناس في المسجد ونحن مع أبينا أو أمنا، ونعطي جارنا من طعامنا.
- 6-9 EN: A man asked the Prophet ﷺ which part of Islam is best, and this hadith teaches that feeding people and greeting people with salam is good. For example, we greet people at the mosque when we are with Mom or Dad, and share our food with a neighbour.
- 10-13 AR: يبين هذا الحديث أن من خير الأعمال في الإسلام إطعام الطعام والسلام على من نعرف ومن لا نعرف. فالسلام لا يقتصر على أصدقائنا، بل هو تحية لكل مسلم نلقاه، وهو يجعل مجتمعنا أقرب وأكثر أمانا. نبدأ بالسلام على الجيران والمعلمين، وعلى من لا نعرفه ونحن مع أهلنا.
- 10-13 EN: This hadith shows that feeding others and greeting people with salam, whether we know them or not, are among the best things in Islam. Salam is not only for our friends, but a greeting for every Muslim we meet, and it brings people closer together. We can start by greeting our neighbours and teachers, and people we do not know when we are with our family.
- ⚠️ Flag **other**: Stranger safety: greeting people we do not know is framed as "when we are with our family".
- [ ] ok

<a id="i4cydpl0"></a>
### B6232 · Sahih al-Bukhari 6232 · ok

- Values: spreading-salam
- dorar: https://dorar.net/h/i4CYDpl0 · narrator: أبو هريرة · grade: صحيح (البخاري)
- First 10 words: «يُسَلِّمُ الرَّاكِبُ على الماشي، والماشي على القاعِدِ، والقَليلُ على الكَثيرِ.»
- Agent's reading: The rider greets the walker, the walker greets the one sitting, and the few greet the many.
- 6-9 AR: هذا الحديث يعلمنا من يبدأ بالسلام: الراكب يسلم على الماشي، والماشي على الجالس، والقليلون على الكثيرين. مثلا، حين نمر بناس جالسين نقول لهم السلام عليكم.
- 6-9 EN: This hadith teaches who starts the greeting of salam: the rider greets the walker, the walker greets the one sitting, and a small group greets a bigger group. For example, when we pass people sitting, we say assalamu alaikum to them.
- 10-13 AR: يعلمنا هذا الحديث آداب بدء السلام: يبدأ الراكب الماشي، ويبدأ الماشي الجالس، وتبدأ المجموعة القليلة الكثيرة. هذه الآداب تجعل السلام عادة منظمة وسهلة بين الناس. وهي تذكرنا بأن نبادر بالسلام ولا ننتظر أن يبدأ غيرنا.
- 10-13 EN: This hadith teaches the manners of who starts the greeting: the rider greets the walker, the walker greets the one sitting, and the smaller group greets the larger one. These manners make greeting an easy and organised habit between people. They remind us to take the first step with salam rather than waiting for others to start.
- [ ] ok

<a id="mkfgoht2"></a>
### B6247 · Sahih al-Bukhari 6247 · ok

- Values: spreading-salam
- dorar: https://dorar.net/h/mkFGoHT2 · narrator: أنس بن مالك · grade: صحيح (البخاري)
- First 10 words: «أنَّه مَرَّ على صِبيانٍ فسَلَّمَ عليهم وقال: كان النَّبيُّ صلَّى …»
- Agent's reading: Anas passed by some children, greeted them, and said the Prophet used to do that.
- 6-9 AR: مر أنس بن مالك على أطفال فسلم عليهم، وقال إن النبي ﷺ كان يفعل ذلك. فالسلام ليس للكبار فقط، ونحن نسلم على أصدقائنا وإخوتنا الصغار أيضا.
- 6-9 EN: Anas ibn Malik passed by some children and greeted them with salam, and he said the Prophet ﷺ used to do this. So salam is not only for grown-ups, and we greet our friends and little brothers and sisters too.
- 10-13 AR: يخبرنا هذا الحديث أن أنس بن مالك سلم على الأطفال، وأنه تعلم ذلك من فعل النبي ﷺ. فالسلام ليس للكبار فقط، والنبي ﷺ كان قدوة لنا في ذلك. فإذا كنت أنت الأكبر في مجموعة من الأطفال الأصغر فلا تتردد في أن تبدأ بالسلام عليهم.
- 10-13 EN: This hadith tells us that Anas ibn Malik greeted some children, and that he learned this from the Prophet's ﷺ example. So salam is not only for grown-ups, and the Prophet ﷺ is our role model in this. If you are the oldest in a group of younger children, do not hesitate to start by greeting them.
- [ ] ok

## table-manners: Table Manners / آداب الطعام

File: `drafts/hadith/items-table-manners.json`

<a id="bra8od5d"></a>
### M2020 · Sahih Muslim 2020 · caution

- Values: table-manners
- dorar: https://dorar.net/h/BRA8OD5D · narrator: عبدالله بن عمر · grade: صحيح (مسلم)
- First 10 words: «إذا أكَلَ أحَدُكُم فليَأكُلْ بيَمينِه، وإذا شَرِبَ فليَشرَبْ بيَمينِه؛ فإنَّ …»
- Agent's reading: When one of you eats or drinks he should use his right hand, because the Shaytan eats and drinks with his left.
- 6-9 AR: هذا الحديث يعلمنا أن نأكل ونشرب باليد اليمنى. هذا أدب جميل نتبع فيه الطريق الحسن، مثلا نمسك الكوب بيدنا اليمنى عند الشرب.
- 6-9 EN: This hadith teaches us to eat and drink with the right hand. It is a lovely manner that follows the good way, for example holding our cup in the right hand when we drink.
- 10-13 AR: يعلمنا هذا الحديث أن نأكل ونشرب باليد اليمنى، ويذكر أن الشيطان يأكل ويشرب بشماله، فنحب أن نتبع الطريق الحسن. نحاول أن نتذكر هذا الأدب في كل وجبة. وإذا كان الطفل يجد صعوبة في ذلك لأي سبب، فيمكنه أن يسأل والديه أو معلما موثوقا.
- 10-13 EN: This hadith teaches us to eat and drink with the right hand, and it mentions that the Shaytan eats and drinks with the left, so we choose the good way. We try to remember this manner at every meal. If a child finds it difficult for any reason, they can ask their parents or a trusted teacher.
- ⚠️ Flag **sensitive_aqidah**: Mentions the Shaytan eating with his left hand. Gentle in the older text only; the younger text does not name him.
- ⚠️ Flag **fiqh_ruling**: Scholars differ on whether this is recommended or obligatory, and left-handed children may feel bad. I gave no ruling and added a line telling the older child to ask a parent or teacher; the lead may want a note on left-handed children.
- [ ] ok

<a id="rrj6d4b6"></a>
### B5376 · Sahih al-Bukhari 5376 · ok

- Values: table-manners
- dorar: https://dorar.net/h/Rrj6d4b6 · narrator: عمر بن أبي سلمة · grade: صحيح (البخاري)
- First 10 words: «كُنتُ غُلامًا في حَجرِ رَسولِ اللهِ صلَّى اللهُ عليه وسلَّم، …»
- Agent's reading: A boy raised by the Prophet whose hand wandered around the dish was taught to say Allah's name, eat with his right hand and eat from what is near him, and it became his habit.
- 6-9 AR: كان عمر بن أبي سلمة طفلا صغيرا عند النبي ﷺ، وكانت يده تتحرك في كل مكان من الصحن. فعلمه النبي ﷺ أن يقول بسم الله، ويأكل باليمين، ويأكل مما أمامه، فصار هذا أدبه دائما.
- 6-9 EN: Umar ibn Abi Salama was a little boy living with the Prophet ﷺ, and his hand used to move all over the dish. The Prophet ﷺ taught him to say bismillah, eat with his right hand and eat from what is near him, and from then on that became his habit.
- 10-13 AR: يحكي عمر بن أبي سلمة أنه كان طفلا عند النبي ﷺ وكانت يده تتحرك في الصحن، فعلمه النبي ﷺ ثلاثة آداب: أن يذكر اسم الله، وأن يأكل بيمينه، وأن يأكل مما يليه. وبقيت هذه عادته بعد ذلك. نتعلم من القصة أن النصيحة اللطيفة تغير سلوكنا، وأن الأدب يتعلم بالتدريب، فنحاول أن نتذكر الآداب الثلاثة في كل وجبة.
- 10-13 EN: Umar ibn Abi Salama tells how, as a boy with the Prophet ﷺ, his hand used to move around the dish, and the Prophet ﷺ taught him three manners: to mention Allah's name, to eat with his right hand, and to eat from what is in front of him. These stayed his habit afterwards. The story shows that kind advice can change our behaviour and that manners are learned by practice, so we try to remember all three at every meal.
- [ ] ok

## trust-in-allah: Trusting in Allah / التوكل على الله

File: `drafts/hadith/items-trust-in-allah.json`

<a id="gdqbrhef"></a>
### B6313 · Sahih al-Bukhari 6313 · caution

- Values: trust-in-allah
- dorar: https://dorar.net/h/GDqbrHEF · narrator: البراء بن عازب · grade: صحيح (البخاري)
- First 10 words: «أنَّ النَّبيَّ صلَّى اللهُ عليه وسلَّم أوصى رَجُلًا، فقال: إذا …»
- Agent's reading: The Prophet taught a man a bedtime dua of handing oneself and one's affairs to Allah and believing in His book and prophet, and said that if he dies that night he dies on the fitra.
- 6-9 AR: هذا الحديث يعلمنا دعاء جميلا نقوله عند النوم، نسلم فيه أمرنا لله ونثق به ونؤمن بكتابه ونبيه. فننام مطمئنين لأن الله يرعانا.
- 6-9 EN: This hadith teaches us a lovely dua to say at bedtime, in which we hand our affairs over to Allah, trust Him, and believe in His book and His Prophet. So we sleep peacefully because Allah looks after us.
- 10-13 AR: علم النبي ﷺ رجلا دعاء يقوله عند الاضطجاع على فراشه، نعلن فيه أننا نسلم أنفسنا وأمورنا لله ونلجأ إليه وحده، ونؤمن بكتابه ونبيه. هذا الدعاء يعلمنا أن نختم يومنا بالثقة بالله والطمأنينة. نستطيع أن نحفظه بمساعدة أهلنا ونقوله كل ليلة.
- 10-13 EN: The Prophet ﷺ taught a man a dua to say when lying down in bed, in which we declare that we hand ourselves and our affairs to Allah, turn only to Him, and believe in His book and His Prophet. It teaches us to end our day with trust in Allah and calm. We can learn it with help from our family and say it every night.
- ⚠️ Flag **death**: The hadith ends with the promise about dying that night on the fitra. I left this out of both texts to avoid worrying children at bedtime and focused on trust and calm. If the card shows the full Arabic, a parent may want to be ready to answer questions.
- [ ] ok

<a id="hkzhkjjw"></a>
### B3653 · Sahih al-Bukhari 3653 · ok

- Values: trust-in-allah
- dorar: https://dorar.net/h/HkzhkjjW · narrator: أبو بكر الصديق · grade: صحيح (البخاري)
- First 10 words: «قُلتُ للنَّبيِّ صلَّى اللهُ عليه وسلَّم وأنا في الغارِ: لو …»
- Agent's reading: Abu Bakr, in the cave, feared that someone looking down would see them, and the Prophet reassured him that Allah was the third with the two of them.
- 6-9 AR: كان النبي ﷺ وأبو بكر مختبئين في غار، وخاف أبو بكر أن يراهما أحد. فطمأنه النبي ﷺ بأن الله معهما. فنحن حين نخاف نتذكر أن الله معنا.
- 6-9 EN: The Prophet ﷺ and Abu Bakr were hiding in a cave, and Abu Bakr was afraid someone would see them. The Prophet ﷺ calmed him by reminding him that Allah was with them. So when we feel scared, we remember that Allah is with us.
- 10-13 AR: يحكي أبو بكر الصديق أنه كان مع النبي ﷺ في الغار، وخشي أن ينظر أحد من الذين يبحثون عنهما تحت قدميه فيراهما. فطمأنه النبي ﷺ بأن الله معهما وأنه لا داعي للخوف. هذا الحديث يعلمنا أن نثق بالله في الأوقات الصعبة، ونتذكر أنه معنا حين نشعر بالقلق أو الخوف.
- 10-13 EN: Abu Bakr as-Siddiq tells how he was with the Prophet ﷺ in the cave and feared that one of those searching for them might look down and see them. The Prophet ﷺ reassured him that Allah was with the two of them, so there was no need to fear. This hadith teaches us to trust Allah in hard times and to remember that He is with us when we feel worried or scared.
- ⚠️ Flag **fear**: The context is the Prophet and Abu Bakr hiding from pursuers. I kept the focus on Allah's reassurance and did not describe the enemy. I wrote 'those searching' for the older text; the hadith itself implies this but does not name them.
- [ ] ok

<a id="ffxwurix"></a>
### B6472 · Sahih al-Bukhari 6472 · suggest_exclude

- Values: trust-in-allah
- dorar: https://dorar.net/h/ffXwurIx · narrator: عبدالله بن عباس · grade: صحيح (البخاري)
- First 10 words: «يَدخُلُ الجَنَّةَ مِن أُمَّتي سَبعونَ ألفًا بغيرِ حِسابٍ، هُمُ الذينَ …»
- Agent's reading: Seventy thousand of the Prophet's community enter Paradise without reckoning: those who do not seek ruqya, do not take bad omens, and rely on their Lord.
- 6-9 AR: هذا الحديث يخبرنا أن الذين يتوكلون على الله حقا ينالون كرما عظيما منه. فنحن نعمل ما نستطيع ونثق أن الله يدبر أمورنا، ولا نظن أن شيئا يجلب لنا الحظ السيئ.
- 6-9 EN: This hadith tells us that people who truly rely on Allah receive great generosity from Him. So we do what we can, trust that Allah arranges things, and do not believe that anything brings us bad luck.
- 10-13 AR: يبين هذا الحديث أن سبعين ألفا من هذه الأمة يدخلون الجنة بلا حساب، وهم الذين يتوكلون على ربهم ولا يتشاءمون من الطيور أو العلامات. فالتوكل أن نعمل بالأسباب ونترك النتيجة لله، ونطمئن أن الله هو من يدبر أمورنا لا العلامات ولا الحظ. وهذا لا يمنع أن نسأل أهلنا ونستشير الكبار ونطلب العلاج عند الحاجة.
- 10-13 EN: This hadith shows that seventy thousand from this community will enter Paradise without reckoning, and they are those who rely on their Lord and do not take bad omens from birds or signs. Trust in Allah means taking the steps we can and leaving the result to Him, knowing that it is Allah who arranges things, not signs or luck. It does not stop us from asking our family, consulting adults and seeking treatment when needed.
- ⚠️ Flag **sensitive_aqidah**: Mentions not believing in bad omens (tatayyur) and not seeking ruqya. Both are nuanced; I explained omens only as 'bad luck signs' and did not discuss ruqya at all, because children could wrongly conclude that seeking treatment or recitation for healing is bad.
- ⚠️ Flag **paradise_exclusion**: The 'seventy thousand without reckoning' wording can leave a child feeling they are not among them. I kept it positive in the older text and softened it to 'great generosity' for ages 6-9.
- ⚠️ Flag **fiqh_ruling**: The ruqya clause is debated by scholars, so I avoided giving any view. The older text adds that trusting Allah does not forbid seeking treatment or advice, which is not in the hadith text; it is a safety note and the lead should confirm or remove it.
- ⚠️ Flag **hard_to_explain**: Hard to explain without a scholar's commentary on ruqya and omens. Fallback if kept: show with caution.
- [ ] ok

## trustworthiness: Trustworthiness / الأمانة

File: `drafts/hadith/items-trustworthiness.json`

<a id="0hjbfzka"></a>
### B1438 · Sahih al-Bukhari 1438 · ok

- Values: trustworthiness
- dorar: https://dorar.net/h/0hJBFzKa · narrator: أبو موسى الأشعري · grade: صحيح (البخاري)
- First 10 words: «الخازِنُ المُسلِمُ الأمينُ الذي يُنفِذُ -ورُبَّما قال: يُعطي- ما أُمِرَ …»
- Agent's reading: The trustworthy Muslim treasurer who carries out what he was ordered, fully and willingly, and hands it to whom it was meant for, is one of the two charity-givers.
- 6-9 AR: هذا الحديث يعلمنا أن الأمين الذي يوصل ما طلب منه إيصاله كاملا وبقلب سعيد ينال مثل أجر المتصدق. مثلا، تعطيك أمك مالا لجارنا المحتاج فتوصله كله.
- 6-9 EN: This hadith teaches that a trustworthy person who delivers what they were asked to deliver, completely and with a happy heart, earns a reward like the one who gave the charity. For example, Mom gives you money for a neighbour in need and you deliver all of it.
- 10-13 AR: يبين هذا الحديث قيمة الأمانة: الأمين الذي ينفذ ما طلب منه ويوصله كاملا وبنفس طيبة إلى من أمر له به، يشارك المتصدق في الأجر. فالأمانة ليست فقط ألا نأخذ ما ليس لنا، بل أن نؤدي ما كلفنا به كاملا وبرضا. نستطيع أن نتدرب على ذلك في الأمور الصغيرة، فنوصل رسالة أو مالا أو شيئا استعرناه كما هو.
- 10-13 EN: This hadith shows the value of trustworthiness: a trustworthy person who carries out what they were asked to do and hands it over completely and willingly to the one it was meant for shares in the reward of the one who gave charity. Trustworthiness is not only about not taking what is not ours, but also about doing what we were trusted with fully and gladly. We can practise with small things, like passing on a message, money or something we borrowed exactly as it was.
- [ ] ok

## visiting-the-sick: Visiting the Sick / عيادة المريض

File: `drafts/hadith/items-visiting-the-sick.json`

<a id="hgjrlbz0"></a>
### M2568 · Sahih Muslim 2568 · ok

- Values: visiting-the-sick
- dorar: https://dorar.net/h/HGJRlBZ0 · narrator: ثوبان مولى رسول الله صلى الله عليه وسلم · grade: صحيح (مسلم)
- First 10 words: «إنَّ المُسلِمَ إذا عادَ أخاه المُسلِمَ لَم يَزَلْ في خُرفةِ …»
- Agent's reading: A Muslim who visits his sick Muslim brother remains in the khurfa (gathered fruit/garden) of Paradise until he returns.
- 6-9 AR: هذا الحديث يعلمنا أن زيارة المريض فيها خير كبير. فمن يزور أخاه المسلم المريض يكون له عند الله ثواب عظيم في الجنة حتى يعود إلى بيته. مثلا، نزور صديقنا المريض ونسأل عن صحته.
- 6-9 EN: This hadith teaches that visiting someone who is sick brings great goodness. Someone who visits their Muslim brother who is sick has a great reward from Allah in Paradise until they go back home. For example, we visit a sick friend and ask how they are feeling.
- 10-13 AR: يبين هذا الحديث فضل عيادة المريض: من زار أخاه المسلم المريض كان له من الله ثواب عظيم في الجنة طوال مدة زيارته حتى يرجع. فزيارتنا تفرح المريض وتخفف عنه، والله يكرمنا عليها. نستطيع أن نزور المريض زيارة قصيرة لطيفة، ونسأل عن حاله وندعو له بالشفاء.
- 10-13 EN: This hadith shows the virtue of visiting the sick: someone who visits their Muslim brother who is sick has a great reward from Allah in Paradise for as long as the visit lasts, until they return. Our visit cheers up the sick person and eases their day, and Allah honours us for it. We can make a short, kind visit, ask how they are and make dua for their recovery.
- ⚠️ Flag **hard_to_explain**: The Arabic word khurfat al-janna is an unusual term; I used the common explanation that it means the gathered fruits or gardens of Paradise, expressed as 'great reward in Paradise'. The lead should check the dorar commentary and confirm this is what the page says.
- [ ] ok

<a id="kan2aebp"></a>
### B1240 · Sahih al-Bukhari 1240 · ok

- Values: visiting-the-sick
- dorar: https://dorar.net/h/Kan2aebp · narrator: أبو هريرة · grade: صحيح (البخاري)
- First 10 words: «حَقُّ المُسلِمِ على المُسلِمِ خَمسٌ: رَدُّ السَّلامِ، وعيادةُ المَريضِ، واتِّباعُ …»
- Agent's reading: A Muslim has five rights over another Muslim: returning salam, visiting the sick, following funerals, accepting an invitation and saying a blessing for a sneezer.
- 6-9 AR: يعلمنا هذا الحديث خمسة أمور من حق المسلم على أخيه المسلم، منها رد السلام وزيارة المريض وإجابة الدعوة والدعاء للعاطس. مثلا، نزور صديقنا المريض ونسأل عن صحته.
- 6-9 EN: This hadith teaches five things a Muslim owes to another Muslim, including replying to salam, visiting the sick, accepting an invitation and making dua for someone who sneezes. For example, we visit a sick friend and ask how they are feeling.
- 10-13 AR: يعلمنا هذا الحديث خمسة حقوق للمسلم على المسلم: رد السلام، وعيادة المريض، وحضور الجنازة مع المسلمين، وإجابة الدعوة، والدعاء للعاطس. وهي تبين كيف تقوى الأخوة بيننا بأعمال بسيطة. من أسهلها أن نزور المريض أو نتصل به ونسأل عنه وندعو له بالشفاء.
- 10-13 EN: This hadith teaches five rights a Muslim has over another Muslim: replying to salam, visiting the sick, joining a funeral with the Muslims, accepting an invitation, and making dua for someone who sneezes. It shows how brotherhood grows through simple acts. One of the easiest is to visit or call someone who is ill, ask about them and pray for their recovery.
- ⚠️ Flag **death**: One of the five items is following funerals. I omitted it for ages 6-9 and mentioned it briefly and neutrally for the older group; the lead may want to keep it out of both.
- ⚠️ Flag **fiqh_ruling**: The word 'right' (haqq) is explained by scholars as a recommended or communal duty, which varies by item. I gave no ruling and kept the focus on kindness.
- [ ] ok
