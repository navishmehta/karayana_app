<?php

namespace App\Http\Requests\Staff;

use App\Constants\AppConstants;
use App\Enums\Permission;
use App\Models\Product;
use App\Models\Unit;
use App\Rules\CatalogueRules;
use App\Support\Money;
use DateTimeInterface;
use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;
use Illuminate\Validation\Validator;

/**
 * Create (POST) and update (PATCH) of product details.
 *  - Purchase price and internal notes: only with pricing.view_purchase.
 *  - Changing selling price / MRP / offer after creation: only with pricing.update_selling.
 *  - Stock quantities are not accepted here at all (inventory module only).
 */
class ProductRequest extends FormRequest
{
    public function rules(): array
    {
        $product = $this->product();
        $creating = $product === null;
        $required = $creating ? 'required' : 'sometimes';

        $rules = [
            'name' => [$required, 'string', 'max:191'],
            'description' => ['sometimes', 'nullable', 'string', 'max:5000'],
            'category_id' => [$required, 'integer', CatalogueRules::existsInStore('categories')],
            'brand_id' => ['sometimes', 'nullable', 'integer', CatalogueRules::existsInStore('brands')],
            'unit_id' => [$required, 'integer', Rule::exists('units', 'id')->where('is_active', true)],
            'sku' => [$creating ? 'nullable' : 'sometimes', 'string', 'max:64', 'regex:/^[A-Za-z0-9._\/-]+$/',
                CatalogueRules::uniqueInStore('products', 'sku', $product?->id)],
            'barcode' => ['sometimes', 'nullable', 'string', 'max:64', 'regex:/^[A-Za-z0-9]+$/',
                CatalogueRules::uniqueInStore('products', 'barcode', $product?->id)],

            'selling_price' => [$required, ...CatalogueRules::price()],
            'mrp' => ['sometimes', 'nullable', ...CatalogueRules::price()],
            'offer_price' => ['sometimes', 'nullable', ...CatalogueRules::price()],
            'offer_starts_at' => ['sometimes', 'nullable', ...CatalogueRules::date()],
            'offer_ends_at' => ['sometimes', 'nullable', ...CatalogueRules::date()],
            'purchase_price' => ['sometimes', 'nullable', ...CatalogueRules::price()],
            'tax_rate' => ['sometimes', 'nullable', 'numeric', 'min:0', 'max:100', 'decimal:0,2'],
            'hsn_code' => ['sometimes', 'nullable', 'string', 'max:10', 'regex:/^\d+$/'],

            'min_stock_level' => ['sometimes', ...CatalogueRules::quantity()],
            'max_stock_level' => ['sometimes', 'nullable', ...CatalogueRules::quantity()],

            'track_expiry' => ['sometimes', 'boolean'],
            'show_expiry_to_customers' => ['sometimes', 'boolean'],
            'is_active' => ['sometimes', 'boolean'],
            'is_visible_to_customers' => ['sometimes', 'boolean'],
            'is_featured' => ['sometimes', 'boolean'],
            'internal_notes' => ['sometimes', 'nullable', 'string', 'max:2000'],
        ];

        $user = $this->user();
        if (! $user->hasPermission(Permission::PricingViewPurchase)) {
            $rules = array_merge($rules, array_fill_keys(Product::PRIVATE_FIELDS, ['prohibited']));
        }
        if (! $creating && ! $user->hasPermission(Permission::PricingUpdateSelling)) {
            $rules = array_merge($rules, array_fill_keys(Product::SELLING_PRICE_FIELDS, ['prohibited']));
        }

        return $rules;
    }

    /** Rules that compare fields, using stored values for anything not sent in this request. */
    public function after(): array
    {
        return [function (Validator $validator) {
            if ($validator->errors()->isNotEmpty()) {
                return;
            }

            $value = fn (string $key) => $this->has($key) ? $this->input($key) : $this->product()?->getAttribute($key);
            $selling = (string) $value('selling_price');
            $mrp = $value('mrp');
            $offer = $value('offer_price');

            if ($mrp !== null && Money::compare($selling, (string) $mrp) > 0) {
                $validator->errors()->add('selling_price', __('validation.selling_above_mrp'));
            }
            if ($offer !== null && Money::compare((string) $offer, $selling) >= 0) {
                $validator->errors()->add('offer_price', __('validation.offer_not_below_selling'));
            }

            $date = fn ($v) => $v instanceof DateTimeInterface ? $v->format(AppConstants::API_DATE_FORMAT) : $v;
            $starts = $date($value('offer_starts_at'));
            $ends = $date($value('offer_ends_at'));
            if ($starts && $ends && $ends < $starts) {
                $validator->errors()->add('offer_ends_at', __('validation.offer_end_before_start'));
            }

            $min = (string) ($value('min_stock_level') ?? '0');
            $max = $value('max_stock_level');
            if ($max !== null && Money::compare((string) $max, $min) < 0) {
                $validator->errors()->add('max_stock_level', __('validation.max_below_min_stock'));
            }

            $unit = Unit::find($value('unit_id'));
            if ($unit && ! $unit->allows_decimal) {
                foreach (['min_stock_level', 'max_stock_level'] as $field) {
                    $qty = $value($field);
                    if ($qty !== null && floor((float) $qty) != (float) $qty) {
                        $validator->errors()->add($field, __('validation.whole_number_for_unit', ['unit' => $unit->short_name]));
                    }
                }
            }
        }];
    }

    private function product(): ?Product
    {
        $product = $this->route('product');

        return $product instanceof Product ? $product : null;
    }
}
