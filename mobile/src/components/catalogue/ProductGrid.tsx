/**
 * Scrollable product grid used by category, search and "see all" screens.
 * It is the screen's scroll view: header content goes in `header`; more pages load near the end.
 */
import type { ReactElement } from 'react';
import { useTranslation } from 'react-i18next';
import { ActivityIndicator, FlatList, RefreshControl, StyleSheet, useWindowDimensions, View } from 'react-native';

import type { PublicProduct } from '@/api/types';
import { EmptyState, ErrorState, LoadingView } from '@/components/ui';
import { useAppTheme } from '@/theme/ThemeProvider';
import { spacing } from '@/theme/tokens';
import { gridColumns } from '@/utils/catalogue';
import { errorMessage } from '@/utils/errors';

import { ProductCard } from './ProductCard';

const MAX_LIST_WIDTH = 1200;

interface ProductGridProps {
  products: PublicProduct[];
  header?: ReactElement;
  isPending: boolean;
  isError: boolean;
  error: unknown;
  isRefetching: boolean;
  isFetchingNextPage: boolean;
  hasNextPage: boolean;
  onRefresh: () => void;
  onEndReached: () => void;
  emptyTitle: string;
  emptyBody?: string;
}

export function ProductGrid(props: ProductGridProps) {
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const { width } = useWindowDimensions();
  const columns = gridColumns(Math.min(width, MAX_LIST_WIDTH) - spacing.lg * 2);

  const body = props.isPending ? (
    <LoadingView />
  ) : props.isError ? (
    <ErrorState message={errorMessage(props.error, t)} onRetry={props.onRefresh} />
  ) : (
    <EmptyState icon="search-outline" title={props.emptyTitle} body={props.emptyBody} />
  );

  return (
    <FlatList
      key={columns} // FlatList needs a remount when the column count changes
      data={props.isPending || props.isError ? [] : props.products}
      keyExtractor={(p) => p.slug}
      numColumns={columns}
      renderItem={({ item }) => <ProductCard product={item} />}
      columnWrapperStyle={columns > 1 ? styles.row : undefined}
      contentContainerStyle={styles.content}
      ListHeaderComponent={props.header}
      ListEmptyComponent={body}
      ListFooterComponent={
        props.isFetchingNextPage ? <ActivityIndicator style={styles.footer} color={colors.primary} /> : <View style={styles.footer} />
      }
      onEndReached={() => props.hasNextPage && !props.isFetchingNextPage && props.onEndReached()}
      onEndReachedThreshold={0.5}
      refreshControl={
        <RefreshControl refreshing={props.isRefetching && !props.isFetchingNextPage} onRefresh={props.onRefresh} tintColor={colors.primary} />
      }
      keyboardShouldPersistTaps="handled"
    />
  );
}

const styles = StyleSheet.create({
  content: { flexGrow: 1, width: '100%', maxWidth: MAX_LIST_WIDTH, alignSelf: 'center', padding: spacing.lg, gap: spacing.md },
  row: { gap: spacing.md },
  footer: { height: spacing.xxxl },
});
