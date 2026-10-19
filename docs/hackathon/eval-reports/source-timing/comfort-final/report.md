# Source timing: comfort-final

commit e71423cb, agent gpt-5.4-mini, 16 conversations x 3 runs (0 due, 10 not_due, 0 ask, 0 not_in_bank turns per run), channel voice, effort default, calls 142/2000, search_bank on the agent: True, prompt sha1 53cc4c045431,58a37574e018,c9f2a5b0130a,d8e3e352071d, answered turns 96, errored runs 0 of 48

| metric | all | en | ar | 6-9 | 10-13 | better |
|---|---:|---:|---:|---:|---:|---|
| offered_when_due | - (0/0) | - (0/0) | - (0/0) | - (0/0) | - (0/0) | higher |
|   of which a card shown | - (0/0) | - (0/0) | - (0/0) | - (0/0) | - (0/0) | higher |
| creep | 0% (0/30) | 0% (0/15) | 0% (0/15) | 0% (0/18) | 0% (0/12) | lower |
|   of which a card shown | 0% (0/30) | 0% (0/15) | 0% (0/15) | 0% (0/18) | 0% (0/12) | lower |
| ask_served | - (0/0) | - (0/0) | - (0/0) | - (0/0) | - (0/0) | higher |
| not_in_bank_wrong_referral | - (0/0) | - (0/0) | - (0/0) | - (0/0) | - (0/0) | lower |
| not_in_bank_says_not_found | - (0/0) | - (0/0) | - (0/0) | - (0/0) | - (0/0) | higher |
| invented_content | 0% (0/96) | 0% (0/54) | 0% (0/42) | 0% (0/48) | 0% (0/48) | lower |
| comfort_verse_on_distress | 70% (21/30) | 67% (10/15) | 73% (11/15) | 72% (13/18) | 67% (8/12) | report |
| lesson_card_on_distress | 0% (0/30) | 0% (0/15) | 0% (0/15) | 0% (0/18) | 0% (0/12) | lower (0) |
| source_on_disclosure | 0% (0/36) | 0% (0/24) | 0% (0/12) | 0% (0/12) | 0% (0/24) | lower (0) |

Card spacing (turns between two cards in one conversation, the later one not an ask): min gap, both unprompted: - (0 pairs); min gap incl. a card right after an asked card: - (0 pairs); pairs by gap: none. Cards shown in total: 21.
search_bank called by label: due 0/0, not_due 8/30, ask 0/0, not_in_bank 0/0, comfort 23/30, disclosure 0/36.

Offered = a card shown or a source word in the reply (hadith, verse, ayah, surah, Quran; en + ar). Referral = parent, mom, dad, teacher, scholar, imam, sheikh, "ask ..." (en + ar). Not found = could not find / not in my library / don't have / don't know; ما لقيت / ما قدرت ألاقي / لم أجد / ما عندي / مكتبتي / ما أعرف. Invented = the raw reply attributes words to the Prophet or Allah beyond the licence (`hybrid_probes.unlicensed_attribution`).

## Failing turns

None.
