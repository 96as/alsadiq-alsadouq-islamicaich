import { Outlet } from 'react-router-dom';
import ChildLayout from '../features/child/components/ChildLayout';
import { PARENT_NAV_TABS } from '../features/child/components/BottomNav';
import { ROUTES } from '../routes';

const ParentApp = () => {
  return (
    <ChildLayout basePath={ROUTES.PARENT_HOME} navTabs={PARENT_NAV_TABS}>
      <Outlet />
    </ChildLayout>
  );
};

export default ParentApp;
