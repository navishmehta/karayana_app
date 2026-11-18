import { useTranslation } from 'react-i18next';
import { View } from 'react-native';

import { SettingsContent } from '@/components/settings/SettingsContent';
import { Screen, ScreenHeader } from '@/components/ui';
import { useAppTheme } from '@/theme/ThemeProvider';

export default function PreferencesScreen() {
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  return (
    <View style={{ flex: 1, backgroundColor: colors.background }}>
      <ScreenHeader title={t('staff.more.preferences')} />
      <Screen edges={[]}>
        <SettingsContent />
      </Screen>
    </View>
  );
}
