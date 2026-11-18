/** Data hooks for staff screens (React Query). Mutations invalidate the lists they affect. */
import { useInfiniteQuery, useQuery } from '@tanstack/react-query';

import {
  categoryApi,
  dashboardApi,
  expiryApi,
  inventoryApi,
  lookupApi,
  productApi,
  notificationApi,
  reportApi,
  sellerApi,
  settingsApi,
  activityApi,
} from '@/api/staff/endpoints';
import type { Page } from '@/api/types';
import { queryClient } from '@/lib/queryClient';

type Query = Record<string, string | number | boolean | (string | number)[] | undefined>;

export const staffKeys = {
  all: ['staff'] as const,
  dashboard: (days: number) => ['staff', 'dashboard', days] as const,
  categories: (q: Query) => ['staff', 'categories', q] as const,
  category: (id: number) => ['staff', 'category', id] as const,
  units: ['staff', 'units'] as const,
  brands: (search: string) => ['staff', 'brands', search] as const,
  products: (q: Query) => ['staff', 'products', q] as const,
  product: (id: number) => ['staff', 'product', id] as const,
  batches: (id: number) => ['staff', 'batches', id] as const,
  transactions: (q: Query) => ['staff', 'transactions', q] as const,
  expirySummary: ['staff', 'expiry-summary'] as const,
  expiryBatches: (q: Query) => ['staff', 'expiry-batches', q] as const,
  permissions: ['staff', 'permissions'] as const,
  sellers: (q: Query) => ['staff', 'sellers', q] as const,
  seller: (id: number) => ['staff', 'seller', id] as const,
  activity: (q: Query) => ['staff', 'activity', q] as const,
  settings: ['staff', 'settings'] as const,
  reports: ['staff', 'reports'] as const,
  report: (key: string, q: Query) => ['staff', 'report', key, q] as const,
  notifications: (q: Query) => ['staff', 'notifications', q] as const,
  unreadCount: ['staff', 'unread-count'] as const,
  notificationPreferences: ['staff', 'notification-preferences'] as const,
};

/** After any change, refresh staff data and the public catalogue (prices, stock and names may have changed). */
export const refreshAfterChange = () =>
  Promise.all([
    queryClient.invalidateQueries({ queryKey: staffKeys.all }),
    queryClient.invalidateQueries({ queryKey: ['public'] }),
  ]);

/** Infinite list over any paginated staff endpoint. */
function usePaged<T>(key: readonly unknown[], fetch: (page: number) => Promise<Page<T>>, enabled = true) {
  const result = useInfiniteQuery({
    queryKey: key,
    queryFn: ({ pageParam }) => fetch(pageParam),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.meta.page < last.meta.last_page ? last.meta.page + 1 : undefined),
    enabled,
  });
  return { ...result, items: result.data?.pages.flatMap((p) => p.data) ?? [], total: result.data?.pages[0]?.meta.total ?? 0 };
}

const PAGE_SIZE = 30;

export const useDashboard = (days: number, enabled: boolean) =>
  useQuery({ queryKey: staffKeys.dashboard(days), queryFn: () => dashboardApi.get(days), select: (r) => r.data, enabled });

export const useStaffCategories = (q: Query = {}, enabled = true) =>
  useQuery({
    queryKey: staffKeys.categories(q),
    queryFn: () => categoryApi.list({ per_page: 100, ...q }),
    select: (r) => r.data,
    enabled,
  });

export const useStaffCategory = (id: number | null) =>
  useQuery({ queryKey: staffKeys.category(id ?? 0), queryFn: () => categoryApi.get(id!), select: (r) => r.data, enabled: !!id });

export const useUnits = () => useQuery({ queryKey: staffKeys.units, queryFn: lookupApi.units, select: (r) => r.data });

export const useBrands = (search: string, enabled: boolean) =>
  useQuery({ queryKey: staffKeys.brands(search), queryFn: () => lookupApi.brands(search), select: (r) => r.data, enabled });

export const useStaffProducts = (q: Query) =>
  usePaged(staffKeys.products(q), (page) => productApi.list({ ...q, page, per_page: PAGE_SIZE }));

export const useStaffProduct = (id: number | null) =>
  useQuery({ queryKey: staffKeys.product(id ?? 0), queryFn: () => productApi.get(id!), select: (r) => r.data, enabled: !!id });

export const useBatches = (productId: number | null, enabled = true) =>
  useQuery({
    queryKey: staffKeys.batches(productId ?? 0),
    queryFn: () => productApi.batches(productId!),
    select: (r) => r.data,
    enabled: !!productId && enabled,
  });

export const useTransactions = (q: Query, enabled = true) =>
  usePaged(staffKeys.transactions(q), (page) => inventoryApi.transactions({ ...q, page, per_page: PAGE_SIZE }), enabled);

export const useExpirySummary = (enabled: boolean) =>
  useQuery({ queryKey: staffKeys.expirySummary, queryFn: expiryApi.summary, select: (r) => r.data, enabled });

export const useExpiryBatches = (q: Query, enabled: boolean) =>
  usePaged(staffKeys.expiryBatches(q), (page) => expiryApi.batches({ ...q, page, per_page: PAGE_SIZE }), enabled);

export const usePermissionGroups = () =>
  useQuery({ queryKey: staffKeys.permissions, queryFn: sellerApi.permissions, select: (r) => r.data, staleTime: Infinity });

export const useSellers = (q: Query) => usePaged(staffKeys.sellers(q), (page) => sellerApi.list({ ...q, page, per_page: PAGE_SIZE }));

export const useSeller = (id: number | null) =>
  useQuery({ queryKey: staffKeys.seller(id ?? 0), queryFn: () => sellerApi.get(id!), select: (r) => r.data, enabled: !!id });

export const useSellerActivity = (id: number) =>
  usePaged(['staff', 'seller-activity', id], (page) => sellerApi.activity(id, { page, per_page: PAGE_SIZE }));

export const useActivity = (q: Query) => usePaged(staffKeys.activity(q), (page) => activityApi.list({ ...q, page, per_page: PAGE_SIZE }));

export const useStoreSettings = () => useQuery({ queryKey: staffKeys.settings, queryFn: settingsApi.get, select: (r) => r.data });

const UNREAD_POLL_MS = 60_000;

export const useReports = () => useQuery({ queryKey: staffKeys.reports, queryFn: reportApi.list, select: (r) => r.data });

export function useReport(key: string, q: Query) {
  const result = useInfiniteQuery({
    queryKey: staffKeys.report(key, q),
    queryFn: ({ pageParam }) => reportApi.view(key, { ...q, page: pageParam, per_page: 50 }),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.data.meta.page < last.data.meta.last_page ? last.data.meta.page + 1 : undefined),
  });
  const first = result.data?.pages[0]?.data;
  return { ...result, report: first, rows: result.data?.pages.flatMap((p) => p.data.rows) ?? [] };
}

export const useNotifications = (q: Query) =>
  usePaged(staffKeys.notifications(q), (page) => notificationApi.list({ ...q, page, per_page: PAGE_SIZE }));

export const useUnreadCount = () =>
  useQuery({
    queryKey: staffKeys.unreadCount,
    queryFn: notificationApi.unreadCount,
    select: (r) => r.data.count,
    refetchInterval: UNREAD_POLL_MS,
  });

export const useNotificationPreferences = () =>
  useQuery({ queryKey: staffKeys.notificationPreferences, queryFn: notificationApi.preferences, select: (r) => r.data });
