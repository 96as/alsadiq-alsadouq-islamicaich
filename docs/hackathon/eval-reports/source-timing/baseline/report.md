# Source timing: baseline

commit c466f5de (dirty), agent gpt-5.4-mini, 72 conversations x 2 runs (42 due, 69 not_due, 20 ask, 23 not_in_bank turns per run), channel voice, effort default, calls 445/2000, search_bank on the agent: True, prompt sha1 20ca964afa80,6080a13d5980,8a47e0a1ef39,eefea5548796, answered turns 308, errored runs 0 of 144

| metric | all | en | ar | 6-9 | 10-13 | better |
|---|---:|---:|---:|---:|---:|---|
| offered_when_due | 7% (6/84) | 5% (2/42) | 10% (4/42) | 0% (0/40) | 14% (6/44) | higher |
|   of which a card shown | 6% (5/84) | 5% (2/42) | 7% (3/42) | 0% (0/40) | 11% (5/44) | higher |
| creep | 1% (1/138) | 1% (1/74) | 0% (0/64) | 1% (1/80) | 0% (0/58) | lower |
|   of which a card shown | 0% (0/138) | 0% (0/74) | 0% (0/64) | 0% (0/80) | 0% (0/58) | lower |
| ask_served | 88% (35/40) | 90% (18/20) | 85% (17/20) | 69% (11/16) | 100% (24/24) | higher |
| not_in_bank_wrong_referral | 94% (43/46) | 96% (23/24) | 91% (20/22) | 83% (15/18) | 100% (28/28) | lower |
| not_in_bank_says_not_found | 54% (25/46) | 38% (9/24) | 73% (16/22) | 56% (10/18) | 54% (15/28) | higher |
| invented_content | 0% (0/308) | 0% (0/160) | 0% (0/148) | 0% (0/154) | 0% (0/154) | lower |

Card spacing (turns between two cards in one conversation, the later one not an ask): min gap, both unprompted: - (0 pairs); min gap incl. a card right after an asked card: 1 (4 pairs); pairs by gap: 1: 4. Cards shown in total: 51.
search_bank called by label: due 8/84, not_due 2/138, ask 40/40, not_in_bank 46/46.

Offered = a card shown or a source word in the reply (hadith, verse, ayah, surah, Quran; en + ar). Referral = parent, mom, dad, teacher, scholar, imam, sheikh, "ask ..." (en + ar). Not found = could not find / not in my library / don't have / don't know; ما لقيت / ما قدرت ألاقي / لم أجد / ما عندي / مكتبتي / ما أعرف. Invented = the raw reply attributes words to the Prophet or Allah beyond the licence (`hybrid_probes.unlicensed_attribution`).

## Failing turns

### e01-broken-window #1 turn 2 [due, en, 6-9]  due: no source offered

**Child:** I told my teacher the truth about the broken window, it was me who broke it

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was brave and honest. Truth is a strong choice, even when it feels hard. What did your teacher say?

### e01-broken-window #2 turn 2 [due, en, 6-9]  due: no source offered

**Child:** I told my teacher the truth about the broken window, it was me who broke it

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very brave and honest. I’m proud of you for telling the truth. Did your teacher stay calm?

### e02-copy-homework #1 turn 2 [due, en, 10-13]  due: no source offered

**Child:** my friend wants to copy my homework tomorrow, what should I do?

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That’s a tricky spot, and I’m glad you asked. It’s kinder to say no and offer to help them understand it instead, because copying isn’t honest.

### e02-copy-homework #2 turn 2 [due, en, 10-13]  due: no source offered

**Child:** my friend wants to copy my homework tomorrow, what should I do?

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That’s a tricky one. Be kind, but don’t help them copy; you can say no and offer to help them study after school instead.

### e03-brother-toys #1 turn 1 [due, en, 6-9]  due: no source offered

**Child:** my little brother keeps taking my toys and I want to yell at him

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That sounds really frustrating. Take one slow breath, and tell him, “Please ask first. Those are mine.” If he keeps doing it, ask a parent to help you.

### e03-brother-toys #2 turn 1 [due, en, 6-9]  due: no source offered

**Child:** my little brother keeps taking my toys and I want to yell at him

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That sounds really annoying. Try using a calm voice and saying, “Please give it back. That is my toy.” Can you tell a parent if he keeps taking them?

### e04-found-money #1 turn 2 [due, en, 6-9]  due: no source offered

**Child:** I found 20 riyals on the floor at school and nobody saw me pick it up. I gave it to the teacher

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very honest. You did a brave and good thing by giving it to the teacher.

### e04-found-money #2 turn 2 [due, en, 6-9]  due: no source offered

**Child:** I found 20 riyals on the floor at school and nobody saw me pick it up. I gave it to the teacher

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very honest and brave. You did a kind thing by giving it to the teacher.

### e05-hadith-honesty-then-cousin #1 turn 3 [due, en, 6-9]  due: no source offered

**Child:** my cousin lied to his mom and told me not to say anything, what should I do?

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That can feel tricky, and I’m glad you asked. It’s better not to keep a lie secret; tell a trusted adult, like your parent, and let them help.

### e05-hadith-honesty-then-cousin #2 turn 3 [due, en, 6-9]  due: no source offered

**Child:** my cousin lied to his mom and told me not to say anything, what should I do?

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That feels tricky. It is better not to keep a lie secret, and you can tell a trusted adult what happened. Did your cousin ask you to keep it secret from his mom?

### e07-verse-parents-dua-exam #1 turn 2 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar; not_in_bank: does not say it could not find it

**Child:** what's the du'a I should say before my exams?

search_bank: {"question": "what's the du'a I should say before my exams?", "topic": "worship", "values": ["trust in Allah", "patience"]}; items returned: 2; cards shown: none; guard: none

**Sadiq:** You can talk to Allah from your heart before the exam, and a parent can teach you a du'a. Try your best, then trust Allah with the result.

### e07-verse-parents-dua-exam #2 turn 2 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar; not_in_bank: does not say it could not find it

**Child:** what's the du'a I should say before my exams?

search_bank: {"question": "what's the du'a I should say before my exams?", "topic": "worship", "values": ["patience", "trust in Allah"]}; items returned: 2; cards shown: none; guard: none

**Sadiq:** You can talk to Allah from your heart, and a parent can teach you a du'a to use before exams. Trust Allah, do your best, and keep going bravely.

### e09-helping-sick-mom #1 turn 1 [due, en, 6-9]  due: no source offered

**Child:** my mom is sick and my dad is cooking dinner and doing all the cleaning, I helped him wash the plates

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That was very kind. Ma sha Allah, you helped your dad when your mom is sick. I hope she feels better soon, in sha Allah.

### e09-helping-sick-mom #1 turn 3 [ask, en, 6-9]  ask: no card shown

**Child:** is there a hadith about helping at home?

