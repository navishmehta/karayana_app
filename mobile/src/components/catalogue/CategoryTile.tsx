import Ionicons from '@expo/vector-icons/Ionicons';
import { Image } from 'expo-image';
import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { StyleSheet, View } from 'react-native';

import type { PublicCategory } from '@/api/types';
import { AppText, PressableScale } from '@/components/ui';
import { useAppTheme } from '@/theme/ThemeProvider';
import { CHIP_HEIGHT, CHIP_HIT_SLOP, radius, shadow, spacing, tintAt } from '@/theme/tokens';
import { categoryIcon, localizedName } from '@/utils/catalogue';

export const openCategory = (slug: string) => router.push({ pathname: '/category/[slug]', params: { slug } });

/** Large tile for the Categories tab. Each tile gets its own soft colour from the theme tints. */
export function CategoryTile({ category, index = 0 }: { category: PublicCategory; index?: number }) {
  const { colors, scheme } = useAppTheme();
  const { t, i18n } = useTranslation();
  const tint = tintAt(scheme, index);
  const name = localizedName(category, i18n.language);
  return (
    <PressableScale
      accessibilityRole="button"
      accessibilityLabel={name}
      onPress={() => openCategory(category.slug)}
      style={[styles.tile, { backgroundColor: colors.surface }, shadow('low', colors.shadow, scheme)]}
    >
      <View style={[styles.icon, { backgroundColor: tint.bg }]}>
        {category.image_thumb_url ? (
          <Image source={category.image_thumb_url} style={styles.image} contentFit="cover" />
        ) : (
          <Ionicons name={categoryIcon(category.name)} size={30} color={tint.fg} />
        )}
      </View>
      <AppText weight="semibold" align="center" numberOfLines={2}>
        {name}
      </AppText>
      <View style={[styles.count, { backgroundColor: tint.bg }]}>
        <AppText size="caption" weight="semibold" style={{ color: tint.fg }}>
          {t('catalogue.productsCount', { count: category.products_count })}
        </AppText>
      </View>
    </PressableScale>
  );
}

/** Pill for the home screen's horizontal category row, with a coloured dot. */
export function CategoryChip({
  category,
  selected,
  onPress,
  index = 0,
}: {
  category: PublicCategory;
  selected?: boolean;
  onPress?: () => void;
  index?: number;
}) {
  const { colors, scheme } = useAppTheme();
  const { i18n } = useTranslation();
  const tint = tintAt(scheme, index);
  return (
    <PressableScale
      accessibilityRole="button"
      accessibilityState={{ selected }}
      onPress={onPress ?? (() => openCategory(category.slug))}
      hitSlop={CHIP_HIT_SLOP}
      style={[
        styles.chip,
        { backgroundColor: selected ? colors.primary : colors.surface, borderColor: selected ? colors.primary : colors.border },
      ]}
    >
      <View style={[styles.chipIcon, { backgroundColor: selected ? colors.primarySoft : tint.bg }]}>
        {category.image_thumb_url ? (
          <Image source={category.image_thumb_url} style={styles.image} contentFit="cover" />
        ) : (
          <View style={[styles.dot, { backgroundColor: tint.fg }]} />
        )}
      </View>
      <AppText size="small" weight="semibold" color={selected ? 'textOnPrimary' : 'text'}>
        {localizedName(category, i18n.language)}
      </AppText>
    </PressableScale>
  );
}

const ICON_SIZE = 72;
const CHIP_ICON = 26;
const DOT = 8;

const styles = StyleSheet.create({
  tile: { flex: 1, alignItems: 'center', gap: spacing.sm, padding: spacing.lg, borderRadius: radius.lg },
  icon: { width: ICON_SIZE, height: ICON_SIZE, borderRadius: radius.xl, overflow: 'hidden', alignItems: 'center', justifyContent: 'center' },
  image: { width: '100%', height: '100%' },
  count: { borderRadius: radius.pill, paddingHorizontal: spacing.sm, paddingVertical: spacing.xxs },
  chip: {
    minHeight: CHIP_HEIGHT,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    borderWidth: StyleSheet.hairlineWidth,
    borderRadius: radius.pill,
    paddingLeft: spacing.xs,
    paddingRight: spacing.lg,
    paddingVertical: spacing.xs,
  },
  chipIcon: { width: CHIP_ICON, height: CHIP_ICON, borderRadius: CHIP_ICON / 2, overflow: 'hidden', alignItems: 'center', justifyContent: 'center' },
  dot: { width: DOT, height: DOT, borderRadius: DOT / 2 },
});
