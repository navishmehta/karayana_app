/** One function per API call used by the app. Paths match backend/app/api/v1/endpoints. */
import { CATALOGUE_PAGE_SIZE, DEVICE_NAME } from '@/constants/app';

import { api } from './client';
import type {
  AuthUser,
  DataResponse,
  LoginResponse,
  MessageResponse,
  Page,
  PublicCategory,
  PublicProduct,
  PublicStore,
  TokenPair,
} from './types';
import type { CatalogueQuery } from '@/utils/catalogue';

export const authApi = {
  login: (email: string, password: string) =>
    api.post<DataResponse<LoginResponse>>('/auth/login', { email, password, device_name: DEVICE_NAME }, { auth: false }),
  refresh: (refreshToken: string) =>
    api.post<DataResponse<TokenPair>>('/auth/refresh', { refresh_token: refreshToken }, { auth: false }),
  me: () => api.get<DataResponse<AuthUser>>('/auth/me'),
  updateMe: (values: Partial<Pick<AuthUser, 'name' | 'phone' | 'locale'>>) =>
    api.patch<DataResponse<AuthUser>>('/auth/me', values),
  logout: () => api.post<MessageResponse>('/auth/logout'),
  forgotPassword: (email: string) => api.post<MessageResponse>('/auth/forgot-password', { email }, { auth: false }),
  resetPassword: (email: string, code: string, password: string) =>
    api.post<MessageResponse>(
      '/auth/reset-password',
      { email, code, password, password_confirmation: password },
      { auth: false },
    ),
};

const publicGet = <T>(path: string, query?: Record<string, string | number | boolean | undefined>) =>
  api.get<T>(`/public${path}`, { auth: false, query });

export const publicApi = {
  store: () => publicGet<DataResponse<PublicStore>>('/store'),
  categories: () => publicGet<DataResponse<PublicCategory[]>>('/categories'),
  category: (slug: string) => publicGet<DataResponse<PublicCategory>>(`/categories/${encodeURIComponent(slug)}`),
  products: (query: CatalogueQuery, page: number) =>
    publicGet<Page<PublicProduct>>('/products', { ...query, page, per_page: CATALOGUE_PAGE_SIZE }),
  featured: () => publicGet<DataResponse<PublicProduct[]>>('/products/featured'),
  newArrivals: () => publicGet<DataResponse<PublicProduct[]>>('/products/new'),
  offers: () => publicGet<DataResponse<PublicProduct[]>>('/products/offers'),
  product: (slug: string) => publicGet<DataResponse<PublicProduct>>(`/products/${encodeURIComponent(slug)}`),
};
