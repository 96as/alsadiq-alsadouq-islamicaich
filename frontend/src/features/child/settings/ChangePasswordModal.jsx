import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { Eye, EyeOff, X } from 'lucide-react';
import { Button, Card, IconButton, TextField } from '../../../components/ui';
import { changeChildPassword } from '../../../services/authService';
import { validateStrongPassword } from '../../../utils/validators';
import { dirOf, useLang, useStrings } from '../../../i18n'; // i18n // cards-spec (05)

const ChangePasswordModal = ({ open, onClose }) => {
  const lang = useLang();
  const s = useStrings().password;
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const modalRef = useRef(null);
  const closeBtnRef = useRef(null);
  const lastFocusedRef = useRef(null);

  // Reset the form whenever the modal opens (adjusting state during render, not in an effect).
  const [wasOpen, setWasOpen] = useState(open);
  if (open !== wasOpen) {
    setWasOpen(open);
    if (open) {
      setNewPassword('');
      setConfirmPassword('');
      setShowPassword(false);
      setError('');
      setSuccess(false);
    }
  }

  useEffect(() => {
    if (!open) {
      if (lastFocusedRef.current?.focus) {
        lastFocusedRef.current.focus();
      }
      return undefined;
    }

    lastFocusedRef.current = document.activeElement;
    closeBtnRef.current?.focus();

    const onKey = (e) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
        return;
      }
      if (e.key !== 'Tab' || !modalRef.current) return;
      const focusable = modalRef.current.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
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
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const pwError = validateStrongPassword(newPassword, lang);
    if (pwError) {
      setError(pwError);
      return;
    }
    if (newPassword !== confirmPassword) {
      setError(s.mismatch);
      return;
    }

    setSubmitting(true);
    try {
      await changeChildPassword(newPassword);
      setSuccess(true);
    } catch (err) {
      const body = err.response?.data;
      if (body?.detail) {
        setError(String(body.detail));
      } else if (body?.new_password) {
        const msg = Array.isArray(body.new_password) ? body.new_password.join(' ') : String(body.new_password);
        setError(msg);
      } else {
        setError(err.message || s.failed);
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (!open) return null;

  return createPortal(
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 p-3 sm:p-4"
      role="dialog"
      dir={dirOf(lang)}
      lang={lang}
      aria-modal="true"
      aria-labelledby="change-password-title"
      onClick={onClose}
    >
      <Card
        ref={modalRef}
        padding="lg"
        className="max-h-[min(90dvh,calc(100dvh-1.5rem))] w-full max-w-md overflow-y-auto pb-[max(1.5rem,env(safe-area-inset-bottom))]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-3">
          <h2 id="change-password-title" className="text-title text-text">
            {s.title}
          </h2>
          <IconButton
            ref={closeBtnRef}
            label={s.close}
            variant="ghost"
            onClick={onClose}
            icon={<X className="size-6" aria-hidden="true" />}
          />
        </div>
        <p className="mt-1 text-body text-text-muted">
          {s.intro}
        </p>

        {success ? (
          <div className="mt-6 space-y-3 pb-2 text-center">
            <p className="text-heading text-primary-strong">
              {s.updated}
            </p>
            <p className="text-body text-text-muted">
              {s.updatedNote}
            </p>
            <Button onClick={onClose} className="w-full">
              {s.done}
            </Button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} noValidate /* cards-spec (05): our messages in the page language, not the browser's bubble */ className="mt-6 space-y-4 pb-2">
            <TextField
              label={s.newLabel}
              type={showPassword ? 'text' : 'password'}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder={s.newHint}
              required
              autoComplete="new-password"
              endAdornment={(
                <IconButton
                  label={showPassword ? s.hide : s.show}
                  variant="ghost"
                  className="border-0"
                  onClick={() => setShowPassword((v) => !v)}
                  icon={showPassword
                    ? <EyeOff className="size-5" aria-hidden="true" />
                    : <Eye className="size-5" aria-hidden="true" />}
                />
              )}
            />

            <TextField
              label={s.confirmLabel}
              type={showPassword ? 'text' : 'password'}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder={s.confirmHint}
              required
              autoComplete="new-password"
            />

            {error ? (
              <p role="alert" className="break-words text-label text-danger-strong">
                {error}
              </p>
            ) : null}

            <Button type="submit" loading={submitting} className="w-full">
              {submitting ? s.submitting : s.submit}
            </Button>
          </form>
        )}
      </Card>
    </div>,
    document.body,
  );
};

export default ChangePasswordModal;
