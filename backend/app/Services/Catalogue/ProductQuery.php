<?php

namespace App\Services\Catalogue;

use App\Enums\ProductSort;
use App\Models\Product;
use App\Support\Search;
use Illuminate\Database\Eloquent\Builder;

/**
 * Builds product list queries from validated filters. Shared by the staff list and (Phase 5) the public catalogue.
 * Permission checks on which filters/sorts are allowed happen in the FormRequest before this runs.
 */
class ProductQuery
{
    public function build(array $filters, ?Builder $query = null): Builder
    {
        $query ??= Product::query();

        $this->search($query, $filters['search'] ?? null);

        $query
            ->when($filters['category_id'] ?? null, fn ($q, $ids) => $q->whereIn('category_id', (array) $ids))
            ->when($filters['brand_id'] ?? null, fn ($q, $ids) => $q->whereIn('brand_id', (array) $ids))
            ->when(isset($filters['min_price']), fn ($q) => $q->where('selling_price', '>=', $filters['min_price']))
            ->when(isset($filters['max_price']), fn ($q) => $q->where('selling_price', '<=', $filters['max_price']))
            ->when($filters['stock_status'] ?? null, fn ($q, $status) => $q->where('stock_status', $status))
            ->when($filters['status'] ?? null, fn ($q, $status) => $q->where('is_active', $status === 'active'))
            ->when($filters['visibility'] ?? null, fn ($q, $v) => $q->where('is_visible_to_customers', $v === 'visible'))
            ->when(isset($filters['featured']), fn ($q) => $q->where('is_featured', (bool) $filters['featured']));

        $sort = ProductSort::tryFrom($filters['sort'] ?? '') ?? ProductSort::DEFAULT;

        return $sort->apply($query);
    }

    /** Matches name, SKU/barcode (prefix), brand and category name. */
    private function search(Builder $query, ?string $term): void
    {
        if ($term === null || trim($term) === '') {
            return;
        }

        $contains = Search::contains($term);
        $prefix = Search::startsWith($term);

        $query->where(fn (Builder $q) => $q
            ->where('name', 'like', $contains)
            ->orWhere('sku', 'like', $prefix)
            ->orWhere('barcode', 'like', $prefix)
            ->orWhereHas('brand', fn ($b) => $b->where('name', 'like', $contains))
            ->orWhereHas('category', fn ($c) => $c->where('name', 'like', $contains)));
    }
}
