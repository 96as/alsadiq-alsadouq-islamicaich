# Verse text re-review (KFGQPC Uthmani, pinned release v2-0)

For: Abdulrahman Salamah (lead). Branch `hk/01-knowledge-bank`, not committed. Generated 2026-10-05 from the item files; the Arabic below is copied from `items/*.json`, never retyped.

## What changed and why

- The hackathon package (p.3) approves the King Fahd Complex (KFGQPC) Uthmani orthography. Our 74 stored verses were an imlaei-style script (research r4), so you approved decision 2: replace them with the Complex text.
- Source: **KFGQPC Hafs `UthmanicHafs_v2-0`**. Pins: zip sha256 `a7b0e5591945712ec5e4d6142938ae4d1e9b49bdc89dff06222789bfebdfd72c`, JSON `hafsData_v2-0.json` sha256 `d2960b3217962e7e4252abdcece67bea3d6b48271e4cd3af45bbbb2dd5c872ca` (stored on each item as `text_edition`: `KFGQPC Hafs v2-0 sha256:d2960b321796`).
- `arabic_text` is the file's `aya_text` byte for byte, minus only the trailing end-of-ayah number glyph. Two fields were added: `arabic_text_search` (the Complex's own simple spelling, for search only) and `text_edition`.
- Nothing else changed in any item (English, child explanations, values, age band, source URL, audio URL, review fields). That was checked by diffing every item against `HEAD`.
- All 74 reviews are now stale on purpose (`mark_reviewed.py --check` lists them). The items seed as `seeded`, not `reviewed`, until you approve below.

## What to check

The text is already proven byte-identical to the pinned Complex file by machine (0 mismatches): `cd backend/session_moral_context/content && python3 tools/verify_arabic.py --kfgqpc "tools/.cache/quran-complex/UthmanicHafs_v2-0 data/hafsData_v2-0.json" --sha256 d2960b3217962e7e4252abdcece67bea3d6b48271e4cd3af45bbbb2dd5c872ca --strict`. You do not need to compare letters. For each verse check only:

1. It is the right surah:ayah for the value and the English/explanation shown on the card.
2. The source link opens the right ayah on quranpedia.net.
3. The text looks complete: starts and ends where the ayah starts and ends, no cut-off or doubled words.

Also: the font renders without empty boxes in the web/mobile app (this sheet is plain text and cannot show that).

Look harder at these two groups (the research sampling plan):

- **Pause marks differ (5 verses, check against a printed or app Madinah mushaf):** 2:262, 24:22, 2:261, 16:78, 5:119.
- **Rasm differs (20 verses, check about 10 including 2:153, 20:14, 39:9):** 2:220, 20:131, 57:23, 9:71, 24:22, 4:36, 16:78, 5:2, 4:135, 5:8, 17:34, 2:83, 33:21, 28:25, 20:14, 2:153, 29:45, 39:9, 98:5, 28:26.
- The other 51 verses differ only in marks, wasla and spacing (the Uthmani orthography: sukun as U+06E1, alef wasla, idgham shadda, dagger alef, open tanween, waqf signs attached to the word).

"Kind of change" is computed from old vs new: **rasm** = the letter skeleton differs (diacritics, hamza seats and alef forms folded; a dagger alef counts as an alef; a hamza on a kashida counts as a difference), **pause marks** = the sequence of waqf signs U+06D6-U+06DB differs, **marks/encoding** = everything else. The computation reproduces r4 sections 2.4 (20 rasm verses) and 2.5 (5 pause-mark verses) exactly.

## Verses by value file

### avoiding-backbiting.json

#### 49:12 | avoiding-backbiting

> يَٰٓأَيُّهَا ٱلَّذِينَ ءَامَنُواْ ٱجۡتَنِبُواْ كَثِيرٗا مِّنَ ٱلظَّنِّ إِنَّ بَعۡضَ ٱلظَّنِّ إِثۡمٞۖ وَلَا تَجَسَّسُواْ وَلَا يَغۡتَب بَّعۡضُكُم بَعۡضًاۚ أَيُحِبُّ أَحَدُكُمۡ أَن يَأۡكُلَ لَحۡمَ أَخِيهِ مَيۡتٗا فَكَرِهۡتُمُوهُۚ وَٱتَّقُواْ ٱللَّهَۚ إِنَّ ٱللَّهَ تَوَّابٞ رَّحِيمٞ

- English (stored): O you who have believed, avoid much [negative] assumption. Indeed, some assumption is sin. And do not spy or backbite each other. Would one of you like to eat the flesh of his brother when dead? You would detest it. And fear Allāh; indeed, Allāh is Accepting of Repentance and Merciful.
- Source: https://quranpedia.net/tafsir/al-hujurat/12
- Change: marks/encoding only
- [x] ok

#### 104:1 | avoiding-backbiting

> وَيۡلٞ لِّكُلِّ هُمَزَةٖ لُّمَزَةٍ

- English (stored): Woe to every scorner and mocker
- Source: https://quranpedia.net/tafsir/al-humaza/1
- Change: marks/encoding only
- [x] ok

### brotherhood.json

#### 49:10 | brotherhood

> إِنَّمَا ٱلۡمُؤۡمِنُونَ إِخۡوَةٞ فَأَصۡلِحُواْ بَيۡنَ أَخَوَيۡكُمۡۚ وَٱتَّقُواْ ٱللَّهَ لَعَلَّكُمۡ تُرۡحَمُونَ

- English (stored): The believers are but brothers, so make settlement between your brothers. And fear Allāh that you may receive mercy.
- Source: https://quranpedia.net/tafsir/al-hujurat/10
- Change: marks/encoding only
- [x] ok

#### 49:11 | brotherhood

> يَٰٓأَيُّهَا ٱلَّذِينَ ءَامَنُواْ لَا يَسۡخَرۡ قَوۡمٞ مِّن قَوۡمٍ عَسَىٰٓ أَن يَكُونُواْ خَيۡرٗا مِّنۡهُمۡ وَلَا نِسَآءٞ مِّن نِّسَآءٍ عَسَىٰٓ أَن يَكُنَّ خَيۡرٗا مِّنۡهُنَّۖ وَلَا تَلۡمِزُوٓاْ أَنفُسَكُمۡ وَلَا تَنَابَزُواْ بِٱلۡأَلۡقَٰبِۖ بِئۡسَ ٱلِٱسۡمُ ٱلۡفُسُوقُ بَعۡدَ ٱلۡإِيمَٰنِۚ وَمَن لَّمۡ يَتُبۡ فَأُوْلَٰٓئِكَ هُمُ ٱلظَّٰلِمُونَ

