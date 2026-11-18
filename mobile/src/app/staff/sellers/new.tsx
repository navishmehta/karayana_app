import { zodResolver } from '@hookform/resolvers/zod';
import { router } from 'expo-router';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { ScrollView, StyleSheet, View } from 'react-native';
import { z } from 'zod';

import { sellerApi } from '@/api/staff/endpoints';
import { isApiError } from '@/api/errors';
import { PermissionEditor } from '@/components/staff/PermissionEditor';
import { FormText } from '@/components/forms/FormText';
import { AppText, Button, Card, LoadingView, ScreenHeader, toast } from '@/components/ui';
import type { Permission } from '@/constants/permissions';
import { refreshAfterChange, usePermissionGroups } from '@/hooks/useStaff';
import { requiredText } from '@/lib/staffValidation';
import { emailField, newPasswordField } from '@/lib/validation';
import { useAppTheme } from '@/theme/ThemeProvider';
import { spacing } from '@/theme/tokens';
import { errorMessage } from '@/utils/errors';
import { applyServerErrors, orNull } from '@/utils/forms';
import { PERMISSION_PRESETS } from '@/utils/permissionEditor';

export default function NewSellerScreen() {
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const groups = usePermissionGroups();
  const [permissions, setPermissions] = useState<Permission[]>(PERMISSION_PRESETS.counter);
  const [formError, setFormError] = useState<string | null>(null);
  const schema = z.object({
    name: requiredText(t),
    email: emailField(t),
    phone: z.string().trim().refine((v) => !v || /^[6-9]\d{9}$/.test(v), t('staff.validation.phone')),
    password: newPasswordField(t),
  });
  type Values = z.infer<typeof schema>;
  const { control, handleSubmit, setError, formState } = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { name: '', email: '', phone: '', password: '' },
  });

  const save = handleSubmit(async (v) => {
    setFormError(null);
    try {
      const { data } = await sellerApi.create({
        name: v.name.trim(),
        email: v.email.trim(),
        phone: orNull(v.phone),
        password: v.password,
        password_confirmation: v.password,
        permissions,
      });
      await refreshAfterChange();
      toast.success(t('staff.sellers.created'));
      router.replace({ pathname: '/staff/sellers/[id]', params: { id: String(data.id) } });
    } catch (error) {
      const leftovers = applyServerErrors(error, setError, ['name', 'email', 'phone', 'password'] as const);
      const permissionError = isApiError(error) ? error.fieldError('permissions') : undefined;
      setFormError(permissionError ?? leftovers[0] ?? errorMessage(error, t));
    }
  });

  return (
    <View style={[styles.root, { backgroundColor: colors.background }]}>
      <ScreenHeader title={t('staff.sellers.newTitle')} />
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <Card>
          <FormText control={control} name="name" label={t('staff.sellers.name')} />
          <FormText control={control} name="email" label={t('auth.email')} keyboardType="email-address" autoCapitalize="none" />
          <FormText control={control} name="phone" label={`${t('staff.sellers.phone')} (${t('staff.common.optional')})`} keyboardType="phone-pad" />
          <FormText control={control} name="password" label={t('staff.sellers.startPassword')} hint={t('staff.sellers.startPasswordHint')} secure />
        </Card>
        <Card>
          <AppText size="subtitle" weight="semibold">
            {t('staff.sellers.permissions')}
          </AppText>
          {groups.data ? <PermissionEditor groups={groups.data} value={permissions} onChange={setPermissions} /> : <LoadingView />}
        </Card>
        {formError && <AppText color="danger">{formError}</AppText>}
        <Button title={t('staff.sellers.create')} onPress={() => void save()} loading={formState.isSubmitting} fullWidth />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  content: { width: '100%', maxWidth: 720, alignSelf: 'center', padding: spacing.lg, gap: spacing.md, paddingBottom: spacing.xxxl },
});
