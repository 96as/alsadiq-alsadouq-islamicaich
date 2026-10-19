import { Outlet } from 'react-router-dom';
import ChildLayout from '../features/child/components/ChildLayout';
import { ROUTES } from '../routes';

const ChildApp = () => {
  return (
    <ChildLayout basePath={ROUTES.CHILD_HOME}>
      <Outlet />
    </ChildLayout>
  );
};

export default ChildApp;
