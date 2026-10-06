// Run with: node frontend/scripts/check-source-cards.mjs   (npm run check:cards)
// cards-spec (05): labels, the two tiers, the sahih-only guard, citation lines, verse markers, the real decoder
// path for the LiveKit `reference` topic, the AI strings and the privacy content. Fixtures are placeholders only:
// no Quran or hadith text anywhere in this file.
import assert from 'node:assert/strict';
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { runInNewContext } from 'node:vm';

const srcRoot = new URL('../src/', import.meta.url);
const readSrc = (name) => readFileSync(new URL(name, srcRoot), 'utf8');
const readSource = (name) => readSrc(`features/child/sources/${name}`);
// Objects built inside the vm have another realm's prototypes; deepEqual needs plain copies.
const plain = (v) => JSON.parse(JSON.stringify(v));
const withoutImports = (source) => source.replace(/^import .*;\r?$/gm, '').replace(/^export /gm, '');

// The decoder as it ships in useLiveKitRoom.js: parseData() feeds the `reference` topic handlers.
const liveKit = readSrc('hooks/useLiveKitRoom.js');
const pdStart = liveKit.indexOf('function parseData(payload)');
const pdEnd = liveKit.indexOf('\nconst AGENT_STATE_ATTR', pdStart);
assert.ok(pdStart >= 0 && pdEnd > pdStart, 'parseData() not found in useLiveKitRoom.js');
assert.match(liveKit, /topic === 'reference'[\s\S]{0,120}referenceHandlersRef\.current\.forEach\(\(handler\) => handler\(data\)\)/);

// Evaluate the real modules without installing React or a JSX test runner.
const api = runInNewContext(`
  ${withoutImports(readSource('surahNames.js'))}
  ${withoutImports(readSource('safeUrl.js'))}
  ${withoutImports(readSource('ayahCounts.js'))}
  ${withoutImports(readSource('quranText.js'))}
  ${withoutImports(readSource('sourceLabels.js'))}
  ${withoutImports(readSource('useSourceCards.js').split('export default function useSourceCards')[0])}
  ${withoutImports(readSource('mockReference.js'))}
  ${liveKit.slice(pdStart, pdEnd)}
  ({
    safeAudioUrl, safeSourceUrl, safeTranslationUrl, sourceHostForType, normalizeReference, HAFS_AYAH_COUNTS,
    toDisplayArabic, splitVerseMarkers, hasBrokenMarker, verseMarkerRefs, quranAudioUrl, surahName, SURAH_EN, SURAH_AR,
    SOURCE_LABELS, EXPLANATION_HEADER, RECITATION_CREDIT, RECITATION_AUDIO_SOURCE_URL, normalizeGrade, sourceHeader,
    fillHeader, hadithCitationPieces, CITATION_SEPARATOR, tafsirCitationPieces, translationLine, verseCaption, surahLine,
    verseRefLabel, recitationCredit, recitationCreditParts, segmentsHaveAudio, openSourceLabel, bookName, graderName,
    MOCK_KINDS, buildMockReference, parseData, MAX_SOURCE_CARDS,
  });
`, { URL, TextDecoder, Number, window: { location: { origin: 'https://app.example' } } });
const {
  safeAudioUrl, safeSourceUrl, safeTranslationUrl, normalizeReference, HAFS_AYAH_COUNTS, toDisplayArabic, splitVerseMarkers,
  hasBrokenMarker, verseMarkerRefs, quranAudioUrl, surahName, SURAH_EN, SURAH_AR, SOURCE_LABELS, EXPLANATION_HEADER,
  RECITATION_CREDIT, RECITATION_AUDIO_SOURCE_URL, normalizeGrade, sourceHeader, fillHeader, hadithCitationPieces,
  CITATION_SEPARATOR, tafsirCitationPieces, translationLine, verseCaption, surahLine, verseRefLabel, recitationCredit,
  recitationCreditParts, segmentsHaveAudio, openSourceLabel, MOCK_KINDS, buildMockReference, parseData,
} = api;

// ---------------------------------------------------------------- URL safety (unchanged rules)
for (const value of [undefined, null, '', ' \t\n', 123, false, {}, ['clip.mp3']]) {
  assert.equal(safeAudioUrl(value), null, `Audio must reject ${String(value)}`);
  assert.equal(safeSourceUrl(value), null);
  assert.equal(safeTranslationUrl(value), null);
}
assert.equal(safeAudioUrl('/recitation.mp3'), 'https://app.example/recitation.mp3');
assert.equal(safeAudioUrl('https://audio.example/clip.mp3'), 'https://audio.example/clip.mp3');
for (const value of ['javascript:alert(1)', 'data:audio/mpeg;base64,AA==', 'http://audio.example/clip.mp3']) {
  assert.equal(safeAudioUrl(value), null);
}
assert.equal(safeSourceUrl('https://sub.dorar.net/placeholder'), 'https://sub.dorar.net/placeholder');
for (const value of ['javascript:alert(1)', 'https://dorar.net.evil.example/placeholder', 'https://dorar.net@evil.example/placeholder']) {
  assert.equal(safeSourceUrl(value), null);
}
assert.equal(safeTranslationUrl('https://hadeethenc.com/en/browse/hadith/12'), 'https://hadeethenc.com/en/browse/hadith/12');
for (const value of ['https://example.com/x', 'javascript:alert(1)', 'https://hadeethenc.com.evil.example/x', 'http://hadeethenc.com/x']) {
  assert.equal(safeTranslationUrl(value), null, `translation link must reject ${value}`);
}

