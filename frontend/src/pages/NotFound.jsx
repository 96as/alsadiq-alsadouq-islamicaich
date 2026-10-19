import { ROUTES } from '../routes';
import AuthLayout from '../features/auth/components/AuthLayout';
import ButtonLink from '../features/auth/components/ButtonLink';

const NotFound = () => {
  return (
    <AuthLayout>
      <div className="flex flex-col items-center gap-3 text-center">
        <p className="text-display text-primary-strong" aria-hidden="true">404</p>
        <h1 className="text-title text-text">Page not found</h1>
        <p className="text-body text-text-muted">The page you are looking for does not exist.</p>
        <ButtonLink variant="primary" to={ROUTES.LOGIN} className="mt-3 max-w-xs">
          Go to Login
        </ButtonLink>
      </div>
    </AuthLayout>
  );
};

export default NotFound;
