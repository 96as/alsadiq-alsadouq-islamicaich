import { cx } from './cx';

const VARIANTS = {
  success: 'bg-primary-soft text-primary-strong',
  info: 'bg-info-soft text-text',
  warning: 'bg-accent-soft text-text',
  danger: 'bg-danger-soft text-danger-strong',
  neutral: 'bg-surface-alt text-text',
};

/**
 * Status pill, soft fill with an AA text colour.
 * Props: variant 'success'|'info'|'warning'|'danger'|'neutral' (neutral), icon (node), className, children.
 */
export default function Pill({ variant = 'neutral', icon = null, className, children, ...rest }) {
  return (
    <span
      className={cx(
        'inline-flex items-center gap-1 rounded-full px-3 py-1 text-label',
        VARIANTS[variant],
        className,
      )}
      {...rest}
    >
      {icon}
      {children}
    </span>
  );
}
