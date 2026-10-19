import { TextField } from '../../../components/ui';

/**
 * AuthField: TextField plus an optional hint line, wired to aria-describedby.
 * Props: id (required), label, hint, error, required (adds "(optional)" when false), plus input props.
 */
const AuthField = ({ id, label, hint, error, required = false, ...rest }) => {
  const hintId = hint && !error ? `${id}-hint` : undefined;
  return (
    <div className="flex flex-col gap-2">
      <TextField
        id={id}
        label={required ? label : `${label} (optional)`}
        error={error}
        aria-describedby={hintId}
        {...rest}
      />
      {hintId ? (
        <p id={hintId} className="text-label text-text-muted">
          {hint}
        </p>
      ) : null}
    </div>
  );
};

export default AuthField;
