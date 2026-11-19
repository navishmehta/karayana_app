import Ionicons from '@expo/vector-icons/Ionicons';
import { StyleSheet, View } from 'react-native';

import { AppText, PressableScale } from '@/components/ui';
import { withAlpha } from '@/theme/color';
import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, shadow, spacing, type ThemeColors } from '@/theme/tokens';

const ICON_TINT = 0.13;
const ICON_BOX = 40;

/** A dashboard number with a colour-coded icon. Tapping it opens the matching filtered list. */
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
  const { colors, scheme } = useAppTheme();
  const toneColor = colors[tone];
  return (
    <PressableScale
      accessibilityRole={onPress ? 'button' : 'summary'}
      accessibilityLabel={`${label}: ${value}`}
      onPress={onPress}
      disabled={!onPress}
      style={[
        styles.tile,
        { backgroundColor: colors.surface },
        scheme === 'dark' && { borderWidth: StyleSheet.hairlineWidth, borderColor: colors.border },
        shadow('medium', colors.shadow, scheme),
      ]}
    >
      <View style={styles.top}>
        <View style={[styles.icon, { backgroundColor: withAlpha(toneColor, ICON_TINT) }]}>
          <Ionicons name={icon} size={20} color={toneColor} />
        </View>
        {onPress && <Ionicons name="arrow-forward" size={16} color={colors.textMuted} />}
      </View>
      <AppText size="heading" weight="bold" numberOfLines={1} adjustsFontSizeToFit>
        {value}
      </AppText>
      <AppText size="small" weight="medium" color="textMuted" numberOfLines={2}>
        {label}
      </AppText>
      <View style={[styles.accent, { backgroundColor: toneColor }]} />
    </PressableScale>
  );
}

const styles = StyleSheet.create({
  tile: { flexGrow: 1, flexBasis: 150, gap: spacing.xs, padding: spacing.lg, borderRadius: radius.lg, overflow: 'hidden' },
  top: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: spacing.xs },
  icon: { width: ICON_BOX, height: ICON_BOX, borderRadius: radius.md, alignItems: 'center', justifyContent: 'center' },
  accent: { position: 'absolute', left: 0, top: spacing.lg, bottom: spacing.lg, width: 3, borderTopRightRadius: 3, borderBottomRightRadius: 3 },
});
