/** Light / dark / system theme with the user's choice saved on the device. */
import { createContext, type PropsWithChildren, useContext, useEffect, useState } from 'react';
import { useColorScheme } from 'react-native';

import { STORAGE_KEYS, THEME_PREFERENCES, type ThemePreference } from '@/constants/app';
import { preferences } from '@/lib/storage';

import { type ColorScheme, colors, type ThemeColors } from './tokens';

interface ThemeContextValue {
  scheme: ColorScheme;
  colors: ThemeColors;
  preference: ThemePreference;
  setPreference: (preference: ThemePreference) => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

const isPreference = (value: string | null): value is ThemePreference =>
  THEME_PREFERENCES.includes(value as ThemePreference);

/** `initialPreference` is used until the saved choice loads (and by tests to force a theme). */
export function ThemeProvider({ children, initialPreference = 'system' }: PropsWithChildren<{ initialPreference?: ThemePreference }>) {
  const system = useColorScheme();
  const [preference, setPreferenceState] = useState<ThemePreference>(initialPreference);

  useEffect(() => {
    void preferences.get(STORAGE_KEYS.theme).then((saved) => {
      if (isPreference(saved)) setPreferenceState(saved);
    });
  }, []);

  const setPreference = (next: ThemePreference) => {
    setPreferenceState(next);
    void preferences.set(STORAGE_KEYS.theme, next);
  };

  const scheme: ColorScheme = preference === 'system' ? (system === 'dark' ? 'dark' : 'light') : preference;

  return (
    <ThemeContext.Provider value={{ scheme, colors: colors[scheme], preference, setPreference }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useAppTheme(): ThemeContextValue {
  const value = useContext(ThemeContext);
  if (!value) throw new Error('useAppTheme must be used inside <ThemeProvider>');
  return value;
}
