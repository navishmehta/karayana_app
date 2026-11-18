/** Mirror of the backend's permission keys (backend/app/enums/permission.py). */
export const PERMISSIONS = {
  dashboardView: 'dashboard.view',
  productsView: 'products.view',
  productsCreate: 'products.create',
  productsUpdate: 'products.update',
  productsDelete: 'products.delete',
  categoriesView: 'categories.view',
  categoriesCreate: 'categories.create',
  categoriesUpdate: 'categories.update',
  categoriesDelete: 'categories.delete',
  pricingViewPurchase: 'pricing.view_purchase',
  pricingViewSelling: 'pricing.view_selling',
  pricingUpdateSelling: 'pricing.update_selling',
  stockView: 'stock.view',
  stockUpdate: 'stock.update',
  expiryView: 'expiry.view',
  expiryUpdate: 'expiry.update',
  reportsView: 'reports.view',
  reportsExport: 'reports.export',
} as const;

export type Permission = (typeof PERMISSIONS)[keyof typeof PERMISSIONS];
