import { forwardRef, useId } from 'react';
import { cx, FOCUS_RING } from './cx';

/**
 * Labelled input (mirrors mobile TextField).
 * Props: label, error (string), type ('text'), endAdornment (node, e.g. show/hide button),
 * id, className (on the input), ref -> input; other props go to the input.
 */
const TextField = forwardRef(function TextField(
  { label, error, type = 'text', endAdornment = null, id, className, 'aria-describedby': describedBy, ...rest },
  ref,
) {
  const autoId = useId();
  const inputId = id || autoId;
  const errorId = `${inputId}-error`;
  return (
    <div className="flex flex-col gap-2">
      {label ? (
        <label htmlFor={inputId} className="text-label text-text">
          {label}
        </label>
      ) : null}
      <div className="relative flex items-center">
        <input
          ref={ref}
          id={inputId}
          type={type}
          aria-invalid={error ? true : undefined}
          aria-describedby={[describedBy, error ? errorId : null].filter(Boolean).join(' ') || undefined}
          className={cx(
            'min-h-target w-full rounded-2xl border bg-surface px-4 text-body text-text',
            'placeholder:text-text-muted',
            FOCUS_RING,
            error ? 'border-danger-strong' : 'border-border',
            endAdornment ? 'pe-16' : null,
            className,
          )}
          {...rest}
        />
        {endAdornment ? <div className="absolute end-1 flex items-center">{endAdornment}</div> : null}
      </div>
      {error ? (
        <p id={errorId} className="text-label text-danger-strong">
          {error}
        </p>
      ) : null}
    </div>
  );
});

export default TextField;
