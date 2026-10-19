// cards-spec (05): rewritten from the verse/hadith-only card. Labels, credits and the two tiers follow
// docs/hackathon/handoffs/05-cards-ai-privacy.md; every label string comes from sourceLabels.js.
import { useEffect, useRef, useState } from 'react';
import { BookOpen, ExternalLink, Library, Loader2, Pause, Play, ScrollText, ShieldCheck, Sparkles } from 'lucide-react';
import { Card, IconButton, Pill } from '../../../components/ui';
import { safeAudioUrl, safeSourceUrl } from './safeUrl';
import { splitVerseMarkers, toDisplayArabic, quranAudioUrl } from './quranText';
import {
  CITATION_SEPARATOR, EXPLANATION_HEADER, SOURCE_LABELS, hadithCitationPieces, openSourceLabel,
  recitationCreditParts, segmentsHaveAudio, sourceHeader, surahLine, tafsirCitationPieces, translationLine,
  verseCaption, verseRefLabel,
} from './sourceLabels';
import useQuranFontFallback from './useQuranFontFallback';
import './sourceCards.css';

const pageLang = (lang) => (lang === 'ar' ? 'ar' : 'en');

// Base of the bank's recitation files for {{verse:S:A}} markers: <base>/SSSAAA.mp3 (the knowledge bank serves static/quran/).
const QURAN_AUDIO_BASE = import.meta.env.VITE_QURAN_AUDIO_BASE
  || `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/static/quran`;

/**
 * The recitation credit line (section 1.6): the payload `audio_credit` or the `RECITATION_CREDIT` fallback, with
 * "everyayah.com" rendered as a link to `audio_source_url` (or the fallback URL) when that link is safe, plain
 * text otherwise. Shared by the verse's own play button and, once per card, by a card whose verse `segments`
 * carry audio (FAQ, tafsir) — never per segment.
 */
function RecitationCreditLine({ card, lang }) {
  const { before, linkText, after, href } = recitationCreditParts(card, lang);
  return (
    <p data-testid="recitation-credit" className="text-caption text-text-muted">
      {before}
      {linkText ? (
        href ? (
          <a href={href} target="_blank" rel="noopener noreferrer" className="text-primary-strong underline">
            {linkText}
          </a>
        ) : linkText
      ) : null}
      {after}
    </p>
  );
}

/**
 * Plays the recitation clip for a verse. Verses are recitation audio only,
 * never TTS. States: idle, loading (buffering), playing, error.
 * The credit line always sits directly under the button: a recitation never plays without its credit. For a
 * segment's play button (`showCredit={false}`) the credit is rendered once elsewhere in the same card instead.
 */
// Only one recitation plays at a time.
let playingAudio = null;

function RecitationButton({ src, labels, card, lang, showCredit = true }) {
  const audioRef = useRef(null);
  const [state, setState] = useState('idle');

  useEffect(() => {
    const el = audioRef.current;
    return () => {
      if (!el) return;
      el.pause();
      if (playingAudio === el) playingAudio = null;
    };
  }, []);

  const toggle = () => {
    const el = audioRef.current;
    if (!el) return;
    if (state === 'playing' || state === 'loading') {
      el.pause();
      return;
    }
    if (playingAudio && playingAudio !== el) playingAudio.pause();
    playingAudio = el;
    setState('loading');
    el.play().catch(() => setState('error'));
  };

  const label = state === 'playing' ? labels.pause : labels.play;

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-3">
        <IconButton
          label={label}
          variant="primary"
          onClick={toggle}
          aria-busy={state === 'loading' || undefined}
          icon={
            state === 'loading' ? (
              <Loader2 aria-hidden="true" className="size-6 motion-safe:animate-spin" />
            ) : state === 'playing' ? (
              <Pause aria-hidden="true" className="size-6" />
            ) : (
              <Play aria-hidden="true" className="size-6" />
            )
          }
        />
        <span className="text-label text-text-muted">
          {state === 'error'
            ? labels.unavailable
            : state === 'playing'
              ? labels.playing
              : state === 'loading'
                ? labels.loading
                : labels.listen}
        </span>
        <audio
          ref={audioRef}
          src={src}
          preload="none"
          onWaiting={() => setState('loading')}
          onPlaying={() => setState('playing')}
          onPause={() => setState('idle')}
          onEnded={() => setState('idle')}
          onError={() => setState('error')}
        />
      </div>
      {showCredit ? <RecitationCreditLine card={card} lang={lang} /> : null}
    </div>
  );
}

function OpenSource({ card, lang }) {
  const href = safeSourceUrl(card.source_url);
  if (!href) return null;
  const L = SOURCE_LABELS[pageLang(lang)];
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="text-label inline-flex min-h-target items-center gap-1 self-start text-primary-strong underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-strong"
    >
      <bdi>{openSourceLabel(card, lang)}</bdi>
      <span className="sr-only">{L.newTab}</span>
      <ExternalLink aria-hidden="true" className="size-4" />
    </a>
  );
}

