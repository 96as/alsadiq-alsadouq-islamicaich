import { Eye, EyeOff } from 'lucide-react';

/** Show/hide button for TextField endAdornment. 44px+ target. */
const PasswordToggle = ({ shown, onToggle }) => (
  <button
    type="button"
    onClick={onToggle}
    aria-label={shown ? 'Hide password' : 'Show password'}
    aria-pressed={shown}
    className="inline-flex min-h-11 min-w-11 cursor-pointer items-center justify-center rounded-xl text-text-muted hover:text-text focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-strong"
  >
    {shown ? <EyeOff aria-hidden="true" className="size-5" /> : <Eye aria-hidden="true" className="size-5" />}
  </button>
);

export default PasswordToggle;
