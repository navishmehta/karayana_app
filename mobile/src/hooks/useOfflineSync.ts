/** Staff area: send queued stock changes on app start and whenever the internet comes back. */
import { onlineManager } from '@tanstack/react-query';
import { useEffect } from 'react';

import { useOfflineQueue } from '@/lib/offlineQueue';

export function useOfflineSync(): void {
  useEffect(() => {
    const sync = () => void useOfflineQueue.getState().sync();
    sync();
    return onlineManager.subscribe((online) => {
      if (online) sync();
    });
  }, []);
}
