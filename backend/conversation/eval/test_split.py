"""split.json (DEV / HELD-OUT) stays in step with cases.yaml and keeps its promises."""
from collections import Counter
from unittest import TestCase

from . import load_cases
from .make_split import build, family, load_split


class SplitTests(TestCase):
    def setUp(self):
        self.cases = load_cases()
        self.split = load_split()

    def test_split_matches_generator(self):
        self.assertEqual(build(self.cases)['dev'], self.split['dev'])
        self.assertEqual(build(self.cases)['heldout'], self.split['heldout'])

    def test_partition_is_complete_and_disjoint(self):
        ids = [c['id'] for c in self.cases]
        both = self.split['dev'] + self.split['heldout']
        self.assertEqual(sorted(both), sorted(ids))

    def test_families_never_straddle(self):
        held = {family(i) for i in self.split['heldout']}
        dev = {family(i) for i in self.split['dev']}
        self.assertFalse(held & dev)

    def test_lead_heldout_tags_are_held_out(self):
        tagged = {c['id'] for c in self.cases if 'heldout' in (c.get('tags') or [])}
        self.assertTrue(tagged <= set(self.split['heldout']))

    def test_dev_tagged_cases_are_dev(self):
        tagged = {c['id'] for c in self.cases if 'dev' in (c.get('tags') or [])}
        self.assertTrue(tagged, 'the classifier cases carry the dev tag')
        self.assertTrue(tagged <= set(self.split['dev']))
        self.assertFalse(tagged & set(self.split['heldout']))

    def test_dev_tag_never_moves_a_drawn_family(self):
        """Dropping the dev-tagged cases leaves every other id on the same side."""
        base = [c for c in self.cases if 'dev' not in (c.get('tags') or [])]
        again = build(base)
        self.assertEqual(again['heldout'], self.split['heldout'])
        self.assertEqual(again['dev'], [i for i in self.split['dev'] if i in {c['id'] for c in base}])

    def test_each_category_on_both_sides(self):
        cats = Counter(c['category'] for c in self.cases)
        dev = Counter(c['category'] for c in self.cases if c['id'] in set(self.split['dev']))
        held = Counter(c['category'] for c in self.cases if c['id'] in set(self.split['heldout']))
        for cat, n in cats.items():
            if n >= 2:
                self.assertTrue(dev[cat] and held[cat], cat)

    def test_heldout_share_is_about_thirty_percent(self):
        share = len(self.split['heldout']) / len(self.cases)
        self.assertTrue(0.25 <= share <= 0.35, share)
