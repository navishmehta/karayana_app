/** Data hooks for the customer catalogue (React Query). */
import { useInfiniteQuery, useQuery } from '@tanstack/react-query';

import { publicApi } from '@/api/endpoints';
import { queryKeys } from '@/lib/queryClient';
import type { CatalogueQuery } from '@/utils/catalogue';

export const useStoreInfo = () =>
  useQuery({ queryKey: queryKeys.publicStore, queryFn: publicApi.store, select: (r) => r.data });

export const useCategories = () =>
  useQuery({ queryKey: queryKeys.publicCategories, queryFn: publicApi.categories, select: (r) => r.data });

export const useCategory = (slug: string) =>
  useQuery({ queryKey: queryKeys.publicCategory(slug), queryFn: () => publicApi.category(slug), select: (r) => r.data });

export const useProduct = (slug: string) =>
  useQuery({ queryKey: queryKeys.publicProduct(slug), queryFn: () => publicApi.product(slug), select: (r) => r.data });

const highlightFetchers = { featured: publicApi.featured, new: publicApi.newArrivals, offers: publicApi.offers };

export const useHighlights = (kind: keyof typeof highlightFetchers, enabled = true) =>
  useQuery({
    queryKey: queryKeys.publicHighlights(kind),
    queryFn: highlightFetchers[kind],
    select: (r) => r.data,
    enabled,
  });

/** Paged product list that loads the next page as the user scrolls. */
export function useProductPages(query: CatalogueQuery) {
  const result = useInfiniteQuery({
    queryKey: queryKeys.publicProducts(query),
    queryFn: ({ pageParam }) => publicApi.products(query, pageParam),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.meta.page < last.meta.last_page ? last.meta.page + 1 : undefined),
  });
  return {
    ...result,
    products: result.data?.pages.flatMap((p) => p.data) ?? [],
    total: result.data?.pages[0]?.meta.total ?? 0,
  };
}
