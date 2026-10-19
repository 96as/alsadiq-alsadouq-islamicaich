# Source timing: fixes

commit c6653b80, agent gpt-5.4-mini, 72 conversations x 3 runs (42 due, 69 not_due, 20 ask, 23 not_in_bank turns per run), channel voice, effort default, calls 671/2000, search_bank on the agent: True, prompt sha1 1cfb89a3b6c3,5515af502a6b,b99e23bae109,fc10f09f33df, answered turns 462, errored runs 0 of 216

| metric | all | en | ar | 6-9 | 10-13 | better |
|---|---:|---:|---:|---:|---:|---|
| offered_when_due | 10% (12/126) | 8% (5/63) | 11% (7/63) | 2% (1/60) | 17% (11/66) | higher |
|   of which a card shown | 9% (11/126) | 8% (5/63) | 10% (6/63) | 2% (1/60) | 15% (10/66) | higher |
| creep | 0% (0/207) | 0% (0/111) | 0% (0/96) | 0% (0/120) | 0% (0/87) | lower |
|   of which a card shown | 0% (0/207) | 0% (0/111) | 0% (0/96) | 0% (0/120) | 0% (0/87) | lower |
| ask_served | 100% (60/60) | 100% (30/30) | 100% (30/30) | 100% (24/24) | 100% (36/36) | higher |
| not_in_bank_wrong_referral | 51% (35/69) | 61% (22/36) | 39% (13/33) | 52% (14/27) | 50% (21/42) | lower |
| not_in_bank_says_not_found | 77% (53/69) | 86% (31/36) | 67% (22/33) | 93% (25/27) | 67% (28/42) | higher |
| invented_content | 0% (1/462) | 0% (0/240) | 0% (1/222) | 0% (1/231) | 0% (0/231) | lower |

Card spacing (turns between two cards in one conversation, the later one not an ask): min gap, both unprompted: - (0 pairs); min gap incl. a card right after an asked card: 1 (9 pairs); pairs by gap: 1: 8, 2: 1. Cards shown in total: 96.
search_bank called by label: due 18/126, not_due 0/207, ask 60/60, not_in_bank 67/69.

Offered = a card shown or a source word in the reply (hadith, verse, ayah, surah, Quran; en + ar). Referral = parent, mom, dad, teacher, scholar, imam, sheikh, "ask ..." (en + ar). Not found = could not find / not in my library / don't have / don't know; ما لقيت / ما قدرت ألاقي / لم أجد / ما عندي / مكتبتي / ما أعرف. Invented = the raw reply attributes words to the Prophet or Allah beyond the licence (`hybrid_probes.unlicensed_attribution`).

## Failing turns

### e01-broken-window #1 turn 2 [due, en, 6-9]  due: no source offered

**Child:** I told my teacher the truth about the broken window, it was me who broke it

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was brave and truthful. I’m proud of you for telling the truth. What did your teacher say?

### e01-broken-window #2 turn 2 [due, en, 6-9]  due: no source offered

**Child:** I told my teacher the truth about the broken window, it was me who broke it

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very brave. Honesty is a beautiful choice, and I’m proud of you. What happened after you told the truth?

### e01-broken-window #3 turn 2 [due, en, 6-9]  due: no source offered

**Child:** I told my teacher the truth about the broken window, it was me who broke it

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very brave. Telling the truth is a strong and good choice. I’m proud of your honesty.

### e02-copy-homework #1 turn 2 [due, en, 10-13]  due: no source offered

**Child:** my friend wants to copy my homework tomorrow, what should I do?

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That’s a tricky one. It’s kinder to help your friend understand it than to let them copy. You can say, “I can explain it, but I can’t give you my answers.”

### e02-copy-homework #2 turn 2 [due, en, 10-13]  due: no source offered

**Child:** my friend wants to copy my homework tomorrow, what should I do?

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That’s tricky. Be kind, but don’t let them copy; you can say you’ll help them understand it instead.

### e02-copy-homework #3 turn 2 [due, en, 10-13]  due: no source offered

**Child:** my friend wants to copy my homework tomorrow, what should I do?

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That’s a tricky spot, and I’m glad you asked. Don’t let them copy; you can say you’ll help them understand it instead, if you want.

### e03-brother-toys #1 turn 1 [due, en, 6-9]  due: no source offered

**Child:** my little brother keeps taking my toys and I want to yell at him

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That sounds really frustrating. Take one slow breath and use calm words like, “Please give my toy back,” or ask a parent to help.

### e03-brother-toys #2 turn 1 [due, en, 6-9]  due: no source offered

**Child:** my little brother keeps taking my toys and I want to yell at him

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That sounds really annoying. Take one slow breath, and tell him, “Please give it back,” or ask a parent to help.

### e03-brother-toys #3 turn 1 [due, en, 6-9]  due: no source offered

**Child:** my little brother keeps taking my toys and I want to yell at him

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That sounds really annoying. Try a calm voice and say, “Please give it back.” If you want, I can help you think of a kind but firm sentence.

### e04-found-money #1 turn 2 [due, en, 6-9]  due: no source offered

**Child:** I found 20 riyals on the floor at school and nobody saw me pick it up. I gave it to the teacher

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very honest. I’m proud of you for doing the right thing.

### e04-found-money #2 turn 2 [due, en, 6-9]  due: no source offered

**Child:** I found 20 riyals on the floor at school and nobody saw me pick it up. I gave it to the teacher

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very honest and brave. You did the right thing by giving it to the teacher.

### e04-found-money #3 turn 2 [due, en, 6-9]  due: no source offered

**Child:** I found 20 riyals on the floor at school and nobody saw me pick it up. I gave it to the teacher

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very honest and brave. You did the right thing by giving it to the teacher.

### e05-hadith-honesty-then-cousin #2 turn 3 [due, en, 6-9]  due: no source offered

**Child:** my cousin lied to his mom and told me not to say anything, what should I do?

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That sounds tricky. It is better not to help keep a lie hidden. You can tell a trusted adult, and try to be calm and kind when you do.

### e05-hadith-honesty-then-cousin #3 turn 3 [due, en, 6-9]  due: no source offered

**Child:** my cousin lied to his mom and told me not to say anything, what should I do?

search_bank: {"question": "What should a child do if a cousin lies and tells them not to say anything?", "topic": "honesty", "values": ["honesty", "trustworthiness"]}; items returned: 3; cards shown: none; guard: none

**Sadiq:** That sounds hard. Don’t keep a lie secret; tell his mom kindly, or tell a trusted adult. Being truthful is a brave choice, and Allah loves truthfulness .

**Sadiq (raw):** That sounds hard. Don’t keep a lie secret; tell his mom kindly, or tell a trusted adult. Being truthful is a brave choice, and Allah loves truthfulness {{card:114}}.

### e07-verse-parents-dua-exam #1 turn 2 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar; not_in_bank: does not say it could not find it

**Child:** what's the du'a I should say before my exams?

search_bank: {"question": "What du'a should I say before my exams?", "topic": "worship", "values": ["seeking-knowledge", "trust-in-allah"]}; items returned: 3; cards shown: [41]; guard: none

**Sadiq:** You can talk to Allah from your heart before the exam, and a parent can teach you a du'a they know. You can also do your part and trust Allah with the rest .

**Sadiq (raw):** You can talk to Allah from your heart before the exam, and a parent can teach you a du'a they know. You can also do your part and trust Allah with the rest {{card:41}}.

### e07-verse-parents-dua-exam #2 turn 2 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar; not_in_bank: does not say it could not find it

**Child:** what's the du'a I should say before my exams?

search_bank: {"question": "what's the du'a I should say before my exams?", "topic": "worship", "values": ["seeking-knowledge", "trust-in-allah"]}; items returned: 3; cards shown: none; guard: none

