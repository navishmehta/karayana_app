/** One function per API call used by the app. Paths match backend/app/api/v1/endpoints. */
import { DEVICE_NAME } from '@/constants/app';

import { api } from './client';
import type { AuthUser, DataResponse, LoginResponse, MessageResponse, PublicStore, TokenPair } from './types';

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

export const publicApi = {
  store: () => api.get<DataResponse<PublicStore>>('/public/store', { auth: false }),
};