// ---------------------------------------------------------------- fixtures (placeholders only)
const verse = {
  id: 42, type: 'verse', kind: 'scripture', arabic_text: '[bank text]', surah: 1, ayah: 1,
  source_url: 'https://quranpedia.net/placeholder',
};
const hadith = {
  id: 43, type: 'hadith', kind: 'scripture', arabic_text: '[bank text]', book: 'Sahih al-Bukhari', number: 12,
  grade: 'صحيح', grader: 'البخاري', source_url: 'https://dorar.net/placeholder',
};
const faq = {
  id: 44, type: 'faq', kind: 'source_excerpt', title: '[question]', arabic_text: '[bank text]', source_url: 'https://dawa.center/placeholder',
};

// ---------------------------------------------------------------- normalizeReference: ids, text, citation bounds
const normalized = normalizeReference({ ...verse, extra: 'discard', english_text: 123, arabic_text: ' [bank text] ' });
assert.equal(normalized.id, '42');
assert.equal(normalized.arabic_text, ' [bank text] ', 'scripture text is kept verbatim, never trimmed');
assert.equal(normalized.surah, '1');
assert.equal(normalized.ayah, '1');
assert.equal(normalized.extra, undefined);
assert.equal(normalized.english_text, undefined);
assert.equal(normalized.source_site, 'quranpedia.net');
assert.ok(normalizeReference({ ...verse, id: 'bank-id', surah: '114', ayah: '6' }));
for (const arabic_text of [undefined, null, '', '  ', 123, false, {}, []]) {
  assert.equal(normalizeReference({ ...verse, arabic_text }), null);
}
for (const id of [undefined, null, '', NaN, Infinity, {}, []]) {
  assert.equal(normalizeReference({ ...verse, id }), null);
}
for (const field of ['surah', 'ayah']) {
  for (const value of [undefined, null, '', 0, -1, 1.5, NaN, Infinity, 'nope', '1.5', '1e0', '0x1', '9007199254740993']) {
    assert.equal(normalizeReference({ ...verse, [field]: value }), null, `${field} must reject ${String(value)}`);
  }
}
assert.equal(normalizeReference({ ...verse, surah: 115 }), null);
assert.equal(HAFS_AYAH_COUNTS.length, 114);
assert.equal(HAFS_AYAH_COUNTS.reduce((sum, count) => sum + count, 0), 6236);
for (const [index, count] of HAFS_AYAH_COUNTS.entries()) {
  assert.ok(normalizeReference({ ...verse, surah: index + 1, ayah: count }));
  assert.equal(normalizeReference({ ...verse, surah: index + 1, ayah: count + 1 }), null);
}
assert.equal(normalizeReference({ ...verse, surah: 1, ayah: 8 }), null);
assert.equal(normalizeReference({ ...verse, surah: 2, ayah: 287 }), null);

// kind must match the type; unknown types and hosts drop the card
assert.equal(normalizeReference({ ...verse, kind: 'source_excerpt' }), null);
assert.equal(normalizeReference({ ...faq, kind: 'scripture' }), null);
assert.equal(normalizeReference({ ...faq, kind: undefined }), null);
assert.equal(normalizeReference({ ...faq, type: 'poem' }), null);
assert.equal(normalizeReference({ ...verse, source_url: 'https://dorar.net/placeholder' }), null, 'a verse needs a Quran host');
assert.ok(normalizeReference({ ...verse, source_url: 'https://qurancomplex.gov.sa/placeholder' }));
assert.equal(normalizeReference({ ...verse, source_site: 'dorar.net' }), null, 'a payload source_site that disagrees drops the card');

// ---------------------------------------------------------------- hadith: sahih only, the host allowlist, no book exemption
assert.equal(normalizeReference(hadith).number, '12');
assert.ok(normalizeReference({ ...hadith, source_url: 'https://shamela.ws/placeholder' }));
assert.equal(normalizeReference({ ...hadith, source_url: 'https://quranpedia.net/placeholder' }), null);
assert.equal(normalizeReference({ ...hadith, source_url: 'https://hadeethenc.com/placeholder' }), null, 'HadeethEnc is a translation source, never the hadith source');
for (const field of ['book', 'number', 'grade', 'grader', 'source_url']) {
  assert.equal(normalizeReference({ ...hadith, [field]: undefined }), null, `hadith needs ${field}`);
}
for (const source_url of [null, '', 123, '/placeholder', 'javascript:alert(1)', 'https://evil.example/placeholder', 'https://dorar.net.evil.example/placeholder']) {
  assert.equal(normalizeReference({ ...hadith, source_url }), null);
}
for (const field of ['book', 'grade', 'grader']) {
  assert.equal(normalizeReference({ ...hadith, [field]: 123 }), null);
}
for (const grade of ['حسن', 'ضعيف', 'hasan', "da'if", '[grade]', 'صحيح لغيره ', '']) {
  assert.equal(normalizeReference({ ...hadith, grade }), null, `grade ${grade} must be dropped`);
}
assert.ok(normalizeReference({ ...hadith, grade: 'sahih' }));
assert.equal(normalizeGrade('صحيح'), 'sahih');
assert.equal(normalizeGrade(' Sahih '), 'sahih');
assert.equal(normalizeGrade('hasan'), null);
assert.equal(normalizeGrade(undefined), null);

