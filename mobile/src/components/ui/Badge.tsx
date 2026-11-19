import { StyleSheet, View } from 'react-native';

import { withAlpha } from '@/theme/color';
import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, spacing, type ThemeColors } from '@/theme/tokens';

import { AppText } from './AppText';

const TINT_OPACITY = 0.12;
const DOT_SIZE = 6;

/** A soft tinted pill with a status dot, e.g. "Low stock". */
export function Badge({ label, tone = 'primary' }: { label: string; tone?: keyof ThemeColors }) {
  const { colors } = useAppTheme();
  return (
    <View style={[styles.badge, { backgroundColor: withAlpha(colors[tone], TINT_OPACITY) }]}>
      <View style={[styles.dot, { backgroundColor: colors[tone] }]} />
      <AppText size="caption" weight="semibold" color={tone}>
        {label}
      </AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    borderRadius: radius.pill,
    paddingHorizontal: spacing.sm + 2,
    paddingVertical: spacing.xxs + 1,
  },
  dot: { width: DOT_SIZE, height: DOT_SIZE, borderRadius: DOT_SIZE / 2 },
});
