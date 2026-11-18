import Ionicons from '@expo/vector-icons/Ionicons';
import { useMutation } from '@tanstack/react-query';
import { type Href, router } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { Pressable, StyleSheet, View } from 'react-native';

import { notificationApi } from '@/api/staff/endpoints';
import type { AppNotification } from '@/api/staff/types';
import { PagedList } from '@/components/staff/PagedList';
import { AppText, Button, ScreenHeader, toast } from '@/components/ui';
import { useNotifications } from '@/hooks/useStaff';
import { queryClient } from '@/lib/queryClient';
import { routeForNotification } from '@/utils/notificationRoutes';
import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, spacing } from '@/theme/tokens';
import { errorMessage } from '@/utils/errors';
import { formatDateTime } from '@/utils/format';

const ICONS: Record<string, keyof typeof Ionicons.glyphMap> = {
  low_stock: 'trending-down-outline',
  out_of_stock: 'alert-circle-outline',
  expiry_digest: 'hourglass-outline',
};
const DOT = 10;

const refreshNotifications = () => queryClient.invalidateQueries({ queryKey: ['staff'] });

export default function NotificationsScreen() {
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const notifications = useNotifications({});
  const readAll = useMutation({
    mutationFn: notificationApi.markAllRead,
    onSuccess: () => void refreshNotifications(),
    onError: (e) => toast.error(errorMessage(e, t)),
  });

  const open = async (n: AppNotification) => {
    if (!n.read) {
      await notificationApi.markRead(n.id).catch(() => undefined);
      void refreshNotifications();
    }
    const route = routeForNotification({ ...n.data, type: n.type });
    if (route && route !== '/staff/notifications') router.push(route as Href);
  };

  const render = (n: AppNotification) => (
    <Pressable
      accessibilityRole="button"
      onPress={() => void open(n)}
      style={[styles.item, { backgroundColor: n.read ? colors.surface : colors.primarySoft, borderColor: colors.border }]}
    >
      <Ionicons name={ICONS[n.type] ?? 'notifications-outline'} size={24} color={n.type === 'out_of_stock' ? colors.danger : colors.warning} />
      <View style={styles.text}>
        <AppText weight={n.read ? 'medium' : 'bold'}>{n.title}</AppText>
        <AppText size="small" color="textMuted">
          {n.body}
        </AppText>
        <AppText size="caption" color="textMuted">
          {formatDateTime(n.created_at)}
        </AppText>
      </View>
      {!n.read && <View style={[styles.dot, { backgroundColor: colors.primary }]} accessibilityLabel={t('staff.notifications.unread')} />}
    </Pressable>
  );

  return (
    <View style={[styles.root, { backgroundColor: colors.background }]}>
      <ScreenHeader
        title={t('staff.notifications.title')}
        right={
          <Pressable accessibilityRole="button" accessibilityLabel={t('staff.notifications.settings')} onPress={() => router.push('/staff/notification-settings')}>
            <Ionicons name="options-outline" size={24} color={colors.primary} />
          </Pressable>
        }
      />
      <PagedList
        items={notifications.items}
        keyOf={(n) => n.id}
        render={render}
        query={{ ...notifications, hasNextPage: !!notifications.hasNextPage }}
        emptyTitle={t('staff.notifications.empty')}
        emptyBody={t('staff.notifications.emptyHint')}
        emptyIcon="notifications-outline"
        header={
          notifications.items.some((n) => !n.read) ? (
            <Button title={t('staff.notifications.markAllRead')} variant="ghost" onPress={() => readAll.mutate()} loading={readAll.isPending} />
          ) : undefined
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  item: { flexDirection: 'row', gap: spacing.md, padding: spacing.md, borderWidth: 1, borderRadius: radius.lg, alignItems: 'flex-start' },
  text: { flex: 1, gap: spacing.xxs },
  dot: { width: DOT, height: DOT, borderRadius: radius.pill, marginTop: spacing.xs },
});