- English (stored): O you who have believed, let not a people ridicule [another] people; perhaps they may be better than them; nor let women ridicule [other] women; perhaps they may be better than them. And do not insult one another and do not call each other by [offensive] nicknames. Wretched is the name [i.e., mention] of disobedience after [one's] faith. And whoever does not repent - then it is those who are the wrongdoers.
- Source: https://quranpedia.net/tafsir/al-hujurat/11
- Change: marks/encoding only
- [x] ok

#### 3:103 | brotherhood

> وَٱعۡتَصِمُواْ بِحَبۡلِ ٱللَّهِ جَمِيعٗا وَلَا تَفَرَّقُواْۚ وَٱذۡكُرُواْ نِعۡمَتَ ٱللَّهِ عَلَيۡكُمۡ إِذۡ كُنتُمۡ أَعۡدَآءٗ فَأَلَّفَ بَيۡنَ قُلُوبِكُمۡ فَأَصۡبَحۡتُم بِنِعۡمَتِهِۦٓ إِخۡوَٰنٗا وَكُنتُمۡ عَلَىٰ شَفَا حُفۡرَةٖ مِّنَ ٱلنَّارِ فَأَنقَذَكُم مِّنۡهَاۗ كَذَٰلِكَ يُبَيِّنُ ٱللَّهُ لَكُمۡ ءَايَٰتِهِۦ لَعَلَّكُمۡ تَهۡتَدُونَ

- English (stored): And hold firmly to the rope of Allāh all together and do not become divided. And remember the favor of Allāh upon you - when you were enemies and He brought your hearts together and you became, by His favor, brothers. And you were on the edge of a pit of the Fire, and He saved you from it. Thus does Allāh make clear to you His verses that you may be guided.
- Source: https://quranpedia.net/tafsir/aal-imran/103
- Change: marks/encoding only
- [x] ok

### caring-for-orphans.json

#### 93:9 | caring-for-orphans

> فَأَمَّا ٱلۡيَتِيمَ فَلَا تَقۡهَرۡ

- English (stored): So as for the orphan, do not oppress [him].
- Source: https://quranpedia.net/tafsir/ad-duha/9
- Change: marks/encoding only
- [x] ok

#### 2:220 | caring-for-orphans

> فِي ٱلدُّنۡيَا وَٱلۡأٓخِرَةِۗ وَيَسۡـَٔلُونَكَ عَنِ ٱلۡيَتَٰمَىٰۖ قُلۡ إِصۡلَاحٞ لَّهُمۡ خَيۡرٞۖ وَإِن تُخَالِطُوهُمۡ فَإِخۡوَٰنُكُمۡۚ وَٱللَّهُ يَعۡلَمُ ٱلۡمُفۡسِدَ مِنَ ٱلۡمُصۡلِحِۚ وَلَوۡ شَآءَ ٱللَّهُ لَأَعۡنَتَكُمۡۚ إِنَّ ٱللَّهَ عَزِيزٌ حَكِيمٞ

- English (stored): To this world and the Hereafter. And they ask you about orphans. Say, "Improvement for them is best. And if you mix your affairs with theirs - they are your brothers. And Allāh knows the corrupter from the amender. And if Allāh had willed, He could have put you in difficulty. Indeed, Allāh is Exalted in Might and Wise."
- Source: https://quranpedia.net/tafsir/al-baqara/220
- Change: rasm + marks/encoding [rasm sample]
- [x] ok

### charity.json

#### 2:262 | charity

> ٱلَّذِينَ يُنفِقُونَ أَمۡوَٰلَهُمۡ فِي سَبِيلِ ٱللَّهِ ثُمَّ لَا يُتۡبِعُونَ مَآ أَنفَقُواْ مَنّٗا وَلَآ أَذٗى لَّهُمۡ أَجۡرُهُمۡ عِندَ رَبِّهِمۡ وَلَا خَوۡفٌ عَلَيۡهِمۡ وَلَا هُمۡ يَحۡزَنُونَ

- English (stored): Those who spend their wealth in the way of Allāh and then do not follow up what they have spent with reminders [of it] or [other] injury will have their reward with their Lord, and there will be no fear concerning them, nor will they grieve.
- Source: https://quranpedia.net/tafsir/al-baqara/262
- Change: pause marks + marks/encoding (old `◌ۙ` -> new `(none)`) [check vs mushaf]
- [x] ok

### cleanliness.json

#### 9:108 | cleanliness

> لَا تَقُمۡ فِيهِ أَبَدٗاۚ لَّمَسۡجِدٌ أُسِّسَ عَلَى ٱلتَّقۡوَىٰ مِنۡ أَوَّلِ يَوۡمٍ أَحَقُّ أَن تَقُومَ فِيهِۚ فِيهِ رِجَالٞ يُحِبُّونَ أَن يَتَطَهَّرُواْۚ وَٱللَّهُ يُحِبُّ ٱلۡمُطَّهِّرِينَ

- English (stored): Do not stand [for prayer] within it - ever. A mosque founded on righteousness from the first day is more worthy for you to stand in. Within it are men who love to purify themselves; and Allāh loves those who purify themselves.
- Source: https://quranpedia.net/tafsir/at-tawba/108
- Change: marks/encoding only
- [x] ok

#### 74:4 | cleanliness

> وَثِيَابَكَ فَطَهِّرۡ

- English (stored): And your clothing purify.
- Source: https://quranpedia.net/tafsir/al-muddaththir/4
- Change: marks/encoding only
- [x] ok

### contentment.json

#### 20:131 | contentment

> وَلَا تَمُدَّنَّ عَيۡنَيۡكَ إِلَىٰ مَا مَتَّعۡنَا بِهِۦٓ أَزۡوَٰجٗا مِّنۡهُمۡ زَهۡرَةَ ٱلۡحَيَوٰةِ ٱلدُّنۡيَا لِنَفۡتِنَهُمۡ فِيهِۚ وَرِزۡقُ رَبِّكَ خَيۡرٞ وَأَبۡقَىٰ

- English (stored): And do not extend your eyes toward that by which We have given enjoyment to [some] categories of them, [its being but] the splendor of worldly life by which We test them. And the provision of your Lord is better and more enduring.
- Source: https://quranpedia.net/tafsir/ta-ha/131
- Change: rasm + marks/encoding [rasm sample]
- [x] ok

#### 57:23 | contentment

> لِّكَيۡلَا تَأۡسَوۡاْ عَلَىٰ مَا فَاتَكُمۡ وَلَا تَفۡرَحُواْ بِمَآ ءَاتَىٰكُمۡۗ وَٱللَّهُ لَا يُحِبُّ كُلَّ مُخۡتَالٖ فَخُورٍ

- English (stored): In order that you not despair over what has eluded you and not exult [in pride] over what He has given you. And Allāh does not like everyone self-deluded and boastful -
- Source: https://quranpedia.net/tafsir/al-hadid/23
- Change: rasm + marks/encoding [rasm sample]
- [x] ok

### cooperation.json

#### 9:71 | cooperation

> وَٱلۡمُؤۡمِنُونَ وَٱلۡمُؤۡمِنَٰتُ بَعۡضُهُمۡ أَوۡلِيَآءُ بَعۡضٖۚ يَأۡمُرُونَ بِٱلۡمَعۡرُوفِ وَيَنۡهَوۡنَ عَنِ ٱلۡمُنكَرِ وَيُقِيمُونَ ٱلصَّلَوٰةَ وَيُؤۡتُونَ ٱلزَّكَوٰةَ وَيُطِيعُونَ ٱللَّهَ وَرَسُولَهُۥٓۚ أُوْلَٰٓئِكَ سَيَرۡحَمُهُمُ ٱللَّهُۗ إِنَّ ٱللَّهَ عَزِيزٌ حَكِيمٞ

- English (stored): The believing men and believing women are allies of one another. They enjoin what is right and forbid what is wrong and establish prayer and give zakāh and obey Allāh and His Messenger. Those - Allāh will have mercy upon them. Indeed, Allāh is Exalted in Might and Wise.
- Source: https://quranpedia.net/tafsir/at-tawba/71
- Change: rasm + marks/encoding [rasm sample]
- [x] ok

#### 18:95 | cooperation

> قَالَ مَا مَكَّنِّي فِيهِ رَبِّي خَيۡرٞ فَأَعِينُونِي بِقُوَّةٍ أَجۡعَلۡ بَيۡنَكُمۡ وَبَيۡنَهُمۡ رَدۡمًا

- English (stored): He said, "That in which my Lord has established me is better [than what you offer], but assist me with strength [i.e., manpower]; I will make between you and them a dam.
- Source: https://quranpedia.net/tafsir/al-kahf/95
- Change: marks/encoding only
- [x] ok

### courage.json

#### 3:139 | courage

> وَلَا تَهِنُواْ وَلَا تَحۡزَنُواْ وَأَنتُمُ ٱلۡأَعۡلَوۡنَ إِن كُنتُم مُّؤۡمِنِينَ

- English (stored): So do not weaken and do not grieve, and you will be superior if you are [true] believers.
- Source: https://quranpedia.net/tafsir/aal-imran/139
- Change: marks/encoding only
- [x] ok

#### 20:46 | courage

> قَالَ لَا تَخَافَآۖ إِنَّنِي مَعَكُمَآ أَسۡمَعُ وَأَرَىٰ

- English (stored): [Allāh] said, "Fear not. Indeed, I am with you both; I hear and I see.
- Source: https://quranpedia.net/tafsir/ta-ha/46
- Change: marks/encoding only
- [x] ok

### family-ties.json

#### 4:1 | family-ties

> يَٰٓأَيُّهَا ٱلنَّاسُ ٱتَّقُواْ رَبَّكُمُ ٱلَّذِي خَلَقَكُم مِّن نَّفۡسٖ وَٰحِدَةٖ وَخَلَقَ مِنۡهَا زَوۡجَهَا وَبَثَّ مِنۡهُمَا رِجَالٗا كَثِيرٗا وَنِسَآءٗۚ وَٱتَّقُواْ ٱللَّهَ ٱلَّذِي تَسَآءَلُونَ بِهِۦ وَٱلۡأَرۡحَامَۚ إِنَّ ٱللَّهَ كَانَ عَلَيۡكُمۡ رَقِيبٗا

- English (stored): O mankind, fear your Lord, who created you from one soul and created from it its mate and dispersed from both of them many men and women. And fear Allāh, through whom you ask one another, and the wombs. Indeed Allāh is ever, over you, an Observer.
- Source: https://quranpedia.net/tafsir/an-nisa/1
- Change: marks/encoding only
- [x] ok

### forgiveness.json

#### 3:134 | forgiveness, controlling-anger

> ٱلَّذِينَ يُنفِقُونَ فِي ٱلسَّرَّآءِ وَٱلضَّرَّآءِ وَٱلۡكَٰظِمِينَ ٱلۡغَيۡظَ وَٱلۡعَافِينَ عَنِ ٱلنَّاسِۗ وَٱللَّهُ يُحِبُّ ٱلۡمُحۡسِنِينَ

- English (stored): Who spend [in the cause of Allāh] during ease and hardship and who restrain anger and who pardon the people - and Allāh loves the doers of good;
- Source: https://quranpedia.net/tafsir/aal-imran/134
- Change: marks/encoding only
- [x] ok

#### 24:22 | forgiveness

> وَلَا يَأۡتَلِ أُوْلُواْ ٱلۡفَضۡلِ مِنكُمۡ وَٱلسَّعَةِ أَن يُؤۡتُوٓاْ أُوْلِي ٱلۡقُرۡبَىٰ وَٱلۡمَسَٰكِينَ وَٱلۡمُهَٰجِرِينَ فِي سَبِيلِ ٱللَّهِۖ وَلۡيَعۡفُواْ وَلۡيَصۡفَحُوٓاْۗ أَلَا تُحِبُّونَ أَن يَغۡفِرَ ٱللَّهُ لَكُمۡۚ وَٱللَّهُ غَفُورٞ رَّحِيمٌ

- English (stored): And let not those of virtue among you and wealth swear not to give [aid] to their relatives and the needy and the emigrants for the cause of Allāh, and let them pardon and overlook. Would you not like that Allāh should forgive you? And Allāh is Forgiving and Merciful.
- Source: https://quranpedia.net/tafsir/an-nur/22
- Change: pause marks + rasm + marks/encoding (old `◌ۖ ◌ۗ ◌ۗ` -> new `◌ۖ ◌ۗ ◌ۚ`) [check vs mushaf, rasm sample]
- [x] ok

### generosity.json

#### 2:261 | generosity, charity

> مَّثَلُ ٱلَّذِينَ يُنفِقُونَ أَمۡوَٰلَهُمۡ فِي سَبِيلِ ٱللَّهِ كَمَثَلِ حَبَّةٍ أَنۢبَتَتۡ سَبۡعَ سَنَابِلَ فِي كُلِّ سُنۢبُلَةٖ مِّاْئَةُ حَبَّةٖۗ وَٱللَّهُ يُضَٰعِفُ لِمَن يَشَآءُۚ وَٱللَّهُ وَٰسِعٌ عَلِيمٌ

- English (stored): The example of those who spend their wealth in the way of Allāh is like a seed [of grain] which grows seven spikes; in each spike is a hundred grains. And Allāh multiplies [His reward] for whom He wills. And Allāh is all-Encompassing and Knowing.
- Source: https://quranpedia.net/tafsir/al-baqara/261
- Change: pause marks + marks/encoding (old `◌ۗ ◌ۗ` -> new `◌ۗ ◌ۚ`) [check vs mushaf]
- [x] ok

#### 76:8 | generosity

> وَيُطۡعِمُونَ ٱلطَّعَامَ عَلَىٰ حُبِّهِۦ مِسۡكِينٗا وَيَتِيمٗا وَأَسِيرًا

- English (stored): And they give food in spite of love for it to the needy, the orphan, and the captive,
- Source: https://quranpedia.net/tafsir/al-insan/8
- Change: marks/encoding only
- [x] ok

### good-character.json

#### 68:4 | good-character

> وَإِنَّكَ لَعَلَىٰ خُلُقٍ عَظِيمٖ

- English (stored): And indeed, you are of a great moral character.
- Source: https://quranpedia.net/tafsir/al-qalam/4
- Change: marks/encoding only
- [x] ok

#### 41:34 | good-character, controlling-anger

> وَلَا تَسۡتَوِي ٱلۡحَسَنَةُ وَلَا ٱلسَّيِّئَةُۚ ٱدۡفَعۡ بِٱلَّتِي هِيَ أَحۡسَنُ فَإِذَا ٱلَّذِي بَيۡنَكَ وَبَيۡنَهُۥ عَدَٰوَةٞ كَأَنَّهُۥ وَلِيٌّ حَمِيمٞ

- English (stored): And not equal are the good deed and the bad. Repel [evil] by that [deed] which is better; and thereupon, the one whom between you and him is enmity [will become] as though he was a devoted friend.
- Source: https://quranpedia.net/tafsir/fussilat/34
- Change: marks/encoding only
- [x] ok

#### 17:53 | good-character, kind-words

> وَقُل لِّعِبَادِي يَقُولُواْ ٱلَّتِي هِيَ أَحۡسَنُۚ إِنَّ ٱلشَّيۡطَٰنَ يَنزَغُ بَيۡنَهُمۡۚ إِنَّ ٱلشَّيۡطَٰنَ كَانَ لِلۡإِنسَٰنِ عَدُوّٗا مُّبِينٗا

- English (stored): And tell My servants to say that which is best. Indeed, Satan induces [dissension] among them. Indeed Satan is ever, to mankind, a clear enemy.
- Source: https://quranpedia.net/tafsir/al-isra/53
- Change: marks/encoding only
- [x] ok

### good-neighbour.json

#### 4:36 | good-neighbour

> ۞ وَٱعۡبُدُواْ ٱللَّهَ وَلَا تُشۡرِكُواْ بِهِۦ شَيۡـٔٗاۖ وَبِٱلۡوَٰلِدَيۡنِ إِحۡسَٰنٗا وَبِذِي ٱلۡقُرۡبَىٰ وَٱلۡيَتَٰمَىٰ وَٱلۡمَسَٰكِينِ وَٱلۡجَارِ ذِي ٱلۡقُرۡبَىٰ وَٱلۡجَارِ ٱلۡجُنُبِ وَٱلصَّاحِبِ بِٱلۡجَنۢبِ وَٱبۡنِ ٱلسَّبِيلِ وَمَا مَلَكَتۡ أَيۡمَٰنُكُمۡۗ إِنَّ ٱللَّهَ لَا يُحِبُّ مَن كَانَ مُخۡتَالٗا فَخُورًا

- English (stored): Worship Allāh and associate nothing with Him, and to parents do good, and to relatives, orphans, the needy, the near neighbor, the neighbor farther away, the companion at your side, the traveler, and those whom your right hands possess. Indeed, Allāh does not like those who are self-deluding and boastful,
- Source: https://quranpedia.net/tafsir/an-nisa/36
- Change: rasm + marks/encoding [rasm sample]
- [x] ok

### gratitude.json

#### 14:7 | gratitude

> وَإِذۡ تَأَذَّنَ رَبُّكُمۡ لَئِن شَكَرۡتُمۡ لَأَزِيدَنَّكُمۡۖ وَلَئِن كَفَرۡتُمۡ إِنَّ عَذَابِي لَشَدِيدٞ

- English (stored): And [remember] when your Lord proclaimed, 'If you are grateful, I will surely increase you [in favor]; but if you deny, indeed, My punishment is severe.'"
- Source: https://quranpedia.net/tafsir/ibrahim/7
- Change: marks/encoding only
- [x] ok

#### 16:78 | gratitude

> وَٱللَّهُ أَخۡرَجَكُم مِّنۢ بُطُونِ أُمَّهَٰتِكُمۡ لَا تَعۡلَمُونَ شَيۡـٔٗا وَجَعَلَ لَكُمُ ٱلسَّمۡعَ وَٱلۡأَبۡصَٰرَ وَٱلۡأَفۡـِٔدَةَ لَعَلَّكُمۡ تَشۡكُرُونَ

- English (stored): And Allāh has extracted you from the wombs of your mothers not knowing a thing, and He made for you hearing and vision and hearts [i.e., intellect] that perhaps you would be grateful.
- Source: https://quranpedia.net/tafsir/an-nahl/78
- Change: pause marks + rasm + marks/encoding (old `◌ۙ` -> new `(none)`) [check vs mushaf, rasm sample]
- [x] ok

#### 31:12 | gratitude

> وَلَقَدۡ ءَاتَيۡنَا لُقۡمَٰنَ ٱلۡحِكۡمَةَ أَنِ ٱشۡكُرۡ لِلَّهِۚ وَمَن يَشۡكُرۡ فَإِنَّمَا يَشۡكُرُ لِنَفۡسِهِۦۖ وَمَن كَفَرَ فَإِنَّ ٱللَّهَ غَنِيٌّ حَمِيدٞ

- English (stored): And We had certainly given Luqmān wisdom [and said], "Be grateful to Allāh." And whoever is grateful is grateful for [the benefit of] himself. And whoever denies [His favor] - then indeed, Allāh is Free of need and Praiseworthy.
- Source: https://quranpedia.net/tafsir/luqman/12
- Change: marks/encoding only
- [x] ok

### helping-others.json

#### 5:2 | cooperation, helping-others

> يَٰٓأَيُّهَا ٱلَّذِينَ ءَامَنُواْ لَا تُحِلُّواْ شَعَٰٓئِرَ ٱللَّهِ وَلَا ٱلشَّهۡرَ ٱلۡحَرَامَ وَلَا ٱلۡهَدۡيَ وَلَا ٱلۡقَلَٰٓئِدَ وَلَآ ءَآمِّينَ ٱلۡبَيۡتَ ٱلۡحَرَامَ يَبۡتَغُونَ فَضۡلٗا مِّن رَّبِّهِمۡ وَرِضۡوَٰنٗاۚ وَإِذَا حَلَلۡتُمۡ فَٱصۡطَادُواْۚ وَلَا يَجۡرِمَنَّكُمۡ شَنَـَٔانُ قَوۡمٍ أَن صَدُّوكُمۡ عَنِ ٱلۡمَسۡجِدِ ٱلۡحَرَامِ أَن تَعۡتَدُواْۘ وَتَعَاوَنُواْ عَلَى ٱلۡبِرِّ وَٱلتَّقۡوَىٰۖ وَلَا تَعَاوَنُواْ عَلَى ٱلۡإِثۡمِ وَٱلۡعُدۡوَٰنِۚ وَٱتَّقُواْ ٱللَّهَۖ إِنَّ ٱللَّهَ شَدِيدُ ٱلۡعِقَابِ

- English (stored): O you who have believed, do not violate the rites of Allāh or [the sanctity of] the sacred month or [neglect the marking of] the sacrificial animals and garlanding [them] or [violate the safety of] those coming to the Sacred House seeking bounty from their Lord and [His] approval. But when you come out of iḥrām, then [you may] hunt. And do not let the hatred of a people for having obstructed you from al-Masjid al-Ḥarām lead you to transgress. And cooperate in righteousness and piety, but do not cooperate in sin and aggression. And fear Allāh; indeed, Allāh is severe in penalty.
- Source: https://quranpedia.net/tafsir/al-maida/2
- Change: rasm + marks/encoding [rasm sample]
- [x] ok

#### 90:14 | helping-others

> أَوۡ إِطۡعَٰمٞ فِي يَوۡمٖ ذِي مَسۡغَبَةٖ

- English (stored): Or feeding on a day of severe hunger
- Source: https://quranpedia.net/tafsir/al-balad/14
- Change: marks/encoding only
- [x] ok

### honesty.json

#### 9:119 | honesty

> يَٰٓأَيُّهَا ٱلَّذِينَ ءَامَنُواْ ٱتَّقُواْ ٱللَّهَ وَكُونُواْ مَعَ ٱلصَّٰدِقِينَ

- English (stored): O you who have believed, fear Allāh and be with those who are true.
- Source: https://quranpedia.net/tafsir/at-tawba/119
- Change: marks/encoding only
- [x] ok

#### 5:119 | honesty

> قَالَ ٱللَّهُ هَٰذَا يَوۡمُ يَنفَعُ ٱلصَّٰدِقِينَ صِدۡقُهُمۡۚ لَهُمۡ جَنَّٰتٞ تَجۡرِي مِن تَحۡتِهَا ٱلۡأَنۡهَٰرُ خَٰلِدِينَ فِيهَآ أَبَدٗاۖ رَّضِيَ ٱللَّهُ عَنۡهُمۡ وَرَضُواْ عَنۡهُۚ ذَٰلِكَ ٱلۡفَوۡزُ ٱلۡعَظِيمُ

- English (stored): Allāh will say, "This is the Day when the truthful will benefit from their truthfulness." For them are gardens [in Paradise] beneath which rivers flow, wherein they will abide forever, Allāh being pleased with them, and they with Him. That is the great attainment.
- Source: https://quranpedia.net/tafsir/al-maida/119
- Change: pause marks + marks/encoding (old `◌ۚ ◌ۚ ◌ۚ` -> new `◌ۚ ◌ۖ ◌ۚ`) [check vs mushaf]
- [x] ok

### honouring-parents.json

#### 17:23 | honouring-parents, respecting-elders

> ۞ وَقَضَىٰ رَبُّكَ أَلَّا تَعۡبُدُوٓاْ إِلَّآ إِيَّاهُ وَبِٱلۡوَٰلِدَيۡنِ إِحۡسَٰنًاۚ إِمَّا يَبۡلُغَنَّ عِندَكَ ٱلۡكِبَرَ أَحَدُهُمَآ أَوۡ كِلَاهُمَا فَلَا تَقُل لَّهُمَآ أُفّٖ وَلَا تَنۡهَرۡهُمَا وَقُل لَّهُمَا قَوۡلٗا كَرِيمٗا

- English (stored): And your Lord has decreed that you worship not except Him, and to parents, good treatment. Whether one or both of them reach old age [while] with you, say not to them [so much as], "uff," and do not repel them but speak to them a noble word.
- Source: https://quranpedia.net/tafsir/al-isra/23
- Change: marks/encoding only
- [x] ok

#### 17:24 | honouring-parents, mercy, respecting-elders

> وَٱخۡفِضۡ لَهُمَا جَنَاحَ ٱلذُّلِّ مِنَ ٱلرَّحۡمَةِ وَقُل رَّبِّ ٱرۡحَمۡهُمَا كَمَا رَبَّيَانِي صَغِيرٗا

- English (stored): And lower to them the wing of humility out of mercy and say, "My Lord, have mercy upon them as they brought me up [when I was] small."
- Source: https://quranpedia.net/tafsir/al-isra/24
- Change: marks/encoding only
- [x] ok

#### 31:14 | honouring-parents

> وَوَصَّيۡنَا ٱلۡإِنسَٰنَ بِوَٰلِدَيۡهِ حَمَلَتۡهُ أُمُّهُۥ وَهۡنًا عَلَىٰ وَهۡنٖ وَفِصَٰلُهُۥ فِي عَامَيۡنِ أَنِ ٱشۡكُرۡ لِي وَلِوَٰلِدَيۡكَ إِلَيَّ ٱلۡمَصِيرُ

- English (stored): And We have enjoined upon man [care] for his parents. His mother carried him, [increasing her] in weakness upon weakness, and his weaning is in two years. Be grateful to Me and to your parents; to Me is the [final] destination.
- Source: https://quranpedia.net/tafsir/luqman/14
- Change: marks/encoding only
- [x] ok

### humility.json

#### 25:63 | humility

> وَعِبَادُ ٱلرَّحۡمَٰنِ ٱلَّذِينَ يَمۡشُونَ عَلَى ٱلۡأَرۡضِ هَوۡنٗا وَإِذَا خَاطَبَهُمُ ٱلۡجَٰهِلُونَ قَالُواْ سَلَٰمٗا

- English (stored): And the servants of the Most Merciful are those who walk upon the earth easily, and when the ignorant address them [harshly], they say [words of] peace,
- Source: https://quranpedia.net/tafsir/al-furqan/63
- Change: marks/encoding only
- [x] ok

#### 31:18 | humility

> وَلَا تُصَعِّرۡ خَدَّكَ لِلنَّاسِ وَلَا تَمۡشِ فِي ٱلۡأَرۡضِ مَرَحًاۖ إِنَّ ٱللَّهَ لَا يُحِبُّ كُلَّ مُخۡتَالٖ فَخُورٖ

- English (stored): And do not turn your cheek [in contempt] toward people and do not walk through the earth exultantly. Indeed, Allāh does not like everyone self-deluded and boastful.
- Source: https://quranpedia.net/tafsir/luqman/18
- Change: marks/encoding only
- [x] ok

#### 17:37 | humility

> وَلَا تَمۡشِ فِي ٱلۡأَرۡضِ مَرَحًاۖ إِنَّكَ لَن تَخۡرِقَ ٱلۡأَرۡضَ وَلَن تَبۡلُغَ ٱلۡجِبَالَ طُولٗا

- English (stored): And do not walk upon the earth exultantly. Indeed, you will never tear the earth [apart], and you will never reach the mountains in height.
- Source: https://quranpedia.net/tafsir/al-isra/37
- Change: marks/encoding only
- [x] ok

### justice.json

#### 4:135 | justice

> ۞ يَٰٓأَيُّهَا ٱلَّذِينَ ءَامَنُواْ كُونُواْ قَوَّٰمِينَ بِٱلۡقِسۡطِ شُهَدَآءَ لِلَّهِ وَلَوۡ عَلَىٰٓ أَنفُسِكُمۡ أَوِ ٱلۡوَٰلِدَيۡنِ وَٱلۡأَقۡرَبِينَۚ إِن يَكُنۡ غَنِيًّا أَوۡ فَقِيرٗا فَٱللَّهُ أَوۡلَىٰ بِهِمَاۖ فَلَا تَتَّبِعُواْ ٱلۡهَوَىٰٓ أَن تَعۡدِلُواْۚ وَإِن تَلۡوُۥٓاْ أَوۡ تُعۡرِضُواْ فَإِنَّ ٱللَّهَ كَانَ بِمَا تَعۡمَلُونَ خَبِيرٗا

- English (stored): O you who have believed, be persistently standing firm in justice, witnesses for Allāh, even if it be against yourselves or parents and relatives. Whether one is rich or poor, Allāh is more worthy of both. So follow not [personal] inclination, lest you not be just. And if you distort [your testimony] or refuse [to give it], then indeed Allāh is ever, of what you do, Aware.
- Source: https://quranpedia.net/tafsir/an-nisa/135
- Change: rasm + marks/encoding [rasm sample]
- [x] ok

#### 5:8 | justice

> يَٰٓأَيُّهَا ٱلَّذِينَ ءَامَنُواْ كُونُواْ قَوَّٰمِينَ لِلَّهِ شُهَدَآءَ بِٱلۡقِسۡطِۖ وَلَا يَجۡرِمَنَّكُمۡ شَنَـَٔانُ قَوۡمٍ عَلَىٰٓ أَلَّا تَعۡدِلُواْۚ ٱعۡدِلُواْ هُوَ أَقۡرَبُ لِلتَّقۡوَىٰۖ وَٱتَّقُواْ ٱللَّهَۚ إِنَّ ٱللَّهَ خَبِيرُۢ بِمَا تَعۡمَلُونَ

- English (stored): O you who have believed, be persistently standing firm for Allāh, witnesses in justice, and do not let the hatred of a people prevent you from being just. Be just; that is nearer to righteousness. And fear Allāh; indeed, Allāh is [fully] Aware of what you do.
- Source: https://quranpedia.net/tafsir/al-maida/8
- Change: rasm + marks/encoding [rasm sample]
- [x] ok

### keeping-promises.json

#### 17:34 | keeping-promises, caring-for-orphans

> وَلَا تَقۡرَبُواْ مَالَ ٱلۡيَتِيمِ إِلَّا بِٱلَّتِي هِيَ أَحۡسَنُ حَتَّىٰ يَبۡلُغَ أَشُدَّهُۥۚ وَأَوۡفُواْ بِٱلۡعَهۡدِۖ إِنَّ ٱلۡعَهۡدَ كَانَ مَسۡـُٔولٗا

- English (stored): And do not approach the property of an orphan, except in the way that is best, until he reaches maturity. And fulfill [every] commitment. Indeed, the commitment is ever [that about which one will be] questioned.
- Source: https://quranpedia.net/tafsir/al-isra/34
- Change: rasm + marks/encoding [rasm sample]
- [x] ok

### kind-words.json

#### 2:83 | kind-words

> وَإِذۡ أَخَذۡنَا مِيثَٰقَ بَنِيٓ إِسۡرَٰٓءِيلَ لَا تَعۡبُدُونَ إِلَّا ٱللَّهَ وَبِٱلۡوَٰلِدَيۡنِ إِحۡسَانٗا وَذِي ٱلۡقُرۡبَىٰ وَٱلۡيَتَٰمَىٰ وَٱلۡمَسَٰكِينِ وَقُولُواْ لِلنَّاسِ حُسۡنٗا وَأَقِيمُواْ ٱلصَّلَوٰةَ وَءَاتُواْ ٱلزَّكَوٰةَ ثُمَّ تَوَلَّيۡتُمۡ إِلَّا قَلِيلٗا مِّنكُمۡ وَأَنتُم مُّعۡرِضُونَ

- English (stored): And [recall] when We took the covenant from the Children of Israel, [enjoining upon them], "Do not worship except Allāh; and to parents do good and to relatives, orphans, and the needy. And speak to people good [words] and establish prayer and give zakāh." Then you turned away, except a few of you, and you were refusing.
- Source: https://quranpedia.net/tafsir/al-baqara/83
- Change: rasm + marks/encoding [rasm sample]
- [x] ok

### kindness-to-animals.json

#### 6:38 | kindness-to-animals

> وَمَا مِن دَآبَّةٖ فِي ٱلۡأَرۡضِ وَلَا طَٰٓئِرٖ يَطِيرُ بِجَنَاحَيۡهِ إِلَّآ أُمَمٌ أَمۡثَالُكُمۚ مَّا فَرَّطۡنَا فِي ٱلۡكِتَٰبِ مِن شَيۡءٖۚ ثُمَّ إِلَىٰ رَبِّهِمۡ يُحۡشَرُونَ

- English (stored): And there is no creature on [or within] the earth or bird that flies with its wings except [that they are] communities like you. We have not neglected in the Register a thing. Then unto their Lord they will be gathered.
- Source: https://quranpedia.net/tafsir/al-anam/38
- Change: marks/encoding only
- [x] ok

#### 27:18 | kindness-to-animals

> حَتَّىٰٓ إِذَآ أَتَوۡاْ عَلَىٰ وَادِ ٱلنَّمۡلِ قَالَتۡ نَمۡلَةٞ يَٰٓأَيُّهَا ٱلنَّمۡلُ ٱدۡخُلُواْ مَسَٰكِنَكُمۡ لَا يَحۡطِمَنَّكُمۡ سُلَيۡمَٰنُ وَجُنُودُهُۥ وَهُمۡ لَا يَشۡعُرُونَ

- English (stored): Until, when they came upon the valley of the ants, an ant said, "O ants, enter your dwellings that you not be crushed by Solomon and his soldiers while they perceive not."
- Source: https://quranpedia.net/tafsir/an-naml/18
- Change: marks/encoding only
- [x] ok

### love-of-the-prophet.json

#### 33:21 | love-of-the-prophet

> لَّقَدۡ كَانَ لَكُمۡ فِي رَسُولِ ٱللَّهِ أُسۡوَةٌ حَسَنَةٞ لِّمَن كَانَ يَرۡجُواْ ٱللَّهَ وَٱلۡيَوۡمَ ٱلۡأٓخِرَ وَذَكَرَ ٱللَّهَ كَثِيرٗا

- English (stored): There has certainly been for you in the Messenger of Allāh an excellent pattern for anyone whose hope is in Allāh and the Last Day and [who] remembers Allāh often.
- Source: https://quranpedia.net/tafsir/al-ahzab/21
- Change: rasm + marks/encoding [rasm sample]
- [x] ok

#### 33:56 | love-of-the-prophet

> إِنَّ ٱللَّهَ وَمَلَٰٓئِكَتَهُۥ يُصَلُّونَ عَلَى ٱلنَّبِيِّۚ يَٰٓأَيُّهَا ٱلَّذِينَ ءَامَنُواْ صَلُّواْ عَلَيۡهِ وَسَلِّمُواْ تَسۡلِيمًا

- English (stored): Indeed, Allāh confers blessing upon the Prophet, and His angels [ask Him to do so]. O you who have believed, ask [Allāh to confer] blessing upon him and ask [Allāh to grant him] peace.
- Source: https://quranpedia.net/tafsir/al-ahzab/56
- Change: marks/encoding only
- [x] ok

### mercy.json

#### 21:107 | mercy, love-of-the-prophet

> وَمَآ أَرۡسَلۡنَٰكَ إِلَّا رَحۡمَةٗ لِّلۡعَٰلَمِينَ

- English (stored): And We have not sent you, [O Muḥammad], except as a mercy to the worlds.
- Source: https://quranpedia.net/tafsir/al-anbiya/107
- Change: marks/encoding only
- [x] ok

#### 9:128 | mercy, love-of-the-prophet

> لَقَدۡ جَآءَكُمۡ رَسُولٞ مِّنۡ أَنفُسِكُمۡ عَزِيزٌ عَلَيۡهِ مَا عَنِتُّمۡ حَرِيصٌ عَلَيۡكُم بِٱلۡمُؤۡمِنِينَ رَءُوفٞ رَّحِيمٞ

- English (stored): There has certainly come to you a Messenger from among yourselves. Grievous to him is what you suffer; [he is] concerned over you [i.e., your guidance] and to the believers is kind and merciful.
- Source: https://quranpedia.net/tafsir/at-tawba/128
- Change: marks/encoding only
- [x] ok

#### 90:17 | mercy

> ثُمَّ كَانَ مِنَ ٱلَّذِينَ ءَامَنُواْ وَتَوَاصَوۡاْ بِٱلصَّبۡرِ وَتَوَاصَوۡاْ بِٱلۡمَرۡحَمَةِ

- English (stored): And then being among those who believed and advised one another to patience and advised one another to compassion.
- Source: https://quranpedia.net/tafsir/al-balad/17
- Change: marks/encoding only
- [x] ok

### modesty.json

#### 28:25 | modesty

> فَجَآءَتۡهُ إِحۡدَىٰهُمَا تَمۡشِي عَلَى ٱسۡتِحۡيَآءٖ قَالَتۡ إِنَّ أَبِي يَدۡعُوكَ لِيَجۡزِيَكَ أَجۡرَ مَا سَقَيۡتَ لَنَاۚ فَلَمَّا جَآءَهُۥ وَقَصَّ عَلَيۡهِ ٱلۡقَصَصَ قَالَ لَا تَخَفۡۖ نَجَوۡتَ مِنَ ٱلۡقَوۡمِ ٱلظَّٰلِمِينَ

- English (stored): Then one of the two women came to him walking with shyness. She said, "Indeed, my father invites you that he may reward you for having watered for us." So when he came to him and related to him the story, he said, "Fear not. You have escaped from the wrongdoing people."
- Source: https://quranpedia.net/tafsir/al-qasas/25
- Change: rasm + marks/encoding [rasm sample]
- [x] ok

#### 7:26 | modesty

> يَٰبَنِيٓ ءَادَمَ قَدۡ أَنزَلۡنَا عَلَيۡكُمۡ لِبَاسٗا يُوَٰرِي سَوۡءَٰتِكُمۡ وَرِيشٗاۖ وَلِبَاسُ ٱلتَّقۡوَىٰ ذَٰلِكَ خَيۡرٞۚ ذَٰلِكَ مِنۡ ءَايَٰتِ ٱللَّهِ لَعَلَّهُمۡ يَذَّكَّرُونَ

- English (stored): O children of Adam, We have bestowed upon you clothing to conceal your private parts and as adornment. But the clothing of righteousness - that is best. That is from the signs of Allāh that perhaps they will remember.
- Source: https://quranpedia.net/tafsir/al-araf/26
- Change: marks/encoding only
- [x] ok

#### 33:59 | modesty

> يَٰٓأَيُّهَا ٱلنَّبِيُّ قُل لِّأَزۡوَٰجِكَ وَبَنَاتِكَ وَنِسَآءِ ٱلۡمُؤۡمِنِينَ يُدۡنِينَ عَلَيۡهِنَّ مِن جَلَٰبِيبِهِنَّۚ ذَٰلِكَ أَدۡنَىٰٓ أَن يُعۡرَفۡنَ فَلَا يُؤۡذَيۡنَۗ وَكَانَ ٱللَّهُ غَفُورٗا رَّحِيمٗا

- English (stored): O Prophet, tell your wives and your daughters and the women of the believers to bring down over themselves [part] of their outer garments. That is more suitable that they will be known and not be abused. And ever is Allāh Forgiving and Merciful.
- Source: https://quranpedia.net/tafsir/al-ahzab/59
- Change: marks/encoding only
- [x] ok

### not-wasting.json

#### 17:26 | not-wasting, family-ties

> وَءَاتِ ذَا ٱلۡقُرۡبَىٰ حَقَّهُۥ وَٱلۡمِسۡكِينَ وَٱبۡنَ ٱلسَّبِيلِ وَلَا تُبَذِّرۡ تَبۡذِيرًا

- English (stored): And give the relative his right, and [also] the poor and the traveler, and do not spend wastefully.
- Source: https://quranpedia.net/tafsir/al-isra/26
- Change: marks/encoding only
- [x] ok

### patience.json

#### 39:10 | patience

> قُلۡ يَٰعِبَادِ ٱلَّذِينَ ءَامَنُواْ ٱتَّقُواْ رَبَّكُمۡۚ لِلَّذِينَ أَحۡسَنُواْ فِي هَٰذِهِ ٱلدُّنۡيَا حَسَنَةٞۗ وَأَرۡضُ ٱللَّهِ وَٰسِعَةٌۗ إِنَّمَا يُوَفَّى ٱلصَّٰبِرُونَ أَجۡرَهُم بِغَيۡرِ حِسَابٖ

- English (stored): Say, "O My servants who have believed, fear your Lord. For those who do good in this world is good, and the earth of Allāh is spacious. Indeed, the patient will be given their reward without account [i.e., limit]."
- Source: https://quranpedia.net/tafsir/az-zumar/10
- Change: marks/encoding only
- [x] ok

#### 16:127 | patience

> وَٱصۡبِرۡ وَمَا صَبۡرُكَ إِلَّا بِٱللَّهِۚ وَلَا تَحۡزَنۡ عَلَيۡهِمۡ وَلَا تَكُ فِي ضَيۡقٖ مِّمَّا يَمۡكُرُونَ

- English (stored): And be patient, [O Muḥammad], and your patience is not but through Allāh. And do not grieve over them and do not be in distress over what they conspire.
- Source: https://quranpedia.net/tafsir/an-nahl/127
- Change: marks/encoding only
- [x] ok

### prayer.json

#### 20:14 | prayer

> إِنَّنِيٓ أَنَا ٱللَّهُ لَآ إِلَٰهَ إِلَّآ أَنَا۠ فَٱعۡبُدۡنِي وَأَقِمِ ٱلصَّلَوٰةَ لِذِكۡرِيٓ

- English (stored): Indeed, I am Allāh. There is no deity except Me, so worship Me and establish prayer for My remembrance.
- Source: https://quranpedia.net/tafsir/ta-ha/14
- Change: rasm + marks/encoding [rasm sample]
- [x] ok

#### 2:153 | prayer, patience

> يَٰٓأَيُّهَا ٱلَّذِينَ ءَامَنُواْ ٱسۡتَعِينُواْ بِٱلصَّبۡرِ وَٱلصَّلَوٰةِۚ إِنَّ ٱللَّهَ مَعَ ٱلصَّٰبِرِينَ

- English (stored): O you who have believed, seek help through patience and prayer. Indeed, Allāh is with the patient.
- Source: https://quranpedia.net/tafsir/al-baqara/153
- Change: rasm + marks/encoding [rasm sample]
- [x] ok

#### 29:45 | prayer

> ٱتۡلُ مَآ أُوحِيَ إِلَيۡكَ مِنَ ٱلۡكِتَٰبِ وَأَقِمِ ٱلصَّلَوٰةَۖ إِنَّ ٱلصَّلَوٰةَ تَنۡهَىٰ عَنِ ٱلۡفَحۡشَآءِ وَٱلۡمُنكَرِۗ وَلَذِكۡرُ ٱللَّهِ أَكۡبَرُۗ وَٱللَّهُ يَعۡلَمُ مَا تَصۡنَعُونَ

- English (stored): Recite, [O Muḥammad], what has been revealed to you of the Book and establish prayer. Indeed, prayer prohibits immorality and wrongdoing, and the remembrance of Allāh is greater. And Allāh knows that which you do.
- Source: https://quranpedia.net/tafsir/al-ankabut/45
- Change: rasm + marks/encoding [rasm sample]
- [x] ok

### remembering-allah.json

#### 13:28 | remembering-allah

> ٱلَّذِينَ ءَامَنُواْ وَتَطۡمَئِنُّ قُلُوبُهُم بِذِكۡرِ ٱللَّهِۗ أَلَا بِذِكۡرِ ٱللَّهِ تَطۡمَئِنُّ ٱلۡقُلُوبُ

- English (stored): Those who have believed and whose hearts are assured by the remembrance of Allāh. Unquestionably, by the remembrance of Allāh hearts are assured."
- Source: https://quranpedia.net/tafsir/ar-rad/28
- Change: marks/encoding only
- [x] ok

#### 33:41 | remembering-allah

> يَٰٓأَيُّهَا ٱلَّذِينَ ءَامَنُواْ ٱذۡكُرُواْ ٱللَّهَ ذِكۡرٗا كَثِيرٗا

- English (stored): O you who have believed, remember Allāh with much remembrance
- Source: https://quranpedia.net/tafsir/al-ahzab/41
- Change: marks/encoding only
- [x] ok

### seeking-knowledge.json

#### 20:114 | seeking-knowledge

> فَتَعَٰلَى ٱللَّهُ ٱلۡمَلِكُ ٱلۡحَقُّۗ وَلَا تَعۡجَلۡ بِٱلۡقُرۡءَانِ مِن قَبۡلِ أَن يُقۡضَىٰٓ إِلَيۡكَ وَحۡيُهُۥۖ وَقُل رَّبِّ زِدۡنِي عِلۡمٗا

- English (stored): So high [above all] is Allāh, the Sovereign, the Truth. And, [O Muḥammad], do not hasten with [recitation of] the Qur’ān before its revelation is completed to you, and say, "My Lord, increase me in knowledge."
- Source: https://quranpedia.net/tafsir/ta-ha/114
- Change: marks/encoding only
- [x] ok

#### 39:9 | seeking-knowledge

> أَمَّنۡ هُوَ قَٰنِتٌ ءَانَآءَ ٱلَّيۡلِ سَاجِدٗا وَقَآئِمٗا يَحۡذَرُ ٱلۡأٓخِرَةَ وَيَرۡجُواْ رَحۡمَةَ رَبِّهِۦۗ قُلۡ هَلۡ يَسۡتَوِي ٱلَّذِينَ يَعۡلَمُونَ وَٱلَّذِينَ لَا يَعۡلَمُونَۗ إِنَّمَا يَتَذَكَّرُ أُوْلُواْ ٱلۡأَلۡبَٰبِ

- English (stored): Is one who is devoutly obedient during periods of the night, prostrating and standing [in prayer], fearing the Hereafter and hoping for the mercy of his Lord, [like one who does not]? Say, "Are those who know equal to those who do not know?" Only they will remember [who are] people of understanding.
- Source: https://quranpedia.net/tafsir/az-zumar/9
- Change: rasm + marks/encoding [rasm sample]
- [x] ok

#### 58:11 | seeking-knowledge

> يَٰٓأَيُّهَا ٱلَّذِينَ ءَامَنُوٓاْ إِذَا قِيلَ لَكُمۡ تَفَسَّحُواْ فِي ٱلۡمَجَٰلِسِ فَٱفۡسَحُواْ يَفۡسَحِ ٱللَّهُ لَكُمۡۖ وَإِذَا قِيلَ ٱنشُزُواْ فَٱنشُزُواْ يَرۡفَعِ ٱللَّهُ ٱلَّذِينَ ءَامَنُواْ مِنكُمۡ وَٱلَّذِينَ أُوتُواْ ٱلۡعِلۡمَ دَرَجَٰتٖۚ وَٱللَّهُ بِمَا تَعۡمَلُونَ خَبِيرٞ

- English (stored): O you who have believed, when you are told, "Space yourselves" in assemblies, then make space; Allāh will make space for you. And when you are told, "Arise," then arise; Allāh will raise those who have believed among you and those who were given knowledge, by degrees. And Allāh is Aware of what you do.
- Source: https://quranpedia.net/tafsir/al-mujadila/11
- Change: marks/encoding only
- [x] ok

### sincerity.json

#### 98:5 | sincerity, prayer, charity

> وَمَآ أُمِرُوٓاْ إِلَّا لِيَعۡبُدُواْ ٱللَّهَ مُخۡلِصِينَ لَهُ ٱلدِّينَ حُنَفَآءَ وَيُقِيمُواْ ٱلصَّلَوٰةَ وَيُؤۡتُواْ ٱلزَّكَوٰةَۚ وَذَٰلِكَ دِينُ ٱلۡقَيِّمَةِ

- English (stored): And they were not commanded except to worship Allāh, [being] sincere to Him in religion, inclining to truth, and to establish prayer and to give zakāh. And that is the correct religion.
- Source: https://quranpedia.net/tafsir/al-bayyina/5
- Change: rasm + marks/encoding [rasm sample]
- [x] ok

#### 76:9 | sincerity, generosity, charity

> إِنَّمَا نُطۡعِمُكُمۡ لِوَجۡهِ ٱللَّهِ لَا نُرِيدُ مِنكُمۡ جَزَآءٗ وَلَا شُكُورًا

- English (stored): [Saying], "We feed you only for the face [i.e., approval] of Allāh. We wish not from you reward or gratitude.
- Source: https://quranpedia.net/tafsir/al-insan/9
- Change: marks/encoding only
- [x] ok

### spreading-salam.json

#### 4:86 | spreading-salam

> وَإِذَا حُيِّيتُم بِتَحِيَّةٖ فَحَيُّواْ بِأَحۡسَنَ مِنۡهَآ أَوۡ رُدُّوهَآۗ إِنَّ ٱللَّهَ كَانَ عَلَىٰ كُلِّ شَيۡءٍ حَسِيبًا

- English (stored): And when you are greeted with a greeting, greet [in return] with one better than it or [at least] return it [in a like manner]. Indeed Allāh is ever, over all things, an Accountant.
- Source: https://quranpedia.net/tafsir/an-nisa/86
- Change: marks/encoding only
- [x] ok

#### 24:27 | spreading-salam

> يَٰٓأَيُّهَا ٱلَّذِينَ ءَامَنُواْ لَا تَدۡخُلُواْ بُيُوتًا غَيۡرَ بُيُوتِكُمۡ حَتَّىٰ تَسۡتَأۡنِسُواْ وَتُسَلِّمُواْ عَلَىٰٓ أَهۡلِهَاۚ ذَٰلِكُمۡ خَيۡرٞ لَّكُمۡ لَعَلَّكُمۡ تَذَكَّرُونَ

- English (stored): O you who have believed, do not enter houses other than your own houses until you ascertain welcome and greet their inhabitants. That is best for you; perhaps you will be reminded [i.e., advised].
- Source: https://quranpedia.net/tafsir/an-nur/27
- Change: marks/encoding only
- [x] ok

### table-manners.json

#### 7:31 | table-manners, not-wasting

> ۞ يَٰبَنِيٓ ءَادَمَ خُذُواْ زِينَتَكُمۡ عِندَ كُلِّ مَسۡجِدٖ وَكُلُواْ وَٱشۡرَبُواْ وَلَا تُسۡرِفُوٓاْۚ إِنَّهُۥ لَا يُحِبُّ ٱلۡمُسۡرِفِينَ

- English (stored): O children of Adam, take your adornment [i.e., wear your clothing] at every masjid, and eat and drink, but be not excessive. Indeed, He likes not those who commit excess.
- Source: https://quranpedia.net/tafsir/al-araf/31
- Change: marks/encoding only
- [x] ok

#### 2:172 | table-manners

> يَٰٓأَيُّهَا ٱلَّذِينَ ءَامَنُواْ كُلُواْ مِن طَيِّبَٰتِ مَا رَزَقۡنَٰكُمۡ وَٱشۡكُرُواْ لِلَّهِ إِن كُنتُمۡ إِيَّاهُ تَعۡبُدُونَ

- English (stored): O you who have believed, eat from the good [i.e., lawful] things which We have provided for you and be grateful to Allāh if it is [indeed] Him that you worship.
- Source: https://quranpedia.net/tafsir/al-baqara/172
- Change: marks/encoding only
- [x] ok

### trust-in-allah.json

#### 3:159 | trust-in-allah, love-of-the-prophet

> فَبِمَا رَحۡمَةٖ مِّنَ ٱللَّهِ لِنتَ لَهُمۡۖ وَلَوۡ كُنتَ فَظًّا غَلِيظَ ٱلۡقَلۡبِ لَٱنفَضُّواْ مِنۡ حَوۡلِكَۖ فَٱعۡفُ عَنۡهُمۡ وَٱسۡتَغۡفِرۡ لَهُمۡ وَشَاوِرۡهُمۡ فِي ٱلۡأَمۡرِۖ فَإِذَا عَزَمۡتَ فَتَوَكَّلۡ عَلَى ٱللَّهِۚ إِنَّ ٱللَّهَ يُحِبُّ ٱلۡمُتَوَكِّلِينَ

- English (stored): So by mercy from Allāh, [O Muḥammad], you were lenient with them. And if you had been rude [in speech] and harsh in heart, they would have disbanded from about you. So pardon them and ask forgiveness for them and consult them in the matter. And when you have decided, then rely upon Allāh. Indeed, Allāh loves those who rely [upon Him].
- Source: https://quranpedia.net/tafsir/aal-imran/159
- Change: marks/encoding only
- [x] ok

#### 65:3 | trust-in-allah

> وَيَرۡزُقۡهُ مِنۡ حَيۡثُ لَا يَحۡتَسِبُۚ وَمَن يَتَوَكَّلۡ عَلَى ٱللَّهِ فَهُوَ حَسۡبُهُۥٓۚ إِنَّ ٱللَّهَ بَٰلِغُ أَمۡرِهِۦۚ قَدۡ جَعَلَ ٱللَّهُ لِكُلِّ شَيۡءٖ قَدۡرٗا

- English (stored): And will provide for him from where he does not expect. And whoever relies upon Allāh - then He is sufficient for him. Indeed, Allāh will accomplish His purpose. Allāh has already set for everything a [decreed] extent.
- Source: https://quranpedia.net/tafsir/at-talaq/3
- Change: marks/encoding only
- [x] ok

### trustworthiness.json

#### 4:58 | trustworthiness, justice

> ۞ إِنَّ ٱللَّهَ يَأۡمُرُكُمۡ أَن تُؤَدُّواْ ٱلۡأَمَٰنَٰتِ إِلَىٰٓ أَهۡلِهَا وَإِذَا حَكَمۡتُم بَيۡنَ ٱلنَّاسِ أَن تَحۡكُمُواْ بِٱلۡعَدۡلِۚ إِنَّ ٱللَّهَ نِعِمَّا يَعِظُكُم بِهِۦٓۗ إِنَّ ٱللَّهَ كَانَ سَمِيعَۢا بَصِيرٗا

- English (stored): Indeed, Allāh commands you to render trusts to whom they are due and when you judge between people to judge with justice. Excellent is that which Allāh instructs you. Indeed, Allāh is ever Hearing and Seeing.
- Source: https://quranpedia.net/tafsir/an-nisa/58
- Change: marks/encoding only
- [x] ok

#### 23:8 | trustworthiness, keeping-promises

> وَٱلَّذِينَ هُمۡ لِأَمَٰنَٰتِهِمۡ وَعَهۡدِهِمۡ رَٰعُونَ

- English (stored): And they who are to their trusts and their promises attentive
- Source: https://quranpedia.net/tafsir/al-muminun/8
- Change: marks/encoding only
- [x] ok

#### 28:26 | trustworthiness

> قَالَتۡ إِحۡدَىٰهُمَا يَٰٓأَبَتِ ٱسۡتَـٔۡجِرۡهُۖ إِنَّ خَيۡرَ مَنِ ٱسۡتَـٔۡجَرۡتَ ٱلۡقَوِيُّ ٱلۡأَمِينُ

- English (stored): One of the women said, "O my father, hire him. Indeed, the best one you can hire is the strong and the trustworthy."
- Source: https://quranpedia.net/tafsir/al-qasas/26
- Change: rasm + marks/encoding [rasm sample]
- [x] ok

## After you approve

Run from the repo root. Marking by file name approves every verse in that file; if you did not tick some verse, pass `verse:<surah>:<ayah>` refs for the approved ones instead of the file name.

```bash
cd backend/session_moral_context/content
python3 tools/mark_reviewed.py --by "Abdulrahman Salamah" --at $(date +%F) \
  avoiding-backbiting.json brotherhood.json caring-for-orphans.json charity.json cleanliness.json contentment.json cooperation.json courage.json family-ties.json forgiveness.json generosity.json good-character.json good-neighbour.json gratitude.json helping-others.json honesty.json honouring-parents.json humility.json justice.json keeping-promises.json kind-words.json kindness-to-animals.json love-of-the-prophet.json mercy.json modesty.json not-wasting.json patience.json prayer.json remembering-allah.json seeking-knowledge.json sincerity.json spreading-salam.json table-manners.json trust-in-allah.json trustworthiness.json
python3 tools/mark_reviewed.py --check        # must print: all reviews valid
```
