import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ROUTES } from '../routes';

const RoleGuard = ({ allowedRole }) => {
  const { user } = useAuth();

  const redirectPath = user?.is_parent ? ROUTES.PARENT_HOME : ROUTES.CHILD_HOME;

  const hasAccess =
    (allowedRole === 'parent' && user?.is_parent) ||
    (allowedRole === 'child' && user?.is_child);

  if (!hasAccess) {
    return <Navigate to={redirectPath} replace />;
  }

  return <Outlet />;
};

export default RoleGuard;
