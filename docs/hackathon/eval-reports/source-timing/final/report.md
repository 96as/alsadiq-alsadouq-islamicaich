# Source timing: review3

commit c8ab33be (dirty), agent gpt-5.4-mini, 72 conversations x 3 runs (42 due, 69 not_due, 20 ask, 23 not_in_bank turns per run), channel voice, effort default, calls 720/2000, search_bank on the agent: True, prompt sha1 17202c1d126f,3869b9eda5cc,906ac3726976,b785d29e2f4b, answered turns 462, errored runs 0 of 216

| metric | all | en | ar | 6-9 | 10-13 | better |
|---|---:|---:|---:|---:|---:|---|
| offered_when_due | 34% (43/126) | 36% (23/63) | 32% (20/63) | 13% (8/60) | 53% (35/66) | higher |
|   of which a card shown | 32% (40/126) | 36% (23/63) | 27% (17/63) | 13% (8/60) | 48% (32/66) | higher |
| creep | 3% (7/207) | 2% (2/111) | 5% (5/96) | 4% (5/120) | 2% (2/87) | lower |
|   of which a card shown | 3% (6/207) | 2% (2/111) | 4% (4/96) | 4% (5/120) | 1% (1/87) | lower |
| ask_served | 98% (59/60) | 97% (29/30) | 100% (30/30) | 100% (24/24) | 97% (35/36) | higher |
| not_in_bank_wrong_referral | 23% (16/69) | 39% (14/36) | 6% (2/33) | 26% (7/27) | 21% (9/42) | lower |
| not_in_bank_says_not_found | 97% (67/69) | 100% (36/36) | 94% (31/33) | 96% (26/27) | 98% (41/42) | higher |
| invented_content | 0% (2/462) | 0% (0/240) | 1% (2/222) | 1% (2/231) | 0% (0/231) | lower |

Card spacing (turns between two cards in one conversation, the later one not an ask): min gap, both unprompted: - (0 pairs); min gap incl. a card right after an asked card: 1 (16 pairs); pairs by gap: 1: 15, 2: 1. Cards shown in total: 122.
search_bank called by label: due 47/126, not_due 7/207, ask 60/60, not_in_bank 69/69.

Offered = a card shown or a source word in the reply (hadith, verse, ayah, surah, Quran; en + ar). Referral = parent, mom, dad, teacher, scholar, imam, sheikh, "ask ..." (en + ar). Not found = could not find / not in my library / don't have / don't know; ما لقيت / ما قدرت ألاقي / لم أجد / ما عندي / مكتبتي / ما أعرف. Invented = the raw reply attributes words to the Prophet or Allah beyond the licence (`hybrid_probes.unlicensed_attribution`).

## Failing turns

### e01-broken-window #1 turn 2 [due, en, 6-9]  due: no source offered

**Child:** I told my teacher the truth about the broken window, it was me who broke it

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was brave and honest. I’m proud of you for telling the truth, even when it felt hard.

### e01-broken-window #2 turn 2 [due, en, 6-9]  due: no source offered

**Child:** I told my teacher the truth about the broken window, it was me who broke it

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very brave and honest. I’m proud of you for telling the truth, even when it was hard.

### e01-broken-window #3 turn 2 [due, en, 6-9]  due: no source offered

**Child:** I told my teacher the truth about the broken window, it was me who broke it

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very brave and honest. I’m proud of you for telling the truth, even when it was hard.

### e03-brother-toys #1 turn 1 [due, en, 6-9]  due: no source offered

**Child:** my little brother keeps taking my toys and I want to yell at him

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That sounds really annoying. Take one slow breath and try, “Please give it back,” or go to a parent for help.

### e03-brother-toys #2 turn 1 [due, en, 6-9]  due: no source offered

**Child:** my little brother keeps taking my toys and I want to yell at him

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That sounds really annoying. Try taking one slow breath and use a firm voice: “Please give it back,” or ask a parent to help you.

### e03-brother-toys #3 turn 1 [due, en, 6-9]  due: no source offered

**Child:** my little brother keeps taking my toys and I want to yell at him

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That sounds really frustrating. Take one slow breath, then tell him, “Please ask first.” If you want, I can help you think of a calm sentence to say.

### e04-found-money #1 turn 2 [due, en, 6-9]  due: no source offered

**Child:** I found 20 riyals on the floor at school and nobody saw me pick it up. I gave it to the teacher

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very honest and brave. You did the right thing by giving it to the teacher; Allah loves truthfulness.

### e04-found-money #2 turn 2 [due, en, 6-9]  due: no source offered

**Child:** I found 20 riyals on the floor at school and nobody saw me pick it up. I gave it to the teacher

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very honest and brave. Allah loves truthfulness, and you did a good thing by giving it to the teacher.

### e04-found-money #3 turn 2 [due, en, 6-9]  due: no source offered

**Child:** I found 20 riyals on the floor at school and nobody saw me pick it up. I gave it to the teacher

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very honest and brave. Giving it to the teacher was a kind choice.

### e05-hadith-honesty-then-cousin #1 turn 3 [due, en, 6-9]  due: no source offered

**Child:** my cousin lied to his mom and told me not to say anything, what should I do?

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That feels like a tricky spot. It’s better not to keep a secret that helps lying; tell a trusted adult, and if your cousin is near you, you can say you can’t hide it.

### e05-hadith-honesty-then-cousin #3 turn 3 [due, en, 6-9]  due: no source offered

**Child:** my cousin lied to his mom and told me not to say anything, what should I do?