/** "From {book}:" with the book in its own <bdi>, or a plain header. */
function Header({ card, lang }) {
  const header = sourceHeader(card, lang);
  if (!header) return null;
  const parts = header.template.split('{book}');
  return (
    <p data-testid="source-header" className="text-label font-semibold text-text-muted">
      {parts.length === 2 ? (
        <>
          {parts[0]}
          <bdi>{header.book}</bdi>
          {parts[1]}
        </>
      ) : (
        header.template
      )}
    </p>
  );
}

function Pieces({ pieces }) {
  return pieces.map((p, i) => (
    <span key={i}>
      {i > 0 ? CITATION_SEPARATOR : null}
      <bdi>{p}</bdi>
    </span>
  ));
}

/**
 * One recited verse that a text points at with a {{verse:S:A}} marker: the reference and a play button, never the
 * raw marker. Its credit is not rendered here — section 1.6 shows the credit once per card, not once per segment —
 * the card renders a single RecitationCreditLine instead when any segment has audio (see segmentsHaveAudio).
 */
function VerseMarker({ seg, lang, labels }) {
  // The recitation file the bank names for this verse (segments from the server) or the base + SSSAAA.mp3 fallback.
  const src = safeAudioUrl(seg.audio_url) || safeAudioUrl(quranAudioUrl(QURAN_AUDIO_BASE, seg.surah, seg.ayah));
  // cards-spec (05) review: lang too, because the marker sits inside the lang="ar" source text and its label may be English.
  return (
    <span data-testid="verse-marker" className="my-1 block" dir={lang === 'ar' ? 'rtl' : 'ltr'} lang={lang}>
      <span className="verse-ref-chip">
        <BookOpen aria-hidden="true" className="size-4" />
        <bdi>{verseRefLabel(seg.surah, seg.ayah, lang)}</bdi>
      </span>
      {src ? <RecitationButton src={src} labels={labels} showCredit={false} /> : null}
    </span>
  );
}

/** The verbatim Arabic. Verses use the Quran font (28px+, never clamped); every other type uses the reading font. */
function ArabicBox({ card, lang, quran, fallback }) {
  const labels = SOURCE_LABELS[pageLang(lang)].audio;
  // `segments` (resolved by the server since hk/01) wins; a raw {{verse:S:A}} marker in arabic_text still splits as before.
  const segments = card.segments?.length ? card.segments : splitVerseMarkers(card.arabic_text);
  return (
    <div
      dir="rtl"
      lang="ar"
      data-testid="arabic-text"
      className={quran ? `quran-text${fallback ? ' quran-fallback' : ''}` : 'reading-ar text-text'}
    >
      {segments.map((seg, i) => (seg.type === 'verse'
        ? <VerseMarker key={i} seg={seg} lang={lang} labels={labels} />
        : <span key={i}>{quran ? toDisplayArabic(seg.value, fallback) : seg.value}</span>))}
    </div>
  );
}

// Only a verse asks for the Quran font, so only a verse starts the font check.
function QuranArabic(props) {
  const fallback = useQuranFontFallback();
  return <ArabicBox {...props} quran fallback={fallback} />;
}

function ArabicText({ card, lang, quran }) {
  return quran
    ? <QuranArabic card={card} lang={lang} />
    : <ArabicBox card={card} lang={lang} quran={false} fallback={false} />;
}

function TranslationLine({ card, lang, dir }) {
  const line = translationLine(card, lang);
  if (!line) return null;
  return line.href ? (
    <a
      data-testid="translation-line"
      href={line.href}
      target="_blank"
      rel="noopener noreferrer"
      dir={dir}
      className="text-caption inline-flex min-h-target items-center gap-1 self-start text-primary-strong underline"
    >
      <bdi>{line.text}</bdi>
      <span className="sr-only">{SOURCE_LABELS[pageLang(lang)].newTab}</span>
      <ExternalLink aria-hidden="true" className="size-3" />
    </a>
  ) : (
    <p data-testid="translation-line" dir={dir} className="text-caption text-text-muted"><bdi>{line.text}</bdi></p>
  );
}

function EnglishBlock({ card, lang, dir }) {
  if (!card.english_text) return null;
  return (
    <div className="flex flex-col gap-1">
      <div dir="ltr" lang="en"> {/* avatar-integ: on an Arabic page the English stays LTR (end punctuation, brackets) */}
        <p data-testid="english-text" className="text-body text-text">{card.english_text}</p>
      </div>
      <TranslationLine card={card} lang={lang} dir={dir} />
    </div>
  );
}

/** Tier 2: our own words, labelled as our explanation and not the source's, in a visibly different style. Plain text only. */
function ExplanationBlock({ card, lang, dir }) {
  if (!card.explanation) return null;
  const explLang = card.explanation_lang;
  return (
    <section data-testid="explanation-block" className="src-explain flex flex-col gap-1" dir={dir}>
      <p data-testid="explanation-header" className="inline-flex items-center gap-1 text-label font-semibold text-text-muted">
        <Sparkles aria-hidden="true" className="size-4" />
        {EXPLANATION_HEADER[pageLang(lang)]}
      </p>
      <p
        lang={explLang}
        dir={explLang === 'ar' ? 'rtl' : explLang === 'en' ? 'ltr' : undefined}
        className="text-body text-text"
      >
        {card.explanation}
      </p>
    </section>
  );
}

