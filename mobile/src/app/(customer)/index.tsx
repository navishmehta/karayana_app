import Ionicons from '@expo/vector-icons/Ionicons';
import { Image } from 'expo-image';
import { router } from 'expo-router';
import * as Linking from 'expo-linking';
import { useTranslation } from 'react-i18next';
import { FlatList, StyleSheet, View } from 'react-native';

import { CategoryChip, ProductRail, SearchBar } from '@/components/catalogue';
import { AppText, Button, Card, ErrorState, LoadingView, Screen } from '@/components/ui';
import { useCategories, useHighlights, useStoreInfo } from '@/hooks/useCatalogue';
import { queryClient } from '@/lib/queryClient';
import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, spacing } from '@/theme/tokens';
import { errorMessage } from '@/utils/errors';

const INDIA_DIALING_CODE = '91';
const LOGO_SIZE = 56;

const openSearch = (params: Record<string, string> = {}) => router.push({ pathname: '/search', params });

export default function CustomerHome() {
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const store = useStoreInfo();
  const categories = useCategories();
  const offersEnabled = !!store.data?.offers_enabled;
  const featured = useHighlights('featured');
  const offers = useHighlights('offers', offersEnabled);
  const newArrivals = useHighlights('new');

  if (store.isPending) return <LoadingView />;
  if (store.isError) return <ErrorState message={errorMessage(store.error, t)} onRetry={() => void store.refetch()} />;

  const s = store.data;
  const refreshing = store.isRefetching || categories.isRefetching || featured.isRefetching || newArrivals.isRefetching;
  const nothingYet =
    categories.isSuccess && featured.isSuccess && newArrivals.isSuccess && !categories.data.length && !newArrivals.data.length;

  return (
    <Screen refreshing={refreshing} onRefresh={() => void queryClient.invalidateQueries({ queryKey: ['public'] })}>
      <View style={styles.header}>
        {s.logo_thumb_url ? (
          <Image source={s.logo_thumb_url} style={styles.logo} contentFit="cover" />
        ) : (
          <View style={[styles.logo, styles.logoFallback, { backgroundColor: colors.primary }]}>
            <Ionicons name="storefront" size={28} color={colors.textOnPrimary} />
          </View>
        )}
        <View style={styles.headerText}>
          <AppText size="title" weight="bold" numberOfLines={2}>
            {s.name}
          </AppText>
          {s.tagline && (
            <AppText size="small" color="textMuted" numberOfLines={1}>
              {s.tagline}
            </AppText>
          )}
        </View>
      </View>

      <SearchBar onPress={() => openSearch()} />

      {!!categories.data?.length && (
        <FlatList
          horizontal
          data={categories.data}
          keyExtractor={(c) => c.slug}
          renderItem={({ item }) => <CategoryChip category={item} />}
          contentContainerStyle={styles.chips}
          showsHorizontalScrollIndicator={false}
        />
      )}

      {offersEnabled && (
        <ProductRail
          title={t('catalogue.specialOffers')}
          products={offers.data ?? []}
          onSeeAll={() => openSearch({ on_offer: '1', sort: 'price_asc' })}
        />
      )}
      <ProductRail title={t('catalogue.featured')} products={featured.data ?? []} onSeeAll={() => openSearch({ featured: '1' })} />
      <ProductRail title={t('catalogue.newArrivals')} products={newArrivals.data ?? []} onSeeAll={() => openSearch({ sort: 'newest' })} />

      {nothingYet ? (
        <Card>
          <AppText align="center" color="textMuted">
            {t('catalogue.emptyStore')}
          </AppText>
        </Card>
      ) : (
        <Button title={t('catalogue.browseAll')} variant="secondary" onPress={() => openSearch()} fullWidth />
      )}

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
  header: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  headerText: { flex: 1, gap: spacing.xxs },
  logo: { width: LOGO_SIZE, height: LOGO_SIZE, borderRadius: radius.lg },
  logoFallback: { alignItems: 'center', justifyContent: 'center' },
  chips: { gap: spacing.sm },
  actions: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md },
  row: { flexDirection: 'row', gap: spacing.md, alignItems: 'flex-start' },
  rowText: { flex: 1, gap: spacing.xxs },
});
