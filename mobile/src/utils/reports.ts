/** Report helpers (pure, unit-tested). */
import type { ColumnKind } from '@/api/staff/types';
import { displayToApiDate, isValidDisplayDate } from '@/utils/dates';

export interface ReportFilterValues {
  categoryId: number | null;
  withinDays: number | null;
  dateFrom: string; // DD-MM-YYYY as typed
  dateTo: string;
}

export const EMPTY_REPORT_FILTERS: ReportFilterValues = { categoryId: null, withinDays: null, dateFrom: '', dateTo: '' };

/** Only filters the report supports, and only valid dates. */
export function reportQuery(filters: ReportFilterValues, supported: string[]): Record<string, string | number | undefined> {
  const query: Record<string, string | number | undefined> = {};
  if (supported.includes('category_id') && filters.categoryId) query.category_id = filters.categoryId;
  if (supported.includes('within_days') && filters.withinDays !== null) query.within_days = filters.withinDays;
  if (supported.includes('date_from') && isValidDisplayDate(filters.dateFrom)) query.date_from = displayToApiDate(filters.dateFrom)!;
  if (supported.includes('date_to') && isValidDisplayDate(filters.dateTo)) query.date_to = displayToApiDate(filters.dateTo)!;
  return query;
}

/** Column width in the in-app table: numbers are narrow, names wide. */
export function columnWidth(kind: ColumnKind, key: string): number {
  if (key === 'product') return 180;
  if (kind === 'text') return 140;
  if (kind === 'datetime') return 140;
  return 104;
}

export const isNumeric = (kind: ColumnKind) => kind !== 'text' && kind !== 'date' && kind !== 'datetime';

export const exportFileName = (key: string, format: 'csv' | 'xlsx', today: Date = new Date()) => {
  const dd = String(today.getDate()).padStart(2, '0');
  const mm = String(today.getMonth() + 1).padStart(2, '0');
  return `${key}-${dd}-${mm}-${today.getFullYear()}.${format}`;
};

export const EXPORT_MIME = {
  csv: 'text/csv',
  xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
} as const;
