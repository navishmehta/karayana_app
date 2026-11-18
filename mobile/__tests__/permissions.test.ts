import type { AuthUser } from '@/api/types';
import { can, isAdmin } from '@/auth/permissions';
import { PERMISSIONS } from '@/constants/permissions';

const user = (overrides: Partial<AuthUser>): AuthUser => ({
  id: 1,
  name: 'Test',
  email: 't@example.com',
  phone: null,
  locale: 'en',
  role: 'seller',
  permissions: [],
  last_login_at: null,
  ...overrides,
});

describe('can()', () => {
  it('gives the admin everything', () => {
    const admin = user({ role: 'admin' });
    expect(isAdmin(admin)).toBe(true);
    expect(can(admin, PERMISSIONS.pricingViewPurchase, PERMISSIONS.productsCreate)).toBe(true);
  });

  it('requires every listed permission for a seller', () => {
    const seller = user({ permissions: [PERMISSIONS.productsView, PERMISSIONS.stockView] });
    expect(can(seller, PERMISSIONS.productsView)).toBe(true);
    expect(can(seller, PERMISSIONS.productsView, PERMISSIONS.stockUpdate)).toBe(false);
  });

  it('denies a logged-out user', () => {
    expect(can(null, PERMISSIONS.productsView)).toBe(false);
  });
});
