/**
 * Push notifications for staff (Expo push service → FCM on Android, APNs on iOS).
 * Registration needs the EAS project ID (added when the app is set up for store builds, Phase 12)
 * and a real build — remote push doesn't work in Expo Go on Android. Until then this quietly does nothing.
 */
import Constants from 'expo-constants';
import * as Notifications from 'expo-notifications';
import { AndroidImportance } from 'expo-notifications';
import { Platform } from 'react-native';

import { deviceApi } from '@/api/staff/endpoints';

export const PUSH_CHANNEL_ID = 'alerts'; // must match the server's PUSH_CHANNEL_ID

let registeredToken: string | null = null;

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowBanner: true,
    shouldShowList: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

const projectId = (): string | undefined =>
  (Constants.expoConfig?.extra?.eas?.projectId as string | undefined) ?? Constants.easConfig?.projectId;

/** Ask permission (once) and send this phone's push token to the server. Never throws. */
export async function registerForPush(alertsTitle: string): Promise<string | null> {
  if (Platform.OS === 'web' || !projectId()) return null;
  try {
    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync(PUSH_CHANNEL_ID, {
        name: alertsTitle,
        importance: AndroidImportance.HIGH,
      });
    }
    let { status } = await Notifications.getPermissionsAsync();
    if (status !== 'granted') status = (await Notifications.requestPermissionsAsync()).status;
    if (status !== 'granted') return null;

    const { data: token } = await Notifications.getExpoPushTokenAsync({ projectId: projectId() });
    await deviceApi.register(token, Platform.OS === 'ios' ? 'ios' : 'android');
    registeredToken = token;
    return token;
  } catch {
    return null; // offline, Expo Go, or push not configured yet — try again next time
  }
}

/** On logout: stop pushes to this phone for the user who is leaving. */
export async function unregisterPush(): Promise<void> {
  if (!registeredToken) return;
  try {
    await deviceApi.remove(registeredToken);
  } catch {
    // The server also clears devices when a session ends; nothing else to do here.
  }
  registeredToken = null;
}

export { routeForNotification } from '@/utils/notificationRoutes';
