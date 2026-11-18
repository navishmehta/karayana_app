/**
 * Logic for the admin's seller-permission editor (pure; mirrors the server's dependency rules).
 * Ticking a permission also ticks what it needs; unticking one also unticks everything that needs it.
 */
import { type Permission, PERMISSIONS as P } from '@/constants/permissions';

export type DependencyMap = Partial<Record<Permission, Permission[]>>;

export function allDependencies(permission: Permission, deps: DependencyMap): Permission[] {
  const result: Permission[] = [];
  for (const direct of deps[permission] ?? []) {
    for (const item of [direct, ...allDependencies(direct, deps)]) {
      if (!result.includes(item)) result.push(item);
    }
  }
  return result;
}

export function togglePermission(selected: Permission[], permission: Permission, deps: DependencyMap): Permission[] {
  if (!selected.includes(permission)) {
    return unique([...selected, permission, ...allDependencies(permission, deps)]);
  }
  // Removing: also remove anything that (directly or indirectly) depends on it.
  return selected.filter((p) => p !== permission && !allDependencies(p, deps).includes(permission));
}

const unique = (items: Permission[]) => [...new Set(items)];

/** Ready-made starting points; the admin can still tick/untick individual boxes. */
export const PERMISSION_PRESETS: Record<'counter' | 'stock' | 'manager', Permission[]> = {
  counter: [P.dashboardView, P.productsView, P.categoriesView, P.pricingViewSelling, P.stockView],
  stock: [P.dashboardView, P.productsView, P.categoriesView, P.pricingViewSelling, P.stockView, P.stockUpdate, P.expiryView, P.expiryUpdate],
  manager: [
    P.dashboardView,
    P.productsView,
    P.productsUpdate,
    P.productsDelete,
    P.categoriesView,
    P.categoriesCreate,
    P.categoriesUpdate,
    P.categoriesDelete,
    P.pricingViewSelling,
    P.pricingUpdateSelling,
    P.stockView,
    P.stockUpdate,
    P.expiryView,
    P.expiryUpdate,
    P.reportsView,
    P.reportsExport,
  ],
};
