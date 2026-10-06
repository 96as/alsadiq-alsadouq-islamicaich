import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ROUTES } from '../routes';
import { isDemoSession } from '../services/demoService';

const ProtectedRoute = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-0 flex-1 items-center justify-center bg-slate-950">
        <span className="inline-flex h-8 w-8 rounded-full border-2 border-white/20 border-t-white/80 animate-spin" />
      </div>
    );
  }

  if (!user) {
    // A demo visitor whose time ran out goes back to "Try Al-Sadiq", not to a login form.
    return <Navigate to={isDemoSession() ? '/' : ROUTES.LOGIN} replace />;
  }

  return <Outlet />;
};

export default ProtectedRoute;
