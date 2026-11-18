/** Staff (admin / seller) API shapes. Optional fields are absent when the user lacks the permission. */
import type { Permission } from '@/constants/permissions';

export interface Ref {
  id: number;
  name: string;
}

export interface Unit {
  id: number;
  name: string;
  short_name: string;
  allows_decimal: boolean;
  is_active: boolean;
}

export interface Brand {
  id: number;
  name: string;
  slug: string;
  is_active: boolean;
}

export interface StaffCategory {
  id: number;
  name: string;
  name_translations: Record<string, string>;
  slug: string;
  description: string | null;
  image_url: string | null;
  image_thumb_url: string | null;
  sort_order: number;
  is_active: boolean;
  products_count: number;
  created_at: string;
  updated_at: string;
}

export interface ProductImage {
  id: number;
  url: string;
  thumb_url: string;
  is_primary: boolean;
  sort_order: number;
}

export interface Profit {
  price_used: string;
  purchase_price: string;
  amount: string;
  markup_percent: string | null;
  margin_percent: string | null;
}

export type StockStatus = 'in_stock' | 'low_stock' | 'out_of_stock';

export interface StaffProduct {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  sku: string;
  barcode: string | null;
  category: Ref;
  brand: Ref | null;
  unit: Unit;
  images: ProductImage[];
  tax_rate: string | null;
  hsn_code: string | null;
  track_expiry: boolean;
  show_expiry_to_customers: boolean;
  is_active: boolean;
  is_visible_to_customers: boolean;
  is_featured: boolean;
  created_at: string;
  updated_at: string;
  // pricing.view_selling
  selling_price?: string;
  mrp?: string | null;
  offer_price?: string | null;
  offer_starts_at?: string | null;
  offer_ends_at?: string | null;
  on_offer?: boolean;
  effective_price?: string;
  discount_percent?: string | null;
  // pricing.view_purchase
  purchase_price?: string | null;
  profit?: Profit | null;
  internal_notes?: string | null;
  // stock.view
  opening_stock?: string;
  current_stock?: string;
  sellable_stock?: string;
  min_stock_level?: string;
  max_stock_level?: string | null;
  stock_status?: StockStatus;
  // expiry.view
  next_expiry_date?: string | null;
}

export type ExpiryBucket = 'expired' | 'critical' | 'warning' | 'notice' | 'safe' | 'no_expiry';

export interface Batch {
  id: number;
  product_id: number;
  batch_number: string | null;
  manufacturing_date: string | null;
  expiry_date: string | null;
  days_to_expiry: number | null;
  bucket: ExpiryBucket;
  quantity_received: string;
  quantity_remaining: string;
  received_at: string;
  notes: string | null;
  purchase_price?: string | null;
}

export interface ExpiryBatch extends Batch {
  product: Ref;
  sku: string;
  category: Ref;
  unit: string;
}

export interface Transaction {
  id: number;
  type: string;
  reason: string | null;
  product: Ref;
  batch: { id: number; batch_number: string | null; expiry_date: string | null };
  quantity_change: string;
  product_qty_before: string;
  product_qty_after: string;
  batch_qty_before: string;
  batch_qty_after: string;
  user: Ref;
  reference_type: string | null;
  reference_id: number | null;
  created_at: string;
  unit_cost?: string | null;
}

export interface ProductStock {
  id: number;
  name: string;
  current_stock: string;
  sellable_stock: string;
  stock_status: StockStatus;
  next_expiry_date: string | null;
}

export interface Adjustment {
  id: number;
  type: string;
  reason: string;
  notes: string | null;
  created_by: Ref;
  created_at: string;
  lines: Transaction[];
  products: ProductStock[];
  cost_impact?: string | null;
}

export interface ExpirySummary {
  as_of: string;
  buckets: { key: string; days: number | null; batches: number; products: number; quantity: string; cost_value?: string }[];
}

export interface Seller {
  id: number;
  name: string;
  email: string;
  phone: string | null;
  locale: string;
  is_active: boolean;
  permissions: Permission[];
  active_sessions: number;
  last_login_at: string | null;
  created_at: string;
}

export interface PermissionGroup {
  key: string;
  label: string;
  permissions: { key: Permission; label: string; depends_on: Permission[] }[];
}

export interface Activity {
  id: number;
  action: string;
  description: string;
  user: Ref | null;
  subject: { type: string; id: number } | null;
  properties: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
}

export interface StoreSettings {
  store_name: string;
  tagline: string | null;
  logo_url: string | null;
  logo_thumb_url: string | null;
  phone: string | null;
  whatsapp: string | null;
  address: string | null;
  hours: string | null;
  offers_enabled: boolean;
  show_out_of_stock: boolean;
  default_min_stock: number;
  expiry_buckets: number[];
  notify_low_stock: boolean;
  notify_out_of_stock: boolean;
  notify_expiry: boolean;
  expiry_digest_time: string;
}

export interface Dashboard {
  products_total: number;
  products_active: number;
  categories_total: number;
  sellers_total?: number;
  stock?: { total_quantity: string; low_stock: number; out_of_stock: number };
  expiry?: { expired_batches: number; expiring_batches: number; expiring_within_days: number };
  value?: { purchase_cost?: string; selling_value?: string };
  stock_by_category?: { id: number; name: string; products: number; quantity: string }[];
  movements?: { day: string; stock_in: string; stock_out: string }[];
  recent_products?: StaffProduct[];
  recent_movements?: Transaction[];
}
