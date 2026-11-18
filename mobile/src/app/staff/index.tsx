import Ionicons from '@expo/vector-icons/Ionicons';
import { router } from 'expo-router';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { StyleSheet, View } from 'react-native';

import { isAdmin } from '@/auth/permissions';
import { useSession } from '@/auth/session';
import { AppText, Badge, Button, Card, ConfirmDialog, EmptyState, Screen } from '@/components/ui';
import { useAppTheme } from '@/theme/ThemeProvider';
import { spacing } from '@/theme/tokens';

export default function StaffHome() {
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const user = useSession((s) => s.user);
  const logout = useSession((s) => s.logout);
  const [confirming, setConfirming] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);

  if (!user) return null;
  const admin = isAdmin(user);

  return (
    <Screen edges={['top', 'bottom']}>
      <View style={styles.header}>
        <AppText size="title" weight="bold">
          {t('staff.greeting', { name: user.name })}
        </AppText>
        <View style={styles.badges}>
          <Badge label={admin ? t('staff.roleAdmin') : t('staff.roleSeller')} />
          <Badge label={t('staff.permissionsCount', { count: user.permissions.length })} tone="textMuted" />
        </View>
      </View>

      {!admin && user.permissions.length === 0 ? (
        <Card>
          <EmptyState icon="lock-closed-outline" title={t('staff.noAccessTitle')} body={t('staff.noAccessBody')} />
        </Card>
      ) : (
        <Card>
          <AppText color="textMuted">{t('staff.panelNote')}</AppText>
        </Card>
      )}

      <Card>
        <Button
          title={t('staff.viewAsCustomer')}
          variant="secondary"
          icon={<Ionicons name="storefront-outline" size={18} color={colors.primary} />}
          onPress={() => router.push('/')}
        />
        <Button
          title={t('common.settings')}
          variant="secondary"
          icon={<Ionicons name="settings-outline" size={18} color={colors.primary} />}
          onPress={() => router.push('/settings')}
        />
        <Button title={t('auth.logout')} variant="ghost" onPress={() => setConfirming(true)} />
      </Card>

      <ConfirmDialog
        visible={confirming}
        title={t('auth.logoutConfirm')}
        confirmLabel={t('auth.logout')}
        destructive
        loading={loggingOut}
        onCancel={() => setConfirming(false)}
        onConfirm={async () => {
          setLoggingOut(true);
          await logout();
          setLoggingOut(false);
          setConfirming(false);
          router.replace('/');
        }}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  header: { gap: spacing.sm },
  badges: { flexDirection: 'row', gap: spacing.sm, flexWrap: 'wrap' },
});