search_bank: {"question": "Is there a hadith about helping at home?", "topic": "hadith", "values": ["kindness", "helping family"]}; items returned: 0; cards shown: none; guard: none

**Sadiq:** That is a beautiful question, and I want to give you the exact answer. I could not find a checked hadith for that, so a parent can help you look together.

### e09-helping-sick-mom #2 turn 1 [due, en, 6-9]  due: no source offered

**Child:** my mom is sick and my dad is cooking dinner and doing all the cleaning, I helped him wash the plates

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That was kind and helpful. Ma sha Allah, you did a good thing by helping your dad, and I hope your mom gets well soon.

### e09-helping-sick-mom #2 turn 3 [ask, en, 6-9]  ask: no card shown

**Child:** is there a hadith about helping at home?

search_bank: {"question": "Is there a hadith about helping at home?", "topic": "hadith", "values": ["kindness", "helpfulness"]}; items returned: 0; cards shown: none; guard: none

**Sadiq:** That is a beautiful question. I could not find a checked hadith for that, so a parent can help with the exact answer.

### e10-yunus-whale #1 turn 1 [not_in_bank, en, 6-9]  not_in_bank: referral to parent/teacher/scholar; not_in_bank: does not say it could not find it

**Child:** how long was Prophet Yunus inside the whale?

search_bank: {"question": "how long was Prophet Yunus inside the whale?", "topic": "prophets_story", "values": ["patience", "trust in Allah"]}; items returned: 0; cards shown: none; guard: none

**Sadiq:** That is a beautiful question, and I want to give you the exact answer. A parent or teacher can tell you the full story properly.

### e10-yunus-whale #2 turn 1 [not_in_bank, en, 6-9]  not_in_bank: referral to parent/teacher/scholar; not_in_bank: does not say it could not find it

**Child:** how long was Prophet Yunus inside the whale?

search_bank: {"question": "how long was Prophet Yunus inside the whale?", "topic": "prophets_story", "values": null}; items returned: 0; cards shown: none; guard: none

**Sadiq:** That is a beautiful question. I want to give you the exact answer, so ask a parent together.

### e11-jealous-captain #1 turn 2 [due, en, 10-13]  due: no source offered

**Child:** this boy on my team keeps getting picked as captain and I'm jealous. I said something mean about him behind his back

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That sounds heavy, and I’m glad you told me. The brave next step is to say sorry and try to speak kindly about him, even if you still feel jealous.

### e11-jealous-captain #2 turn 2 [due, en, 10-13]  due: no source offered

**Child:** this boy on my team keeps getting picked as captain and I'm jealous. I said something mean about him behind his back

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** I’m glad you told me the truth. That kind of feeling happens, and the kind next step is to say sorry and not keep talking badly about him.

### e13-patience-sister-bathroom #1 turn 2 [due, en, 10-13]  due: no source offered

**Child:** I get so mad when my sister takes forever in the bathroom

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That sounds really annoying. Try taking one slow breath and saying, “I’m upset, but I can wait kindly.”

### e14-how-many-angels #1 turn 1 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar; not_in_bank: does not say it could not find it

**Child:** how many angels are there?

search_bank: {"question": "how many angels are there?", "topic": "creed", "values": null}; items returned: 0; cards shown: none; guard: none

**Sadiq:** That’s a beautiful question, and I’d love to give you the exact answer, but I need to ask a parent or trusted scholar with you. The unseen is one of those things we should not guess about.

### e14-how-many-angels #2 turn 1 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar; not_in_bank: does not say it could not find it

**Child:** how many angels are there?

search_bank: {"question": "how many angels are there?", "topic": "creed", "values": null}; items returned: 0; cards shown: none; guard: none

**Sadiq:** That’s a beautiful question, and I want to give you the exact answer, so it’s best to ask a parent or a trusted scholar together. The angels are part of the unseen, so I don’t want to guess.

### e15-new-kid-lunch #1 turn 1 [due, en, 6-9]  due: no source offered

**Child:** today at lunch a new kid had nobody to sit with so I sat with him

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very kind. You made a lonely kid feel seen.

### e15-new-kid-lunch #2 turn 1 [due, en, 6-9]  due: no source offered

**Child:** today at lunch a new kid had nobody to sit with so I sat with him

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That was very kind. Ma sha Allah, you made him feel welcome. Did he smile or talk to you?

### e16-grandma-questions #1 turn 1 [due, en, 6-9]  due: no source offered

**Child:** my grandma lives with us and she asks me the same questions again and again and sometimes I get annoyed

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That sounds tiring, and it is kind that you notice your own feelings. Try to answer gently, even if you feel annoyed, and if you need a break, ask a parent for help.

### e16-grandma-questions #2 turn 1 [due, en, 6-9]  due: no source offered

**Child:** my grandma lives with us and she asks me the same questions again and again and sometimes I get annoyed

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That sounds tiring, and it is okay to feel annoyed sometimes. Try to answer gently, because your grandma may just be forgetting, and your patience can be a very kind gift.

### e17-prophet-camel-then-animals #1 turn 1 [not_in_bank, en, 6-9]  not_in_bank: referral to parent/teacher/scholar; not_in_bank: does not say it could not find it

**Child:** what was the name of the Prophet's camel?

search_bank: {"question": "what was the name of the Prophet's camel?", "topic": "prophets_story", "values": null}; items returned: 0; cards shown: none; guard: none

**Sadiq:** That is a beautiful question. I want to give you the exact answer, so it is best to ask a parent together.

### e17-prophet-camel-then-animals #2 turn 1 [not_in_bank, en, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** what was the name of the Prophet's camel?

search_bank: {"question": "what was the name of the Prophet's camel?", "topic": "prophets_story", "values": null}; items returned: 0; cards shown: none; guard: none

**Sadiq:** That is a beautiful question. I could not find a checked answer, so I would love for you to ask a parent together so you get the exact name.

### e19-bad-word-laugh #1 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my friend said a bad word about another kid and I laughed. now I feel weird about it

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That uneasy feeling is worth listening to. You can make it right by not joining in next time and by being kind to that kid if you can.

### e19-bad-word-laugh #2 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my friend said a bad word about another kid and I laughed. now I feel weird about it

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That uneasy feeling is a good sign, and being honest about it is brave. You can tell your friend you don’t want to laugh at mean words next time, and if it fits, you can quietly be kinder to that kid today.

### e21-forgiveness-fight-sorry-first #2 turn 2 [due, en, 10-13]  due: no source offered

**Child:** should I be the first one to say sorry even if it wasn't my fault?

search_bank: {"question": "should I be the first one to say sorry even if it wasn't my fault?", "topic": "word_meaning", "values": ["forgiveness", "kindness"]}; items returned: 0; cards shown: none; guard: none

**Sadiq:** That’s a thoughtful question. I want to give you the exact answer, so it’s best to ask a parent together. If you want, I can help you plan a calm first sentence to say to your friend.

