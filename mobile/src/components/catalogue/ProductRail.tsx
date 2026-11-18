/** Horizontal strip of products on the home screen, with a title and "See all". */
import { useTranslation } from 'react-i18next';
import { FlatList, Pressable, StyleSheet, View } from 'react-native';

import type { PublicProduct } from '@/api/types';
import { AppText } from '@/components/ui';
import { spacing } from '@/theme/tokens';

import { ProductCard } from './ProductCard';

const CARD_WIDTH = 168;

export function ProductRail({ title, products, onSeeAll }: { title: string; products: PublicProduct[]; onSeeAll?: () => void }) {
  const { t } = useTranslation();
  if (!products.length) return null;
  return (
    <View style={styles.section}>
      <View style={styles.header}>
        <AppText size="subtitle" weight="bold">
          {title}
        </AppText>
        {onSeeAll && (
          <Pressable accessibilityRole="link" onPress={onSeeAll} hitSlop={spacing.sm}>
            <AppText weight="semibold" color="primary">
              {t('catalogue.seeAll')}
            </AppText>
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
  list: { gap: spacing.md },
});
