<?php

namespace App\Http\Resources\Staff;

use App\Enums\Permission;
use App\Models\Product;
use App\Services\Catalogue\PricingCalculator;
use App\Support\StoreClock;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

/**
 * Product for staff. Each field group appears only if the user has the matching permission;
 * groups the user can't see are left out entirely (not sent as null).
 *
 * @mixin Product
 */
class ProductResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        $user = $request->user();
        $pricing = app(PricingCalculator::class);

        return [
            'id' => $this->id,
            'name' => $this->name,
            'slug' => $this->slug,
            'description' => $this->description,
            'sku' => $this->sku,
            'barcode' => $this->barcode,
            'category' => $this->whenLoaded('category', fn () => ['id' => $this->category->id, 'name' => $this->category->name]),
            'brand' => $this->whenLoaded('brand', fn () => $this->brand ? ['id' => $this->brand->id, 'name' => $this->brand->name] : null),
            'unit' => new UnitResource($this->whenLoaded('unit')),
            'images' => ProductImageResource::collection($this->whenLoaded('images')),
            'tax_rate' => $this->tax_rate,
            'hsn_code' => $this->hsn_code,
            'track_expiry' => $this->track_expiry,
            'show_expiry_to_customers' => $this->show_expiry_to_customers,
            'is_active' => $this->is_active,
            'is_visible_to_customers' => $this->is_visible_to_customers,
            'is_featured' => $this->is_featured,

            $this->mergeWhen($user->hasPermission(Permission::PricingViewSelling), fn () => [
                'selling_price' => $this->selling_price,
                'mrp' => $this->mrp,
                'offer_price' => $this->offer_price,
                'offer_starts_at' => StoreClock::toApiDate($this->offer_starts_at),
                'offer_ends_at' => StoreClock::toApiDate($this->offer_ends_at),
                'on_offer' => $pricing->isOfferActive($this->resource),
                'effective_price' => $pricing->effectivePrice($this->resource),
                'discount_percent' => $pricing->discountPercent($this->resource),
            ]),

            $this->mergeWhen($user->hasPermission(Permission::PricingViewPurchase), fn () => [
                'purchase_price' => $this->purchase_price,
                'profit' => $pricing->profit($this->resource),
                'internal_notes' => $this->internal_notes,
            ]),

            $this->mergeWhen($user->hasPermission(Permission::StockView), fn () => [
                'opening_stock' => $this->opening_stock,
                'current_stock' => $this->current_stock,
                'sellable_stock' => $this->sellable_stock,
                'min_stock_level' => $this->min_stock_level,
                'max_stock_level' => $this->max_stock_level,
                'stock_status' => $this->stock_status,
            ]),

            'created_at' => StoreClock::toApi($this->created_at),
            'updated_at' => StoreClock::toApi($this->updated_at),
            'deleted_at' => $this->when($this->trashed(), fn () => StoreClock::toApi($this->deleted_at)),
        ];
    }
}
