import Ionicons from '@expo/vector-icons/Ionicons';
import { useMutation } from '@tanstack/react-query';
import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Pressable, ScrollView, StyleSheet, View } from 'react-native';

import { productApi } from '@/api/staff/endpoints';
import type { Batch, StaffProduct } from '@/api/staff/types';
import { useCan } from '@/auth/permissions';
import { ProductImage } from '@/components/catalogue/ProductImage';
import { ExpiryBadge, StockBadge } from '@/components/staff/StatusBadges';
import {
  AppText,
  Badge,
  Button,
  Card,
  ConfirmDialog,
  ErrorState,
  ListRow,
  LoadingView,
  ScreenHeader,
  SwitchRow,
  toast,
} from '@/components/ui';
import { PERMISSIONS } from '@/constants/permissions';
import { refreshAfterChange, useBatches, useStaffProduct, useTransactions } from '@/hooks/useStaff';
import { pickImageForm } from '@/lib/images';
import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, spacing } from '@/theme/tokens';
import { errorMessage } from '@/utils/errors';
import { formatDate, formatDateTime, formatMoney, formatPercent, formatQuantity } from '@/utils/format';

const MAX_IMAGES = 6;
const IMAGE_SIZE = 88;
const HISTORY_ROWS = 10;

export default function StaffProductScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const productId = Number(id);
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const product = useStaffProduct(productId);
  const canUpdate = useCan(PERMISSIONS.productsUpdate);
  const canDelete = useCan(PERMISSIONS.productsDelete);
  const canStock = useCan(PERMISSIONS.stockView);
  const canMoveStock = useCan(PERMISSIONS.stockUpdate);
  const canExpiry = useCan(PERMISSIONS.expiryView);
  const batches = useBatches(productId, canStock || canExpiry);
  const history = useTransactions({ product_id: productId }, canStock);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const onError = (error: unknown) => toast.error(errorMessage(error, t));
  const update = useMutation({
    mutationFn: (body: Partial<StaffProduct>) => productApi.update(productId, body),
    onSuccess: () => {
      void refreshAfterChange();
      toast.success(t('staff.common.saved'));
    },
    onError,
  });
  const remove = useMutation({
    mutationFn: () => productApi.remove(productId),
    onSuccess: () => {
      void refreshAfterChange();
      toast.success(t('staff.common.deleted'));
      router.back();
    },
    onError,
  });
  const addImage = useMutation({
    mutationFn: async () => {
      const form = await pickImageForm();
      return form ? productApi.uploadImage(productId, form) : null;
    },
    onSuccess: (result) => result && void refreshAfterChange(),
    onError,
  });
  const imageAction = useMutation({
    mutationFn: async ({ imageId, action }: { imageId: number; action: 'main' | 'remove' }): Promise<void> => {
      if (action === 'main') await productApi.makePrimary(productId, imageId);
      else await productApi.removeImage(productId, imageId);
    },
    onSuccess: () => void refreshAfterChange(),
    onError,
  });

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
  const unit = p.unit.short_name;
  const stockMove = (kind: string, batch?: Batch) =>
    router.push({ pathname: '/staff/stock/[kind]', params: { kind, productId: String(p.id), ...(batch ? { batchId: String(batch.id) } : {}) } });

  return (
    <View style={[styles.root, { backgroundColor: colors.background }]}>
      <ScreenHeader
        title={p.name}
        right={
          canUpdate ? (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={t('staff.common.edit')}
              onPress={() => router.push({ pathname: '/staff/product/form', params: { id: String(p.id) } })}
            >
              <Ionicons name="create-outline" size={24} color={colors.primary} />
            </Pressable>
          ) : undefined
        }
      />
      <ScrollView contentContainerStyle={styles.content}>
        <Card>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.images}>
            {p.images.map((img) => (
              <View key={img.id} style={styles.imageBox}>
                <ProductImage uri={img.thumb_url} style={styles.image} />
                {img.is_primary && <Badge label={t('staff.products.mainImage')} />}
                {canUpdate && (
                  <View style={styles.imageActions}>
                    {!img.is_primary && (
                      <Pressable accessibilityRole="button" accessibilityLabel={t('staff.products.makeMain')} onPress={() => imageAction.mutate({ imageId: img.id, action: 'main' })}>
                        <Ionicons name="star-outline" size={20} color={colors.primary} />
                      </Pressable>
                    )}
                    <Pressable accessibilityRole="button" accessibilityLabel={t('staff.products.removeImage')} onPress={() => imageAction.mutate({ imageId: img.id, action: 'remove' })}>
                      <Ionicons name="trash-outline" size={20} color={colors.danger} />
                    </Pressable>
                  </View>
                )}
              </View>
            ))}
            {canUpdate && p.images.length < MAX_IMAGES && (
              <Pressable
                accessibilityRole="button"
                accessibilityLabel={t('staff.products.addImage')}
                onPress={() => addImage.mutate()}
                style={[styles.image, styles.addImage, { borderColor: colors.border }]}
              >
                <Ionicons name={addImage.isPending ? 'hourglass-outline' : 'camera-outline'} size={28} color={colors.primary} />
              </Pressable>
            )}
          </ScrollView>
          <View style={styles.badges}>
            {!p.is_active && <Badge label={t('staff.common.inactive')} tone="textMuted" />}
            {!p.is_visible_to_customers && <Badge label={t('staff.products.hiddenFromCustomers')} tone="textMuted" />}
            {p.is_featured && <Badge label={t('catalogue.featured')} tone="accent" />}
            {p.stock_status && <StockBadge status={p.stock_status} />}
          </View>
          <Row label={t('staff.products.category')} value={p.category.name} />
          {p.brand && <Row label={t('staff.products.brand')} value={p.brand.name} />}
          <Row label={t('staff.products.sku')} value={p.sku} />
          {p.barcode && <Row label={t('staff.products.barcode')} value={p.barcode} />}
          <Row label={t('staff.products.unit')} value={`${p.unit.name} (${unit})`} />
          {p.description && <AppText color="textMuted">{p.description}</AppText>}
        </Card>

        {p.selling_price !== undefined && (
          <Card>
            <AppText size="subtitle" weight="semibold">
              {t('staff.products.pricing')}
            </AppText>
            <Row label={t('staff.products.sellingPrice')} value={formatMoney(p.selling_price)} />
            <Row label={t('staff.products.mrp')} value={formatMoney(p.mrp)} />
            {p.offer_price && (
              <Row
                label={t('staff.products.offerPrice')}
                value={`${formatMoney(p.offer_price)}${p.on_offer ? '' : ` (${t('staff.products.offerNotRunning')})`}`}
              />
            )}
            {p.on_offer && <Row label={t('staff.products.customerPays')} value={formatMoney(p.effective_price)} />}
            {p.purchase_price !== undefined && <Row label={t('staff.products.purchasePrice')} value={formatMoney(p.purchase_price)} />}
            {p.profit && (
              <View style={[styles.profit, { backgroundColor: colors.primarySoft }]}>
                <AppText weight="semibold" color="primary">
                  {t('staff.products.profitPerUnit', { amount: formatMoney(p.profit.amount) })}
                </AppText>
                <AppText size="small" color="textMuted">
                  {t('staff.products.profitExplain', {
                    price: formatMoney(p.profit.price_used),
                    cost: formatMoney(p.profit.purchase_price),
                    markup: formatPercent(p.profit.markup_percent),
                    margin: formatPercent(p.profit.margin_percent),
                  })}
                </AppText>
              </View>
            )}
            {p.internal_notes && <Row label={t('staff.products.internalNotes')} value={p.internal_notes} />}
          </Card>
        )}

        {p.current_stock !== undefined && (
          <Card>
            <AppText size="subtitle" weight="semibold">
              {t('staff.products.stock')}
            </AppText>
            <Row label={t('staff.products.currentStock')} value={formatQuantity(p.current_stock, unit)} />
            <Row label={t('staff.products.sellableStock')} value={formatQuantity(p.sellable_stock, unit)} />
            <Row label={t('staff.products.minStock')} value={formatQuantity(p.min_stock_level, unit)} />
            {canMoveStock && (
              <View style={styles.actions}>
                <Button title={t('staff.stock.actions.stock-in')} variant="secondary" onPress={() => stockMove('stock-in')} />
                <Button title={t('staff.stock.actions.stock-out')} variant="secondary" onPress={() => stockMove('stock-out')} />
              </View>
            )}
          </Card>
        )}

        {batches.data && (
          <Card>
            <AppText size="subtitle" weight="semibold">
              {t('staff.products.batches')}
            </AppText>
            {batches.data.length === 0 ? (
              <AppText color="textMuted">{t('staff.products.noBatches')}</AppText>
            ) : (
              batches.data.map((b) => (
                <View key={b.id} style={[styles.batch, { borderColor: colors.border }]}>
                  <View style={styles.batchTop}>
                    <AppText weight="semibold" style={styles.flex}>
                      {t('staff.expiry.batchLabel', { number: b.batch_number ?? b.id })}
                    </AppText>
                    <ExpiryBadge bucket={b.bucket} days={b.days_to_expiry} />
                  </View>
                  <AppText size="small" color="textMuted">
                    {formatQuantity(b.quantity_remaining, unit)} · {t('staff.products.expiresOn', { date: formatDate(b.expiry_date) })}
                    {b.purchase_price !== undefined ? ` · ${formatMoney(b.purchase_price)}` : ''}
                  </AppText>
                  {canMoveStock && (
                    <View style={styles.actions}>
                      <Button title={t('staff.stock.actions.adjust')} variant="ghost" onPress={() => stockMove('adjust', b)} />
                      <Button title={t('staff.stock.actions.damage')} variant="ghost" onPress={() => stockMove('damage', b)} />
                    </View>
                  )}
                </View>
              ))
            )}
          </Card>
        )}

        {canStock && (
          <Card>
            <AppText size="subtitle" weight="semibold">
              {t('staff.products.history')}
            </AppText>
            {history.items.length === 0 ? (
              <AppText color="textMuted">{t('staff.products.noHistory')}</AppText>
            ) : (
              history.items.slice(0, HISTORY_ROWS).map((tx) => (
                <ListRow
                  key={tx.id}
                  title={t(`staff.stock.types.${tx.type}`, { defaultValue: tx.type })}
                  subtitle={`${t('staff.stock.by', { name: tx.user.name })} · ${formatDateTime(tx.created_at)}`}
                  right={
                    <AppText weight="semibold" color={Number(tx.quantity_change) > 0 ? 'success' : 'danger'}>
                      {Number(tx.quantity_change) > 0 ? '+' : ''}
                      {formatQuantity(tx.quantity_change)}
                    </AppText>
                  }
                  chevron={false}
                />
              ))
            )}
          </Card>
        )}

        {canUpdate && (
          <Card>
            <SwitchRow label={t('staff.products.activeLabel')} value={p.is_active} onChange={(v) => update.mutate({ is_active: v })} />
            <SwitchRow
              label={t('staff.products.visibleLabel')}
              hint={t('staff.products.visibleHint')}
              value={p.is_visible_to_customers}
              onChange={(v) => update.mutate({ is_visible_to_customers: v })}
            />
            <SwitchRow label={t('staff.products.featuredLabel')} value={p.is_featured} onChange={(v) => update.mutate({ is_featured: v })} />
          </Card>
        )}

        {canDelete && <Button title={t('staff.products.delete')} variant="danger" onPress={() => setConfirmDelete(true)} />}
      </ScrollView>

      <ConfirmDialog
        visible={confirmDelete}
        title={t('staff.products.deleteConfirm', { name: p.name })}
        confirmLabel={t('staff.common.delete')}
        destructive
        loading={remove.isPending}
        onCancel={() => setConfirmDelete(false)}
        onConfirm={() => remove.mutate()}
      />
    </View>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.row}>
      <AppText color="textMuted">{label}</AppText>
      <AppText weight="medium" style={styles.value}>
        {value}
      </AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  content: { width: '100%', maxWidth: 820, alignSelf: 'center', padding: spacing.lg, gap: spacing.md, paddingBottom: spacing.xxxl },
  images: { gap: spacing.md },
  imageBox: { width: IMAGE_SIZE, gap: spacing.xs },
  image: { width: IMAGE_SIZE, borderRadius: radius.md },
  imageActions: { flexDirection: 'row', justifyContent: 'space-around' },
  addImage: { aspectRatio: 1, borderWidth: 1.5, borderStyle: 'dashed', alignItems: 'center', justifyContent: 'center' },
  badges: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  row: { flexDirection: 'row', justifyContent: 'space-between', gap: spacing.md },
  value: { flexShrink: 1, textAlign: 'right' },
  profit: { borderRadius: radius.md, padding: spacing.md, gap: spacing.xs },
  actions: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  batch: { borderTopWidth: StyleSheet.hairlineWidth, paddingTop: spacing.sm, gap: spacing.xs },
  batchTop: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  flex: { flex: 1 },
});
