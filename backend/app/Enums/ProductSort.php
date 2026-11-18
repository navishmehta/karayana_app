<?php

namespace App\Enums;

use Illuminate\Database\Eloquent\Builder;

/** Sort options for product lists. Sorting by a private value needs the matching permission. */
enum ProductSort: string
{
    case NameAsc = 'name_asc';
    case NameDesc = 'name_desc';
    case PriceAsc = 'price_asc';
    case PriceDesc = 'price_desc';
    case Newest = 'newest';
    case StockAsc = 'stock_asc';

    public const DEFAULT = self::NameAsc;

    public function requiredPermission(): ?Permission
    {
        return match ($this) {
            self::PriceAsc, self::PriceDesc => Permission::PricingViewSelling,
            self::StockAsc => Permission::StockView,
            default => null,
        };
    }

    public function apply(Builder $query): Builder
    {
        $table = $query->getModel()->getTable();

        return match ($this) {
            self::NameAsc => $query->orderBy("$table.name"),
            self::NameDesc => $query->orderByDesc("$table.name"),
            self::PriceAsc => $query->orderBy("$table.selling_price")->orderBy("$table.name"),
            self::PriceDesc => $query->orderByDesc("$table.selling_price")->orderBy("$table.name"),
            self::Newest => $query->orderByDesc("$table.created_at")->orderByDesc("$table.id"),
            self::StockAsc => $query->orderBy("$table.sellable_stock")->orderBy("$table.name"),
        };
    }
}
