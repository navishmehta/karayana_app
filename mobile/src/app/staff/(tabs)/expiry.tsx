import { useMutation } from '@tanstack/react-query';
import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { inventoryApi } from '@/api/staff/endpoints';
import type { ExpiryBatch } from '@/api/staff/types';
import { useCan } from '@/auth/permissions';
import { BatchDatesDialog } from '@/components/staff/BatchDatesDialog';
import { KpiTile } from '@/components/staff/KpiTile';
import { PagedList } from '@/components/staff/PagedList';
import { ExpiryBadge } from '@/components/staff/StatusBadges';
import { AppText, Button, ChipGroup, ConfirmDialog, toast } from '@/components/ui';
import { PERMISSIONS } from '@/constants/permissions';
import { refreshAfterChange, useExpiryBatches, useExpirySummary } from '@/hooks/useStaff';
import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, spacing } from '@/theme/tokens';
import { errorMessage } from '@/utils/errors';
import { formatDate, formatMoney, formatQuantity } from '@/utils/format';
import { newRequestKey } from '@/utils/forms';

type Status = 'expiring' | 'expired' | 'all';
const STATUSES: Status[] = ['expiring', 'expired', 'all'];

export default function ExpiryScreen() {
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const params = useLocalSearchParams<{ status?: string }>();
  const canView = useCan(PERMISSIONS.expiryView);
  const canWriteOff = useCan(PERMISSIONS.stockUpdate);
  const canEditDates = useCan(PERMISSIONS.expiryUpdate);
  const [status, setStatus] = useState<Status>(STATUSES.includes(params.status as Status) ? (params.status as Status) : 'expiring');
  const [withinDays, setWithinDays] = useState<number | undefined>(undefined);
  const [writeOff, setWriteOff] = useState<ExpiryBatch | null>(null);
  const [editing, setEditing] = useState<ExpiryBatch | null>(null);

  const summary = useExpirySummary(canView);
  const batches = useExpiryBatches({ status, within_days: status === 'expiring' ? withinDays : undefined }, canView);

  const writeOffMutation = useMutation({
    mutationFn: (batch: ExpiryBatch) => inventoryApi.writeOff([batch.id], newRequestKey()),
    onSuccess: () => {
      void refreshAfterChange();
      toast.success(t('staff.expiry.writtenOff'));
      setWriteOff(null);
    },
    onError: (e) => toast.error(errorMessage(e, t)),
  });

  const render = (b: ExpiryBatch) => (
    <View style={[styles.card, { backgroundColor: colors.surface, borderColor: colors.border }]}>
      <View style={styles.top}>
        <AppText weight="semibold" style={styles.flex} onPress={() => router.push({ pathname: '/staff/product/[id]', params: { id: String(b.product.id) } })}>
          {b.product.name}
        </AppText>
        <ExpiryBadge bucket={b.bucket} days={b.days_to_expiry} />
      </View>
      <AppText size="small" color="textMuted">
        {[
          t('staff.expiry.batchLabel', { number: b.batch_number ?? b.id }),
          formatQuantity(b.quantity_remaining, b.unit),
          t('staff.products.expiresOn', { date: formatDate(b.expiry_date) }),
          b.category.name,
          b.purchase_price !== undefined ? formatMoney(b.purchase_price) : null,
        ]
          .filter(Boolean)
          .join(' · ')}
      </AppText>
      {(canEditDates || (canWriteOff && b.bucket === 'expired')) && (
        <View style={styles.actions}>
          {canEditDates && <Button title={t('staff.expiry.editDates')} variant="ghost" onPress={() => setEditing(b)} />}
          {canWriteOff && b.bucket === 'expired' && <Button title={t('staff.expiry.writeOff')} variant="danger" onPress={() => setWriteOff(b)} />}
        </View>
      )}
    </View>
  );

  return (
    <SafeAreaView edges={['top']} style={[styles.root, { backgroundColor: colors.background }]}>
      <PagedList
        items={batches.items}
        keyOf={(b) => b.id}
        render={render}
        query={{ ...batches, hasNextPage: !!batches.hasNextPage }}
        emptyTitle={status === 'expired' ? t('staff.expiry.noneExpired') : t('staff.expiry.empty')}
        emptyIcon="hourglass-outline"
        header={
          <View style={styles.header}>
            <AppText size="heading" weight="bold">
              {t('staff.tabs.expiry')}
            </AppText>
            {summary.data && (
              <View style={styles.tiles}>
                {summary.data.buckets.map((bucket) => (
                  <KpiTile
                    key={bucket.key}
                    icon={bucket.days === null ? 'close-circle-outline' : 'hourglass-outline'}
                    tone={bucket.days === null ? 'danger' : 'warning'}
                    label={bucket.days === null ? t('staff.expiry.expired') : t('staff.expiry.within', { days: bucket.days })}
                    value={String(bucket.batches)}
                    onPress={() => {
                      setStatus(bucket.days === null ? 'expired' : 'expiring');
                      setWithinDays(bucket.days ?? undefined);
                    }}
                  />
                ))}
              </View>
            )}
            <ChipGroup
              options={STATUSES.map((s) => ({ value: s, label: t(`staff.expiry.filters.${s}`) }))}
              value={status}
              onChange={(s) => {
                setStatus(s);
                setWithinDays(undefined);
              }}
            />
            {status === 'expiring' && withinDays !== undefined && (
              <AppText size="small" color="textMuted">
                {t('staff.expiry.within', { days: withinDays })}
              </AppText>
            )}
          </View>
        }
      />
      <ConfirmDialog
        visible={!!writeOff}
        title={writeOff ? t('staff.expiry.writeOffConfirm', { qty: formatQuantity(writeOff.quantity_remaining, writeOff.unit), name: writeOff.product.name }) : ''}
        confirmLabel={t('staff.expiry.writeOff')}
        destructive
        loading={writeOffMutation.isPending}
        onCancel={() => setWriteOff(null)}
        onConfirm={() => writeOff && writeOffMutation.mutate(writeOff)}
      />
      <BatchDatesDialog batch={editing} onClose={() => setEditing(null)} />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  header: { gap: spacing.md, marginBottom: spacing.sm },
  tiles: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  card: { borderWidth: 1, borderRadius: radius.lg, padding: spacing.md, gap: spacing.xs },
  top: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  flex: { flex: 1 },
  actions: { flexDirection: 'row', justifyContent: 'flex-end', gap: spacing.sm },
});
