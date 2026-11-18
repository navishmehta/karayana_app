import Ionicons from '@expo/vector-icons/Ionicons';
import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { FlatList, StyleSheet, View } from 'react-native';

import { EmptyState, ErrorState, ListRow, LoadingView, ScreenHeader } from '@/components/ui';
import { useReports } from '@/hooks/useStaff';
import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, spacing } from '@/theme/tokens';
import { errorMessage } from '@/utils/errors';

const ICONS: Record<string, keyof typeof Ionicons.glyphMap> = {
  products: 'cube-outline',
  categories: 'grid-outline',
  stock: 'layers-outline',
  low_stock: 'trending-down-outline',
  expiry: 'hourglass-outline',
  purchase_cost: 'wallet-outline',
  selling_price: 'pricetag-outline',
  valuation: 'cash-outline',
  profit_margin: 'trending-up-outline',
  stock_movements: 'swap-vertical-outline',
};

export default function ReportsScreen() {
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const reports = useReports();

  return (
    <View style={[styles.root, { backgroundColor: colors.background }]}>
      <ScreenHeader title={t('staff.more.reports')} />
      {reports.isPending ? (
        <LoadingView />
      ) : reports.isError ? (
        <ErrorState message={errorMessage(reports.error, t)} onRetry={() => void reports.refetch()} />
      ) : (
        <FlatList
          data={reports.data}
          keyExtractor={(r) => r.key}
          contentContainerStyle={styles.content}
          ListEmptyComponent={<EmptyState icon="document-text-outline" title={t('staff.reports.none')} />}
          renderItem={({ item }) => (
            <View style={[styles.card, { backgroundColor: colors.surface, borderColor: colors.border }]}>
              <ListRow
                title={item.label}
                subtitle={item.description}
                left={<Ionicons name={ICONS[item.key] ?? 'document-text-outline'} size={22} color={colors.primary} />}
                onPress={() => router.push({ pathname: '/staff/reports/[key]', params: { key: item.key } })}
              />
            </View>
          )}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  content: { width: '100%', maxWidth: 820, alignSelf: 'center', padding: spacing.lg, gap: spacing.sm },
  card: { borderWidth: 1, borderRadius: radius.lg, paddingHorizontal: spacing.md },
});
