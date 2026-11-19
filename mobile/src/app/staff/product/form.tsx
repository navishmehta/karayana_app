import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { router, useLocalSearchParams } from 'expo-router';
import { useMemo, useState } from 'react';
import { Controller, useForm, useWatch } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { ScrollView, StyleSheet, View } from 'react-native';
import { z } from 'zod';

import { lookupApi, productApi } from '@/api/staff/endpoints';
import type { StaffProduct, Unit } from '@/api/staff/types';
import { productFormAccess } from '@/auth/access';
import { useSession } from '@/auth/session';
import { FormText } from '@/components/forms/FormText';
import { AppText, Button, Card, ErrorState, LoadingView, PickerField, PickerSheet, ScreenHeader, SwitchRow, toast } from '@/components/ui';
import { SEARCH_DEBOUNCE_MS } from '@/constants/app';
import { useDebouncedValue } from '@/hooks/useDebouncedValue';
import { refreshAfterChange, staffKeys, useBrands, useStaffCategories, useStaffProduct, useUnits } from '@/hooks/useStaff';
import { money, optionalDate, optionalMoney, optionalQuantity, quantity, requiredId, requiredText } from '@/lib/staffValidation';
import { useAppTheme } from '@/theme/ThemeProvider';
import { spacing } from '@/theme/tokens';
import { apiToDisplayDate, displayToApiDate } from '@/utils/dates';
import { errorMessage } from '@/utils/errors';
import { applyServerErrors, orNull, pickDefaultUnit } from '@/utils/forms';
import { showError } from '@/utils/query';
import { goBack } from '@/utils/navigation';

const schema = (t: Parameters<typeof requiredText>[0], requireSelling: boolean) =>
  z.object({
    name: requiredText(t),
    categoryId: requiredId(t),
    brandId: z.number().nullable(),
    unitId: requiredId(t),
    sku: z.string(),
    barcode: z.string(),
    description: z.string(),
    sellingPrice: requireSelling ? money(t) : z.string(), // hidden from users who can't see prices
    mrp: optionalMoney(t),
    offerPrice: optionalMoney(t),
    offerStartsAt: optionalDate(t),
    offerEndsAt: optionalDate(t),
    purchasePrice: optionalMoney(t),
    minStockLevel: z.union([quantity(t), z.literal('')]),
    maxStockLevel: optionalQuantity(t),
    internalNotes: z.string(),
    isActive: z.boolean(),
    isVisible: z.boolean(),
    isFeatured: z.boolean(),
    trackExpiry: z.boolean(),
    showExpiry: z.boolean(),
  });

type FormValues = z.infer<ReturnType<typeof schema>>;
type PickerKind = 'category' | 'brand' | 'unit' | null;

const toForm = (p?: StaffProduct, defaultUnit?: Unit): FormValues => ({
  name: p?.name ?? '',
  categoryId: p?.category.id ?? 0,
  brandId: p?.brand?.id ?? null,
  unitId: p?.unit.id ?? defaultUnit?.id ?? 0,
  sku: p?.sku ?? '',
  barcode: p?.barcode ?? '',
  description: p?.description ?? '',
  sellingPrice: p?.selling_price ?? '',
  mrp: p?.mrp ?? '',
  offerPrice: p?.offer_price ?? '',
  offerStartsAt: apiToDisplayDate(p?.offer_starts_at),
  offerEndsAt: apiToDisplayDate(p?.offer_ends_at),
  purchasePrice: p?.purchase_price ?? '',
  minStockLevel: p ? (p.min_stock_level ?? '') : '0', // '' = hidden from this user, left unchanged
  maxStockLevel: p?.max_stock_level ?? '',
  internalNotes: p?.internal_notes ?? '',
  isActive: p?.is_active ?? true,
  isVisible: p?.is_visible_to_customers ?? true,
  isFeatured: p?.is_featured ?? false,
  trackExpiry: p?.track_expiry ?? true,
  showExpiry: p?.show_expiry_to_customers ?? false,
});

