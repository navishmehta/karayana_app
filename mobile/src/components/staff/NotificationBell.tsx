import Ionicons from '@expo/vector-icons/Ionicons';
import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { StyleSheet, View } from 'react-native';

import { AppText, PressableScale } from '@/components/ui';
import { useUnreadCount } from '@/hooks/useStaff';
import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, spacing, TOUCH_TARGET } from '@/theme/tokens';

const MAX_BADGE = 99;
const GLASS = 'rgba(255, 255, 255, 0.16)';
const GLASS_BORDER = 'rgba(255, 255, 255, 0.3)';

/** `onHero`: frosted-glass look for use on top of a green hero header. */
export function NotificationBell({ onHero }: { onHero?: boolean }) {
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const unread = useUnreadCount().data ?? 0;
  return (
    <PressableScale
      accessibilityRole="button"
      accessibilityLabel={t('staff.notifications.bell', { count: unread })}
      onPress={() => router.push('/staff/notifications')}
      style={[
        styles.bell,
        onHero ? styles.glass : { backgroundColor: colors.surface, borderColor: colors.border },
      ]}
    >
      <Ionicons name="notifications-outline" size={24} color={onHero ? colors.textOnHero : colors.text} />
      {unread > 0 && (
        <View style={[styles.badge, { backgroundColor: colors.danger }]}>
          <AppText size="caption" weight="bold" color="textOnPrimary">
            {unread > MAX_BADGE ? `${MAX_BADGE}+` : unread}
          </AppText>
        </View>
      )}
    </PressableScale>
  );
}

const styles = StyleSheet.create({
  bell: { width: TOUCH_TARGET, height: TOUCH_TARGET, borderRadius: radius.pill, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  glass: { backgroundColor: GLASS, borderColor: GLASS_BORDER },
  badge: {
    position: 'absolute',
    top: -spacing.xxs,
    right: -spacing.xxs,
    minWidth: 20,
    height: 20,
    paddingHorizontal: spacing.xxs,
    borderRadius: radius.pill,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
