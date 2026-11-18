import { router } from 'expo-router';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import type { Transaction } from '@/api/staff/types';
import { useCan } from '@/auth/permissions';
import { PagedList } from '@/components/staff/PagedList';
import { AppText, Button, ChipGroup, ListRow } from '@/components/ui';
import { PERMISSIONS } from '@/constants/permissions';
import { STOCK_KINDS } from '@/constants/stock';
import { useTransactions } from '@/hooks/useStaff';
import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, spacing } from '@/theme/tokens';
import { formatDateTime, formatQuantity } from '@/utils/format';

/** History filters -> ledger transaction types. */
const TYPE_FILTERS: Record<string, string[] | undefined> = {
  all: undefined,
  in: ['opening', 'stock_in'],
  out: ['stock_out'],
  adjust: ['adjustment_in', 'adjustment_out'],
  damaged: ['damaged'],
  expired: ['expired'],
};

export default function StockScreen() {
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const canMove = useCan(PERMISSIONS.stockUpdate);
  const [filter, setFilter] = useState('all');
  const history = useTransactions({ type: TYPE_FILTERS[filter] });

  const render = (tx: Transaction) => {
    const positive = Number(tx.quantity_change) > 0;
    return (
      <View style={[styles.row, { backgroundColor: colors.surface, borderColor: colors.border }]}>
        <ListRow
          title={tx.product.name}
          subtitle={[
            t(`staff.stock.types.${tx.type}`, { defaultValue: tx.type }),
            tx.reason ? t(`staff.stock.reasons.${tx.reason}`, { defaultValue: tx.reason }) : null,
            t('staff.stock.by', { name: tx.user.name }),
            formatDateTime(tx.created_at),
          ]
            .filter(Boolean)
            .join(' · ')}
          right={
            <View style={styles.qty}>
              <AppText weight="bold" color={positive ? 'success' : 'danger'}>
                {positive ? '+' : ''}
                {formatQuantity(tx.quantity_change)}
              </AppText>
              <AppText size="caption" color="textMuted">
                {t('staff.stock.after', { qty: formatQuantity(tx.product_qty_after) })}
              </AppText>
            </View>
          }
          onPress={() => router.push({ pathname: '/staff/product/[id]', params: { id: String(tx.product.id) } })}
        />
      </View>
    );
  };

  return (
    <SafeAreaView edges={['top']} style={[styles.root, { backgroundColor: colors.background }]}>
      <PagedList
        items={history.items}
        keyOf={(tx) => tx.id}
        render={render}
        query={{ ...history, hasNextPage: !!history.hasNextPage }}
        emptyTitle={t('staff.stock.empty')}
        emptyIcon="swap-vertical-outline"
        header={
          <View style={styles.header}>
            <AppText size="heading" weight="bold">
              {t('staff.tabs.stock')}
            </AppText>
            {canMove && (
              <View style={styles.actions}>
                {STOCK_KINDS.map((kind) => (
                  <View key={kind} style={styles.action}>
                    <Button
                      title={t(`staff.stock.actions.${kind}`)}
                      variant={kind === 'stock-in' ? 'primary' : 'secondary'}
                      onPress={() => router.push({ pathname: '/staff/stock/[kind]', params: { kind } })}
                      fullWidth
                    />
                  </View>
                ))}
              </View>
            )}
            <AppText size="subtitle" weight="semibold">
              {t('staff.stock.history')}
            </AppText>
            <ChipGroup options={Object.keys(TYPE_FILTERS).map((f) => ({ value: f, label: t(`staff.stock.filters.${f}`) }))} value={filter} onChange={setFilter} />
          </View>
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  header: { gap: spacing.md, marginBottom: spacing.sm },
  actions: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  action: { flexGrow: 1, flexBasis: 140 },
  row: { borderWidth: 1, borderRadius: radius.lg, paddingHorizontal: spacing.md },
  qty: { alignItems: 'flex-end' },
});
