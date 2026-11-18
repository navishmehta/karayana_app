import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { StyleSheet, View } from 'react-native';

import type { Activity } from '@/api/staff/types';
import { PagedList } from '@/components/staff/PagedList';
import { ChipGroup, ListRow, ScreenHeader } from '@/components/ui';
import { useActivity } from '@/hooks/useStaff';
import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, spacing } from '@/theme/tokens';
import { formatDateTime } from '@/utils/format';

/** Groups match the first part of each action, e.g. "stock.in" -> stock. */
const GROUPS = ['all', 'auth', 'sellers', 'products', 'categories', 'stock', 'settings'] as const;

export default function ActivityScreen() {
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const [group, setGroup] = useState<(typeof GROUPS)[number]>('all');
  const activity = useActivity({ group: group === 'all' ? undefined : group });

  const render = (a: Activity) => (
    <View style={[styles.row, { backgroundColor: colors.surface, borderColor: colors.border }]}>
      <ListRow
        title={a.description}
        subtitle={[a.user?.name ?? t('staff.activity.system'), formatDateTime(a.created_at), a.ip_address].filter(Boolean).join(' · ')}
        chevron={false}
      />
    </View>
  );

  return (
    <View style={[styles.root, { backgroundColor: colors.background }]}>
      <ScreenHeader title={t('staff.more.activity')} />
      <PagedList
        items={activity.items}
        keyOf={(a) => a.id}
        render={render}
        query={{ ...activity, hasNextPage: !!activity.hasNextPage }}
        emptyTitle={t('staff.activity.empty')}
        emptyIcon="time-outline"
        header={
          <View style={styles.header}>
            <ChipGroup options={GROUPS.map((g) => ({ value: g, label: t(`staff.activity.groups.${g}`) }))} value={group} onChange={setGroup} />
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  header: { marginBottom: spacing.sm },
  row: { borderWidth: 1, borderRadius: radius.lg, paddingHorizontal: spacing.md },
});
