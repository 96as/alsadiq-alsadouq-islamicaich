import { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import AuroraBackground from '../../../components/AuroraBackground';
import BottomNav, { CHILD_NAV_TABS } from './BottomNav';
import { NavVisibilityContext } from './navVisibility';
import DemoBanner from '../../demo/DemoBanner';
import ParentLangButton from '../../parent/components/ParentLangButton';
import { PARENT_SHELL } from '../../parent/parentShell';
import { useAuth } from '../../../context/AuthContext';
import { dirOf, normalizeLang, useDocumentLang } from '../../../i18n'; // i18n // avatar-integ
import { isDemoSession, readDemoLang, writeDemoLang } from '../../../services/demoService';

/**
 * ChildLayout — full-screen layout wrapper for child and parent apps.
 *
 * Provides:
 * - Warm token gradient background (cream to green; parent palette via data-theme)
 * - Sticky bottom navigation (NavLink-driven)
 * - A content area for nested routes
 *
 * @param {React.ReactNode} children  - page content (typically <Outlet />)
 * @param {string}          basePath  - route prefix for BottomNav ("/child" or "/parent")
 * @param {typeof CHILD_NAV_TABS} [navTabs] - optional tab config (parent vs child)
 * @param {boolean}         [hideNav] - explicit prop to hide nav (e.g. parent shell)
 */
const ChildLayout = ({ children, basePath = '/child', navTabs, hideNav = false }) => {
  const isParentShell = basePath === '/parent';
  const lang = useDocumentLang(); // i18n: <html lang dir> follows the language
  const { user } = useAuth();
  const profileLang = user?.is_child && user?.profile?.language_preference
    ? normalizeLang(user.profile.language_preference)
    : null;
  // i18n: a child's own account speaks the language on the profile (a demo follows the landing page toggle).
  useEffect(() => {
    if (!profileLang || isDemoSession() || readDemoLang() === profileLang) return;
    writeDemoLang(profileLang);
  }, [profileLang]);
  const location = useLocation();
  const isImmersive = location.pathname === basePath || location.pathname === `${basePath}/`;
  const [roomBg, setRoomBg] = useState(() => (
    basePath === '/parent'
      ? window.localStorage.getItem('parent_room_snapshot') || ''
      : ''
  ));
  const [hidden, setHidden] = useState(false);
  const floatNav = isImmersive && !isParentShell; // avatar-integ

  useEffect(() => {
    if (!isParentShell) return;
    const onUpdate = () => {
      const next = window.localStorage.getItem('parent_room_snapshot') || '';
      setRoomBg(next);
    };
    window.addEventListener('parent-room-snapshot-updated', onUpdate);
    return () => window.removeEventListener('parent-room-snapshot-updated', onUpdate);
  }, [isParentShell]);

  return (
    <NavVisibilityContext.Provider value={{ hidden, setHidden }}>
      <div
        className="relative flex h-dvh max-h-dvh min-h-0 flex-col overflow-clip bg-bg font-sans text-text antialiased"
        dir={dirOf(lang)}
        lang={lang}
        data-theme={isParentShell ? 'parent' : 'child'}
        data-view={isImmersive ? 'immersive' : 'standard'}
      >
        <AuroraBackground />
        {isImmersive && isParentShell && roomBg ? (
          <div
            className="pointer-events-none absolute inset-0 z-0 scale-105 bg-cover bg-center opacity-20 blur-[10px]"
            style={{ backgroundImage: `url(${roomBg})` }}
            aria-hidden="true"
          />
        ) : null}

        {/* Demo bar: renders nothing unless this is a one-click demo session. */}
        <DemoBanner />

        <div className="relative z-10 flex min-h-0 flex-1 flex-col">
          {/* In flow (not floating) so it never covers a page title or a header button; the DemoBanner stays above it. */}
          {isParentShell ? (
            <div className={`flex shrink-0 justify-end pt-2 ${PARENT_SHELL}`}>
              <ParentLangButton />
            </div>
          ) : null}
          {children}
        </div>

        {/* avatar-integ: on the child's Home the nav floats over the meadow, so the stage never resizes when it hides. */}
        {!hideNav && !hidden && (floatNav ? (
          <div className="absolute inset-x-0 bottom-0 z-30 px-3" style={{ paddingBottom: 'max(0.75rem, env(safe-area-inset-bottom))' }}>
            <BottomNav basePath={basePath} tabs={navTabs} floating />
          </div>
        ) : (
          <div className="relative z-30">
            <BottomNav basePath={basePath} tabs={navTabs} />
          </div>
        ))}
      </div>
    </NavVisibilityContext.Provider>
  );
};

export default ChildLayout;
