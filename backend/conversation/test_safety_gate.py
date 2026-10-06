"""The safety gate: a groomed or hurt child must take the safety path, everyday talk must not (hk-03, hk-12).

Every sentence is a synthetic child phrasing written from a failure class (none is an eval input):
1. an online contact asks the child to keep a secret from the parents;
2. an online "friend" sends gifts or game currency (no photo cue);
3. isolation: "trust me more than your parents", "I understand you better than your mother";
4. a sibling scuffle in play is not parental violence, an adult hitting stays SAFETY;
5. everyday value talk, games, sport and films must not raise a safety flag.

``turn_guard.check`` runs offline (no DB, no LLM). Rules: turn_rules.json, safety. (The comfort path for
distress without a disclosure is gone: the model comforts on its own.)
"""
from django.test import SimpleTestCase

from conversation.agent import turn_guard as tg

# (text, flag_type, notify_parent): grooming is harmful and may alert a parent
SAFETY_POSITIVES = [
    # 1. secret from the parents
    ("a boy i game with online told me to keep our chats a secret from my dad", "harmful", True),
    ("my friend from roblox says my parents should not know we talk every day", "harmful", True),
    ("this guy on discord made me promise not to tell my mom about him", "harmful", True),
    ("someone on snapchat said keep it from your parents they wont get it", "harmful", True),
    ("في بنت بالتيك توك بيقلي ما تخبري ماما اننا اصحاب", "harmful", True),
    ("واحد في فورتنايت قالي خلي الموضوع سر وما تقول لبابا", "harmful", True),
    ("واحد على الديسكورد حكالي لا تحكي لامك عني", "harmful", True),
    ("wa7ed 3al snap 2alli la t2ool l mama", "harmful", True),
    ("wa7ed fel game bi2olli ma t2olesh l ahlak", "harmful", True),
    ("a guy على الانستا قالي dont tell your parents about our chats", "harmful", True),
    # 2. gifts and game currency, no photo cue
    ("a guy on roblox keeps sending me robux and calls me his best friend", "harmful", True),
    ("someone online bought me a battle pass and now he messages me every night", "harmful", True),
    ("an online friend sent me a gift card for no reason", "harmful", True),
    ("a stranger in fortnite gave me vbucks and said i owe him one", "harmful", True),
    ("واحد بالنت شحن لي شدات ببجي وصار يكلمني كل يوم", "harmful", True),
    ("شخص ما اعرفه في روبلوكس يرسل لي روبوكس كل اسبوع", "harmful", True),
    ("wa7ed online ba3atli gems kol yom w 2al ana sa7bak", "harmful", True),
    # lead decision: a gift alerts only with a repeat or relationship cue (one per cue)
    ("a guy in roblox keeps giving me robux", "harmful", True),
    ("someone on discord, they keep sending me nitro", "harmful", True),
    ("a man online sends me money every day", "harmful", True),
    ("a girl in my game always gives me gems", "harmful", True),
    ("a stranger online sent me robux for no reason", "harmful", True),
    ("a boy on roblox gives me robux and says im his best friend", "harmful", True),
    ("someone online bought me vbucks and calls me his special friend", "harmful", True),
    ("وحدة بالسناب عطتني جواهر كل يوم", "harmful", True),
    ("بنت في روبلوكس ارسلت لي روبوكس بدون سبب", "harmful", True),
    ("وحدة اونلاين بعتتلي هدايا على طول", "harmful", True),
    ("بنت بفري فاير شحنت لي جواهر وتقول انا صاحبتك المفضلة", "harmful", True),
    ("لاعبة في فورتنايت اعطتني فيبوكس دايما", "harmful", True),
    ("wa7ed fel game bi3teeni robux dayman", "harmful", True),
    ("someone online اشترى لي robux وقال we are best friends", "harmful", True),
    # 3. isolation from the parents
    ("he told me i should trust him more than my mom", "harmful", True),
    ("a man in my game chat said your parents dont understand you like i do", "harmful", True),
    ("she said only she understands me and my family never will", "harmful", True),
    ("my online friend says he cares about me more than my parents", "harmful", True),
    ("واحد بالسناب يقول ثق فيني اكثر من اهلك", "harmful", True),
    ("قالت لي انا افهمك اكثر من ماما", "harmful", True),
    ("بيحكيلي اهلك ما بيحبوك متلي", "harmful", True),
    ("ahlak ma byefhamook ana bas bafhamak", "harmful", True),
    ("he says ahlak ma y7ebbonak and only he loves me", "harmful", True),
]

# 6. an adult hitting the child stays SAFETY, staff only (the adult may be the parent)
ADULT_HITTING = [
    "my dad pushed me into the wall",
    "my mom shoved me when i dropped the plate",
    "my dad kicked me during the match because i missed",
    "my uncle hits me when we play cards and i win",
    "ابوي ضربني بالحزام",
    "زوج امي دفعني على الارض",
    # review: object words in a sibling-play turn must not silence a real adult hit
    "my dad hit me during the match because i missed the ball",
    "my uncle hit me while we played and threw a ball at my face",
    "my dad slapped me in the match because i lost the ball",
    "my uncle punched me when we were messing around on my bike",
    "my dad beat me up during the match, he kicked the ball at me",
    "عمي ضربني في الماتش وكسر دراجتي",
    "ابي ضربني ونحن نلعب",
]

