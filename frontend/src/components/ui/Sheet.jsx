import { useId } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';
import useDialogFocus from '../../features/auth/useDialogFocus';
import { useStrings } from '../../i18n';
import IconButton from './IconButton';

/**
 * Bottom sheet on phones, centred dialog from `sm:` up.
 * Props: open, onClose (stable, e.g. useCallback), title (string, labels the dialog), icon (node, before the title),
 * children (the body). Focus moves to the close button, Tab is trapped, Esc and a backdrop tap close,
 * and focus returns to whatever opened it (useDialogFocus).
 */
export default function Sheet({ open, onClose, title, icon = null, children }) {
  const titleId = useId();
  const { dialogRef, initialRef } = useDialogFocus(open, onClose);
  const closeLabel = useStrings().common.close;
  if (!open) return null;

  // Portalled to <body>: the floating child nav (z-30) would otherwise sit over the bottom of the sheet.
  return createPortal(
    <div
      className="fixed inset-0 z-[80] flex items-end justify-center bg-black/50 sm:items-center sm:p-4"
      onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="flex max-h-[92dvh] w-full max-w-lg flex-col gap-4 overflow-y-auto rounded-t-3xl border border-border bg-surface px-6 pt-3 pb-[max(1.5rem,env(safe-area-inset-bottom))] text-text shadow-[0_-8px_32px_var(--color-shadow)] motion-safe:transition-[translate,opacity] motion-safe:duration-300 motion-safe:starting:translate-y-full sm:rounded-3xl sm:pt-6 sm:motion-safe:starting:translate-y-6 sm:motion-safe:starting:opacity-0"
      >
        <span aria-hidden="true" className="mx-auto h-1.5 w-12 shrink-0 rounded-full bg-border sm:hidden" />
        <div className="flex items-start justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
            {icon}
            <h2 id={titleId} dir="auto" className="min-w-0 text-title text-text">{title}</h2>
          </div>
          <IconButton
            ref={initialRef}
            label={closeLabel}
            icon={<X aria-hidden="true" className="size-6" />}
            onClick={onClose}
            className="shrink-0"
          />
        </div>
        {children}
      </div>
    </div>,
    document.body,
  );
}
