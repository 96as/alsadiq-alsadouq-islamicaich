import { createElement, useCallback, useEffect, useState } from 'react';
import { Check, KeyRound, LogOut } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { Button, Card } from '../../components/ui';
import { FOCUS_RING } from '../../components/ui/cx';
import { useAuth } from '../../context/AuthContext';
import { ROUTES } from '../../routes';
import { patchChildProfile } from '../../services/authService';
import ChangePasswordModal from '../../features/child/settings/ChangePasswordModal';
import { PROFILE_ICON_OPTIONS } from '../../features/child/settings/profileIconOptions';
import { useThemePreference } from '../../context/useThemePreference';
import { PRIVACY_LINK } from '../../features/child/ai/aiStrings'; // cards-spec (05)
import { writeDemoLang } from '../../services/demoService';
import { useLang, useStrings } from '../../i18n'; // i18n // cards-spec (05)

const SHELL =
  'w-full max-w-3xl mx-auto lg:max-w-none lg:mx-0 px-4 sm:px-6 pt-4 pb-20 flex flex-col min-h-0 flex-1 overflow-y-auto';

const LANG_VALUES = ['ar', 'en'];

const ToggleSwitch = ({ id, checked, onChange, label, description }) => (
  <div className="flex min-h-target items-center justify-between gap-4">
    <div className="min-w-0">
      <label htmlFor={id} className="cursor-pointer text-heading text-text">{label}</label>
      {description ? <p className="mt-1 text-label text-text-muted">{description}</p> : null}
    </div>
    <button
      id={id}
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className={`grid min-h-target min-w-target shrink-0 cursor-pointer place-items-center rounded-full ${FOCUS_RING}`}
    >
      <span
        className={`relative block h-8 w-14 rounded-full transition-colors duration-200 ${
          checked ? 'bg-primary-strong' : 'bg-text-muted'
        }`}
        aria-hidden="true"
      >
        <span
          className={`absolute start-1 top-1 block size-6 rounded-full bg-surface shadow-[0_2px_6px_var(--color-shadow)] transition-transform duration-200 ${
            checked ? 'translate-x-6 rtl:-translate-x-6' : 'translate-x-0'
          }`}
        />
      </span>
    </button>
  </div>
);

const SectionTitle = ({ id, children }) => (
  <h2 id={id} className="text-title text-text">{children}</h2>
);

