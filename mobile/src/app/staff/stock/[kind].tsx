import { useQuery } from '@tanstack/react-query';
import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ScrollView, StyleSheet, View } from 'react-native';

import { inventoryApi, productApi, type StockKind } from '@/api/staff/endpoints';
import type { Batch, StaffProduct } from '@/api/staff/types';
import { useCan } from '@/auth/permissions';
import { AppText, Button, Card, ChipGroup, ErrorState, PickerField, PickerSheet, ScreenHeader, TextField, toast } from '@/components/ui';
import { SEARCH_DEBOUNCE_MS } from '@/constants/app';
import { PERMISSIONS } from '@/constants/permissions';
import { NEEDS_BATCH, STOCK_KINDS, STOCK_REASONS } from '@/constants/stock';
import { useDebouncedValue } from '@/hooks/useDebouncedValue';
import { refreshAfterChange, useBatches, useStaffProduct } from '@/hooks/useStaff';
import { useAppTheme } from '@/theme/ThemeProvider';
import { spacing } from '@/theme/tokens';
import { displayToApiDate, isValidDisplayDate } from '@/utils/dates';
import { errorMessage } from '@/utils/errors';
import { formatDate, formatQuantity } from '@/utils/format';
import { newRequestKey, orNull } from '@/utils/forms';
import { isApiError } from '@/api/errors';

const QUANTITY = /^\d{1,6}(\.\d{1,3})?$/;
const FEFO_ID = 0;

type Errors = Partial<Record<'product' | 'batch' | 'quantity' | 'expiry' | 'manufacturing' | 'price' | 'form', string>>;

