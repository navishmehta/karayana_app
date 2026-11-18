import { zodResolver } from '@hookform/resolvers/zod';
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { ScrollView, StyleSheet, View } from 'react-native';
import { z } from 'zod';

import { settingsApi } from '@/api/staff/endpoints';
import type { StoreSettings } from '@/api/staff/types';
import { ProductImage } from '@/components/catalogue/ProductImage';
import { FormText } from '@/components/forms/FormText';
import { AppText, Button, Card, ErrorState, LoadingView, ScreenHeader, SwitchRow, toast } from '@/components/ui';
import { refreshAfterChange, staffKeys, useStoreSettings } from '@/hooks/useStaff';
import { pickImageForm } from '@/lib/images';
import { requiredText } from '@/lib/staffValidation';
import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, spacing } from '@/theme/tokens';
import { errorMessage } from '@/utils/errors';
import { applyServerErrors } from '@/utils/forms';

const LOGO_SIZE = 88;
const PHONE = /^[6-9]\d{9}$/;

export default function StoreSettingsScreen() {
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const settings = useStoreSettings();
  return (
    <View style={[styles.root, { backgroundColor: colors.background }]}>
      <ScreenHeader title={t('staff.more.storeSettings')} />
      {settings.isPending ? (
        <LoadingView />
      ) : settings.isError ? (
        <ErrorState message={errorMessage(settings.error, t)} onRetry={() => void settings.refetch()} />
      ) : (
        <SettingsForm settings={settings.data} />
      )}
    </View>
  );
}

