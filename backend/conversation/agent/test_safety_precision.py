"""Precision tests for the SAFETY rules: everyday talk must not raise a parent alert, real risk must.

Offline and deterministic (no LLM, no network). The sentences live in ``safety_precision_data.py`` and
``safety_precision_probes.py``; the before and after tables come from ``safety_harness.py``. Rules under
test: the grooming and eating restructure and the mixed Arabic-English variants (handoff section 14).
"""
import json
from pathlib import Path

from django.test import SimpleTestCase

from conversation.agent import safety_precision_data as data
from conversation.agent import turn_guard
from conversation.agent.safety_precision_probes import PARAPHRASE_PROBES
from conversation.agent.text_match import has_both_scripts, token_forms, tokenize

BASELINE = Path(__file__).with_name("safety_precision_baseline.json")


def fired(text):
    tf = token_forms(text)
    return sorted({r.id for r in turn_guard.load_rules().safety if r.matches(tf)})


class EverydayPrecisionTests(SimpleTestCase):
    def test_everyday_false_positive_rate_is_at_most_two_percent(self):
        hits = [(text, fired(text)) for _topic, _lang, text in data.EVERYDAY if fired(text)]
        rate = len(hits) / len(data.EVERYDAY)
        self.assertLessEqual(rate, 0.02, f"{len(hits)} of {len(data.EVERYDAY)} everyday sentences fire: {hits}")

    def test_everyday_set_covers_the_topics_and_languages(self):
        self.assertGreaterEqual(len(data.EVERYDAY), 120)
        topics = {t for t, _l, _x in data.EVERYDAY}
        for needed in ("video", "game", "gift", "camera", "photo", "dream", "school", "meal", "mix"):
            self.assertIn(needed, topics)
        self.assertEqual({lang for _t, lang, _x in data.EVERYDAY}, {"en", "ar", "mix"})

    def test_the_review_examples_stay_silent(self):
        for text in ("i watched a free video online",
                     "my mom will give me a camera and a new game for eid",
                     "اخوي قال لي شوف فيديو غريب"):
            self.assertEqual(fired(text), [], text)

    def test_a_surprise_party_secret_is_not_grooming(self):
        for text in ("my mom took a photo of the cake and told me to keep it a secret until the party",
                     "بابا عطاني هدية كاميرا وقال لا تقول لاحد لين يجي عيد ميلاد اخوي"):
            self.assertEqual(fired(text), [], text)


class RealRiskTests(SimpleTestCase):
    def test_every_real_risk_sentence_fires(self):
        silent = [text for _tag, _lang, text in data.REAL_RISK if not fired(text)]
        self.assertEqual(silent, [])

    def test_real_risk_set_is_large_and_mixed(self):
        self.assertGreaterEqual(len(data.REAL_RISK), 60)
        self.assertIn("mix", {lang for _t, lang, _x in data.REAL_RISK})

    def test_paraphrase_probes_fire(self):
        self.assertGreaterEqual(len(PARAPHRASE_PROBES), 100)
        silent = [t for t in PARAPHRASE_PROBES if not fired(t)]
        self.assertEqual(silent, [])

    def test_every_sentence_that_fired_before_the_restructure_still_fires(self):
        baseline = json.loads(BASELINE.read_text(encoding="utf-8"))["sentences"]
        self.assertGreater(len(baseline), 300)
        lost = [t for t in baseline if not fired(t)]
        self.assertEqual(lost, [])


class DreamFrameTests(SimpleTestCase):
    """The dream veto is narrow: it sits only on the rules that need no secrecy, gift or threat."""

    def test_a_dream_of_a_stranger_asking_for_a_photo_is_silent(self):
        self.assertEqual(fired("last night i dreamed that a stranger in a game asked me for a photo"), [])
        self.assertEqual(fired("حلمت ان واحد غريب طلب مني صورتي وصحيت خايفة"), [])

    def test_the_same_request_awake_fires(self):
        self.assertIn("grooming_unknown_asks_media", fired("a stranger in a game asked me for a photo"))
        self.assertTrue(fired("واحد غريب طلب مني صورتي"))

    def test_a_dream_word_does_not_cancel_secrecy_or_threats(self):
        self.assertTrue(fired("i had a dream last night and today a man online asked for my photo "
                              "and said keep it between us"))
        self.assertTrue(fired("حلمت امس وبعدين واحد بالنت طلب صورتي وقال لا تقول لاحد"))
        self.assertTrue(fired("a stranger online asked for my photos and said he will post them if i dont "
                              "send more, and i had a nightmare about it"))


class StrangeVersusStrangerTests(SimpleTestCase):
    def test_the_arabic_adjective_is_not_a_stranger(self):
        self.assertEqual(fired("شفت فيديو غريب وقلت لاخوي يشوفه"), [])

    def test_the_arabic_stranger_with_a_request_fires(self):
        self.assertTrue(fired("الغريب طلب مني صورتي وقال سر"))
        self.assertTrue(fired("غريب بالنت طلب مني صور"))