export default function StockMoveScreen() {
  const params = useLocalSearchParams<{ kind: string; productId?: string; batchId?: string }>();
  const kind = (STOCK_KINDS.includes(params.kind as StockKind) ? params.kind : 'stock-in') as StockKind;
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const canMove = useCan(PERMISSIONS.stockUpdate);
  const seePurchase = useCan(PERMISSIONS.pricingViewPurchase);

  const [productId, setProductId] = useState<number | null>(params.productId ? Number(params.productId) : null);
  const [batchId, setBatchId] = useState<number>(params.batchId ? Number(params.batchId) : FEFO_ID);
  const [picker, setPicker] = useState<'product' | 'batch' | null>(null);
  const [search, setSearch] = useState('');
  const [quantity, setQuantity] = useState('');
  const [expiry, setExpiry] = useState('');
  const [manufacturing, setManufacturing] = useState('');
  const [batchNumber, setBatchNumber] = useState('');
  const [price, setPrice] = useState<string | null>(null);
  const [reason, setReason] = useState(STOCK_REASONS[kind][0]);
  const [notes, setNotes] = useState('');
  const [errors, setErrors] = useState<Errors>({});
  const [saving, setSaving] = useState(false);
  const [requestKey] = useState(newRequestKey); // same key if the user taps Save again after a network error

  const product = useStaffProduct(productId);
  const batches = useBatches(productId, kind !== 'stock-in');
  const debounced = useDebouncedValue(search, SEARCH_DEBOUNCE_MS);
  const productSearch = useQuery({
    queryKey: ['staff', 'product-picker', debounced],
    queryFn: () => productApi.list({ search: debounced || undefined, per_page: 30 }),
    select: (r) => r.data,
    enabled: picker === 'product',
  });

  if (!canMove) return <ErrorState message={t('staff.common.noPermission')} />;

  const p = product.data;
  const unit = p?.unit.short_name ?? '';
  // Before a product is chosen there is no unit: use the label's plain version (e.g. "Quantity", not "Quantity ()").
  const withUnit = (key: string) => (unit ? t(key, { unit }) : t(`${key}NoUnit`));
  const batchList = (batches.data ?? []).filter((b) => Number(b.quantity_remaining) > 0 || kind === 'adjust');
  const chosenBatch = batchList.find((b) => b.id === batchId);
  const purchasePrice = price ?? p?.purchase_price ?? '';
  const batchLabel = (b: Batch) =>
    `${t('staff.expiry.batchLabel', { number: b.batch_number ?? b.id })} · ${formatQuantity(b.quantity_remaining, unit)} · ${formatDate(b.expiry_date)}`;

  const validate = (): Errors => {
    const e: Errors = {};
    if (!p) e.product = t('validation.required');
    if (NEEDS_BATCH.includes(kind) && !chosenBatch) e.batch = t('validation.required');
    const q = quantity.trim();
    if (!QUANTITY.test(q) || (kind !== 'adjust' && Number(q) <= 0)) e.quantity = t('staff.validation.quantity');
    else if (p && !p.unit.allows_decimal && !Number.isInteger(Number(q))) e.quantity = t('staff.validation.wholeNumber', { unit });
    if (kind === 'stock-in') {
      if (p?.track_expiry && !expiry.trim()) e.expiry = t('validation.required');
      if (expiry.trim() && !isValidDisplayDate(expiry)) e.expiry = t('staff.validation.date');
      if (manufacturing.trim() && !isValidDisplayDate(manufacturing)) e.manufacturing = t('staff.validation.date');
      if (seePurchase && purchasePrice && !/^\d{1,7}(\.\d{1,2})?$/.test(purchasePrice)) e.price = t('staff.validation.money');
    }
    return e;
  };

  const body = (): Record<string, unknown> => {
    const q = quantity.trim();
    const common = { reason, notes: orNull(notes) };
    switch (kind) {
      case 'stock-in':
        return {
          ...common,
          product_id: productId,
          quantity: q,
          expiry_date: displayToApiDate(expiry),
          manufacturing_date: displayToApiDate(manufacturing),
          batch_number: orNull(batchNumber),
          ...(seePurchase && purchasePrice ? { purchase_price: purchasePrice } : {}),
        };
      case 'stock-out':
        return { ...common, product_id: productId, quantity: q, batch_id: batchId || null };
      case 'adjust':
        return { ...common, batch_id: batchId, counted_quantity: q };
      case 'damage':
        return { ...common, batch_id: batchId, quantity: q };
    }
  };

  const submit = async () => {
    const found = validate();
    setErrors(found);
    if (Object.keys(found).length) return;
    setSaving(true);
    try {
      await inventoryApi.move(kind, body(), requestKey);
      await refreshAfterChange();
      toast.success(t('staff.stock.saved'));
      router.back();
    } catch (error) {
      const field = (name: string) => (isApiError(error) ? error.fieldError(name) : undefined);
      setErrors({
        quantity: field('quantity') ?? field('counted_quantity'),
        expiry: field('expiry_date'),
        manufacturing: field('manufacturing_date'),
        price: field('purchase_price'),
        batch: field('batch_id'),
        form: errorMessage(error, t),
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <View style={[styles.root, { backgroundColor: colors.background }]}>
      <ScreenHeader title={t(`staff.stock.actions.${kind}`)} />
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <Card>
          <PickerField
            label={t('staff.stock.product')}
            value={p?.name}
            placeholder={t('staff.stock.chooseProduct')}
            error={errors.product}
            onPress={() => setPicker('product')}
            disabled={!!params.productId}
          />
          {p?.current_stock !== undefined && (
            <AppText size="small" color="textMuted">
              {t('staff.stock.currentStock', { qty: formatQuantity(p.current_stock, unit) })}
            </AppText>
          )}
          {kind !== 'stock-in' && p && (
            <PickerField
              label={t('staff.stock.batch')}
              value={chosenBatch ? batchLabel(chosenBatch) : kind === 'stock-out' ? t('staff.stock.fefo') : undefined}
              placeholder={t('staff.stock.chooseBatch')}
              error={errors.batch}
              onPress={() => setPicker('batch')}
            />
          )}
        </Card>

        <Card>
          <TextField
            label={withUnit(kind === 'adjust' ? 'staff.stock.countedQuantity' : 'staff.stock.quantity')}
            hint={kind === 'adjust' && chosenBatch ? t('staff.stock.systemSays', { qty: formatQuantity(chosenBatch.quantity_remaining, unit) }) : undefined}
            value={quantity}
            onChangeText={setQuantity}
            keyboardType={p && !p.unit.allows_decimal ? 'number-pad' : 'decimal-pad'}
            error={errors.quantity}
          />
          {kind === 'stock-in' && (
            <>
              <TextField
                label={p?.track_expiry === false ? `${t('staff.stock.expiryDate')} (${t('staff.common.optional')})` : t('staff.stock.expiryDate')}
                placeholder={t('staff.common.dateHint')}
                value={expiry}
                onChangeText={setExpiry}
                error={errors.expiry}
              />
              <TextField
                label={`${t('staff.stock.manufacturingDate')} (${t('staff.common.optional')})`}
                placeholder={t('staff.common.dateHint')}
                value={manufacturing}
                onChangeText={setManufacturing}
                error={errors.manufacturing}
              />
              <TextField
                label={`${t('staff.stock.batchNumber')} (${t('staff.common.optional')})`}
                hint={t('staff.stock.batchNumberHint')}
                value={batchNumber}
                onChangeText={setBatchNumber}
                autoCapitalize="characters"
              />
              {seePurchase && (
                <TextField
                  label={withUnit('staff.stock.purchasePricePerUnit')}
                  value={purchasePrice}
                  onChangeText={setPrice}
                  keyboardType="decimal-pad"
                  error={errors.price}
                />
              )}
            </>
          )}
          <AppText size="small" weight="medium" color="textMuted">
            {t('staff.stock.reason')}
          </AppText>
          <ChipGroup options={STOCK_REASONS[kind].map((r) => ({ value: r, label: t(`staff.stock.reasons.${r}`) }))} value={reason} onChange={setReason} />
          <TextField label={`${t('staff.stock.notes')} (${t('staff.common.optional')})`} value={notes} onChangeText={setNotes} multiline />
        </Card>

        {errors.form && (
          <AppText color="danger" accessibilityLiveRegion="polite">
            {errors.form}
          </AppText>
        )}
        <Button title={t(`staff.stock.submit.${kind}`)} onPress={() => void submit()} loading={saving} fullWidth />
      </ScrollView>

      <PickerSheet
        visible={picker === 'product'}
        title={t('staff.stock.chooseProduct')}
        loading={productSearch.isPending}
        items={(productSearch.data ?? []).map((item: StaffProduct) => ({
          id: item.id,
          label: item.name,
          hint: item.current_stock !== undefined ? formatQuantity(item.current_stock, item.unit.short_name) : item.sku,
        }))}
        selectedId={productId}
        onSearch={setSearch}
        onClose={() => setPicker(null)}
        onSelect={(item) => {
          setProductId(item.id);
          setBatchId(FEFO_ID);
          setPicker(null);
        }}
      />
      <PickerSheet
        visible={picker === 'batch'}
        title={t('staff.stock.chooseBatch')}
        loading={batches.isPending}
        items={[
          ...(kind === 'stock-out' ? [{ id: FEFO_ID, label: t('staff.stock.fefo'), hint: t('staff.stock.fefoHint') }] : []),
          ...batchList.map((b) => ({ id: b.id, label: batchLabel(b), hint: b.bucket === 'expired' ? t('staff.expiry.expired') : undefined })),
        ]}
        selectedId={batchId}
        onClose={() => setPicker(null)}
        onSelect={(item) => {
          setBatchId(item.id);
          setPicker(null);
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  content: { width: '100%', maxWidth: 720, alignSelf: 'center', padding: spacing.lg, gap: spacing.md, paddingBottom: spacing.xxxl },
});
