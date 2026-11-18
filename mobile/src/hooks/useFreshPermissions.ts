import { useEffect } from 'react';
import { AppState } from 'react-native';

import { useSession } from '@/auth/session';

/**
 * Reload the staff member's permissions when the staff area opens and whenever the app returns
 * to the foreground, so changes the admin made (or a deactivation) take effect without logging in again.
 */
export function useFreshPermissions(): void {
  useEffect(() => {
    void useSession.getState().reloadUser();
    const subscription = AppState.addEventListener('change', (state) => {
      if (state === 'active') void useSession.getState().reloadUser();
    });
    return () => subscription.remove();
  }, []);
}
