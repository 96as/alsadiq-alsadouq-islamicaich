# Source timing: proactive

commit dbbc021d (dirty), agent gpt-5.4-mini, 72 conversations x 3 runs (42 due, 69 not_due, 20 ask, 23 not_in_bank turns per run), channel voice, effort default, calls 729/2000, search_bank on the agent: True, prompt sha1 7e0a552a769f,b4981cadf3c1,deb4839703fd,e3118e79de8e, answered turns 462, errored runs 0 of 216

| metric | all | en | ar | 6-9 | 10-13 | better |
|---|---:|---:|---:|---:|---:|---|
| offered_when_due | 38% (48/126) | 30% (19/63) | 46% (29/63) | 20% (12/60) | 55% (36/66) | higher |
|   of which a card shown | 35% (44/126) | 29% (18/63) | 41% (26/63) | 18% (11/60) | 50% (33/66) | higher |
| creep | 4% (8/207) | 3% (3/111) | 5% (5/96) | 4% (5/120) | 3% (3/87) | lower |
|   of which a card shown | 3% (6/207) | 3% (3/111) | 3% (3/96) | 4% (5/120) | 1% (1/87) | lower |
| ask_served | 100% (60/60) | 100% (30/30) | 100% (30/30) | 100% (24/24) | 100% (36/36) | higher |
| not_in_bank_wrong_referral | 33% (23/69) | 44% (16/36) | 21% (7/33) | 44% (12/27) | 26% (11/42) | lower |
| not_in_bank_says_not_found | 99% (68/69) | 100% (36/36) | 97% (32/33) | 100% (27/27) | 98% (41/42) | higher |
| invented_content | 0% (1/462) | 0% (0/240) | 0% (1/222) | 0% (1/231) | 0% (0/231) | lower |

Card spacing (turns between two cards in one conversation, the later one not an ask): min gap, both unprompted: 1 (1 pairs); min gap incl. a card right after an asked card: 1 (14 pairs); pairs by gap: 1: 13, 2: 1. Cards shown in total: 125.
search_bank called by label: due 55/126, not_due 9/207, ask 60/60, not_in_bank 69/69.

Offered = a card shown or a source word in the reply (hadith, verse, ayah, surah, Quran; en + ar). Referral = parent, mom, dad, teacher, scholar, imam, sheikh, "ask ..." (en + ar). Not found = could not find / not in my library / don't have / don't know; ما لقيت / ما قدرت ألاقي / لم أجد / ما عندي / مكتبتي / ما أعرف. Invented = the raw reply attributes words to the Prophet or Allah beyond the licence (`hybrid_probes.unlicensed_attribution`).

## Failing turns

### e01-broken-window #1 turn 2 [due, en, 6-9]  due: no source offered

**Child:** I told my teacher the truth about the broken window, it was me who broke it

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very brave and honest. I’m proud of you for telling the truth.

### e01-broken-window #2 turn 2 [due, en, 6-9]  due: no source offered

**Child:** I told my teacher the truth about the broken window, it was me who broke it

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was brave and honest. I’m proud of you for telling the truth, even when it was hard.

### e01-broken-window #3 turn 2 [due, en, 6-9]  due: no source offered

**Child:** I told my teacher the truth about the broken window, it was me who broke it

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very brave and honest. I’m proud of you for telling the truth; what happened after you told your teacher?

### e02-copy-homework #1 turn 2 [due, en, 10-13]  due: no source offered

**Child:** my friend wants to copy my homework tomorrow, what should I do?

search_bank: {"question": "A friend wants to copy my homework tomorrow, what should I do?", "topic": "honesty", "values": ["honesty", "kindness"]}; items returned: 3; cards shown: none; guard: none

**Sadiq:** That’s a tricky spot, and it’s kind that you want to handle it well. Tell your friend no, and offer to help them start their own work; honesty keeps trust strong.

### e02-copy-homework #2 turn 2 [due, en, 10-13]  due: no source offered

**Child:** my friend wants to copy my homework tomorrow, what should I do?

search_bank: {"question": "My friend wants to copy my homework tomorrow. What should I do?", "topic": "honesty", "values": ["honesty", "kindness-to-animals"]}; items returned: 3; cards shown: none; guard: none

**Sadiq:** That is a tricky spot. Tell him kindly you can help him understand it, but not copy it; if you want, we can think of a polite sentence together.

### e04-found-money #1 turn 2 [due, en, 6-9]  due: no source offered

**Child:** I found 20 riyals on the floor at school and nobody saw me pick it up. I gave it to the teacher

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was honest and brave. You did a really good thing by giving it to the teacher.

### e04-found-money #2 turn 2 [due, en, 6-9]  due: no source offered

**Child:** I found 20 riyals on the floor at school and nobody saw me pick it up. I gave it to the teacher

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was a brave and honest choice. You did a very good thing by giving it to the teacher.

### e04-found-money #3 turn 2 [due, en, 6-9]  due: no source offered

**Child:** I found 20 riyals on the floor at school and nobody saw me pick it up. I gave it to the teacher

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was honest and brave. You did a very good thing by giving it to the teacher.

### e05-hadith-honesty-then-cousin #1 turn 3 [due, en, 6-9]  due: no source offered

**Child:** my cousin lied to his mom and told me not to say anything, what should I do?

