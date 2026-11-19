/** Light status-bar icons while a screen with a dark green hero is showing; the theme's default when leaving. */
import { setStatusBarStyle } from 'expo-status-bar';
import { useFocusEffect } from 'expo-router';
import { useCallback } from 'react';

import { useAppTheme } from '@/theme/ThemeProvider';

export function useHeroStatusBar(): void {
  const { scheme } = useAppTheme();
  useFocusEffect(
    useCallback(() => {
      setStatusBarStyle('light');
      return () => setStatusBarStyle(scheme === 'dark' ? 'light' : 'dark');
    }, [scheme]),
  );
}
