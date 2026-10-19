// cards-spec (05) section 4.2: "Sadiq is an AI" info sheet. Short sentences for readers aged 6 to 13,
// the child's language first, an EN/AR toggle inside, focus trapped by useDialogFocus (Escape closes, focus returns).
import { useCallback, useId, useState } from 'react';
import { createPortal } from 'react-dom'; // cards-spec (05) judge r2
import { ExternalLink, Languages, Sparkles, X } from 'lucide-react';
import useDialogFocus from '../../auth/useDialogFocus';
import { ROUTES } from '../../../routes';
import { assetUrl } from '../../../utils/assetUrl';
import { AI_STRINGS, SHOW_PARENT_SUMMARY_LINE } from './aiStrings';

/**
 * @param {{ open: boolean, onClose: () => void, lang?: 'ar'|'en' }} props
 */
export default function AiInfoSheet({ open, onClose, lang = 'en' }) {
  const titleId = useId();
  const [override, setOverride] = useState(null); // the toggle inside the sheet, reset each time the sheet opens
  const stableClose = useCallback(() => {
    setOverride(null);
    onClose();
  }, [onClose]);
  const { dialogRef, initialRef } = useDialogFocus(open, stableClose);
  if (!open) return null;

  const shown = override || (lang === 'ar' ? 'ar' : 'en');
  const s = AI_STRINGS[shown];
  const dir = shown === 'ar' ? 'rtl' : 'ltr';
  const lines = [s.line1, s.line2, s.line3, s.line4, ...(SHOW_PARENT_SUMMARY_LINE ? [s.line5] : [])];

  // cards-spec (05) judge r2: portalled to <body> (like ChangePasswordModal). Inside the page's z-10 layer the floating
  // Home nav (z-30) covered the sheet's privacy link on phones, and the demo bar covered its top.
  return createPortal(
    <div
      className="fixed inset-0 z-[80] flex items-end justify-center bg-black/50 p-0 sm:items-center sm:p-4"
      onMouseDown={(e) => { if (e.target === e.currentTarget) stableClose(); }}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        dir={dir}
        lang={shown}
        data-testid="ai-info-sheet"
        className="flex max-h-[92dvh] w-full max-w-lg flex-col gap-4 overflow-y-auto rounded-t-3xl border border-border bg-surface p-6 text-text shadow-[0_-8px_32px_var(--color-shadow)] sm:rounded-3xl"
      >
        <div className="flex items-start justify-between gap-3">
          <h2 id={titleId} className="inline-flex items-center gap-2 text-title text-text">
            <Sparkles aria-hidden="true" className="size-6 text-primary-strong" />
            {s.title}
          </h2>
          <button
            type="button"
            onClick={() => setOverride(shown === 'ar' ? 'en' : 'ar')}
            aria-label={s.toggleLabel}
            data-testid="ai-sheet-lang-toggle"
            className="inline-flex min-h-target shrink-0 cursor-pointer items-center gap-1 rounded-full border border-border px-4 text-label text-text focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-strong"
          >
            <Languages aria-hidden="true" className="size-4" />
            {s.toggleTo}
          </button>
        </div>

        <ul className="flex flex-col gap-3 text-body text-text">
          {lines.map((line) => (
            <li key={line} className="rounded-2xl bg-surface-alt px-4 py-3">{line}</li>
          ))}
        </ul>

        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <button
            ref={initialRef}
            type="button"
            onClick={stableClose}
            className="inline-flex min-h-target min-w-target cursor-pointer items-center justify-center gap-2 rounded-full bg-primary-strong px-8 text-heading text-on-strong focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-strong"
          >
            <X aria-hidden="true" className="size-5" />
            {s.button}
          </button>
          {/* A new tab: leaving this page would end the live conversation. */}
          <a
            href={assetUrl(`${ROUTES.PRIVACY}?lang=${shown}`)}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex min-h-target items-center justify-center gap-1 text-label text-primary-strong underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-strong"
          >
            {s.link}
            <ExternalLink aria-hidden="true" className="size-4" />
          </a>
        </div>
      </div>
    </div>,
    document.body,
  );
}
