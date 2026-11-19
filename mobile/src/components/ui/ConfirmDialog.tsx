/** Cross-platform confirmation dialog (Alert.alert has no buttons on web). */
import { useTranslation } from 'react-i18next';
import { Modal, Pressable, StyleSheet, View } from 'react-native';

import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, spacing } from '@/theme/tokens';

import { AppText } from './AppText';
import { Button } from './Button';

export function ConfirmDialog({
  visible,
  title,
  message,
  confirmLabel,
  destructive,
  loading,
  onConfirm,
  onCancel,
}: {
  visible: boolean;
  title: string;
  /** Extra explanation under the title (e.g. what will be lost). */
  message?: string;
  confirmLabel: string;
  destructive?: boolean;
  loading?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const { colors } = useAppTheme();
  const { t } = useTranslation();
  return (
    <Modal transparent visible={visible} animationType="fade" onRequestClose={onCancel}>
      <Pressable style={[styles.backdrop, { backgroundColor: colors.overlay }]} onPress={onCancel}>
        <Pressable style={[styles.dialog, { backgroundColor: colors.surface }]} accessibilityViewIsModal>
          <AppText size="subtitle" weight="semibold">
            {title}
          </AppText>
          {message && <AppText color="textMuted">{message}</AppText>}
          <View style={styles.actions}>
            <Button title={t('common.cancel')} variant="ghost" onPress={onCancel} />
            <Button
              title={confirmLabel}
              variant={destructive ? 'danger' : 'primary'}
              loading={loading}
              onPress={onConfirm}
            />
          </View>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing.xl },
  dialog: { width: '100%', maxWidth: 420, borderRadius: radius.lg, padding: spacing.xl, gap: spacing.xl },
  actions: { flexDirection: 'row', justifyContent: 'flex-end', gap: spacing.md },
});
