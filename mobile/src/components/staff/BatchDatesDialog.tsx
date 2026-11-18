/** Correct a batch's number and dates (never its quantity). */
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Modal, Pressable, StyleSheet, View } from 'react-native';

import { inventoryApi } from '@/api/staff/endpoints';
import { isApiError } from '@/api/errors';
import type { Batch } from '@/api/staff/types';
import { AppText, Button, TextField, toast } from '@/components/ui';
import { refreshAfterChange } from '@/hooks/useStaff';
import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, spacing } from '@/theme/tokens';
import { apiToDisplayDate, displayToApiDate, isValidDisplayDate } from '@/utils/dates';
import { errorMessage } from '@/utils/errors';
import { orNull } from '@/utils/forms';

export function BatchDatesDialog({ batch, onClose }: { batch: Batch | null; onClose: () => void }) {
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const [number, setNumber] = useState('');
  const [expiry, setExpiry] = useState('');
  const [manufacturing, setManufacturing] = useState('');
  const [errors, setErrors] = useState<Record<string, string | undefined>>({});
  const [saving, setSaving] = useState(false);

  const save = async () => {
    if (!batch) return;
    const e: Record<string, string> = {};
    if (expiry && !isValidDisplayDate(expiry)) e.expiry = t('staff.validation.date');
    if (manufacturing && !isValidDisplayDate(manufacturing)) e.manufacturing = t('staff.validation.date');
    setErrors(e);
    if (Object.keys(e).length) return;
    setSaving(true);
    try {
      await inventoryApi.updateBatch(batch.id, {
        batch_number: orNull(number) ?? batch.batch_number,
        expiry_date: displayToApiDate(expiry),
        manufacturing_date: displayToApiDate(manufacturing),
      });
      await refreshAfterChange();
      toast.success(t('staff.common.saved'));
      onClose();
    } catch (error) {
      const field = (name: string) => (isApiError(error) ? error.fieldError(name) : undefined);
      setErrors({ expiry: field('expiry_date'), manufacturing: field('manufacturing_date'), form: errorMessage(error, t) });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal
      transparent
      visible={!!batch}
      animationType="fade"
      onRequestClose={onClose}
      onShow={() => {
        setNumber(batch?.batch_number ?? '');
        setExpiry(apiToDisplayDate(batch?.expiry_date));
        setManufacturing(apiToDisplayDate(batch?.manufacturing_date));
        setErrors({});
      }}
    >
      <Pressable style={[styles.backdrop, { backgroundColor: colors.overlay }]} onPress={onClose}>
        <Pressable style={[styles.dialog, { backgroundColor: colors.surface }]}>
          <AppText size="subtitle" weight="semibold">
            {t('staff.expiry.editDates')}
          </AppText>
          <TextField label={t('staff.stock.batchNumber')} value={number} onChangeText={setNumber} autoCapitalize="characters" />
          <TextField label={t('staff.stock.expiryDate')} placeholder={t('staff.common.dateHint')} value={expiry} onChangeText={setExpiry} error={errors.expiry} />
          <TextField
            label={`${t('staff.stock.manufacturingDate')} (${t('staff.common.optional')})`}
            placeholder={t('staff.common.dateHint')}
            value={manufacturing}
            onChangeText={setManufacturing}
            error={errors.manufacturing}
          />
          {errors.form && <AppText color="danger">{errors.form}</AppText>}
          <View style={styles.actions}>
            <Button title={t('common.cancel')} variant="ghost" onPress={onClose} />
            <Button title={t('staff.common.save')} onPress={() => void save()} loading={saving} />
          </View>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing.xl },
  dialog: { width: '100%', maxWidth: 440, borderRadius: radius.lg, padding: spacing.xl, gap: spacing.md },
  actions: { flexDirection: 'row', justifyContent: 'flex-end', gap: spacing.md },
});
