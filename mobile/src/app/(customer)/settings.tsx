import Ionicons from '@expo/vector-icons/Ionicons';
import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';

import { useSession } from '@/auth/session';
import { SettingsContent } from '@/components/settings/SettingsContent';
import { AppText, Button, Card, Screen } from '@/components/ui';
import { useAppTheme } from '@/theme/ThemeProvider';

export default function CustomerSettings() {
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const isStaff = useSession((s) => s.status === 'staff');

  return (
    <Screen>
      <SettingsContent>
        <Card>
          <AppText weight="semibold">{t('settings.staff')}</AppText>
          <Button
            title={isStaff ? t('settings.openStaffPanel') : t('settings.staffLogin')}
            variant="secondary"
            icon={<Ionicons name="lock-closed-outline" size={18} color={colors.primary} />}
            onPress={() => router.push(isStaff ? '/staff' : '/login')}
          />
        </Card>
      </SettingsContent>
    </Screen>
  );
}
