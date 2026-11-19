/** Stock movement kinds and the reasons each allows (mirrors backend StockReason.allowed_for). */
import type { StockKind } from '@/api/staff/endpoints';

export const STOCK_KINDS: StockKind[] = ['stock-in', 'stock-out', 'adjust', 'damage'];

export const STOCK_REASONS: Record<StockKind, readonly string[]> = {
  'stock-in': ['purchase', 'customer_return', 'found', 'other'],
  'stock-out': ['sold_manually', 'returned_to_supplier', 'personal_use', 'sample', 'theft', 'other'],
  adjust: ['count_correction', 'other'],
  damage: ['broken', 'rodent', 'spoiled', 'leaked', 'other'],
};

/** Movements that work on one chosen batch. */
export const NEEDS_BATCH: StockKind[] = ['adjust', 'damage'];

/** Unit pre-selected for a new product (most kirana items are sold by the piece). Falls back to the first unit. */
export const DEFAULT_UNIT_SHORT_NAME = 'pcs';
