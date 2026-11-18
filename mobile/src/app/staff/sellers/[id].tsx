import { useMutation } from '@tanstack/react-query';
import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Modal, Pressable, ScrollView, StyleSheet, View } from 'react-native';

import { sellerApi } from '@/api/staff/endpoints';
import { isApiError } from '@/api/errors';
import { PermissionEditor } from '@/components/staff/PermissionEditor';
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
  TextField,
  toast,
} from '@/components/ui';
import type { Permission } from '@/constants/permissions';
import { refreshAfterChange, usePermissionGroups, useSeller, useSellerActivity } from '@/hooks/useStaff';
import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, spacing } from '@/theme/tokens';
import { errorMessage } from '@/utils/errors';
import { formatDateTime } from '@/utils/format';

const ACTIVITY_ROWS = 10;

export default function SellerScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const sellerId = Number(id);
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const seller = useSeller(sellerId);
  const groups = usePermissionGroups();
  const activity = useSellerActivity(sellerId);
  // Unsaved edits only; without edits the saved permissions are shown.
  const [draft, setDraft] = useState<Permission[] | null>(null);
  const [dialog, setDialog] = useState<'delete' | 'password' | null>(null);
  const [password, setPassword] = useState('');
  const [passwordError, setPasswordError] = useState<string | undefined>();

  const onError = (e: unknown) => toast.error(isApiError(e) && e.fieldError('permissions') ? e.fieldError('permissions')! : errorMessage(e, t));
  const done = (message: string) => () => {
    void refreshAfterChange();
    toast.success(message);
  };
  const savePermissions = useMutation({
    mutationFn: (next: Permission[]) => sellerApi.setPermissions(sellerId, next),
    onSuccess: () => {
      setDraft(null);
      done(t('staff.sellers.permissionsSaved'))();
    },
    onError,
  });
  const setActive = useMutation({ mutationFn: (active: boolean) => sellerApi.setActive(sellerId, active), onSuccess: done(t('staff.common.saved')), onError });
  const resetPassword = useMutation({
    mutationFn: () => sellerApi.resetPassword(sellerId, password),
    onSuccess: () => {
      toast.success(t('staff.sellers.passwordReset'));
      setDialog(null);
      setPassword('');
    },
    onError: (e) => setPasswordError(isApiError(e) ? (e.fieldError('password') ?? e.message) : errorMessage(e, t)),
  });
  const remove = useMutation({
    mutationFn: () => sellerApi.remove(sellerId),
    onSuccess: () => {
      void refreshAfterChange();
      toast.success(t('staff.common.deleted'));
      router.back();
    },
    onError,
  });

  if (seller.isPending) return <LoadingView />;
  if (seller.isError) return <ErrorState message={errorMessage(seller.error, t)} onRetry={() => void seller.refetch()} />;
  const s = seller.data;
  const permissions = draft ?? s.permissions;
  const permissionsChanged = [...permissions].sort().join() !== [...s.permissions].sort().join();

  return (
    <View style={[styles.root, { backgroundColor: colors.background }]}>
      <ScreenHeader title={s.name} />
      <ScrollView contentContainerStyle={styles.content}>
        <Card>
          <AppText size="subtitle" weight="semibold">
            {s.name}
          </AppText>
          <AppText color="textMuted">{[s.email, s.phone].filter(Boolean).join(' · ')}</AppText>
          <View style={styles.badges}>
            <Badge label={s.is_active ? t('staff.common.active') : t('staff.common.inactive')} tone={s.is_active ? 'success' : 'textMuted'} />
            <Badge label={t('staff.sellers.sessions', { count: s.active_sessions })} tone="textMuted" />
          </View>
          <AppText size="small" color="textMuted">
            {t('staff.sellers.lastLogin', { when: s.last_login_at ? formatDateTime(s.last_login_at) : t('staff.sellers.never') })}
          </AppText>
          <SwitchRow label={t('staff.sellers.active')} hint={t('staff.sellers.activeHint')} value={s.is_active} onChange={(v) => setActive.mutate(v)} disabled={setActive.isPending} />
        </Card>

        <Card>
          <AppText size="subtitle" weight="semibold">
            {t('staff.sellers.permissions')}
          </AppText>
          {groups.data ? <PermissionEditor groups={groups.data} value={permissions} onChange={setDraft} /> : <LoadingView />}
          <Button title={t('staff.sellers.savePermissions')} onPress={() => savePermissions.mutate(permissions)} loading={savePermissions.isPending} disabled={!permissionsChanged} fullWidth />
        </Card>

        <Card>
          <AppText size="subtitle" weight="semibold">
            {t('staff.sellers.activity')}
          </AppText>
          {activity.items.length === 0 ? (
            <AppText color="textMuted">{t('staff.activity.empty')}</AppText>
          ) : (
            activity.items.slice(0, ACTIVITY_ROWS).map((a) => <ListRow key={a.id} title={a.description} subtitle={formatDateTime(a.created_at)} chevron={false} />)
          )}
        </Card>

        <Button title={t('staff.sellers.resetPassword')} variant="secondary" onPress={() => setDialog('password')} />
        <Button title={t('staff.sellers.delete')} variant="danger" onPress={() => setDialog('delete')} />
      </ScrollView>

      <ConfirmDialog
        visible={dialog === 'delete'}
        title={t('staff.sellers.deleteConfirm', { name: s.name })}
        confirmLabel={t('staff.common.delete')}
        destructive
        loading={remove.isPending}
        onCancel={() => setDialog(null)}
        onConfirm={() => remove.mutate()}
      />
      <Modal transparent visible={dialog === 'password'} animationType="fade" onRequestClose={() => setDialog(null)}>
        <Pressable style={[styles.backdrop, { backgroundColor: colors.overlay }]} onPress={() => setDialog(null)}>
          <Pressable style={[styles.dialog, { backgroundColor: colors.surface }]}>
            <AppText size="subtitle" weight="semibold">
              {t('staff.sellers.resetPassword')}
            </AppText>
            <AppText size="small" color="textMuted">
              {t('staff.sellers.resetPasswordHint')}
            </AppText>
            <TextField label={t('auth.newPassword')} value={password} onChangeText={(v) => { setPassword(v); setPasswordError(undefined); }} secure error={passwordError} />
            <View style={styles.dialogActions}>
              <Button title={t('common.cancel')} variant="ghost" onPress={() => setDialog(null)} />
              <Button title={t('staff.common.save')} onPress={() => resetPassword.mutate()} loading={resetPassword.isPending} disabled={!password} />
            </View>
          </Pressable>
        </Pressable>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  content: { width: '100%', maxWidth: 720, alignSelf: 'center', padding: spacing.lg, gap: spacing.md, paddingBottom: spacing.xxxl },
  badges: { flexDirection: 'row', gap: spacing.sm, flexWrap: 'wrap' },
  backdrop: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing.xl },
  dialog: { width: '100%', maxWidth: 440, borderRadius: radius.lg, padding: spacing.xl, gap: spacing.md },
  dialogActions: { flexDirection: 'row', justifyContent: 'flex-end', gap: spacing.md },
});