**Sadiq:** You can talk to Allah from your heart, and a parent can teach you a du'a. If you want, I can play a short reminder card about trusting Allah with your effort.

### e07-verse-parents-dua-exam #3 turn 2 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar; not_in_bank: does not say it could not find it

**Child:** what's the du'a I should say before my exams?

search_bank: {"question": "What du'a should I say before my exams?", "topic": "worship", "values": ["seeking-knowledge", "trust-in-allah"]}; items returned: 3; cards shown: none; guard: none

**Sadiq:** You can talk to Allah from your heart, and a parent can teach you a du'a to learn by heart.

### e09-helping-sick-mom #1 turn 1 [due, en, 6-9]  due: no source offered

**Child:** my mom is sick and my dad is cooking dinner and doing all the cleaning, I helped him wash the plates

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very kind of you. You helped your dad when your mom was sick, and that is a loving thing to do.

### e09-helping-sick-mom #2 turn 1 [due, en, 6-9]  due: no source offered

**Child:** my mom is sick and my dad is cooking dinner and doing all the cleaning, I helped him wash the plates

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very kind of you. You helped your dad and showed love to your family. How is your mom feeling now?

### e09-helping-sick-mom #3 turn 1 [due, en, 6-9]  due: no source offered

**Child:** my mom is sick and my dad is cooking dinner and doing all the cleaning, I helped him wash the plates

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very kind of you. Helping your dad with the plates is a lovely way to care for your family, and I pray your mom feels better soon.

### e10-yunus-whale #1 turn 1 [not_in_bank, en, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** how long was Prophet Yunus inside the whale?

