import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';
import { createChild } from '../../../services/authService';
import { validateStrongPassword } from '../../../utils/validators';
import { Button, TextField } from '../../../components/ui';

const SELECT_CLASS =
  'min-h-target w-full rounded-2xl border border-border bg-surface px-4 text-body text-text focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-strong';

/**
 * Modal to create a child account (POST /api/auth/children/).
 */
const AddChildModal = ({ open, onClose, onCreated }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [nickname, setNickname] = useState('');
  const [birthYear, setBirthYear] = useState(String(new Date().getFullYear() - 10));
  const [gender, setGender] = useState('male');
  const [languagePreference, setLanguagePreference] = useState('en');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});
  const modalRef = useRef(null);
  const closeBtnRef = useRef(null);
  const lastFocusedRef = useRef(null);

  const parseApiErrors = (body) => {
    if (!body) return { general: 'Could not create account. Please try again.', fields: {} };
    if (typeof body === 'string') return { general: body, fields: {} };
    if (body.detail) return { general: String(body.detail), fields: {} };

    const fields = {};
    let general = '';
    Object.entries(body).forEach(([key, val]) => {
      const msg = Array.isArray(val) ? val.map(String).join(' ') : String(val);
      if (['username', 'password', 'nickname', 'birth_year', 'gender', 'language_preference'].includes(key)) {
        fields[key] = msg;
      } else if (!general) {
        general = msg;
      }
    });

    return { general, fields };
  };

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
    setFieldErrors({});

    const pwError = validateStrongPassword(password);
    if (pwError) {
      setFieldErrors({ password: pwError });
      return;
    }

    setSubmitting(true);
    try {
      await createChild({
        username: username.trim(),
        password,
        nickname: nickname.trim(),
        birth_year: parseInt(birthYear, 10),
        gender,
        language_preference: languagePreference,
      });
      setUsername('');
      setPassword('');
      setNickname('');
      setBirthYear(String(new Date().getFullYear() - 10));
      setGender('male');
      setLanguagePreference('en');
      onCreated?.();
      onClose();
    } catch (err) {
      const body = err.response?.data;
      const parsed = parseApiErrors(body);
      setFieldErrors(parsed.fields);
      setError(parsed.general || err.message || 'Could not create account');
    } finally {
      setSubmitting(false);
    }
  };

  if (!open) return null;

  // Render at document root so z-index competes above ChildLayout’s bottom nav (z-30).
  // When nested under the shell’s z-10 outlet, a high z on this dialog still loses to the nav.
  // The portal sits outside the themed shell, so it sets data-theme itself.
  return createPortal(
    <div
      data-theme="parent"
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 p-3 sm:p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="add-child-title"
      onClick={onClose}
    >
      <div
        ref={modalRef}
        className="max-h-[min(90dvh,calc(100dvh-1.5rem))] w-full max-w-md overflow-y-auto rounded-3xl border border-border bg-surface px-5 pt-5 pb-[max(1.05rem,env(safe-area-inset-bottom))] text-text sm:max-h-[90vh] sm:p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-3">
          <h2 id="add-child-title" className="text-title text-text">
            Add child
          </h2>
          <button
            ref={closeBtnRef}
            type="button"
            onClick={onClose}
            className="inline-flex min-h-11 min-w-11 cursor-pointer items-center justify-center rounded-full text-text-muted hover:bg-surface-alt hover:text-text focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-strong"
            aria-label="Close"
          >
            <X aria-hidden="true" className="size-5" />
          </button>
        </div>
        <p className="mt-1 text-body text-text-muted">
          Create a login for your child. They will use this username and password in the child app.
        </p>

        <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4 pb-4">
          <TextField
            label="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            error={fieldErrors.username}
            required
            autoComplete="off"
          />
          <TextField
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={fieldErrors.password}
            required
            autoComplete="new-password"
            placeholder="Min. 8 chars, upper, lower, num, symbol"
          />
          <TextField
            label="Display name"
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
            error={fieldErrors.nickname}
            required
            maxLength={50}
          />
          <div className="grid grid-cols-2 gap-3">
            <TextField
              label="Birth year"
              type="number"
              value={birthYear}
              onChange={(e) => setBirthYear(e.target.value)}
              error={fieldErrors.birth_year}
              required
              min={new Date().getFullYear() - 13}
              max={new Date().getFullYear() - 6}
            />
            <div className="flex flex-col gap-2">
              <label htmlFor="add-child-gender" className="text-label text-text">Gender</label>
              <select
                id="add-child-gender"
                className={SELECT_CLASS}
                value={gender}
                onChange={(e) => setGender(e.target.value)}
                aria-invalid={fieldErrors.gender ? true : undefined}
                aria-describedby={fieldErrors.gender ? 'add-child-gender-error' : undefined}
              >
                <option value="male">Male</option>
                <option value="female">Female</option>
              </select>
              {fieldErrors.gender ? (
                <p id="add-child-gender-error" className="text-label text-danger-strong">{fieldErrors.gender}</p>
              ) : null}
            </div>
          </div>
          <div className="flex flex-col gap-2">
            <label htmlFor="add-child-language" className="text-label text-text">
              Session language
            </label>
            <select
              id="add-child-language"
              className={SELECT_CLASS}
              value={languagePreference}
              onChange={(e) => setLanguagePreference(e.target.value)}
            >
              <option value="en">English</option>
              <option value="ar">Arabic / العربية</option>
            </select>
            <p className="text-caption text-text-muted">
              Al-Sadiq will start sessions in this language. Your child can change it later in Settings.
            </p>
            {fieldErrors.language_preference ? (
              <p className="text-label text-danger-strong">{fieldErrors.language_preference}</p>
            ) : null}
          </div>

          {error ? (
            <p className="break-words text-label text-danger-strong" role="alert">{error}</p>
          ) : null}

          <Button type="submit" loading={submitting}>
            {submitting ? 'Creating…' : 'Create child account'}
          </Button>
        </form>
      </div>
    </div>,
    document.body,
  );
};

export default AddChildModal;