/** Form values -> API body (snake_case, empty optional fields as null). */
const toApi = (v: FormValues) => ({
  name: v.name.trim(),
  category_id: v.categoryId,
  brand_id: v.brandId,
  unit_id: v.unitId,
  sku: orNull(v.sku),
  barcode: orNull(v.barcode),
  description: orNull(v.description),
  selling_price: v.sellingPrice.trim(),
  mrp: orNull(v.mrp),
  offer_price: orNull(v.offerPrice),
  offer_starts_at: displayToApiDate(v.offerStartsAt),
  offer_ends_at: displayToApiDate(v.offerEndsAt),
  purchase_price: orNull(v.purchasePrice),
  min_stock_level: v.minStockLevel.trim() || undefined,
  max_stock_level: orNull(v.maxStockLevel),
  internal_notes: orNull(v.internalNotes),
  is_active: v.isActive,
  is_visible_to_customers: v.isVisible,
  is_featured: v.isFeatured,
  track_expiry: v.trackExpiry,
  show_expiry_to_customers: v.showExpiry,
});

const API_FIELD_TO_FORM: Record<string, keyof FormValues> = {
  category_id: 'categoryId',
  brand_id: 'brandId',
  unit_id: 'unitId',
  selling_price: 'sellingPrice',
  offer_price: 'offerPrice',
  offer_starts_at: 'offerStartsAt',
  offer_ends_at: 'offerEndsAt',
  purchase_price: 'purchasePrice',
  min_stock_level: 'minStockLevel',
  max_stock_level: 'maxStockLevel',
  internal_notes: 'internalNotes',
};
const FORM_FIELDS = Object.keys(toForm()) as (keyof FormValues)[];

export default function ProductFormScreen() {
  const { id } = useLocalSearchParams<{ id?: string }>();
  const productId = id ? Number(id) : null;
  const existing = useStaffProduct(productId);
  const units = useUnits();
  const { colors } = useAppTheme();
  const { t } = useTranslation();

  if ((productId && existing.isPending) || units.isPending) return <LoadingView />;
  if (productId && showError(existing)) return <ErrorState message={errorMessage(existing.error, t)} onRetry={() => void existing.refetch()} />;

  return (
    <View style={[styles.root, { backgroundColor: colors.background }]}>
      <ScreenHeader title={productId ? t('staff.products.form.editTitle') : t('staff.products.form.newTitle')} />
      <ProductForm product={existing.data} defaultUnit={pickDefaultUnit(units.data)} />
    </View>
  );
}

