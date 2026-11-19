/**
 * Online / offline awareness for the whole app.
 *  - TanStack Query pauses data loading while offline and refreshes everything when the connection returns.
 *  - Coming back to the app (from the background) refreshes stale data.
 *  - `useIsOnline()` lets any screen react to the connection.
 */
import NetInfo from '@react-native-community/netinfo';
import { focusManager, onlineManager } from '@tanstack/react-query';
import { useSyncExternalStore } from 'react';
import { AppState, Platform } from 'react-native';

let started = false;

export function startNetworkMonitoring(): void {
  if (started) return;
  started = true;
  onlineManager.setEventListener((setOnline) =>
    NetInfo.addEventListener((state) => {
      // isInternetReachable is null while unknown: only a definite "no" counts as offline.
      setOnline(!!state.isConnected && state.isInternetReachable !== false);
    }),
  );
  if (Platform.OS !== 'web') {
    focusManager.setEventListener((setFocused) => {
      const subscription = AppState.addEventListener('change', (status) => setFocused(status === 'active'));
      return () => subscription.remove();
    });
  }
}

export const isOnline = (): boolean => onlineManager.isOnline();

export function useIsOnline(): boolean {
  return useSyncExternalStore(
    (onChange) => onlineManager.subscribe(onChange),
    () => onlineManager.isOnline(),
    () => true,
  );
}
