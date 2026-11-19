import { router } from 'expo-router';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { StyleSheet, View } from 'react-native';

import type { Seller } from '@/api/staff/types';
import { SearchBar } from '@/components/catalogue';
import { PagedList } from '@/components/staff/PagedList';
import { AppText, Badge, ChipGroup, Fab, ListRow, ScreenHeader } from '@/components/ui';
import { SEARCH_DEBOUNCE_MS } from '@/constants/app';
import { useDebouncedValue } from '@/hooks/useDebouncedValue';
import { useSellers } from '@/hooks/useStaff';
import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, spacing } from '@/theme/tokens';

type Status = 'all' | 'active' | 'inactive';

export default function SellersScreen() {
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState<Status>('all');
  const sellers = useSellers({
    search: useDebouncedValue(search, SEARCH_DEBOUNCE_MS) || undefined,
    is_active: status === 'all' ? undefined : status === 'active',
  });

  const render = (s: Seller) => (
    <View style={[styles.row, { backgroundColor: colors.surface, borderColor: colors.border }]}>
      <ListRow
        title={s.name}
        subtitle={`${s.email} · ${t('staff.permissionsCount', { count: s.permissions.length })}`}
        below={!s.is_active ? <Badge label={t('staff.common.inactive')} tone="textMuted" /> : undefined}
        onPress={() => router.push({ pathname: '/staff/sellers/[id]', params: { id: String(s.id) } })}
      />
    </View>
  );

  return (
    <View style={[styles.root, { backgroundColor: colors.background }]}>
      <ScreenHeader title={t('staff.more.sellers')} />
      <PagedList
        items={sellers.items}
        keyOf={(s) => s.id}
        render={render}
        query={{ ...sellers, hasNextPage: !!sellers.hasNextPage }}
        emptyTitle={t('staff.sellers.empty')}
        emptyBody={t('staff.sellers.emptyHint')}
        emptyIcon="people-outline"
        bottomSpace
        header={
          <View style={styles.header}>
            <SearchBar value={search} onChangeText={setSearch} placeholder={t('staff.sellers.searchPlaceholder')} />
            <ChipGroup
              options={(['all', 'active', 'inactive'] as const).map((v) => ({ value: v, label: t(`staff.sellers.filters.${v}`) }))}
              value={status}
              onChange={setStatus}
            />
            {!sellers.isPending && (
              <AppText size="small" color="textMuted">
                {t('staff.sellers.count', { count: sellers.total })}
              </AppText>
            )}
          </View>
        }
      />
      <Fab label={t('staff.sellers.add')} onPress={() => router.push('/staff/sellers/new')} />
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  header: { gap: spacing.md, marginBottom: spacing.sm },
  row: { borderWidth: 1, borderRadius: radius.lg, paddingHorizontal: spacing.md },
});
