import { Redirect, router } from 'expo-router';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { StyleSheet, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { dashboardLinks } from '@/auth/access';
import { can, isAdmin } from '@/auth/permissions';
import { useSession } from '@/auth/session';
import { firstAllowedTab } from '@/auth/staffTabs';
import { BarList, DailyColumns } from '@/components/staff/Charts';
import { KpiTile } from '@/components/staff/KpiTile';
import { NotificationBell } from '@/components/staff/NotificationBell';
import { AppText, Card, EmptyState, ErrorState, Gradient, ListRow, LoadingView, Screen, SegmentedControl } from '@/components/ui';
import { PERMISSIONS } from '@/constants/permissions';
import { useHeroStatusBar } from '@/hooks/useHeroStatusBar';
import { useDashboard } from '@/hooks/useStaff';
import { radius, spacing } from '@/theme/tokens';
import { errorMessage } from '@/utils/errors';
import { formatDate, formatDateTime, formatMoney, formatQuantity } from '@/utils/format';

const CHART_DAYS = ['7', '30'] as const;
const TOP_CATEGORIES = 6;
// Frosted-glass whites on the green hero (same in both themes).
const HERO_GLASS = 'rgba(255, 255, 255, 0.14)';
const HERO_MUTED = 'rgba(255, 255, 255, 0.85)';

export default function DashboardScreen() {
  const { t } = useTranslation();
  const user = useSession((s) => s.user);
  const allowed = can(user, PERMISSIONS.dashboardView);
  const [days, setDays] = useState<(typeof CHART_DAYS)[number]>('7');
  const dashboard = useDashboard(Number(days), allowed);
  const insets = useSafeAreaInsets();
  useHeroStatusBar();

  if (!user) return null;
  if (!allowed) {
    const landing = firstAllowedTab(user);
    if (landing.name !== 'index') return <Redirect href={landing.href} />;
  }
  if (dashboard.isPending) return <LoadingView />;
  if (dashboard.isError) return <ErrorState message={errorMessage(dashboard.error, t)} onRetry={() => void dashboard.refetch()} />;

  const d = dashboard.data;
  const links = dashboardLinks(user);
  const openProducts = (params: Record<string, string> = {}) => router.push({ pathname: '/staff/products', params });

  return (
    <Screen edges={[]} refreshing={dashboard.isRefetching} onRefresh={() => void dashboard.refetch()}>
      <Gradient name="hero" style={[styles.hero, { paddingTop: insets.top + spacing.xl }]}>
        <View style={[styles.blob, styles.blobLarge]} />
        <View style={[styles.blob, styles.blobSmall]} />
        <View style={styles.headerRow}>
          <View style={styles.header}>
            <AppText size="small" weight="medium" style={styles.heroMuted}>
              {formatDate(new Date().toISOString())}
            </AppText>
            <AppText size="heading" weight="bold" color="textOnHero">
              {t('staff.greeting', { name: user.name })}
            </AppText>
            <View style={styles.rolePill}>
              <AppText size="caption" weight="semibold" color="textOnHero">
                {isAdmin(user) ? t('staff.roleAdmin') : t('staff.roleSeller')}
              </AppText>
            </View>
          </View>
          <NotificationBell onHero />
        </View>
      </Gradient>

      <View style={styles.tiles}>
        <KpiTile label={t('staff.dashboard.products')} value={String(d.products_total)} icon="cube-outline" onPress={links.products ? () => openProducts() : undefined} />
        <KpiTile
          label={t('staff.dashboard.categories')}
          value={String(d.categories_total)}
          icon="grid-outline"
          onPress={links.categories ? () => router.push('/staff/categories') : undefined}
        />
        {d.sellers_total !== undefined && (
          <KpiTile label={t('staff.dashboard.sellers')} value={String(d.sellers_total)} icon="people-outline" onPress={() => router.push('/staff/sellers')} />
        )}
        {d.stock && (
          <>
            <KpiTile label={t('staff.dashboard.totalStock')} value={formatQuantity(d.stock.total_quantity)} icon="layers-outline" />
            <KpiTile label={t('staff.dashboard.lowStock')} value={String(d.stock.low_stock)} icon="trending-down-outline" tone="warning" onPress={() => openProducts({ filter: 'low_stock' })} />
            <KpiTile label={t('staff.dashboard.outOfStock')} value={String(d.stock.out_of_stock)} icon="alert-circle-outline" tone="danger" onPress={() => openProducts({ filter: 'out_of_stock' })} />
          </>
        )}
        {d.expiry && (
          <>
            <KpiTile
              label={t('staff.dashboard.expiringSoon', { days: d.expiry.expiring_within_days })}
              value={String(d.expiry.expiring_batches)}
              icon="hourglass-outline"
              tone="warning"
              onPress={() => router.push({ pathname: '/staff/expiry', params: { status: 'expiring' } })}
            />
            <KpiTile label={t('staff.dashboard.expired')} value={String(d.expiry.expired_batches)} icon="close-circle-outline" tone="danger" onPress={() => router.push({ pathname: '/staff/expiry', params: { status: 'expired' } })} />
          </>
        )}
        {d.value?.purchase_cost !== undefined && (
          <KpiTile label={t('staff.dashboard.purchaseValue')} value={formatMoney(d.value.purchase_cost)} icon="wallet-outline" />
        )}
        {d.value?.selling_value !== undefined && (
          <KpiTile label={t('staff.dashboard.sellingValue')} value={formatMoney(d.value.selling_value)} icon="cash-outline" tone="success" />
        )}
      </View>

      {d.movements && (
        <Card>
          <View style={styles.cardHeader}>
            <AppText size="subtitle" weight="semibold" style={styles.flex}>
              {t('staff.dashboard.movements')}
            </AppText>
            <View style={styles.daysToggle}>
              <SegmentedControl
                accessibilityLabel={t('staff.dashboard.movements')}
                options={CHART_DAYS.map((v) => ({ value: v, label: t(`staff.dashboard.last${v}`) }))}
                value={days}
                onChange={setDays}
              />
            </View>
          </View>
          <DailyColumns
            inLabel={t('staff.dashboard.stockIn')}
            outLabel={t('staff.dashboard.stockOut')}
            days={d.movements.map((m) => ({ label: formatDate(m.day).slice(0, 5), in: Number(m.stock_in), out: Number(m.stock_out) }))}
          />
        </Card>
      )}

      {!!d.stock_by_category?.length && (
        <Card>
          <AppText size="subtitle" weight="semibold">
            {t('staff.dashboard.stockByCategory')}
          </AppText>
          <BarList rows={d.stock_by_category.slice(0, TOP_CATEGORIES).map((c) => ({ label: c.name, value: Number(c.quantity) }))} />
        </Card>
      )}

      {d.recent_products && (
        <Card>
          <AppText size="subtitle" weight="semibold">
            {t('staff.dashboard.recentProducts')}
          </AppText>
          {d.recent_products.length ? (
            d.recent_products.map((p) => (
              <ListRow
                key={p.id}
                title={p.name}
                subtitle={`${p.category.name} · ${formatDate(p.created_at)}`}
                onPress={() => router.push({ pathname: '/staff/product/[id]', params: { id: String(p.id) } })}
              />
            ))
          ) : (
            <AppText color="textMuted">{t('staff.products.empty')}</AppText>
          )}
        </Card>
      )}

      {d.recent_movements && (
        <Card>
          <AppText size="subtitle" weight="semibold">
            {t('staff.dashboard.recentActivity')}
          </AppText>
          {d.recent_movements.length ? (
            d.recent_movements.map((m) => (
              <ListRow
                key={m.id}
                title={`${m.product.name} · ${t(`staff.stock.types.${m.type}`, { defaultValue: m.type })}`}
                subtitle={`${t('staff.stock.by', { name: m.user.name })} · ${formatDateTime(m.created_at)}`}
                right={
                  <AppText weight="semibold" color={Number(m.quantity_change) > 0 ? 'success' : 'danger'}>
                    {Number(m.quantity_change) > 0 ? '+' : ''}
                    {formatQuantity(m.quantity_change)}
                  </AppText>
                }
                chevron={false}
              />
            ))
          ) : (
            <EmptyState icon="swap-vertical-outline" title={t('staff.dashboard.noActivity')} />
          )}
        </Card>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  hero: {
    marginHorizontal: -spacing.lg,
    marginTop: -spacing.lg,
    paddingHorizontal: spacing.xl,
    paddingBottom: spacing.xxl,
    borderBottomLeftRadius: radius.xl,
    borderBottomRightRadius: radius.xl,
    overflow: 'hidden',
  },
  blob: { position: 'absolute', borderRadius: 999, backgroundColor: HERO_GLASS },
  blobLarge: { width: 200, height: 200, top: -80, right: -50 },
  blobSmall: { width: 110, height: 110, bottom: -50, left: 40 },
  heroMuted: { color: HERO_MUTED },
  rolePill: {
    alignSelf: 'flex-start',
    marginTop: spacing.xs,
    backgroundColor: HERO_GLASS,
    borderRadius: radius.pill,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xxs,
  },
  header: { gap: spacing.xxs, flex: 1 },
  headerRow: { flexDirection: 'row', alignItems: 'flex-start', gap: spacing.md },
  tiles: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md },
  cardHeader: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, flexWrap: 'wrap' },
  daysToggle: { width: 200 },
  flex: { flexGrow: 1 },
});
