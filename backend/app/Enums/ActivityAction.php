<?php

namespace App\Enums;

/**
 * Every audited action. The value is stored as the activity `event`;
 * the part before the dot is the log name (auth, sellers, …).
 */
enum ActivityAction: string
{
    case Login = 'auth.login';
    case LoginFailed = 'auth.login_failed';
    case Logout = 'auth.logout';
    case LogoutAll = 'auth.logout_all';
    case ProfileUpdated = 'auth.profile_updated';
    case PasswordChanged = 'auth.password_changed';
    case PasswordResetRequested = 'auth.password_reset_requested';
    case PasswordReset = 'auth.password_reset';

    case SellerCreated = 'sellers.created';
    case SellerUpdated = 'sellers.updated';
    case SellerPermissionsUpdated = 'sellers.permissions_updated';
    case SellerActivated = 'sellers.activated';
    case SellerDeactivated = 'sellers.deactivated';
    case SellerPasswordReset = 'sellers.password_reset';
    case SellerDeleted = 'sellers.deleted';

    case CategoryCreated = 'categories.created';
    case CategoryUpdated = 'categories.updated';
    case CategoryImageUpdated = 'categories.image_updated';
    case CategoryImageRemoved = 'categories.image_removed';
    case CategoriesReordered = 'categories.reordered';
    case CategoryDeleted = 'categories.deleted';

    case ProductCreated = 'products.created';
    case ProductUpdated = 'products.updated';
    case ProductPriceChanged = 'products.price_changed';
    case ProductImageAdded = 'products.image_added';
    case ProductImageRemoved = 'products.image_removed';
    case ProductDeleted = 'products.deleted';
    case ProductRestored = 'products.restored';

    case BrandCreated = 'brands.created';
    case BrandUpdated = 'brands.updated';
    case BrandDeleted = 'brands.deleted';

    case UnitCreated = 'units.created';
    case UnitUpdated = 'units.updated';
    case UnitDeleted = 'units.deleted';

    public function logName(): string
    {
        return explode('.', $this->value)[0];
    }

    /** Human-readable description stored with the activity (translated when displayed). */
    public function description(): string
    {
        return __('activity.'.$this->value);
    }
}
