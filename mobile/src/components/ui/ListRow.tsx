import Ionicons from '@expo/vector-icons/Ionicons';
import type { ReactNode } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';

import { useAppTheme } from '@/theme/ThemeProvider';
import { spacing, TOUCH_TARGET } from '@/theme/tokens';

import { AppText } from './AppText';

interface ListRowProps {
  title: string;
  subtitle?: string;
  left?: ReactNode;
  right?: ReactNode;
  onPress?: () => void;
  chevron?: boolean;
  danger?: boolean;
}

export function ListRow({ title, subtitle, left, right, onPress, chevron = !!onPress, danger }: ListRowProps) {
  const { colors } = useAppTheme();
  return (
    <Pressable
      accessibilityRole={onPress ? 'button' : undefined}
      onPress={onPress}
      disabled={!onPress}
      style={({ pressed }) => [styles.row, { opacity: pressed ? 0.7 : 1 }]}
    >
      {left}
      <View style={styles.text}>
        <AppText weight="medium" color={danger ? 'danger' : 'text'} numberOfLines={2}>
          {title}
        </AppText>
        {subtitle && (
          <AppText size="small" color="textMuted" numberOfLines={2}>
            {subtitle}
          </AppText>
        )}
      </View>
      {right}
      {chevron && <Ionicons name="chevron-forward" size={20} color={colors.textMuted} />}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  row: { minHeight: TOUCH_TARGET, flexDirection: 'row', alignItems: 'center', gap: spacing.md, paddingVertical: spacing.sm },
  text: { flex: 1, gap: spacing.xxs },
});
