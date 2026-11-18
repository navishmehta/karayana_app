/** Staff (admin / seller) API calls. Paths match backend/app/api/v1/endpoints. */
import { api } from '@/api/client';
import type { DataResponse, MessageResponse, Page } from '@/api/types';
import type { Permission } from '@/constants/permissions';

import type {
  Activity,
  AppNotification,
  NotificationPreference,
  ReportData,
  ReportInfo,
  Adjustment,
  Batch,
  Brand,
  Dashboard,
  ExpiryBatch,
  ExpirySummary,
  PermissionGroup,
  Seller,
  StaffCategory,
  StaffProduct,
  StoreSettings,
  Transaction,
  Unit,
} from './types';

type Query = Record<string, string | number | boolean | (string | number)[] | undefined>;
type Body = Record<string, unknown>;

/** Unique key per stock form submit, so a retry on a weak connection never records stock twice. */
const idempotent = (key: string) => ({ headers: { 'Idempotency-Key': key } });

export const dashboardApi = {
  get: (days: number) => api.get<DataResponse<Dashboard>>('/dashboard', { query: { days } }),
};

export const categoryApi = {
  list: (query: Query) => api.get<Page<StaffCategory>>('/categories', { query }),
  get: (id: number) => api.get<DataResponse<StaffCategory>>(`/categories/${id}`),
  create: (body: Body) => api.post<DataResponse<StaffCategory>>('/categories', body),
  update: (id: number, body: Body) => api.patch<DataResponse<StaffCategory>>(`/categories/${id}`, body),
  reorder: (ids: number[]) => api.patch<void>('/categories/reorder', { ids }),
  uploadImage: (id: number, form: FormData) => api.post<DataResponse<StaffCategory>>(`/categories/${id}/image`, form),
  removeImage: (id: number) => api.delete<DataResponse<StaffCategory>>(`/categories/${id}/image`),
  remove: (id: number) => api.delete<void>(`/categories/${id}`),
};

export const lookupApi = {
  units: () => api.get<DataResponse<Unit[]>>('/units', { query: { active_only: true } }),
  brands: (search: string) => api.get<Page<Brand>>('/brands', { query: { search, per_page: 50 } }),
  createBrand: (name: string) => api.post<DataResponse<Brand>>('/brands', { name }),
};

export const productApi = {
  list: (query: Query) => api.get<Page<StaffProduct>>('/products', { query }),
  get: (id: number) => api.get<DataResponse<StaffProduct>>(`/products/${id}`),
  create: (body: Body) => api.post<DataResponse<StaffProduct>>('/products', body),
  update: (id: number, body: Body) => api.patch<DataResponse<StaffProduct>>(`/products/${id}`, body),
  remove: (id: number) => api.delete<void>(`/products/${id}`),
  restore: (id: number) => api.post<DataResponse<StaffProduct>>(`/admin/products/${id}/restore`),
  uploadImage: (id: number, form: FormData) => api.post<DataResponse<StaffProduct>>(`/products/${id}/images`, form),
  makePrimary: (id: number, imageId: number) =>
    api.patch<DataResponse<StaffProduct>>(`/products/${id}/images/${imageId}`, { is_primary: true }),
  removeImage: (id: number, imageId: number) => api.delete<void>(`/products/${id}/images/${imageId}`),
  batches: (id: number, includeEmpty = false) =>
    api.get<DataResponse<Batch[]>>(`/products/${id}/batches`, { query: { include_empty: includeEmpty } }),
};

export type StockKind = 'stock-in' | 'stock-out' | 'adjust' | 'damage';

export const inventoryApi = {
  move: (kind: StockKind, body: Body, key: string) =>
    api.post<DataResponse<Adjustment>>(`/inventory/${kind}`, body, idempotent(key)),
  writeOff: (batchIds: number[], key: string) =>
    api.post<DataResponse<Adjustment>>('/inventory/expired-writeoff', { batch_ids: batchIds }, idempotent(key)),
  updateBatch: (batchId: number, body: Body) => api.patch<DataResponse<Batch>>(`/batches/${batchId}`, body),
  transactions: (query: Query) => api.get<Page<Transaction>>('/inventory/transactions', { query }),
};

export const expiryApi = {
  summary: () => api.get<DataResponse<ExpirySummary>>('/expiry/summary'),
  batches: (query: Query) => api.get<Page<ExpiryBatch>>('/expiry/batches', { query }),
};

export const sellerApi = {
  permissions: () => api.get<DataResponse<PermissionGroup[]>>('/admin/permissions'),
  list: (query: Query) => api.get<Page<Seller>>('/admin/sellers', { query }),
  get: (id: number) => api.get<DataResponse<Seller>>(`/admin/sellers/${id}`),
  create: (body: Body) => api.post<DataResponse<Seller>>('/admin/sellers', body),
  update: (id: number, body: Body) => api.patch<DataResponse<Seller>>(`/admin/sellers/${id}`, body),
  setPermissions: (id: number, permissions: Permission[]) =>
    api.put<DataResponse<Seller>>(`/admin/sellers/${id}/permissions`, { permissions }),
  setActive: (id: number, isActive: boolean) =>
    api.patch<DataResponse<Seller>>(`/admin/sellers/${id}/status`, { is_active: isActive }),
  resetPassword: (id: number, password: string) =>
    api.post<MessageResponse>(`/admin/sellers/${id}/reset-password`, { password, password_confirmation: password }),
  remove: (id: number) => api.delete<void>(`/admin/sellers/${id}`),
  activity: (id: number, query: Query) => api.get<Page<Activity>>(`/admin/sellers/${id}/activity`, { query }),
};

export const activityApi = {
  list: (query: Query) => api.get<Page<Activity>>('/admin/activity-logs', { query }),
};

export const settingsApi = {
  get: () => api.get<DataResponse<StoreSettings>>('/admin/settings'),
  update: (body: Body) => api.patch<DataResponse<StoreSettings>>('/admin/settings', body),
  uploadLogo: (form: FormData) => api.post<DataResponse<StoreSettings>>('/admin/settings/logo', form),
};

export const reportApi = {
  list: () => api.get<DataResponse<ReportInfo[]>>('/reports'),
  view: (key: string, query: Query) => api.get<DataResponse<ReportData>>(`/reports/${key}`, { query }),
};

export const notificationApi = {
  list: (query: Query) => api.get<Page<AppNotification>>('/notifications', { query }),
  unreadCount: () => api.get<DataResponse<{ count: number }>>('/notifications/unread-count'),
  markRead: (id: number) => api.post<DataResponse<AppNotification>>(`/notifications/${id}/read`),
  markAllRead: () => api.post<MessageResponse>('/notifications/read-all'),
  preferences: () => api.get<DataResponse<NotificationPreference[]>>('/notifications/preferences'),
  savePreferences: (preferences: NotificationPreference[]) =>
    api.put<DataResponse<NotificationPreference[]>>('/notifications/preferences', { preferences }),
};

export const deviceApi = {
  register: (token: string, platform: 'android' | 'ios' | 'web') => api.post<MessageResponse>('/devices', { token, platform }),
  remove: (token: string) => api.delete<void>(`/devices/${encodeURIComponent(token)}`),
};
