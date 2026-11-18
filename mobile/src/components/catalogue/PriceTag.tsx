import { useTranslation } from 'react-i18next';
import { StyleSheet, View } from 'react-native';

import type { PublicProduct } from '@/api/types';
import { AppText } from '@/components/ui';
import { spacing } from '@/theme/tokens';
import { formatMoney, formatPercent } from '@/utils/format';

/** Customer price, MRP struck through when higher, and the discount. */
export function PriceTag({ product, large }: { product: PublicProduct; large?: boolean }) {
  const { t } = useTranslation();
  const showMrp = product.mrp !== null && Number(product.mrp) > Number(product.price);
  return (
    <View style={styles.row}>
      <AppText size={large ? 'title' : 'body'} weight="bold" accessibilityLabel={t('catalogue.priceLabel', { price: formatMoney(product.price) })}>
        {formatMoney(product.price)}
      </AppText>
      {showMrp && (
        <AppText
          size={large ? 'body' : 'small'}
          color="textMuted"
          style={styles.mrp}
          accessibilityLabel={t('catalogue.mrpLabel', { price: formatMoney(product.mrp) })}
        >
          {formatMoney(product.mrp)}
        </AppText>
      )}
      {product.discount_percent && (
        <AppText size={large ? 'body' : 'small'} weight="semibold" color="success">
          {t('catalogue.percentOff', { percent: formatPercent(product.discount_percent) })}
        </AppText>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'baseline', flexWrap: 'wrap', columnGap: spacing.sm },
  mrp: { textDecorationLine: 'line-through' },
});
