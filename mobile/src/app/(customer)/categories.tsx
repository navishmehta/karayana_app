import { useTranslation } from 'react-i18next';
import { FlatList, StyleSheet, useWindowDimensions } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { CategoryTile } from '@/components/catalogue';
import { AppText, EmptyState, ErrorState, LoadingView } from '@/components/ui';
import { useCategories } from '@/hooks/useCatalogue';
import { useAppTheme } from '@/theme/ThemeProvider';
import { spacing } from '@/theme/tokens';
import { gridColumns } from '@/utils/catalogue';
import { errorMessage } from '@/utils/errors';

const MAX_WIDTH = 1200;

export default function CategoriesScreen() {
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const { width } = useWindowDimensions();
  const categories = useCategories();
  const columns = gridColumns(Math.min(width, MAX_WIDTH));

  return (
    <SafeAreaView edges={['top']} style={[styles.root, { backgroundColor: colors.background }]}>
      {categories.isPending ? (
        <LoadingView />
      ) : categories.isError ? (
        <ErrorState message={errorMessage(categories.error, t)} onRetry={() => void categories.refetch()} />
      ) : (
        <FlatList
          key={columns}
          data={categories.data}
          keyExtractor={(c) => c.slug}
          numColumns={columns}
          renderItem={({ item }) => <CategoryTile category={item} />}
          columnWrapperStyle={styles.row}
          contentContainerStyle={styles.content}
          ListHeaderComponent={
            <AppText size="heading" weight="bold">
              {t('catalogue.categories')}
            </AppText>
          }
          ListEmptyComponent={<EmptyState icon="grid-outline" title={t('catalogue.noCategories')} />}
          refreshing={categories.isRefetching}
          onRefresh={() => void categories.refetch()}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  content: { flexGrow: 1, width: '100%', maxWidth: MAX_WIDTH, alignSelf: 'center', padding: spacing.lg, gap: spacing.md },
  row: { gap: spacing.md },
});
