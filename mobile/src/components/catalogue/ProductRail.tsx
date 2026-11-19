/** Horizontal strip of products on the home screen, with a title and "See all". */
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { FlatList, Pressable, StyleSheet, View } from 'react-native';

import type { PublicProduct } from '@/api/types';
import { AppText } from '@/components/ui';
import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, spacing } from '@/theme/tokens';

import { ProductCard } from './ProductCard';

const CARD_WIDTH = 168;

export function ProductRail({ title, products, onSeeAll }: { title: string; products: PublicProduct[]; onSeeAll?: () => void }) {
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  if (!products.length) return null;
  return (
    <View style={styles.section}>
      <View style={styles.header}>
        <AppText size="title" weight="bold">
          {title}
        </AppText>
        {onSeeAll && (
          <Pressable
            accessibilityRole="link"
            onPress={onSeeAll}
            hitSlop={spacing.sm}
            style={[styles.seeAll, { backgroundColor: colors.primarySoft }]}
          >
            <AppText size="small" weight="semibold" color="primary">
              {t('catalogue.seeAll')}
            </AppText>
            <Ionicons name="arrow-forward" size={14} color={colors.primary} />
          </Pressable>
        )}
      </View>
      <FlatList
        horizontal
        data={products}
        keyExtractor={(p) => p.slug}
        renderItem={({ item }) => <ProductCard product={item} width={CARD_WIDTH} />}
        contentContainerStyle={styles.list}
        showsHorizontalScrollIndicator={false}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  section: { gap: spacing.md },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  list: { gap: spacing.md, paddingVertical: spacing.sm, paddingHorizontal: spacing.xxs },
  seeAll: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xxs,
    borderRadius: radius.pill,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
  },
});
