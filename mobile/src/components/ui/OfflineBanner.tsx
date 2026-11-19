/**
 * Small floating pill when there is no internet, or when stock changes are waiting to be sent.
 * Tapping it (staff) opens the list of unsent changes.
 */
import Ionicons from '@expo/vector-icons/Ionicons';
import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { Pressable, StyleSheet } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useSession } from '@/auth/session';
import { OFFLINE_BANNER_BOTTOM_OFFSET } from '@/constants/app';
import { useIsOnline } from '@/lib/network';
import { useOfflineQueue } from '@/lib/offlineQueue';
import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, shadow, spacing } from '@/theme/tokens';

import { AppText } from './AppText';

export function OfflineBanner() {
  const { t } = useTranslation();
  const { colors, scheme } = useAppTheme();
  const insets = useSafeAreaInsets();
  const online = useIsOnline();
  const isStaff = useSession((s) => s.status === 'staff');
  const pending = useOfflineQueue((s) => s.items.length);
  const syncing = useOfflineQueue((s) => s.syncing);

  if (online && !(isStaff && pending)) return null;

  const message = !online
    ? isStaff && pending
      ? t('offline.offlineWithPending', { count: pending })
      : t('offline.banner')
    : syncing
      ? t('offline.syncing', { count: pending })
      : t('offline.pending', { count: pending });

  return (
    <Pressable
      accessibilityRole={isStaff && pending ? 'button' : 'text'}
      accessibilityLiveRegion="polite"
      disabled={!(isStaff && pending)}
      onPress={() => router.push('/staff/pending')}
      style={[
        styles.pill,
        { bottom: insets.bottom + OFFLINE_BANNER_BOTTOM_OFFSET, backgroundColor: online ? colors.primary : colors.text },
        shadow('high', colors.shadow, scheme),
      ]}
    >
      <Ionicons
        name={online ? 'cloud-upload-outline' : 'cloud-offline-outline'}
        size={18}
        color={online ? colors.textOnPrimary : colors.background}
      />
      <AppText size="small" weight="semibold" style={{ color: online ? colors.textOnPrimary : colors.background }}>
        {message}
      </AppText>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  pill: {
    position: 'absolute',
    alignSelf: 'center',
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    borderRadius: radius.pill,
    maxWidth: '92%',
  },
});
