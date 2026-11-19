import { useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ActivityIndicator, FlatList, ScrollView, StyleSheet, View } from 'react-native';

import { AppText, Button, ChipGroup, EmptyState, ErrorState, LoadingView, PickerField, PickerSheet, ScreenHeader, TextField, toast } from '@/components/ui';
import type { ReportData } from '@/api/staff/types';
import { useCan } from '@/auth/permissions';
import { PERMISSIONS } from '@/constants/permissions';
import { useReport, useReports, useStaffCategories } from '@/hooks/useStaff';
import { downloadAndShare } from '@/lib/download';
import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, spacing } from '@/theme/tokens';
import { errorMessage } from '@/utils/errors';
import { showError } from '@/utils/query';
import {
  columnWidth,
  EMPTY_REPORT_FILTERS,
  EXPORT_MIME,
  exportFileName,
  isNumeric,
  type ReportFilterValues,
  reportQuery,
} from '@/utils/reports';

const WITHIN_OPTIONS = ['7', '15', '30', '90'] as const;

export default function ReportScreen() {
  const { key } = useLocalSearchParams<{ key: string }>();
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const info = useReports().data?.find((r) => r.key === key);
  const supported = info?.filters ?? [];
  const canPickCategory = useCan(PERMISSIONS.categoriesView);
  const categories = useStaffCategories({}, canPickCategory && supported.includes('category_id'));
  const [filters, setFilters] = useState<ReportFilterValues>({ ...EMPTY_REPORT_FILTERS, withinDays: key === 'expiry' ? 30 : null });
  const [pickCategory, setPickCategory] = useState(false);
  const [exporting, setExporting] = useState<'csv' | 'xlsx' | null>(null);
  const query = reportQuery(filters, supported);
  const report = useReport(key, query);
  const columns = report.report?.columns ?? [];
  const width = columns.reduce((sum, c) => sum + columnWidth(c.kind, c.key), 0);

  const exportAs = async (format: 'csv' | 'xlsx') => {
    setExporting(format);
    try {
      await downloadAndShare(`/reports/${key}/export`, { ...query, format }, exportFileName(key, format), EXPORT_MIME[format]);
    } catch (error) {
      toast.error(errorMessage(error, t));
    } finally {
      setExporting(null);
    }
  };

  const categoryName = categories.data?.find((c) => c.id === filters.categoryId)?.name;

  return (
    <View style={[styles.root, { backgroundColor: colors.background }]}>
      <ScreenHeader title={info?.label ?? report.report?.label ?? ''} />
      <View style={styles.filters}>
        {supported.includes('category_id') && canPickCategory && (
          <PickerField label={t('staff.products.category')} value={categoryName} placeholder={t('staff.reports.allCategories')} onPress={() => setPickCategory(true)} />
        )}
        {supported.includes('within_days') && (
          <ChipGroup
            options={WITHIN_OPTIONS.map((d) => ({ value: d, label: t('staff.expiry.within', { days: d }) }))}
            value={String(filters.withinDays ?? 30) as (typeof WITHIN_OPTIONS)[number]}
            onChange={(d) => setFilters((f) => ({ ...f, withinDays: Number(d) }))}
          />
        )}
        {supported.includes('date_from') && (
          <View style={styles.pair}>
            <View style={styles.flex}>
              <TextField label={t('staff.reports.from')} placeholder={t('staff.common.dateHint')} value={filters.dateFrom} onChangeText={(v) => setFilters((f) => ({ ...f, dateFrom: v }))} />
            </View>
            <View style={styles.flex}>
              <TextField label={t('staff.reports.to')} placeholder={t('staff.common.dateHint')} value={filters.dateTo} onChangeText={(v) => setFilters((f) => ({ ...f, dateTo: v }))} />
            </View>
          </View>
        )}
        {info?.can_export && (
          <View style={styles.pair}>
            <View style={styles.flex}>
              <Button title={t('staff.reports.exportExcel')} onPress={() => void exportAs('xlsx')} loading={exporting === 'xlsx'} disabled={!!exporting} fullWidth />
            </View>
            <View style={styles.flex}>
              <Button title={t('staff.reports.exportCsv')} variant="secondary" onPress={() => void exportAs('csv')} loading={exporting === 'csv'} disabled={!!exporting} fullWidth />
            </View>
          </View>
        )}
      </View>

      {report.isPending ? (
        <LoadingView />
      ) : showError(report) ? (
        <ErrorState message={errorMessage(report.error, t)} onRetry={() => void report.refetch()} />
      ) : (
        <ScrollView horizontal contentContainerStyle={styles.tableScroll}>
          <View style={[styles.table, { width, backgroundColor: colors.surface, borderColor: colors.border }]}>
            <View style={[styles.row, styles.header, { backgroundColor: colors.surfaceAlt, borderBottomColor: colors.border }]}>
              {columns.map((c) => (
                <AppText key={c.key} size="small" weight="semibold" style={[styles.cell, { width: columnWidth(c.kind, c.key), textAlign: isNumeric(c.kind) ? 'right' : 'left' }]}>
                  {c.label}
                </AppText>
              ))}
            </View>
            <FlatList
              data={report.rows}
              keyExtractor={(_, i) => String(i)}
              renderItem={({ item }) => <TableRow columns={columns} values={item} borderColor={colors.border} />}
              ListEmptyComponent={<EmptyState icon="document-text-outline" title={t('staff.reports.empty')} />}
              ListFooterComponent={
                <>
                  {report.isFetchingNextPage && <ActivityIndicator color={colors.primary} style={styles.loading} />}
                  {!report.hasNextPage && report.report?.totals && <TableRow columns={columns} values={{ ...report.report.totals, [columns[0]?.key ?? '']: report.report.totals[columns[0]?.key ?? ''] ?? t('staff.reports.total') }} borderColor={colors.border} bold />}
                </>
              }
              onEndReached={() => report.hasNextPage && !report.isFetchingNextPage && void report.fetchNextPage()}
              onEndReachedThreshold={0.5}
            />
          </View>
        </ScrollView>
      )}
      {report.report && (
        <AppText size="small" color="textMuted" style={styles.count}>
          {t('staff.reports.rows', { count: report.report.meta.total })}
          {report.report.truncated ? ` · ${t('staff.reports.truncated')}` : ''}
        </AppText>
      )}

      <PickerSheet
        visible={pickCategory}
        title={t('staff.products.category')}
        items={[{ id: 0, label: t('staff.reports.allCategories') }, ...(categories.data ?? []).map((c) => ({ id: c.id, label: c.name }))]}
        selectedId={filters.categoryId ?? 0}
        onClose={() => setPickCategory(false)}
        onSelect={(item) => {
          setFilters((f) => ({ ...f, categoryId: item.id || null }));
          setPickCategory(false);
        }}
      />
    </View>
  );
}

