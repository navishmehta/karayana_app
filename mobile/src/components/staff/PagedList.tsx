/** Scrolling list for paged staff data: header, rows, load more, refresh, empty / error states. */
import type { ReactElement } from 'react';
import { useTranslation } from 'react-i18next';
import { ActivityIndicator, FlatList, RefreshControl, StyleSheet, View } from 'react-native';

import { EmptyState, ErrorState, LoadingView } from '@/components/ui';
import { useAppTheme } from '@/theme/ThemeProvider';
import { spacing } from '@/theme/tokens';
import { errorMessage } from '@/utils/errors';

const MAX_WIDTH = 900;

interface PagedListProps<T> {
  items: T[];
  keyOf: (item: T) => string | number;
  render: (item: T) => ReactElement;
  header?: ReactElement;
  query: {
    isPending: boolean;
    isError: boolean;
    error: unknown;
    isRefetching: boolean;
    isFetchingNextPage: boolean;
    hasNextPage: boolean;
    refetch: () => unknown;
    fetchNextPage: () => unknown;
  };
  emptyTitle: string;
  emptyBody?: string;
  emptyIcon?: Parameters<typeof EmptyState>[0]['icon'];
  bottomSpace?: boolean; // leave room for a floating button
}

export function PagedList<T>({ items, keyOf, render, header, query, emptyTitle, emptyBody, emptyIcon, bottomSpace }: PagedListProps<T>) {
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  // Saved items stay visible when a reload fails (e.g. offline); the error only shows when there is nothing.
  const failed = query.isError && items.length === 0;
  const empty = query.isPending ? (
    <LoadingView />
  ) : failed ? (
    <ErrorState message={errorMessage(query.error, t)} onRetry={() => void query.refetch()} />
  ) : (
    <EmptyState icon={emptyIcon} title={emptyTitle} body={emptyBody} />
  );

  return (
    <FlatList
      data={query.isPending || failed ? [] : items}
      keyExtractor={(item) => String(keyOf(item))}
      renderItem={({ item }) => render(item)}
      ListHeaderComponent={header}
      ListEmptyComponent={empty}
      ListFooterComponent={
        <View style={bottomSpace ? styles.fabSpace : styles.footer}>
          {query.isFetchingNextPage && <ActivityIndicator color={colors.primary} />}
        </View>
      }
      contentContainerStyle={styles.content}
      onEndReached={() => query.hasNextPage && !query.isFetchingNextPage && void query.fetchNextPage()}
      onEndReachedThreshold={0.5}
      refreshControl={
        <RefreshControl refreshing={query.isRefetching && !query.isFetchingNextPage} onRefresh={() => void query.refetch()} tintColor={colors.primary} />
      }
      keyboardShouldPersistTaps="handled"
    />
  );
}

const styles = StyleSheet.create({
  content: { flexGrow: 1, width: '100%', maxWidth: MAX_WIDTH, alignSelf: 'center', padding: spacing.lg, gap: spacing.sm },
  footer: { minHeight: spacing.xl },
  fabSpace: { minHeight: spacing.xxxl * 2 },
});