// ---------------------------------------------------------------- translation rule
const withEn = { ...verse, english_text: '[translation]', translation_name: 'Saheeh International' };
assert.equal(normalizeReference(withEn).english_text, '[translation]');
assert.equal(normalizeReference({ ...withEn, translation_name: undefined }).english_text, undefined, 'no translation_name means no English text');
assert.equal(normalizeReference({ ...withEn, translation_name: '  ' }).english_text, undefined);
assert.equal(normalizeReference({ ...withEn, translation_source_url: 'https://example.com/x' }).translation_source_url, undefined);
assert.equal(
  normalizeReference({ ...withEn, translation_source_url: 'https://hadeethenc.com/en/browse/hadith/9' }).translation_source_url,
  'https://hadeethenc.com/en/browse/hadith/9',
);
{
  const card = normalizeReference({ ...withEn, source_url: 'https://quranpedia.net/placeholder' });
  assert.equal(translationLine(card, 'en').text, 'Translation: Saheeh International via Quranpedia');
  assert.equal(translationLine(card, 'en').href, null);
  assert.equal(translationLine(card, 'ar').text, 'الترجمة: Saheeh International عبر Quranpedia');
  const he = normalizeReference({
    ...hadith, english_text: '[translation]', translation_name: 'HadeethEnc.com', translation_source_url: 'https://hadeethenc.com/en/browse/hadith/1234',
  });
  assert.deepEqual(plain(translationLine(he, 'en')), { text: 'Translation: HadeethEnc.com #1234', href: 'https://hadeethenc.com/en/browse/hadith/1234' });
  const heBad = normalizeReference({
    ...hadith, english_text: '[translation]', translation_name: 'HadeethEnc.com', translation_source_url: 'https://example.com/en/browse/hadith/1234',
  });
  assert.deepEqual(plain(translationLine(heBad, 'en')), { text: 'Translation: HadeethEnc.com', href: null }, 'an unapproved host never becomes a link');
  assert.equal(translationLine({ ...card, translation_name: '' }, 'en'), null);
}

// ---------------------------------------------------------------- headers, verse labels, credits (acceptance checks 1 and 2)
const verseCard = normalizeReference({ ...verse, audio_url: '/x.mp3', surah_name: '[اسم]' });
assert.equal(fillHeader(sourceHeader(verseCard, 'en')), 'From the Quran:');
assert.equal(fillHeader(sourceHeader(verseCard, 'ar')), 'من القرآن الكريم:');
assert.equal(surahLine(verseCard, 'en'), 'Surah 1:1');
assert.equal(surahLine(verseCard, 'ar'), 'سورة [اسم] : 1');
assert.equal(verseCaption(verseCard, 'en'), 'Text: King Fahd Complex (KFGQPC), via Quranpedia');
assert.equal(verseCaption(normalizeReference({ ...verse, source_url: 'https://qurancomplex.gov.sa/p' }), 'en'), 'Text: King Fahd Complex (KFGQPC)');
// cards-spec (05) section 1.6, organiser ruling 2026-10-05: exact wording, no "via".
assert.equal(recitationCredit(verseCard, 'en'), 'Recitation: Mahmoud Khalil Al-Husary, everyayah.com');
assert.equal(recitationCredit({ audio_credit: 'Recitation: [reciter], via mp3quran.net' }, 'en'), 'Recitation: [reciter], via mp3quran.net');
assert.equal(recitationCredit(verseCard, 'ar'), RECITATION_CREDIT.ar);
assert.equal(RECITATION_CREDIT.en, 'Recitation: Mahmoud Khalil Al-Husary, everyayah.com');
assert.equal(RECITATION_CREDIT.ar, 'التلاوة: محمود خليل الحصري، everyayah.com');
assert.equal(RECITATION_AUDIO_SOURCE_URL, 'https://everyayah.com/');
assert.equal(EXPLANATION_HEADER.en, 'In simple words, for children (our explanation, not the source\'s words):');
assert.equal(EXPLANATION_HEADER.ar, 'بكلمات بسيطة للأطفال (شرحنا، وليس نص المصدر):');
assert.equal(SOURCE_LABELS.en.explanationHeader, EXPLANATION_HEADER.en);
assert.equal(SOURCE_LABELS.ar.explanationHeader, EXPLANATION_HEADER.ar);

