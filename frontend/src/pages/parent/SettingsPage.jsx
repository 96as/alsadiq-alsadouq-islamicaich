import { useCallback, useState } from 'react';
import { LogOut, Mail, User, Users, Plus, ChevronRight } from 'lucide-react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { ROUTES } from '../../routes';
import { PARENT_SHELL } from '../../features/parent/parentShell';
import AddChildModal from '../../features/parent/components/AddChildModal';
import { useThemePreference } from '../../context/useThemePreference';
import { Button, Card } from '../../components/ui';
import { useLang, useStrings } from '../../i18n'; // i18n
import { writeDemoLang } from '../../services/demoService';
import { FOCUS_RING } from '../../components/ui/cx';
import { PRIVACY_LINK, REGISTRATION_STRINGS } from '../../features/child/ai/aiStrings'; // cards-spec (05) judge r2

const ToggleSwitch = ({ id, checked, onChange, label, description, disabled = false }) => (
  <div className="flex min-h-target items-center justify-between gap-4 py-3">
    <div className="min-w-0">
      <label htmlFor={id} className={`text-body text-text ${disabled ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'}`}>{label}</label>
      {description && <p className="mt-0.5 text-label text-text-muted">{description}</p>}
    </div>
    <button
      id={id}
      type="button"
      role="switch"
      aria-checked={checked}
      aria-disabled={disabled}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={`relative h-8 w-14 shrink-0 cursor-pointer rounded-full border border-border motion-safe:transition-colors motion-safe:duration-200 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-strong disabled:cursor-not-allowed disabled:opacity-50 ${
        checked ? 'bg-primary-strong' : 'bg-surface-alt'
      }`}
    >
      <span
        className={`absolute start-0.5 top-0.5 size-6 rounded-full bg-surface shadow motion-safe:transition-transform motion-safe:duration-200 ${
          checked ? 'translate-x-6 rtl:-translate-x-6' : 'translate-x-0'
        }`}
      />
    </button>
  </div>
);

const SectionCard = ({ children, className = '' }) => (
  <Card className={`divide-y divide-border overflow-hidden p-0! ${className}`}>
    {children}
  </Card>
);

const SectionHeading = ({ id, children }) => (
  <h2 id={id} className="mb-3 px-1 text-heading text-text">
    {children}
  </h2>
);

