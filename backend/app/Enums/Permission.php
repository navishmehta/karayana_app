<?php

namespace App\Enums;

/**
 * Single source of truth for seller permissions. Admin bypasses all checks (Gate::before).
 * Sellers get no permissions from their role; the admin grants each one directly per seller.
 */
enum Permission: string
{
    case DashboardView = 'dashboard.view';

    case ProductsView = 'products.view';
    case ProductsCreate = 'products.create';
    case ProductsUpdate = 'products.update';
    case ProductsDelete = 'products.delete';

    case CategoriesView = 'categories.view';
    case CategoriesCreate = 'categories.create';
    case CategoriesUpdate = 'categories.update';
    case CategoriesDelete = 'categories.delete';

    case PricingViewPurchase = 'pricing.view_purchase';
    case PricingViewSelling = 'pricing.view_selling';
    case PricingUpdateSelling = 'pricing.update_selling';

    case StockView = 'stock.view';
    case StockUpdate = 'stock.update';

    case ExpiryView = 'expiry.view';
    case ExpiryUpdate = 'expiry.update';

    case ReportsView = 'reports.view';
    case ReportsExport = 'reports.export';

    /** Permissions that must also be granted for this one to be valid. */
    public function dependsOn(): array
    {
        return match ($this) {
            self::ProductsCreate, self::ProductsUpdate, self::ProductsDelete,
            self::PricingViewPurchase, self::PricingViewSelling,
            self::StockView, self::ExpiryView => [self::ProductsView],
            self::CategoriesCreate, self::CategoriesUpdate, self::CategoriesDelete => [self::CategoriesView],
            self::PricingUpdateSelling => [self::PricingViewSelling],
            self::StockUpdate => [self::StockView],
            self::ExpiryUpdate => [self::ExpiryView],
            self::ReportsExport => [self::ReportsView],
            default => [],
        };
    }

    /** Direct and indirect dependencies (stock.update → stock.view → products.view). @return list<self> */
    public function allDependencies(): array
    {
        $all = [];
        foreach ($this->dependsOn() as $dependency) {
            $all = [...$all, $dependency, ...$dependency->allDependencies()];
        }

        return array_values(array_unique($all, SORT_REGULAR));
    }

    public function group(): string
    {
        return explode('.', $this->value)[0];
    }

    /** Translated label from lang/{locale}/permissions.php. */
    public function label(): string
    {
        return __('permissions.'.$this->value);
    }

    /** @param  list<string>  $granted  @return list<string> Dependencies of $granted that are not granted. */
    public static function missingDependencies(array $granted): array
    {
        $missing = [];
        foreach ($granted as $value) {
            foreach (self::tryFrom($value)?->allDependencies() ?? [] as $dependency) {
                if (! in_array($dependency->value, $granted, true)) {
                    $missing[$value][] = $dependency->value;
                }
            }
        }

        return $missing;
    }

    /** @return list<string> */
    public static function values(): array
    {
        return array_column(self::cases(), 'value');
    }
}