const SettingsPage = () => {
  const { user, logout, refreshProfile } = useAuth();
  const { isDarkMode, setThemeMode } = useThemePreference();
  const navigate = useNavigate();
  const lang = useLang();
  const strings = useStrings();
  const s = strings.settings;

  const profile = user?.profile;
  const isChild = user?.is_child;

  const [passwordOpen, setPasswordOpen] = useState(false);
  const [saveMessage, setSaveMessage] = useState({ type: '', text: '' });

  useEffect(() => {
    if (saveMessage.type !== 'success') return undefined;
    const timer = window.setTimeout(() => {
      setSaveMessage((prev) => (prev.type === 'success' ? { type: '', text: '' } : prev));
    }, 2500);
    return () => window.clearTimeout(timer);
  }, [saveMessage]);

  // The child picks one language for the app and for Sadiq: the UI follows the same switch.
  const languagePreference = lang;
  const profileIcon = profile?.profile_icon ?? 'sparkles';
  const previewOption = PROFILE_ICON_OPTIONS.find((option) => option.value === profileIcon) || PROFILE_ICON_OPTIONS[0];
  const signedInName = profile?.nickname?.trim() || user?.username || s.yourAccount;

  const updateChildPreference = useCallback(async (payload) => {
    if (!isChild) return;
    setSaveMessage({ type: '', text: '' });
    try {
      await patchChildProfile(payload);
      await refreshProfile();
      setSaveMessage({ type: 'success', text: s.saved });
    } catch {
      setSaveMessage({ type: 'error', text: s.saveFailed });
    }
  }, [isChild, refreshProfile, s]);

  const handleLanguageChange = (nextLanguage) => {
    writeDemoLang(nextLanguage); // i18n: the page flips at once; the profile save follows
    updateChildPreference({ language_preference: nextLanguage });
  };

  const handleProfileIconChange = (nextIcon) => {
    updateChildPreference({ profile_icon: nextIcon });
  };

  const handleLogout = async () => {
    await logout();
    navigate(ROUTES.LOGIN);
  };
  const handleToggleTheme = (v) => {
    setThemeMode(v ? 'dark' : 'light');
  };

  if (!isChild) {
    return (
      <div className={`${SHELL} items-center justify-center text-center`}>
        <p className="text-body text-text-muted">{s.childOnly}</p>
        <Button
          variant="secondary"
          className="mt-6"
          onClick={handleLogout}
          icon={<LogOut className="size-5" aria-hidden="true" />}
        >
          {s.logout}
        </Button>
      </div>
    );
  }

  return (
    <div className={SHELL}>
      <header className="mb-6 shrink-0">
        <h1 className="text-display text-text">{s.title}</h1>
        <p className="mt-1 text-body text-text-muted">
          {s.signedInAs} <bdi className="text-text">{signedInName}</bdi>
        </p>
      </header>

      <section className="space-y-3" aria-labelledby="profile-heading">
        <SectionTitle id="profile-heading">{s.avatarTitle}</SectionTitle>

        <Card>
          <div className="mb-4 flex items-center gap-4">
            <div
              className="flex size-16 shrink-0 items-center justify-center rounded-full bg-accent-soft text-text"
              aria-hidden="true"
            >
              {createElement(previewOption.Icon, { className: 'size-8', strokeWidth: 1.75 })}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-label text-text-muted">{s.nickname}</p>
              <p className="truncate text-heading text-text"><bdi>{signedInName}</bdi></p>{/* cards-spec (05): isolated, but aligned under its label */}
            </div>
          </div>

          <p className="mb-2 text-label text-text-muted">{s.chooseIcon}</p>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3" role="radiogroup" aria-label={s.iconGroup}>
            {PROFILE_ICON_OPTIONS.map(({ value, Icon: ProfileIcon }) => {
              const selected = profileIcon === value;
              return (
                <div key={value}>
                  <button
                    type="button"
                    role="radio"
                    aria-checked={selected}
                    onClick={() => handleProfileIconChange(value)}
                    className={`flex min-h-target w-full cursor-pointer items-center gap-2 rounded-2xl border-2 px-3 text-label text-text transition-colors ${FOCUS_RING} ${
                      selected
                        ? 'border-primary-strong bg-primary-soft'
                        : 'border-border bg-surface hover:bg-surface-alt'
                    }`}
                  >
                    {createElement(ProfileIcon, { className: 'size-6 shrink-0', strokeWidth: 1.75, 'aria-hidden': true })}
                    <span className="truncate">{s.icons[value]}</span>
                    {selected ? <Check className="ms-auto size-5 shrink-0 text-primary-strong" strokeWidth={3} aria-hidden="true" /> : null}
                  </button>
                </div>
              );
            })}
          </div>
        </Card>
      </section>

      <section className="mt-8 space-y-3" aria-labelledby="prefs-heading">
        <SectionTitle id="prefs-heading">{s.prefsTitle}</SectionTitle>

        <Card>
          <label htmlFor="child-language" className="mb-2 block text-label text-text">
            {s.languageLabel}
          </label>
          <select
            id="child-language"
            value={languagePreference}
            onChange={(e) => handleLanguageChange(e.target.value)}
            className={`min-h-target w-full rounded-2xl border border-border bg-surface px-4 text-body text-text [[data-color-mode=dark]_&]:[color-scheme:dark] ${FOCUS_RING}`}
          >
            {LANG_VALUES.map((value) => (
              <option key={value} value={value}>
                {s.languages[value]}
              </option>
            ))}
          </select>
          <p className="mt-2 text-label text-text-muted">
            {s.languageNote}
          </p>
        </Card>
      </section>

      <section className="mt-8 space-y-3" aria-labelledby="appearance-heading">
        <SectionTitle id="appearance-heading">{s.appearanceTitle}</SectionTitle>
        <Card>
          <ToggleSwitch
            id="child-dark-mode"
            checked={isDarkMode}
            onChange={handleToggleTheme}
            label={s.darkMode}
            description={s.darkModeNote}
          />
        </Card>
      </section>

      {saveMessage.text ? (
        <div className="mt-4">
          {saveMessage.type === 'success' ? (
            <p className="rounded-2xl bg-primary-soft px-4 py-3 text-label text-primary-strong" role="status">
              {saveMessage.text}
            </p>
          ) : null}
          {saveMessage.type === 'error' ? (
            <p className="rounded-2xl bg-danger-soft px-4 py-3 text-label text-danger-strong" role="alert">
              {saveMessage.text}
            </p>
          ) : null}
        </div>
      ) : null}

      <section className="mt-8 space-y-3" aria-labelledby="security-heading">
        <SectionTitle id="security-heading">{s.securityTitle}</SectionTitle>
        <Card>
          <p className="text-heading text-text">{s.passwordTitle}</p>
          <p className="mt-1 text-body text-text-muted">
            {s.passwordNote}
          </p>
          <Button
            variant="secondary"
            className="mt-4"
            onClick={() => setPasswordOpen(true)}
            icon={<KeyRound className="size-5" aria-hidden="true" />}
          >
            {s.changePassword}
          </Button>
        </Card>
      </section>

      {/* cards-spec (05) section 5: privacy row */}
      <section className="mt-8 space-y-3" aria-labelledby="privacy-heading">
        <SectionTitle id="privacy-heading">{PRIVACY_LINK[languagePreference]}</SectionTitle>
        <Card>
          <Link
            to={`${ROUTES.PRIVACY}?lang=${languagePreference}`}
            data-testid="settings-privacy-link"
            className={`inline-flex min-h-target items-center text-heading text-primary-strong underline ${FOCUS_RING}`}
          >
            {languagePreference === 'ar' ? 'سياسة الخصوصية' : 'Privacy policy'}
          </Link>
        </Card>
      </section>

      <section className="mt-8 border-t border-border pt-6">
        <Button
          variant="danger"
          className="w-full"
          onClick={handleLogout}
          icon={<LogOut className="size-5" aria-hidden="true" />}
        >
          {s.logout}
        </Button>
      </section>

      <ChangePasswordModal
        open={passwordOpen}
        onClose={() => setPasswordOpen(false)}
      />
    </div>
  );
};

export default SettingsPage;
