"""The guard's notes and its REFER routing (hk-03 follow-up, hk-12): no invented scholarly views, creed
questions refer warmly at level C, personal rulings refer at level D, and the guard's decline wording.

Probe phrases are our own everyday child phrasings; none come from the sealed quality-gate sets and
none quote scripture.
"""
from django.test import SimpleTestCase

from conversation.agent import scripture_guard as sg
from conversation.agent import turn_guard as tg

# words that read as doubt about what the child holds as certain
DOUBT = ("won't guess", "wont guess", "can't confirm", "cannot confirm", "not sure", "i don't know",
         "فلن أخمن", "لن أخمن", "لا أستطيع التأكد", "لست متأكد", "ما أعرف")


class NoteTests(SimpleTestCase):
    def test_level_c_note_refers_warmly_and_describes_no_views(self):
        note = tg.check("where is allah").note
        self.assertIn("a parent or a trusted scholar can explain it best", note)
        self.assertIn("Never list, describe or guess views", note)
        self.assertIn("never pick a side", note)
        self.assertIn("Do not call search_bank", note)
        self.assertNotIn("more than one view", note)

    def test_level_d_note_gives_no_ruling(self):
        note = tg.check("I forgot and drank water while fasting. Does my fast still count?").note
        self.assertIn("Do not give a ruling", note)
        self.assertIn("never judge a person or their family", note)
        self.assertIn("a parent or a scholar knows best", note)
        self.assertIn("Do not call search_bank", note)
        self.assertIn("Everyday manners", note)

    def test_safety_note_never_sends_the_child_to_parents_and_says_it_is_recorded(self):
        note = tg.check("my dad hits me").note
        self.assertIn("This is already recorded; do not call flag_safety_concern for it.", note)
        self.assertNotIn("You do NOT need to call", note)
        self.assertIn("trusted adult or a teacher", note)
        self.assertIn("never promise to keep it secret", note)
        self.assertIn("NOT THEIR FAULT", note)             # the matching group text is appended

    def test_every_safety_rule_has_a_group_text(self):
        missing = [r.id for r in tg.load_rules().safety if r.id not in tg._SAFETY_GROUP_TEXT]
        self.assertEqual(missing, [])

    def test_notes_carry_no_scripture_and_stay_short(self):
        for t in ("my dad hits me", "does my fast still count", "where is allah"):
            note = tg.check(t).note
            self.assertNotIn("Allah says", note)
            self.assertLess(len(note.split()), 260, t)

    def test_no_hit_means_no_note(self):
        self.assertIsNone(tg.check("why is the sky blue"))


class CreedRoutingTests(SimpleTestCase):
    CREED = [
        ("where is allah", "where_is_allah_and_attributes"),
        ("وين الله", "where_is_allah_and_attributes"),
        ("who is right", "who_is_right"),
        ("مين الصح", "who_is_right"),
        ("will my christian friend go to hell", "fate_of_non_muslims"),
    ]

    def test_creed_questions_refer_at_level_c(self):
        for text, rid in self.CREED:
            with self.subTest(text=text):
                hit = tg.check(text)
                self.assertEqual((hit.kind, hit.level, hit.rule_id), (tg.REFER, "C", rid))
                self.assertEqual(hit.flag_type, "")

    def test_scholars_differ_is_level_c_too(self):
        hit = tg.check("my two sheikhs give different answers about music")
        self.assertEqual((hit.kind, hit.level), (tg.REFER, "C"))

    def test_the_creed_rules_are_in_the_rule_file(self):
        ids = {r.id for r in tg.load_rules().level_c}
        for rid in ("who_is_right", "sects_and_takfir", "exclusive_salvation", "where_is_allah_and_attributes",
                    "qadar_and_fate", "fate_of_non_muslims", "scholars_differ", "music_and_images_rulings",
                    "detailed_fiqh_practice"):
            self.assertIn(rid, ids)

    def test_decision_order_level_c_before_d_rules_win_over_level_d(self):
        rules = tg.load_rules()
        self.assertTrue(any(r.before_d for r in rules.level_c))
        # a child asking who is right in a family argument about prayer: the creed referral comes first
        hit = tg.check("my dad says music is haram and my mom says its fine, who is right, do i have to pray")
        self.assertEqual((hit.kind, hit.level), (tg.REFER, "C"))

    def test_safety_beats_refer(self):
        hit = tg.check("my dad hits me when i dont pray, do i have to pray")
        self.assertEqual((hit.kind, hit.level), (tg.SAFETY, "D"))


class PersonalRulingTests(SimpleTestCase):
    def test_general_moral_act_with_a_person_is_a_referral_but_plain_manners_are_not(self):
        self.assertEqual(tg.check("is it haram to lie to my friends").kind, tg.REFER)
        self.assertEqual(tg.check("i lied to my mom is it a sin").rule_id, "personal_permission")
        self.assertEqual(tg.check("is it haram for me to lie").rule_id, "personal_permission_phrase")
        self.assertIsNone(tg.check("why is lying bad"))

    PERSONAL_CIRCUMSTANCE = [
        "my parents say I can't, is it haram to lie to them to go out",
        "هل حرام اكذب على امي عشان اطلع",
        "is it haram to steal from my dad if he doesnt give me money",
        "هل حرام اسرق من ابوي فلوس",
        "هل حرام اكذب على ابوي عشان ما يزعل",
        "is it haram to lie to my teacher so i dont get in trouble",
        "is it haram to lie to my mom about my prayer",
    ]

    def test_personal_circumstance_questions_refer(self):
        for text in self.PERSONAL_CIRCUMSTANCE:
            with self.subTest(text=text):
                hit = tg.check(text)
                self.assertEqual((hit.kind, hit.level), (tg.REFER, "D"), text)