### e22-bilal-adhan #1 turn 1 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** who was Bilal and why did he give the adhan?

search_bank: {"question": "who was Bilal and why did he give the adhan?", "topic": "prophets_story", "values": ["truthfulness", "patience"]}; items returned: 0; cards shown: none; guard: none

**Sadiq:** That is a beautiful question. I couldn’t find a checked answer here, so a parent or teacher can tell you the full story properly.

### e22-bilal-adhan #2 turn 1 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** who was Bilal and why did he give the adhan?

search_bank: {"question": "who was Bilal and why did he give the adhan?", "topic": "prophets_story", "values": ["truthfulness", "patience"]}; items returned: 0; cards shown: none; guard: none

**Sadiq:** That’s a beautiful question, and I want to give you the exact answer. I couldn’t find a checked card for it, so a parent or teacher can tell you the full story properly.

### e23-shared-lunch #1 turn 1 [due, en, 6-9]  due: no source offered

**Child:** I shared my lunch with a kid who forgot his today

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very kind. You made his day a little easier, and that is a beautiful thing.

### e23-shared-lunch #2 turn 1 [due, en, 6-9]  due: no source offered

**Child:** I shared my lunch with a kid who forgot his today

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very kind. You shared and helped a friend who needed it, and that is a beautiful thing.

### e25-badr #1 turn 1 [not_in_bank, en, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** can you tell me what happened in the Battle of Badr?

search_bank: {"question": "What happened in the Battle of Badr?", "topic": "prophets_story", "values": null}; items returned: 0; cards shown: none; guard: none

**Sadiq:** That is a beautiful question, and I want to give you the exact answer. I could not find a checked story for it here, so please ask a parent or teacher to tell you the full story properly.

### e25-badr #2 turn 1 [not_in_bank, en, 6-9]  not_in_bank: does not say it could not find it

**Child:** can you tell me what happened in the Battle of Badr?

search_bank: {"question": "can you tell me what happened in the Battle of Badr?", "topic": "sirah", "values": ["truth", "courage"]}; items returned: 3; cards shown: [96]; guard: none

**Sadiq:** Assalamu alaikum. Badr was an early battle where the Muslims faced a much bigger group, and Allah helped them stay brave and strong. The Prophet ﷺ was very brave too .

**Sadiq (raw):** Assalamu alaikum. Badr was an early battle where the Muslims faced a much bigger group, and Allah helped them stay brave and strong. The Prophet ﷺ was very brave too {{card:96}}.

### e26-gossip-girl #1 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my friends are talking badly about a girl in our class and they want me to join in

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That feels tricky, and I’m glad you told me. It’s better not to join in; you can stay quiet or say something kind and change the subject.

### e26-gossip-girl #2 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my friends are talking badly about a girl in our class and they want me to join in

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That feels uncomfortable. You can stay kind and not join in, maybe say, I don’t want to talk about her like that. What’s a calm way you could change the subject?

### e27-gratitude-presentation #2 turn 2 [not_due, en, 6-9]  creep: source on a not_due turn

**Child:** I'm thankful for my dog

search_bank: {"question": "a verse or hadith about gratitude", "topic": "hadith", "values": ["gratitude"]}; items returned: 3; cards shown: none; guard: none

**Sadiq:** That is sweet. In simple words, the hadith on your screen means we thank Allah when something good happens, and it is good for us too.

**Sadiq (raw):** That is sweet. In simple words, the hadith on your screen means we thank Allah when something good happens, and it is good for us too. {{card:109}}

### e28-sister-doll #1 turn 2 [due, en, 6-9]  due: no source offered

**Child:** my sister cried because I broke her doll and I said sorry and gave her a hug

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was kind and brave. Saying sorry and giving a hug was a gentle choice. How did your sister feel after that?

### e28-sister-doll #2 turn 2 [due, en, 6-9]  due: no source offered

**Child:** my sister cried because I broke her doll and I said sorry and gave her a hug

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very kind. Saying sorry and giving a hug was a brave fix. Did she feel a little better after that?

### e29-travel-dua #1 turn 1 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** what is the du'a for travelling? we're going to grandma's tomorrow

