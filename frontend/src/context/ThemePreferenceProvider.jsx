import { useCallback, useEffect, useMemo, useState } from 'react';
import { useAuth } from './AuthContext';
import { ThemePreferenceContext } from './themePreferenceContext';

const DEFAULT_THEME_MODE = 'light';

function storageKeyForUser(user) {
  const id = user?.user_id || user?.id || user?.username;
  return id ? `alsadiq_theme_mode_${id}` : 'alsadiq_theme_mode_guest';
}

function normalizeThemeMode(value) {
  return value === 'dark' ? 'dark' : DEFAULT_THEME_MODE;
}

function readStoredThemeMode(key) {
  try {
    return normalizeThemeMode(window.localStorage.getItem(key));
  } catch {
    return DEFAULT_THEME_MODE;
  }
}

function persistThemeMode(key, mode) {
  try {
    window.localStorage.setItem(key, mode);
  } catch {
    // Browsers can block storage. The in-memory preference still applies.
  }
}

export const ThemePreferenceProvider = ({ children }) => {
  const { user } = useAuth();
  const storageKey = useMemo(() => storageKeyForUser(user), [user]);
  const [themeModes, setThemeModes] = useState({});
  const themeMode = useMemo(
    () => themeModes[storageKey] || readStoredThemeMode(storageKey),
    [storageKey, themeModes],
  );

  useEffect(() => {
    document.documentElement.dataset.colorMode = themeMode;
  }, [themeMode]);

  const setThemeMode = useCallback((nextMode) => {
    const normalized = normalizeThemeMode(nextMode);
    setThemeModes((prev) => ({ ...prev, [storageKey]: normalized }));
    persistThemeMode(storageKey, normalized);
  }, [storageKey]);

  const value = useMemo(() => ({
    themeMode,
    isDarkMode: themeMode === 'dark',
    setThemeMode,
  }), [setThemeMode, themeMode]);

  return (
    <ThemePreferenceContext.Provider value={value}>
      {children}
    </ThemePreferenceContext.Provider>
  );
};
