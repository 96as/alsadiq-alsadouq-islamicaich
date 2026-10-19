// Task 04: the trust parts of the parent Insights page (docs/hackathon/handoffs/04-parent-trust.md).
// Every label the API sends comes as { en, ar } and is shown as sent, in the UI language: this file hard-codes none of
// them. It only adds what the API does not send (the sources title and "discussed N times", both in i18n/strings.js).
// All of the data is database-only (ServedReference, TurnAudit, the value bank): no child message text reaches it.
import { useId, useMemo } from 'react';
import { Info, MessageCircle, Sparkles } from 'lucide-react';
import { Pill } from '../../../components/ui';
import { num, shortDate, useLang, useStrings } from '../../../i18n';
import { normalizeReference } from '../../child/sources/useSourceCards';
import ParentSourceCard from './ParentSourceCard';

/** An API label is { en, ar }: the UI language's text, else English, else nothing (the line is then left out). */
const pick = (label, lang) => label?.[lang] || label?.en || '';
/** A bank name or description that the API sends as an English and an Arabic field. */
const byLang = (lang, en, ar) => (lang === 'ar' ? ar || en : en || ar) || '';

/** `bare`: the title is already shown by a collapsible row around the section, so it stays for screen readers only. */
export function Title({ id, children, bare = false }) {
  return <h3 id={id} className={bare ? 'sr-only' : 'mb-3 text-heading text-text'}>{children}</h3>;
}

/** "Written by AI ..." / "Suggested by AI": visible text, 14px, never a tooltip. `label` is an { en, ar } object from the API. */
export function AiLabel({ label }) {
  const lang = useLang();
  const text = pick(label, lang);
  if (!text) return null;
  return (
    <p className="mb-2 flex items-start gap-1.5 text-label text-text">
      <Sparkles aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
      <span>{text}</span>
    </p>
  );
}

/** "Sources discussed this week": the trust line, one card per source, the "reviewed" footer, or the empty message. */
export function SourcesDiscussed({ data, bare = false }) {
  const lang = useLang();
  const s = useStrings().parent.insights;
  const titleId = useId();
  const items = useMemo(() => {
    // sources[].value_name is the bank's English name; values_this_week carries the Arabic name of the same value.
    const arabicName = new Map((data?.values_this_week || []).map((v) => [v.name_en, v.name_ar]));
    return (data?.sources || []).flatMap((raw) => {
      const card = normalizeReference(raw);
      if (!card) {
        if (import.meta.env.DEV) console.warn('Dropped a source the child card would not show', raw?.id);
        return [];
      }
      const name = typeof raw.value_name === 'string' ? raw.value_name : '';
      return [{
        card,
        times: Number.isInteger(raw.times_discussed) ? raw.times_discussed : 0,
        valueName: lang === 'ar' ? arabicName.get(name) || name : name,
      }];
    });
  }, [data, lang]);

  const labels = data?.labels || {};
  const trust = pick(data?.trust_line, lang);
  const reviewed = pick(labels.reviewed, lang);
  const notScholar = pick(labels.not_scholar_reviewed, lang);
  const footer = pick(labels.sources_footer, lang);
  const noSources = pick(labels.no_sources, lang);
  // No `sources` key at all (a server without task 04): say nothing rather than "no sources".
  if (!Array.isArray(data?.sources)) return null;
  // The empty message follows the API's list, not what could be drawn: never say "no sources" when there were some.
  const noneThisWeek = data.sources.length === 0;
  // Sources came but none can be drawn: nothing under the title beyond a lone trust line would mislead, so say nothing.
  if (!noneThisWeek && items.length === 0) return null;

  return (
    <section className={bare ? undefined : 'mt-8'} aria-labelledby={titleId}>
      <Title id={titleId} bare={bare}>{s.sourcesTitle}</Title>
      {trust ? (
        <p className="mb-4 flex items-start gap-2 rounded-2xl bg-info-soft px-4 py-3 text-body text-text">
          <Info aria-hidden="true" className="mt-0.5 size-5 shrink-0" />
          <span>{trust}</span>
        </p>
      ) : null}
      {items.length > 0 ? (
        <>
          <ul className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {items.map(({ card, times, valueName }) => (
              <li key={card.id} className="min-w-0">
                <ParentSourceCard
                  card={card}
                  lang={lang}
                  times={times}
                  valueName={valueName}
                  reviewedLabel={reviewed}
                  notScholarLabel={notScholar}
                />
              </li>
            ))}
          </ul>
          {footer ? <p className="mt-4 text-label text-text-muted">{footer}</p> : null}
        </>
      ) : noneThisWeek && noSources ? (
        <p className="text-body text-text-muted">{noSources}</p>
      ) : null}
    </section>
  );
}

/** "Values this week": neutral counts from the value bank (names come only from the bank). Hidden when there are none. */
export function ValuesThisWeek({ values, title, bare = false }) {
  const lang = useLang();
  const titleId = useId();
  const heading = pick(title, lang);
  if (!heading || !Array.isArray(values) || values.length === 0) return null;
  return (
    <section className={bare ? undefined : 'mt-8'} aria-labelledby={titleId}>
      <Title id={titleId} bare={bare}>{heading}</Title>
      <ul className="flex flex-wrap gap-2">
        {values.map((v) => (
          <li key={v.slug}>
            <Pill variant="success" className="gap-2">
              <bdi dir="auto">{byLang(lang, v.name_en, v.name_ar)}</bdi>
              <span className="min-w-6 rounded-full bg-surface px-2 text-center text-text">{num(v.count, lang)}</span>
            </Pill>
          </li>
        ))}
      </ul>
    </section>
  );
}

/** "Questions Sadiq asked you to discuss": topic and a plain-words description only. Hidden when the list is empty. */
export function QuestionsToDiscuss({ items, title, bare = false }) {
  const lang = useLang();
  const titleId = useId();
  const heading = pick(title, lang);
  if (!heading || !Array.isArray(items) || items.length === 0) return null;
  return (
    <section className={bare ? undefined : 'mt-8'} aria-labelledby={titleId}>
      <Title id={titleId} bare={bare}>{heading}</Title>
      <ul className="max-w-3xl space-y-2 lg:max-w-none">
        {items.map((q, i) => {
          // topic is empty when the question is not linked to a value: the description is then all there is.
          const topic = byLang(lang, q.topic_en, q.topic_ar);
          const description = byLang(lang, q.description_en, q.description_ar);
          return (
            <li key={q.topic || i} className="flex items-start gap-3 rounded-2xl bg-info-soft px-4 py-3">
              <MessageCircle aria-hidden="true" className="mt-0.5 size-5 shrink-0 text-text" />
              <p dir="auto" className="text-body text-text">
                {topic ? <strong>{topic}</strong> : null}
                {topic && description ? ' · ' : null}
                {description}
              </p>
              {q.date ? <span className="ms-auto shrink-0 text-label text-text-muted">{shortDate(q.date, lang)}</span> : null}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
