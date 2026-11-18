import Ionicons from '@expo/vector-icons/Ionicons';
import { router } from 'expo-router';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { StyleSheet, View } from 'react-native';

import { can, isAdmin } from '@/auth/permissions';
import { useSession } from '@/auth/session';
import { AppText, Badge, Card, ConfirmDialog, EmptyState, ListRow, Screen } from '@/components/ui';
import { PERMISSIONS } from '@/constants/permissions';
import { queryClient } from '@/lib/queryClient';
import { useAppTheme } from '@/theme/ThemeProvider';
import { spacing } from '@/theme/tokens';

type IconName = keyof typeof Ionicons.glyphMap;

export default function MoreScreen() {
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const user = useSession((s) => s.user);
  const logout = useSession((s) => s.logout);
  const [confirming, setConfirming] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);
  if (!user) return null;

  const admin = isAdmin(user);
  const icon = (name: IconName) => <Ionicons name={name} size={22} color={colors.primary} />;
  const links: { show: boolean; title: string; icon: IconName; href: Parameters<typeof router.push>[0] }[] = [
    { show: true, title: t('staff.notifications.title'), icon: 'notifications-outline', href: '/staff/notifications' },
    { show: can(user, PERMISSIONS.reportsView), title: t('staff.more.reports'), icon: 'document-text-outline', href: '/staff/reports' },
    { show: can(user, PERMISSIONS.categoriesView), title: t('staff.more.categories'), icon: 'grid-outline', href: '/staff/categories' },
    { show: admin, title: t('staff.more.sellers'), icon: 'people-outline', href: '/staff/sellers' },
    { show: admin, title: t('staff.more.activity'), icon: 'time-outline', href: '/staff/activity' },
    { show: admin, title: t('staff.more.storeSettings'), icon: 'storefront-outline', href: '/staff/store-settings' },
    { show: true, title: t('staff.more.preferences'), icon: 'language-outline', href: '/staff/preferences' },
    { show: true, title: t('staff.viewAsCustomer'), icon: 'eye-outline', href: '/' },
  ];

  return (
    <Screen>
      <AppText size="heading" weight="bold">
        {t('staff.tabs.more')}
      </AppText>
      <Card>
        <AppText size="subtitle" weight="semibold">
          {user.name}
        </AppText>
        <AppText color="textMuted">{user.email}</AppText>
        <Badge label={admin ? t('staff.roleAdmin') : t('staff.roleSeller')} />
      </Card>
      {!admin && (
        <Card>
          {user.permissions.length === 0 ? (
            <EmptyState icon="lock-closed-outline" title={t('staff.noAccessTitle')} body={t('staff.noAccessBody')} />
          ) : (
            <>
              <AppText weight="semibold">{t('staff.more.yourAccess')}</AppText>
              {user.permissions.map((permission) => (
                <View key={permission} style={styles.permission}>
                  <Ionicons name="checkmark-circle" size={18} color={colors.success} />
                  <AppText size="small">{t(`staff.permissionLabels.${permission}`, { defaultValue: permission })}</AppText>
                </View>
              ))}
              <AppText size="small" color="textMuted">
                {t('staff.more.askAdmin')}
              </AppText>
            </>
          )}
        </Card>
      )}
      <Card>
        {links
          .filter((l) => l.show)
          .map((l) => (
            <ListRow key={l.title} title={l.title} left={icon(l.icon)} onPress={() => router.push(l.href)} />
          ))}
      </Card>
      <Card>
        <ListRow title={t('auth.logout')} left={<Ionicons name="log-out-outline" size={22} color={colors.danger} />} danger onPress={() => setConfirming(true)} chevron={false} />
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
          queryClient.removeQueries({ queryKey: ['staff'] }); // never show one user's data to the next
          setLoggingOut(false);
          setConfirming(false);
          router.replace('/');
        }}
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  permission: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
});
