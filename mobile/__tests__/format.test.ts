import { formatDate, formatDateTime, formatMoney, formatPercent, formatQuantity } from '@/utils/format';

describe('formatMoney', () => {
  it('uses rupees with Indian grouping and two decimals', () => {
    expect(formatMoney('123456.5')).toBe('₹1,23,456.50');
    expect(formatMoney(285)).toBe('₹285.00');
  });
  it('shows a dash for missing values', () => {
    expect(formatMoney(null)).toBe('—');
    expect(formatMoney('')).toBe('—');
    expect(formatMoney('abc')).toBe('—');
  });
});

describe('formatQuantity', () => {
  it('drops trailing zeros and adds the unit', () => {
    expect(formatQuantity('12.000', 'pcs')).toBe('12 pcs');
    expect(formatQuantity('1.250', 'kg')).toBe('1.25 kg');
    expect(formatQuantity('100000')).toBe('1,00,000');
  });
});

describe('dates are DD-MM-YYYY in store time (IST)', () => {
  it('formats plain dates without shifting the day', () => {
    expect(formatDate('2026-11-19')).toBe('19-11-2026');
  });
  it('converts timestamps to India time', () => {
    // 20:00 UTC on the 18th is 01:30 IST on the 19th
    expect(formatDate('2026-11-18T20:00:00Z')).toBe('19-11-2026');
    expect(formatDateTime('2026-11-18T20:00:00Z')).toBe('19-11-2026, 01:30');
    expect(formatDateTime('2026-11-19T10:15:00+05:30')).toBe('19-11-2026, 10:15');
  });
  it('handles missing or broken values', () => {
    expect(formatDate(null)).toBe('—');
    expect(formatDateTime('not a date')).toBe('—');
  });
});

it('formats percentages', () => {
  expect(formatPercent('14.29')).toBe('14.3%');
});
