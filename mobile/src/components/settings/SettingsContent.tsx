/** Language and theme choices, shared by the customer and staff settings screens. */
import Constants from 'expo-constants';
import { useTranslation } from 'react-i18next';

import { AppText, Card, SegmentedControl } from '@/components/ui';
import { LANGUAGES, type LanguageCode, type ThemePreference } from '@/constants/app';
import { currentLanguage, setLanguage } from '@/i18n';
import { useAppTheme } from '@/theme/ThemeProvider';

export function SettingsContent({ children }: { children?: React.ReactNode }) {
  const { t } = useTranslation();
  const { preference, setPreference } = useAppTheme();

  const themeOptions: { value: ThemePreference; label: string }[] = [
    { value: 'system', label: t('settings.themeSystem') },
    { value: 'light', label: t('settings.themeLight') },
    { value: 'dark', label: t('settings.themeDark') },
  ];
  const languageOptions = LANGUAGES.map((l) => ({ value: l.code as LanguageCode, label: l.nativeName }));

  return (
    <>
      <AppText size="heading" weight="bold">
        {t('settings.title')}
      </AppText>
      <Card>
        <AppText weight="semibold">{t('settings.language')}</AppText>
        <SegmentedControl
          accessibilityLabel={t('settings.language')}
          options={languageOptions}
          value={currentLanguage()}
          onChange={(code) => void setLanguage(code)}
        />
      </Card>
      <Card>
        <AppText weight="semibold">{t('settings.theme')}</AppText>
        <SegmentedControl
          accessibilityLabel={t('settings.theme')}
          options={themeOptions}
          value={preference}
          onChange={setPreference}
        />
      </Card>
      {children}
      <AppText size="small" color="textMuted" align="center">
        {t('common.appName')} · {t('settings.version', { version: Constants.expoConfig?.version ?? '1.0.0' })}
      </AppText>
    </>
  );
}
