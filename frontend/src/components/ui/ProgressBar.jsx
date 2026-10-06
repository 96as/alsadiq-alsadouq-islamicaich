import { cx } from './cx';

/**
 * Accessible progress bar (0-100).
 * A11y: the fill is primary-strong because primary on primary-soft is only 2.63:1 (needs 3:1, WCAG 1.4.11).
 * Props: progress (0), label (aria-label, 'Progress'), className.
 */
export default function ProgressBar({ progress = 0, label = 'Progress', className }) {
  const value = Number.isFinite(progress) ? Math.max(0, Math.min(100, progress)) : 0;
  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={value}
      className={cx('h-2.5 w-full overflow-hidden rounded-full bg-primary-soft', className)}
    >
      <div
        className="h-full rounded-full bg-primary-strong motion-safe:transition-[width] motion-safe:duration-500"
        style={{ width: `${value}%` }}
      />
    </div>
  );
}
