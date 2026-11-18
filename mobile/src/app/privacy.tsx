/** Privacy policy (needed for the app stores). Public, no login. Text lives in the locale files: privacy.sections. */
import { useTranslation } from 'react-i18next';
import { StyleSheet, View } from 'react-native';

import { AppText, Card, Screen, ScreenHeader } from '@/components/ui';
import { PRIVACY_SECTIONS, PRIVACY_UPDATED } from '@/constants/app';
import { useStoreInfo } from '@/hooks/useCatalogue';
import { useAppTheme } from '@/theme/ThemeProvider';

export default function PrivacyScreen() {
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const store = useStoreInfo();
  const storeName = store.data?.name ?? t('common.appName');
  const contact = store.data?.phone ?? store.data?.whatsapp;

  return (
    <View style={[styles.root, { backgroundColor: colors.background }]}>
      <ScreenHeader title={t('privacy.title')} />
      <Screen edges={[]}>
        <AppText color="textMuted">{t('privacy.intro', { store: storeName })}</AppText>
        {PRIVACY_SECTIONS.map((key) => (
          <Card key={key}>
            <AppText weight="semibold">{t(`privacy.sections.${key}.title`)}</AppText>
            <AppText>{t(`privacy.sections.${key}.body`)}</AppText>
          </Card>
        ))}
        {contact && <AppText>{t('privacy.contact', { store: storeName, contact })}</AppText>}
        <AppText size="small" color="textMuted">
          {t('privacy.updated', { date: PRIVACY_UPDATED })}
        </AppText>
      </Screen>
    </View>
  );
}

const styles = StyleSheet.create({ root: { flex: 1 } });
