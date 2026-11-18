<?php

namespace App\Http\Requests\Staff;

use App\Constants\AppConstants;
use App\Enums\Permission;
use App\Enums\ProductSort;
use App\Enums\StockStatus;
use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;

/** Filtering or sorting by a value the user can't see is refused (403), so hidden values can't be inferred. */
class ProductIndexRequest extends FormRequest
{
    public function authorize(): bool
    {
        $user = $this->user();

        $needsSelling = $this->hasAny(['min_price', 'max_price']);
        $needsStock = $this->has('stock_status');
        $sortPermission = ProductSort::tryFrom((string) $this->query('sort'))?->requiredPermission();

        return (! $needsSelling || $user->hasPermission(Permission::PricingViewSelling))
            && (! $needsStock || $user->hasPermission(Permission::StockView))
            && (! $sortPermission || $user->hasPermission($sortPermission));
    }

    public function rules(): array
    {
        return [
            'search' => ['sometimes', 'nullable', 'string', 'max:'.AppConstants::MAX_SEARCH_LENGTH],
            'category_id' => ['sometimes', 'array'],
            'category_id.*' => ['integer'],
            'brand_id' => ['sometimes', 'array'],
            'brand_id.*' => ['integer'],
            'min_price' => ['sometimes', 'numeric', 'min:0'],
            'max_price' => ['sometimes', 'numeric', 'min:0', 'gte:min_price'],
            'stock_status' => ['sometimes', Rule::enum(StockStatus::class)],
            'status' => ['sometimes', Rule::in(['active', 'inactive'])],
            'visibility' => ['sometimes', Rule::in(['visible', 'hidden'])],
            'featured' => ['sometimes', 'boolean'],
            'sort' => ['sometimes', Rule::enum(ProductSort::class)],
            'per_page' => ['sometimes', 'integer', 'min:1', 'max:'.AppConstants::MAX_PER_PAGE],
        ];
    }
}