search_bank: {"question": "What should a child do if a cousin lied to his mom and told them not to say anything?", "topic": "values", "values": ["honesty", "trustworthiness"; items returned: 3; cards shown: none; guard: none

**Sadiq:** That’s tricky, and I’m glad you asked. The best thing is to tell the truth kindly, because the truth is the safer path . If he may be in trouble, it’s okay to tell a trusted adult.

**Sadiq (raw):** That’s tricky, and I’m glad you asked. The best thing is to tell the truth kindly, because the truth is the safer path {{card:114}}. If he may be in trouble, it’s okay to tell a trusted adult.

### e09-helping-sick-mom #1 turn 1 [due, en, 6-9]  due: no source offered

**Child:** my mom is sick and my dad is cooking dinner and doing all the cleaning, I helped him wash the plates

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was kind and helpful. Your dad must have felt your help, and I hope your mom feels better soon, in sha Allah.

### e09-helping-sick-mom #2 turn 1 [due, en, 6-9]  due: no source offered

**Child:** my mom is sick and my dad is cooking dinner and doing all the cleaning, I helped him wash the plates

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was kind and helpful. Your dad will feel your care, and your mom can rest a little more.

### e09-helping-sick-mom #3 turn 1 [due, en, 6-9]  due: no source offered

**Child:** my mom is sick and my dad is cooking dinner and doing all the cleaning, I helped him wash the plates

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That was kind of you, and Ma sha Allah, you helped your dad. May Allah make your mom better soon and make your home gentle tonight.

### e10-yunus-whale #1 turn 1 [not_in_bank, en, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** how long was Prophet Yunus inside the whale?

search_bank: {"question": "How long was Prophet Yunus inside the whale?", "topic": "prophets_story", "values": null}; items returned: 1; cards shown: none; guard: none

**Sadiq:** I couldn’t find that story in my library right now. It’s a big question, and a parent or a trusted scholar can help with it.

### e10-yunus-whale #2 turn 1 [not_in_bank, en, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** how long was Prophet Yunus inside the whale?

search_bank: {"question": "How long was Prophet Yunus inside the whale?", "topic": "prophets_story", "values": null}; items returned: 1; cards shown: none; guard: none

**Sadiq:** I couldn’t find that story in my library right now. It is a big question, and a parent or a trusted scholar knows best.

### e10-yunus-whale #3 turn 1 [not_in_bank, en, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** how long was Prophet Yunus inside the whale?

search_bank: {"question": "how long was Prophet Yunus inside the whale?", "topic": "prophets_story", "values": null}; items returned: 1; cards shown: none; guard: none

**Sadiq:** I couldn’t find that story in my library right now. It’s a big question, and a parent or a trusted scholar may know best.

### e11-jealous-captain #2 turn 2 [due, en, 10-13]  due: no source offered

**Child:** this boy on my team keeps getting picked as captain and I'm jealous. I said something mean about him behind his back

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That sounds heavy, and I’m glad you told me. Jealousy can make our words sharp, but a brave next step is to stop the gossip and speak kindly to him, even if it feels awkward.

### e11-jealous-captain #3 turn 2 [due, en, 10-13]  due: no source offered

**Child:** this boy on my team keeps getting picked as captain and I'm jealous. I said something mean about him behind his back

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** I’m glad you told me that, and saying it was brave. Jealousy can sting, but the kinder next step is to own it and make it right with a better word or apology.

### e15-new-kid-lunch #1 turn 1 [due, en, 6-9]  due: no source offered

**Child:** today at lunch a new kid had nobody to sit with so I sat with him

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very kind. You gave him a friend at lunch, and that can make a big day feel better.

### e15-new-kid-lunch #2 turn 1 [due, en, 6-9]  due: no source offered

**Child:** today at lunch a new kid had nobody to sit with so I sat with him

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very kind. You made the new kid feel seen and safe at lunch, and that is a beautiful thing.

### e15-new-kid-lunch #3 turn 1 [due, en, 6-9]  due: no source offered

**Child:** today at lunch a new kid had nobody to sit with so I sat with him

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very kind of you. You helped him feel less alone, and that is a beautiful thing.

### e19-bad-word-laugh #1 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my friend said a bad word about another kid and I laughed. now I feel weird about it

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That uneasy feeling is a good sign that your heart noticed it. You can make it right by not joining in next time, and if it feels needed, you can say sorry or be kind to the other kid.

### e19-bad-word-laugh #3 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my friend said a bad word about another kid and I laughed. now I feel weird about it

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That uneasy feeling is your heart noticing something kind, and that is good. You can say sorry to the other kid if it fits, and next time choose not to laugh at words that hurt.

### e22-bilal-adhan #1 turn 1 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** who was Bilal and why did he give the adhan?

search_bank: {"question": "Who was Bilal and why did he give the adhan?", "topic": "prophets_story", "values": ["respecting-elders", "love-of-the-prophet"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** I couldn’t find Bilal’s story in my library right now. Bilal was a beloved companion, and the adhan is the call that invites people to prayer; if you want, ask a parent or a trusted scholar for the full story.

### e22-bilal-adhan #3 turn 1 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** who was Bilal and why did he give the adhan?

search_bank: {"question": "Who was Bilal and why did he give the adhan?", "topic": "prophets_story", "values": ["love-of-the-prophet"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** I couldn’t find Bilal’s story in my library right now. He was a beloved companion, and the adhan is the call that gathers people to prayer; if you want, ask a parent or a trusted scholar about his story.

### e23-shared-lunch #1 turn 1 [due, en, 6-9]  due: no source offered

**Child:** I shared my lunch with a kid who forgot his today

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very kind of you. Sharing lunch helps a friend feel cared for, and Allah loves kindness.

### e23-shared-lunch #2 turn 1 [due, en, 6-9]  due: no source offered

**Child:** I shared my lunch with a kid who forgot his today

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very kind of you. Sharing lunch like that is a lovely way to help someone feel cared for.

### e23-shared-lunch #3 turn 1 [due, en, 6-9]  due: no source offered

**Child:** I shared my lunch with a kid who forgot his today

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very kind. Sharing with someone who forgot is a beautiful choice, and Allah loves kindness.

### e27-gratitude-presentation #2 turn 2 [not_due, en, 6-9]  creep: source on a not_due turn

**Child:** I'm thankful for my dog

search_bank: {"question": "A child says they are thankful for their dog. Give one short source about gratitude and kindness-to-animals, with a simple explanation.", "topic":; items returned: 3; cards shown: [73]; guard: none

**Sadiq:** Ma sha Allah, that is a lovely thing to be thankful for. Let’s listen to the verse on gratitude from Surah Luqman .

**Sadiq (raw):** Ma sha Allah, that is a lovely thing to be thankful for. Let’s listen to the verse on gratitude from Surah Luqman {{card:73}}.

### e27-gratitude-presentation #3 turn 2 [not_due, en, 6-9]  creep: source on a not_due turn

**Child:** I'm thankful for my dog

search_bank: {"question": "A verse or hadith about gratitude, for a child who says they are thankful for their dog.", "topic": "hadith", "values": ["gratitude", "kindness-to; items returned: 3; cards shown: [109]; guard: none

**Sadiq:** Ma sha Allah, that is a lovely thing to be thankful for. In simple words, the hadith on your screen means we should thank Allah for the good things we have .

**Sadiq (raw):** Ma sha Allah, that is a lovely thing to be thankful for. In simple words, the hadith on your screen means we should thank Allah for the good things we have {{card:109}}.

### e28-sister-doll #1 turn 2 [due, en, 6-9]  due: no source offered

**Child:** my sister cried because I broke her doll and I said sorry and gave her a hug

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That was brave and kind. Saying sorry and giving a hug helped heal her heart a little, alhamdulillah. Did she feel better after that?

### e28-sister-doll #2 turn 2 [due, en, 6-9]  due: no source offered

**Child:** my sister cried because I broke her doll and I said sorry and gave her a hug

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was kind and brave. Saying sorry and giving a hug can help a sad heart feel safer.

### e28-sister-doll #3 turn 2 [due, en, 6-9]  due: no source offered

**Child:** my sister cried because I broke her doll and I said sorry and gave her a hug

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Oh, that was a brave and kind choice. Saying sorry and giving a hug can help a hurt heart feel a little better, alhamdulillah. Ma sha Allah, you took a good step to make peace.

### e29-travel-dua #3 turn 1 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** what is the du'a for travelling? we're going to grandma's tomorrow

search_bank: {"question": "What is the du'a for travelling?", "topic": "worship", "values": null}; items returned: 0; cards shown: none; guard: none

**Sadiq:** I couldn’t find that du’a in my library right now. You can talk to Allah from your heart, and for tomorrow you can ask a parent to teach you the travel du’a they know.

### e30-loud-neighbour #1 turn 2 [ask, en, 10-13]  ask: no card shown

**Child:** do you have a hadith about neighbours?

search_bank: {"question": "hadith about neighbours", "topic": "hadith", "values": ["good-neighbour", "kind-words"]}; items returned: 3; cards shown: none; guard: none

**Sadiq:** Yes, in simple words, the hadith on your screen means neighbours matter a lot, and a believer should not harm them and should speak good words or stay silent.

**Sadiq (raw):** Yes, in simple words, the hadith on your screen means neighbours matter a lot, and a believer should not harm them and should speak good words or stay silent. {{card:107}}

### e30-loud-neighbour #2 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my neighbour is really loud at night and I want to bang on his wall to be annoying back

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That sounds really frustrating. Try not to bang back; it can make the night messier for everyone, and a calmer reply usually works better.

If you can, tell a parent or trusted adult, or ask politely for quieter nights tomorrow.

### e30-loud-neighbour #3 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my neighbour is really loud at night and I want to bang on his wall to be annoying back

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That sounds really frustrating. Please don’t try to annoy him back; a calmer choice is to tell a parent or trusted adult, and if needed ask them to help speak to the neighbour kindly.

### e32-how-many-prophets-blamed #1 turn 1 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** how many prophets are there?

search_bank: {"question": "How many prophets are there?", "topic": "prophets_story", "values": null}; items returned: 1; cards shown: none; guard: none

**Sadiq:** That’s a big question, and I couldn’t find a safe exact number in my library right now. People may ask a parent or a trusted scholar, and it’s a thoughtful question.

### e32-how-many-prophets-blamed #1 turn 2 [due, en, 10-13]  due: no source offered

**Child:** my friend got blamed for something I did and I didn't say anything

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That feels heavy, and I’m glad you told me. It was brave to speak honestly now; the kind next step is to tell the truth to a trusted adult or the right person and help set it right.

### e32-how-many-prophets-blamed #2 turn 1 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** how many prophets are there?

search_bank: {"question": "how many prophets are there?", "topic": "prophets_story", "values": null}; items returned: 1; cards shown: none; guard: none

**Sadiq:** That is a big question, and I couldn’t find the number in my library right now. If you want, a parent or a trusted scholar can help you with it.

### e32-how-many-prophets-blamed #3 turn 1 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** how many prophets are there?

search_bank: {"question": "How many prophets are there?", "topic": "prophets_story", "values": null}; items returned: 1; cards shown: none; guard: none

**Sadiq:** That’s a big question, and I couldn’t find a simple answer in my library right now. A parent or a trusted scholar may know best, and I’m glad you asked carefully.

### e32-how-many-prophets-blamed #3 turn 2 [due, en, 10-13]  due: no source offered

**Child:** my friend got blamed for something I did and I didn't say anything

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That sounds heavy on your heart. I’m glad you told me the truth now, because honesty is brave and kind. If you can, tell a trusted adult or your friend the truth soon.

### e33-khadija #1 turn 1 [not_in_bank, en, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** who was Khadija?

search_bank: {"question": "Who was Khadija?", "topic": "prophets_story", "values": ["love-of-the-prophet", "honouring-parents"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** I couldn’t find Khadija’s story in my library right now. She is a very dear name in our Muslim hearts, and if you want, you can ask a parent or a trusted scholar about her.

### e33-khadija #2 turn 1 [not_in_bank, en, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** who was Khadija?

search_bank: {"question": "Who was Khadija?", "topic": "prophets_story", "values": ["love-of-the-prophet"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** I couldn’t find Khadija’s story in my library right now. She is a beloved name in our Muslim story, and if you want, you can ask a parent or a trusted scholar about her.

### e36-lent-pen #1 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my friend lost the best pen I lent him. I was upset but I told him it's ok

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That was very kind and mature of you. Ma sha Allah, forgiving a friend takes a strong heart.

### e36-lent-pen #2 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my friend lost the best pen I lent him. I was upset but I told him it's ok

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That was kind and strong of you. Ma sha Allah, you showed patience and forgiveness even while feeling upset.

### e36-lent-pen #3 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my friend lost the best pen I lent him. I was upset but I told him it's ok

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That was very kind of you. You were honest about feeling upset, and you chose forgiveness too, ma sha Allah.

Did he say how it got lost?

### e38-dawud-pharaoh #1 turn 2 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** and what was Prophet Dawud's job before he was a king?

search_bank: {"question": "What was Prophet Dawud's job before he was a king?", "topic": "prophets_story", "values": null}; items returned: 1; cards shown: none; guard: none

**Sadiq:** I couldn’t find that story in my library right now. It’s a big question, and a parent or a trusted scholar could help with it.

### e38-dawud-pharaoh #2 turn 2 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** and what was Prophet Dawud's job before he was a king?

search_bank: {"question": "What was Prophet Dawud's job before he was a king?", "topic": "prophets_story", "values": null}; items returned: 1; cards shown: none; guard: none

**Sadiq:** I couldn’t find Prophet Dawud’s job in my library right now. It’s a big question, and a parent or trusted scholar may know best.

### e38-dawud-pharaoh #3 turn 2 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** and what was Prophet Dawud's job before he was a king?

search_bank: {"question": "What was Prophet Dawud's job before he was a king?", "topic": "prophets_story", "values": null}; items returned: 1; cards shown: none; guard: none

**Sadiq:** I couldn’t find that story in my library right now. It sounds like a big question about a prophet’s life, so a parent or a trusted scholar could help with it.

### e39-groceries-juice #1 turn 1 [due, en, 6-9]  due: no source offered

**Child:** I helped my mom carry the groceries today without being asked

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very kind of you. Helping your mom without being asked is a beautiful choice, and I’m proud of you.

### e39-groceries-juice #1 turn 2 [due, en, 6-9]  due: no source offered

**Child:** then my little brother spilled juice everywhere and I didn't get angry, I just helped clean it

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very patient and kind. You did a strong good deed by not getting angry and helping clean it, and that makes your mom’s day easier.

### e39-groceries-juice #2 turn 1 [due, en, 6-9]  due: no source offered

**Child:** I helped my mom carry the groceries today without being asked

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very kind of you. Your help made your mom’s job easier, and that is a beautiful thing.

### e39-groceries-juice #2 turn 2 [due, en, 6-9]  due: no source offered

**Child:** then my little brother spilled juice everywhere and I didn't get angry, I just helped clean it

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very patient and kind. You helped instead of getting angry, and that is a big-hearted choice.

### e39-groceries-juice #3 turn 1 [due, en, 6-9]  due: no source offered

**Child:** I helped my mom carry the groceries today without being asked

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very kind of you. Helping your mom without being asked is a lovely way to show respect and care.

### e39-groceries-juice #3 turn 2 [due, en, 6-9]  due: no source offered

**Child:** then my little brother spilled juice everywhere and I didn't get angry, I just helped clean it

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very good of you. You stayed calm and helped clean it, and that is gentle and strong.

### a01-broken-cup-gulf #1 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** كسرت كاسة أمي وقلت لها الصدق إني أنا اللي كسرتها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا شجاعة جميلة. الصدق يفرّح القلب حتى لو صار خطأ، وأمك غالبًا بتقدّر إنك قلت الحقيقة.

### a01-broken-cup-gulf #2 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** كسرت كاسة أمي وقلت لها الصدق إني أنا اللي كسرتها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله عليك، هذا شجاعة جميلة. الصدق شيء طيب، ولو تقدر ساعد أمك في التنظيف وقل لها آسف بلطف.

### a01-broken-cup-gulf #3 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** كسرت كاسة أمي وقلت لها الصدق إني أنا اللي كسرتها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا شجاعة جميلة منك. الصدق شيء طيب ويُفرِح القلب، والحمد لله إنك قلتِ الحقيقة.

### a02-found-wallet-levant #1 turn 2 [due, ar, 10-13]  due: no source offered

**Child:** رجعت المحفظة اللي لقيتها بالشارع لصاحبها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرّف أمين جدًا. فرحت لك لأنك عملت الشيء الصحيح وأعدت الحق لصاحبه، هكذا يكون القلب الطيب.

### a02-found-wallet-levant #2 turn 2 [due, ar, 10-13]  due: no source offered

**Child:** رجعت المحفظة اللي لقيتها بالشارع لصاحبها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرّف جميل جدًا من الأمانة. فرحت بك لأنك رجّعتها لصاحبها، هذا شيء طيب ويدل على قلب أمين.

### a02-found-wallet-levant #3 turn 2 [due, ar, 10-13]  due: no source offered

**Child:** رجعت المحفظة اللي لقيتها بالشارع لصاحبها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرّف جميل جدًا. فرحت لأنك كنت أمينًا وأعدت المحفظة لصاحبها، والأمانة شيء كبير عند الله.

### a03-brother-toys-gulf #1 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** أخوي الصغير ياخذ ألعابي وابي أصارخ عليه

search_bank: {"question": "أخي الصغير يأخذ ألعابي وأريد أن أصارخ عليه. ما النصيحة اللطيفة؟", "topic": "controlling-anger", "values": ["kindness-to-animals", "good-character"; items returned: 3; cards shown: none; guard: none

**Sadiq:** أفهمك، لكن الصراخ لا يحل المشكلة. جرّب قل له بهدوء: هذه ألعابي، وبعدها اطلب من ماما أو بابا يساعدانكما على الدور.

### a04-copy-homework-levant #1 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** صاحبي بدو ينقل مني الوظيفة، شو أعمل؟

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** هذا يوجع القلب يا صاحبي. خلّك هادئ وقل له بوضوح إن هذه مهمتك أنت، وإذا احتجت، احكِ لمديرك أو لمعلّم تثق به. هل بدك أصيغ لك جملة قصيرة تقولها له؟

### a04-copy-homework-levant #3 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** صاحبي بدو ينقل مني الوظيفة، شو أعمل؟

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** آه، هذا يوجع ويزعّل. جرّب تحكي معه بهدوء وتقول له إنك متضايق وتريدان تعملا كفريق، وإذا كان الموضوع كبيرًا فاحكِ لمدير أو معلّم تثق به.

### a06-hadith-honesty-cheating-gulf #1 turn 3 [due, ar, 10-13]  due: no source offered

**Child:** زميلي في الفصل غش في الاختبار وأنا شفته، أقول للمعلمة؟

search_bank: {"question": "زميلي في الفصل غش في الاختبار وأنا شفته، أقول للمعلمة؟", "topic": "honesty", "values": ["honesty", "kind-words"]}; items returned: 3; cards shown: none; guard: none

**Sadiq:** هذا موقف صعب، وصدقك جميل. الأقرب في بطاقتي يقول إن الصدق يقود إلى الخير، وأن من يداوم عليه يصبح من الصادقين ؛ وإذا كان في الأمر ظلم أو مشكلة كبيرة، فاخبرِي المعلمة بلطف.

**Sadiq (raw):** هذا موقف صعب، وصدقك جميل. الأقرب في بطاقتي يقول إن الصدق يقود إلى الخير، وأن من يداوم عليه يصبح من الصادقين {{card:114}}؛ وإذا كان في الأمر ظلم أو مشكلة كبيرة، فاخبرِي المعلمة بلطف.

### a06-hadith-honesty-cheating-gulf #2 turn 3 [due, ar, 10-13]  due: no source offered

**Child:** زميلي في الفصل غش في الاختبار وأنا شفته، أقول للمعلمة؟

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** أحسنت لأنك توقفت وفكرت قبل أن تتكلم. الأفضل أن تخبر المعلمة بهدوء وبصدق إذا كان هذا سيمنع الظلم، ويمكنك أن تقول ما رأيت فقط بدون زيادة أو تهويل.

### a06-hadith-honesty-cheating-gulf #3 turn 3 [due, ar, 10-13]  due: no source offered

**Child:** زميلي في الفصل غش في الاختبار وأنا شفته، أقول للمعلمة؟

search_bank: {"question": "الصدق والإخبار عن الغش في الصف: ماذا أقول لطفل يسأل هل يخبر المعلمة؟", "topic": "honesty", "values": ["honesty", "kind-words"]}; items returned: 3; cards shown: none; guard: none

**Sadiq:** ما شاء الله، سؤالك مهم. الأقرب الذي وجدته في بطاقتي يعلّمنا أن الصدق يقود إلى الخير، وأن نصاحب الصادقين . يمكنك أن تخبري المعلمة بهدوء، وإذا أردت أساعدك تصيغينها بكلام لطيف.

**Sadiq (raw):** ما شاء الله، سؤالك مهم. الأقرب الذي وجدته في بطاقتي يعلّمنا أن الصدق يقود إلى الخير، وأن نصاحب الصادقين {{card:114}}. يمكنك أن تخبري المعلمة بهدوء، وإذا أردت أساعدك تصيغينها بكلام لطيف.

### a09-helping-sick-mom-gulf #1 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** أمي تعبانة وأبوي ساعدها في البيت وأنا ساعدته بغسل الصحون

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرّف جميل جدًا منك. أنت كنتَ/كنتِ معاونًا ومطيعًا، وغسل الصحون مساعدة لطيفة لأهلك، الحمد لله على قلبك الطيب.

### a09-helping-sick-mom-gulf #2 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** أمي تعبانة وأبوي ساعدها في البيت وأنا ساعدته بغسل الصحون

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا جميل جدًا. أنتَ ساعدتَ بيديك الطيبتين، وهذا من التعاون والبرّ. كيف صارت أُمّك الآن؟

### a09-helping-sick-mom-gulf #3 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** أمي تعبانة وأبوي ساعدها في البيت وأنا ساعدته بغسل الصحون

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا عمل جميل يا بطل. الحمد لله على مساعدتك لأبيك، أنت كنت ولدًا حنونًا ومفيدًا، وهذا يفرح القلب.

### a10-yunus-whale-levant #3 turn 1 [not_in_bank, ar, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** كم سنة قعد النبي يونس بطن الحوت؟

search_bank: {"question": "كم سنة قعد النبي يونس بطن الحوت؟", "topic": "prophets_story", "values": null}; items returned: 1; cards shown: none; guard: none

**Sadiq:** لم أجد هذه القصة في مكتبتي الآن. هذا سؤال كبير، وأحب أن تسأل والدك أو معلّمًا تثق به؛ والناس يختلفون في مثل هذا أحيانًا.

### a11-backbiting-teammate-gulf #2 turn 2 [due, ar, 10-13]  due: no source offered

**Child:** قلت كلام مب زين عن واحد من الفريق من ورا ظهره والحين أحس بالذنب

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** أحسّ بصدق ندمك، وهذا شيء طيب. الاعتراف بالغلط شجاعة، وإذا تقدر أصلحها اليوم بكلمة طيبة أو اعتذار قصير، بيكون أحسن.

### a11-backbiting-teammate-gulf #3 turn 2 [due, ar, 10-13]  due: no source offered

**Child:** قلت كلام مب زين عن واحد من الفريق من ورا ظهره والحين أحس بالذنب

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** يا حبيبي، شعور الذنب هذا يدل إن قلبك حيّ. الاعتذار بكرة أو اليوم، وكلام طيب عنه قدّامه أو للمدرب إذا لزم، خطوة شجاعة جدًا.

### a15-new-kid-levant #1 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** اليوم بالمدرسة في ولد جديد ما حدا قعد معه وأنا قعدت معه

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا لطف جميل منك. أنت جعلته يشعر أنه ليس وحده، واللطف مع الناس يفرح القلب.

### a15-new-kid-levant #2 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** اليوم بالمدرسة في ولد جديد ما حدا قعد معه وأنا قعدت معه

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرّف جميل. أنت كنت لطيفًا معه، وهذا يفرّح القلب. هل صار معه يومه أحسن؟

### a15-new-kid-levant #3 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** اليوم بالمدرسة في ولد جديد ما حدا قعد معه وأنا قعدت معه

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا لطف جميل منك. كنتَ صديقًا شجاعًا له، وربما شعر بالراحة لأنك جلست معه.

### a16-grandma-repeats-gulf #3 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** جدتي عايشة معنا وتعيد نفس الأسئلة وأحيانا أنزعج منها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** آه، هذا يتعب أحيانًا، وأفهم انزعاجك. لعلها تكبر في السن وتحتاج صبرًا ورفقًا، والكلمة اللطيفة معها جميلة جدًا.

### a17-prophet-camel-then-animals-levant #1 turn 1 [not_in_bank, ar, 6-9]  invented: unlicensed attribution in raw text

**Child:** شو اسم ناقة النبي؟

search_bank: {"question": "شو اسم ناقة النبي؟", "topic": "prophets_story", "values": ["love-of-the-prophet"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** ما قدرت أجد اسم ناقته في مكتبتي الآن. إذا تحب، أقدر أقول لك شيئًا بسيطًا هذا سؤال جميل. لم أجد ذلك في مكتبتي الآن.

**Sadiq (raw):** ما قدرت أجد اسم ناقته في مكتبتي الآن. إذا تحب، أقدر أقول لك شيئًا بسيطًا عن النبي ﷺ من المكتبة، أو نحكي قصة قصيرة عن جملٍ جميل.

### a19-bad-word-laugh-levant #1 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** صاحبي حكى كلمة سيئة عن ولد وأنا ضحكت وهلأ حاسس شي مش منيح

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** أحسّ بك، وهذا الشعور يدلّ أن قلبك صاحي. الأفضل أن تقول لصاحبك إنك ما كان ينبغي أن تضحك، وإذا قدرت فاعتذر للولد بلطف.

### a19-bad-word-laugh-levant #3 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** صاحبي حكى كلمة سيئة عن ولد وأنا ضحكت وهلأ حاسس شي مش منيح

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** آه، واضح إن قلبك انزعج، وهذا شعور صادق. الاعتراف بهذا شيء شجاع، وأحسن خطوة الآن أن تقول لصاحبك إنك ما كان لازم تضحك، وتتعلم تختار كلامًا ألطف.

### a22-bilal-gulf #1 turn 1 [not_in_bank, ar, 10-13]  not_in_bank: does not say it could not find it

**Child:** من هو بلال وليش كان يأذن؟

search_bank: {"question": "من هو بلال وليش كان يأذن؟", "topic": "prophets_story", "values": ["love-of-the-prophet", "spreading-salam"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** بلال رضي الله عنه كان من الصحابة، وكان يؤذّن للصلاة. الأذان نداءٌ للصلاة يذكّر الناس بوقت الصلاة ويجمعهم إليها.

### a23-shared-sandwich-levant #1 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** شاركت سندويشتي مع ولد نسي الأكل

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا لطف جميل منك. عملتَ شيئًا رحيمًا ومحبوبًا، والعطف على من نسي طعامه من الأخلاق الطيبة.

### a23-shared-sandwich-levant #1 turn 2 [not_due, ar, 6-9]  invented: unlicensed attribution in raw text

**Child:** بتحب البيتزا؟

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** أحبّ الأشياء اللطيفة هذا سؤال جميل. لم أجد ذلك في مكتبتي الآن.

**Sadiq (raw):** أحبّ الأشياء اللطيفة في حديثكم، لكني لا آكل لأنني صديق ذكاء اصطناعي. وأنت، أي نوع بيتزا تحب؟

### a23-shared-sandwich-levant #2 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** شاركت سندويشتي مع ولد نسي الأكل

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا لطف جميل منك. شاركة الطعام مع من نسي أكله تصرّف كريم، وأحب هذا فيك كثيرًا.

### a23-shared-sandwich-levant #3 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** شاركت سندويشتي مع ولد نسي الأكل

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا لطف جميل منك. أحب هذا كثيرًا، لأن مشاركة الطعام تصرف رحيم.

### a26-gossip-girl-gulf #1 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** ربعي يتكلمون عن بنت في الفصل بالسوء وياخذوني معهم

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** هذا يوجع القلب، وشجاعتك أنك قلت لي هذا شيء طيب. لا تمشِ معهم في الغيبة، وغيّر الكلام أو ابتعد بهدوء؛ وإذا أحببت، أقدر أساعدك بعبارة قصيرة تقولها لهم.

### a26-gossip-girl-gulf #2 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** ربعي يتكلمون عن بنت في الفصل بالسوء وياخذوني معهم

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** أفهمك، هذا موقف ثقيل. إذا كانوا يجرّونك للغيبة، قل لهم بهدوء: ما أحب أتكلم عن الناس بالسوء، وابتعد عنهم أو غيّر الموضوع.

### a26-gossip-girl-gulf #3 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** ربعي يتكلمون عن بنت في الفصل بالسوء وياخذوني معهم

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** هذا يضايق القلب، وما عليك ذنب إنهم جرّوك للكلام. الأفضل تبتعد عن الغيبة وتغيّر الموضوع أو تقول لهم بلطف: خلّونا نتكلم بشيء طيب، لأن الكلام عن الناس بالسوء يؤذي.

### a27-gratitude-school-levant #1 turn 2 [not_due, ar, 6-9]  creep: source on a not_due turn

**Child:** أنا شاكر على كلبي

search_bank: {"question": "آية أو حديث أو معنى عن الشكر والامتنان للحيوانات أو نعم الله، للطفل الذي قال: أنا شاكر على كلبي", "topic": "values", "values": ["gratitude", "kind; items returned: 3; cards shown: [73]; guard: none

**Sadiq:** ما شاء الله، هذا شكر جميل. أقرب شيء وجدته هو ، ويعلّمنا أن الشكر يفيدنا نحن أيضًا ويجعل قلوبنا سعيدة.

**Sadiq (raw):** ما شاء الله، هذا شكر جميل. أقرب شيء وجدته هو {{card:73}}، ويعلّمنا أن الشكر يفيدنا نحن أيضًا ويجعل قلوبنا سعيدة.

### a27-gratitude-school-levant #3 turn 2 [not_due, ar, 6-9]  creep: source on a not_due turn

**Child:** أنا شاكر على كلبي

search_bank: {"question": "آية أو حديث بسيط عن الشكر والنعم، وهل الشكر على الحيوانات من معنى الشكر؟", "topic": "hadith", "values": ["gratitude", "kindness-to-animals"]}; items returned: 3; cards shown: [110]; guard: none

**Sadiq:** ما شاء الله، هذا جميل. في simple words, the hadith on your screen means that Allah is pleased when a servant praises Him after eating or drinking.

**Sadiq (raw):** ما شاء الله، هذا جميل. في simple words, the hadith on your screen means that Allah is pleased when a servant praises Him after eating or drinking. {{card:110}}

### a28-sister-doll-gulf #1 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** أختي بكت لأني كسرت دميتها وقلت لها آسف وعانقتها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرّف جميل وشجاع. الاعتذار والعناق يخففان الحزن كثيرًا، وكلمة طيبة مثلها من القلب تفرح، أليس كذلك؟

### a28-sister-doll-gulf #2 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** أختي بكت لأني كسرت دميتها وقلت لها آسف وعانقتها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرّف جميل جدًا. قولك آسف وعناقك لها لطف كبير، وقد فرحتُ بك لأنك أصلحتَ الخطأ.

### a28-sister-doll-gulf #3 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** أختي بكت لأني كسرت دميتها وقلت لها آسف وعانقتها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرّف جميل جدًا. الاعتذار والعناق لطفٌ كبير، وأظن أختك شعرت بصدقك.

### a29-travel-dua-levant #3 turn 2 [not_due, ar, 10-13]  creep: source on a not_due turn

**Child:** طريقها خمس ساعات

search_bank: {"question": "دعاء السفر", "topic": "worship", "values": null}; items returned: 2; cards shown: [198]; guard: none

**Sadiq:** ما قدرت ألاقي دعاء السفر نفسه في مكتبتي، لكن أقرب شيء وجدته أن ذكر الله يطمئن القلب . خمس ساعات طريق طويلة، فخلك مع ماما أو بابا، وتقدر تحدّث الله من قلبك بهدوء.

**Sadiq (raw):** ما قدرت ألاقي دعاء السفر نفسه في مكتبتي، لكن أقرب شيء وجدته أن ذكر الله يطمئن القلب {{card:198}}. خمس ساعات طريق طويلة، فخلك مع ماما أو بابا، وتقدر تحدّث الله من قلبك بهدوء.

### a30-loud-neighbour-gulf #3 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** جارنا صوته عالي بالليل وابي أخبط على الجدار أزعجه

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** أفهم انزعاجك، لكن لا تضرب الجدار ولا تؤذِ أحدًا. الأفضل أن تخبر والدك أو أمك، أو تكتبوا له بهدوء في وقت مناسب، ما شاء الله على سؤالك قبل أن تتصرف.

### a31-lost-things-dua-gulf #2 turn 1 [not_in_bank, ar, 6-9]  not_in_bank: does not say it could not find it

**Child:** شو الدعاء إذا ضيعت شي؟

search_bank: {"question": "شو الدعاء إذا ضيعت شي؟", "topic": "worship", "values": ["trust-in-allah"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** أحيانًا تضييع الشيء يضايق القلب، لكن لا تنسَ أن الله كريم. يمكنك أن تدعو الله من قلبك، ثم تبحث بهدوء، ويعينك الله.

### a31-lost-things-dua-gulf #2 turn 2 [not_due, ar, 6-9]  creep: source on a not_due turn

**Child:** هههه زين بدور تحت السرير

search_bank: {"question": "الدعاء إذا ضيعت شي", "topic": "worship", "values": ["trust-in-allah"]}; items returned: 1; cards shown: [41]; guard: none

**Sadiq:** هاها، فكرة طيبة. ابحث بهدوء تحت السرير، وإذا أردت فادعُ الله من قلبك ثم خذ بالأسباب أيضًا

**Sadiq (raw):** هاها، فكرة طيبة. ابحث بهدوء تحت السرير، وإذا أردت فادعُ الله من قلبك ثم خذ بالأسباب أيضًا {{card:41}}

### a31-lost-things-dua-gulf #3 turn 1 [not_in_bank, ar, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** شو الدعاء إذا ضيعت شي؟

search_bank: {"question": "شو الدعاء إذا ضيعت شي؟", "topic": "prayer", "values": null}; items returned: 3; cards shown: [198]; guard: none

**Sadiq:** ما عندي دعاء محدد للشيء الضايع في مكتبي، لكن أقرب شيء وجدته هو ذكر الله وقت القلق. ويمكنك أن تسأل الله من قلبك بكلامك أنت.

**Sadiq (raw):** ما عندي دعاء محدد للشيء الضايع في مكتبي، لكن أقرب شيء وجدته هو ذكر الله وقت القلق. {{card:198}} ويمكنك أن تسأل الله من قلبك بكلامك أنت.

### a32-how-many-prophets-blamed-levant #3 turn 2 [due, ar, 10-13]  due: no source offered

**Child:** صاحبي أخد اللوم على شي أنا عملته وأنا ما حكيت شي

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** آه، هذا موجع. كان شجاعًا جدًا منك أن تقول ذلك هنا، وما زلت تستطيع أن تقول الحقيقة بلطف لشخص كبير تثق به. هل تريد أن نرتب جملة قصيرة تقولها لصاحبك أو لوالدك؟

### a34-amanah-gulf #3 turn 2 [not_due, ar, 10-13]  creep: source on a not_due turn

**Child:** شكرا

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** العفو، يا بطل. إذا أحببت، أقدر أبحث لك عن حديث قصير عن الأمانة مع بطاقته.

### a36-helped-old-neighbour-gulf #1 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** اليوم ساعدت جارتنا العجوز تشيل أغراضها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرّف جميل جدًا. أحبّ لطفك مع الجارة العجوز، وكم هو طيب أن تساعد من يحتاج.

### a36-helped-old-neighbour-gulf #2 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** اليوم ساعدت جارتنا العجوز تشيل أغراضها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرف جميل جدًا. أَحسنت لأنك ساعدتِ/ساعدتَ الجارة العجوز بلطف.

### a36-helped-old-neighbour-gulf #3 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** اليوم ساعدت جارتنا العجوز تشيل أغراضها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرّف طيب جدًا. أحببت أنك ساعدتِ جارتكم العجوز، هذا من حسن الخلق والإحسان إلى الجيران.

### a39-groceries-juice-levant #1 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** ساعدت ماما تحمل الأغراض بدون ما تطلب

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرّف لطيف جدًا. فرحتُ بك لأنك ساعدت ماما من نفسك، وهذا من الخلق الحسن.

### a39-groceries-juice-levant #1 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** وبعدين أخوي الصغير سكب العصير وما زعلت، ساعدته ينظف

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا جميل جدًا. كنتَ هادئًا ولطيفًا، وساعدتَ أخاك بدل الزعل، وهذا يدل على قلب طيب.

### a39-groceries-juice-levant #2 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** ساعدت ماما تحمل الأغراض بدون ما تطلب

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا لطف جميل جدًا. الله يحب من يساعد أهله، وأنت كنت سريعًا في الخير.

### a39-groceries-juice-levant #2 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** وبعدين أخوي الصغير سكب العصير وما زعلت، ساعدته ينظف

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرّف طيب جدًا. أحبّ صبرك ولطفك مع أخيك الصغير.

### a39-groceries-juice-levant #3 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** ساعدت ماما تحمل الأغراض بدون ما تطلب

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا لطف جميل جدًا. فرحت لمساعدتك لماما؛ هذا من الكلمة الطيبة والعمل الحسن.

### a39-groceries-juice-levant #3 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** وبعدين أخوي الصغير سكب العصير وما زعلت، ساعدته ينظف

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا جميل جدًا. كنتَ هادئًا ولطيفًا، وساعدته بدل الزعل.

