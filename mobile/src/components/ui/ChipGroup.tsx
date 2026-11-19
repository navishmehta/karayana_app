/** Single-choice chips in a horizontal row (filters such as Active / Inactive). */
import { Pressable, ScrollView, StyleSheet } from 'react-native';

import { useAppTheme } from '@/theme/ThemeProvider';
import { CHIP_HEIGHT, CHIP_HIT_SLOP, radius, spacing } from '@/theme/tokens';

import { AppText } from './AppText';

export function ChipGroup<T extends string>({
  options,
  value,
  onChange,
}: {
  options: readonly { value: T; label: string }[];
  value: T;
  onChange: (value: T) => void;
}) {
  const { colors } = useAppTheme();
  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.row} accessibilityRole="radiogroup">
      {options.map((o) => {
        const selected = o.value === value;
        return (
          <Pressable
            key={o.value}
            accessibilityRole="radio"
            accessibilityState={{ checked: selected }}
            onPress={() => onChange(o.value)}
            hitSlop={CHIP_HIT_SLOP}
            style={[
              styles.chip,
              { borderColor: selected ? colors.primary : colors.border, backgroundColor: selected ? colors.primarySoft : colors.surface },
            ]}
          >
            <AppText size="small" weight={selected ? 'semibold' : 'regular'} color={selected ? 'primary' : 'text'}>
              {o.label}
            </AppText>
          </Pressable>
        );
      })}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  // Vertical padding keeps the enlarged tap area inside the scroll view; the end padding shows the row continues.
  row: { gap: spacing.sm, paddingVertical: CHIP_HIT_SLOP, paddingRight: spacing.xl },
  chip: {
    minHeight: CHIP_HEIGHT,
    justifyContent: 'center',
    borderWidth: 1,
    borderRadius: radius.pill,
    paddingHorizontal: spacing.lg,
  },
});
