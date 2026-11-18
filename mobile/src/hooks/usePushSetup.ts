import * as Notifications from 'expo-notifications';
import { router, type Href } from 'expo-router';
import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Platform } from 'react-native';

import { staffKeys } from '@/hooks/useStaff';
import { queryClient } from '@/lib/queryClient';
import { registerForPush } from '@/lib/push';
import { routeForNotification } from '@/utils/notificationRoutes';

/** Staff area: register this phone for alerts, refresh the badge when one arrives, open the right screen on tap. */
export function usePushSetup(): void {
  const { t } = useTranslation();

  useEffect(() => {
    if (Platform.OS === 'web') return;
    void registerForPush(t('staff.notifications.channelName'));

    const received = Notifications.addNotificationReceivedListener(() => {
      void queryClient.invalidateQueries({ queryKey: staffKeys.unreadCount });
    });
    const tapped = Notifications.addNotificationResponseReceivedListener((response) => {
      const route = routeForNotification(response.notification.request.content.data as Record<string, unknown>);
      if (route) router.push(route as Href);
    });
    return () => {
      received.remove();
      tapped.remove();
    };
  }, [t]);
}
