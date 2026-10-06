/**
 * DEV-only placeholder `reference` payloads (task 03 has not landed).
 * Every text field is an obvious fake: NEVER put real Quran or hadith text here. A {{verse:S:A}} marker is
 * just a pointer (numbers), not text. The shapes follow cards-spec (05) section 2.
 *
 * Note: window.__mockReference only shows cards in the connected state, because
 * starting a session clears the cards.
 *
 * kinds: verse, verse-explained, hadith, hadith-hadeeth, tafsir, tafsir-book, faq, faq-marker, term, aqidah,
 * fiqh, sirah, level-c, plus three payloads that must be DROPPED: bad-grade, bad-host, bad-marker.
 */
let counter = 0;

const AR_EXPLANATION = '[شرح مبسط تجريبي]';
const EN_EXPLANATION = '[A placeholder explanation in simple words]';

export const MOCK_KINDS = [
  'verse', 'verse-explained', 'hadith', 'hadith-hadeeth', 'tafsir', 'tafsir-book', 'faq', 'faq-marker', 'faq-segments', 'term',
  'aqidah', 'fiqh', 'sirah', 'level-c', 'bad-grade', 'bad-host', 'bad-marker', 'bad-segment',
];

export function buildMockReference(kind = 'verse') {
  counter += 1;
  const id = `mock-${kind}-${counter}`;
  const dorar = 'https://dorar.net/placeholder';
  switch (kind) {
    case 'verse':
    case 'verse-explained':
      return {
        id,
        type: 'verse',
        kind: 'scripture',
        arabic_text: '[نص الآية من بنك المحتوى]',
        english_text: '[Verse translation from the content bank]',
        translation_name: 'Saheeh International',
        surah: 1,
        surah_name: '[اسم السورة]',
        ayah: 1,
        audio_url: '/placeholder-recitation.mp3',
        source_site: 'quranpedia.net',
        source_url: 'https://quranpedia.net/placeholder',
        value: 'Kindness',
        verification_status: 'reviewed',
        ...(kind === 'verse-explained'
          ? { explanation: AR_EXPLANATION, explanation_lang: 'ar', explanation_origin: 'generated' }
          : {}),
      };
    case 'hadith':
    case 'hadith-hadeeth':
      return {
        id,
        type: 'hadith',
        kind: 'scripture',
        arabic_text: '[نص الحديث من بنك المحتوى]',
        english_text: '[Hadith translation from the content bank]',
        translation_name: 'HadeethEnc.com',
        translation_source_url: kind === 'hadith-hadeeth'
          ? 'https://hadeethenc.com/en/browse/hadith/1234'
          : 'https://example.com/placeholder',
        book: counter % 2 ? 'Sahih al-Bukhari' : 'Sahih Muslim',
        number: '000',
        grade: 'صحيح',
        grader: counter % 2 ? 'البخاري' : 'مسلم',
        source_site: 'dorar.net',
        source_url: dorar,
        value: 'Honesty',
        content_level: 'A',
        verification_status: 'reviewed',
        explanation: EN_EXPLANATION,
        explanation_lang: 'en',
      };
    case 'tafsir':
    case 'tafsir-book':
      return {
        id,
        type: 'tafsir',
        kind: 'source_excerpt',
        arabic_text: '[مقتطف تفسير تجريبي]',
        book: '[اسم الكتاب]',
        number: '1:1-2',
        source_site: kind === 'tafsir' ? 'dorar.net' : 'shamela.ws',
        source_url: kind === 'tafsir' ? dorar : 'https://shamela.ws/placeholder',
        value: 'Kindness',
      };
    case 'faq':
      return {
        id,
        type: 'faq',
        kind: 'source_excerpt',
        title: '[سؤال تجريبي]',
        arabic_text: '[نص الجواب التجريبي]',
        source_site: 'dawa.center',
        source_url: 'https://dawa.center/placeholder',
        value: 'Honesty',
        explanation: AR_EXPLANATION,
        explanation_lang: 'ar',
      };
    case 'faq-marker':
      return {
        id,
        type: 'faq',
        kind: 'source_excerpt',
        title: '[سؤال تجريبي]',
        arabic_text: '[بداية الجواب] {{verse:2:255}} [تتمة الجواب]',
        verse_refs: ['2:255'],
        source_site: 'dawa.center',
        source_url: 'https://dawa.center/placeholder',
      };
    case 'faq-segments':
      // The shape hk/01 sends: markers already resolved. arabic_text is the plain fallback (reference in place of the
      // marker), `segments` is the ordered rendering with the bank verse's recitation. cards-spec (05) section 1.6
      // (organiser ruling 2026-10-05): a non-verse card whose segments carry everyayah.com audio still gets the
      // card-level audio_credit/audio_source_url, shown once by the UI, not once per segment.
      return {
        id,
        type: 'faq',
        kind: 'source_excerpt',
        title: '[سؤال تجريبي]',
        arabic_text: '[بداية الجواب] (البقرة 2:255) [تتمة الجواب]',
        verse_refs: ['2:255'],
        segments: [
          { type: 'text', text: '[بداية الجواب] ' },
          { type: 'verse', surah: 2, ayah: 255, ref: '2:255', item_key: 'verse:2:255', id: 1, surah_name: 'البقرة', audio_url: 'https://audio.example.test/quran/002255.mp3' },
          { type: 'text', text: ' [تتمة الجواب]' },
        ],
        audio_credit: 'Recitation: [reciter], everyayah.com',
        audio_source_url: 'https://everyayah.com/data/placeholder',
        source_site: 'dawa.center',
        source_url: 'https://dawa.center/placeholder',
      };
    case 'term':
      return {
        id,
        type: 'term',
        kind: 'source_excerpt',
        title: '[مصطلح تجريبي]',
        arabic_text: '[تعريف المصطلح التجريبي]',
        english_text: '[Placeholder term definition]',
        translation_name: 'Al-Jamhara (en)',
        source_site: 'islamic-content.com',
        source_url: 'https://islamic-content.com/placeholder',
      };
    case 'aqidah':
    case 'fiqh':
    case 'sirah':
      return {
        id,
        type: kind,
        kind: 'source_excerpt',
        title: `[عنوان ${kind} تجريبي]`,
        arabic_text: `[مقتطف ${kind} تجريبي]`,
        source_site: 'dorar.net',
        source_url: dorar,
        content_level: 'B',
        explanation: EN_EXPLANATION,
        explanation_lang: 'en',
      };
    case 'level-c':
      return {
        id,
        type: 'aqidah',
        kind: 'source_excerpt',
        title: '[موضوع خلافي تجريبي]',
        arabic_text: '[مقتطف تجريبي]',
        source_site: 'dorar.net',
        source_url: dorar,
        content_level: 'C',
        disagreement_note: '[A placeholder note: scholars hold different views]',
      };
    // The three below must be dropped by normalizeReference.
    case 'bad-grade':
      return { ...buildMockReference('hadith'), id, grade: 'حسن' };
    case 'bad-host':
      return { ...buildMockReference('hadith'), id, source_url: 'https://hadeethenc.com/placeholder' };
    case 'bad-marker':
      return { ...buildMockReference('faq'), id, arabic_text: '[نص] {{verse:2:9999}} [نص]' };
    case 'bad-segment':
      return { ...buildMockReference('faq-segments'), id, segments: [{ type: 'verse', surah: 2, ayah: 9999, audio_url: '' }] };
    default:
      return buildMockReference('verse');
  }
}
