import type { AuthUser } from '@/api/types';
import { categoryFormAccess, dashboardLinks, productFormAccess } from '@/auth/access';
import { PERMISSIONS as P, type Permission } from '@/constants/permissions';

const seller = (...permissions: Permission[]): AuthUser => ({
  id: 2, name: 'Raju', email: 'r@example.com', phone: null, locale: 'en', role: 'seller', permissions, last_login_at: null,
});
const admin: AuthUser = { ...seller(), role: 'admin' };

describe('product form access', () => {
  it('admin can see and change everything', () => {
    expect(productFormAccess(admin, true)).toEqual({
      seeSelling: true, editPrices: true, seePurchase: true, seeStockLevels: true, pickCategory: true,
    });
  });

  it('an editor without price or stock rights cannot see or overwrite them', () => {
    const access = productFormAccess(seller(P.productsView, P.productsUpdate), true);
    expect(access).toEqual({ seeSelling: false, editPrices: false, seePurchase: false, seeStockLevels: false, pickCategory: false });
  });

  it('seeing selling prices does not mean changing them', () => {
    const access = productFormAccess(seller(P.productsView, P.productsUpdate, P.pricingViewSelling), true);
    expect(access.seeSelling).toBe(true);
    expect(access.editPrices).toBe(false);
  });
});

describe('category form access', () => {
  it('adding a category without edit rights hides the image (upload counts as an edit)', () => {
    expect(categoryFormAccess(seller(P.categoriesView, P.categoriesCreate), false)).toEqual({ editImage: false, remove: false });
  });
  it('delete only shows for existing categories with the delete right', () => {
    expect(categoryFormAccess(seller(P.categoriesView, P.categoriesDelete), false).remove).toBe(false);
    expect(categoryFormAccess(seller(P.categoriesView, P.categoriesDelete), true).remove).toBe(true);
  });
});

it('dashboard tiles only link to screens the user can open', () => {
  expect(dashboardLinks(seller(P.dashboardView))).toEqual({ products: false, categories: false, expiry: false });
  expect(dashboardLinks(admin)).toEqual({ products: true, categories: true, expiry: true });
});
