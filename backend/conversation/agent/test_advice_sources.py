"""hk/13c: advice about treating people is tied to one library item, and "another one?" gets the next
item, never a claim that more exist. Placeholder text only: no scripture."""
from __future__ import annotations

import unittest

from conversation.agent import bank_search
from conversation.agent.prompt import STATIC_PROMPT
from conversation.agent.test_bank_tool import make_agent_class


class AdviceContractTests(unittest.TestCase):
    def test_the_prompt_ties_advice_to_one_item_and_never_claims_unseen_sources(self):
        for line in ("before any advice or gentle word on how to treat people", "a fight",
                     "call search_bank and tie it to ONE item", "In our", "في ديننا",
                     "Other value moments: offer one at most once every 4 turns",
                     "Never say more sources exist unless", "you show one"):
            self.assertIn(line, STATIC_PROMPT, line)
        # distress, comfort and disclosure rules are unchanged
        for line in ("If the child is sad, scared, worried or grieving", "never on a flagged turn"):
            self.assertIn(line, STATIC_PROMPT, line)

    def test_the_tool_says_to_call_it_before_advice_and_for_another_one(self):
        doc = " ".join((make_agent_class().search_bank.__doc__ or "").split())
        self.assertIn("before advice on treating people", doc)
        self.assertIn("For another one, share an item not shown yet", doc)
        self.assertIn("say that's all you have on this topic", doc)


if __name__ == "__main__":
    unittest.main()
