import { useEffect, useState } from 'react';
import { Mail, KeyRound, ArrowLeft, CheckCircle, RefreshCw } from 'lucide-react';
import useForm from '../hooks/useForm';
import AuthLayout from '../features/auth/components/AuthLayout';
import AuthField from '../features/auth/components/AuthField';
import AuthHeader from '../features/auth/components/AuthHeader';
import ButtonLink from '../features/auth/components/ButtonLink';
import { Button, Card } from '../components/ui';
import { requestPasswordReset } from '../services/authService';
import { ROUTES } from '../routes';

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function validateForgotPassword(values) {
  const next = {};
  const email = (values.email ?? '').trim();
  if (!email) {
    next.email = 'Please enter your email address.';
  } else if (!EMAIL_PATTERN.test(email)) {
    next.email = 'Please enter a valid email address.';
  }
  return next;
}

const ForgotPassword = () => {
  const [sent, setSent] = useState(false);
  const [countdown, setCountdown] = useState(0);

  useEffect(() => {
    let timer;
    if (countdown > 0) {
      timer = setTimeout(() => setCountdown((c) => c - 1), 1000);
    }
    return () => clearTimeout(timer);
  }, [countdown]);

  const { values, errors, handleChange, handleSubmit, isSubmitting } = useForm({
    initialValues: { email: '' },
    validate: validateForgotPassword,
    onSubmit: async (formValues) => {
      await requestPasswordReset(formValues.email.trim());
      setSent(true);
      setCountdown(60);
    },
  });

  const handleResend = async () => {
    if (countdown > 0) return;
    try {
      await requestPasswordReset(values.email.trim());
      setCountdown(60);
    } catch (err) {
      console.error('Failed to resend reset link', err);
    }
  };

  return (
    <AuthLayout>
      <AuthHeader
        icon={KeyRound}
        title="Forgot Password"
        subtitle={sent ? 'Check your inbox' : 'Reset your account password'}
      />

      <Card as="section" padding="lg" className="mt-6">
        {sent ? (
          <div className="flex flex-col items-center gap-4 text-center" role="status">
            <CheckCircle aria-hidden="true" className="size-10 text-primary-strong" />
            <p className="text-heading text-text">Reset link sent!</p>
            <p className="max-w-xs text-body text-text-muted">
              If an account with that email exists, you&apos;ll receive a password reset link shortly.
              Check your inbox (and spam folder).
            </p>
            <div className="flex w-full max-w-xs flex-col gap-3">
              <Button
                variant="secondary"
                onClick={handleResend}
                disabled={countdown > 0}
                icon={<RefreshCw aria-hidden="true" className="size-5" />}
              >
                {countdown > 0 ? `Resend available in ${countdown}s` : 'Resend link'}
              </Button>
              <ButtonLink variant="primary" to={ROUTES.LOGIN}>
                <ArrowLeft aria-hidden="true" className="size-5 rtl:rotate-180" />
                Back to Login
              </ButtonLink>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
            <p className="text-center text-body text-text-muted">
              Enter the email address linked to your parent account and we&apos;ll send you a reset link.
            </p>

            <AuthField
              id="forgot-email"
              name="email"
              type="email"
              label="Email address"
              placeholder="you@example.com"
              value={values.email}
              onChange={handleChange}
              error={errors.email}
              autoComplete="email"
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
              icon={isSubmitting ? null : <Mail aria-hidden="true" className="size-5" />}
            >
              {isSubmitting ? 'Sending...' : 'Send Reset Link'}
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

export default ForgotPassword;
