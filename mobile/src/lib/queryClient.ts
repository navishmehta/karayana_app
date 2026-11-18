import { QueryClient } from '@tanstack/react-query';

import { isApiError } from '@/api/errors';
import { QUERY_RETRY_COUNT, QUERY_STALE_MS } from '@/constants/app';

const NO_RETRY_STATUSES = new Set([400, 401, 403, 404, 409, 422]);

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: QUERY_STALE_MS,
      // Retry only problems that can go away by themselves (network, server hiccups).
      retry: (count, error) =>
        count < QUERY_RETRY_COUNT && !(isApiError(error) && NO_RETRY_STATUSES.has(error.status)),
    },
  },
});

export const queryKeys = {
  publicStore: ['public', 'store'] as const,
  publicCategories: ['public', 'categories'] as const,
  publicCategory: (slug: string) => ['public', 'category', slug] as const,
  publicProducts: (query: object) => ['public', 'products', query] as const,
  publicHighlights: (kind: 'featured' | 'new' | 'offers') => ['public', 'highlights', kind] as const,
  publicProduct: (slug: string) => ['public', 'product', slug] as const,
  me: ['auth', 'me'] as const,
};
