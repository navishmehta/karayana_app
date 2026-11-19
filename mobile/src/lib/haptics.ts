/** Gentle vibration feedback on phones (nothing on the web). Never throws. */
import * as Haptics from 'expo-haptics';
import { Platform } from 'react-native';

const enabled = Platform.OS === 'ios' || Platform.OS === 'android';

/** A light tick for taps on buttons, cards and tabs. */
export function tapFeedback(): void {
  if (enabled) void Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => undefined);
}

/** A confirming buzz after something is saved. */
export function successFeedback(): void {
  if (enabled) void Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => undefined);
}
