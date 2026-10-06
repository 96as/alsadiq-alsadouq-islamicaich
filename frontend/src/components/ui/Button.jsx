import { Loader2 } from 'lucide-react';
import { cx, FOCUS_RING } from './cx';

const VARIANTS = {
  lg: {
    primary: 'bg-primary text-on-primary',
    secondary: 'bg-primary-soft text-text',
    danger: 'bg-danger-soft text-danger-strong',
    ghost: 'bg-transparent text-text border border-border',
  },
  // Small labels use the -strong fills so 14px text still passes AA.
  sm: {
    primary: 'bg-primary-strong text-on-strong',
    secondary: 'bg-primary-soft text-text',
    danger: 'bg-danger-soft text-danger-strong',
    ghost: 'bg-transparent text-text border border-border',
  },
};

const SIZES = {
  lg: 'min-h-target rounded-3xl px-5 text-heading',
  sm: 'min-h-11 rounded-3xl px-4 text-label',
};

/**
 * Child-sized button (mirrors mobile Button).
 * Props: variant 'primary'|'secondary'|'danger'|'ghost' (primary), size 'lg'|'sm' (lg),
 * loading (false), disabled (false), icon (node), type ('button'), className, children.
 * Note: lg primary relies on large text (text-heading) for AA contrast. size="sm" (44px) is for parent and
 * secondary contexts only; child UI uses lg (56px).
 */
export default function Button({
  variant = 'primary',
  size = 'lg',
  loading = false,
  disabled = false,
  icon = null,
  type = 'button',
  className,
  children,
  ...rest
}) {
  return (
    <button
      type={type}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={cx(
        'inline-flex cursor-pointer items-center justify-center gap-2 transition-transform',
        'motion-safe:active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-50',
        FOCUS_RING,
        SIZES[size],
        VARIANTS[size][variant],
        className,
      )}
      {...rest}
    >
      {loading ? (
        <>
          <Loader2 aria-hidden="true" className="size-5 motion-safe:animate-spin" />
          <span className="sr-only">Loading</span>
        </>
      ) : (
        icon
      )}
      {children}
    </button>
  );
}