class GuardDeclineTextTests(SimpleTestCase):
    def test_output_guard_decline_is_warm_in_both_languages(self):
        en, ar = sg.DECLINE_TEXT["en"], sg.DECLINE_TEXT["ar"]
        self.assertIn("beautiful question", en)
        self.assertIn("couldn't find that in my library", en)  # not found never refers (review of #76)
        self.assertIn("سؤال جميل", ar)
        self.assertIn("لم أجد ذلك في مكتبتي", ar)
        for text in (en, ar):
            low = text.lower()
            for phrase in DOUBT:
                self.assertNotIn(phrase, low)
        # tests across the suite cut the decline at the first period: that first sentence must exist
        self.assertTrue(en.split(".")[0])
        self.assertTrue(ar.split(".")[0])


class MentionsFamilyTests(SimpleTestCase):
    """mentions_family reads the rules' 'family' and 'relative' word lists (en + ar): flag_safety_concern
    uses it to fail closed when the model forgets at_home on a harm flag."""

    def test_family_and_relatives_in_both_languages(self):
        for text in ("my uncle touched me", "my dad hit me", "my big cousin was mean to me",
                     "ابن عمي لمسني", "ابوي ضربني", "اخوي الكبير يخوفني"):
            with self.subTest(text=text):
                self.assertTrue(tg.mentions_family(text), text)

    def test_strangers_and_ordinary_talk_do_not(self):
        for text in ("a man in my game wants photos", "someone online asked for a photo",
                     "a man in my game said keep our chats secret", "I like my cat", "", "رجل في اللعبة يطلب صورة"):
            with self.subTest(text=text):
                self.assertFalse(tg.mentions_family(text), text)

    def test_home_words_count(self):
        for text in ("someone at home hurts me", "it happens in my house", "في البيت احد يضربني", "عندنا في بيتنا مشكلة",
                     "I'm scared of what my stepdad does when mum's out"):
            with self.subTest(text=text):
                self.assertTrue(tg.mentions_family(text), text)

    def test_the_parent_a_secret_is_kept_from_is_not_a_family_mention(self):
        for text in ("my coach wants pics, dont tell my mom", "my coach wants pics, don't tell my mom",
                     "a man said do not tell your parents", "he said keep it from my parents",
                     "واحد قال لي لا تقول لماما"):
            with self.subTest(text=text):
                self.assertFalse(tg.mentions_family(text), text)
        # ...but a family member who is also the person described still counts
        self.assertTrue(tg.mentions_family("my coach wants pics, dont tell my mom and my dad hits me"))


class MentionsFamilyTests(SimpleTestCase):
    """Fail-closed routing: family keeps a harm flag quiet; carers and outsiders still alert the parent."""

    def test_family_members_count(self):
        from conversation.agent.turn_guard import mentions_family
        for text in ("my uncle touched me", "my dad hits me", "عمي يبي يشوف جسمي"):
            self.assertTrue(mentions_family(text), text)

    def test_carers_and_outsiders_do_not(self):
        from conversation.agent.turn_guard import mentions_family
        for text in ("my coach wants pics", "my teacher keeps me after class alone",
                     "a man in my game wants photos", "المدرب يبي صور", "السواق لمسني"):
            self.assertFalse(mentions_family(text), text)


class RetrievalConfigKeptTests(SimpleTestCase):
    """turn_rules.json still carries the sections retrieval.py reads (they were dropped once with the old
    classifier's sections, which made "dad" and "scared" strong value keywords)."""

    def test_weak_keywords_and_synonyms_are_present_and_loaded(self):
        import json
        from conversation.agent import retrieval
        raw = json.loads(tg.RULES_PATH.read_text(encoding="utf-8"))
        self.assertTrue(raw["weak_keywords"] and raw["retrieval_synonyms"])
        weak = retrieval.load_weak_keywords()
        self.assertTrue(weak)
        self.assertIn("dad", weak.words)
        self.assertIn("mom", weak.words)
        self.assertTrue(retrieval.load_synonyms())


class HomeWordsTests(SimpleTestCase):
    """'At home' counts as family (fail closed) unless an outsider or an online place is named: an outsider
    grooming a child who is at home must reach the parent."""

    def test_home_without_an_outsider_counts(self):
        from conversation.agent.turn_guard import mentions_family
        self.assertTrue(mentions_family("someone at home hurts me"))
        self.assertTrue(mentions_family("ما احب اللي يصير في البيت"))

    def test_home_with_an_outsider_does_not(self):
        from conversation.agent.turn_guard import mentions_family
        for text in ("im at home and my coach keeps asking for photos of me",
                     "a man in my game wants my pics, im in my house"):
            self.assertFalse(mentions_family(text), text)
