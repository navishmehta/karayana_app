import type { AuthUser } from '@/api/types';
import { canOpenTab, firstAllowedTab, STAFF_TABS } from '@/auth/staffTabs';
import { PERMISSIONS as P } from '@/constants/permissions';
import { apiToDisplayDate, displayToApiDate, isValidDisplayDate } from '@/utils/dates';
import { applyServerErrors, newRequestKey, orNull } from '@/utils/forms';
import { ApiError } from '@/api/errors';

const user = (role: 'admin' | 'seller', permissions: AuthUser['permissions'] = []): AuthUser => ({
  id: 1, name: 'x', email: 'x@example.com', phone: null, locale: 'en', role, permissions, last_login_at: null,
});

describe('DD-MM-YYYY dates', () => {
  it('validates real dates only', () => {
    expect(isValidDisplayDate('19-11-2026')).toBe(true);
    expect(isValidDisplayDate('31-02-2026')).toBe(false);
    expect(isValidDisplayDate('2026-11-19')).toBe(false);
  });
  it('converts both ways', () => {
    expect(displayToApiDate('05-01-2027')).toBe('2027-01-05');
    expect(displayToApiDate('')).toBeNull();
    expect(apiToDisplayDate('2027-01-05')).toBe('05-01-2027');
    expect(apiToDisplayDate(null)).toBe('');
  });
});

describe('staff tabs', () => {
  it('admin sees every tab and lands on the dashboard', () => {
    const admin = user('admin');
    expect(STAFF_TABS.every((tab) => canOpenTab(admin, tab))).toBe(true);
    expect(firstAllowedTab(admin).name).toBe('index');
  });
  it('a seller sees only permitted tabs and lands on the first one', () => {
    const seller = user('seller', [P.productsView, P.stockView]);
    expect(STAFF_TABS.filter((tab) => canOpenTab(seller, tab)).map((t) => t.name)).toEqual(['products', 'stock', 'more']);
    expect(firstAllowedTab(seller).name).toBe('products');
  });
  it('a seller with no permissions lands on More', () => {
    expect(firstAllowedTab(user('seller')).name).toBe('more');
  });
});

describe('form helpers', () => {
  it('puts server messages on matching fields and returns the rest', () => {
    const setError = jest.fn();
    const error = new ApiError(422, 'VALIDATION_FAILED', 'Check', {
      selling_price: ['Selling price cannot be more than the MRP.'],
      name: ['This name is already in use.'],
      permissions: ['Other problem'],
    });
    const leftovers = applyServerErrors(error, setError, ['name', 'sellingPrice'] as const, { selling_price: 'sellingPrice' });
    expect(setError).toHaveBeenCalledWith('sellingPrice', { message: 'Selling price cannot be more than the MRP.' });
    expect(setError).toHaveBeenCalledWith('name', { message: 'This name is already in use.' });
    expect(leftovers).toEqual(['Other problem']);
  });
  it('makes unique request keys and trims optional text', () => {
    expect(newRequestKey()).not.toBe(newRequestKey());
    expect(orNull('  ')).toBeNull();
    expect(orNull(' Amul ')).toBe('Amul');
  });
});
