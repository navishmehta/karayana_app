import { PERMISSIONS as P, type Permission } from '@/constants/permissions';
import { allDependencies, type DependencyMap, PERMISSION_PRESETS, togglePermission } from '@/utils/permissionEditor';

// Same dependency rules the server sends in /admin/permissions.
const deps: DependencyMap = {
  [P.productsUpdate]: [P.productsView],
  [P.stockView]: [P.productsView],
  [P.stockUpdate]: [P.stockView],
  [P.pricingViewSelling]: [P.productsView],
  [P.pricingUpdateSelling]: [P.pricingViewSelling],
  [P.expiryView]: [P.productsView],
  [P.expiryUpdate]: [P.expiryView],
  [P.categoriesCreate]: [P.categoriesView],
  [P.categoriesUpdate]: [P.categoriesView],
  [P.categoriesDelete]: [P.categoriesView],
  [P.productsDelete]: [P.productsView],
  [P.reportsExport]: [P.reportsView],
};

it('finds indirect dependencies', () => {
  expect(allDependencies(P.stockUpdate, deps)).toEqual([P.stockView, P.productsView]);
});

it('ticking adds what is needed', () => {
  expect(togglePermission([], P.stockUpdate, deps).sort()).toEqual([P.productsView, P.stockUpdate, P.stockView].sort());
});

it('unticking removes everything that needs it', () => {
  const selected: Permission[] = [P.productsView, P.stockView, P.stockUpdate, P.categoriesView];
  expect(togglePermission(selected, P.productsView, deps)).toEqual([P.categoriesView]);
  expect(togglePermission(selected, P.stockView, deps)).toEqual([P.productsView, P.categoriesView]);
});

it('presets are complete (every dependency included) and never include admin-only rights', () => {
  for (const preset of Object.values(PERMISSION_PRESETS)) {
    for (const permission of preset) {
      for (const needed of allDependencies(permission, deps)) expect(preset).toContain(needed);
    }
    expect(preset).not.toContain(P.productsCreate);
  }
  expect(PERMISSION_PRESETS.manager).not.toContain(P.pricingViewPurchase);
});