// ---------------------------------------------------------------- recitation credit link (section 1.6, acceptance check 1)
{
  // 1. A verse card with a payload credit and its own (safe) audio_source_url: "everyayah.com" links to that URL.
  const withLink = normalizeReference({ ...verse, audio_url: '/x.mp3', audio_credit: 'Recitation: [reciter], everyayah.com', audio_source_url: 'https://everyayah.com/data/placeholder' });
  assert.equal(withLink.audio_credit, 'Recitation: [reciter], everyayah.com');
  assert.equal(withLink.audio_source_url, 'https://everyayah.com/data/placeholder');
  assert.deepEqual(plain(recitationCreditParts(withLink, 'en')), {
    before: 'Recitation: [reciter], ', linkText: 'everyayah.com', after: '', href: 'https://everyayah.com/data/placeholder',
  });

  // 2. Empty audio_credit but the card has audio: the fallback text and the fallback link (RECITATION_AUDIO_SOURCE_URL).
  const noCredit = normalizeReference({ ...verse, audio_url: '/x.mp3' });
  assert.equal(noCredit.audio_credit, undefined);
  assert.deepEqual(plain(recitationCreditParts(noCredit, 'en')), {
    before: 'Recitation: Mahmoud Khalil Al-Husary, ', linkText: 'everyayah.com', after: '', href: RECITATION_AUDIO_SOURCE_URL,
  });
  assert.deepEqual(plain(recitationCreditParts(noCredit, 'ar')), {
    before: 'التلاوة: محمود خليل الحصري، ', linkText: 'everyayah.com', after: '', href: RECITATION_AUDIO_SOURCE_URL,
  });

  // 3. A credit whose text names no everyayah.com host at all (a different reciter site): no link, plain text.
  const otherSite = { audio_credit: 'Recitation: [reciter], mp3quran.net', audio_source_url: 'https://mp3quran.net/placeholder' };
  assert.deepEqual(plain(recitationCreditParts(otherSite, 'en')), {
    before: 'Recitation: [reciter], mp3quran.net', linkText: '', after: '', href: null,
  });

  // 4. A present but unapproved audio_source_url host is dropped at normalize time, never trusted as an href;
  //    the card still shows the credit text with the safe fallback link, not the unsafe one.
  const unsafeLink = normalizeReference({ ...verse, audio_url: '/x.mp3', audio_credit: 'Recitation: [reciter], everyayah.com', audio_source_url: 'https://evil.example/everyayah.com' });
  assert.equal(unsafeLink.audio_source_url, undefined, 'an unapproved audio_source_url host is dropped by normalizeReference');
  assert.equal(recitationCreditParts(unsafeLink, 'en').href, RECITATION_AUDIO_SOURCE_URL);

  // 5. FAQ/tafsir with no everyayah.com audio at all: audio_credit and audio_source_url both survive normalization
  //    for non-verse types too (section 2: not "verse only"), unlike audio_url which is verse-only.
  const faqWithCredit = normalizeReference({ ...faq, audio_credit: 'Recitation: [reciter], everyayah.com', audio_source_url: 'https://everyayah.com/data/placeholder', audio_url: '/should-be-dropped.mp3' });
  assert.equal(faqWithCredit.audio_credit, 'Recitation: [reciter], everyayah.com');
  assert.equal(faqWithCredit.audio_source_url, 'https://everyayah.com/data/placeholder');
  assert.equal(faqWithCredit.audio_url, undefined, 'audio_url stays verse-only even when audio_credit is kept');

  // 6. segmentsHaveAudio: true for any verse segment (its play button always has a base-URL fallback), false for
  //    text-only segments, an empty list, or a non-array.
  assert.equal(segmentsHaveAudio([{ type: 'text', value: '[a]' }]), false);
  assert.equal(segmentsHaveAudio([{ type: 'text', value: '[a]' }, { type: 'verse', surah: 2, ayah: 255, ref: '2:255' }]), true);
  assert.equal(segmentsHaveAudio([]), false);
  assert.equal(segmentsHaveAudio(undefined), false);
  assert.equal(segmentsHaveAudio('nope'), false);

  // Play-button labels (section 1.6), both languages, exact spec wording.
  assert.equal(SOURCE_LABELS.en.audio.listen, 'Listen to the recitation');
  assert.equal(SOURCE_LABELS.en.audio.playing, 'Playing recitation');
  assert.equal(SOURCE_LABELS.en.audio.loading, 'Loading...');
  assert.equal(SOURCE_LABELS.en.audio.unavailable, 'Recitation unavailable');
  assert.equal(SOURCE_LABELS.ar.audio.listen, 'استمع إلى التلاوة');
  assert.equal(SOURCE_LABELS.ar.audio.playing, 'جارٍ تشغيل التلاوة');
  assert.equal(SOURCE_LABELS.ar.audio.loading, 'جارٍ التحميل...');
  assert.equal(SOURCE_LABELS.ar.audio.unavailable, 'التلاوة غير متاحة');
}

// ---------------------------------------------------------------- two tiers: the explanation never replaces or merges with the source
{
  const card = normalizeReference({
    ...hadith, explanation: '[explanation]', explanation_lang: 'en', explanation_origin: 'human',
  });
  assert.equal(card.arabic_text, '[bank text]');
  assert.equal(card.explanation, '[explanation]');
  assert.equal(card.explanation_origin, undefined, 'the label is always the same: the payload origin is never read');
  assert.equal(card.explanation_lang, 'en');
  assert.equal(normalizeReference({ ...hadith, explanation_lang: 'fr' }).explanation_lang, undefined);
}

// ---------------------------------------------------------------- hadith citation line (acceptance check 3)
{
  const card = normalizeReference(hadith);
  assert.equal(
    hadithCitationPieces(card, 'en').join(CITATION_SEPARATOR),
    'Sahih al-Bukhari 12 · graded sahih (al-Bukhari) · source: الدرر السنية',
  );
  assert.equal(
    hadithCitationPieces(card, 'ar').join(CITATION_SEPARATOR),
    'صحيح البخاري 12 · الحكم: صحيح (البخاري) · المصدر: الدرر السنية',
  );
  assert.equal(fillHeader(sourceHeader(card, 'en')), 'From Sahih al-Bukhari:');
  assert.equal(fillHeader(sourceHeader(card, 'ar')), 'من صحيح البخاري:');
  const muslim = normalizeReference({ ...hadith, book: 'صحيح مسلم', grader: 'Muslim', source_url: 'https://shamela.ws/placeholder' });
  assert.equal(
    hadithCitationPieces(muslim, 'en').join(CITATION_SEPARATOR),
    'Sahih Muslim 12 · graded sahih (Muslim) · source: المكتبة الشاملة',
  );
  assert.equal(hadithCitationPieces({ ...card, grade: 'hasan' }, 'en'), null, 'a non-sahih grade never yields a citation');
  assert.equal(hadithCitationPieces({ ...card, grade: undefined }, 'en'), null);
  // a book the label table does not know is shown as stored, nothing is invented
  const other = normalizeReference({ ...hadith, book: '[some book]', grader: '[grader]' });
  assert.equal(hadithCitationPieces(other, 'en')[0], '[some book] 12');
  assert.equal(hadithCitationPieces(other, 'en')[1], 'graded sahih ([grader])');
  // cards-spec (05) review: only the exact names are translated; a book that merely contains one is never relabelled
  for (const book of ['Hisn al-Muslim', 'al-Adab al-Mufrad (al-Bukhari)', 'شرح صحيح مسلم', 'Sahih Muslim, commentary']) {
    assert.equal(api.bookName(book, 'en'), book, `${book} must be shown as stored`);
    assert.equal(fillHeader(sourceHeader({ type: 'tafsir', source_site: 'shamela.ws', book }, 'en')), `${book} says:`);
  }
  assert.equal(api.bookName(' sahih  AL-BUKHARI ', 'ar'), 'صحيح البخاري');
  assert.equal(api.bookName('صحيح مسلم', 'en'), 'Sahih Muslim');
  assert.equal(api.graderName('الإمام البخاري', 'en'), 'al-Bukhari');
  assert.equal(api.graderName('[grader]', 'en'), '[grader]');
}

