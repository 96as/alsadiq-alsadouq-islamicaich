/* eslint-disable react-refresh/only-export-components */
import { NavLink } from 'react-router-dom';
import { COPY } from '../../demo/copy';
import { useDemoLang } from '../../../services/demoService';
import { useStrings } from '../../../i18n'; // i18n // avatar-integ
import { Bell, Home, HousePlus, Scroll, Medal, Settings, Sparkles } from 'lucide-react';

export const CHILD_NAV_TABS = [
  { path: '',         icon: Home,     label: 'Home',     key: 'home', end: true },
  { path: '/quests',  icon: Scroll,   label: 'Quests',   key: 'quests', end: false },
  { path: '/badges',  icon: Medal,    label: 'Badges', key: 'badges', end: false },
  { path: '/settings', icon: Settings, label: 'Settings', key: 'settings', end: false },
];

/** Parent app: no quests, second tab is Insights (stories & summaries preview). */
export const PARENT_NAV_TABS = [
  { path: '',          icon: HousePlus, label: 'Children', key: 'children', end: true },
  { path: '/insights', icon: Sparkles,  label: 'Insights', key: 'insights', end: false },
  { path: '/alerts',   icon: Bell,      label: 'Alerts',   key: 'alerts',   end: false },
  { path: '/settings', icon: Settings,  label: 'Settings', key: 'settings', end: false },
];

/**
 * BottomNav, four-tab bottom navigation (mirrors the mobile tabs).
 * Uses NavLink for URL-driven active state. Each tab is at least 56px tall.
 *
 * @param {string} basePath - route prefix ("/child" or "/parent")
 * @param {typeof CHILD_NAV_TABS} [tabs] - tab definitions (defaults to child quests flow)
 */
const BottomNav = ({ basePath, tabs = CHILD_NAV_TABS, floating = false }) => { // avatar-integ: floating = the card over the meadow (WebUI photo 2)
  const demoLang = useDemoLang(); // qa: follows toggles live
  // Both apps speak the app language (Arabic first).
  const strings = useStrings();
  const nav = tabs === CHILD_NAV_TABS ? COPY[demoLang].idle.nav : strings.nav.parent;
  return (
    <nav
      aria-label={strings.nav.aria}
      className={floating
        ? 'mx-auto max-w-md rounded-[28px] bg-surface/95 px-2 pt-2 shadow-[0_8px_28px_rgba(34,72,44,0.22)] backdrop-blur-md'
        : 'border-t border-border bg-surface px-2 pt-2'}
      style={{ paddingBottom: floating ? '0.5rem' : 'max(0.5rem, env(safe-area-inset-bottom))' }}
    >
      <ul className="mx-auto flex w-full max-w-2xl items-stretch justify-between gap-1">
        {tabs.map((tab) => {
          const TabIcon = tab.icon;
          const to = `${basePath}${tab.path}`;

          return (
            <li key={tab.path} className="min-w-0 flex-1">
              <NavLink
                to={to}
                end={tab.end}
                className={({ isActive }) =>
                  `mh-tab flex min-h-target flex-col items-center justify-center gap-1 rounded-2xl px-2 py-1 text-label no-underline transition-colors hover:no-underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-strong ${
                    isActive
                      ? `${floating ? '' : 'bg-primary-soft '}text-primary-strong hover:text-primary-strong`
                      : 'text-text-muted hover:text-text'
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <TabIcon
                      aria-hidden="true"
                      className="size-6"
                      strokeWidth={isActive ? 2.25 : 1.75}
                    />
                    <span className="max-w-full truncate">{(nav && nav[tab.key]) || tab.label}</span>
                  </>
                )}
              </NavLink>
            </li>
          );
        })}
      </ul>
    </nav>
  );
};

export default BottomNav;
