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

export type Availability = 'in_stock' | 'low_stock' | 'out_of_stock';

export interface PublicCategory {
  slug: string;
  name: string;
  name_translations: Record<string, string>;
  description: string | null;
  image_url: string | null;
  image_thumb_url: string | null;
  products_count: number;
}

export interface PublicImage {
  url: string;
  thumb_url: string;
}

export interface PublicProduct {
  slug: string;
  name: string;
  description: string | null;
  brand: string | null;
  category: Pick<PublicCategory, 'slug' | 'name' | 'name_translations'>;
  unit: string;
  price: string;
  selling_price: string;
  mrp: string | null;
  discount_percent: string | null;
  on_offer: boolean;
  offer_ends_at: string | null;
  availability: Availability;
  expiry_date: string | null;
  is_featured: boolean;
  images: PublicImage[];
}