function SettingsForm({ settings }: { settings: StoreSettings }) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [uploading, setUploading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const phone = z.string().trim().refine((v) => !v || PHONE.test(v), t('staff.validation.phone'));
  const day = z.string().trim().regex(/^\d{1,3}$/, t('staff.validation.days'));
  const schema = z.object({
    storeName: requiredText(t),
    tagline: z.string(),
    phone,
    whatsapp: phone,
    address: z.string(),
    hours: z.string(),
    offersEnabled: z.boolean(),
    showOutOfStock: z.boolean(),
    defaultMinStock: z.string().trim().regex(/^\d{1,6}$/, t('staff.validation.quantity')),
    day1: day,
    day2: day,
    day3: day,
    notifyLow: z.boolean(),
    notifyOut: z.boolean(),
    notifyExpiry: z.boolean(),
    digestTime: z.string().trim().regex(/^([01]\d|2[0-3]):[0-5]\d$/, t('staff.validation.time')),
  });
  type Values = z.infer<typeof schema>;
  const [d1, d2, d3] = settings.expiry_buckets;
  const { control, handleSubmit, setError, formState } = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: {
      storeName: settings.store_name,
      tagline: settings.tagline ?? '',
      phone: settings.phone ?? '',
      whatsapp: settings.whatsapp ?? '',
      address: settings.address ?? '',
      hours: settings.hours ?? '',
      offersEnabled: settings.offers_enabled,
      showOutOfStock: settings.show_out_of_stock,
      defaultMinStock: String(settings.default_min_stock),
      day1: String(d1),
      day2: String(d2),
      day3: String(d3),
      notifyLow: settings.notify_low_stock,
      notifyOut: settings.notify_out_of_stock,
      notifyExpiry: settings.notify_expiry,
      digestTime: settings.expiry_digest_time,
    },
  });

  const save = handleSubmit(async (v) => {
    setFormError(null);
    try {
      const result = await settingsApi.update({
        store_name: v.storeName.trim(),
        tagline: v.tagline.trim(),
        phone: v.phone.trim() || null,
        whatsapp: v.whatsapp.trim() || null,
        address: v.address.trim(),
        hours: v.hours.trim(),
        offers_enabled: v.offersEnabled,
        show_out_of_stock: v.showOutOfStock,
        default_min_stock: Number(v.defaultMinStock),
        expiry_buckets: [Number(v.day1), Number(v.day2), Number(v.day3)],
        notify_low_stock: v.notifyLow,
        notify_out_of_stock: v.notifyOut,
        notify_expiry: v.notifyExpiry,
        expiry_digest_time: v.digestTime,
      });
      queryClient.setQueryData(staffKeys.settings, result);
      await refreshAfterChange();
      toast.success(t('staff.common.saved'));
    } catch (error) {
      const leftovers = applyServerErrors(error, setError, ['storeName', 'phone', 'whatsapp', 'day1', 'digestTime'] as const, {
        store_name: 'storeName',
        expiry_buckets: 'day1',
        expiry_digest_time: 'digestTime',
      });
      setFormError(leftovers[0] ?? errorMessage(error, t));
    }
  });

  const changeLogo = async () => {
    const form = await pickImageForm();
    if (!form) return;
    setUploading(true);
    try {
      queryClient.setQueryData(staffKeys.settings, await settingsApi.uploadLogo(form));
      await refreshAfterChange();
      toast.success(t('staff.common.saved'));
    } catch (error) {
      toast.error(errorMessage(error, t));
    } finally {
      setUploading(false);
    }
  };

  const toggle = (name: 'offersEnabled' | 'showOutOfStock' | 'notifyLow' | 'notifyOut' | 'notifyExpiry', label: string, hint?: string) => (
    <Controller control={control} name={name} render={({ field }) => <SwitchRow label={label} hint={hint} value={field.value} onChange={field.onChange} />} />
  );

  return (
    <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
      <Card>
        <AppText size="subtitle" weight="semibold">
          {t('staff.settings.storeSection')}
        </AppText>
        <View style={styles.logoRow}>
          <ProductImage uri={settings.logo_thumb_url} style={styles.logo} />
          <Button title={t('staff.settings.changeLogo')} variant="secondary" onPress={() => void changeLogo()} loading={uploading} />
        </View>
        <FormText control={control} name="storeName" label={t('staff.settings.storeName')} hint={t('staff.settings.storeNameHint')} />
        <FormText control={control} name="tagline" label={`${t('staff.settings.tagline')} (${t('staff.common.optional')})`} />
        <FormText control={control} name="phone" label={`${t('staff.settings.phone')} (${t('staff.common.optional')})`} keyboardType="phone-pad" />
        <FormText control={control} name="whatsapp" label={`${t('staff.settings.whatsapp')} (${t('staff.common.optional')})`} keyboardType="phone-pad" />
        <FormText control={control} name="address" label={`${t('staff.settings.address')} (${t('staff.common.optional')})`} multiline />
        <FormText control={control} name="hours" label={`${t('staff.settings.hours')} (${t('staff.common.optional')})`} placeholder={t('staff.settings.hoursExample')} />
      </Card>

      <Card>
        <AppText size="subtitle" weight="semibold">
          {t('staff.settings.catalogueSection')}
        </AppText>
        {toggle('offersEnabled', t('staff.settings.offersEnabled'), t('staff.settings.offersHint'))}
        {toggle('showOutOfStock', t('staff.settings.showOutOfStock'), t('staff.settings.showOutOfStockHint'))}
      </Card>

      <Card>
        <AppText size="subtitle" weight="semibold">
          {t('staff.settings.inventorySection')}
        </AppText>
        <FormText control={control} name="defaultMinStock" label={t('staff.settings.defaultMinStock')} keyboardType="number-pad" />
        <AppText size="small" weight="medium" color="textMuted">
          {t('staff.settings.expiryDays')}
        </AppText>
        <View style={styles.days}>
          {(['day1', 'day2', 'day3'] as const).map((name, i) => (
            <View key={name} style={styles.flex}>
              <FormText control={control} name={name} label={t('staff.settings.limit', { n: i + 1 })} keyboardType="number-pad" />
            </View>
          ))}
        </View>
        <AppText size="small" color="textMuted">
          {t('staff.settings.expiryDaysHint')}
        </AppText>
      </Card>

      <Card>
        <AppText size="subtitle" weight="semibold">
          {t('staff.settings.notificationsSection')}
        </AppText>
        {toggle('notifyLow', t('staff.settings.notifyLowStock'))}
        {toggle('notifyOut', t('staff.settings.notifyOutOfStock'))}
        {toggle('notifyExpiry', t('staff.settings.notifyExpiry'))}
        <FormText control={control} name="digestTime" label={t('staff.settings.digestTime')} hint={t('staff.settings.digestHint')} placeholder="08:00" />
      </Card>

      {formError && <AppText color="danger">{formError}</AppText>}
      <Button title={t('staff.common.save')} onPress={() => void save()} loading={formState.isSubmitting} fullWidth />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  content: { width: '100%', maxWidth: 720, alignSelf: 'center', padding: spacing.lg, gap: spacing.md, paddingBottom: spacing.xxxl },
  logoRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.lg },
  logo: { width: LOGO_SIZE, borderRadius: radius.lg },
  days: { flexDirection: 'row', gap: spacing.md },
  flex: { flex: 1 },
});