function Footer({ card, lang }) {
  const L = SOURCE_LABELS[pageLang(lang)];
  return (
    <>
      {card.verification_status === 'reviewed' ? (
        <p data-testid="reviewed-line" title={L.reviewedTitle} className="inline-flex items-center gap-1 text-caption text-text-muted">
          <ShieldCheck aria-hidden="true" className="size-4" />
          {L.reviewed}
        </p>
      ) : null}
      <OpenSource card={card} lang={lang} />
    </>
  );
}

function pillInfo(type) {
  if (type === 'verse') return { variant: 'success', Icon: BookOpen };
  if (type === 'hadith') return { variant: 'warning', Icon: ScrollText };
  if (type === 'tafsir') return { variant: 'info', Icon: Library };
  return { variant: 'neutral', Icon: Library };
}

/**
 * SourceCard, shows the verse, hadith or source excerpt the companion just used.
 *
 * @param {{ card: object, lang?: 'ar'|'en' }} props card is a normalized `reference` payload
 *   (see normalizeReference); lang is the child's language (labels, direction), default 'en'.
 */
export default function SourceCard({ card, lang = 'en' }) {
  const language = pageLang(lang);
  const dir = language === 'ar' ? 'rtl' : 'ltr';
  const L = SOURCE_LABELS[language];
  const { variant, Icon } = pillInfo(card.type);
  const isVerse = card.type === 'verse';
  const isHadith = card.type === 'hadith';
  const isTafsir = card.type === 'tafsir';
  const audioSrc = isVerse ? safeAudioUrl(card.audio_url) : null;
  // Section 1.6: a non-verse card (FAQ, tafsir) whose verse segments carry audio shows the credit once, not once
  // per segment (VerseMarker's own buttons render with showCredit={false}). Same fallback as ArabicBox below
  // (server-resolved `segments` wins; an unresolved {{verse:S:A}} marker still splits client-side).
  const segmentAudio = !isVerse && segmentsHaveAudio(card.segments?.length ? card.segments : splitVerseMarkers(card.arabic_text));
  const citation = isHadith ? hadithCitationPieces(card, language) : isTafsir ? tafsirCitationPieces(card) : null;
  if (isHadith && !citation) return null; // a hadith that is not sahih never renders (second guard)

  return (
    <Card
      as="article"
      dir={dir}
      lang={language}
      data-card-type={card.type}
      className="flex flex-col gap-3 motion-safe:transition-all motion-safe:duration-300 motion-safe:starting:translate-y-2 motion-safe:starting:opacity-0"
    >
      <div className="flex flex-wrap items-center gap-2">
        <Pill variant={variant} icon={<Icon aria-hidden="true" className="size-4" />}>
          {L.pill[card.type]}
        </Pill>
        {card.value ? <Pill variant="neutral">{card.value}</Pill> : null}
      </div>

      {/* Tier 1: the source block, verbatim from the source. Nothing of our own words goes inside it. */}
      <div
        data-testid="source-block"
        className={`src-quote flex flex-col gap-3${isTafsir ? ' src-quote-tafsir' : ''}${!isVerse && !isHadith && !isTafsir ? ' src-quote-excerpt' : ''}`}
      >
        <Header card={card} lang={language} />
        {card.title ? <p dir="auto" className="text-heading text-text">{card.title}</p> : null}
        <ArabicText card={card} lang={language} quran={isVerse} />
        {segmentAudio ? <RecitationCreditLine card={card} lang={language} /> : null}

        {isVerse ? (
          <>
            <p data-testid="surah-line" className="text-heading text-text"><bdi>{surahLine(card, language)}</bdi></p>
            <EnglishBlock card={card} lang={language} dir={dir} />
            {verseCaption(card, language) ? (
              <p data-testid="verse-caption" className="text-caption text-text-muted">{verseCaption(card, language)}</p>
            ) : null}
            {audioSrc ? (
              <RecitationButton src={audioSrc} labels={L.audio} card={card} lang={language} />
            ) : null}
          </>
        ) : (
          <>
            {citation && citation.length ? (
              <p data-testid="citation-line" className="text-label text-text">
                <Pieces pieces={citation} />
              </p>
            ) : null}
            <EnglishBlock card={card} lang={language} dir={dir} />
          </>
        )}
      </div>

      {/* cards-spec (05) review: these two lines are our words, not the source's, so they sit outside the quote block. */}
      {card.type === 'fiqh' ? (
        <p data-testid="fiqh-note" className="text-label text-text">{L.fiqhNote}</p>
      ) : null}
      {card.content_level === 'C' && card.disagreement_note ? (
        <p data-testid="disagreement-note" className="text-label text-text">
          <strong>{L.scholarsDiffer}</strong> {card.disagreement_note}
        </p>
      ) : null}

      {/* Tier 2: always after the source block in the DOM, always labelled. */}
      <ExplanationBlock card={card} lang={language} dir={dir} />
      <Footer card={card} lang={language} />
    </Card>
  );
}
