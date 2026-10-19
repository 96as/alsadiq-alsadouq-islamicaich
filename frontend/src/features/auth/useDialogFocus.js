import { useEffect, useRef } from 'react';

/**
 * Dialog behaviour: focus moves to initialRef on open, Escape closes, Tab is trapped,
 * and focus returns to the previously focused element on close.
 * Returns { dialogRef, initialRef }. Pass a stable onClose.
 */
export default function useDialogFocus(open, onClose) {
  const dialogRef = useRef(null);
  const initialRef = useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    const previous = document.activeElement;
    initialRef.current?.focus();

    const onKey = (e) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
        return;
      }
      if (e.key !== 'Tab' || !dialogRef.current) return;
      const focusable = dialogRef.current.querySelectorAll(
        'button:not([disabled]), [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
      );
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };

    window.addEventListener('keydown', onKey);
    return () => {
      window.removeEventListener('keydown', onKey);
      if (previous?.focus) previous.focus();
    };
  }, [open, onClose]);

  return { dialogRef, initialRef };
}
