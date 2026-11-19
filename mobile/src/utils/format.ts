/** Display formatting. Western digits and Indian grouping in every language: ₹1,23,456.50 */
import { CURRENCY, NUMBER_LOCALE, STORE_TIME_ZONE } from '@/constants/app';

type Amount = string | number | null | undefined;

const toNumber = (value: Amount): number | null => {
  if (value === null || value === undefined || value === '') return null;
  const n = typeof value === 'number' ? value : Number(value);
  return Number.isFinite(n) ? n : null;
};

const moneyFormatter = new Intl.NumberFormat(NUMBER_LOCALE, {
  style: 'currency',
  currency: CURRENCY,
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

/** "285.00" -> "₹285.00", null -> "—" */
export function formatMoney(value: Amount): string {
  const n = toNumber(value);
  return n === null ? '—' : moneyFormatter.format(n);
}

/** "12.000" + "pcs" -> "12 pcs"; "1.250" + "kg" -> "1.25 kg" */
export function formatQuantity(value: Amount, unit?: string): string {
  const n = toNumber(value);
  if (n === null) return '—';
  const text = new Intl.NumberFormat(NUMBER_LOCALE, { maximumFractionDigits: 3 }).format(n);
  return unit ? `${text} ${unit}` : text;
}

export function formatPercent(value: Amount): string {
  const n = toNumber(value);
  return n === null ? '—' : `${new Intl.NumberFormat(NUMBER_LOCALE, { maximumFractionDigits: 1 }).format(n)}%`;
}

const NON_BREAKING_HYPHEN = '\u2011';
const NON_BREAKING_SPACE = '\u00A0';

/**
 * Dates and times are shown as one unbreakable piece, so a line never wraps in the middle ("20-" / "11-2026").
 * They look the same as normal hyphens and spaces. For display only — never for values sent to the server.
 */
const keepTogether = (text: string) => text.replaceAll('-', NON_BREAKING_HYPHEN).replaceAll(' ', NON_BREAKING_SPACE);

/** "2026-11-19" or an ISO timestamp -> "19-11-2026" (store time zone for timestamps). */
export function formatDate(value: string | null | undefined): string {
  if (!value) return '—';
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    const [y, m, d] = value.split('-');
    return keepTogether(`${d}-${m}-${y}`);
  }
  const parts = storeParts(value);
  return parts ? keepTogether(`${parts.day}-${parts.month}-${parts.year}`) : '—';
}

/** ISO timestamp -> "19-11-2026, 14:05" in store time. */
export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '—';
  const parts = storeParts(value);
  return parts ? keepTogether(`${parts.day}-${parts.month}-${parts.year}, ${parts.hour}:${parts.minute}`) : '—';
}

const storeDateTimeFormatter = new Intl.DateTimeFormat('en-GB', {
  timeZone: STORE_TIME_ZONE,
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  hourCycle: 'h23',
});

function storeParts(iso: string) {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return null;
  const parts = storeDateTimeFormatter.formatToParts(date);
  const get = (type: Intl.DateTimeFormatPartTypes) => parts.find((p) => p.type === type)?.value ?? '';
  return { day: get('day'), month: get('month'), year: get('year'), hour: get('hour'), minute: get('minute') };
}