const ParentSettingsPage = () => {
  const { user, logout, refreshProfile } = useAuth();
  const strings = useStrings();
  const s = strings.parent.settings;
  const d = strings.parent.display;
  const lang = useLang();
  const privacyLang = lang === 'ar' ? 'ar' : 'en'; // cards-spec (05) judge r2: the row was English-only in Arabic
  const { isDarkMode, setThemeMode } = useThemePreference();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const childIdParam = searchParams.get('child');
  const managedChild =
    childIdParam && user?.children?.length
      ? user.children.find((c) => String(c.id) === String(childIdParam))
      : null;

  const [showAddChild, setShowAddChild] = useState(false);
  const closeAddChild = useCallback(() => setShowAddChild(false), []);
  const handleToggleTheme = (v) => {
    setThemeMode(v ? 'dark' : 'light');
  };

  const handleLogout = async () => {
    await logout();
    navigate(ROUTES.LOGIN);
  };

  const displayName =
    [user?.first_name, user?.last_name].filter(Boolean).join(' ') || user?.username || s.parentDefault;

  return (
    <div className={`flex-1 min-h-0 overflow-y-auto pt-4 pb-8 ${PARENT_SHELL}`}>
      <div className="mx-auto w-full max-w-md lg:mx-0 lg:max-w-none">

        <header className="mb-6">
          <h1 className="text-title text-text">{s.title}</h1>
          {managedChild && (
            <p className="mt-1 text-body text-text-muted">
              {s.viewingFor}{' '}
              <bdi dir="auto" className="text-text">{managedChild.nickname}</bdi>
              {managedChild.username && (
                <bdi dir="ltr"> · @{managedChild.username}</bdi>
              )}
            </p>
          )}
        </header>

        {/* Display section: language and theme */}
        <section className="mb-6" aria-labelledby="display-heading">
          <SectionHeading id="display-heading">{d.title}</SectionHeading>
          <SectionCard>
            <div className="px-4 py-3">
              <p className="mb-2 text-body text-text">{d.language}</p>
              <div role="group" aria-label={d.languageGroup} className="grid grid-cols-2 gap-1 rounded-2xl bg-surface-alt p-1">
                {[['ar', d.arabic], ['en', d.english]].map(([code, name]) => (
                  <button
                    key={code}
                    type="button"
                    lang={code}
                    aria-pressed={lang === code}
                    onClick={() => writeDemoLang(code)}
                    className={`min-h-11 cursor-pointer rounded-xl px-3 text-body ${FOCUS_RING} ${
                      lang === code ? 'bg-primary-strong text-on-strong' : 'text-text hover:bg-surface'
                    }`}
                  >
                    {name}
                  </button>
                ))}
              </div>
            </div>
            <div className="px-4">
              <ToggleSwitch
                id="parent-dark-mode"
                checked={isDarkMode}
                onChange={handleToggleTheme}
                label={s.darkMode}
                description={s.darkModeHint}
              />
            </div>
          </SectionCard>
        </section>

        {/* Account section */}
        <section className="mb-6" aria-labelledby="account-heading">
          <SectionHeading id="account-heading">{s.account}</SectionHeading>
          <SectionCard>
            <div className="flex min-h-target items-center gap-3 px-4 py-3">
              <User aria-hidden="true" className="size-5 shrink-0 text-text-muted" />
              <div className="min-w-0">
                <p className="text-label text-text-muted">{s.name}</p>
                <p dir="auto" className="truncate text-body text-text">{displayName}</p>
              </div>
            </div>
            <div className="flex min-h-target items-center gap-3 px-4 py-3">
              <Mail aria-hidden="true" className="size-5 shrink-0 text-text-muted" />
              <div className="min-w-0">
                <p className="text-label text-text-muted">{s.email}</p>
                <p dir="ltr" className="truncate text-body text-text text-start">{user?.email ?? user?.username}</p>
              </div>
            </div>
          </SectionCard>
        </section>

        {/* My Children section */}
        <section className="mb-6" aria-labelledby="children-heading">
          <SectionHeading id="children-heading">{s.myChildren}</SectionHeading>
          <SectionCard>
            {user?.children?.length > 0 ? (
              user.children.map((child) => (
                <div key={child.id} className="flex min-h-target items-center gap-3 px-4 py-3">
                  <Users aria-hidden="true" className="size-5 shrink-0 text-text-muted" />
                  <div className="min-w-0 flex-1">
                    <p dir="auto" className="truncate text-body text-text">
                      {child.nickname || child.username}
                    </p>
                    {child.username && child.nickname && (
                      <p dir="ltr" className="truncate text-label text-text-muted text-start">@{child.username}</p>
                    )}
                  </div>
                  <ChevronRight aria-hidden="true" className="size-5 shrink-0 text-text-muted rtl:rotate-180" />
                </div>
              ))
            ) : (
              <div className="px-4 py-4 text-center">
                <p className="text-body text-text-muted">{s.noChildren}</p>
              </div>
            )}
            <button
              type="button"
              onClick={() => setShowAddChild(true)}
              className="flex min-h-target w-full cursor-pointer items-center gap-3 px-4 py-3 text-start hover:bg-surface-alt focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-primary-strong"
            >
              <Plus aria-hidden="true" className="size-5 shrink-0 text-primary-strong" />
              <span className="text-body text-primary-strong">{s.addChild}</span>
            </button>
          </SectionCard>
        </section>

        {/* Notifications section */}
        <section className="mb-8" aria-labelledby="notif-heading">
          <SectionHeading id="notif-heading">{s.notifications}</SectionHeading>
          <SectionCard>
            <div className="px-4">
              <ToggleSwitch
                id="notif-safety"
                checked={false}
                onChange={() => {}}
                label={s.safetyAlerts}
                description={s.comingSoon}
                disabled
              />
            </div>
            <div className="px-4">
              <ToggleSwitch
                id="notif-weekly"
                checked={false}
                onChange={() => {}}
                label={s.weeklySummary}
                description={s.comingSoon}
                disabled
              />
            </div>
          </SectionCard>
          <p className="mt-2 px-1 text-label text-text-muted">
            {s.notificationsNote}
          </p>
        </section>

        {/* cards-spec (05) section 5: privacy row */}
        <section className="mb-8" aria-labelledby="privacy-heading">
          <SectionHeading id="privacy-heading">{PRIVACY_LINK[privacyLang]}</SectionHeading>
          <SectionCard>
            <Link
              to={`${ROUTES.PRIVACY}?lang=${privacyLang}`}
              data-testid="settings-privacy-link"
              className="flex min-h-target w-full items-center gap-3 px-4 py-3 text-body text-primary-strong hover:bg-surface-alt focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-primary-strong"
            >
              <span className="flex-1 underline">{REGISTRATION_STRINGS[privacyLang].privacyPolicy}</span>
              <ChevronRight aria-hidden="true" className="size-5 shrink-0 rtl:rotate-180" />
            </Link>
          </SectionCard>
        </section>

        {/* Logout */}
        <Button
          variant="danger"
          className="w-full"
          onClick={handleLogout}
          icon={<LogOut aria-hidden="true" className="size-5" />}
        >
          {s.logout}
        </Button>
      </div>

      <AddChildModal
        open={showAddChild}
        onClose={closeAddChild}
        onCreated={() => refreshProfile()}
      />
    </div>
  );
};

export default ParentSettingsPage;
