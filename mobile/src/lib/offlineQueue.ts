/**
 * Stock changes made without internet are kept on the phone and sent when the connection returns.
 *
 * Each change keeps the Idempotency-Key it was created with, so sending it again after a lost reply
 * can never move stock twice — the server recognises the key and returns the first result.
 * Changes are sent one at a time, oldest first. If the server refuses one (e.g. "not enough stock"),
 * it stays in the list with the reason, for the user to retry or discard; the rest keep going.
 */
import AsyncStorage from '@react-native-async-storage/async-storage';
import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';

import { inventoryApi, type StockKind } from '@/api/staff/endpoints';
import { API_ERROR_CODES, isApiError } from '@/api/errors';
import { STORAGE_KEYS } from '@/constants/app';
import { refreshAfterChange } from '@/hooks/useStaff';
import { isOnline } from '@/lib/network';

export interface QueuedChange {
  key: string; // Idempotency-Key, also the item's id
  kind: StockKind;
  body: Record<string, unknown>;
  /** Short description for the list, e.g. "Amul Butter 500g · Stock out · 2 pcs". */
  label: string;
  createdAt: string;
  /** Set when the server refused the change; the user decides what to do. */
  error?: string;
}

interface QueueState {
  items: QueuedChange[];
  syncing: boolean;
  add: (item: Omit<QueuedChange, 'createdAt'>) => void;
  remove: (key: string) => void;
  retry: (key: string) => void;
  clear: () => void;
  sync: () => Promise<void>;
}

/** Only connection problems are worth waiting for; anything else is a real answer from the server. */
export const isConnectionError = (error: unknown): boolean =>
  isApiError(error) && (error.code === API_ERROR_CODES.network || error.code === API_ERROR_CODES.timeout);

export const useOfflineQueue = create<QueueState>()(
  persist(
    (set, get) => ({
      items: [],
      syncing: false,

      add: (item) => set((s) => ({ items: [...s.items, { ...item, createdAt: new Date().toISOString() }] })),
      remove: (key) => set((s) => ({ items: s.items.filter((i) => i.key !== key) })),
      retry: (key) => {
        set((s) => ({ items: s.items.map((i) => (i.key === key ? { ...i, error: undefined } : i)) }));
        void get().sync();
      },
      clear: () => set({ items: [] }),

      async sync() {
        if (get().syncing || !isOnline()) return;
        set({ syncing: true });
        let sent = 0;
        try {
          for (const item of get().items.filter((i) => !i.error)) {
            try {
              await inventoryApi.move(item.kind, item.body, item.key);
              get().remove(item.key);
              sent += 1;
            } catch (error) {
              if (isConnectionError(error)) break; // still offline: try again later, in the same order
              const reason = isApiError(error) ? error.message : String(error);
              set((s) => ({ items: s.items.map((i) => (i.key === item.key ? { ...i, error: reason } : i)) }));
            }
          }
        } finally {
          set({ syncing: false });
          if (sent) await refreshAfterChange();
        }
      },
    }),
    {
      name: STORAGE_KEYS.offlineQueue,
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (s) => ({ items: s.items }), // "syncing" is never saved
    },
  ),
);

/** Changes still waiting to be sent (including refused ones). */
export const usePendingCount = () => useOfflineQueue((s) => s.items.length);
