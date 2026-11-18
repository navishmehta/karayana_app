/**
 * What each staff screen may show or change, from the user's permissions (pure, unit-tested).
 * Hiding things is only for a clean interface — the server checks every request on its own.
 */
import type { AuthUser } from '@/api/types';
import { PERMISSIONS as P } from '@/constants/permissions';

import { can } from './permissions';

export interface ProductFormAccess {
  seeSelling: boolean; // selling price, MRP, offer
  editPrices: boolean; // change them (always allowed when creating — only the admin creates)
  seePurchase: boolean; // purchase price + internal notes
  seeStockLevels: boolean; // min / max stock (hidden values must not be shown as 0 and saved back)
  pickCategory: boolean; // the category list needs categories.view
}

export function productFormAccess(user: AuthUser | null, editing: boolean): ProductFormAccess {
  return {
    seeSelling: can(user, P.pricingViewSelling),
    editPrices: !editing || can(user, P.pricingUpdateSelling),
    seePurchase: can(user, P.pricingViewPurchase),
    seeStockLevels: can(user, P.stockView),
    pickCategory: can(user, P.categoriesView),
  };
}

export interface CategoryFormAccess {
  editImage: boolean; // uploading/removing an image is an update
  remove: boolean;
}

export function categoryFormAccess(user: AuthUser | null, editing: boolean): CategoryFormAccess {
  return {
    editImage: can(user, P.categoriesUpdate),
    remove: editing && can(user, P.categoriesDelete),
  };
}

/** Dashboard tiles only open screens the user can use. */
export function dashboardLinks(user: AuthUser | null) {
  return {
    products: can(user, P.productsView),
    categories: can(user, P.categoriesView),
    expiry: can(user, P.expiryView),
  };
}