search_bank: {"question": "what is the du'a for travelling? we're going to grandma's tomorrow", "topic": "worship", "values": ["gratitude", "trust in Allah"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** That’s nice travel plans. I couldn’t find a travel du’a card right now, but you can talk to Allah from your heart, and a parent can teach you the words later. You can also ask Allah to keep Grandma’s trip easy and happy.

### e29-travel-dua #2 turn 1 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** what is the du'a for travelling? we're going to grandma's tomorrow

search_bank: {"question": "what is the du'a for travelling?", "topic": "worship", "values": ["gratitude", "trust in Allah"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** Assalamu alaikum. I couldn’t find the travel du’a in my library right now, but a parent can teach you one. You can talk to Allah from your heart before you go, and may your trip to grandma’s be lovely, in sha Allah.

### e30-loud-neighbour #1 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my neighbour is really loud at night and I want to bang on his wall to be annoying back

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That feels really frustrating, but banging back will only make it worse. Try telling a parent or trusted adult, or use a calm note if you can, and keep your side quiet.

### e30-loud-neighbour #2 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my neighbour is really loud at night and I want to bang on his wall to be annoying back

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That would only make the night worse for both of you. Try a calmer step first, like telling a parent or asking him quietly to keep it down tomorrow.

### e31-lost-things-dua #1 turn 2 [not_in_bank, en, 6-9]  not_in_bank: referral to parent/teacher/scholar; not_in_bank: does not say it could not find it

**Child:** what's the du'a to say when I lose something?

search_bank: {"question": "what's the du'a to say when I lose something?", "topic": "word_meaning", "values": null}; items returned: 1; cards shown: [259]; guard: none

**Sadiq:** Dua is when we ask Allah for what we need, showing that we depend on Him. You can talk to Allah from your heart, and a parent can teach you words to say.

**Sadiq (raw):** Dua is when we ask Allah for what we need, showing that we depend on Him. {{card:259}} You can talk to Allah from your heart, and a parent can teach you words to say.

### e31-lost-things-dua #2 turn 2 [not_in_bank, en, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** what's the du'a to say when I lose something?

search_bank: {"question": "what's the du'a to say when I lose something?", "topic": "worship", "values": ["patience", "trust in Allah"]}; items returned: 2; cards shown: none; guard: none

**Sadiq:** I couldn’t find a du’a for losing something in my library. You can talk to Allah from your heart, and a parent can teach you a du’a to say.

### e32-how-many-prophets-blamed #1 turn 1 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar; not_in_bank: does not say it could not find it

**Child:** how many prophets are there?

search_bank: {"question": "how many prophets are there?", "topic": "word_meaning", "values": ["prophets"]}; items returned: 1; cards shown: [254]; guard: none

**Sadiq:** That’s a big question, and scholars explain it in more than one way. A prophet is a person Allah chose and sent revelation to ; a parent or a trusted scholar can tell you more.

**Sadiq (raw):** That’s a big question, and scholars explain it in more than one way. A prophet is a person Allah chose and sent revelation to {{card:254}}; a parent or a trusted scholar can tell you more.

### e32-how-many-prophets-blamed #1 turn 2 [due, en, 10-13]  due: no source offered

**Child:** my friend got blamed for something I did and I didn't say anything

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That sounds heavy, and I’m glad you told me. It was brave to speak up here; the kind next step is to tell the truth and set it right with your friend and a trusted adult if needed.

### e32-how-many-prophets-blamed #2 turn 1 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar; not_in_bank: does not say it could not find it

**Child:** how many prophets are there?

search_bank: {"question": "how many prophets are there?", "topic": "prophets_story", "values": null}; items returned: 0; cards shown: none; guard: none

**Sadiq:** That’s a beautiful question, and I want to give you the exact answer, so let’s ask a parent together.

### e32-how-many-prophets-blamed #2 turn 2 [due, en, 10-13]  due: no source offered

**Child:** my friend got blamed for something I did and I didn't say anything

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That sounds heavy, and I’m glad you told me. The kind next step is to tell the truth and, if you can, apologize to your friend and a trusted adult.

### e33-khadija #1 turn 1 [not_in_bank, en, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** who was Khadija?

search_bank: {"question": "who was Khadija?", "topic": "prophets_story", "values": ["honesty", "support"]}; items returned: 0; cards shown: none; guard: none

**Sadiq:** That is a beautiful question. I couldn’t find a checked card for Khadija, so I want to give the exact answer with a parent or teacher together.

### e33-khadija #2 turn 1 [not_in_bank, en, 6-9]  not_in_bank: referral to parent/teacher/scholar; not_in_bank: does not say it could not find it

**Child:** who was Khadija?

search_bank: {"question": "who was Khadija?", "topic": "prophets_story", "values": ["kindness", "truthfulness"]}; items returned: 0; cards shown: none; guard: none

**Sadiq:** That is a beautiful question. I want to give you the exact answer, so please ask a parent with you, and they can tell you the full story properly.

### e36-lent-pen #1 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my friend lost the best pen I lent him. I was upset but I told him it's ok

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That was very kind of you. You showed patience and mercy, and that is a strong friend move.

### e36-lent-pen #2 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my friend lost the best pen I lent him. I was upset but I told him it's ok

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That was very kind of you. Ma sha Allah, you were upset but still forgave him. Did he try to help look for the pen?

### e37-phone-sneak #1 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my mom took my phone as a punishment and I'm thinking about sneaking it back. what should I do?

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** I’m sorry, that feels frustrating. Sneaking it back would break trust; it’s better to wait and then calmly ask your mom what you can do to earn it back.

### e37-phone-sneak #2 turn 1 [due, en, 10-13]  due: no source offered

**Child:** my mom took my phone as a punishment and I'm thinking about sneaking it back. what should I do?

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** That feels frustrating. Don’t sneak it back; it will only make things messier. Try asking your mom when you can earn it back, and show her you can handle it better.

### e38-dawud-pharaoh #1 turn 1 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** how many plagues did Pharaoh get?

search_bank: {"question": "how many plagues did Pharaoh get?", "topic": "prophets_story", "values": ["patience", "truth"]}; items returned: 0; cards shown: none; guard: none

**Sadiq:** That’s a beautiful question, and I’d love to give you the exact answer with you, but I couldn’t find a verified card for it. A parent or teacher can tell you the full story properly.

### e38-dawud-pharaoh #1 turn 2 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar; not_in_bank: does not say it could not find it

**Child:** and what was Prophet Dawud's job before he was a king?

search_bank: {"question": "and what was Prophet Dawud's job before he was a king?", "topic": "prophets_story", "values": null}; items returned: 0; cards shown: none; guard: none

**Sadiq:** That’s a beautiful question, and I’d love to give you the exact answer, but I would rather ask a parent together so you hear it properly.

### e38-dawud-pharaoh #2 turn 1 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar; not_in_bank: does not say it could not find it

**Child:** how many plagues did Pharaoh get?

search_bank: {"question": "how many plagues did Pharaoh get?", "topic": "prophets_story", "values": null}; items returned: 0; cards shown: none; guard: none

**Sadiq:** That’s a beautiful question, and I want to give you the exact answer, so it’s best to ask a parent together. A parent or teacher can tell you the full story properly.

### e38-dawud-pharaoh #2 turn 2 [not_in_bank, en, 10-13]  not_in_bank: referral to parent/teacher/scholar; not_in_bank: does not say it could not find it

**Child:** and what was Prophet Dawud's job before he was a king?

search_bank: {"question": "What was Prophet Dawud's job before he was a king?", "topic": "prophets_story", "values": ["truthfulness"]}; items returned: 0; cards shown: none; guard: none

**Sadiq:** That’s a beautiful question, and I want to give you the exact answer, so I’d ask a parent together. A parent or teacher can tell you Prophet Dawud’s story properly.

### e39-groceries-juice #1 turn 1 [due, en, 6-9]  due: no source offered

**Child:** I helped my mom carry the groceries today without being asked

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was kind and helpful. I’m proud of you for noticing and helping your mom.

### e39-groceries-juice #1 turn 2 [due, en, 6-9]  due: no source offered

**Child:** then my little brother spilled juice everywhere and I didn't get angry, I just helped clean it

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very patient and kind. You helped clean up instead of getting angry, and that is a beautiful choice.

### e39-groceries-juice #2 turn 1 [due, en, 6-9]  due: no source offered

**Child:** I helped my mom carry the groceries today without being asked

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very kind and helpful. Your mom must have felt glad. What did you carry?

### e39-groceries-juice #2 turn 2 [due, en, 6-9]  due: no source offered

**Child:** then my little brother spilled juice everywhere and I didn't get angry, I just helped clean it

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** Ma sha Allah, that was very patient and kind. You chose help instead of anger, and that is lovely.

### a01-broken-cup-gulf #1 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** كسرت كاسة أمي وقلت لها الصدق إني أنا اللي كسرتها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** يا سلام عليك، هذا شجاع وجميل. قولك الصدق كان تصرّفًا طيبًا، وإن شاء الله أمك تقدّر أمانتك.

### a01-broken-cup-gulf #2 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** كسرت كاسة أمي وقلت لها الصدق إني أنا اللي كسرتها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا شجاع وجميل. قولك الصدق شيء قوي، وأمك ستعرف أنك كنت أمينًا. هل هي زعلت كثيرًا؟

### a02-found-wallet-levant #1 turn 2 [due, ar, 10-13]  due: no source offered

**Child:** رجعت المحفظة اللي لقيتها بالشارع لصاحبها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرّف جميل وأمين. فرحت لأنك رجّعتها لصاحبها؛ الأمانة شيء كبير.

### a02-found-wallet-levant #2 turn 2 [due, ar, 10-13]  due: no source offered

**Child:** رجعت المحفظة اللي لقيتها بالشارع لصاحبها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرّف أمين جدًا. أحبّ شجاعتك في ردّ الحق لأهله، هل فرح صاحبها؟

### a03-brother-toys-gulf #1 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** أخوي الصغير ياخذ ألعابي وابي أصارخ عليه

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** أفهم زعلك. خذ نفسًا واحدًا وقل لأحد الكبار في البيت ما يحدث، ثم قل لأخيك بهدوء: هذا لعبي، أرجعه من فضلك.

### a03-brother-toys-gulf #2 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** أخوي الصغير ياخذ ألعابي وابي أصارخ عليه

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** أفهم زعلك. خذ نفسًا واحدًا وقل له بهدوء: هذا لعبي، أرجعه الآن. وإذا ما وقف، نادِ ماما أو بابا.

### a04-copy-homework-levant #1 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** صاحبي بدو ينقل مني الوظيفة، شو أعمل؟

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** هذا مزعج، وأفهم إنك منزعج. احكِ له بهدوء إنك كنت تعبّت على الشغل، واطلب منه يترك لك حقك أو تتفقوا على الدور بينكم؛ والصدق والعدل أحسن.

### a04-copy-homework-levant #2 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** صاحبي بدو ينقل مني الوظيفة، شو أعمل؟

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** آه، هذا يوجع. جرّب تحكي معه بهدوء وتقول له إنك ما بتحبّ ينسب شغلك لنفسه، وإذا ما نفع، احكِ لمعلّم أو لشخص كبير بتثق فيه.

### a06-hadith-honesty-cheating-gulf #1 turn 3 [due, ar, 10-13]  due: no source offered

**Child:** زميلي في الفصل غش في الاختبار وأنا شفته، أقول للمعلمة؟

search_bank: {"question": "زميلي في الفصل غش في الاختبار وأنا شفته، أقول للمعلمة؟", "topic": "values", "values": ["صدق", "أمانة"]}; items returned: 0; cards shown: none; guard: none

**Sadiq:** هذا سؤال مهم يا صديقي. أريد أن أجيبك بدقة، لكن لا أستطيع الجزم هنا؛ الأفضل أن تسأل معلمتك أو أحد والديك اليوم.

### a06-hadith-honesty-cheating-gulf #2 turn 3 [due, ar, 10-13]  due: no source offered

**Child:** زميلي في الفصل غش في الاختبار وأنا شفته، أقول للمعلمة؟

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** هذا موقف صعب، وأنت شجاع لأنك سألت. الأفضل أن تخبر المعلمة بهدوء وبالصدق، من دون فضيحة أو سخرية، لأن الأمانة مهمة.

### a07-verse-parents-exam-dua-gulf #1 turn 2 [not_in_bank, ar, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** شو الدعاء اللي أقوله قبل الاختبار؟

search_bank: {"question": "شو الدعاء اللي أقوله قبل الاختبار؟", "topic": "worship", "values": ["trust in Allah", "calmness"]}; items returned: 0; cards shown: none; guard: none

**Sadiq:** سؤال جميل، لكن ما لقيت دعاءً موثوقًا جاهزًا عندي الآن. يمكنك أن تتكلم مع الله من قلبك قبل الاختبار، وإذا أحببت فاسأل أحد والديك ليعلّمك دعاءً مناسبًا.

### a07-verse-parents-exam-dua-gulf #2 turn 2 [not_in_bank, ar, 10-13]  not_in_bank: referral to parent/teacher/scholar; not_in_bank: does not say it could not find it

**Child:** شو الدعاء اللي أقوله قبل الاختبار؟

search_bank: {"question": "شو الدعاء اللي أقوله قبل الاختبار؟", "topic": "worship", "values": ["du'a", "trust in Allah"]}; items returned: 0; cards shown: none; guard: none

**Sadiq:** سؤال جميل، وأريد أن أعطيك الصيغة الدقيقة. اسأل أحد والديك ليعلّموك دعاءً مناسبًا، ويمكنك أن تتكلم مع الله من قلبك بما تريد.

### a09-helping-sick-mom-gulf #1 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** أمي تعبانة وأبوي ساعدها في البيت وأنا ساعدته بغسل الصحون

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا لطف جميل منك. لقد كنتَ مساعدًا ومهذبًا، وهذا يفرح القلب.

### a09-helping-sick-mom-gulf #1 turn 3 [ask, ar, 6-9]  ask: no card shown

**Child:** في حديث عن مساعدة الأهل؟

search_bank: {"question": "في حديث عن مساعدة الأهل؟", "topic": "hadith", "values": ["kindness", "family"]}; items returned: 0; cards shown: none; guard: none

**Sadiq:** سؤال جميل، وأريد أن أعطيك الجواب الصحيح بالضبط. لم أجد حديثًا موثوقًا هنا عن هذا، فاسألوا أحد الوالدين معًا.

### a09-helping-sick-mom-gulf #2 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** أمي تعبانة وأبوي ساعدها في البيت وأنا ساعدته بغسل الصحون

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا جميل جدًا. أنتَ كنتَ عونًا لأبيك، وهذا من الطيبة والبر. أتمنى لأمك الشفاء بسرعة، وإن شاء الله تتحسن قريبًا.

### a09-helping-sick-mom-gulf #2 turn 3 [ask, ar, 6-9]  ask: no card shown

**Child:** في حديث عن مساعدة الأهل؟

search_bank: {"question": "في حديث عن مساعدة الأهل؟", "topic": "hadith", "values": ["helping family", "kindness"]}; items returned: 0; cards shown: none; guard: none

**Sadiq:** سؤال جميل، لكني لم أجد حديثًا مُتحققًا عنه هنا. اسألْ أحد والديك، وإن أحببتَ أبحث معك عن جواب أدق.

### a10-yunus-whale-levant #2 turn 1 [not_in_bank, ar, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** كم سنة قعد النبي يونس بطن الحوت؟

search_bank: {"question": "كم سنة قعد النبي يونس بطن الحوت؟", "topic": "prophets_story", "values": null}; items returned: 0; cards shown: none; guard: none

**Sadiq:** سؤال جميل جدًا، وأحب أن أعطيك الجواب الدقيق، لكن لم أجد عندي شيئًا موثوقًا هنا. اسأل أحد والديك أو معلّمك، وهم يقدرون يروون لك القصة كاملة.

### a11-backbiting-teammate-gulf #1 turn 2 [due, ar, 10-13]  due: no source offered

**Child:** قلت كلام مب زين عن واحد من الفريق من ورا ظهره والحين أحس بالذنب

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** آه، هذا شعور ثقيل، وأحس فيك. الاعتذار له والكلام الطيب عنه بعد كذا خطوة جميلة، وإذا تقدر تصلحها بكلمة صادقة اليوم يكون هذا شجاع.

### a11-backbiting-teammate-gulf #2 turn 2 [due, ar, 10-13]  due: no source offered

**Child:** قلت كلام مب زين عن واحد من الفريق من ورا ظهره والحين أحس بالذنب

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** يا حبيبي، شعورك بالذنب يدل إن قلبك حي. الاعتذار له ومصافحته بكلمة طيبة خطوة شجاعة، وبإذن الله يخفّ ثقل قلبك؛ هل تبي أساعدك بصيغة اعتذار قصيرة؟

### a13-patience-bathroom-levant #2 turn 2 [due, ar, 10-13]  due: no source offered

**Child:** بنفعل كتير لما أختي بتتأخر بالحمام

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** أفهمك، الانتظار يزعج أحيانًا. جرّب تتنفس بهدوء وتعدّ شوي، وذكّر نفسك أن أختك أيضًا تحتاج وقتها، وما شاء الله على صبرك إذا قدرت تهدأ.

### a14-how-many-angels-gulf #1 turn 1 [not_in_bank, ar, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** كم عدد الملائكة؟

search_bank: {"question": "كم عدد الملائكة؟", "topic": "afterlife", "values": null}; items returned: 0; cards shown: none; guard: none

**Sadiq:** سؤال جميل، وأحب أن أعطيك الجواب الدقيق. ما وجدتُ جوابًا موثوقًا في المكتبة هنا، فنسأل أحد الوالدين أو معلّمًا معًا.

### a14-how-many-angels-gulf #2 turn 1 [not_in_bank, ar, 10-13]  not_in_bank: referral to parent/teacher/scholar; not_in_bank: does not say it could not find it

**Child:** كم عدد الملائكة؟

search_bank: {"question": "كم عدد الملائكة؟", "topic": "creed", "values": null}; items returned: 0; cards shown: none; guard: none

**Sadiq:** سؤال جميل، وأريد أن أعطيك جوابًا دقيقًا. هذا من الأمور التي يسأل عنها الطفل مع والديه أو مع شخصٍ عالم موثوق، لأنني لا أريد أن أظنّ أو أُخمّن.

### a15-new-kid-levant #1 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** اليوم بالمدرسة في ولد جديد ما حدا قعد معه وأنا قعدت معه

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا لطف جميل منك. جعلت الولد الجديد لا يشعر بالوحدة، وهذا شيء طيب جدًا. هل ابتسم لك أو تكلم معك؟

### a15-new-kid-levant #2 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** اليوم بالمدرسة في ولد جديد ما حدا قعد معه وأنا قعدت معه

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا لطف جميل منك. لقد جعلته لا يشعر بالوحدة، وهذا شيء طيب جدًا.

### a16-grandma-repeats-gulf #1 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** جدتي عايشة معنا وتعيد نفس الأسئلة وأحيانا أنزعج منها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** أفهمك، هذا يزعج أحيانًا. جرّب أن تجيبها بهدوء مرة أخرى، فبرّ الجدة كلام جميل. هل تريد أن أساعدك بجملة لطيفة تقولها لها؟

### a16-grandma-repeats-gulf #2 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** جدتي عايشة معنا وتعيد نفس الأسئلة وأحيانا أنزعج منها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** آه، هذا يقدر يضايق أحيانًا. جرّب ترد بلطف مرة ثانية، لأن الكبير إذا كرر السؤال قد يكون ناسيًا أو محتاجًا طمأنة، والكلمة الطيبة تفرح القلب.

### a17-prophet-camel-then-animals-levant #1 turn 1 [not_in_bank, ar, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** شو اسم ناقة النبي؟

search_bank: {"question": "شو اسم ناقة النبي؟", "topic": "prophets_story", "values": null}; items returned: 0; cards shown: none; guard: none

**Sadiq:** سؤال جميل. ما لقيت جوابًا موثوقًا هنا، وأحب أن أقول لك الجواب الدقيق مع والدك أو والدتك.

### a17-prophet-camel-then-animals-levant #2 turn 1 [not_in_bank, ar, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** شو اسم ناقة النبي؟

search_bank: {"question": "شو اسم ناقة النبي؟", "topic": "prophets_story", "values": ["respect for the Prophet ﷺ"]}; items returned: 0; cards shown: none; guard: none

**Sadiq:** سؤال جميل يا حبيبي. ما لقيت جوابًا موثوقًا عندي هنا، وأحب أن تقولها مع أحد والديك أو تسأل معلمًا.

### a17-prophet-camel-then-animals-levant #2 turn 2 [ask, ar, 6-9]  ask: no card shown

**Child:** طيب بدي حديث عن الرفق بالحيوان

search_bank: {"question": "حديث عن الرفق بالحيوان", "topic": "hadith", "values": ["الرفق بالحيوان", "الرحمة"]}; items returned: 3; cards shown: none; guard: none

**Sadiq:** ما لقيت حديثًا عن الرفق بالحيوان في البطاقات هنا. إذا أحببت، أقدر أبحث لك عن حديث قريب عن الرحمة.

### a19-bad-word-laugh-levant #1 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** صاحبي حكى كلمة سيئة عن ولد وأنا ضحكت وهلأ حاسس شي مش منيح

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** أحسن أنك حسّيت بهالشي وقلتَه، هذا يدل على قلب صاحي. ممكن تروح تحكي لصاحبك بلطف إنك ما بدك تضحك على الولد، وإذا قدرت صحّحها مع الولد بكلمة طيبة.

### a19-bad-word-laugh-levant #2 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** صاحبي حكى كلمة سيئة عن ولد وأنا ضحكت وهلأ حاسس شي مش منيح

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** أفهمك، هذا شعور مزعج. جميل أنك انتبهت لخطأك بسرعة، وتقدر تصلّحه بأن تقول لصاحبك إنك ما بدك تضحك على الكلام السيئ، وإذا قدرت اعتذر للولد.

### a22-bilal-gulf #1 turn 1 [not_in_bank, ar, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** من هو بلال وليش كان يأذن؟

search_bank: {"question": "من هو بلال وليش كان يأذن؟", "topic": "prophets_story", "values": ["truthfulness", "patience"]}; items returned: 0; cards shown: none; guard: none

**Sadiq:** سؤال جميل يا صديقي، وأحب أن أعطيك الجواب الدقيق. لم أجد شيئًا موثَّقًا هنا، فالأفضل أن تسأل أحد والديك أو معلّمك ليحكيه لك كاملًا بطريقة صحيحة.

### a22-bilal-gulf #2 turn 1 [not_in_bank, ar, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** من هو بلال وليش كان يأذن؟

search_bank: {"question": "من هو بلال وليش كان يأذن؟", "topic": "prophets_story", "values": ["truthfulness", "patience"]}; items returned: 0; cards shown: none; guard: none

**Sadiq:** سؤال جميل، وأحب أن أقول لك الجواب الدقيق. لم أجد في المكتبة الموثوقة هنا بطاقة جاهزة عن بلال، فالأفضل أن يسألها لك أحد الوالدين أو المعلم ليحكي لك القصة كاملة.

### a23-shared-sandwich-levant #1 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** شاركت سندويشتي مع ولد نسي الأكل

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا لطف جميل منك. أنت كنت رحيمًا ومشاركًا، وهذا يفرح القلب.

### a23-shared-sandwich-levant #2 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** شاركت سندويشتي مع ولد نسي الأكل

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا لطف جميل. لقد فعلت خيرًا ومشاركة الطعام شيء طيب جدًا.

### a25-badr-levant #1 turn 1 [not_in_bank, ar, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** احكيلي شو صار بغزوة بدر

search_bank: {"question": "احكيلي شو صار بغزوة بدر", "topic": "prophets_story", "values": null}; items returned: 0; cards shown: none; guard: none

**Sadiq:** سؤال جميل. ما لقيت جوابًا مُتحققًا هنا، وأحب أن تسمع القصة الصحيحة من والدك أو والدتك.

### a25-badr-levant #2 turn 1 [not_in_bank, ar, 6-9]  not_in_bank: referral to parent/teacher/scholar

**Child:** احكيلي شو صار بغزوة بدر

search_bank: {"question": "احكيلي شو صار بغزوة بدر", "topic": "prophets_story", "values": null}; items returned: 0; cards shown: none; guard: none

**Sadiq:** سؤال جميل، وأحب أعطيك الجواب الدقيق. ما لقيت عندي قصة موثوقة لها الآن، فالأفضل تسألها مع أحد والديك أو معلّمك عشان تسمعها كاملة وصحيحة.

### a26-gossip-girl-gulf #1 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** ربعي يتكلمون عن بنت في الفصل بالسوء وياخذوني معهم

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** هذا مؤلم، وموقفك يحتاج شجاعة. لا تمشِ معهم في الكلام الجارح، وغيّر الموضوع أو ابتعد بهدوء؛ الكلمة الطيبة أحسن.

### a26-gossip-girl-gulf #2 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** ربعي يتكلمون عن بنت في الفصل بالسوء وياخذوني معهم

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** أفهمك، هذا يضايق القلب. لا تشاركهم في الغيبة، وقل كلمة طيبة أو اسكت وابتعد بلطف؛ هذا أحسن لك ولها.

### a28-sister-doll-gulf #1 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** أختي بكت لأني كسرت دميتها وقلت لها آسف وعانقتها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرّف جميل وشجاع. أنت أصلحت الخطأ بلطف، وهذا يفرح القلب. كيف شعرت أختك بعد العناق؟

### a28-sister-doll-gulf #2 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** أختي بكت لأني كسرت دميتها وقلت لها آسف وعانقتها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا تصرّف جميل جدًا. أنت كنت صادقًا ولطيفًا، واعتذارك وعناقك طيّبان القلب. كيف أصبحت أختك الآن؟

### a29-travel-dua-levant #1 turn 1 [not_in_bank, ar, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** شو دعاء السفر؟ بكرة رايحين عند ستي

search_bank: {"question": "شو دعاء السفر؟", "topic": "worship", "values": ["travel", "du'a"]}; items returned: 0; cards shown: none; guard: none

**Sadiq:** سؤال جميل، وبكرة إن شاء الله رحلة حلوة عند ستك. ما لقيت دعاءً موثوقًا هنا، فالأفضل تسألوا ماما أو بابا ليعلّموك الدعاء الصحيح، وتقدر تقول لربنا من قلبك بالطريقة اللي تعرفها.

### a29-travel-dua-levant #2 turn 1 [not_in_bank, ar, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** شو دعاء السفر؟ بكرة رايحين عند ستي

search_bank: {"question": "شو دعاء السفر؟ بكرة رايحين عند ستي", "topic": "worship", "values": ["gratitude", "trust in Allah"]}; items returned: 1; cards shown: none; guard: none

**Sadiq:** ما لقيت دعاء السفر من المصدر الموثوق عندي الآن. تقدرين تطلبينه من ماما أو ستي، وتقولين لربنا من قلبك قبل الطريق.

### a30-loud-neighbour-gulf #1 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** جارنا صوته عالي بالليل وابي أخبط على الجدار أزعجه

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** أفهم انزعاجك، لكن لا تخبط الجدار ولا ترد بإزعاج. الأفضل تكلم أحد من أهلك بهدوء أو تشتكي بطريقة محترمة، وإذا أحببت أساعدك بكلام قصير تقوله لهم.

### a30-loud-neighbour-gulf #2 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** جارنا صوته عالي بالليل وابي أخبط على الجدار أزعجه

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** أفهم أنك منزعج. الأفضل لا ترد بالأذى أو الإزعاج، وجرب تقول لولي أمرك أو تخفف الضجيج بهدوء بدلًا من ضرب الجدار.

### a31-lost-things-dua-gulf #1 turn 1 [not_in_bank, ar, 6-9]  not_in_bank: referral to parent/teacher/scholar; not_in_bank: does not say it could not find it

**Child:** شو الدعاء إذا ضيعت شي؟

search_bank: {"question": "شو الدعاء إذا ضيعت شي؟", "topic": "worship", "values": ["remembering Allah when something is lost"]}; items returned: 0; cards shown: none; guard: none

**Sadiq:** سؤال جميل، وأريد أعطيك الجواب الصحيح تمامًا. خلّينا نسأل أحد الوالدين معًا، لأنهم يعرفون أفضل.

### a31-lost-things-dua-gulf #2 turn 1 [not_in_bank, ar, 6-9]  not_in_bank: does not say it could not find it

**Child:** شو الدعاء إذا ضيعت شي؟

search_bank: {"question": "شو الدعاء إذا ضيعت شي؟", "topic": "word_meaning", "values": []}; items returned: 1; cards shown: [259]; guard: none

**Sadiq:** أقدر قلقك. لا أستطيع أن أقول لك صيغة دعاء معيّنة هنا، لكن يمكنك أن تتكلم مع الله من قلبك وتطلب ما ضاع منك، والدعاء هو أن نطلب من الله ما نحتاجه هل تريد أن أساعدك تفكر أين رأيته آخر مرة؟

**Sadiq (raw):** أقدر قلقك. لا أستطيع أن أقول لك صيغة دعاء معيّنة هنا، لكن يمكنك أن تتكلم مع الله من قلبك وتطلب ما ضاع منك، والدعاء هو أن نطلب من الله ما نحتاجه {{card:259}} هل تريد أن أساعدك تفكر أين رأيته آخر مرة؟

### a32-how-many-prophets-blamed-levant #1 turn 1 [not_in_bank, ar, 10-13]  not_in_bank: referral to parent/teacher/scholar; not_in_bank: does not say it could not find it

**Child:** كم عدد الأنبياء؟

search_bank: {"question": "كم عدد الأنبياء؟", "topic": "creed", "values": ["الأنبياء"]}; items returned: 0; cards shown: none; guard: none

**Sadiq:** سؤال جميل، وأحب أن أعطيك جوابًا دقيقًا. هذا من الأسئلة التي يوضحها لك أحد والديك أو شخصٌ موثوق يعرفها جيدًا.

### a32-how-many-prophets-blamed-levant #1 turn 2 [due, ar, 10-13]  due: no source offered

**Child:** صاحبي أخد اللوم على شي أنا عملته وأنا ما حكيت شي

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** يا قلبي، هذا يوجع. من الشجاعة أن تقول الحقيقة بهدوء وتصلّح الخطأ بدل أن يظل صاحبك وحده يتحملها. هل تريد أن أساعدك بكلمات قصيرة تقولها له؟

### a32-how-many-prophets-blamed-levant #2 turn 1 [not_in_bank, ar, 10-13]  not_in_bank: referral to parent/teacher/scholar; not_in_bank: does not say it could not find it

**Child:** كم عدد الأنبياء؟

search_bank: {"question": "كم عدد الأنبياء؟", "topic": "word_meaning", "values": null}; items returned: 2; cards shown: [254]; guard: none

**Sadiq:** هذا سؤال كبير، والنبي إنسان اختاره الله وأوحى إليه بشرع . وعدد الأنبياء بالتحديد شيء يشرحه العلماء، فاسأل أحد والديك أو عالمًا موثوقًا.

**Sadiq (raw):** هذا سؤال كبير، والنبي إنسان اختاره الله وأوحى إليه بشرع {{card:254}}. وعدد الأنبياء بالتحديد شيء يشرحه العلماء، فاسأل أحد والديك أو عالمًا موثوقًا.

### a32-how-many-prophets-blamed-levant #2 turn 2 [due, ar, 10-13]  due: no source offered

**Child:** صاحبي أخد اللوم على شي أنا عملته وأنا ما حكيت شي

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** هذا مؤلم، وأنت شجاع لأنك قلتها. الأفضل أن تقول الحقيقة بلطف اليوم، لأن الصدق يحميك ويحمي صاحبك؛ هل تريد أن أصيغ لك جملة قصيرة تقولها له؟

### a36-helped-old-neighbour-gulf #1 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** اليوم ساعدت جارتنا العجوز تشيل أغراضها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا عمل طيب جدًا. أنت كنت رحيمًا ومساعدًا، وهذا يفرح القلب.

### a36-helped-old-neighbour-gulf #2 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** اليوم ساعدت جارتنا العجوز تشيل أغراضها

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا عمل طيب وجميل. أحببتُ لطفك مع جارتكم العجوز؛ هل كانت الأغراض كثيرة؟

### a37-brother-window-levant #2 turn 1 [due, ar, 10-13]  due: no source offered

**Child:** أخي الكبير قلي ما تقول لماما إنو كسر الشباك، شو أعمل؟

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** أحسن شيء تقول الحقيقة بهدوء، حتى لو كنت خايف. إذا أخوك كسر الشباك، لا تغطي عليه؛ قل لماما بما تعرفه فقط، وخلّها تحلها.

### a38-dawud-pharaoh-gulf #1 turn 1 [not_in_bank, ar, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** كم عدد الضربات اللي جت على فرعون؟

search_bank: {"question": "كم عدد الضربات اللي جت على فرعون؟", "topic": "quran", "values": null}; items returned: 0; cards shown: none; guard: none

**Sadiq:** سؤال جميل، وأريد لك الجواب الدقيق، لكن لم أجد شيئًا موثوقًا هنا، فاسأل أحد والديك معًا.

### a38-dawud-pharaoh-gulf #1 turn 2 [not_in_bank, ar, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** وش كان شغل النبي داود قبل ما يصير ملك؟

search_bank: {"question": "وش كان شغل النبي داود قبل ما يصير ملك؟", "topic": "prophets_story", "values": ["honesty", "patience"]}; items returned: 0; cards shown: none; guard: none

**Sadiq:** سؤال جميل، وأريد لك الجواب الدقيق، لكن لم أجد شيئًا موثوقًا هنا، فاسأل أحد والديك أو معلّمك ليحكوه لك كاملًا.

### a38-dawud-pharaoh-gulf #2 turn 1 [not_in_bank, ar, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** كم عدد الضربات اللي جت على فرعون؟

search_bank: {"question": "كم عدد الضربات اللي جت على فرعون؟", "topic": "quran", "values": null}; items returned: 0; cards shown: none; guard: none

**Sadiq:** سؤال جميل، وأريد أن أعطيك الجواب الدقيق، لكن لم أجد نصًا موثوقًا هنا. اسأل أحد والديك معك، وإذا أردت أقدر أساعدك تصيغ السؤال لهم.

### a38-dawud-pharaoh-gulf #2 turn 2 [not_in_bank, ar, 10-13]  not_in_bank: referral to parent/teacher/scholar

**Child:** وش كان شغل النبي داود قبل ما يصير ملك؟

search_bank: {"question": "وش كان شغل النبي داود قبل ما يصير ملك؟", "topic": "prophets_story", "values": ["honesty", "hard work"]}; items returned: 0; cards shown: none; guard: none

**Sadiq:** سؤال جميل، وأحب أعطيك الجواب الدقيق، لكن ما لقيت جوابًا موثوقًا هنا. اسأل أحد والديك معك، وإذا أردت أقدر أساعدك تصيغ السؤال لهم.

### a39-groceries-juice-levant #1 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** ساعدت ماما تحمل الأغراض بدون ما تطلب

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا لطف جميل منك. أمك ستفرح بك كثيرًا.

### a39-groceries-juice-levant #1 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** وبعدين أخوي الصغير سكب العصير وما زعلت، ساعدته ينظف

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** أحسنت، هذا تصرّف طيب جدًا. صبرك ومساعدتك له شيء جميل، وكأنك كنت أخًا كبيرًا رحيمًا.

### a39-groceries-juice-levant #2 turn 1 [due, ar, 6-9]  due: no source offered

**Child:** ساعدت ماما تحمل الأغراض بدون ما تطلب

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا لطف جميل منك. أحسنتَ بمساعدة ماما من غير أن تطلب.

### a39-groceries-juice-levant #2 turn 2 [due, ar, 6-9]  due: no source offered

**Child:** وبعدين أخوي الصغير سكب العصير وما زعلت، ساعدته ينظف

search_bank: not called; items returned: 0; cards shown: none; guard: none

**Sadiq:** ما شاء الله، هذا خلق جميل منك. كنتَ هادئًا وساعدتَ أخاك، وهذا طيب جدًا.

