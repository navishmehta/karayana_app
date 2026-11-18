import { Image } from 'expo-image';
import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { Pressable, StyleSheet, View } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';

import type { PublicCategory } from '@/api/types';
import { AppText } from '@/components/ui';
import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, spacing } from '@/theme/tokens';
import { localizedName } from '@/utils/catalogue';

export const openCategory = (slug: string) => router.push({ pathname: '/category/[slug]', params: { slug } });

/** Large tile for the Categories tab. */
export function CategoryTile({ category }: { category: PublicCategory }) {
  const { colors } = useAppTheme();
  const { t, i18n } = useTranslation();
  const name = localizedName(category, i18n.language);
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={name}
      onPress={() => openCategory(category.slug)}
      style={({ pressed }) => [
        styles.tile,
        { backgroundColor: colors.surface, borderColor: colors.border, opacity: pressed ? 0.85 : 1 },
      ]}
    >
      <View style={[styles.icon, { backgroundColor: colors.primarySoft }]}>
        {category.image_thumb_url ? (
          <Image source={category.image_thumb_url} style={styles.image} contentFit="cover" />
        ) : (
          <Ionicons name="grid-outline" size={28} color={colors.primary} />
        )}
      </View>
      <AppText weight="semibold" align="center" numberOfLines={2}>
        {name}
      </AppText>
      <AppText size="caption" color="textMuted">
        {t('catalogue.productsCount', { count: category.products_count })}
      </AppText>
    </Pressable>
  );
}

/** Small pill for the home screen's horizontal category row. */
export function CategoryChip({ category, selected, onPress }: { category: PublicCategory; selected?: boolean; onPress?: () => void }) {
  const { colors } = useAppTheme();
  const { i18n } = useTranslation();
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ selected }}
      onPress={onPress ?? (() => openCategory(category.slug))}
      style={[
        styles.chip,
        { backgroundColor: selected ? colors.primary : colors.surface, borderColor: selected ? colors.primary : colors.border },
      ]}
    >
      <AppText size="small" weight="medium" color={selected ? 'textOnPrimary' : 'text'}>
        {localizedName(category, i18n.language)}
      </AppText>
    </Pressable>
  );
}

const ICON_SIZE = 64;

const styles = StyleSheet.create({
  tile: { flex: 1, alignItems: 'center', gap: spacing.sm, padding: spacing.lg, borderWidth: 1, borderRadius: radius.lg },
  icon: { width: ICON_SIZE, height: ICON_SIZE, borderRadius: radius.lg, overflow: 'hidden', alignItems: 'center', justifyContent: 'center' },
  image: { width: '100%', height: '100%' },
  chip: { borderWidth: 1, borderRadius: radius.pill, paddingHorizontal: spacing.lg, paddingVertical: spacing.sm },
});