// ---------------------------------------------------------------- tafsir, FAQ, term, aqidah, fiqh, sirah (acceptance check 5)
{
  const tafsirDorar = normalizeReference({
    id: 't1', type: 'tafsir', kind: 'source_excerpt', arabic_text: '[excerpt]', book: '[book]', number: '1:1-2', source_url: 'https://dorar.net/p',
  });
  assert.equal(fillHeader(sourceHeader(tafsirDorar, 'en')), 'Tafsir encyclopedia (al-Durar al-Saniyya) says:');
  assert.deepEqual(plain(tafsirCitationPieces(tafsirDorar)), ['[book]', '1:1-2']);
  const tafsirShamela = normalizeReference({
    id: 't2', type: 'tafsir', kind: 'source_excerpt', arabic_text: '[excerpt]', book: '[book]', source_url: 'https://shamela.ws/p',
  });
  assert.equal(fillHeader(sourceHeader(tafsirShamela, 'en')), '[book] says:');
  assert.equal(normalizeReference({ ...tafsirShamela, book: undefined }), null, 'a Shamela tafsir without a book has no header');
  assert.equal(normalizeReference({ ...tafsirShamela, kind: 'scripture' }), null);
  assert.equal(fillHeader(sourceHeader(normalizeReference(faq), 'en')), 'From Bayyinat (Questions and Answers about Islam):');
  assert.equal(fillHeader(sourceHeader(normalizeReference({ ...faq, id: 'x', type: 'term', source_url: 'https://islamic-content.com/p' }), 'en')), 'From the Al-Jamhara dictionary:');
  for (const [type, header] of [['aqidah', 'From the Creed encyclopedia (al-Durar al-Saniyya):'], ['fiqh', 'From the Fiqh encyclopedia (al-Durar al-Saniyya):'], ['sirah', 'From the History encyclopedia (al-Durar al-Saniyya):']]) {
    const card = normalizeReference({ ...faq, id: type, type, source_url: 'https://dorar.net/p' });
    assert.equal(fillHeader(sourceHeader(card, 'en')), header);
    assert.equal(normalizeReference({ ...faq, id: type, type, source_url: 'https://dawa.center/p' }), null, `${type} must come from dorar.net`);
  }
  // level C needs the disagreement note
  const levelC = { ...faq, id: 'c', type: 'aqidah', source_url: 'https://dorar.net/p', content_level: 'C' };
  assert.equal(normalizeReference(levelC), null);
  assert.equal(normalizeReference({ ...levelC, disagreement_note: '[note]' }).disagreement_note, '[note]');
  assert.equal(normalizeReference({ ...levelC, content_level: 'B', disagreement_note: '[note]' }).disagreement_note, undefined);
}

// ---------------------------------------------------------------- verse markers (acceptance check 4) and the display mapping
{
  const text = '[a] {{verse:2:255}} [b] {{ verse : 1 : 7 }} [c]';
  const parts = splitVerseMarkers(text);
  assert.deepEqual(plain(parts).map((p) => p.type), ['text', 'verse', 'text', 'verse', 'text']);
  assert.ok(parts.every((p) => p.type === 'verse' || !p.value.includes('{{')), 'the raw marker never reaches the screen');
  // SourceCard.jsx falls back to splitVerseMarkers() when a card has no server-resolved `segments` (an
  // unresolved marker still in arabic_text): that fallback must still count as having audio (section 1.6).
  assert.equal(segmentsHaveAudio(parts), true, 'a client-split marker still counts as a play button needing the credit');
  assert.deepEqual(plain(verseMarkerRefs(`${text} {{verse:2:255}}`)).map((r) => r.ref), ['2:255', '1:7']);
  assert.equal(hasBrokenMarker(text), false);
  for (const bad of ['{{verse:2:}}', '{{verse:x:1}}', '[a] {{verse:2:255', 'a }} b', '{{ayah:2:255}}']) {
    assert.equal(hasBrokenMarker(bad), true, `${bad} is a broken marker`);
  }
  const ok = normalizeReference({ ...faq, arabic_text: text });
  assert.deepEqual(plain(ok.marker_refs), ['2:255', '1:7']);
  assert.equal(normalizeReference({ ...faq, arabic_text: '[a] {{verse:2:9999}} [b]' }), null);
  assert.equal(normalizeReference({ ...faq, arabic_text: '[a] {{verse:115:1}} [b]' }), null);
  assert.equal(normalizeReference({ ...faq, arabic_text: '[a] {{verse:2:255 [b]' }), null);
  assert.equal(verseRefLabel(2, 255, 'en'), `Surah ${SURAH_EN[1]} 2:255`);
  assert.equal(verseRefLabel(2, 255, 'ar'), `سورة ${SURAH_AR[1]} 2:255`);
  assert.equal(quranAudioUrl('https://audio.test/quran/', 2, 255), 'https://audio.test/quran/002255.mp3');
  assert.equal(surahName(1, 'en'), 'Al-Fatihah');
  assert.equal(SURAH_EN.length, 114);
  assert.equal(SURAH_AR.length, 114);

  // toDisplayArabic: only the three legacy marks are mapped, only for the fallback font, and the input never changes
  const legacy = ['ٗ', 'ٞ', 'ٖ'];
  const mapped = ['ࣰ', 'ࣱ', 'ࣲ'];
  const sample = `[a${legacy[0]}b${legacy[1]}c${legacy[2]}d]`;
  assert.equal(toDisplayArabic(sample, false), sample, 'with the KFGQPC font the text is shown as stored');
  assert.equal(toDisplayArabic(sample, true), `[a${mapped[0]}b${mapped[1]}c${mapped[2]}d]`);
  assert.equal(toDisplayArabic('[plain text]', true), '[plain text]');
  assert.equal(toDisplayArabic(undefined, true), '');
}