function TableRow({
  columns,
  values,
  borderColor,
  bold,
}: {
  columns: ReportData['columns'];
  values: Record<string, string>;
  borderColor: string;
  bold?: boolean;
}) {
  return (
    <View style={[styles.row, { borderBottomColor: borderColor }]}>
      {columns.map((c) => (
        <AppText
          key={c.key}
          size="small"
          weight={bold ? 'bold' : 'regular'}
          numberOfLines={2}
          style={[styles.cell, { width: columnWidth(c.kind, c.key), textAlign: isNumeric(c.kind) ? 'right' : 'left' }]}
        >
          {values[c.key] ?? ''}
        </AppText>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  filters: { width: '100%', maxWidth: 820, alignSelf: 'center', padding: spacing.lg, gap: spacing.md },
  pair: { flexDirection: 'row', gap: spacing.md },
  flex: { flex: 1 },
  tableScroll: { paddingHorizontal: spacing.lg, paddingBottom: spacing.lg, flexGrow: 1 },
  table: { borderWidth: 1, borderRadius: radius.md, overflow: 'hidden', flex: 1 },
  header: { borderBottomWidth: 1 },
  row: { flexDirection: 'row', borderBottomWidth: StyleSheet.hairlineWidth },
  cell: { paddingHorizontal: spacing.sm, paddingVertical: spacing.sm },
  loading: { padding: spacing.md },
  count: { textAlign: 'center', padding: spacing.sm },
});
