import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import type { StaffProduct } from '@/api/staff/types';
import { useCan } from '@/auth/permissions';
import { SearchBar } from '@/components/catalogue';
import { ProductImage } from '@/components/catalogue/ProductImage';
import { PagedList } from '@/components/staff/PagedList';
import { StockBadge } from '@/components/staff/StatusBadges';
import { AppText, ChipGroup, Fab, ListRow } from '@/components/ui';
import { SEARCH_DEBOUNCE_MS } from '@/constants/app';
import { PERMISSIONS } from '@/constants/permissions';
import { useDebouncedValue } from '@/hooks/useDebouncedValue';
import { useStaffProducts } from '@/hooks/useStaff';
import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, spacing } from '@/theme/tokens';
import { formatMoney, formatQuantity } from '@/utils/format';

const FILTERS = ['all', 'low_stock', 'out_of_stock', 'inactive', 'hidden'] as const;
type Filter = (typeof FILTERS)[number];

const THUMB = 48;

export const openProduct = (id: number) => router.push({ pathname: '/staff/product/[id]', params: { id: String(id) } });

export default function ProductsScreen() {
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const params = useLocalSearchParams<{ filter?: string }>();
  const canCreate = useCan(PERMISSIONS.productsCreate);
  const canSeeStock = useCan(PERMISSIONS.stockView);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<Filter>(FILTERS.includes(params.filter as Filter) ? (params.filter as Filter) : 'all');
  const debounced = useDebouncedValue(search, SEARCH_DEBOUNCE_MS);

  const filters = FILTERS.filter((f) => canSeeStock || (f !== 'low_stock' && f !== 'out_of_stock'));
  const products = useStaffProducts({
    search: debounced || undefined,
    stock_status: filter === 'low_stock' || filter === 'out_of_stock' ? filter : undefined,
    is_active: filter === 'inactive' ? false : undefined,
    is_visible_to_customers: filter === 'hidden' ? false : undefined,
  });

  const render = (p: StaffProduct) => (
    <View style={[styles.row, { backgroundColor: colors.surface, borderColor: colors.border }]}>
      <ListRow
        title={p.name}
        subtitle={[p.sku, p.selling_price !== undefined ? formatMoney(p.selling_price) : null, p.current_stock !== undefined ? formatQuantity(p.current_stock, p.unit.short_name) : null]
          .filter(Boolean)
          .join(' · ')}
        left={<ProductImage uri={p.images[0]?.thumb_url} style={styles.thumb} iconSize={20} />}
        right={p.stock_status && p.stock_status !== 'in_stock' ? <StockBadge status={p.stock_status} /> : !p.is_active ? <AppText size="small" color="textMuted">{t('staff.common.inactive')}</AppText> : undefined}
        onPress={() => openProduct(p.id)}
      />
    </View>
  );

  return (
    <SafeAreaView edges={['top']} style={[styles.root, { backgroundColor: colors.background }]}>
      <PagedList
        items={products.items}
        keyOf={(p) => p.id}
        render={render}
        query={{ ...products, hasNextPage: !!products.hasNextPage }}
        emptyTitle={t('staff.products.empty')}
        emptyBody={canCreate ? t('staff.products.emptyHint') : undefined}
        emptyIcon="cube-outline"
        bottomSpace={canCreate}
        header={
          <View style={styles.header}>
            <AppText size="heading" weight="bold">
              {t('staff.tabs.products')}
            </AppText>
            <SearchBar value={search} onChangeText={setSearch} />
            <ChipGroup options={filters.map((f) => ({ value: f, label: t(`staff.products.filters.${f}`) }))} value={filter} onChange={setFilter} />
            {!products.isPending && (
              <AppText size="small" color="textMuted">
                {t('catalogue.resultsCount', { count: products.total })}
              </AppText>
            )}
          </View>
        }
      />
      {canCreate && <Fab label={t('staff.products.add')} onPress={() => router.push('/staff/product/form')} />}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  header: { gap: spacing.md, marginBottom: spacing.sm },
  row: { borderWidth: 1, borderRadius: radius.lg, paddingHorizontal: spacing.md },
  thumb: { width: THUMB, borderRadius: radius.sm },
});