// ---------------------------------------------------------------- labels: both languages complete, none mixed
{
  const walk = (a, b, path) => {
    assert.deepEqual(Object.keys(a).sort(), Object.keys(b).sort(), `label keys differ at ${path}`);
    for (const k of Object.keys(a)) {
      if (typeof a[k] === 'object') walk(a[k], b[k], `${path}.${k}`);
      else assert.ok(a[k] && b[k], `empty label ${path}.${k}`);
    }
  };
  walk(SOURCE_LABELS.en, SOURCE_LABELS.ar, 'SOURCE_LABELS');
  assert.equal(openSourceLabel(verseCard, 'en'), 'View on Quranpedia (quranpedia.net)');
  assert.equal(openSourceLabel(normalizeReference(hadith), 'ar'), 'عرض في الدرر السنية (dorar.net)');
}

// ---------------------------------------------------------------- hadith card: both links (organiser ruling 2026-10-05, item 4)
// dorar.net (source_url) is the cited Arabic source; HadeethEnc (translation_source_url) carries the English and is
// labelled as the translation, never as the source.
{
  const both = normalizeReference({
    ...hadith, english_text: '[translation]', translation_name: 'HadeethEnc.com', translation_source_url: 'https://hadeethenc.com/en/browse/hadith/1234',
  });
  assert.equal(both.source_url, 'https://dorar.net/placeholder');
  assert.equal(both.translation_source_url, 'https://hadeethenc.com/en/browse/hadith/1234');
  for (const lang of ['en', 'ar']) {
    const src = openSourceLabel(both, lang);
    const tr = translationLine(both, lang);
    assert.ok(src.includes('dorar.net') && !/hadeethenc/i.test(src), `${lang}: the open-source link names dorar.net, not HadeethEnc`);
    assert.equal(tr.href, 'https://hadeethenc.com/en/browse/hadith/1234', `${lang}: the translation line links HadeethEnc`);
    assert.ok(tr.text.startsWith(lang === 'ar' ? 'الترجمة:' : 'Translation:'), `${lang}: HadeethEnc is labelled as the translation`);
    const cite = hadithCitationPieces(both, lang).join(CITATION_SEPARATOR);
    assert.ok(!/hadeethenc/i.test(cite), `${lang}: HadeethEnc is never the cited source`);
  }
  assert.equal(safeSourceUrl(both.translation_source_url), null, 'HadeethEnc can never be the source link');
  // SourceCard.jsx: the non-verse branch (hadith) renders the English block (translation line) right after its
  // citation line, and the footer that every card renders holds the dorar source link.
  const cardSrc = readSource('SourceCard.jsx');
  assert.match(cardSrc, /<Pieces pieces=\{citation\} \/>[\s\S]*?<\/p>\s*\) : null\}\s*<EnglishBlock card=\{card\} lang=\{language\} dir=\{dir\} \/>/, 'hadith: the translation line renders in the non-verse branch');
  assert.match(cardSrc, /function Footer\([^)]*\) \{[\s\S]*?<OpenSource card=\{card\} lang=\{lang\} \/>[\s\S]*?\n\}/, 'hadith: the footer renders the source link');
  assert.match(cardSrc, /<Footer card=\{card\} lang=\{language\} \/>/, 'every card renders the footer');
}

