import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { LogIn, ShieldCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import useForm from '../hooks/useForm';
import AuthLayout from '../features/auth/components/AuthLayout';
import AuthField from '../features/auth/components/AuthField';
import AuthHeader from '../features/auth/components/AuthHeader';
import ButtonLink from '../features/auth/components/ButtonLink';
import PasswordToggle from '../features/auth/components/PasswordToggle';
import { Button, Card } from '../components/ui';
import { ROUTES } from '../routes';

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function validateLogin(values) {
  const next = {};
  const username = (values.username ?? '').trim();
  const password = values.password ?? '';

  if (!username) {
    next.username = 'Please enter your username or email.';
  } else if (username.includes('@') && !EMAIL_PATTERN.test(username)) {
    next.username = 'Please enter a valid email address.';
  }

  if (!password) {
    next.password = 'Please enter your password.';
  }

  return next;
}

const Login = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);

  const { values, errors, handleChange, handleSubmit, isSubmitting } = useForm({
    initialValues: { username: '', password: '' },
    validate: validateLogin,
    onSubmit: async (formValues) => {
      const user = await login(
        formValues.username.trim(),
        formValues.password,
      );
      navigate(user.is_parent ? ROUTES.PARENT_HOME : ROUTES.CHILD_HOME);
    },
  });

  return (
    <AuthLayout>
      <AuthHeader icon={ShieldCheck} title="Al-Sadiq Al-Sadouq AI" subtitle="Welcome back" />

      <Card as="section" padding="lg" className="mt-6">
        <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
          <AuthField
            id="login-username"
            name="username"
            label="Username or email"
            placeholder="Username or email"
            value={values.username}
            onChange={handleChange}
            error={errors.username}
            autoComplete="username"
            required
          />

          <AuthField
            id="login-password"
            name="password"
            type={showPassword ? 'text' : 'password'}
            label="Password"
            placeholder="Enter your password"
            value={values.password}
            onChange={handleChange}
            error={errors.password}
            autoComplete="current-password"
            endAdornment={
              <PasswordToggle shown={showPassword} onToggle={() => setShowPassword((prev) => !prev)} />
            }
            required
          />

          <Link
            to={ROUTES.FORGOT_PASSWORD}
            className="inline-flex min-h-11 items-center self-start text-label text-primary-strong underline"
          >
            Forgot password
          </Link>

          {errors.general && (
            <div className="rounded-2xl bg-danger-soft p-3" role="alert">
              <p className="text-label text-danger-strong">{errors.general}</p>
            </div>
          )}

          <Button
            type="submit"
            loading={isSubmitting}
            icon={isSubmitting ? null : <LogIn aria-hidden="true" className="size-5" />}
          >
            {isSubmitting ? 'Logging in...' : 'Login'}
          </Button>

          <ButtonLink to={ROUTES.REGISTER}>Create Parent Account</ButtonLink>
        </form>
      </Card>

      <p className="mt-6 text-center text-label text-text-muted">
        Child-safe access • Parent-controlled setup
      </p>
      {/* cards-spec (05) section 5: privacy link on the login page */}
      <p className="mt-1 text-center text-label">
        <Link
          to={`${ROUTES.PRIVACY}?lang=en`}
          data-testid="login-privacy-link"
          className="inline-flex min-h-11 items-center text-primary-strong underline"
        >
          Privacy
        </Link>
      </p>
    </AuthLayout>
  );
};

export default Login;
