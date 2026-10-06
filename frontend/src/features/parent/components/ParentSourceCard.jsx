// Task 04: one source the child heard this week, as the parent sees it on the Insights page.
// Wording, guards and fonts are the child card's (features/child/sources). The section normalizes every source with
// normalizeReference first, so a card that reaches this file already has an approved source link, a sahih hadith and a
// valid verse. It shows the source's own text and citation only: the child explanation is the child's tier, and the
// API does not send it. The two review labels come from the API (props), never from this file.
import { BookOpen, ExternalLink, Library, ScrollText, ShieldCheck } from 'lucide-react';
import { Card, Pill } from '../../../components/ui';
import { FOCUS_RING, cx } from '../../../components/ui/cx';
import { dirOf, useStrings } from '../../../i18n';
import { toDisplayArabic } from '../../child/sources/quranText';
import { safeSourceUrl } from '../../child/sources/safeUrl';
import {
  CITATION_SEPARATOR, SOURCE_LABELS, hadithCitationPieces, openSourceLabel, sourceHeader, surahLine,
  tafsirCitationPieces, translationLine, verseCaption,
} from '../../child/sources/sourceLabels';
import useQuranFontFallback from '../../child/sources/useQuranFontFallback';
import '../../child/sources/sourceCards.css';

const PILLS = { verse: ['success', BookOpen], hadith: ['warning', ScrollText], tafsir: ['info', Library] };

/** Verses use the Quran font; while the fallback font is in use the three legacy marks are mapped at display time only. */
function QuranArabic({ text }) {
  const fallback = useQuranFontFallback();
  return (
    <div dir="rtl" lang="ar" className={`quran-text${fallback ? ' quran-fallback' : ''}`}>
      {toDisplayArabic(text, fallback)}
    </div>
  );
}

/** A link that opens in a new tab. The visible text is wrapped in <bdi> so Arabic and Latin names never scramble. */
function NewTabLink({ href, lang, className, iconClass = 'size-4', children }) {
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" className={className}>
      <bdi>{children}</bdi>
      <span className="sr-only">{SOURCE_LABELS[lang].newTab}</span>
      <ExternalLink aria-hidden="true" className={iconClass} />
    </a>
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
 * @param {{ card: object, lang: 'ar'|'en', times: number, valueName: string,
 *   reviewedLabel: string, notScholarLabel: string }} props
 *   card is a normalizeReference result; reviewedLabel and notScholarLabel are the API's labels for this language.
 */
export default function ParentSourceCard({ card, lang, times, valueName, reviewedLabel, notScholarLabel }) {
  const s = useStrings().parent.insights;
  const isVerse = card.type === 'verse';
  const [variant, Icon] = PILLS[card.type] || ['neutral', Library];
  const header = sourceHeader(card, lang);
  const [beforeBook, afterBook] = header ? header.template.split('{book}') : [];
  const citation = card.type === 'hadith'
    ? hadithCitationPieces(card, lang)
    : card.type === 'tafsir' ? tafsirCitationPieces(card) : null;
  const translation = translationLine(card, lang);
  const caption = isVerse ? verseCaption(card, lang) : '';
  const sourceHref = safeSourceUrl(card.source_url);
  const tinted = card.type === 'tafsir' ? ' src-quote-tafsir' : isVerse || card.type === 'hadith' ? '' : ' src-quote-excerpt';

  return (
    <Card
      as="article"
      dir={dirOf(lang)}
      lang={lang}
      data-testid="parent-source-card"
      data-card-type={card.type}
      className="flex h-full flex-col gap-3"
    >
      <div className="flex flex-wrap items-center gap-2">
        <Pill variant={variant} icon={<Icon aria-hidden="true" className="size-4" />}>
          {SOURCE_LABELS[lang].pill[card.type]}
        </Pill>
        {valueName ? <Pill variant="neutral"><bdi dir="auto">{valueName}</bdi></Pill> : null}
        {times > 0 ? <span className="ms-auto text-label text-text-muted">{s.discussed(times)}</span> : null}
      </div>

      {/* The source's own words, verbatim, with its citation. Nothing of ours goes inside this block. */}
      <div className={`src-quote flex flex-col gap-3${tinted}`}>
        {header ? (
          <p className="text-label font-semibold text-text">
            {afterBook === undefined ? header.template : <>{beforeBook}<bdi>{header.book}</bdi>{afterBook}</>}
          </p>
        ) : null}
        {card.title ? <p dir="auto" className="text-heading text-text">{card.title}</p> : null}
        {isVerse ? (
          <QuranArabic text={card.arabic_text} />
        ) : (
          <div dir="rtl" lang="ar" className="reading-ar text-text">{card.arabic_text}</div>
        )}
        {isVerse ? <p className="text-heading text-text"><bdi>{surahLine(card, lang)}</bdi></p> : null}
        {citation && citation.length ? (
          <p className="text-label text-text"><Pieces pieces={citation} /></p>
        ) : null}
        {card.english_text ? (
          <div className="flex flex-col gap-1">
            <div dir="ltr" lang="en">
              <p className="text-body text-text">{card.english_text}</p>
            </div>
            {translation && translation.href ? (
              <NewTabLink
                href={translation.href}
                lang={lang}
                iconClass="size-3.5"
                className="inline-flex items-center gap-1 self-start text-label text-primary-strong underline"
              >
                {translation.text}
              </NewTabLink>
            ) : translation ? (
              <p className="text-label text-text-muted"><bdi>{translation.text}</bdi></p>
            ) : null}
          </div>
        ) : null}
        {caption ? <p className="text-label text-text-muted">{caption}</p> : null}
      </div>

      {card.type === 'fiqh' ? <p className="text-label text-text">{SOURCE_LABELS[lang].fiqhNote}</p> : null}
      {card.content_level === 'C' && card.disagreement_note ? (
        <p className="text-label text-text">
          <strong>{SOURCE_LABELS[lang].scholarsDiffer}</strong> <span dir="auto">{card.disagreement_note}</span>
        </p>
      ) : null}

      <div className="mt-auto flex flex-wrap items-center justify-between gap-3">
        {card.verification_status === 'reviewed' && reviewedLabel ? (
          <p title={notScholarLabel || undefined} className="inline-flex items-center gap-1.5 text-label text-text-muted">
            <ShieldCheck aria-hidden="true" className="size-4 shrink-0" />
            {reviewedLabel}
          </p>
        ) : null}
        {sourceHref ? (
          <NewTabLink
            href={sourceHref}
            lang={lang}
            className={cx(
              'inline-flex min-h-11 items-center justify-center gap-2 rounded-3xl bg-primary-soft px-4 text-label text-text no-underline',
              FOCUS_RING,
            )}
          >
            {openSourceLabel(card, lang)}
          </NewTabLink>
        ) : null}
      </div>
    </Card>
  );
}
