# Hadith drafts (staging, NOT seeded)

Drafts made on 5 Oct 2026 by the dorar proof step (plan §4, route H + D). `seed_content` never reads this folder.

- Each `draft-<value>-<dorar id>.json` was produced by `tools/fetch_hadith.py --pick` from a dorar.net `/h/<id>` page saved from a real browser at human pace. The page text was checked byte-for-byte (SHA-256 in the browser vs the saved file) before drafting. The saved pages themselves stay in the gitignored `tools/.cache/dorar-hadith/` on the lead's laptop.
- Every draft: Sahih al-Bukhari or Sahih Muslim, grade exactly `صحيح`, grader = the compiler, `source_url` = the dorar permalink, status `unverified`.
- `provenance-*.json`: file name, sha256 and retrieved date per pick.
- Some dorar pages serve two values (same hadith, different draft files): merge their `values` lists when building items.

Next: add child explanations, review (Opus, then the lead on dorar), then move accepted items into `content/items/<value>.json` and mark them reviewed with `tools/mark_reviewed.py`.