search_bank: {"question": "A child asks what to do when a cousin lied to his mom and told them not to say anything.", "topic": "honesty", "values": ["honesty", "keeping-prom; items returned: 3; cards shown: none; guard: none

**Sadiq:** That sounds tricky. Tell the truth to a trusted adult, and don’t keep a secret that helps a lie.

**Sadiq (raw):** That sounds tricky. Tell the truth to a trusted adult, and don’t keep a secret that helps a lie. {{card:114}}

### e05-hadith-honesty-then-cousin #2 turn 3 [due, en, 6-9]  due: no source offered

**Child:** my cousin lied to his mom and told me not to say anything, what should I do?

search_bank: {"question": "What should a child do when a cousin tells them not to tell after lying to mom?", "topic": "values", "values": ["honesty", "trustworthiness"]}; items returned: 3; cards shown: none; guard: none

**Sadiq:** That sounds hard. Don’t keep the lie secret; tell his mom kindly, or get a trusted grown-up to help you tell the truth.

**Sadiq (raw):** That sounds hard. Don’t keep the lie secret; tell his mom kindly, or get a trusted grown-up to help you tell the truth. {{card:114}}

### e05-hadith-honesty-then-cousin #3 turn 3 [due, en, 6-9]  due: no source offered

**Child:** my cousin lied to his mom and told me not to say anything, what should I do?

search_bank: {"question": "hadith or guidance about honesty and keeping trust, for a child asking what to do when a cousin asks them to keep a lie secret", "topic": "values"; items returned: 3; cards shown: none; guard: none

**Sadiq:** Tell his mom the truth, kindly, and don’t help keep the lie. Ma sha Allah, you asked a brave honest question.

### e08-thunder #3 turn 1 [not_due, en, 6-9]  creep: source on a not_due turn

**Child:** I'm scared of the thunder tonight

search_bank: {"question": "The child is scared of thunder tonight. What simple comfort can I say?", "topic": "trust-in-allah", "values": ["trust-in-allah", "remembering-alla; items returned: 3; cards shown: [198]; guard: none

**Sadiq:** That sounds scary. Remembering Allah can help hearts feel calm . Do you want me to stay with you and tell you a tiny calm story?

**Sadiq (raw):** That sounds scary. Remembering Allah can help hearts feel calm {{card:198}}. Do you want me to stay with you and tell you a tiny calm story?

### e09-helping-sick-mom #1 turn 1 [due, en, 6-9]  due: no source offered

**Child:** my mom is sick and my dad is cooking dinner and doing all the cleaning, I helped him wash the plates

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That was kind of you, Ma sha Allah. Helping your dad when your mom is sick is a very gentle thing to do.

### e09-helping-sick-mom #2 turn 1 [due, en, 6-9]  due: no source offered

**Child:** my mom is sick and my dad is cooking dinner and doing all the cleaning, I helped him wash the plates

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That was kind, Ma sha Allah. You helped your dad when your mom was sick, and that is a big help. How is your mom feeling now?

### e09-helping-sick-mom #3 turn 1 [due, en, 6-9]  due: no source offered

**Child:** my mom is sick and my dad is cooking dinner and doing all the cleaning, I helped him wash the plates

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That was very kind of you. Ma sha Allah, helping your dad like that is a big help. How is your mom feeling now?

### e10-yunus-whale #1 turn 1 [not_in_bank, en, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** how long was Prophet Yunus inside the whale?

search_bank: {"question": "How long was Prophet Yunus inside the whale?", "topic": "prophets_story", "values": null}; items returned: 1; cards shown: none; guard: none

**Sadiq:** I’m sorry, I couldn’t find that story in my library right now. You could ask a parent or a trusted scholar, and Prophet Yunus’s story is a very beautiful one, mashallah.

### e10-yunus-whale #2 turn 1 [not_in_bank, en, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** how long was Prophet Yunus inside the whale?

search_bank: {"question": "how long was Prophet Yunus inside the whale?", "topic": "prophets_story", "values": null}; items returned: 1; cards shown: none; guard: none

**Sadiq:** I couldn’t find that story in my library right now. It is a big question, and a parent or a trusted scholar can help with it.

### e10-yunus-whale #3 turn 1 [not_in_bank, en, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** how long was Prophet Yunus inside the whale?

search_bank: {"question": "how long was Prophet Yunus inside the whale?", "topic": "prophets_story", "values": ["courage", "patience"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** I couldn’t find that story in my library right now. If you want, you can ask a parent or a trusted scholar, and I can still tell you a short made-up story about a brave child.

### e11-jealous-captain #1 turn 2 [due, en, 10-13]  due: no source offered

**Child:** this boy on my team keeps getting picked as captain and I'm jealous. I said something mean about him behind his back

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That feels heavy, and I’m glad you told me the truth. The kinder next step is to stop the mean talk and, if you can, make it right with him.

### e11-jealous-captain #2 turn 2 [due, en, 10-13]  due: no source offered

**Child:** this boy on my team keeps getting picked as captain and I'm jealous. I said something mean about him behind his back

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That sounds heavy, and I’m glad you told me. Saying sorry and choosing a kind word next is a brave repair; would you like help thinking of one honest sentence to say to him?

### e13-patience-sister-bathroom #3 turn 2 [due, en, 10-13]  due: no source offered

**Child:** I get so mad when my sister takes forever in the bathroom

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That sounds really annoying. Try taking a slow breath and using calm words, like asking for a turn without shouting.

### e15-new-kid-lunch #1 turn 1 [due, en, 6-9]  due: no source offered

**Child:** today at lunch a new kid had nobody to sit with so I sat with him

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very kind. You helped him feel less alone, and that is a beautiful thing.

### e15-new-kid-lunch #2 turn 1 [due, en, 6-9]  due: no source offered

**Child:** today at lunch a new kid had nobody to sit with so I sat with him

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very kind. You made the new kid feel seen and safe.

### e15-new-kid-lunch #3 turn 1 [due, en, 6-9]  due: no source offered

**Child:** today at lunch a new kid had nobody to sit with so I sat with him

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That was very kind. Ma sha Allah, you made someone feel seen at lunch.

### e17-prophet-camel-then-animals #1 turn 1 [not_in_bank, en, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** what was the name of the Prophet's camel?

search_bank: {"question": "What was the name of the Prophet's camel?", "topic": "prophets_story", "values": null}; items returned: 1; cards shown: none; guard: none

**Sadiq:** I couldn’t find that in my library right now. You could ask a parent or a trusted scholar, and it’s a lovely question about the Prophet ﷺ.

### e17-prophet-camel-then-animals #2 turn 1 [not_in_bank, en, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** what was the name of the Prophet's camel?

search_bank: {"question": "What was the name of the Prophet's camel?", "topic": "prophets_story", "values": null}; items returned: 1; cards shown: none; guard: none

**Sadiq:** I couldn’t find that in my library right now. It sounds like a big question, and a parent or trusted scholar may know better.

### e19-bad-word-laugh #1 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my friend said a bad word about another kid and I laughed. now I feel weird about it

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That uneasy feeling is your heart noticing something unkind. Next time, you can stay quiet or say, “Let’s not say that about people.”

### e19-bad-word-laugh #2 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my friend said a bad word about another kid and I laughed. now I feel weird about it

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That uneasy feeling is a good sign. Next time, you can stop the laugh, say nothing, or change the subject kindly; it takes a brave heart.

### e22-bilal-adhan #3 turn 1 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** who was Bilal and why did he give the adhan?

search_bank: {"question": "Who was Bilal, and why did he give the adhan?", "topic": "prophets_story", "values": ["love-of-the-prophet", "prayer"]}; items returned: 2; cards shown: none; guard: none

**Sadiq:** I couldn’t find Bilal’s story in my library right now. It’s a big question, and Bilal was a beautiful companion of the Prophet ﷺ; if you want, a parent or trusted scholar can help with the details.

### e23-shared-lunch #1 turn 1 [due, en, 6-9]  due: no source offered

**Child:** I shared my lunch with a kid who forgot his today

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was kind of you. Sharing with someone who forgot their lunch is a lovely mercy.

### e23-shared-lunch #2 turn 1 [due, en, 6-9]  due: no source offered

**Child:** I shared my lunch with a kid who forgot his today

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very kind. Sharing like that shows a soft heart and good character.

### e23-shared-lunch #3 turn 1 [due, en, 6-9]  due: no source offered

**Child:** I shared my lunch with a kid who forgot his today

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That was very kind, Ma sha Allah. You helped a friend and made their day a little easier.

### e26-gossip-girl #3 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my friends are talking badly about a girl in our class and they want me to join in

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That feels awkward, but staying kind is stronger. You can say you don’t want to join in and change the subject or walk away.

### e27-gratitude-presentation #2 turn 2 [not_due, en, 6-9]  creep: source on a not_due turn

**Child:** I'm thankful for my dog

search_bank: {"question": "A child says they are thankful for their dog. Give one short source about gratitude that fits this moment.", "topic": "values", "values": ["gratit; items returned: 3; cards shown: [73]; guard: none

**Sadiq:** Ma sha Allah, that is a lovely thing to be thankful for. Let’s listen to a verse: it teaches that being thankful is good for us too and makes our hearts happy.

**Sadiq (raw):** Ma sha Allah, that is a lovely thing to be thankful for. Let’s listen to a verse: {{card:73}} it teaches that being thankful is good for us too and makes our hearts happy.

### e27-gratitude-presentation #3 turn 2 [not_due, en, 6-9]  creep: source on a not_due turn

**Child:** I'm thankful for my dog

search_bank: {"question": "A child says they are thankful for their dog. Share one simple Islamic source about gratitude, if available, and keep it very short.", "topic": "v; items returned: 3; cards shown: [71]; guard: none

**Sadiq:** Ma sha Allah, that is a lovely thing to be thankful for. Let’s listen to a verse: .

**Sadiq (raw):** Ma sha Allah, that is a lovely thing to be thankful for. Let’s listen to a verse: {{card:71}}.

### e28-sister-doll #2 turn 2 [due, en, 6-9]  due: no source offered

**Child:** my sister cried because I broke her doll and I said sorry and gave her a hug

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very kind and brave. Saying sorry and giving a hug can help hearts feel softer.

### e28-sister-doll #3 turn 2 [due, en, 6-9]  due: no source offered

**Child:** my sister cried because I broke her doll and I said sorry and gave her a hug

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was kind and brave. Saying sorry and giving a hug can help a hurt heart feel safer.

### e29-travel-dua #3 turn 1 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** what is the du'a for travelling? we're going to grandma's tomorrow

search_bank: {"question": "What is the du'a for travelling?", "topic": "worship", "values": ["trust-in-allah"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** I’m sorry, I couldn’t find that du’a in my library. You can talk to Allah from your heart, and ask a parent to teach you the travel du’a before tomorrow.

### e30-loud-neighbour #1 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my neighbour is really loud at night and I want to bang on his wall to be annoying back

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That sounds really frustrating. Don’t bang the wall back; it can make things worse, and a calmer next step is better. Could you tell a parent or another trusted adult, or write down the times it happens so someone can help?

### e30-loud-neighbour #2 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my neighbour is really loud at night and I want to bang on his wall to be annoying back

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That sounds really annoying. Try not to bang back; a calmer choice is to tell a parent or kindly ask the neighbour to keep it quieter. What time is it usually the loudest?

### e32-how-many-prophets-blamed #1 turn 1 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** how many prophets are there?

search_bank: {"question": "how many prophets are there?", "topic": "prophets_story", "values": null}; items returned: 1; cards shown: none; guard: none

**Sadiq:** That’s a big question, and I couldn’t find a clear answer in my library right now. A parent or a trusted scholar knows best, and I like that you’re asking about the prophets.

### e32-how-many-prophets-blamed #1 turn 2 [due, en, 10-13]  due: no source offered

**Child:** my friend got blamed for something I did and I didn't say anything

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That must feel heavy. It was brave to tell me, and the kind next step is to tell the truth to a trusted adult or the person who was blamed.

### e32-how-many-prophets-blamed #2 turn 1 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** how many prophets are there?

search_bank: {"question": "How many prophets are there?", "topic": "prophets_story", "values": ["love-of-the-prophet"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** That is a big question, and I couldn’t find a clear answer in my library right now. A parent or a trusted scholar can help with it, in sha Allah.

### e32-how-many-prophets-blamed #2 turn 2 [due, en, 10-13]  due: no source offered

**Child:** my friend got blamed for something I did and I didn't say anything

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That sounds heavy, and I’m glad you told the truth now. The kind next step is to tell the truth to the right adult and try to put it right for your friend.

### e32-how-many-prophets-blamed #3 turn 1 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** how many prophets are there?

search_bank: {"question": "How many prophets are there?", "topic": "prophets_story", "values": null}; items returned: 1; cards shown: none; guard: none

**Sadiq:** That’s a big question, and I couldn’t find a clear answer for it in my library right now. If you want, a parent or a trusted scholar can help with the different numbers people mention.

### e32-how-many-prophets-blamed #3 turn 2 [due, en, 10-13]  due: no source offered

**Child:** my friend got blamed for something I did and I didn't say anything

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That sounds heavy, and I’m glad you told me. The kind next step is to tell the truth to a trusted adult or the person who was blamed, so your friend is not left carrying it.

### e33-khadija #1 turn 1 [not_in_bank, en, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** who was Khadija?

search_bank: {"question": "Who was Khadija?", "topic": "prophets_story", "values": ["love-of-the-prophet", "kindness-to-animals"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** I couldn’t find Khadija in my library right now. She was a very dear, kind person in the early Muslim story, and if you want, a parent or trusted scholar can tell you more.

### e33-khadija #2 turn 1 [not_in_bank, en, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** who was Khadija?

search_bank: {"question": "Who was Khadija?", "topic": "prophets_story", "values": ["love-of-the-prophet", "honesty"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** I couldn’t find Khadija’s story in my library right now. She is a very beloved person in Islam, and if you want, ask a parent or a trusted scholar about her.

### e33-khadija #3 turn 1 [not_in_bank, en, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** who was Khadija?

search_bank: {"question": "Who was Khadija?", "topic": "prophets_story", "values": ["love-of-the-prophet"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** I’m sorry, I couldn’t find Khadija in my library right now. She was a kind and important person, and if you want, you can ask a parent or trusted scholar for more.

### e36-lent-pen #1 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my friend lost the best pen I lent him. I was upset but I told him it's ok

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That was very kind of you. Forgiving him when you were upset is strong and sweet, and it helps friendship stay warm.

### e36-lent-pen #2 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my friend lost the best pen I lent him. I was upset but I told him it's ok

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That was kind and strong of you. Forgiving when you were upset is a brave choice, and Allah loves good character.

### e36-lent-pen #3 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my friend lost the best pen I lent him. I was upset but I told him it's ok

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That was very kind of you. Ma sha Allah, you showed patience and good character there.

### e37-phone-sneak #1 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my mom took my phone as a punishment and I'm thinking about sneaking it back. what should I do?

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That’s frustrating, but sneaking it back would break trust. It’s better to wait, stay calm, and ask your mom when you can earn it back; if you want, I can help you think of a respectful way to say it.

### e37-phone-sneak #2 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my mom took my phone as a punishment and I'm thinking about sneaking it back. what should I do?

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That’s a tricky moment. Sneaking it back would break trust, and trust is hard to mend; it’s better to wait, stay calm, and ask your mom if you can earn it back by showing good behavior.

### e37-phone-sneak #3 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my mom took my phone as a punishment and I'm thinking about sneaking it back. what should I do?

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That feels frustrating. Don’t sneak it back; it will likely make the problem bigger. Try telling your mom calmly that you want another chance and ask what you can do to earn it back.

### e38-dawud-pharaoh #1 turn 2 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** and what was Prophet Dawud's job before he was a king?

search_bank: {"question": "What was Prophet Dawud's job before he was a king?", "topic": "prophets_story", "values": null}; items returned: 1; cards shown: none; guard: none

**Sadiq:** I couldn’t find that story in my library right now. If you want, ask a parent or a trusted scholar, and I can still share a made-up story about an everyday child.

### e38-dawud-pharaoh #2 turn 2 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** and what was Prophet Dawud's job before he was a king?

search_bank: {"question": "What was Prophet Dawud's job before he was a king?", "topic": "prophets_story", "values": null}; items returned: 1; cards shown: none; guard: none

**Sadiq:** I couldn’t find that story in my library right now. It’s a big question, and a parent or a trusted scholar may know best.

### e38-dawud-pharaoh #3 turn 2 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** and what was Prophet Dawud's job before he was a king?

search_bank: {"question": "What was Prophet Dawud's job before he was a king?", "topic": "prophets_story", "values": null}; items returned: 1; cards shown: none; guard: none

**Sadiq:** I couldn’t find Prophet Dawud’s job in my library right now. If you want, ask a parent or a trusted scholar, and I can help with a short made-up story instead.

### e39-groceries-juice #1 turn 1 [due, en, 6-9]  due: no source offered

**Child:** I helped my mom carry the groceries today without being asked

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was kind and helpful. Your mom must have felt very happy, and you did a good thing without being asked.

### e39-groceries-juice #1 turn 2 [due, en, 6-9]  due: no source offered

**Child:** then my little brother spilled juice everywhere and I didn't get angry, I just helped clean it

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very good. You stayed calm and helped instead of getting upset, and that is strong kindness.

### e39-groceries-juice #2 turn 1 [due, en, 6-9]  due: no source offered

**Child:** I helped my mom carry the groceries today without being asked

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was kind and helpful. Helping without being asked is a lovely way to care for your mom.

### e39-groceries-juice #2 turn 2 [due, en, 6-9]  due: no source offered

**Child:** then my little brother spilled juice everywhere and I didn't get angry, I just helped clean it

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very patient and kind. Helping clean it instead of getting angry is a big act of good character.

### e39-groceries-juice #3 turn 1 [due, en, 6-9]  due: no source offered

**Child:** I helped my mom carry the groceries today without being asked

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very kind of you. Helping your mom without being asked is a beautiful thing, and I bet it made her feel happy.

### a01-broken-cup-gulf #1 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** كسرت كاسة أمي وقلت لها الصدق إني أنا اللي كسرتها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا شجاع منك. الصدق شيء جميل، وقدّرت أمانتك كثيرًا.

### a01-broken-cup-gulf #2 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** كسرت كاسة أمي وقلت لها الصدق إني أنا اللي كسرتها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا شجاع جدًا منك. الصدق يفرّح القلب، وأحسن شيء تسويه الآن إنك تساعد أمك وتقول لها: آسف.

### a01-broken-cup-gulf #3 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** كسرت كاسة أمي وقلت لها الصدق إني أنا اللي كسرتها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا شجاعة جميلة منك. الصدق صعب أحيانًا، لكنك اخترته، وهذا شيء طيب جدًا.

### a02-found-wallet-levant #1 turn 2 [due, ar, 10-13]  due: no source offered

**Child:** رجعت المحفظة اللي لقيتها بالشارع لصاحبها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرّف أمين وجميل جدًا. أحسنت لأنك رجّعتها لصاحبها، والأمانة من أجمل الصفات.

### a02-found-wallet-levant #2 turn 2 [due, ar, 10-13]  due: no source offered

**Child:** رجعت المحفظة اللي لقيتها بالشارع لصاحبها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرّف أمين جدًا. أحسنت لأنك رددت المحفظة لصاحبها، هذا من الأخلاق الجميلة.

### a02-found-wallet-levant #3 turn 2 [due, ar, 10-13]  due: no source offered

**Child:** رجعت المحفظة اللي لقيتها بالشارع لصاحبها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرّف أمين وجميل جدًا. أحبّ شجاعتك في ردّ الحق لصاحبه، هذا من الأخلاق الطيبة.

### a03-brother-toys-gulf #3 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** أخوي الصغير ياخذ ألعابي وابي أصارخ عليه

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** أفهم زعلك. خذ نفسًا واحدًا وقل له بهدوء: هذا لعبي، أرجعه بعدين، واطلب من أمك أو أبيك يساعدونكم على الدور.

### a06-hadith-honesty-cheating-gulf #1 turn 3 [due, ar, 10-13]  due: no source offered

**Child:** زميلي في الفصل غش في الاختبار وأنا شفته، أقول للمعلمة؟

search_bank: {"question": "هل توجد توجيهات بسيطة عن الصدق والأمانة في مثل رؤية غشّ زميل في الفصل؟", "topic": "values", "values": ["honesty", "good-character"]}; items returned: 3; cards shown: none; guard: none

**Sadiq:** هذا موقف صعب، وأنت صادق لأنك انتبهت له. الأفضل أن تخبري المعلمة بهدوء، فالصدق جميل، هل تريدين أن أقول لك جملة قصيرة تقوليها؟

**Sadiq (raw):** هذا موقف صعب، وأنت صادق لأنك انتبهت له. الأفضل أن تخبري المعلمة بهدوء، فالصدق جميل، {{card:114}} هل تريدين أن أقول لك جملة قصيرة تقوليها؟

### a06-hadith-honesty-cheating-gulf #2 turn 3 [due, ar, 10-13]  due: no source offered

**Child:** زميلي في الفصل غش في الاختبار وأنا شفته، أقول للمعلمة؟

search_bank: {"question": "زميلي في الفصل غش في الاختبار وأنا شفته، أقول للمعلمة؟", "topic": "honesty", "values": ["honesty", "kind-words"]}; items returned: 3; cards shown: none; guard: none

**Sadiq:** هذا موقف صعب، وأنت صادق لأنك قلت ما رأيت. الأفضل أن تخبري المعلمة بهدوء وبالحق، وإذا أردتِ أساعدك بصيغة لطيفة تقولينها لها.

**Sadiq (raw):** هذا موقف صعب، وأنت صادق لأنك قلت ما رأيت. {{card:114}} الأفضل أن تخبري المعلمة بهدوء وبالحق، وإذا أردتِ أساعدك بصيغة لطيفة تقولينها لها.

### a09-helping-sick-mom-gulf #1 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** أمي تعبانة وأبوي ساعدها في البيت وأنا ساعدته بغسل الصحون

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا جميل جدًا. ساعدتَ أهلك بلطف، وهذا تصرّف طيب. كيف أصبحت أمك الآن؟

### a09-helping-sick-mom-gulf #3 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** أمي تعبانة وأبوي ساعدها في البيت وأنا ساعدته بغسل الصحون

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا جميل يا بطل. أنت كنت عونًا لأبيك، وهذا لطف كبير مع أمك أيضًا.

### a10-yunus-whale-levant #2 turn 1 [not_in_bank, ar, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** كم سنة قعد النبي يونس بطن الحوت؟

search_bank: {"question": "كم سنة قعد النبي يونس بطن الحوت؟", "topic": "prophets_story", "values": null}; items returned: 1; cards shown: none; guard: none

**Sadiq:** هذا سؤال كبير، ولم أجد قصة النبي يونس عليه السلام في مكتبتي الآن. يمكنك أن تسأل أحد والديك أو عالِمًا موثوقًا، والله أرحم وأعلم.

### a15-new-kid-levant #1 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** اليوم بالمدرسة في ولد جديد ما حدا قعد معه وأنا قعدت معه

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا لطف جميل منك. جعلت الولد الجديد لا يشعر بالوحدة، وهذا شيء طيب جدًا.

### a15-new-kid-levant #2 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** اليوم بالمدرسة في ولد جديد ما حدا قعد معه وأنا قعدت معه

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا لطف جميل منك. هل صار يبتسم أو يرتاح لما جلست معه؟

### a15-new-kid-levant #3 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** اليوم بالمدرسة في ولد جديد ما حدا قعد معه وأنا قعدت معه

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا لطف جميل منك. هل هو صار أسعد لما جلست معه؟

### a16-grandma-repeats-gulf #1 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** جدتي عايشة معنا وتعيد نفس الأسئلة وأحيانا أنزعج منها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** أفهمك، هذا قد يضايق أحيانًا. جرّب أن تردّ عليها بلطف وبكلمات قصيرة، فمساعدة الكبار بلين من أخلاق جميلة، والله يحب الكلمة الطيبة.

### a16-grandma-repeats-gulf #2 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** جدتي عايشة معنا وتعيد نفس الأسئلة وأحيانا أنزعج منها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** أفهمك، هذا يقدر يضايق أحيانًا. جرّب ترد عليها بلطف وبصبر، فهي كبيرة في السن وربما تنسى؛ والرفق معها من الأخلاق الجميلة.

### a16-grandma-repeats-gulf #3 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** جدتي عايشة معنا وتعيد نفس الأسئلة وأحيانا أنزعج منها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** آه، هذا متعب أحيانًا. ربما هي تنسى، فجرّب أن تجيبها بلطف مرة أخرى وتقول في قلبك: الحمد لله على وجودها معنا، ولو أردت أساعدك بكلمة لطيفة تقولها لها.

### a17-prophet-camel-then-animals-levant #1 turn 1 [not_in_bank, ar, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** شو اسم ناقة النبي؟

search_bank: {"question": "شو اسم ناقة النبي؟", "topic": "prophets_story", "values": null}; items returned: 1; cards shown: none; guard: none

**Sadiq:** لا أجد اسم ناقة النبي في مكتبتي الآن. إذا أردت، اسألني عن قصة قصيرة من السيرة، أو اسأل ماما أو شيخًا تثق به.

### a17-prophet-camel-then-animals-levant #2 turn 1 [not_in_bank, ar, 6-9]  not_in_bank: referral to parent/teacher/scholar; invented: unlicensed attribution in raw text

**Child:** شو اسم ناقة النبي؟

search_bank: {"question": "ما اسم ناقة النبي ﷺ؟", "topic": "prophets_story", "values": null}; items returned: 1; cards shown: none; guard: none

**Sadiq:** ما قدرت أجد هذا في مكتبتي الآن. إذا أحببت، اسأل ماما أو أبًا يعرفون، وأنا أقدر أساعدك بسؤال آخر هذا سؤال جميل. أريد أن أعطيك الجواب الدقيق، فلنسأل والديك أو معلمك معا.

**Sadiq (raw):** ما قدرت أجد هذا في مكتبتي الآن. إذا أحببت، اسأل ماما أو أبًا يعرفون، وأنا أقدر أساعدك بسؤال آخر عن النبي ﷺ.

### a17-prophet-camel-then-animals-levant #3 turn 1 [not_in_bank, ar, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** شو اسم ناقة النبي؟

search_bank: {"question": "شو اسم ناقة النبي؟", "topic": "prophets_story", "values": ["love-of-the-prophet"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** ما قدرت أجد اسم ناقة النبي في مكتبتي الآن. إذا أحببت، اسأل ماما أو أباك أو معلّمًا تثق به، وأنا أقدر أساعدك بشيء جميل عن السيرة بدلًا من ذلك.

### a19-bad-word-laugh-levant #1 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** صاحبي حكى كلمة سيئة عن ولد وأنا ضحكت وهلأ حاسس شي مش منيح

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** آه، هذا شعور ثقيل، والحمد لله أنك انتبهت له. الأفضل الآن تقول لصاحبك إنك ما كان لازم تضحك، وإذا قدرت اعتذر للولد بكلمة قصيرة ولطيفة.

### a19-bad-word-laugh-levant #2 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** صاحبي حكى كلمة سيئة عن ولد وأنا ضحكت وهلأ حاسس شي مش منيح

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** آسف إنك حاسس هيك، والصدق مع نفسك شجاعة جميلة. تقدر تصلّحها بأنك تقول لصاحبك إنك ما كان لازم تضحك، وإذا قدرت اعتذر للولد بكلمة طيبة.

### a22-bilal-gulf #2 turn 1 [not_in_bank, ar, 10-13]  not_in_bank: does not say it could not find it

**Child:** من هو بلال وليش كان يأذن؟

search_bank: {"question": "من هو بلال ولماذا كان يؤذن؟", "topic": "prophets_story", "values": ["love-of-the-prophet", "spreading-salam"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** بلال رضي الله عنه كان من الصحابة، وكان يؤذّن لأن الأذان ينادي الناس إلى الصلاة. هذا سؤال جميل عن بلال، وإذا أردت أستطيع أشرح لك ما هو الأذان بطريقة بسيطة.

### a23-shared-sandwich-levant #1 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** شاركت سندويشتي مع ولد نسي الأكل

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا لطف جميل منك. أحسنت المشاركة مع من نسي أكلَه، يا بطل.

### a23-shared-sandwich-levant #3 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** شاركت سندويشتي مع ولد نسي الأكل

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا لطف جميل منك. شاركتَ وأطعمتَ من نسي الأكل، وهذا من التعاون والرحمة

**Sadiq (raw):** ما شاء الله، هذا لطف جميل منك. شاركتَ وأطعمتَ من نسي الأكل، وهذا من التعاون والرحمة {{card:helping-others}}

### a27-gratitude-school-levant #1 turn 2 [not_due, ar, 6-9]  creep: source on a not_due turn

**Child:** أنا شاكر على كلبي

search_bank: {"question": "آية أو حديث عن الشكر", "topic": "hadith", "values": ["gratitude"]}; items returned: 3; cards shown: [110]; guard: none

**Sadiq:** ما شاء الله، هذا جميل. في الحديث على بطاقتك: يعني أن الله يرضى عن العبد إذا حمده بعد الأكل أو الشرب.

**Sadiq (raw):** ما شاء الله، هذا جميل. في الحديث على بطاقتك: {{card:110}} يعني أن الله يرضى عن العبد إذا حمده بعد الأكل أو الشرب.

### a27-gratitude-school-levant #2 turn 2 [not_due, ar, 6-9]  creep: source on a not_due turn

**Child:** أنا شاكر على كلبي

search_bank: {"question": "آية أو حديث عن الشكر", "topic": "hadith", "values": ["gratitude"]}; items returned: 3; cards shown: [110]; guard: none

**Sadiq:** ما شاء الله، هذا جميل. وفي simple words، الحديث on your screen means أن الله يرضى عن العبد إذا حمده بعد الأكل أو الشرب؛ فقولك الحمد لله مع كلبك أيضًا يذكّرك بالنعمة.

**Sadiq (raw):** ما شاء الله، هذا جميل. {{card:110}} وفي simple words، الحديث on your screen means أن الله يرضى عن العبد إذا حمده بعد الأكل أو الشرب؛ فقولك الحمد لله مع كلبك أيضًا يذكّرك بالنعمة.

### a28-sister-doll-gulf #1 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** أختي بكت لأني كسرت دميتها وقلت لها آسف وعانقتها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا لطف جميل منك. الاعتذار والعناق يرمّمان القلوب الصغيرة، وأختك ستفرح بلطفك.

### a28-sister-doll-gulf #2 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** أختي بكت لأني كسرت دميتها وقلت لها آسف وعانقتها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرّف جميل جدًا. الاعتذار والعناق يرمّمان القلوب الصغيرة، وأنت كنت شجاعًا وصادقًا.

### a28-sister-doll-gulf #3 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** أختي بكت لأني كسرت دميتها وقلت لها آسف وعانقتها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرّف جميل جدًا. أحسنت لأنك قلت آسف وعانقتها؛ هذا لطف وشجاعة.

### a29-travel-dua-levant #2 turn 1 [not_in_bank, ar, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** شو دعاء السفر؟ بكرة رايحين عند ستي

search_bank: {"question": "شو دعاء السفر؟", "topic": "worship", "values": null}; items returned: 2; cards shown: [198]; guard: none

**Sadiq:** ما لقيت دعاء السفر في مكتبتي، لكن أقرب شيء وجدته أن ذكر الله يطمئن القلب. بكرة بالسيارة أو الباص، إذا حسّيتي قلبك متوتر، احكي لستك أو ماما عن اللي بتتمنّيه للطريق.

**Sadiq (raw):** ما لقيت دعاء السفر في مكتبتي، لكن أقرب شيء وجدته أن ذكر الله يطمئن القلب. {{card:198}} بكرة بالسيارة أو الباص، إذا حسّيتي قلبك متوتر، احكي لستك أو ماما عن اللي بتتمنّيه للطريق.

### a29-travel-dua-levant #2 turn 2 [not_due, ar, 10-13]  creep: source on a not_due turn

**Child:** طريقها خمس ساعات

search_bank: {"question": "دعاء السفر", "topic": "worship", "values": null}; items returned: 2; cards shown: none; guard: none

**Sadiq:** خمّس ساعات طويلة شوي، بس فيكِ تخلّيها أحلى بشي هادئ مع ستي. أقرب شيء لقيته إن ذكر الله يطمّن القلب، وخلّينا نسمع هذه الآية:

**Sadiq (raw):** خمّس ساعات طويلة شوي، بس فيكِ تخلّيها أحلى بشي هادئ مع ستي. أقرب شيء لقيته إن ذكر الله يطمّن القلب، وخلّينا نسمع هذه الآية: {{card:198}}

### a29-travel-dua-levant #3 turn 2 [not_due, ar, 10-13]  creep: source on a not_due turn

**Child:** طريقها خمس ساعات

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، خمس ساعات رحلة طويلة شوي. إن شاء الله يمر الوقت بسرعة مع شيء جميل: قرآن، لعبة هادئة، أو عدّ السيارات والغيوم من الشباك.

### a30-loud-neighbour-gulf #2 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** جارنا صوته عالي بالليل وابي أخبط على الجدار أزعجه

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** أفهم أنك منزعج، لكن لا تضرب الجدار؛ هذا يزيد المشكلة. الأفضل تقول لأحد من أهلك أو تكتب له رسالة هادئة إذا كانوا مناسبين، ثم حاول تهدأ قليلًا.

### a30-loud-neighbour-gulf #3 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** جارنا صوته عالي بالليل وابي أخبط على الجدار أزعجه

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** أفهم أنك منزعج، لكن لا تخبط على الجدار ولا تؤذِ أحدًا. الأفضل أن تخبر والدك أو والدتك بهدوء، وهم يعرفون كيف يتصرفون.

### a36-helped-old-neighbour-gulf #1 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** اليوم ساعدت جارتنا العجوز تشيل أغراضها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا لطف جميل جدًا. أفرحتَها وساعدتَها، وهذا من حسن الخلق.

### a36-helped-old-neighbour-gulf #2 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** اليوم ساعدت جارتنا العجوز تشيل أغراضها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا لطف جميل منك. أحسنت لأنك خففت عنها وساعدتَها، وهذا من حسن الخلق.

### a37-brother-window-levant #1 turn 2 [not_due, ar, 10-13]  creep: source on a not_due turn

**Child:** طيب خلص، بفكر

search_bank: {"question": "الصدق وإصلاح الخطأ عندما يطلب منك أحد أن تخفي كسر الشباك", "topic": "honesty", "values": ["honesty", "kind-words"]}; items returned: 3; cards shown: [170]; guard: none

**Sadiq:** يا بطل، فكّرت بهدوء وهذا شيء طيب. أقرب شيء وجدته في مكتبة بسيطة عندي هو ، وتقدر تقول الحقيقة بلطف لماما أو تطلب من أخيك يساعدك يصلّح الخطأ.

**Sadiq (raw):** يا بطل، فكّرت بهدوء وهذا شيء طيب. أقرب شيء وجدته في مكتبة بسيطة عندي هو {{card:170}}، وتقدر تقول الحقيقة بلطف لماما أو تطلب من أخيك يساعدك يصلّح الخطأ.

### a38-dawud-pharaoh-gulf #1 turn 2 [not_in_bank, ar, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** وش كان شغل النبي داود قبل ما يصير ملك؟

search_bank: {"question": "وش كان شغل النبي داود قبل ما يصير ملك؟", "topic": "prophets_story", "values": null}; items returned: 1; cards shown: none; guard: none

**Sadiq:** ما قدرت ألقى قصة داود عليه السلام في مكتبتي الآن. هذا سؤال كبير، وأسلم شيء تسأله والدك أو عالِمًا موثوقًا، والله يعلم وأنت سؤالك جميل.

### a38-dawud-pharaoh-gulf #2 turn 2 [not_in_bank, ar, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** وش كان شغل النبي داود قبل ما يصير ملك؟

search_bank: {"question": "وش كان شغل النبي داود قبل ما يصير ملك؟", "topic": "prophets_story", "values": ["seeking-knowledge"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** هذا سؤال كبير، ولم أجد قصة شغل النبي داود عليه السلام في مكتبتي الآن. اسأل أبًا أو عالمًا تثق به، والله أعلم.

### a39-groceries-juice-levant #1 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** ساعدت ماما تحمل الأغراض بدون ما تطلب

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا لطف جميل منك. أحبّ هذا فيك؛ يساعد بلا طلب ويخفّف عن ماما.

### a39-groceries-juice-levant #1 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** وبعدين أخوي الصغير سكب العصير وما زعلت، ساعدته ينظف

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** هذا جميل جدًا، ما شاء الله. رأيتَ خطأً صغيرًا وبقيتَ هادئًا وساعدتَه، وهذا من الأخلاق الطيبة.

### a39-groceries-juice-levant #2 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** ساعدت ماما تحمل الأغراض بدون ما تطلب

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرّف جميل جدًا. أنتَ/أنتِ كنتَ لطيفًا ومبادرًا، وهذا يفرح القلب.

### a39-groceries-juice-levant #2 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** وبعدين أخوي الصغير سكب العصير وما زعلت، ساعدته ينظف

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا جميل جدًا! صبرتَ وساعدتَ أخاكَ، وهذا من الأخلاق الطيبة.

### a39-groceries-juice-levant #3 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** ساعدت ماما تحمل الأغراض بدون ما تطلب

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا لطف جميل منك. أحبّ هذا فيك؛ ساعدتَ أمك بطيب خاطر، وهذا من الخُلُق الحسن.

### a39-groceries-juice-levant #3 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** وبعدين أخوي الصغير سكب العصير وما زعلت، ساعدته ينظف

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا جميل جدًا. صبرتَ وساعدتَ أخاك تنظّف، وهذا لطف وحسن خُلُق.

