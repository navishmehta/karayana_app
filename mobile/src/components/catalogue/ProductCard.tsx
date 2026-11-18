import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { Pressable, StyleSheet, View } from 'react-native';

import type { PublicProduct } from '@/api/types';
import { AppText, Badge } from '@/components/ui';
import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, spacing } from '@/theme/tokens';

import { AvailabilityBadge } from './AvailabilityBadge';
import { PriceTag } from './PriceTag';
import { ProductImage } from './ProductImage';

export function ProductCard({ product, width }: { product: PublicProduct; width?: number }) {
  const { colors } = useAppTheme();
  const { t } = useTranslation();
  const outOfStock = product.availability === 'out_of_stock';

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={product.name}
      onPress={() => router.push({ pathname: '/product/[slug]', params: { slug: product.slug } })}
      style={({ pressed }) => [
        styles.card,
        { backgroundColor: colors.surface, borderColor: colors.border, opacity: pressed ? 0.85 : 1 },
        width ? { width } : styles.flex,
      ]}
    >
      <View>
        <ProductImage uri={product.images[0]?.thumb_url} style={outOfStock ? styles.dimmed : undefined} />
        {product.on_offer && (
          <View style={styles.ribbon}>
            <Badge label={t('catalogue.offer')} tone="accent" />
          </View>
        )}
      </View>
      <View style={styles.body}>
        {product.brand && (
          <AppText size="caption" color="textMuted" numberOfLines={1}>
            {product.brand}
          </AppText>
        )}
        <AppText weight="medium" numberOfLines={2} style={styles.name}>
          {product.name}
        </AppText>
        <AppText size="caption" color="textMuted">
          {t('catalogue.perUnit', { unit: product.unit })}
        </AppText>
        <PriceTag product={product} />
        {product.availability !== 'in_stock' && <AvailabilityBadge availability={product.availability} />}
      </View>
    </Pressable>
  );
}

const NAME_MIN_LINES = 2;

const styles = StyleSheet.create({
  card: { borderWidth: 1, borderRadius: radius.lg, overflow: 'hidden' },
  flex: { flex: 1 },
  body: { padding: spacing.md, gap: spacing.xs },
  name: { minHeight: NAME_MIN_LINES * 20 },
  ribbon: { position: 'absolute', top: spacing.sm, left: spacing.sm },
  dimmed: { opacity: 0.5 },
});
