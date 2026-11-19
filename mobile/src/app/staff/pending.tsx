/** Stock changes saved on this phone while offline, waiting to be sent (or refused by the server). */
import Ionicons from '@expo/vector-icons/Ionicons';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { StyleSheet, View } from 'react-native';

import { AppText, Button, Card, ConfirmDialog, EmptyState, Screen, ScreenHeader } from '@/components/ui';
import { useIsOnline } from '@/lib/network';
import { type QueuedChange, useOfflineQueue } from '@/lib/offlineQueue';
import { useAppTheme } from '@/theme/ThemeProvider';
import { spacing } from '@/theme/tokens';
import { formatDateTime } from '@/utils/format';

export default function PendingChangesScreen() {
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const online = useIsOnline();
  const { items, syncing, sync } = useOfflineQueue();
  const [discarding, setDiscarding] = useState<QueuedChange | null>(null);

  return (
    <View style={[styles.root, { backgroundColor: colors.background }]}>
      <ScreenHeader title={t('offline.screenTitle')} />
      <Screen edges={[]}>
        {!items.length ? (
          <EmptyState icon="cloud-done-outline" title={t('offline.empty')} />
        ) : (
          <>
            <AppText color="textMuted">{online ? t('offline.explainOnline') : t('offline.explainOffline')}</AppText>
            <Button
              title={t('offline.syncNow')}
              icon={<Ionicons name="cloud-upload-outline" size={18} color={colors.textOnPrimary} />}
              onPress={() => void sync()}
              loading={syncing}
              disabled={!online}
              fullWidth
            />
            {items.map((item) => (
              <Card key={item.key}>
                <AppText weight="semibold">{item.label}</AppText>
                <AppText size="small" color="textMuted">
                  {t('offline.savedAt', { time: formatDateTime(item.createdAt) })}
                </AppText>
                {item.error ? (
                  <>
                    <AppText size="small" color="danger">
                      {t('offline.refused', { reason: item.error })}
                    </AppText>
                    <View style={styles.actions}>
                      <Button title={t('offline.retry')} variant="secondary" onPress={() => useOfflineQueue.getState().retry(item.key)} />
                      <Button title={t('offline.discard')} variant="ghost" onPress={() => setDiscarding(item)} />
                    </View>
                  </>
                ) : (
                  <View style={styles.status}>
                    <Ionicons name="time-outline" size={16} color={colors.warning} />
                    <AppText size="small" color="warning">
                      {online ? t('offline.sending') : t('offline.waiting')}
                    </AppText>
                  </View>
                )}
              </Card>
            ))}
          </>
        )}
      </Screen>
      <ConfirmDialog
        visible={!!discarding}
        title={t('offline.discardConfirm')}
        confirmLabel={t('offline.discard')}
        destructive
        onCancel={() => setDiscarding(null)}
        onConfirm={() => {
          if (discarding) useOfflineQueue.getState().remove(discarding.key);
          setDiscarding(null);
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  actions: { flexDirection: 'row', gap: spacing.sm, flexWrap: 'wrap' },
  status: { flexDirection: 'row', alignItems: 'center', gap: spacing.xs },
});
