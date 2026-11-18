import Ionicons from '@expo/vector-icons/Ionicons';
import { Pressable, StyleSheet, View } from 'react-native';

import { AppText } from '@/components/ui';
import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, spacing, type ThemeColors } from '@/theme/tokens';

/** A dashboard number. Tapping it opens the matching filtered list. */
export function KpiTile({
  label,
  value,
  icon,
  tone = 'primary',
  onPress,
}: {
  label: string;
  value: string;
  icon: keyof typeof Ionicons.glyphMap;
  tone?: keyof ThemeColors;
  onPress?: () => void;
}) {
  const { colors } = useAppTheme();
  return (
    <Pressable
      accessibilityRole={onPress ? 'button' : 'summary'}
      accessibilityLabel={`${label}: ${value}`}
      onPress={onPress}
      disabled={!onPress}
      style={({ pressed }) => [
        styles.tile,
        { backgroundColor: colors.surface, borderColor: colors.border, opacity: pressed ? 0.8 : 1 },
      ]}
    >
      <View style={[styles.icon, { backgroundColor: colors.surfaceAlt }]}>
        <Ionicons name={icon} size={20} color={colors[tone]} />
      </View>
      <AppText size="title" weight="bold" numberOfLines={1} adjustsFontSizeToFit>
        {value}
      </AppText>
      <AppText size="small" color="textMuted" numberOfLines={2}>
        {label}
      </AppText>
    </Pressable>
  );
}

const ICON_BOX = 36;

const styles = StyleSheet.create({
  tile: { flexGrow: 1, flexBasis: 150, gap: spacing.xs, padding: spacing.lg, borderWidth: 1, borderRadius: radius.lg },
  icon: { width: ICON_BOX, height: ICON_BOX, borderRadius: radius.md, alignItems: 'center', justifyContent: 'center' },
});