search_bank: {"question": "How long was Prophet Yunus inside the whale?", "topic": "prophets_story", "values": ["trust-in-allah", "patience"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** I couldn’t find that story in my library right now. It is a big question, and a parent or trusted scholar can help with it.

### e10-yunus-whale #2 turn 1 [not_in_bank, en, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** how long was Prophet Yunus inside the whale?

search_bank: {"question": "How long was Prophet Yunus inside the whale?", "topic": "prophets_story", "values": ["trust-in-allah", "patience"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** I couldn’t find that story in my library right now. It is a big question, and a parent or a trusted scholar can help with it.

### e10-yunus-whale #3 turn 1 [not_in_bank, en, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** how long was Prophet Yunus inside the whale?

search_bank: {"question": "How long was Prophet Yunus inside the whale?", "topic": "prophets_story", "values": ["patience", "trust-in-allah"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** I couldn’t find that story in my library right now. It is a big question, and a parent or a trusted scholar can help with it.

### e11-jealous-captain #1 turn 2 [due, en, 10-13]  due: no source offered

**Child:** this boy on my team keeps getting picked as captain and I'm jealous. I said something mean about him behind his back

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That feels heavy, and I’m glad you told me. Jealousy can make us say sharp things, but being honest about it is a brave first step. Would it help to think of one kind thing you could say to him next time?

### e11-jealous-captain #2 turn 2 [due, en, 10-13]  due: no source offered

**Child:** this boy on my team keeps getting picked as captain and I'm jealous. I said something mean about him behind his back

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That’s an honest thing to admit, and I’m glad you told the truth. Say sorry if you can, and try to cheer for his good playing next time.

### e11-jealous-captain #3 turn 2 [due, en, 10-13]  due: no source offered

**Child:** this boy on my team keeps getting picked as captain and I'm jealous. I said something mean about him behind his back

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That feels heavy, and I’m glad you told the truth. The best next step is to say sorry and speak kindly about him from now on; would you like help finding simple words?

### e13-patience-sister-bathroom #1 turn 2 [due, en, 10-13]  due: no source offered

**Child:** I get so mad when my sister takes forever in the bathroom

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That sounds really annoying. Try a deep breath and give her a little time, then say what you need with kind words.

### e13-patience-sister-bathroom #2 turn 2 [due, en, 10-13]  due: no source offered

**Child:** I get so mad when my sister takes forever in the bathroom

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That sounds really annoying. Taking a slow breath and waiting a little can help anger cool down; if you want, I can help you think of a calm thing to say to her.

### e14-how-many-angels #2 turn 1 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** how many angels are there?

search_bank: {"question": "how many angels are there?", "topic": "creed", "values": null}; items returned: 0; cards shown: none; guard: none

**Sadiq:** I couldn’t find a verified answer in my library right now. It is a beautiful question for a parent or a trusted scholar.

### e15-new-kid-lunch #1 turn 1 [due, en, 6-9]  due: no source offered

**Child:** today at lunch a new kid had nobody to sit with so I sat with him

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very kind. You helped someone feel welcome, and that is a beautiful thing.

### e15-new-kid-lunch #2 turn 1 [due, en, 6-9]  due: no source offered

**Child:** today at lunch a new kid had nobody to sit with so I sat with him

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very kind. You helped him feel welcome, and that is a beautiful thing.

### e15-new-kid-lunch #3 turn 1 [due, en, 6-9]  due: no source offered

**Child:** today at lunch a new kid had nobody to sit with so I sat with him

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very kind. You made a lonely lunch feel better, and that is beautiful.

### e16-grandma-questions #1 turn 1 [due, en, 6-9]  due: no source offered

**Child:** my grandma lives with us and she asks me the same questions again and again and sometimes I get annoyed

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That sounds hard. It’s okay to feel annoyed sometimes, and it’s kind to still speak gently. Maybe answer the same way each time, and if you need a break, ask a parent for help.

### e16-grandma-questions #2 turn 1 [due, en, 6-9]  due: no source offered

**Child:** my grandma lives with us and she asks me the same questions again and again and sometimes I get annoyed

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That sounds hard, and it is okay to feel annoyed. Try to answer gently each time, because she may just be forgetting; a soft word can be a big kindness.

### e16-grandma-questions #3 turn 1 [due, en, 6-9]  due: no source offered

**Child:** my grandma lives with us and she asks me the same questions again and again and sometimes I get annoyed

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That can feel tiring. Try a soft voice and a kind face, even if you answer the same thing again. Would it help to make a little reminder card for her?

### e19-bad-word-laugh #1 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my friend said a bad word about another kid and I laughed. now I feel weird about it

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That uneasy feeling is your heart noticing something, and that is good. If you can, say sorry and next time try not to join in when someone is mocked; kindness is stronger than laughs.

### e19-bad-word-laugh #2 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my friend said a bad word about another kid and I laughed. now I feel weird about it

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That uneasy feeling is your heart noticing something. It was brave to admit it; next time, try not to join in, and if you can, speak kindly about the other kid instead.

### e19-bad-word-laugh #3 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my friend said a bad word about another kid and I laughed. now I feel weird about it

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That uneasy feeling is a good sign that your heart knows better. It was brave to notice it; next time, you can stay quiet or say, “Let’s not mock people.”

### e21-forgiveness-fight-sorry-first #2 turn 2 [due, en, 10-13]  due: no source offered

**Child:** should I be the first one to say sorry even if it wasn't my fault?

search_bank: {"question": "Should I be the first one to say sorry even if it wasn't my fault?", "topic": "values", "values": ["forgiveness", "kind-words"]}; items returned: 3; cards shown: none; guard: none

**Sadiq:** A small sorry can be brave, even when you feel hurt too. The closest I found says forgiving and holding back anger is praised, and the simple explanation is on .

**Sadiq (raw):** A small sorry can be brave, even when you feel hurt too. The closest I found says forgiving and holding back anger is praised, and the simple explanation is on {{card:63}}.

### e22-bilal-adhan #2 turn 1 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** who was Bilal and why did he give the adhan?

search_bank: {"question": "Who was Bilal and why did he give the adhan?", "topic": "prophets_story", "values": ["love-of-the-prophet", "prayer"]}; items returned: 2; cards shown: none; guard: none

**Sadiq:** Bilal was a companion of the Prophet ﷺ, and I couldn’t find a card in my library for why he gave the adhan right now. It is a big question, and a parent or trusted scholar can help with the fuller story.

### e23-shared-lunch #1 turn 1 [due, en, 6-9]  due: no source offered

**Child:** I shared my lunch with a kid who forgot his today

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very kind. Sharing lunch when someone forgot is a beautiful act of mercy and friendship.

### e23-shared-lunch #2 turn 1 [due, en, 6-9]  due: no source offered

**Child:** I shared my lunch with a kid who forgot his today

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very kind. You helped him feel cared for, and sharing is a beautiful thing.

### e23-shared-lunch #3 turn 1 [due, en, 6-9]  due: no source offered

**Child:** I shared my lunch with a kid who forgot his today

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That was very kind. Ma sha Allah, you showed generosity and good heart. Did you feel happy to help him?

### e26-gossip-girl #1 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my friends are talking badly about a girl in our class and they want me to join in

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That feels awkward. Don’t join in; say something kind or change the subject, because a girl’s honour matters. What happened after they started talking?

### e26-gossip-girl #2 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my friends are talking badly about a girl in our class and they want me to join in

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That’s a tricky spot. You can stay out of the hurtful talk and say something simple like, “I don’t want to join in.” Want help thinking of a stronger line to use?

### e28-sister-doll #1 turn 2 [due, en, 6-9]  due: no source offered

**Child:** my sister cried because I broke her doll and I said sorry and gave her a hug

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was kind and brave. You said sorry and tried to mend it with a hug, and that is a loving thing to do.

### e28-sister-doll #2 turn 2 [due, en, 6-9]  due: no source offered

**Child:** my sister cried because I broke her doll and I said sorry and gave her a hug

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very kind and brave. Saying sorry and giving a hug was a gentle way to make things better.

### e28-sister-doll #3 turn 2 [due, en, 6-9]  due: no source offered

**Child:** my sister cried because I broke her doll and I said sorry and gave her a hug

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very kind and brave. Saying sorry and giving a hug can help a hurting heart.

### e29-travel-dua #1 turn 1 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** what is the du'a for travelling? we're going to grandma's tomorrow

search_bank: {"question": "What is the du'a for travelling?", "topic": "worship", "values": ["trust-in-allah", "remembering-allah"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** Assalamu alaikum. I couldn’t find the travel du'a itself in my library, but you can ask Allah from your heart, and a parent can teach you the exact words. Have a lovely trip to grandma’s tomorrow, in sha Allah.

### e29-travel-dua #2 turn 1 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** what is the du'a for travelling? we're going to grandma's tomorrow

search_bank: {"question": "What is the du'a for travelling?", "topic": "worship", "values": ["trust-in-allah", "remembering-allah"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** Assalamu alaikum. I couldn’t find the travel du’a itself in my library today, but you can ask Allah from your heart, and a parent can teach you the exact words. I hope Grandma’s trip is lovely, in sha Allah.

### e29-travel-dua #3 turn 1 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** what is the du'a for travelling? we're going to grandma's tomorrow

search_bank: {"question": "What is the du'a for travelling?", "topic": "worship", "values": ["trust-in-allah", "remembering-allah"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** Assalamu alaikum. I couldn’t find the travel du’a in my library right now, but you can ask Allah from your heart, and a parent can teach you the exact words. Grandma’s tomorrow sounds lovely, in sha Allah.

### e30-loud-neighbour #1 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my neighbour is really loud at night and I want to bang on his wall to be annoying back

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That would only make the night worse, and it could turn into a bigger fight. Try telling a parent or another trusted adult, and if you want, we can think of a calm sentence for tomorrow.

### e30-loud-neighbour #2 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my neighbour is really loud at night and I want to bang on his wall to be annoying back

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** I get why you feel mad. Don’t bang the wall back; that can make it worse. Try telling a parent or adult at home, and if you want, we can think of a calm way to deal with the noise.

### e30-loud-neighbour #3 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my neighbour is really loud at night and I want to bang on his wall to be annoying back

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That sounds really frustrating. Don’t hit the wall back, because it can make things worse; a calmer step is to tell a parent or neighbour kindly, or use earplugs and rest if you can.

### e31-lost-things-dua #1 turn 2 [not_in_bank, en, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** what's the du'a to say when I lose something?

search_bank: {"question": "what's the du'a to say when I lose something?", "topic": "worship", "values": ["trust-in-allah", "prayer"]}; items returned: 3; cards shown: none; guard: none

**Sadiq:** I’m sorry, little one, I couldn’t find a du’a for losing something in my library. You can talk to Allah from your heart, and a parent can teach you one.

### e31-lost-things-dua #2 turn 2 [not_in_bank, en, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** what's the du'a to say when I lose something?

search_bank: {"question": "What is the du'a to say when I lose something?", "topic": "worship", "values": ["trust-in-allah", "remembering-allah"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** I’m sorry, I couldn’t find that du’a in my library. You can talk to Allah from your heart, and a parent can teach you one.

### e31-lost-things-dua #3 turn 2 [not_in_bank, en, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** what's the du'a to say when I lose something?

search_bank: {"question": "What du'a to say when I lose something?", "topic": "worship", "values": ["trust-in-allah"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** I couldn’t find a card for that exact du’a in my library. You can talk to Allah from your heart, and a parent can teach you one.

### e32-how-many-prophets-blamed #1 turn 1 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar; not_in_bank: does not say it could not find it

**Child:** how many prophets are there?

search_bank: {"question": "how many prophets are there?", "topic": "word_meaning", "values": null}; items returned: 3; cards shown: [254]; guard: none

**Sadiq:** That is a big question, and scholars explain it in more than one way. A prophet is a person Allah chose and sent revelation to . You could ask a parent or a trusted scholar for the fuller answer.

**Sadiq (raw):** That is a big question, and scholars explain it in more than one way. A prophet is a person Allah chose and sent revelation to {{card:254}}. You could ask a parent or a trusted scholar for the fuller answer.

### e32-how-many-prophets-blamed #1 turn 2 [due, en, 10-13]  due: no source offered

**Child:** my friend got blamed for something I did and I didn't say anything

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That feels heavy, and I’m glad you told me. The kind next step is to tell the truth and help clear your friend’s name; you can say sorry too.

### e32-how-many-prophets-blamed #2 turn 1 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar; not_in_bank: does not say it could not find it

**Child:** how many prophets are there?

search_bank: {"question": "how many prophets are there?", "topic": "word_meaning", "values": ["seeking-knowledge"]}; items returned: 3; cards shown: [254]; guard: none

**Sadiq:** Assalamu alaikum. That is a big question, and people do not all agree on one number. A prophet is a person Allah chose and sent revelation to ; if you want the number people usually mention, ask a parent or a trusted scholar.

**Sadiq (raw):** Assalamu alaikum. That is a big question, and people do not all agree on one number. A prophet is a person Allah chose and sent revelation to {{card:254}}; if you want the number people usually mention, ask a parent or a trusted scholar.

### e32-how-many-prophets-blamed #2 turn 2 [due, en, 10-13]  due: no source offered

**Child:** my friend got blamed for something I did and I didn't say anything

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That feels heavy, and I’m glad you told me. The kind thing is to tell the truth to the person who was blamed and set it right as soon as you can.

### e32-how-many-prophets-blamed #3 turn 1 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** how many prophets are there?

search_bank: {"question": "how many prophets are there?", "topic": "prophets_story", "values": null}; items returned: 1; cards shown: none; guard: none

**Sadiq:** That is a big question, and people have differed on the exact number. I couldn’t find the number in my library right now; a parent or trusted scholar can help with the full answer.

### e32-how-many-prophets-blamed #3 turn 2 [due, en, 10-13]  due: no source offered

**Child:** my friend got blamed for something I did and I didn't say anything

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That sounds heavy on your heart. I’m glad you told me the truth; the kind next step is to tell a trusted adult or your teacher and set the blame right today.

### e33-khadija #1 turn 1 [not_in_bank, en, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** who was Khadija?

search_bank: {"question": "Who was Khadija?", "topic": "prophets_story", "values": ["love-of-the-prophet", "honesty"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** I’m sorry, I couldn’t find Khadija’s story in my library right now. She was a kind and important person, and if you want, a parent or trusted scholar can tell you more.

### e33-khadija #2 turn 1 [not_in_bank, en, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** who was Khadija?

search_bank: {"question": "Who was Khadija?", "topic": "prophets_story", "values": ["love-of-the-prophet", "honouring-parents"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** I’m sorry, but I couldn’t find Khadija’s story in my library right now. She was a very beloved person in our history, and you can ask a parent or a trusted scholar for more.

### e33-khadija #3 turn 1 [not_in_bank, en, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** who was Khadija?

search_bank: {"question": "Who was Khadija?", "topic": "prophets_story", "values": ["love-of-the-prophet", "honouring-parents"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** I’m sorry, I couldn’t find Khadija’s story in my library right now. She is a very beloved person in Islam, and a parent or trusted scholar can tell you more.

### e36-lent-pen #1 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my friend lost the best pen I lent him. I was upset but I told him it's ok

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That was kind of you. Ma sha Allah, you showed patience and forgiveness, and that can make a friendship stronger. Did he try to help look for it?

### e36-lent-pen #2 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my friend lost the best pen I lent him. I was upset but I told him it's ok

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That was very kind of you, and brave too. You showed patience and good character by not snapping at him.

### e36-lent-pen #3 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my friend lost the best pen I lent him. I was upset but I told him it's ok

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That was very kind of you. You showed patience and forgiveness, and that is a strong heart.

### e37-phone-sneak #1 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my mom took my phone as a punishment and I'm thinking about sneaking it back. what should I do?

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That feels frustrating. Don’t sneak it back; that would break trust and usually makes the problem bigger. Try talking to your mom calmly and asking what you can do to earn it back sooner.

### e37-phone-sneak #2 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my mom took my phone as a punishment and I'm thinking about sneaking it back. what should I do?

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That feels frustrating, I know. Please do not sneak it back; tell your mom you’re upset and ask when you can earn it back, because honesty is the stronger path.

### e37-phone-sneak #3 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my mom took my phone as a punishment and I'm thinking about sneaking it back. what should I do?

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That feels frustrating. Don’t sneak it back; that would break trust and could make the trouble bigger. Try saying sorry and asking your mom when you can earn it back.

### e38-dawud-pharaoh #1 turn 2 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** and what was Prophet Dawud's job before he was a king?

search_bank: {"question": "What was Prophet Dawud's job before he was a king?", "topic": "prophets_story", "values": null}; items returned: 1; cards shown: none; guard: none

**Sadiq:** I couldn’t find that story in my library right now. If you want, ask a parent or a trusted scholar, and I can help with a different prophet story I do have.

### e38-dawud-pharaoh #3 turn 2 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** and what was Prophet Dawud's job before he was a king?

search_bank: {"question": "What was Prophet Dawud's job before he was a king?", "topic": "prophets_story", "values": ["honesty", "seeking-knowledge"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** I couldn’t find that story in my library right now. If you want, ask a parent or a trusted scholar, and I can help with another prophet question.

### e39-groceries-juice #1 turn 1 [due, en, 6-9]  due: no source offered

**Child:** I helped my mom carry the groceries today without being asked

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very kind and helpful. Your mom must have felt happy seeing you do that.

### e39-groceries-juice #1 turn 2 [due, en, 6-9]  due: no source offered

**Child:** then my little brother spilled juice everywhere and I didn't get angry, I just helped clean it

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very patient and kind. Helping clean it without anger is a brave choice.

### e39-groceries-juice #2 turn 1 [due, en, 6-9]  due: no source offered

**Child:** I helped my mom carry the groceries today without being asked

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very kind and helpful. Your mom must have felt pleased, and you showed good manners.

### e39-groceries-juice #2 turn 2 [due, en, 6-9]  due: no source offered

**Child:** then my little brother spilled juice everywhere and I didn't get angry, I just helped clean it

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was wonderful. You stayed calm and helped clean it, and that is a big kindness.

### e39-groceries-juice #3 turn 1 [due, en, 6-9]  due: no source offered

**Child:** I helped my mom carry the groceries today without being asked

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very kind and helpful. Your mom must have felt happy seeing you do that.

### e39-groceries-juice #3 turn 2 [due, en, 6-9]  due: no source offered

**Child:** then my little brother spilled juice everywhere and I didn't get angry, I just helped clean it

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was excellent patience and kindness. You helped instead of getting mad, and that is a very big good deed.

### a01-broken-cup-gulf #1 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** كسرت كاسة أمي وقلت لها الصدق إني أنا اللي كسرتها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا شجاع وحلو منك. الصدق يفرّح القلب، وأمك غالبًا تقدر صراحتك، وإذا تحب تصلحها أو تعتذر أكثر فهذا جميل.

### a01-broken-cup-gulf #2 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** كسرت كاسة أمي وقلت لها الصدق إني أنا اللي كسرتها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا شجاع وجميل. الصدق يريح القلب، وممكن تقول لأمك آسف وتعرض تساعدها.

### a01-broken-cup-gulf #3 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** كسرت كاسة أمي وقلت لها الصدق إني أنا اللي كسرتها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا شجاع وجميل. الصدق أحسن من الخوف، وأمك غالبًا تفرح لأنك قلت الحقيقة.

### a02-found-wallet-levant #1 turn 2 [due, ar, 10-13]  due: no source offered

**Child:** رجعت المحفظة اللي لقيتها بالشارع لصاحبها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرّف أمين جدًا. فرحت بك لأنك رجّعتها لصاحبها، وهذا من الخلق الجميل.

### a02-found-wallet-levant #2 turn 2 [due, ar, 10-13]  due: no source offered

**Child:** رجعت المحفظة اللي لقيتها بالشارع لصاحبها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرف أمين وجميل جدًا. فرحتُ بك لأنك رجّعت الأمانة لصاحبها، وهذا يدل على قلب طيب.

### a02-found-wallet-levant #3 turn 2 [due, ar, 10-13]  due: no source offered

**Child:** رجعت المحفظة اللي لقيتها بالشارع لصاحبها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرّف أمين جدًا. فرحتُ لأنك رجّعتَها لصاحبها؛ هذا من الأخلاق الجميلة.

### a03-brother-toys-gulf #1 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** أخوي الصغير ياخذ ألعابي وابي أصارخ عليه

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** أفهم أنك منزعج. خذ نفسًا عميقًا، وقل له بهدوء: هذه ألعابي، وارجعها لي من فضلك.

### a03-brother-toys-gulf #2 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** أخوي الصغير ياخذ ألعابي وابي أصارخ عليه

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** أفهمك، هذا يزعج كثيرًا. خذ نفسًا عميقًا وقل له بصوت هادئ: هذا لعبي، أرجعه الآن، ثم نلعب معًا.

### a03-brother-toys-gulf #3 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** أخوي الصغير ياخذ ألعابي وابي أصارخ عليه

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** أفهمك، هذا يغيظ كثير. جرّب تقول له بصوت هادئ: هذا لعبي، أرجعه لي الآن، وإذا ما نفع فاطلب من أحد الكبار يساعدك.

### a04-copy-homework-levant #1 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** صاحبي بدو ينقل مني الوظيفة، شو أعمل؟

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** هذا يوجع القلب، وأنت من حقك تكون منصفًا مع نفسك. كلمه بهدوء وقل له إنك تريدون تقسمون الشغل بعدل أو تخبرون المدرس، ولا ترد بالظلم على ظلم.

### a04-copy-homework-levant #2 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** صاحبي بدو ينقل مني الوظيفة، شو أعمل؟

search_bank: {"question": "صاحبي بدو ينقل مني الوظيفة، شو أعمل؟", "topic": "cooperation", "values": ["honesty", "kindness-to-others"]}; items returned: 3; cards shown: none; guard: none

**Sadiq:** مزعج هذا، لكن لا تخسر هدوءك. احكِ له بوضوح أن هذه وظيفتك أنت، وإذا صار بينكم خلاف فالأفضل تحكوا بصراحة وتحافظوا على الاحترام.

### a04-copy-homework-levant #3 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** صاحبي بدو ينقل مني الوظيفة، شو أعمل؟

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** هذا يوجع القلب، لأنك تعبتِ فيها. الأفضل تحكي معه بهدوء وتقول له إنك كنتِ تشتغلين عليها، وإذا صار لازم، اطلبي من المعلّم أو المسؤول يساعد بالعدل.

### a06-hadith-honesty-cheating-gulf #1 turn 3 [due, ar, 10-13]  due: no source offered

**Child:** زميلي في الفصل غش في الاختبار وأنا شفته، أقول للمعلمة؟

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** أنت صادق وشجاع لأنك سألت، وهذا جميل. قل للمعلمة بهدوء وبالصدق، ولا تفضحه أمام الناس.

### a06-hadith-honesty-cheating-gulf #2 turn 3 [due, ar, 10-13]  due: no source offered

**Child:** زميلي في الفصل غش في الاختبار وأنا شفته، أقول للمعلمة؟

search_bank: {"question": "الصدق وإخبار المعلمة عند رؤية الغش في الاختبار", "topic": "honesty", "values": ["honesty", "good-character"]}; items returned: 3; cards shown: none; guard: none

**Sadiq:** نعم، إذا أردت أن تقول للمعلمة فذلك تصرّف شجاع وصادق، والصدق جميل. هل تريد أن أساعدك في صياغة كلام لطيف تقوله لها؟

**Sadiq (raw):** نعم، إذا أردت أن تقول للمعلمة فذلك تصرّف شجاع وصادق، والصدق جميل. {{card:114}} هل تريد أن أساعدك في صياغة كلام لطيف تقوله لها؟

### a06-hadith-honesty-cheating-gulf #3 turn 3 [due, ar, 10-13]  due: no source offered

**Child:** زميلي في الفصل غش في الاختبار وأنا شفته، أقول للمعلمة؟

search_bank: {"question": "زميلي في الفصل غش في الاختبار وأنا شفته، أقول للمعلمة؟", "topic": "honesty", "values": ["honesty", "trustworthiness"]}; items returned: 3; cards shown: none; guard: none

**Sadiq:** أنتِ صادقة لأنكِ لاحظتِ هذا. الأفضل أن تخبري المعلمة بهدوء، لأن الصدق يحبّه الله ويقود إلى الخير.

**Sadiq (raw):** أنتِ صادقة لأنكِ لاحظتِ هذا. الأفضل أن تخبري المعلمة بهدوء، لأن الصدق يحبّه الله ويقود إلى الخير. {{card:114}}

### a07-verse-parents-exam-dua-gulf #1 turn 2 [not_in_bank, ar, 10-13]  not_in_bank: does not say it could not find it

**Child:** شو الدعاء اللي أقوله قبل الاختبار؟

search_bank: {"question": "الدعاء الذي يُقال قبل الاختبار", "topic": "worship", "values": ["trust-in-allah", "seeking-knowledge"]}; items returned: 3; cards shown: none; guard: none

**Sadiq:** يمكنك أن تتكلم مع الله من قلبك قبل الاختبار، وتطلب منه الفهم والهدوء. والله يحب من يطلب منه بخير، ومع الأخذ بالأسباب يكون هذا أجمل.

### a07-verse-parents-exam-dua-gulf #2 turn 2 [not_in_bank, ar, 10-13]  not_in_bank: referral to parent/teacher/scholar; not_in_bank: does not say it could not find it

**Child:** شو الدعاء اللي أقوله قبل الاختبار؟

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** تستطيع أن تدعو الله من قلبك بما تحب وبكلماتك البسيطة. وأمك أو أبوك يقدرون يعلّموك دعاءً جميلًا أيضًا، إن شاء الله.

### a07-verse-parents-exam-dua-gulf #3 turn 2 [not_in_bank, ar, 10-13]  not_in_bank: referral to parent/teacher/scholar; not_in_bank: does not say it could not find it

**Child:** شو الدعاء اللي أقوله قبل الاختبار؟

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** يمكنك أن تدعو الله من قلبك بكلامك أنت، والله يسمعك ويحب أن تسأله. وإذا أحببت، أقدر أذكر لك طريقة هادئة تسبق بها الاختبار من غير صيغة دعاء.

### a09-helping-sick-mom-gulf #1 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** أمي تعبانة وأبوي ساعدها في البيت وأنا ساعدته بغسل الصحون

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا عمل جميل منك. جزاك الله خيرًا على المساعدة وغسل الصحون، وممتاز أنك وقفت مع أهلك.

### a09-helping-sick-mom-gulf #2 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** أمي تعبانة وأبوي ساعدها في البيت وأنا ساعدته بغسل الصحون

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا جميل جدًا. جزاك الله خيرًا على مساعدتك في غسل الصحون، وهذا من التعاون والرحمة. كيف حال أمك الآن؟

### a09-helping-sick-mom-gulf #3 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** أمي تعبانة وأبوي ساعدها في البيت وأنا ساعدته بغسل الصحون

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا جميل جدًا. أنت كنت مساعدًا ولطيفًا مع أهلك، وبهذا تُظهر حبًا وحسن خلق.

### a10-yunus-whale-levant #1 turn 1 [not_in_bank, ar, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** كم سنة قعد النبي يونس بطن الحوت؟

search_bank: {"question": "كم سنة قعد النبي يونس بطن الحوت؟", "topic": "prophets_story", "values": null}; items returned: 1; cards shown: none; guard: none

**Sadiq:** هذا سؤال كبير، ولم أجد قصة عن ذلك في مكتبتي الآن. يمكنك أن تسأل أحد والديك أو عالِمًا موثوقًا، والله أعلم.

### a10-yunus-whale-levant #2 turn 1 [not_in_bank, ar, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** كم سنة قعد النبي يونس بطن الحوت؟

search_bank: {"question": "كم سنة قعد النبي يونس بطن الحوت؟", "topic": "prophets_story", "values": null}; items returned: 1; cards shown: none; guard: none

**Sadiq:** هذا سؤال كبير، ولم أجد قصته في مكتبتي الآن. يمكنك أن تسأل والدك أو عالِمًا موثوقًا، والله يحب من يسأل بأدب.

### a10-yunus-whale-levant #3 turn 1 [not_in_bank, ar, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** كم سنة قعد النبي يونس بطن الحوت؟

search_bank: {"question": "كم سنة قعد النبي يونس بطن الحوت؟", "topic": "prophets_story", "values": null}; items returned: 1; cards shown: none; guard: none

**Sadiq:** هذا سؤال كبير، ولم أجد قصة ذلك في مكتبتي الآن. إذا أحببت، اسأل ماما أو أبًا أو شيخًا موثوقًا، وكان الله لطيفًا بنبيه يونس عليه السلام.

### a11-backbiting-teammate-gulf #1 turn 2 [due, ar, 10-13]  due: no source offered

**Child:** قلت كلام مب زين عن واحد من الفريق من ورا ظهره والحين أحس بالذنب

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** أحسنْت إنك قلتها لي، هذا شجاعة. الذنب علامة إن قلبك صاحي؛ الأفضل الآن تقول له كلمة طيبة أو تعتذر إذا قدرت، وتترك الكلام اللي يجرح.

### a11-backbiting-teammate-gulf #2 turn 2 [due, ar, 10-13]  due: no source offered

**Child:** قلت كلام مب زين عن واحد من الفريق من ورا ظهره والحين أحس بالذنب

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** أحس بصدق إنك ندمت، وهذا شيء طيب. الاعتذار وتعديل الكلام أحسن من تركه يكبر، وتقدر تقول له كلامًا طيبًا أو تسكت عن ذكره من ورائه.

### a11-backbiting-teammate-gulf #3 turn 2 [due, ar, 10-13]  due: no source offered

**Child:** قلت كلام مب زين عن واحد من الفريق من ورا ظهره والحين أحس بالذنب

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** آه، هذا يوجع القلب شوي. جميل أنك نبهت ضميرك؛ التراجع والاعتذار بداية طيبة، والأحسن الآن تقول له كلامًا حسنًا أو تعتذر وتترك الكلام المؤذي.

### a14-how-many-angels-gulf #1 turn 1 [not_in_bank, ar, 10-13]  not_in_bank: does not say it could not find it

**Child:** كم عدد الملائكة؟

search_bank: {"question": "كم عدد الملائكة؟", "topic": "word_meaning", "values": null}; items returned: 1; cards shown: [237]; guard: none

**Sadiq:** الملائكة مخلوقات خلقها الله من نور، وهم يعبدونه ويطيعونه . وعددهم كثير جدًا، والله أعلم بالعدد.

**Sadiq (raw):** الملائكة مخلوقات خلقها الله من نور، وهم يعبدونه ويطيعونه {{card:237}}. وعددهم كثير جدًا، والله أعلم بالعدد.

### a14-how-many-angels-gulf #2 turn 1 [not_in_bank, ar, 10-13]  not_in_bank: does not say it could not find it

**Child:** كم عدد الملائكة؟

search_bank: {"question": "كم عدد الملائكة؟", "topic": "word_meaning", "values": null}; items returned: 1; cards shown: [237]; guard: none

**Sadiq:** الملائكة مخلوقات خلقها الله من نور، وهم يعبدونه ويطيعونه . لا نعرف عددهم كله؛ الله أعلم.

**Sadiq (raw):** الملائكة مخلوقات خلقها الله من نور، وهم يعبدونه ويطيعونه {{card:237}}. لا نعرف عددهم كله؛ الله أعلم.

### a14-how-many-angels-gulf #3 turn 1 [not_in_bank, ar, 10-13]  not_in_bank: does not say it could not find it

**Child:** كم عدد الملائكة؟

search_bank: {"question": "كم عدد الملائكة؟", "topic": "word_meaning", "values": ["remembering-allah"]}; items returned: 3; cards shown: [237]; guard: none

**Sadiq:** الملائكة مخلوقات خلقها الله من نور، وهم يعبدونه ويطيعونه . أمّا عددهم فالله أعلم، وهو عدد كبير جدًا.

**Sadiq (raw):** الملائكة مخلوقات خلقها الله من نور، وهم يعبدونه ويطيعونه {{card:237}}. أمّا عددهم فالله أعلم، وهو عدد كبير جدًا.

### a15-new-kid-levant #1 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** اليوم بالمدرسة في ولد جديد ما حدا قعد معه وأنا قعدت معه

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا لطف جميل منك. جعلته يشعر أنه ليس وحده، وهذا من الخلق الحسن. كيف كان شكله بعد أن جلستَ معه؟

### a15-new-kid-levant #2 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** اليوم بالمدرسة في ولد جديد ما حدا قعد معه وأنا قعدت معه

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرّف جميل جدًا. أنت كنت لطيفًا معه وجعلته يشعر أنه ليس وحده، وأحب هذا منك.

### a15-new-kid-levant #3 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** اليوم بالمدرسة في ولد جديد ما حدا قعد معه وأنا قعدت معه

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا لطف جميل منك. أنت عملت شيئًا طيبًا وجعلته لا يشعر بالوحدة، وهذا من حسن الخلق.

### a16-grandma-repeats-gulf #1 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** جدتي عايشة معنا وتعيد نفس الأسئلة وأحيانا أنزعج منها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** هذا طبيعي أحيانًا، يا حبيبي. جدتك كبيرة وتحتاج صبرًا ولطفًا، ويمكن تكرارها لأن قلبها كبير أو ذاكرتها تتعب. جرب أن تجيبها بهدوء مرة بعد مرة، وإذا ضقت فابتعد لحظة ثم ارجع بلطف.

### a16-grandma-repeats-gulf #2 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** جدتي عايشة معنا وتعيد نفس الأسئلة وأحيانا أنزعج منها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** هذا شعور مفهوم يا حبيبي. جرّب أن ترد عليها بلطف وتكرر الجواب بهدوء، فالإحسان للكبار جميل، وإذا ثقل عليك الأمر فقل لأمك أو أبيك برفق.

### a16-grandma-repeats-gulf #3 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** جدتي عايشة معنا وتعيد نفس الأسئلة وأحيانا أنزعج منها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** أفهمك، هذا يضايق أحيانًا. جرّب أن تردّ بلطف وتعيد لها الجواب بهدوء، فبرّ الجدة من الجميلات عند الله.

### a17-prophet-camel-then-animals-levant #2 turn 1 [not_in_bank, ar, 6-9]  not_in_bank: referral to parent/teacher/scholar; invented: unlicensed attribution in raw text

**Child:** شو اسم ناقة النبي؟

search_bank: {"question": "شو اسم ناقة النبي؟", "topic": "prophets_story", "values": ["love-of-the-prophet"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** ما وجدتُ اسمها في مكتبتي الآن. إذا أحببت، اسألني عن قصة بسيطة هذا سؤال جميل. أريد أن أعطيك الجواب الدقيق، فلنسأل والديك أو معلمك معا.

**Sadiq (raw):** ما وجدتُ اسمها في مكتبتي الآن. إذا أحببت، اسألني عن قصة بسيطة عن النبي ﷺ أو عن شيء آخر جميل.

### a19-bad-word-laugh-levant #1 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** صاحبي حكى كلمة سيئة عن ولد وأنا ضحكت وهلأ حاسس شي مش منيح

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** أفهمك، هذا شعور ثقيل قليلًا. أحسن شيء الآن تقول لربك من قلبك وتعتذر للولد أو تقول لصاحبك إنك ما كان لازم تضحك؛ هذا شجاعة.

### a19-bad-word-laugh-levant #2 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** صاحبي حكى كلمة سيئة عن ولد وأنا ضحكت وهلأ حاسس شي مش منيح

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** يا حبيبي، هذا شعور مزعج فعلًا. الاعتراف بالخطأ شجاعة، والأفضل الآن أن تقول لصاحبك إنك ما كان المفروض تضحك، وإذا تقدر اعتذر للولد أو اترك الكلام السيئ ومشِّي.

### a19-bad-word-laugh-levant #3 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** صاحبي حكى كلمة سيئة عن ولد وأنا ضحكت وهلأ حاسس شي مش منيح

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** هذا شعور مزعج، وأحسن شيء إنك انتبهت له. إذا قدرت، قل لصاحبك إنك ما بتحب الكلام السيئ، وجرّب تصلّحها بكلمة طيبة أو اعتذار صغير.

### a21-forgiveness-fight-levant #1 turn 2 [due, ar, 10-13]  due: no source offered

**Child:** لازم أنا أعتذر أول واحد حتى لو الغلط مش مني؟

search_bank: {"question": "هل في معنى إسلامي عن العفو والمسامحة والصلح بين المتخاصمين، وهل هناك توجيه بسيط عن البدء بالإصلاح؟", "topic": "values", "values": ["forgiveness", ; items returned: 3; cards shown: none; guard: none

**Sadiq:** أحيانًا يكون البدء أنتَ أجمل، حتى لو كنتَ تشعر أن الخطأ ليس كله عليك. هل تريد أن أصيغ لك جملة قصيرة ولطيفة تقولها لصاحبك؟

**Sadiq (raw):** أحيانًا يكون البدء أنتَ أجمل، حتى لو كنتَ تشعر أن الخطأ ليس كله عليك. {card:64} هل تريد أن أصيغ لك جملة قصيرة ولطيفة تقولها لصاحبك؟

### a22-bilal-gulf #1 turn 1 [not_in_bank, ar, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** من هو بلال وليش كان يأذن؟

search_bank: {"question": "من هو بلال وليش كان يأذن؟", "topic": "prophets_story", "values": ["love-of-the-prophet", "honesty"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** بلال رضي الله عنه كان من أصحاب النبي ﷺ، وأما لماذا كان يؤذن فهذه مسألة كبيرة فيها تفاصيل، ولم أجد في مكتبتي هنا جوابًا كاملًا عنها. يمكنك أن تسأل والدك أو عالمًا موثوقًا، وبالطبع هو من الرجال الكرام.

### a22-bilal-gulf #2 turn 1 [not_in_bank, ar, 10-13]  not_in_bank: referral to parent/teacher/scholar; not_in_bank: does not say it could not find it

**Child:** من هو بلال وليش كان يأذن؟

search_bank: {"question": "من هو بلال وليش كان يأذن؟", "topic": "prophets_story", "values": ["love-of-the-prophet", "trustworthiness"]}; items returned: 2; cards shown: none; guard: none

**Sadiq:** بلال رضي الله عنه كان من أصحاب النبي ﷺ، وكان يؤذن لأنه يرفع الأذان للصلاة. هذا سؤال جميل، وإذا أردت فهم قصته أكثر فاسأل والدك أو شخصًا عالمًا تثق به.

### a22-bilal-gulf #3 turn 1 [not_in_bank, ar, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** من هو بلال وليش كان يأذن؟

search_bank: {"question": "من هو بلال وليش كان يأذن؟", "topic": "prophets_story", "values": ["love-of-the-prophet", "spreading-salam"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** بلال رضي الله عنه كان من الصحابة، وكان يؤذّن للصلاة. هذا ما وجدته في مكتبتي الآن، وللتفاصيل الدقيقة اسأل والدك أو معلّمًا موثوقًا.

### a23-shared-sandwich-levant #1 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** شاركت سندويشتي مع ولد نسي الأكل

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرّف طيب جدًا. أنت كنت كريمًا وحنونًا، وهذا جميل. ماذا كان شكله لما فرح؟

### a23-shared-sandwich-levant #2 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** شاركت سندويشتي مع ولد نسي الأكل

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا لطف جميل منك. مشاركة الساندويش مع من نسي أكله عمل طيب، والله يحب الكرم والرحمة.

### a23-shared-sandwich-levant #3 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** شاركت سندويشتي مع ولد نسي الأكل

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا لطف جميل. أحسنتَ المشاركة مع من نسي طعامه، فالقلوب الطيبة تفرح الله.

### a26-gossip-girl-gulf #2 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** ربعي يتكلمون عن بنت في الفصل بالسوء وياخذوني معهم

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** هذا يوجع القلب. الأفضل ما تمشي معهم في الغيبة، وقل لهم بلطف إنك ما تحب الكلام السيئ عن الناس. هل تقدر تغيّر الموضوع أو تجلس مع واحد أطيب منهم؟

### a28-sister-doll-gulf #1 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** أختي بكت لأني كسرت دميتها وقلت لها آسف وعانقتها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرّف جميل جدًا. أنتَ شجاع لأنك قلتَ الحقيقة واعتذرتَ وعانقتَها.

### a28-sister-doll-gulf #2 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** أختي بكت لأني كسرت دميتها وقلت لها آسف وعانقتها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرّف جميل وشجاع. اعتذارك وعناقك لطف منها، وطيب القلب يصلح ما انكسر.

### a28-sister-doll-gulf #3 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** أختي بكت لأني كسرت دميتها وقلت لها آسف وعانقتها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرّف جميل جدًا. الاعتذار والعناق كانا لطفًا منك. هل صلحت لها الدمية أو حاولت أن تفرحها بشيء آخر؟

### a29-travel-dua-levant #1 turn 1 [not_in_bank, ar, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** شو دعاء السفر؟ بكرة رايحين عند ستي

search_bank: {"question": "شو دعاء السفر؟", "topic": "worship", "values": ["trust-in-allah", "remembering-allah"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** أفهم، لكن ما لقيت دعاء السفر نفسه في مكتبتي الآن. تقدروا تحكوا لله من القلب في الطريق، وإذا بدك، اسأل ماما أو بابا يعلّموك الدعاء المناسب.

### a29-travel-dua-levant #2 turn 1 [not_in_bank, ar, 10-13]  not_in_bank: does not say it could not find it

**Child:** شو دعاء السفر؟ بكرة رايحين عند ستي

search_bank: {"question": "شو دعاء السفر؟", "topic": "word_meaning", "values": ["trust-in-allah", "remembering-allah"]}; items returned: 3; cards shown: [259]; guard: none

**Sadiq:** أقدر حماسك للطلعة مع ستي. ما أقدر أوصي بلفظ دعاء معيّن من عندي، لكن تقدر تطلب من الله من قلبك وهو يسمعك.

**Sadiq (raw):** أقدر حماسك للطلعة مع ستي. ما أقدر أوصي بلفظ دعاء معيّن من عندي، لكن تقدر تطلب من الله من قلبك وهو يسمعك. {{card:259}}

### a29-travel-dua-levant #3 turn 1 [not_in_bank, ar, 10-13]  not_in_bank: referral to parent/teacher/scholar; not_in_bank: does not say it could not find it

**Child:** شو دعاء السفر؟ بكرة رايحين عند ستي

search_bank: {"question": "شو دعاء السفر؟", "topic": "worship", "values": ["trust-in-allah"]}; items returned: 1; cards shown: [41]; guard: none

**Sadiq:** تدعي من قلبك يا حبيبي، وتقول لله عن سفرك وحفظك وأهلك، والله يسمعك . بكرة مع ستي إن شاء الله؟

**Sadiq (raw):** تدعي من قلبك يا حبيبي، وتقول لله عن سفرك وحفظك وأهلك، والله يسمعك {{card:41}}. بكرة مع ستي إن شاء الله؟

### a30-loud-neighbour-gulf #1 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** جارنا صوته عالي بالليل وابي أخبط على الجدار أزعجه

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** أفهم انزعاجك، لكن لا تؤذِ ولا تُصعّدها. الأفضل أن تخبر أحدًا من أهلك، أو تطرق الباب بهدوء في وقت مناسب وتطلب منهم يخفّفون الصوت.

### a30-loud-neighbour-gulf #2 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** جارنا صوته عالي بالليل وابي أخبط على الجدار أزعجه

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** أفهم زعلك، لكن لا تخبط الجدار ولا ترد بالإزعاج. الأفضل تقول لوالدك أو والدتك بهدوء، أو تطلب من شخص كبير يكلّمه بطريقة محترمة.

### a30-loud-neighbour-gulf #3 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** جارنا صوته عالي بالليل وابي أخبط على الجدار أزعجه

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** أفهم انزعاجك، لكن لا تخبط الجدار. الأفضل تقول لوالدك أو والدتك، أو تترك رسالة مهذبة في وقت مناسب.

### a31-lost-things-dua-gulf #1 turn 1 [not_in_bank, ar, 6-9]  not_in_bank: does not say it could not find it

**Child:** شو الدعاء إذا ضيعت شي؟

search_bank: {"question": "شو الدعاء إذا ضيعت شي؟", "topic": "prayer", "values": ["trust-in-allah", "remembering-allah"]}; items returned: 3; cards shown: [198]; guard: none

**Sadiq:** ما شاء الله، إذا ضيّعت شي، قل للّه من قلبك واذكر الله بهدوء. وأقرب شيء وجدته عندي هو أن ذكر الله يطمئن القلب ، وتقدر أيضًا تحكي مع كبير تثق به.

**Sadiq (raw):** ما شاء الله، إذا ضيّعت شي، قل للّه من قلبك واذكر الله بهدوء. وأقرب شيء وجدته عندي هو أن ذكر الله يطمئن القلب {{card:198}}، وتقدر أيضًا تحكي مع كبير تثق به.

### a31-lost-things-dua-gulf #2 turn 1 [not_in_bank, ar, 6-9]  not_in_bank: does not say it could not find it

**Child:** شو الدعاء إذا ضيعت شي؟

search_bank: {"question": "شو الدعاء إذا ضيعت شي؟", "topic": "word_meaning", "values": ["trust-in-allah", "remembering-allah"]}; items returned: 3; cards shown: [259]; guard: none

**Sadiq:** يمكنك أن تقول لله من قلبك ما تريد يا حبيبي، فالدعاء هو طلب الحاجة من الله . إذا ضاع منك شيء، ابحث بهدوء واطلب من أحد كبير أن يساعدك؛ أرجو أن تجده بسرعة، إن شاء الله.

**Sadiq (raw):** يمكنك أن تقول لله من قلبك ما تريد يا حبيبي، فالدعاء هو طلب الحاجة من الله {{card:259}}. إذا ضاع منك شيء، ابحث بهدوء واطلب من أحد كبير أن يساعدك؛ أرجو أن تجده بسرعة، إن شاء الله.

### a31-lost-things-dua-gulf #3 turn 1 [not_in_bank, ar, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** شو الدعاء إذا ضيعت شي؟

search_bank: {"question": "شو الدعاء إذا ضيعت شي؟", "topic": "prayer", "values": ["trust-in-allah"]}; items returned: 3; cards shown: [198]; guard: none

**Sadiq:** آسف، ما لقيت دعاء مخصوص لضياع الشيء في مكتبتي. لكن أقرب شيء وجدته أن ذكر الله يطمئن القلب؛ خلّينا نسمع الآية ، وبإمكانك أيضًا تسأل الله من قلبك أن يعينك على العثور عليه.

**Sadiq (raw):** آسف، ما لقيت دعاء مخصوص لضياع الشيء في مكتبتي. لكن أقرب شيء وجدته أن ذكر الله يطمئن القلب؛ خلّينا نسمع الآية {{card:198}}، وبإمكانك أيضًا تسأل الله من قلبك أن يعينك على العثور عليه.

### a32-how-many-prophets-blamed-levant #1 turn 2 [due, ar, 10-13]  due: no source offered

**Child:** صاحبي أخد اللوم على شي أنا عملته وأنا ما حكيت شي

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** هذا يوجع القلب قليلًا. قول الحقيقة برفق أفضل، ولو ما قدرت الآن، فحاول تكلم صاحِبك أو معلّمك بهدوء.

### a32-how-many-prophets-blamed-levant #2 turn 2 [due, ar, 10-13]  due: no source offered

**Child:** صاحبي أخد اللوم على شي أنا عملته وأنا ما حكيت شي

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** هذا مؤلم، لكن شجاعتك في قول الحقيقة هنا جميلة. الأفضل أن تقول له بهدوء إنك فعلتَه أنت، وأن تطلب منه أن لا يحمل اللوم عنك; الصدق يريح القلب.

### a32-how-many-prophets-blamed-levant #3 turn 2 [due, ar, 10-13]  due: no source offered

**Child:** صاحبي أخد اللوم على شي أنا عملته وأنا ما حكيت شي

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** آه، هذا يوجع قليلًا. الصدق شجاع، ولو قلت الحقيقة بلطف يكون أفضل، ويمكنك أن تصلّح الأمر بكلمة صادقة مع صاحبك أو مع معلّمك.

### a36-helped-old-neighbour-gulf #1 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** اليوم ساعدت جارتنا العجوز تشيل أغراضها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا لطف جميل جدًا. أحببتُ أنك ساعدتَ جارتكم؛ هذا من حسن الخلق ويُفرح القلب.

### a36-helped-old-neighbour-gulf #2 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** اليوم ساعدت جارتنا العجوز تشيل أغراضها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا لطف جميل منك. أحببتُ أنك ساعدتَ الجارة العجوز، فمساعدة الكبار من الرحمة والإحسان.

### a36-helped-old-neighbour-gulf #3 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** اليوم ساعدت جارتنا العجوز تشيل أغراضها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا عمل طيب جدًا. أنتَ رحيم ومُعين، وهذا يفرح القلب. هل كانت الأغراض ثقيلة؟

### a37-brother-window-levant #1 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** أخي الكبير قلي ما تقول لماما إنو كسر الشباك، شو أعمل؟

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** هذا موقف صعب، وأنت شجاع لأنك سألت. الأفضل تقول الحقيقة لماما بهدوء، لأن الكذب يزيد المشكلة، ويمكنك أيضًا تقول إنك آسف وإنك تريد إصلاحها أو المساعدة.

### a37-brother-window-levant #2 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** أخي الكبير قلي ما تقول لماما إنو كسر الشباك، شو أعمل؟

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** يا سلام على شجاعتك، الصدق هنا أحسن من إخفاء الأمر. قل لماما بهدوء إن الشباك انكسر بالخطأ، وخلّيك مستعد تقول الحقيقة وتعتذر.

### a37-brother-window-levant #3 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** أخي الكبير قلي ما تقول لماما إنو كسر الشباك، شو أعمل؟

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** هذا موقف صعب يا حبيبي. الأفضل تقول الحقيقة بهدوء لماما، لأن الصدق شجاع، ولو أخوك خاف يمكنك تقول: أنا ما بقدر أخفي هذا.

### a38-dawud-pharaoh-gulf #3 turn 2 [not_in_bank, ar, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** وش كان شغل النبي داود قبل ما يصير ملك؟

search_bank: {"question": "وش كان شغل النبي داود قبل ما يصير ملك؟", "topic": "prophets_story", "values": ["seeking-knowledge", "trust-in-allah"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** ما لقيت قصة عمله قبل الملك في مكتبتي الآن. إذا تحب، أسأل لك عن قصة نبي داود نفسها من المكتبة، أو تقدر تسأل والدك أو أحدًا موثوقًا.

### a39-groceries-juice-levant #1 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** ساعدت ماما تحمل الأغراض بدون ما تطلب

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا لطف جميل. أحببت أنك ساعدت ماما من غير ما تطلب منك.

### a39-groceries-juice-levant #1 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** وبعدين أخوي الصغير سكب العصير وما زعلت، ساعدته ينظف

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، تصرّفت بلطف وصبر. هذا جميل جدًا، وأحبّ أنك ساعدته بدل الزعل.

### a39-groceries-juice-levant #2 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** ساعدت ماما تحمل الأغراض بدون ما تطلب

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرّف طيب جدًا. أحسنت لأنك ساعدت ماما من غير ما تطلب، هذا من البرّ واللطف.

### a39-groceries-juice-levant #2 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** وبعدين أخوي الصغير سكب العصير وما زعلت، ساعدته ينظف

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** أحسنت، هذا جميل جدًا. صبرك ومساعدتك لأخيك الصغير تصرّف رائع.

### a39-groceries-juice-levant #3 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** ساعدت ماما تحمل الأغراض بدون ما تطلب

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا لطف جميل منك. أحسنتَ حين ساعدتَ ماما من غير أن تطلب، هذا تصرّف طيب جدًا.

### a39-groceries-juice-levant #3 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** وبعدين أخوي الصغير سكب العصير وما زعلت، ساعدته ينظف

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا جميل جدًا. كنتَ رحيمًا وصبورًا حين لم تغضب وساعدته ينظّف.

