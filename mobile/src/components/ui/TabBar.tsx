/** Shared look for the customer and staff tab bars: no hard line, soft shadow, active icon in a tinted pill. */
import Ionicons from '@expo/vector-icons/Ionicons';
import type { BottomTabNavigationOptions } from 'expo-router/build/layouts/Tabs';
import { StyleSheet, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useTypography } from '@/hooks/useTypography';
import { tapFeedback } from '@/lib/haptics';
import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, shadow, spacing } from '@/theme/tokens';

type IconName = keyof typeof Ionicons.glyphMap;

/** "cube-outline" → "cube": the filled icon shown for the selected tab. */
const filled = (icon: IconName) => icon.replace(/-outline$/, '') as IconName;

const PILL_WIDTH = 56;
const PILL_HEIGHT = 30;
const ICON_SIZE = 22;
const BAR_HEIGHT = 68; // room for the icon pill and a label in Punjabi script

export function TabIcon({ icon, focused, color }: { icon: IconName; focused: boolean; color: string }) {
  const { colors } = useAppTheme();
  return (
    <View style={[styles.pill, focused && { backgroundColor: colors.primarySoft }]}>
      <Ionicons name={focused ? filled(icon) : icon} size={ICON_SIZE} color={color} />
    </View>
  );
}

export function useTabBarOptions(): BottomTabNavigationOptions {
  const { colors, scheme } = useAppTheme();
  const typography = useTypography();
  const insets = useSafeAreaInsets();
  return {
    headerShown: false,
    tabBarActiveTintColor: colors.primary,
    tabBarInactiveTintColor: colors.textMuted,
    tabBarStyle: {
      backgroundColor: colors.surface,
      borderTopWidth: scheme === 'dark' ? StyleSheet.hairlineWidth : 0,
      borderTopColor: colors.border,
      height: BAR_HEIGHT + insets.bottom,
      paddingTop: spacing.sm,
      paddingBottom: insets.bottom + spacing.xs,
      ...shadow('high', colors.shadow, scheme),
    },
    tabBarLabelStyle: typography('caption', 'semibold'),
  };
}

/** Tab press listener that adds a haptic tick. */
export const tabHaptics = { tabPress: () => tapFeedback() };

const styles = StyleSheet.create({
  pill: { width: PILL_WIDTH, height: PILL_HEIGHT, borderRadius: radius.pill, alignItems: 'center', justifyContent: 'center' },
});
