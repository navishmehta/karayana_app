import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { StyleSheet, View } from 'react-native';

import type { PublicProduct } from '@/api/types';
import { AppText, Gradient, PressableScale } from '@/components/ui';
import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, shadow, spacing } from '@/theme/tokens';
import { formatPercent } from '@/utils/format';

import { AvailabilityBadge } from './AvailabilityBadge';
import { PriceTag } from './PriceTag';
import { ProductImage } from './ProductImage';

export function ProductCard({ product, width }: { product: PublicProduct; width?: number }) {
  const { colors, scheme } = useAppTheme();
  const { t } = useTranslation();
  const outOfStock = product.availability === 'out_of_stock';

  return (
    <PressableScale
      accessibilityRole="button"
      accessibilityLabel={product.name}
      onPress={() => router.push({ pathname: '/product/[slug]', params: { slug: product.slug } })}
      style={[
        styles.card,
        { backgroundColor: colors.surface },
        scheme === 'dark' && { borderWidth: StyleSheet.hairlineWidth, borderColor: colors.border },
        shadow('medium', colors.shadow, scheme),
        width ? { width } : styles.flex,
      ]}
    >
      <View style={[styles.imageBox, { backgroundColor: colors.surfaceAlt }]}>
        <ProductImage uri={product.images[0]?.thumb_url} style={outOfStock ? styles.dimmed : styles.rounded} />
        {(product.on_offer || product.discount_percent) && (
          <Gradient name="accent" direction="horizontal" style={styles.ribbon}>
            <AppText size="caption" weight="bold" style={styles.ribbonText}>
              {product.discount_percent
                ? t('catalogue.percentOff', { percent: formatPercent(product.discount_percent) })
                : t('catalogue.offer')}
            </AppText>
          </Gradient>
        )}
      </View>
      <View style={styles.body}>
        {product.brand && (
          <AppText size="caption" weight="semibold" color="primary" numberOfLines={1} style={styles.brand}>
            {product.brand}
          </AppText>
        )}
        <AppText weight="semibold" numberOfLines={2} style={styles.name}>
          {product.name}
        </AppText>
        <AppText size="caption" color="textMuted">
          {t('catalogue.perUnit', { unit: product.unit })}
        </AppText>
        <PriceTag product={product} hideDiscount />
        {product.availability !== 'in_stock' && <AvailabilityBadge availability={product.availability} />}
      </View>
    </PressableScale>
  );
}

const NAME_MIN_LINES = 2;
const WHITE = '#FFFFFF'; // ribbon text sits on the dark saffron gradient in both themes

const styles = StyleSheet.create({
  card: { borderRadius: radius.lg, padding: spacing.sm },
  flex: { flex: 1 },
  imageBox: { borderRadius: radius.md, overflow: 'hidden' },
  rounded: { borderRadius: radius.md },
  body: { paddingHorizontal: spacing.xs, paddingTop: spacing.sm, paddingBottom: spacing.xs, gap: spacing.xxs + 1 },
  brand: { textTransform: 'uppercase', letterSpacing: 0.6 },
  name: { minHeight: NAME_MIN_LINES * 20 },
  ribbon: {
    position: 'absolute',
    top: spacing.sm,
    left: spacing.sm,
    borderRadius: radius.pill,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xxs,
  },
  ribbonText: { color: WHITE },
  dimmed: { opacity: 0.45, borderRadius: radius.md },
});
