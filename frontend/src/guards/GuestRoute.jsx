import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ROUTES } from '../routes';

/**
 * GuestRoute — inverse of ProtectedRoute.
 *
 * Redirects already-authenticated users to their role home.
 * Used to wrap /login and /register so logged-in users
 * can't accidentally visit public auth pages.
 */
const GuestRoute = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-0 flex-1 items-center justify-center bg-slate-950">
        <span className="inline-flex h-8 w-8 rounded-full border-2 border-white/20 border-t-white/80 animate-spin" />
      </div>
    );
  }

  if (user) {
    const home = user.is_parent ? ROUTES.PARENT_HOME : ROUTES.CHILD_HOME;
    return <Navigate to={home} replace />;
  }

  return <Outlet />;
};

export default GuestRoute;