// ---------------------------------------------------------------- the real decoder path: bytes -> parseData -> normalizeReference
{
  const bytes = (obj) => new TextEncoder().encode(JSON.stringify(obj));
  const decode = (kind) => normalizeReference(parseData(bytes(buildMockReference(kind))));
  const mustRender = MOCK_KINDS.filter((k) => !k.startsWith('bad-'));
  const mustDrop = MOCK_KINDS.filter((k) => k.startsWith('bad-'));
  assert.deepEqual(plain(mustDrop), ['bad-grade', 'bad-host', 'bad-marker', 'bad-segment']);
  for (const kind of mustRender) {
    const card = decode(kind);
    assert.ok(card, `mock kind ${kind} must decode to a card`);
    assert.ok(sourceHeader(card, 'en') && sourceHeader(card, 'ar'), `${kind} has a header in both languages`);
  }
  for (const kind of mustDrop) assert.equal(decode(kind), null, `mock kind ${kind} must be dropped`);
  const explained = decode('verse-explained');
  assert.equal(explained.explanation_lang, 'ar');
  assert.equal(explained.explanation_origin, undefined);
  assert.equal(decode('hadith-hadeeth').translation_source_url, 'https://hadeethenc.com/en/browse/hadith/1234');
  assert.equal(decode('hadith').translation_source_url, undefined, 'the placeholder example.com link is dropped');
  assert.ok(decode('faq-marker').marker_refs.includes('2:255'));
  // hk/01: the server resolves the markers into `segments`; the card renders those and no raw marker survives.
  const resolved = decode('faq-segments');
  assert.deepEqual(plain(resolved.segments).map((s) => s.type), ['text', 'verse', 'text']);
  assert.deepEqual(plain(resolved.marker_refs), ['2:255']);
  assert.equal(resolved.segments[1].audio_url, 'https://audio.example.test/quran/002255.mp3');
  assert.ok(!/\{\{|\}\}/.test(JSON.stringify(resolved)), 'no raw marker in a resolved card');
  // section 1.6: a FAQ card survives normalization with its own audio_credit/audio_source_url, and
  // segmentsHaveAudio sees its verse segment, so the card shows the credit once (SourceCard.jsx).
  assert.equal(resolved.audio_credit, 'Recitation: [reciter], everyayah.com');
  assert.equal(resolved.audio_source_url, 'https://everyayah.com/data/placeholder');
  assert.equal(segmentsHaveAudio(resolved.segments), true);
  assert.deepEqual(plain(recitationCreditParts(resolved, 'en')), {
    before: 'Recitation: [reciter], ', linkText: 'everyayah.com', after: '', href: 'https://everyayah.com/data/placeholder',
  });
  const base = buildMockReference('faq-segments');
  assert.equal(normalizeReference({ ...base, segments: [{ type: 'text', text: 'a {{verse:2:255}} b' }] }), null, 'a brace in a text segment drops the card');
  assert.equal(normalizeReference({ ...base, segments: [{ type: 'verse', surah: 115, ayah: 1 }] }), null, 'an impossible verse drops the card');
  assert.equal(normalizeReference({ ...base, segments: [{ type: 'script', text: 'x' }] }), null, 'an unknown segment type drops the card');
  assert.equal(normalizeReference({ ...base, segments: 'nope' }), null);
  assert.equal(normalizeReference({ ...base, segments: [] }).segments, undefined, 'no segments: the plain text is shown');
  assert.equal(normalizeReference({ ...base, segments: [{ type: 'verse', surah: 2, ayah: 255, audio_url: 'javascript:alert(1)' }] }).segments[0].audio_url, undefined, 'a non-http audio url is not kept');
  // garbage on the wire is dropped, never thrown
  for (const raw of ['not json', '[]', 'null', '42', '"text"', '']) {
    assert.equal(normalizeReference(parseData(new TextEncoder().encode(raw))), null, `wire value ${raw}`);
  }
  assert.equal(parseData(new Uint8Array([0xff, 0xfe])), null);
  // a node on a real session sends the card id as a number sometimes
  assert.equal(normalizeReference(parseData(bytes({ ...hadith, id: 77 }))).id, '77');
}

