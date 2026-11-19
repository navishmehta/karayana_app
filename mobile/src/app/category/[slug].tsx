import { useLocalSearchParams } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { StyleSheet, View } from 'react-native';

import { CatalogueBrowser } from '@/components/catalogue';
import { ErrorState, LoadingView, ScreenHeader } from '@/components/ui';
import { useCategory } from '@/hooks/useCatalogue';
import { useAppTheme } from '@/theme/ThemeProvider';
import { DEFAULT_FILTERS, localizedName } from '@/utils/catalogue';
import { errorMessage } from '@/utils/errors';
import { showError } from '@/utils/query';

export default function CategoryScreen() {
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const { t, i18n } = useTranslation();
  const { colors } = useAppTheme();
  const category = useCategory(slug);

  return (
    <View style={[styles.root, { backgroundColor: colors.background }]}>
      <ScreenHeader title={category.data ? localizedName(category.data, i18n.language) : ''} />
      {category.isPending ? (
        <LoadingView />
      ) : showError(category) ? (
        <ErrorState message={errorMessage(category.error, t)} onRetry={() => void category.refetch()} />
      ) : (
        <CatalogueBrowser initial={{ ...DEFAULT_FILTERS, category: slug }} />
      )}
    </View>
  );
}

const styles = StyleSheet.create({ root: { flex: 1 } });
