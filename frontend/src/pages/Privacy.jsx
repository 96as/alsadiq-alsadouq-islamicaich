// cards-spec (05) section 5: the public privacy page. Route /privacy, outside every guard.
import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, Languages, ShieldCheck } from 'lucide-react';
import { PRIVACY_CONTENT } from '../features/privacy/privacyContent';
import { ROUTES } from '../routes';

function initialLang(search) {
  const asked = search.get('lang');
  if (asked === 'ar' || asked === 'en') return asked;
  try {
    return String(navigator.language || '').toLowerCase().startsWith('ar') ? 'ar' : 'en';
  } catch {
    return 'en';
  }
}

function Block({ block }) {
  switch (block.t) {
    case 'p':
      return <p className="text-body text-text">{block.text}</p>;
    case 'lead':
      return (
        <p className="text-body text-text">
          <strong className="font-bold">{block.lead}</strong> {block.text}
        </p>
      );
    case 'ul':
      return (
        <ul className="list-disc space-y-2 ps-6 text-body text-text marker:text-primary-strong">
          {block.items.map((item) => <li key={item}>{item}</li>)}
        </ul>
      );
    case 'lines':
      return (
        <address className="space-y-1 text-body not-italic text-text">
          {block.lines.map((line) => <p key={line}>{line}</p>)}
        </address>
      );
    case 'table':
      // Real table with a caption. Below sm each row stacks as a card with its column name in front of every value.
      return (
        <table role="table" className="w-full border-collapse text-start text-label text-text">
          <caption className="pb-2 text-start text-label font-semibold text-text-muted">{block.caption}</caption>
          <thead role="rowgroup" className="sr-only sm:not-sr-only sm:table-header-group">
            <tr role="row" className="sm:table-row">
              {block.head.map((h) => (
                <th key={h} role="columnheader" scope="col" className="border-b border-border bg-surface-alt px-3 py-2 text-start font-bold">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody role="rowgroup" className="block sm:table-row-group">
            {block.rows.map((row) => (
              <tr key={row[0]} role="row" className="mb-3 block rounded-2xl border border-border sm:mb-0 sm:table-row sm:rounded-none sm:border-0">
                {row.map((cell, i) => (
                  <td
                    key={block.head[i]}
                    role="cell"
                    data-label={block.head[i]}
                    className="block px-3 py-2 align-top before:block before:text-caption before:font-bold before:text-text-muted before:content-[attr(data-label)] sm:table-cell sm:border-b sm:border-border sm:before:hidden"
                  >
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      );
    default:
      return null;
  }
}

const Privacy = () => {
  const [search] = useSearchParams();
  const navigate = useNavigate();
  const [lang, setLang] = useState(() => initialLang(search));
  const c = PRIVACY_CONTENT[lang];

  const goBack = () => {
    if (window.history.length > 1) navigate(-1);
    else navigate(ROUTES.LOGIN);
  };

  return (
    <div
      className="relative flex min-h-0 flex-1 flex-col items-center overflow-y-auto bg-bg p-4 text-text antialiased sm:p-6"
      data-theme="child"
      data-view="privacy"
    >
      <main dir={c.dir} lang={c.lang} className="w-full max-w-3xl py-4" data-testid="privacy-page">
        <div className="flex items-center justify-between gap-3">
          <button
            type="button"
            onClick={goBack}
            className="inline-flex min-h-target cursor-pointer items-center gap-2 rounded-full border border-border bg-surface px-4 text-label text-text focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-strong"
          >
            <ArrowLeft aria-hidden="true" className={`size-4 ${c.dir === 'rtl' ? 'rotate-180' : ''}`} />
            {c.back}
          </button>
          <button
            type="button"
            onClick={() => setLang(lang === 'ar' ? 'en' : 'ar')}
            aria-label={c.switchLabel}
            data-testid="privacy-lang-toggle"
            className="inline-flex min-h-target cursor-pointer items-center gap-2 rounded-full border border-border bg-surface px-4 text-label text-text focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-strong"
          >
            <Languages aria-hidden="true" className="size-4" />
            {c.switchTo}
          </button>
        </div>

        <header className="mt-6 flex flex-col gap-2">
          <p className="inline-flex items-center gap-2 text-label font-semibold text-primary-strong">
            <ShieldCheck aria-hidden="true" className="size-5" />
            {c.subtitle}
          </p>
          <h1 className="text-display text-text">{c.title}</h1>
          <p
            data-testid="privacy-draft-banner"
            className="self-start rounded-full bg-accent-soft px-4 py-1 text-label font-semibold text-text"
          >
            {c.draft}
          </p>
        </header>

        <div className="mt-6 flex flex-col gap-8">
          {c.sections.map((section) => (
            <section key={section.heading} className="flex flex-col gap-3">
              <h2 className="text-title text-text">{section.heading}</h2>
              {section.blocks.map((block, i) => <Block key={i} block={block} />)}
            </section>
          ))}
        </div>

        <p className="mt-10 text-center text-label text-text-muted">
          <Link to={ROUTES.LOGIN} className="inline-flex min-h-11 items-center underline">Al-Sadiq Al-Sadouq</Link>
        </p>
      </main>
    </div>
  );
};

export default Privacy;
