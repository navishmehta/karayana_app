import Ionicons from '@expo/vector-icons/Ionicons';
import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { Pressable, StyleSheet, View } from 'react-native';

import { AppText } from '@/components/ui';
import { useUnreadCount } from '@/hooks/useStaff';
import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, spacing, TOUCH_TARGET } from '@/theme/tokens';

const MAX_BADGE = 99;

export function NotificationBell() {
  const { t } = useTranslation();
  const { colors } = useAppTheme();
  const unread = useUnreadCount().data ?? 0;
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={t('staff.notifications.bell', { count: unread })}
      onPress={() => router.push('/staff/notifications')}
      style={[styles.bell, { backgroundColor: colors.surface, borderColor: colors.border }]}
    >
      <Ionicons name="notifications-outline" size={24} color={colors.text} />
      {unread > 0 && (
        <View style={[styles.badge, { backgroundColor: colors.danger }]}>
          <AppText size="caption" weight="bold" color="textOnPrimary">
            {unread > MAX_BADGE ? `${MAX_BADGE}+` : unread}
          </AppText>
        </View>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  bell: { width: TOUCH_TARGET, height: TOUCH_TARGET, borderRadius: radius.pill, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
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
