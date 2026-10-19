// cards-spec (05) section 4.1: the permanent AI chip. Always visible on the conversation screen (every session
// state, chat and voice), never hideable, and it does not scroll away (fixed position).
import { useCallback, useState } from 'react';
import AiInfoSheet from './AiInfoSheet';
import { AI_STRINGS } from './aiStrings';

/**
 * @param {{ lang?: 'ar'|'en', className?: string }} props
 */
export default function AiChip({ lang = 'en', className = '' }) {
  const [open, setOpen] = useState(false);
  const close = useCallback(() => setOpen(false), []);
  const s = AI_STRINGS[lang === 'ar' ? 'ar' : 'en'];
  return (
    <>
      <button
        type="button"
        data-testid="ai-chip"
        dir={lang === 'ar' ? 'rtl' : 'ltr'} // end-3 follows the child's language, the same side the header reserves
        aria-label={s.chipLabel}
        aria-haspopup="dialog"
        onClick={() => setOpen(true)}
        // cards-spec (05) judge r2: below the demo bar when it is shown (DemoBanner sets --demo-bar-h). At top-3 the bar
        // (z-40, outside this page's z-10 layer) covered the chip in every demo session, so judges could not open it.
        style={{ top: 'calc(var(--demo-bar-h, 0px) + 0.75rem)' }}
        className={`fixed end-3 z-[70] inline-flex min-h-target min-w-target cursor-pointer items-center justify-center rounded-full border-2 border-primary-strong bg-surface px-4 text-heading font-extrabold text-primary-strong shadow-[0_4px_16px_var(--color-shadow)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-strong ${className}`}
      >
        {s.chipText}
      </button>
      <AiInfoSheet open={open} onClose={close} lang={lang} />
    </>
  );
}
