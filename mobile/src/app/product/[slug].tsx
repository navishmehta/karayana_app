import Ionicons from '@expo/vector-icons/Ionicons';
import * as Linking from 'expo-linking';
import { useLocalSearchParams } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { ScrollView, StyleSheet, View } from 'react-native';

import { AvailabilityBadge, ImageCarousel, openCategory, PriceTag } from '@/components/catalogue';
import { AppText, Badge, Button, Card, ErrorState, LoadingView, ScreenHeader } from '@/components/ui';
import { useProduct, useStoreInfo } from '@/hooks/useCatalogue';
import { useAppTheme } from '@/theme/ThemeProvider';
import { spacing } from '@/theme/tokens';
import { localizedName } from '@/utils/catalogue';
import { errorMessage } from '@/utils/errors';
import { formatDate } from '@/utils/format';

const MAX_WIDTH = 720;

export default function ProductScreen() {
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const { t, i18n } = useTranslation();
  const { colors } = useAppTheme();
  const product = useProduct(slug);
  const store = useStoreInfo();

  if (product.isPending) return <LoadingView />;
  if (product.isError) {
    return (
      <View style={[styles.root, { backgroundColor: colors.background }]}>
        <ScreenHeader title="" />
        <ErrorState message={errorMessage(product.error, t)} onRetry={() => void product.refetch()} />
      </View>
    );
  }

  const p = product.data;
  const phone = store.data?.phone;

  return (
    <View style={[styles.root, { backgroundColor: colors.background }]}>
      <ScreenHeader title={p.name} />
      <ScrollView contentContainerStyle={styles.scroll}>
        <ImageCarousel images={p.images} />
        <View style={styles.content}>
          <View style={styles.badges}>
            <AvailabilityBadge availability={p.availability} />
            {p.on_offer && <Badge label={t('catalogue.offer')} tone="accent" />}
          </View>
          {p.brand && <AppText color="textMuted">{p.brand}</AppText>}
          <AppText size="title" weight="bold">
            {p.name}
          </AppText>
          <PriceTag product={p} large />
          <AppText size="small" color="textMuted">
            {t('catalogue.perUnit', { unit: p.unit })} · {t('catalogue.inclusiveOfTaxes')}
          </AppText>
          {p.on_offer && p.offer_ends_at && (
            <AppText size="small" color="accent" weight="semibold">
              {t('catalogue.offerEnds', { date: formatDate(p.offer_ends_at) })}
            </AppText>
          )}

          <Card>
            <DetailRow label={t('catalogue.category')} value={localizedName(p.category, i18n.language)} onPress={() => openCategory(p.category.slug)} />
            {p.brand && <DetailRow label={t('catalogue.brand')} value={p.brand} />}
            <DetailRow label={t('catalogue.unit')} value={p.unit} />
            {p.expiry_date && <DetailRow label={t('catalogue.bestBefore')} value={formatDate(p.expiry_date)} />}
          </Card>

          {p.description && (
            <Card>
              <AppText weight="semibold">{t('catalogue.description')}</AppText>
              <AppText>{p.description}</AppText>
            </Card>
          )}

          {phone && (
            <Button
              title={t('catalogue.askStore')}
              variant="secondary"
              icon={<Ionicons name="call-outline" size={18} color={colors.primary} />}
              onPress={() => void Linking.openURL(`tel:${phone}`)}
              fullWidth
            />
          )}
        </View>
      </ScrollView>
    </View>
  );
}

function DetailRow({ label, value, onPress }: { label: string; value: string; onPress?: () => void }) {
  return (
    <View style={styles.detailRow}>
      <AppText color="textMuted">{label}</AppText>
      <AppText
        weight="medium"
        color={onPress ? 'primary' : 'text'}
        onPress={onPress}
        accessibilityRole={onPress ? 'link' : undefined}
        style={styles.detailValue}
      >
        {value}
      </AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  scroll: { paddingBottom: spacing.xxxl },
  content: { width: '100%', maxWidth: MAX_WIDTH, alignSelf: 'center', padding: spacing.lg, gap: spacing.md },
  badges: { flexDirection: 'row', gap: spacing.sm },
  detailRow: { flexDirection: 'row', justifyContent: 'space-between', gap: spacing.md },
  detailValue: { flexShrink: 1, textAlign: 'right' },
});