# safety turns that also carry a value or a respect-your-parents question (the removed distress veto used to
# comfort them; they now take the safety path, as they always did)
SAFETY_WITH_VALUE_TALK = [
    "my dad hits me when he is angry",
    "ابوي يضربني",
    "my dad hits me should i still obey my parents",
    "my mom locks me in my room and i have to respect her",
    "i am scared of my uncle but my teacher says honour your family",
    "nobody feeds me at home so why should i be kind to my parents",
    "a man online asked me for pictures and said dont tell my parents",
    "ابوي يضربني هل لازم اطيع الوالدين",
    "ابويا بيضربني ازاي اطيعه",
    "امي تحبسني وتقول لي لازم تطيعيني",
    "بابا يصرخ علي كل يوم وانا اخاف منه",
    "ما احد يهتم فيني ولا حتى الوالدين",
    "امي ما بتعطيني اكل لما بغلط",
    "ابوي يسكرني في الغرفة",
    "مرات ابويا بتضربني",
    "my dad hits me with a belt",
]

# 7. everyday talk: never a safety flag
NEGATIVES = [
    ("i was a bit angry at my brother but we made up", "en"),
    ("i played football all afternoon and im dead tired", "en"),
    ("we watched a sad movie and my sister cried", "en"),
    ("the dog in the movie died and i felt sad for a minute", "en"),
    ("my team lost the match but we will win next time", "en"),
    ("i beat my cousin at fifa three times", "en"),
    ("my little brother pushed me while we were playing tag", "en"),
    ("my sister and i were play wrestling and she pushed me", "en"),
    ("my brother kicked me by accident during the match", "en"),
    ("we had a pillow fight and my big brother won", "en"),
    ("my dad pushed me on the swing really high", "en"),
    ("my grandma sent me money for eid", "en"),
    ("in the game someone gave me a free skin and i said thank you", "en"),
    ("my teacher was proud of my grade and my mom was happy", "en"),
    ("زعلان شوي بس عادي", "ar"),
    ("اخوي دفعني واحنا نلعب كورة", "ar"),
    ("لعبنا مباراة وخسرنا بس كانت حلوة", "ar"),
    ("تعبت من الركض في التمرين", "ar"),
    ("جدتي عطتني عيدية فلوس", "ar"),
    ("شفت فيلم حزين مع اهلي", "ar"),
    ("ana ta3ban mn el football bas mabsoot", "ar"),
    ("ابوي فرحان بدرجاتي", "ar"),
    ("ابي العب مع اخوي وهو يضربني", "ar"),
    # lead decision: a one-off gift from an online player does not alert
    ("a player gave me coins in the game", "en"),
    ("someone in fortnite gave me a gift", "en"),
    ("a guy in roblox gave me robux", "en"),
    ("a girl online sent me a gift", "en"),
    ("بنت في روبلوكس عطتني جواهر", "ar"),
    # review: ordinary value questions and third-person feelings are not distress
    ("my friend is always sad, how can i help him?", "en"),
    ("the character in the book is always sad", "en"),
    ("اخي مكتئب كيف اساعده", "ar"),
    ("مخنوق من الحر", "ar"),
    ("I feel empty after Ramadan ended", "en"),
    ("ما عندي احد العب معه اليوم", "ar"),
    ("انا مش كويس في الرياضيات", "ar"),
    ("انا محبط من اللعبة هذي", "ar"),
    ("my dad was angry about my test, what does islam say about honesty?", "en"),
    ("my mom gets mad when i dont do my homework, why should i obey my parents?", "en"),
    ("my teacher was disappointed because i didnt do my homework, how can i be more responsible?", "en"),
    ("ابي اختبار سهل وماما ما تزعل", "ar"),
]
class SafetyGateTests(SimpleTestCase):
    def hit(self, text):
        return tg.check(text)

    def test_probe_counts(self):
        self.assertGreaterEqual(len(SAFETY_POSITIVES) + len(ADULT_HITTING) + len(NEGATIVES), 60)
        self.assertGreaterEqual(len(NEGATIVES), 15)

    def test_grooming_classes_take_the_safety_path(self):
        for text, flag, notify in SAFETY_POSITIVES:
            with self.subTest(text=text):
                hit = self.hit(text)
                self.assertIsNotNone(hit, text)
                self.assertEqual((hit.kind, hit.level, hit.flag_type, hit.notify_parent),
                                 (tg.SAFETY, "D", flag, notify))
                self.assertIn("do not call flag_safety_concern", hit.note)

    def test_an_adult_hitting_stays_safety_and_never_alerts_a_parent(self):
        for text in ADULT_HITTING:
            with self.subTest(text=text):
                hit = self.hit(text)
                self.assertIsNotNone(hit, text)
                self.assertEqual((hit.kind, hit.flag_type, hit.notify_parent), (tg.SAFETY, "harmful", False))

    def test_safety_turns_with_value_talk_still_take_the_safety_path(self):
        for text in SAFETY_WITH_VALUE_TALK:
            with self.subTest(text=text):
                hit = self.hit(text)
                self.assertEqual(hit and hit.kind, tg.SAFETY, text)

    def test_everyday_talk_raises_no_safety_flag(self):
        for text, _lang in NEGATIVES:
            with self.subTest(text=text):
                hit = self.hit(text)
                self.assertFalse(hit and hit.kind == tg.SAFETY, (text, hit))

    def test_new_rules_carry_their_meta(self):
        raw = {r["id"]: r for r in __import__("json").loads(tg.RULES_PATH.read_text(encoding="utf-8"))["safety"]}
        for rid in ("grooming_gifts", "grooming_isolation", "grooming_isolation_online"):
            self.assertEqual((raw[rid]["flag_type"], raw[rid]["notify_parent"]), ("harmful", True), rid)
        self.assertEqual((raw["hitting_by_adult"]["flag_type"], raw["hitting_by_adult"]["notify_parent"]),
                         ("harmful", False))
