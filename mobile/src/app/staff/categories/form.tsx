import { zodResolver } from '@hookform/resolvers/zod';
import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { ScrollView, StyleSheet, View } from 'react-native';
import { z } from 'zod';

import { categoryApi } from '@/api/staff/endpoints';
import type { StaffCategory } from '@/api/staff/types';
import { categoryFormAccess } from '@/auth/access';
import { useSession } from '@/auth/session';
import { ProductImage } from '@/components/catalogue/ProductImage';
import { FormText } from '@/components/forms/FormText';
import { AppText, Button, Card, ConfirmDialog, ErrorState, LoadingView, ScreenHeader, SwitchRow, toast } from '@/components/ui';
import { refreshAfterChange, useStaffCategory } from '@/hooks/useStaff';
import { pickImageForm } from '@/lib/images';
import { requiredText } from '@/lib/staffValidation';
import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, spacing } from '@/theme/tokens';
import { errorMessage } from '@/utils/errors';
import { applyServerErrors, orNull } from '@/utils/forms';

const IMAGE_SIZE = 96;

export default function CategoryFormScreen() {
  const { id } = useLocalSearchParams<{ id?: string }>();
  const categoryId = id ? Number(id) : null;
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const category = useStaffCategory(categoryId);

  if (categoryId && category.isPending) return <LoadingView />;
  if (categoryId && category.isError) return <ErrorState message={errorMessage(category.error, t)} onRetry={() => void category.refetch()} />;
  return (
    <View style={[styles.root, { backgroundColor: colors.background }]}>
      <ScreenHeader title={categoryId ? t('staff.categories.editTitle') : t('staff.categories.newTitle')} />
      <CategoryForm category={category.data} />
    </View>
  );
}

function CategoryForm({ category }: { category?: StaffCategory }) {
  const { t } = useTranslation();
  const access = categoryFormAccess(useSession((s) => s.user), !!category);
  const [image, setImage] = useState<{ form: FormData | null; preview: string | null }>({ form: null, preview: category?.image_thumb_url ?? null });
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const schema = z.object({ name: requiredText(t), namePa: z.string(), description: z.string(), isActive: z.boolean() });
  type Values = z.infer<typeof schema>;
  const { control, handleSubmit, setError, formState } = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: category?.name ?? '',
      namePa: category?.name_translations.pa ?? '',
      description: category?.description ?? '',
      isActive: category?.is_active ?? true,
    },
  });

  const chooseImage = async () => {
    const form = await pickImageForm();
    if (form) setImage({ form, preview: null });
  };

  const save = handleSubmit(async (v) => {
    setFormError(null);
    const body = {
      name: v.name.trim(),
      name_translations: v.namePa.trim() ? { pa: v.namePa.trim() } : null,
      description: orNull(v.description),
      is_active: v.isActive,
    };
    try {
      const saved = category ? await categoryApi.update(category.id, body) : await categoryApi.create(body);
      if (access.editImage && image.form) await categoryApi.uploadImage(saved.data.id, image.form);
      else if (access.editImage && category?.image_url && !image.preview) await categoryApi.removeImage(category.id);
      await refreshAfterChange();
      toast.success(t('staff.common.saved'));
      router.back();
    } catch (error) {
      const leftovers = applyServerErrors(error, setError, ['name', 'namePa', 'description'] as const, { name_translations: 'namePa' });
      setFormError(leftovers[0] ?? errorMessage(error, t));
    }
  });

  const remove = async () => {
    if (!category) return;
    setBusy(true);
    try {
      await categoryApi.remove(category.id);
      await refreshAfterChange();
      toast.success(t('staff.common.deleted'));
      router.back();
    } catch (error) {
      toast.error(errorMessage(error, t)); // e.g. "This category still has products…"
      setConfirmDelete(false);
    } finally {
      setBusy(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
      <Card>
        <FormText control={control} name="name" label={t('staff.categories.name')} />
        <FormText control={control} name="namePa" label={`${t('staff.categories.punjabiName')} (${t('staff.common.optional')})`} hint={t('staff.categories.punjabiHint')} />
        <FormText control={control} name="description" label={`${t('staff.products.description')} (${t('staff.common.optional')})`} multiline />
        <Controller control={control} name="isActive" render={({ field }) => <SwitchRow label={t('staff.categories.active')} hint={t('staff.categories.activeHint')} value={field.value} onChange={field.onChange} />} />
      </Card>
      {access.editImage && (
      <Card>
        <AppText weight="semibold">{t('staff.categories.image')}</AppText>
        <View style={styles.imageRow}>
          {image.form ? (
            <AppText color="success">{t('staff.categories.imageChosen')}</AppText>
          ) : (
            <ProductImage uri={image.preview} style={styles.image} />
          )}
          <View style={styles.imageButtons}>
            <Button title={t('staff.categories.changeImage')} variant="secondary" onPress={() => void chooseImage()} />
            {(image.preview || image.form) && <Button title={t('staff.categories.removeImage')} variant="ghost" onPress={() => setImage({ form: null, preview: null })} />}
          </View>
        </View>
      </Card>
      )}
      {formError && <AppText color="danger">{formError}</AppText>}
      <Button title={t('staff.common.save')} onPress={() => void save()} loading={formState.isSubmitting} fullWidth />
      {access.remove && <Button title={t('staff.categories.delete')} variant="danger" onPress={() => setConfirmDelete(true)} />}
      <ConfirmDialog
        visible={confirmDelete}
        title={t('staff.categories.deleteConfirm', { name: category?.name })}
        confirmLabel={t('staff.common.delete')}
        destructive
        loading={busy}
        onCancel={() => setConfirmDelete(false)}
        onConfirm={() => void remove()}
      />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  content: { width: '100%', maxWidth: 720, alignSelf: 'center', padding: spacing.lg, gap: spacing.md, paddingBottom: spacing.xxxl },
  imageRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.lg },
  image: { width: IMAGE_SIZE, borderRadius: radius.md },
  imageButtons: { flex: 1, gap: spacing.sm },
});
