import { cx, FOCUS_RING } from './cx';

/**
 * Filter buttons in one row, like tabs without panels. Each button has aria-pressed.
 * Props: label (names the group), options [{ value, label }], value, onChange(value), className.
 */
export default function SegmentedControl({ label, options, value, onChange, className }) {
  return (
    <div role="group" aria-label={label} className={cx('flex gap-1 rounded-3xl border border-border bg-surface p-1', className)}>
      {options.map((o) => {
        const on = o.value === value;
        return (
          <button
            key={o.value}
            type="button"
            aria-pressed={on}
            onClick={() => onChange(o.value)}
            className={cx(
              'min-h-target min-w-0 flex-1 cursor-pointer rounded-3xl px-2 text-center text-label',
              FOCUS_RING,
              on ? 'bg-primary-strong text-on-strong' : 'text-text',
            )}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}
