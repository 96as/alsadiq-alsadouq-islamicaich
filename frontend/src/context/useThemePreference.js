import { useContext } from 'react';
import { ThemePreferenceContext } from './themePreferenceContext';

export const useThemePreference = () => {
  const context = useContext(ThemePreferenceContext);
  if (!context) {
    throw new Error('useThemePreference must be used within ThemePreferenceProvider');
  }
  return context;
};