function ProductForm({ product, defaultUnit }: { product?: StaffProduct; defaultUnit?: Unit }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const editing = !!product;
  const access = productFormAccess(useSession((s) => s.user), editing);
  const { seeSelling, seePurchase, editPrices } = access;
  const [picker, setPicker] = useState<PickerKind>(null);
  const [brandSearch, setBrandSearch] = useState('');
  const [labels, setLabels] = useState({
    category: product?.category.name ?? '',
    brand: product?.brand?.name ?? '',
    unit: product
      ? `${product.unit.name} (${product.unit.short_name})`
      : defaultUnit
        ? `${defaultUnit.name} (${defaultUnit.short_name})`
        : '',
  });
  const [formError, setFormError] = useState<string | null>(null);

  const categories = useStaffCategories({ is_active: true }, access.pickCategory);
  const units = useUnits();
  const brands = useBrands(useDebouncedValue(brandSearch, SEARCH_DEBOUNCE_MS), picker === 'brand');
  const initial = useMemo(() => toForm(product, defaultUnit), [product, defaultUnit]);
  const { control, handleSubmit, setError, setValue, formState } = useForm<FormValues>({
    resolver: zodResolver(schema(t, seeSelling && editPrices)),
    defaultValues: initial,
  });
  const [categoryId, brandId, unitId] = useWatch({ control, name: ['categoryId', 'brandId', 'unitId'] });
  const values = { categoryId, brandId, unitId };

  const unitAllowsDecimal = useMemo(
    () => units.data?.find((u) => u.id === values.unitId)?.allows_decimal ?? true,
    [units.data, values.unitId],
  );

  const createBrand = useMutation({
    mutationFn: (name: string) => lookupApi.createBrand(name),
    onSuccess: ({ data }) => {
      setValue('brandId', data.id);
      setLabels((l) => ({ ...l, brand: data.name }));
      setPicker(null);
      void queryClient.invalidateQueries({ queryKey: ['staff', 'brands'] });
    },
    onError: (e) => toast.error(errorMessage(e, t)),
  });

  const save = handleSubmit(async (formValues) => {
    setFormError(null);
    const body: Record<string, unknown> = toApi(formValues);
    if (!seePurchase) {
      delete body.purchase_price;
      delete body.internal_notes;
    }
    if (!access.seeStockLevels && editing) {
      delete body.min_stock_level;
      delete body.max_stock_level;
    }
    for (const key of Object.keys(body)) if (body[key] === undefined) delete body[key];
    if (editing) {
      if (!editPrices) for (const key of ['selling_price', 'mrp', 'offer_price', 'offer_starts_at', 'offer_ends_at']) delete body[key];
      const before = toApi(initial) as Record<string, unknown>;
      for (const key of Object.keys(body)) if (body[key] === before[key]) delete body[key];
      if (!body.sku) delete body.sku; // SKU can't be emptied once set
    }
    try {
      const result = editing ? await productApi.update(product.id, body) : await productApi.create(body);
      await refreshAfterChange();
      queryClient.setQueryData(staffKeys.product(result.data.id), result);
      toast.success(editing ? t('staff.common.saved') : t('staff.products.created'));
      if (editing) goBack('/staff/products');
      else router.replace({ pathname: '/staff/product/[id]', params: { id: String(result.data.id) } });
    } catch (error) {
      const leftovers = applyServerErrors(error, setError, FORM_FIELDS, API_FIELD_TO_FORM);
      setFormError(leftovers[0] ?? (leftovers.length || Object.keys(formState.errors).length ? null : errorMessage(error, t)));
    }
  });

  const numeric = { keyboardType: 'decimal-pad' as const };
  const qtyKeyboard = { keyboardType: unitAllowsDecimal ? ('decimal-pad' as const) : ('number-pad' as const) };

  return (
    <>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <Card>
          <AppText size="subtitle" weight="semibold">
            {t('staff.products.form.basics')}
          </AppText>
          <FormText control={control} name="name" label={t('staff.products.name')} />
          <Controller
            control={control}
            name="categoryId"
            render={({ fieldState }) => (
              <PickerField
                label={t('staff.products.category')}
                value={labels.category}
                placeholder={t('staff.products.form.choose')}
                error={fieldState.error?.message}
                onPress={() => setPicker('category')}
                disabled={!access.pickCategory}
              />
            )}
          />
          <PickerField
            label={`${t('staff.products.brand')} (${t('staff.common.optional')})`}
            value={labels.brand}
            placeholder={t('staff.products.form.noBrand')}
            onPress={() => setPicker('brand')}
          />
          <Controller
            control={control}
            name="unitId"
            render={({ fieldState }) => (
              <PickerField
                label={t('staff.products.unit')}
                value={labels.unit}
                placeholder={t('staff.products.form.choose')}
                error={fieldState.error?.message}
                onPress={() => setPicker('unit')}
              />
            )}
          />
          <FormText control={control} name="sku" label={t('staff.products.sku')} hint={editing ? undefined : t('staff.products.form.skuHint')} autoCapitalize="characters" />
          <FormText control={control} name="barcode" label={`${t('staff.products.barcode')} (${t('staff.common.optional')})`} keyboardType="number-pad" />
          <FormText control={control} name="description" label={`${t('staff.products.description')} (${t('staff.common.optional')})`} multiline />
        </Card>

        {seeSelling && (
          <Card>
            <AppText size="subtitle" weight="semibold">
              {t('staff.products.pricing')}
            </AppText>
            {!editPrices && <AppText size="small" color="textMuted">{t('staff.products.form.pricesLocked')}</AppText>}
            <FormText control={control} name="sellingPrice" label={t('staff.products.sellingPrice')} editable={editPrices} {...numeric} />
            <FormText control={control} name="mrp" label={t('staff.products.mrp')} editable={editPrices} {...numeric} />
            {seePurchase && (
              <FormText control={control} name="purchasePrice" label={t('staff.products.purchasePrice')} hint={t('staff.products.form.purchaseHint')} {...numeric} />
            )}
            <FormText control={control} name="offerPrice" label={`${t('staff.products.offerPrice')} (${t('staff.common.optional')})`} editable={editPrices} {...numeric} />
            <View style={styles.pair}>
              <View style={styles.flex}>
                <FormText control={control} name="offerStartsAt" label={t('staff.products.offerStarts')} placeholder={t('staff.common.dateHint')} editable={editPrices} />
              </View>
              <View style={styles.flex}>
                <FormText control={control} name="offerEndsAt" label={t('staff.products.offerEnds')} placeholder={t('staff.common.dateHint')} editable={editPrices} />
              </View>
            </View>
          </Card>
        )}

        {(access.seeStockLevels || !editing) && (
        <Card>
          <AppText size="subtitle" weight="semibold">
            {t('staff.products.form.stockLevels')}
          </AppText>
          <View style={styles.pair}>
            <View style={styles.flex}>
              <FormText control={control} name="minStockLevel" label={t('staff.products.minStock')} hint={t('staff.products.form.minHint')} {...qtyKeyboard} />
            </View>
            <View style={styles.flex}>
              <FormText control={control} name="maxStockLevel" label={`${t('staff.products.maxStock')} (${t('staff.common.optional')})`} {...qtyKeyboard} />
            </View>
          </View>
          {!editing && <AppText size="small" color="textMuted">{t('staff.products.form.stockAfterCreate')}</AppText>}
        </Card>
        )}

        <Card>
          <AppText size="subtitle" weight="semibold">
            {t('staff.products.form.options')}
          </AppText>
          <Toggle control={control} name="isActive" label={t('staff.products.activeLabel')} />
          <Toggle control={control} name="isVisible" label={t('staff.products.visibleLabel')} hint={t('staff.products.visibleHint')} />
          <Toggle control={control} name="isFeatured" label={t('staff.products.featuredLabel')} />
          <Toggle control={control} name="trackExpiry" label={t('staff.products.trackExpiry')} hint={t('staff.products.trackExpiryHint')} />
          <Toggle control={control} name="showExpiry" label={t('staff.products.showExpiry')} />
          {seePurchase && <FormText control={control} name="internalNotes" label={t('staff.products.internalNotes')} hint={t('staff.products.form.notesHint')} multiline />}
        </Card>

        {formError && <AppText color="danger">{formError}</AppText>}
        <Button title={t('staff.common.save')} onPress={() => void save()} loading={formState.isSubmitting} fullWidth />
      </ScrollView>

      <PickerSheet
        visible={picker === 'category'}
        title={t('staff.products.category')}
        loading={categories.isPending}
        items={(categories.data ?? []).map((c) => ({ id: c.id, label: c.name }))}
        selectedId={values.categoryId}
        onClose={() => setPicker(null)}
        onSelect={(item) => {
          setValue('categoryId', item.id, { shouldValidate: true });
          setLabels((l) => ({ ...l, category: item.label }));
          setPicker(null);
        }}
      />
      <PickerSheet
        visible={picker === 'brand'}
        title={t('staff.products.brand')}
        loading={brands.isPending}
        items={[{ id: 0, label: t('staff.products.form.noBrand') }, ...(brands.data ?? []).map((b) => ({ id: b.id, label: b.name }))]}
        selectedId={values.brandId ?? 0}
        onSearch={setBrandSearch}
        onCreate={(name) => createBrand.mutate(name)}
        createLabel={(name) => t('staff.products.form.newBrand', { name })}
        onClose={() => setPicker(null)}
        onSelect={(item) => {
          setValue('brandId', item.id || null);
          setLabels((l) => ({ ...l, brand: item.id ? item.label : '' }));
          setPicker(null);
        }}
      />
      <PickerSheet
        visible={picker === 'unit'}
        title={t('staff.products.unit')}
        loading={units.isPending}
        items={(units.data ?? []).map((u) => ({ id: u.id, label: `${u.name} (${u.short_name})`, hint: u.allows_decimal ? t('staff.products.form.decimalsAllowed') : undefined }))}
        selectedId={values.unitId}
        onClose={() => setPicker(null)}
        onSelect={(item) => {
          setValue('unitId', item.id, { shouldValidate: true });
          setLabels((l) => ({ ...l, unit: item.label }));
          setPicker(null);
        }}
      />
    </>
  );
}

function Toggle({
  control,
  name,
  label,
  hint,
}: {
  control: ReturnType<typeof useForm<FormValues>>['control'];
  name: 'isActive' | 'isVisible' | 'isFeatured' | 'trackExpiry' | 'showExpiry';
  label: string;
  hint?: string;
}) {
  return (
    <Controller control={control} name={name} render={({ field }) => <SwitchRow label={label} hint={hint} value={field.value} onChange={field.onChange} />} />
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  content: { width: '100%', maxWidth: 820, alignSelf: 'center', padding: spacing.lg, gap: spacing.md, paddingBottom: spacing.xxxl },
  pair: { flexDirection: 'row', gap: spacing.md },
  flex: { flex: 1 },
});
