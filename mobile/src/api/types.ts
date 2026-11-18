/** Shapes returned by the Smart Kirana API (see backend/app/schemas). */
import type { Role } from '@/constants/app';
import type { Permission } from '@/constants/permissions';

export interface DataResponse<T> {
  data: T;
}

export interface PageMeta {
  page: number;
  per_page: number;
  total: number;
  last_page: number;
}

export interface Page<T> {
  data: T[];
  meta: PageMeta;
}

export interface MessageResponse {
  message: string;
}

export interface ApiErrorBody {
  message: string;
  code: string;
  errors?: Record<string, string[]>;
}

export interface AuthUser {
  id: number;
  name: string;
  email: string;
  phone: string | null;
  locale: string;
  role: Role;
  permissions: Permission[];
  last_login_at: string | null;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  access_token_expires_at: string;
  refresh_token_expires_at: string;
}

export interface LoginResponse extends TokenPair {
  user: AuthUser;
}

export interface PublicStore {
  name: string;
  tagline: string | null;
  logo_url: string | null;
  logo_thumb_url: string | null;
  phone: string | null;
  whatsapp: string | null;
  address: string | null;
  hours: string | null;
  offers_enabled: boolean;
  currency: string;
}
