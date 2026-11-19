import AsyncStorage from '@react-native-async-storage/async-storage';
import { createAsyncStoragePersister } from '@tanstack/query-async-storage-persister';
import { QueryClient } from '@tanstack/react-query';
import type { PersistQueryClientOptions } from '@tanstack/react-query-persist-client';
import Constants from 'expo-constants';

import { isApiError } from '@/api/errors';
import { OFFLINE_CACHE_MAX_AGE_MS, QUERY_RETRY_COUNT, QUERY_STALE_MS, STORAGE_KEYS } from '@/constants/app';

const NO_RETRY_STATUSES = new Set([400, 401, 403, 404, 409, 422]);

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: QUERY_STALE_MS,
      gcTime: OFFLINE_CACHE_MAX_AGE_MS, // kept in memory as long as it is kept on the device
      // Retry only problems that can go away by themselves (network, server hiccups).
      retry: (count, error) =>
        count < QUERY_RETRY_COUNT && !(isApiError(error) && NO_RETRY_STATUSES.has(error.status)),
    },
  },
});

/**
 * Loaded data is also saved on the device, so screens open with the last known data when offline
 * (and instantly on the next app start). A new app version starts with a fresh cache.
 */
export const persistOptions: Omit<PersistQueryClientOptions, 'queryClient'> = {
  persister: createAsyncStoragePersister({ storage: AsyncStorage, key: STORAGE_KEYS.queryCache }),
  maxAge: OFFLINE_CACHE_MAX_AGE_MS,
  buster: Constants.expoConfig?.version ?? '1',
  dehydrateOptions: { shouldDehydrateQuery: (query) => query.state.status === 'success' },
};

/** Forget all loaded data, in memory and on the device (on logout: never show one user's data to the next). */
export async function clearSavedData(): Promise<void> {
  queryClient.clear();
  await persistOptions.persister.removeClient();
}

export const queryKeys = {
  publicStore: ['public', 'store'] as const,
  publicCategories: ['public', 'categories'] as const,
  publicCategory: (slug: string) => ['public', 'category', slug] as const,
  publicProducts: (query: object) => ['public', 'products', query] as const,
  publicHighlights: (kind: 'featured' | 'new' | 'offers') => ['public', 'highlights', kind] as const,
  publicProduct: (slug: string) => ['public', 'product', slug] as const,
  me: ['auth', 'me'] as const,
};
