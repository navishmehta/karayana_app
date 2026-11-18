import { useLocalSearchParams } from 'expo-router';
import { StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { CatalogueBrowser } from '@/components/catalogue';
import { useAppTheme } from '@/theme/ThemeProvider';
import { DEFAULT_FILTERS, SORT_OPTIONS, type SortOption } from '@/utils/catalogue';

/** Search tab. "See all" links from the home screen open it with filters preset via URL params. */
export default function SearchScreen() {
  const { colors } = useAppTheme();
  const params = useLocalSearchParams<{ q?: string; sort?: string; on_offer?: string; featured?: string }>();
  const sort = SORT_OPTIONS.includes(params.sort as SortOption) ? (params.sort as SortOption) : DEFAULT_FILTERS.sort;
  const initial = {
    ...DEFAULT_FILTERS,
    search: params.q ?? '',
    sort,
    onOffer: params.on_offer === '1',
    featured: params.featured === '1',
  };

  return (
    <SafeAreaView edges={['top']} style={[styles.root, { backgroundColor: colors.background }]}>
      {/* A new key resets the filters whenever the screen is opened with different presets. */}
      <CatalogueBrowser key={JSON.stringify(params)} initial={initial} autoFocus={!params.sort && !params.featured && !params.on_offer} />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({ root: { flex: 1 } });
