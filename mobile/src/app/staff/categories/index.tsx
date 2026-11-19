import Ionicons from '@expo/vector-icons/Ionicons';
import { useMutation } from '@tanstack/react-query';
import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { FlatList, Pressable, StyleSheet, View } from 'react-native';

import { categoryApi } from '@/api/staff/endpoints';
import type { StaffCategory } from '@/api/staff/types';
import { useCan } from '@/auth/permissions';
import { Badge, EmptyState, ErrorState, Fab, ListRow, LoadingView, ScreenHeader, toast } from '@/components/ui';
import { PERMISSIONS } from '@/constants/permissions';
import { refreshAfterChange, useStaffCategories } from '@/hooks/useStaff';
import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, spacing, TOUCH_TARGET } from '@/theme/tokens';
import { errorMessage } from '@/utils/errors';
import { showError } from '@/utils/query';

export default function CategoriesScreen() {
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const categories = useStaffCategories();
  const canCreate = useCan(PERMISSIONS.categoriesCreate);
  const canUpdate = useCan(PERMISSIONS.categoriesUpdate);

  const reorder = useMutation({
    mutationFn: (ids: number[]) => categoryApi.reorder(ids),
    onSuccess: () => void refreshAfterChange(),
    onError: (e) => toast.error(errorMessage(e, t)),
  });

  const move = (list: StaffCategory[], index: number, by: -1 | 1) => {
    const ids = list.map((c) => c.id);
    [ids[index], ids[index + by]] = [ids[index + by], ids[index]];
    reorder.mutate(ids);
  };

  const list = categories.data ?? [];
  const open = (id?: number) => router.push({ pathname: '/staff/categories/form', params: id ? { id: String(id) } : {} });

  return (
    <View style={[styles.root, { backgroundColor: colors.background }]}>
      <ScreenHeader title={t('staff.more.categories')} />
      {categories.isPending ? (
        <LoadingView />
      ) : showError(categories) ? (
        <ErrorState message={errorMessage(categories.error, t)} onRetry={() => void categories.refetch()} />
      ) : (
        <FlatList
          data={list}
          keyExtractor={(c) => String(c.id)}
          contentContainerStyle={styles.content}
          ListEmptyComponent={<EmptyState icon="grid-outline" title={t('staff.categories.empty')} />}
          ListFooterComponent={<View style={styles.fabSpace} />}
          refreshing={categories.isRefetching}
          onRefresh={() => void categories.refetch()}
          renderItem={({ item, index }) => (
            <View style={[styles.row, { backgroundColor: colors.surface, borderColor: colors.border }]}>
              <View style={styles.flex}>
                <ListRow
                  title={item.name}
                  subtitle={[item.name_translations.pa, t('catalogue.productsCount', { count: item.products_count })].filter(Boolean).join(' · ')}
                  below={!item.is_active ? <Badge label={t('staff.common.inactive')} tone="textMuted" /> : undefined}
                  onPress={canUpdate ? () => open(item.id) : undefined}
                />
              </View>
              {canUpdate && (
                <View style={styles.arrows}>
                  <Arrow icon="chevron-up" label={t('staff.categories.moveUp')} disabled={index === 0 || reorder.isPending} onPress={() => move(list, index, -1)} />
                  <Arrow icon="chevron-down" label={t('staff.categories.moveDown')} disabled={index === list.length - 1 || reorder.isPending} onPress={() => move(list, index, 1)} />
                </View>
              )}
            </View>
          )}
        />
      )}
      {canCreate && <Fab label={t('staff.categories.add')} onPress={() => open()} />}
    </View>
  );
}

function Arrow({ icon, label, disabled, onPress }: { icon: 'chevron-up' | 'chevron-down'; label: string; disabled: boolean; onPress: () => void }) {
  const { colors } = useAppTheme();
  return (
    <Pressable accessibilityRole="button" accessibilityLabel={label} disabled={disabled} onPress={onPress} style={styles.arrow}>
      <Ionicons name={icon} size={20} color={disabled ? colors.border : colors.primary} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  content: { width: '100%', maxWidth: 820, alignSelf: 'center', padding: spacing.lg, gap: spacing.sm },
  row: { flexDirection: 'row', alignItems: 'center', borderWidth: 1, borderRadius: radius.lg, paddingLeft: spacing.md },
  flex: { flex: 1 },
  arrows: { justifyContent: 'center' },
  arrow: { width: TOUCH_TARGET, height: TOUCH_TARGET / 1.5, alignItems: 'center', justifyContent: 'center' },
  fabSpace: { height: spacing.xxxl * 2 },
});
