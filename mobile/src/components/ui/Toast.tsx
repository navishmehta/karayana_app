/** Short success / error message at the bottom of the screen. Call toast.success('Saved') anywhere. */
import { useEffect } from 'react';
import { StyleSheet, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { create } from 'zustand';

import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, spacing } from '@/theme/tokens';

import { AppText } from './AppText';

const TOAST_MS = 2800;

interface ToastState {
  message: string | null;
  tone: 'success' | 'danger';
  show: (message: string, tone: 'success' | 'danger') => void;
  hide: () => void;
}

const useToastStore = create<ToastState>((set) => ({
  message: null,
  tone: 'success',
  show: (message, tone) => set({ message, tone }),
  hide: () => set({ message: null }),
}));

export const toast = {
  success: (message: string) => useToastStore.getState().show(message, 'success'),
  error: (message: string) => useToastStore.getState().show(message, 'danger'),
};

export function ToastHost() {
  const { colors } = useAppTheme();
  const insets = useSafeAreaInsets();
  const { message, tone, hide } = useToastStore();

  useEffect(() => {
    if (!message) return;
    const timer = setTimeout(hide, TOAST_MS);
    return () => clearTimeout(timer);
  }, [message, hide]);

  if (!message) return null;
  return (
    <View pointerEvents="none" style={[styles.wrap, { bottom: insets.bottom + spacing.xxxl * 1.5 }]}>
      <View style={[styles.toast, { backgroundColor: colors[tone] }]} accessibilityLiveRegion="polite" accessibilityRole="alert">
        <AppText weight="medium" color="textOnPrimary" align="center">
          {message}
        </AppText>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { position: 'absolute', left: spacing.lg, right: spacing.lg, alignItems: 'center' },
  toast: { maxWidth: 480, borderRadius: radius.md, paddingHorizontal: spacing.lg, paddingVertical: spacing.md },
});
