import Ionicons from '@expo/vector-icons/Ionicons';
import { useQuery } from '@tanstack/react-query';
import { Image } from 'expo-image';
import * as Linking from 'expo-linking';
import { useTranslation } from 'react-i18next';
import { StyleSheet, View } from 'react-native';

import { publicApi } from '@/api/endpoints';
import { AppText, Button, Card, ErrorState, LoadingView, Screen } from '@/components/ui';
import { queryKeys } from '@/lib/queryClient';
import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, spacing } from '@/theme/tokens';
import { errorMessage } from '@/utils/errors';

const INDIA_DIALING_CODE = '91';
const LOGO_SIZE = 72;

/** Customer home: store details from the admin's settings. Phase 7 adds categories, offers and products. */
export default function CustomerHome() {
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const store = useQuery({ queryKey: queryKeys.publicStore, queryFn: publicApi.store, select: (r) => r.data });

  if (store.isPending) return <LoadingView />;
  if (store.isError) return <ErrorState message={errorMessage(store.error, t)} onRetry={() => void store.refetch()} />;

  const s = store.data;
  return (
    <Screen refreshing={store.isRefetching} onRefresh={() => void store.refetch()}>
      <View style={[styles.hero, { backgroundColor: colors.primarySoft }]}>
        {s.logo_thumb_url ? (
          <Image source={s.logo_thumb_url} style={styles.logo} contentFit="cover" accessibilityIgnoresInvertColors />
        ) : (
          <View style={[styles.logo, styles.logoFallback, { backgroundColor: colors.primary }]}>
            <Ionicons name="storefront" size={36} color={colors.textOnPrimary} />
          </View>
        )}
        <AppText color="textMuted">{t('customer.welcome')}</AppText>
        <AppText size="heading" weight="bold" align="center">
          {s.name}
        </AppText>
        {s.tagline && (
          <AppText align="center" color="textMuted">
            {s.tagline}
          </AppText>
        )}
      </View>

      {(s.phone || s.whatsapp || s.hours || s.address) && (
        <Card>
          <AppText size="subtitle" weight="semibold">
            {t('customer.contact')}
          </AppText>
          {s.hours && <InfoRow icon="time-outline" label={t('customer.hours')} value={s.hours} />}
          {s.address && <InfoRow icon="location-outline" label={t('customer.address')} value={s.address} />}
          <View style={styles.actions}>
            {s.phone && (
              <Button
                title={t('common.call')}
                variant="secondary"
                icon={<Ionicons name="call-outline" size={18} color={colors.primary} />}
                onPress={() => void Linking.openURL(`tel:${s.phone}`)}
              />
            )}
            {s.whatsapp && (
              <Button
                title={t('common.whatsapp')}
                variant="secondary"
                icon={<Ionicons name="logo-whatsapp" size={18} color={colors.primary} />}
                onPress={() => void Linking.openURL(`https://wa.me/${INDIA_DIALING_CODE}${s.whatsapp}`)}
              />
            )}
          </View>
        </Card>
      )}
    </Screen>
  );
}

function InfoRow({ icon, label, value }: { icon: keyof typeof Ionicons.glyphMap; label: string; value: string }) {
  const { colors } = useAppTheme();
  return (
    <View style={styles.row}>
      <Ionicons name={icon} size={20} color={colors.textMuted} />
      <View style={styles.rowText}>
        <AppText size="small" color="textMuted">
          {label}
        </AppText>
        <AppText>{value}</AppText>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  hero: { alignItems: 'center', gap: spacing.xs, padding: spacing.xl, borderRadius: radius.xl },
  logo: { width: LOGO_SIZE, height: LOGO_SIZE, borderRadius: radius.lg, marginBottom: spacing.sm },
  logoFallback: { alignItems: 'center', justifyContent: 'center' },
  actions: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md },
  row: { flexDirection: 'row', gap: spacing.md, alignItems: 'flex-start' },
  rowText: { flex: 1, gap: spacing.xxs },
});
