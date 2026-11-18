import { StyleSheet, View } from 'react-native';

import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, spacing, type ThemeColors } from '@/theme/tokens';

import { AppText } from './AppText';

export function Badge({ label, tone = 'primary' }: { label: string; tone?: keyof ThemeColors }) {
  const { colors } = useAppTheme();
  return (
    <View style={[styles.badge, { borderColor: colors[tone] }]}>
      <AppText size="caption" weight="semibold" color={tone}>
        {label}
      </AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    alignSelf: 'flex-start',
    borderWidth: 1,
    borderRadius: radius.pill,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xxs,
  },
});
