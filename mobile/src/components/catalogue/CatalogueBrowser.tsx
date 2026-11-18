/** Search box + filter sheet + product grid. Used by the Search tab and the category page. */
import Ionicons from '@expo/vector-icons/Ionicons';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Pressable, StyleSheet, View } from 'react-native';

import { AppText } from '@/components/ui';
import { SEARCH_DEBOUNCE_MS } from '@/constants/app';
import { useProductPages, useStoreInfo } from '@/hooks/useCatalogue';
import { useDebouncedValue } from '@/hooks/useDebouncedValue';
import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, spacing, TOUCH_TARGET } from '@/theme/tokens';
import { activeFilterCount, type CatalogueFilters, toCatalogueQuery } from '@/utils/catalogue';

import { FilterSheet } from './FilterSheet';
import { ProductGrid } from './ProductGrid';
import { SearchBar } from './SearchBar';

export function CatalogueBrowser({ initial, autoFocus }: { initial: CatalogueFilters; autoFocus?: boolean }) {
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const store = useStoreInfo();
  const [filters, setFilters] = useState(initial);
  const [sheetOpen, setSheetOpen] = useState(false);
  const search = useDebouncedValue(filters.search, SEARCH_DEBOUNCE_MS);
  const pages = useProductPages(toCatalogueQuery({ ...filters, search }));
  const activeCount = activeFilterCount(filters);

  const header = (
    <View style={styles.header}>
      <View style={styles.searchRow}>
        <View style={styles.flex}>
          <SearchBar value={filters.search} onChangeText={(text) => setFilters((f) => ({ ...f, search: text }))} autoFocus={autoFocus} />
        </View>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={t('catalogue.filters')}
          onPress={() => setSheetOpen(true)}
          style={[styles.filterButton, { borderColor: activeCount ? colors.primary : colors.border, backgroundColor: colors.surface }]}
        >
          <Ionicons name="options-outline" size={22} color={activeCount ? colors.primary : colors.text} />
          {activeCount > 0 && (
            <View style={[styles.count, { backgroundColor: colors.primary }]}>
              <AppText size="caption" weight="bold" color="textOnPrimary">
                {activeCount}
              </AppText>
            </View>
          )}
        </Pressable>
      </View>
      {!pages.isPending && !pages.isError && (
        <AppText size="small" color="textMuted" accessibilityLiveRegion="polite">
          {t('catalogue.resultsCount', { count: pages.total })}
        </AppText>
      )}
    </View>
  );

  return (
    <>
      <ProductGrid
        products={pages.products}
        header={header}
        isPending={pages.isPending}
        isError={pages.isError}
        error={pages.error}
        isRefetching={pages.isRefetching}
        isFetchingNextPage={pages.isFetchingNextPage}
        hasNextPage={!!pages.hasNextPage}
        onRefresh={() => void pages.refetch()}
        onEndReached={() => void pages.fetchNextPage()}
        emptyTitle={t('catalogue.noResults')}
        emptyBody={t('catalogue.noResultsHint')}
      />
      <FilterSheet
        visible={sheetOpen}
        filters={filters}
        offersEnabled={!!store.data?.offers_enabled}
        onClose={() => setSheetOpen(false)}
        onApply={(next) => {
          setFilters(next);
          setSheetOpen(false);
        }}
      />
    </>
  );
}

const styles = StyleSheet.create({
  header: { gap: spacing.sm, marginBottom: spacing.xs },
  searchRow: { flexDirection: 'row', gap: spacing.sm, alignItems: 'center' },
  flex: { flex: 1 },
  filterButton: {
    width: TOUCH_TARGET,
    height: TOUCH_TARGET,
    borderRadius: radius.pill,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  count: {
    position: 'absolute',
    top: -2,
    right: -2,
    minWidth: 18,
    height: 18,
    borderRadius: radius.pill,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: spacing.xxs,
  },
});