// ---------------------------------------------------------------- AI strings and registration strings
{
  const ai = runInNewContext(`${withoutImports(readSrc('features/child/ai/aiStrings.js'))}
    ({ AI_STRINGS, SHOW_PARENT_SUMMARY_LINE, REGISTRATION_STRINGS, PRIVACY_LINK });`);
  assert.deepEqual(Object.keys(ai.AI_STRINGS.en), Object.keys(ai.AI_STRINGS.ar));
  assert.equal(ai.AI_STRINGS.en.chipText, 'AI');
  assert.equal(ai.AI_STRINGS.ar.chipText, 'AI');
  assert.equal(ai.AI_STRINGS.en.title, 'Al-Sadiq is an AI');
  assert.equal(ai.AI_STRINGS.ar.title, 'الصديق ذكاء اصطناعي');
  // Lead decision 5 Oct: the AI line says "AI friend" / «ذكاء اصطناعي» and never "computer" / «كمبيوتر».
  assert.equal(ai.AI_STRINGS.en.line1, 'I am Al-Sadiq, an AI friend. I am not a real person.');
  assert.equal(ai.AI_STRINGS.ar.line1, 'أنا الصديق، ذكاء اصطناعي ولست إنسانًا.');
  for (const lang of ['en', 'ar']) {
    assert.ok(!/computer|كمبيوتر|صادق(?![ء-ي])/.test(JSON.stringify(ai.AI_STRINGS[lang])), `old wording in AI_STRINGS.${lang}`);
  }
  assert.equal(ai.AI_STRINGS.en.line2, 'I can make mistakes. I am not a scholar and I do not give fatwas.');
  // cards-spec (05) judge r2: line 5 ("your parents see short summaries") is on, so the parent API must not send raw text.
  if (ai.SHOW_PARENT_SUMMARY_LINE) {
    const ser = readFileSync(new URL('../../backend/conversation/serializers.py', import.meta.url), 'utf8');
    assert.match(ser, /def get_preview\(self, obj\):(?:\s*#[^\n]*)*\s*return ''/,
      'AI sheet line 5 is on, so ParentSessionSummarySerializer.get_preview must return an empty string');
  }
  assert.ok(ai.REGISTRATION_STRINGS.en.terms11.startsWith('11. '));
  assert.ok(ai.REGISTRATION_STRINGS.ar.terms11.startsWith('11. '));
}

// ---------------------------------------------------------------- privacy content: both languages, the same shape, no leftover brackets
{
  const { PRIVACY_CONTENT } = runInNewContext(`${withoutImports(readSrc('features/privacy/privacyContent.js'))}
    ({ PRIVACY_CONTENT });`);
  const { en, ar } = PRIVACY_CONTENT;
  assert.equal(en.dir, 'ltr');
  assert.equal(ar.dir, 'rtl');
  assert.equal(en.sections.length, ar.sections.length, 'same number of sections in both languages');
  en.sections.forEach((section, i) => {
    assert.deepEqual(section.blocks.map((b) => b.t), ar.sections[i].blocks.map((b) => b.t), `section ${i} block types`);
  });
  const strings = [];
  const collect = (v) => { if (typeof v === 'string') strings.push(v); else if (v && typeof v === 'object') Object.values(v).forEach(collect); };
  collect(PRIVACY_CONTENT);
  const dump = strings.join(' ');
  assert.ok(strings.length > 50);
  assert.ok(!/[[\]]/.test(dump), 'the privacy page must hold no [bracketed] placeholder');
  assert.ok(!/\bxAI\b|gpt-?4/i.test(dump), 'only the approved processors are named');
  assert.ok(/ElevenLabs/.test(dump));
  assert.ok(en.draft && ar.draft, 'the draft banner stays until legal review');
}

// ---------------------------------------------------------------- no Quran annotation marks (U+06D6-06ED) anywhere in src
{
  const walkDir = (dir, files = []) => {
    for (const name of readdirSync(dir)) {
      const p = join(dir, name);
      if (statSync(p).isDirectory()) walkDir(p, files);
      else if (/\.(js|jsx|css|json|md|html)$/.test(name)) files.push(p);
    }
    return files;
  };
  const bad = walkDir(new URL('../src', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'))
    .filter((p) => /[ۖ-ۭ]/.test(readFileSync(p, 'utf8')));
  assert.deepEqual(bad, [], 'no Quran annotation marks in source files');
}

// ---------------------------------------------------------------- SourceCard.jsx: RecitationButton behaviour (StrictMode cleanup), markup guards
const cardSource = readSource('SourceCard.jsx');
const start = cardSource.indexOf('let playingAudio = null;');
const end = cardSource.indexOf('\n  return (', start);
assert.ok(start >= 0 && end > start);
let setup;
let pauses = 0;
let plays = 0;
const audio = {
  src: 'https://audio.example/clip.mp3',
  pause() { pauses += 1; },
  play() { plays += 1; return Promise.resolve(); },
  removeAttribute(name) { delete this[name]; },
  load() { throw new Error('Cleanup must retain the React-managed src'); },
};
const { toggle } = runInNewContext(`${cardSource.slice(start, end)}
  return { toggle };
}
RecitationButton({ src: audio.src, labels: { play: 'Play recitation', pause: 'Pause recitation' }, card: null, lang: 'en' });`, {
  audio,
  useRef: () => ({ current: audio }),
  useState: () => ['idle', () => {}],
  useEffect: (effect) => { setup = effect; },
});
// StrictMode replays setup -> cleanup -> setup while keeping the DOM node.
setup()();
assert.equal(audio.src, 'https://audio.example/clip.mp3');
const cleanup = setup();
toggle();
assert.equal(plays, 1);
cleanup();
assert.equal(pauses, 2);
assert.equal(audio.src, 'https://audio.example/clip.mp3');
assert.match(cardSource, /<audio\b[^>]*\bsrc=\{src\}/);
assert.match(cardSource, /data-testid="recitation-credit"/, 'a recitation always shows its credit line');
// Section 1.6: a per-segment play button never carries its own credit line; the card shows it once instead.
const verseMarkerSrc = cardSource.slice(cardSource.indexOf('function VerseMarker'), cardSource.indexOf('/** The verbatim Arabic'));
assert.match(verseMarkerSrc, /<RecitationButton src=\{src\} labels=\{labels\} showCredit=\{false\} \/>/, 'a segment play button suppresses its own credit');
assert.match(cardSource, /\{segmentAudio \? <RecitationCreditLine card=\{card\} lang=\{language\} \/> : null\}/, 'a non-verse card with segment audio shows the credit once, outside the segments loop');
assert.match(cardSource, /audioSrc \? \(\s*<RecitationButton src=\{audioSrc\} labels=\{L\.audio\} card=\{card\} lang=\{language\} \/>/, 'the verse play button always carries its own credit');
assert.match(cardSource, /data-testid="explanation-header"/);
assert.ok(cardSource.indexOf('<ExplanationBlock') > cardSource.indexOf('source-block'), 'the explanation block comes after the source block');
// Scoped to OpenSource (not RecitationCreditLine's inline "everyayah.com" word, which is not a tap target of its own).
const openSourceSrc = cardSource.slice(cardSource.indexOf('function OpenSource'), cardSource.indexOf('/** "From {book}:" '));
const sourceLink = openSourceSrc.match(/<a\s[^>]*className="([^"]*)"/);
assert.ok(sourceLink?.[1].split(/\s+/).includes('min-h-target'), 'Source link needs the child touch-target token');
assert.match(readFileSync(new URL('../src/index.css', import.meta.url), 'utf8'), /--spacing-target:\s*56px;/);
const css = readSource('sourceCards.css');
assert.match(css, /\.quran-text[^}]*font-size:\s*max\(\s*(2[89]|[3-9]\d)px/s, 'Quran text is 28px or larger');
assert.match(css, /KFGQPC Hafs[\s\S]*Amiri Quran/);

console.log('Source-card checks passed (URL safety, citation bounds, sahih-only, labels and credits, two tiers, markers, decoder path, AI strings, privacy content).');
