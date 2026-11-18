import { useMutation } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { ScrollView, StyleSheet, View } from 'react-native';

import { notificationApi } from '@/api/staff/endpoints';
import type { NotificationPreference } from '@/api/staff/types';
import { AppText, Card, EmptyState, ErrorState, LoadingView, ScreenHeader, SwitchRow, toast } from '@/components/ui';
import { staffKeys, useNotificationPreferences } from '@/hooks/useStaff';
import { queryClient } from '@/lib/queryClient';
import { useAppTheme } from '@/theme/ThemeProvider';
import { spacing } from '@/theme/tokens';
import { errorMessage } from '@/utils/errors';

/** Each staff member chooses which alerts reach them (the admin switches alert types on/off for the store). */
export default function NotificationSettingsScreen() {
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const prefs = useNotificationPreferences();
  const save = useMutation({
    mutationFn: (next: NotificationPreference[]) => notificationApi.savePreferences(next),
    onSuccess: (result) => queryClient.setQueryData(staffKeys.notificationPreferences, result),
    onError: (e) => toast.error(errorMessage(e, t)),
  });

  const update = (type: NotificationPreference['type'], patch: Partial<NotificationPreference>) => {
    if (!prefs.data) return;
    save.mutate(prefs.data.map((p) => (p.type === type ? { ...p, ...patch } : p)));
  };

  return (
    <View style={[styles.root, { backgroundColor: colors.background }]}>
      <ScreenHeader title={t('staff.notifications.settings')} />
      {prefs.isPending ? (
        <LoadingView />
      ) : prefs.isError ? (
        <ErrorState message={errorMessage(prefs.error, t)} onRetry={() => void prefs.refetch()} />
      ) : (
        <ScrollView contentContainerStyle={styles.content}>
          {prefs.data.length === 0 && <EmptyState icon="notifications-off-outline" title={t('staff.notifications.noTypes')} />}
          {prefs.data.map((p) => (
            <Card key={p.type}>
              <AppText weight="semibold">{t(`staff.notifications.types.${p.type}`)}</AppText>
              <SwitchRow label={t('staff.notifications.push')} hint={t('staff.notifications.pushHint')} value={p.push_enabled} onChange={(v) => update(p.type, { push_enabled: v })} disabled={save.isPending} />
              <SwitchRow label={t('staff.notifications.inApp')} value={p.in_app_enabled} onChange={(v) => update(p.type, { in_app_enabled: v })} disabled={save.isPending} />
            </Card>
          ))}
          <AppText size="small" color="textMuted">
            {t('staff.notifications.adminNote')}
          </AppText>
        </ScrollView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  content: { width: '100%', maxWidth: 720, alignSelf: 'center', padding: spacing.lg, gap: spacing.md },
});
