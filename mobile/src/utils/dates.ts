/** Dates are typed and shown as DD-MM-YYYY; the API uses YYYY-MM-DD. */

const DISPLAY = /^(\d{2})-(\d{2})-(\d{4})$/;

export function isValidDisplayDate(value: string): boolean {
  const match = DISPLAY.exec(value.trim());
  if (!match) return false;
  const [, d, m, y] = match.map(Number);
  const date = new Date(Date.UTC(y, m - 1, d));
  return date.getUTCFullYear() === y && date.getUTCMonth() === m - 1 && date.getUTCDate() === d;
}

/** "19-11-2026" -> "2026-11-19"; "" -> null. Call isValidDisplayDate first. */
export function displayToApiDate(value: string): string | null {
  const match = DISPLAY.exec(value.trim());
  return match ? `${match[3]}-${match[2]}-${match[1]}` : null;
}

/** "2026-11-19" -> "19-11-2026"; null -> "" (for form fields). */
export function apiToDisplayDate(value: string | null | undefined): string {
  if (!value) return '';
  const [y, m, d] = value.split('-');
  return `${d}-${m}-${y}`;
}
