import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { KeyRound, CheckCircle } from 'lucide-react';
import useForm from '../hooks/useForm';
import AuthLayout from '../features/auth/components/AuthLayout';
import AuthField from '../features/auth/components/AuthField';
import AuthHeader from '../features/auth/components/AuthHeader';
import ButtonLink from '../features/auth/components/ButtonLink';
import PasswordToggle from '../features/auth/components/PasswordToggle';
import { Button, Card } from '../components/ui';
import { confirmPasswordReset } from '../services/authService';
import { ROUTES } from '../routes';
import { validateStrongPassword } from '../utils/validators';

function validateResetPassword(values) {
  const next = {};
  const password = values.new_password ?? '';
  const confirm = values.confirm_password ?? '';

  const pwError = validateStrongPassword(password);
  if (pwError) {
    next.new_password = pwError;
  }

  if (!confirm) {
    next.confirm_password = 'Please confirm your new password.';
  } else if (password && confirm !== password) {
    next.confirm_password = 'Passwords do not match.';
  }

  return next;
}

const ResetPassword = () => {
  const { uid, token } = useParams();
  const [showPassword, setShowPassword] = useState(false);
  const [success, setSuccess] = useState(false);

  const { values, errors, handleChange, handleSubmit, isSubmitting } = useForm({
    initialValues: { new_password: '', confirm_password: '' },
    validate: validateResetPassword,
    onSubmit: async (formValues) => {
      await confirmPasswordReset(uid, token, formValues.new_password);
      setSuccess(true);
    },
  });

  const passwordToggle = (
    <PasswordToggle shown={showPassword} onToggle={() => setShowPassword((prev) => !prev)} />
  );

  return (
    <AuthLayout>
      <AuthHeader
        icon={KeyRound}
        title={success ? 'Password Reset' : 'New Password'}
        subtitle={success ? "You're all set" : 'Choose a strong new password'}
      />

      <Card as="section" padding="lg" className="mt-6">
        {success ? (
          <div className="flex flex-col items-center gap-4 text-center" role="status">
            <CheckCircle aria-hidden="true" className="size-10 text-primary-strong" />
            <p className="text-heading text-text">Password updated!</p>
            <p className="max-w-xs text-body text-text-muted">
              Your password has been reset successfully. You can now log in with your new password.
            </p>
            <ButtonLink variant="primary" to={ROUTES.LOGIN} className="max-w-xs">
              Go to Login
            </ButtonLink>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
            <p className="text-center text-body text-text-muted">
              Enter and confirm your new password below.
            </p>

            <AuthField
              id="reset-new-password"
              name="new_password"
              type={showPassword ? 'text' : 'password'}
              label="New password"
              placeholder="Enter your new password"
              value={values.new_password}
              onChange={handleChange}
              error={errors.new_password}
              autoComplete="new-password"
              endAdornment={passwordToggle}
              hint="Min 8 chars, 1 upper, 1 lower, 1 number, 1 symbol"
              required
            />

            <AuthField
              id="reset-confirm-password"
              name="confirm_password"
              type={showPassword ? 'text' : 'password'}
              label="Confirm new password"
              placeholder="Confirm your new password"
              value={values.confirm_password}
              onChange={handleChange}
              error={errors.confirm_password}
              autoComplete="new-password"
              required
            />

            {errors.general && (
              <div className="rounded-2xl bg-danger-soft p-3" role="alert">
                <p className="text-label text-danger-strong">{errors.general}</p>
              </div>
            )}

            <Button
              type="submit"
              loading={isSubmitting}
              icon={isSubmitting ? null : <KeyRound aria-hidden="true" className="size-5" />}
            >
              {isSubmitting ? 'Resetting...' : 'Reset Password'}
            </Button>

            <ButtonLink to={ROUTES.LOGIN}>Back to Login</ButtonLink>
          </form>
        )}
      </Card>

      <p className="mt-6 text-center text-label text-text-muted">
        Child-safe access • Parent-controlled setup
      </p>
    </AuthLayout>
  );
};

export default ResetPassword;