class EatingMotiveTests(SimpleTestCase):
    def test_a_bare_weight_word_is_not_a_motive(self):
        for text in ("my brother is on a diet and does not eat sweets and i asked him why",
                     "i dont eat the fat on the meat because it tastes bad",
                     "اخس ما ابي اكل البروكلي"):
            self.assertEqual(fired(text), [], text)

    def test_a_stated_motive_still_fires(self):
        for text in ("i dont eat because i dont want to get fat",
                     "ما اكل عشان ابقى نحيفة",
                     "i skip lunch every day to lose weight"):
            self.assertIn("restricting_food_for_weight", fired(text), text)

    def test_a_clear_restriction_with_a_bare_word_fires(self):
        self.assertIn("restricting_food_bare_motive", fired("i skip meals and i am too skinny to eat"))
        self.assertIn("restricting_food_bare_motive",
                      fired("i only drink water and skip all meals because of my diet"))


class MixedLanguageTests(SimpleTestCase):
    def test_fused_mixed_script_tokens_are_split(self):
        self.assertEqual(tokenize("الphoto"), ["ال", "photo"])
        self.assertEqual(tokenize("الـphoto"), ["ال", "photo"])
        self.assertEqual(tokenize("photoال"), ["photo", "ال"])
        self.assertEqual(tokenize("camera123"), ["camera123"])

    def test_has_both_scripts(self):
        self.assertTrue(has_both_scripts(token_forms("a man قال لي send photo")))
        self.assertFalse(has_both_scripts(token_forms("a man said send photo")))
        self.assertFalse(has_both_scripts(token_forms("واحد قال لي ارسل صورة")))

    def test_mixed_variants_only_run_on_mixed_turns(self):
        rules = turn_guard.load_rules().safety
        mixed = [r for r in rules if r.both_scripts]
        self.assertGreater(len(mixed), 20)
        # the same words in one script never reach a mixed variant
        for r in mixed:
            self.assertFalse(r.matches(token_forms("hello there my friend")), r.id)
        self.assertGreater(len([r for r in rules if not r.both_scripts]), len(mixed))

    def test_code_switched_disclosures_fire(self):
        for text in ("a man online قال لي send photo ولا تقول لأحد",
                     "واحد غريب online يطلب مني الـphoto وقال خلها سر",
                     "a stranger في الانستا يبي my address وقال don't tell your parents",
                     "ابوي hits me every night وانا خايف",
                     "بتقيا بعد الاكل because i feel fat"):
            self.assertTrue(fired(text), text)

    def test_code_switched_everyday_talk_is_silent(self):
        for text in ("ماما will buy me a new camera و game for eid",
                     "i love اللعبة الجديدة في roblox وعندي كاميرا جديدة هدية",
                     "i dont eat the fat على اللحم لانه طعمه مو حلو"):
            self.assertEqual(fired(text), [], text)


class ReviewRestoreTests(SimpleTestCase):
    """Reviewer findings on ae92244 (handoff section 15): real disclosures the narrowed rules had silenced."""

    def test_reviewer_blind_and_fresh_risk_fires(self):
        from conversation.agent import safety_review_probes as rp
        for name in ("BLIND_RISK", "RESTORED_RISK", "FRESH_RISK"):
            silent = [t for t in getattr(rp, name) if not fired(t)]
            self.assertEqual(silent, [], name)

    def test_reviewer_everyday_sets_stay_silent(self):
        from conversation.agent import safety_review_probes as rp
        for name in ("BLIND_EVERYDAY", "FRESH_EVERYDAY", "ADVERSARIAL_EVERYDAY"):
            hits = [(t, fired(t)) for t in getattr(rp, name) if fired(t)]
            self.assertEqual(hits, [], name)

    def test_a_dream_word_inside_a_disclosure_is_not_a_dream(self):
        for text in ("a man online asked me for photos and now i keep having nightmares",
                     "a stranger on snapchat asked me for a video and said he can make my dreams come true",
                     "رجال بالنت قال بيحقق حلمي اذا ارسلت له صوري"):
            self.assertTrue(fired(text), text)
        # a dream told as a dream stays silent
        for text in ("i was dreaming that a stranger in a game asked me for a photo",
                     "i had a weird dream that a man online asked for my picture",
                     "حلمت ان واحد غريب طلب صوري"):
            self.assertEqual(fired(text), [], text)

    def test_secrecy_from_parents_needs_no_named_platform(self):
        self.assertIn("grooming_secrecy_parents",
                      fired("someone told me not to tell my parents that we talk every night"))
        self.assertIn("grooming_secrecy_parents", fired("واحد قال لي لا تقول لاهلك عن كلامنا"))
        # a sibling saying "do not tell mum" is not a contact keeping the child from their parents
        self.assertEqual(fired("my sister said dont tell mom i ate the last cookie"), [])

    def test_a_gift_on_a_camera_condition_fires_but_not_on_family_whatsapp(self):
        self.assertIn("grooming_media_gift_offer", fired("a guy on roblox promised me robux if i turn on my camera"))
        self.assertEqual(fired("my dad said if i turn on the camera for grandma on whatsapp he will buy me ice cream"), [])

    def test_a_self_description_next_to_a_restriction_fires(self):
        for text in ("i don't eat breakfast anymore because i'm getting fat",
                     "ما اكل عشان ما اصير سمينة",
                     "لا اريد ان اكل لانني سمينة"):
            self.assertIn("restricting_food_for_weight", fired(text), text)
        self.assertEqual(fired("my cat is getting fat so we only give her a little food"), [])
