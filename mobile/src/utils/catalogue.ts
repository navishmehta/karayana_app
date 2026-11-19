/** Pure helpers for the customer catalogue (easy to unit-test). */
import { MAX_GRID_COLUMNS, PRODUCT_CARD_MIN_WIDTH } from '@/constants/app';
import { CATEGORY_ICON_RULES, DEFAULT_CATEGORY_ICON } from '@/constants/categoryIcons';

export const SORT_OPTIONS = ['name_asc', 'name_desc', 'price_asc', 'price_desc', 'newest'] as const;
export type SortOption = (typeof SORT_OPTIONS)[number];

export interface CatalogueFilters {
  search: string;
  category?: string;
  minPrice: string;
  maxPrice: string;
  inStock: boolean;
  onOffer: boolean;
  featured: boolean;
  sort: SortOption;
}

export const DEFAULT_FILTERS: CatalogueFilters = {
  search: '',
  minPrice: '',
  maxPrice: '',
  inStock: false,
  onOffer: false,
  featured: false,
  sort: 'name_asc',
};

/** Query parameters for GET /public/products (only what's set). */
export type CatalogueQuery = Record<string, string | number | boolean | undefined>;

const asPrice = (value: string): number | undefined => {
  const n = Number(value.replace(/,/g, '').trim());
  return value.trim() && Number.isFinite(n) && n >= 0 ? n : undefined;
};

export function toCatalogueQuery(filters: CatalogueFilters): CatalogueQuery {
  const query: CatalogueQuery = { sort: filters.sort };
  if (filters.search.trim()) query.search = filters.search.trim();
  if (filters.category) query.category = filters.category;
  const min = asPrice(filters.minPrice);
  const max = asPrice(filters.maxPrice);
  if (min !== undefined) query.min_price = min;
  if (max !== undefined) query.max_price = min !== undefined && max < min ? min : max;
  if (filters.inStock) query.in_stock = true;
  if (filters.onOffer) query.on_offer = true;
  if (filters.featured) query.featured = true;
  return query;
}

/** How many filters (beyond search/category) are active — shown on the Filter button. */
export function activeFilterCount(filters: CatalogueFilters): number {
  return [
    asPrice(filters.minPrice) !== undefined,
    asPrice(filters.maxPrice) !== undefined,
    filters.inStock,
    filters.onOffer,
    filters.featured,
    filters.sort !== DEFAULT_FILTERS.sort,
  ].filter(Boolean).length;
}

/** Grid columns for a screen width: 2 on phones, more on tablets / web. */
export function gridColumns(width: number): number {
  return Math.max(2, Math.min(MAX_GRID_COLUMNS, Math.floor(width / PRODUCT_CARD_MIN_WIDTH)));
}

/**
 * Width of one grid cell, so a lone item on the last row keeps its column width instead of stretching.
 * `contentWidth` is the list width without its side padding.
 */
export function gridItemWidth(contentWidth: number, columns: number, gap: number): number {
  return Math.floor((contentWidth - gap * (columns - 1)) / columns);
}

/** Admin-entered translation if there is one, otherwise the name as typed. */
export function localizedName(item: { name: string; name_translations?: Record<string, string> }, language: string): string {
  return item.name_translations?.[language] || item.name;
}

/** Icon for a category without a photo, chosen from words in its English name (see constants/categoryIcons.ts). */
export function categoryIcon(name: string): (typeof CATEGORY_ICON_RULES)[number]['icon'] {
  const text = name.toLowerCase();
  return CATEGORY_ICON_RULES.find((rule) => rule.words.some((word) => text.includes(word)))?.icon ?? DEFAULT_CATEGORY_ICON;
}
