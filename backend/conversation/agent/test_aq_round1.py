"""Agent-quality round 1 tests (hk/agent-quality): attribution wording of the output guard. Every religious
sentence here is a PLACEHOLDER sentence about nothing in particular; no Quran or hadith text appears in this
file. (The per-turn mode texts and the old persona constants these tests used were removed in hk/12; the
prompt now has its own tests in test_prompt.py.)"""
from django.test import SimpleTestCase

from conversation.agent import scripture_guard as sg


class DescribingAServedVerseTests(SimpleTestCase):
    """A served verse licenses "Allah says" wording. Describing what it is about, with the
    Prophet as the subject of a plain description, is not a hadith attribution."""

    def test_description_of_the_prophet_with_a_verse_served_is_not_cut(self):
        for text in (
            "في السورة نتعلم أن النبي ﷺ كان رحيما بالناس",          # "we learn that the Prophet was kind"
            "هذه الآية تقول إن رسول الله كان لطيفا",                # a description, no saying
            "the card shows the Prophet was kind to everyone",
        ):
            self.assertIsNone(sg.find_attribution(text, frozenset({"quran"})), text)

    def test_a_narration_lead_in_with_an_instruction_is_still_cut(self):
        for text in (
            "ان النبي امر بكذا",       # "that the Prophet commanded ..."
            "ان النبي نهى عن كذا",     # "that the Prophet forbade ..."
            "ان رسول الله قال كذا",    # "that the Messenger of Allah said ..."
            "ان النبي كان يقول كذا",   # "that the Prophet used to say ..."
            "عن النبي كذا وكذا",       # "on the authority of the Prophet ..."
        ):
            self.assertIsNotNone(sg.find_attribution(text, frozenset({"quran"})), text)

    def test_a_lead_in_with_a_blessing_or_an_imperfect_verb_is_still_cut(self):
        # review fix: bf89e41 had dropped these, which the broad "ان النبي" pattern used to cut
        for text in (
            "أن النبي صلى الله عليه وسلم نهى عن كذا",   # blessing, then "forbade"
            "ان رسول الله صلى الله عليه وسلم حث على كذا",  # blessing, then "urged"
            "ان النبي عليه السلام امر بكذا",              # short blessing, then "commanded"
            "ان النبي صلى الله عليه وسلم علم الناس كذا",   # "taught" (the lead's own example)
            "ان النبي كان ينهى عن كذا",                   # "used to forbid"
            "أن النبي ﷺ كان يأمر بكذا",                   # ligature blessing, "used to command"
        ):
            self.assertIsNotNone(sg.find_attribution(text, frozenset({"quran"})), text)
        # the description a served verse gives stays allowed, with or without a blessing
        for text in (
            "أن النبي صلى الله عليه وسلم كان رحيما بالناس",
            "تقول البطاقة أن النبي محمدا ﷺ كان لطيفا",
        ):
            self.assertIsNone(sg.find_attribution(text, frozenset({"quran"})), text)

    def test_nothing_is_licensed_without_a_served_item(self):
        # with no item served even the description is held back by the guard's own rule
        # only when it is a saying; a plain description passes in every case
        self.assertIsNone(sg.find_attribution("نتعلم أن النبي كان رحيما", frozenset()))
        self.assertIsNotNone(sg.find_attribution("قال النبي كذا", frozenset()))
