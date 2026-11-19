import Ionicons from '@expo/vector-icons/Ionicons';
import { Image } from 'expo-image';
import { router } from 'expo-router';
import * as Linking from 'expo-linking';
import { useTranslation } from 'react-i18next';
import { FlatList, StyleSheet, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { CategoryChip, ProductRail, SearchBar } from '@/components/catalogue';
import { AppText, Button, Card, ErrorState, Gradient, LoadingView, Screen } from '@/components/ui';
import { useCategories, useHighlights, useStoreInfo } from '@/hooks/useCatalogue';
import { useHeroStatusBar } from '@/hooks/useHeroStatusBar';
import { queryClient } from '@/lib/queryClient';
import { useAppTheme } from '@/theme/ThemeProvider';
import { CHIP_HIT_SLOP, radius, spacing } from '@/theme/tokens';
import { errorMessage } from '@/utils/errors';
import { showError } from '@/utils/query';

const INDIA_DIALING_CODE = '91';
const LOGO_SIZE = 64;
// Frosted-glass whites drawn on top of the green hero gradient (same in both themes).
const HERO_GLASS = 'rgba(255, 255, 255, 0.12)';
const HERO_GLASS_STRONG = 'rgba(255, 255, 255, 0.35)';
const HERO_MUTED = 'rgba(255, 255, 255, 0.85)';

const openSearch = (params: Record<string, string> = {}) => router.push({ pathname: '/search', params });

export default function CustomerHome() {
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const insets = useSafeAreaInsets();
  useHeroStatusBar();
  const store = useStoreInfo();
  const categories = useCategories();
  const offersEnabled = !!store.data?.offers_enabled;
  const featured = useHighlights('featured');
  const offers = useHighlights('offers', offersEnabled);
  const newArrivals = useHighlights('new');

  if (store.isPending) return <LoadingView />;
  if (showError(store)) return <ErrorState message={errorMessage(store.error, t)} onRetry={() => void store.refetch()} />;

  const s = store.data;
  const refreshing = store.isRefetching || categories.isRefetching || featured.isRefetching || newArrivals.isRefetching;
  const nothingYet =
    categories.isSuccess && featured.isSuccess && newArrivals.isSuccess && !categories.data.length && !newArrivals.data.length;

  return (
    <Screen
      edges={[]}
      refreshing={refreshing}
      onRefresh={() => void queryClient.invalidateQueries({ queryKey: ['public'] })}
    >
      <Gradient name="hero" style={[styles.hero, { paddingTop: insets.top + spacing.xl }]}>
        <View style={[styles.blob, styles.blobLarge]} />
        <View style={[styles.blob, styles.blobSmall]} />
        <View style={styles.header}>
          {s.logo_thumb_url ? (
            <Image source={s.logo_thumb_url} style={styles.logo} contentFit="cover" />
          ) : (
            <View style={[styles.logo, styles.logoFallback]}>
              <Ionicons name="basket" size={28} color={colors.textOnHero} />
            </View>
          )}
          <View style={styles.headerText}>
            <AppText size="small" weight="medium" style={styles.heroMuted}>
              {t('customer.welcome')}
            </AppText>
            <AppText size="heading" weight="bold" color="textOnHero" numberOfLines={2}>
              {s.name}
            </AppText>
            {s.tagline && (
              <AppText size="small" numberOfLines={2} style={styles.heroMuted}>
                {s.tagline}
              </AppText>
            )}
          </View>
        </View>
      </Gradient>

      <View style={styles.searchLift}>
        <SearchBar onPress={() => openSearch()} />
      </View>

      {!!categories.data?.length && (
        <FlatList
          horizontal
          data={categories.data}
          keyExtractor={(c) => c.slug}
          renderItem={({ item, index }) => <CategoryChip category={item} index={index} />}
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
        <Card style={styles.emptyCard}>
          <View style={[styles.emptyIcon, { backgroundColor: colors.primarySoft }]}>
            <Ionicons name="basket" size={34} color={colors.primary} />
          </View>
          <AppText align="center" weight="semibold" size="subtitle">
            {t('catalogue.emptyStore')}
          </AppText>
        </Card>
      ) : (
        <Button title={t('catalogue.browseAll')} variant="secondary" onPress={() => openSearch()} fullWidth />
      )}

      {(s.phone || s.whatsapp || s.hours || s.address) && (
        <Card>
          <AppText size="subtitle" weight="bold">
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
  hero: {
    marginHorizontal: -spacing.lg,
    marginTop: -spacing.lg,
    paddingHorizontal: spacing.xl,
    paddingBottom: spacing.xxxl + spacing.xl,
    borderBottomLeftRadius: radius.xl,
    borderBottomRightRadius: radius.xl,
    overflow: 'hidden',
  },
  blob: { position: 'absolute', borderRadius: 999, backgroundColor: HERO_GLASS },
  blobLarge: { width: 220, height: 220, top: -70, right: -60 },
  blobSmall: { width: 120, height: 120, bottom: -40, left: -30 },
  heroMuted: { color: HERO_MUTED },
  searchLift: { marginTop: -(spacing.xxl + spacing.md) }, // search bar sits half on the hero's edge
  header: { flexDirection: 'row', alignItems: 'center', gap: spacing.lg },
  headerText: { flex: 1, gap: spacing.xxs },
  logo: { width: LOGO_SIZE, height: LOGO_SIZE, borderRadius: radius.lg, borderWidth: 2, borderColor: HERO_GLASS_STRONG },
  logoFallback: { alignItems: 'center', justifyContent: 'center', backgroundColor: HERO_GLASS },
  chips: { gap: spacing.sm, paddingVertical: CHIP_HIT_SLOP, paddingRight: spacing.xl },
  emptyCard: { alignItems: 'center', paddingVertical: spacing.xxl },
  emptyIcon: { width: 72, height: 72, borderRadius: radius.xl, alignItems: 'center', justifyContent: 'center' },
  actions: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md },
  row: { flexDirection: 'row', gap: spacing.md, alignItems: 'flex-start' },
  rowText: { flex: 1, gap: spacing.xxs },
});
