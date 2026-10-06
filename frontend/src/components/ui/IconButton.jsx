import { cx, FOCUS_RING } from './cx';

const VARIANTS = {
  primary: 'bg-primary text-on-primary',
  secondary: 'bg-primary-soft text-text',
  ghost: 'bg-transparent text-text border border-border',
};

/**
 * Round icon-only button, 56px target.
 * Props: label (required, becomes aria-label), icon (node), variant 'primary'|'secondary'|'ghost'
 * (secondary), type ('button'), className.
 */
export default function IconButton({
  label,
  icon,
  variant = 'secondary',
  type = 'button',
  className,
  ...rest
}) {
  if (import.meta.env.DEV && !label) {
    console.warn('IconButton: the "label" prop is required for accessibility.');
  }
  return (
    <button
      type={type}
      aria-label={label}
      title={label}
      className={cx(
        'inline-flex min-h-target min-w-target cursor-pointer items-center justify-center rounded-full',
        'transition-transform motion-safe:active:scale-95 disabled:cursor-not-allowed disabled:opacity-50',
        FOCUS_RING,
        VARIANTS[variant],
        className,
      )}
      {...rest}
    >
      {icon}
    </button>
  );
}
