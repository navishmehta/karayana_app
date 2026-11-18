<?php

namespace App\Models;

use App\Constants\AppConstants;
use App\Enums\StockStatus;
use App\Models\Concerns\BelongsToStore;
use App\Models\Concerns\HasUniqueSlug;
use Database\Factories\ProductFactory;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Database\Eloquent\SoftDeletes;

/**
 * Stock columns (opening_stock, current_stock, sellable_stock) are NOT fillable:
 * they change only through the inventory service so every change has a ledger row.
 * Private fields (purchase_price, internal_notes) must only be exposed via permission-aware resources.
 */
class Product extends Model
{
    /** @use HasFactory<ProductFactory> */
    use BelongsToStore, HasFactory, HasUniqueSlug, SoftDeletes;

    /** Fields only users with pricing.view_purchase may see or set. */
    public const PRIVATE_FIELDS = ['purchase_price', 'internal_notes'];

    /** Fields that need pricing.update_selling to change after creation. */
    public const SELLING_PRICE_FIELDS = ['selling_price', 'mrp', 'offer_price', 'offer_starts_at', 'offer_ends_at'];

    protected $fillable = [
        'category_id', 'brand_id', 'unit_id', 'name', 'description', 'sku', 'barcode',
        'purchase_price', 'selling_price', 'mrp', 'offer_price', 'offer_starts_at', 'offer_ends_at',
        'tax_rate', 'hsn_code', 'min_stock_level', 'max_stock_level', 'track_expiry',
        'show_expiry_to_customers', 'is_active', 'is_visible_to_customers', 'is_featured',
        'internal_notes', 'created_by', 'updated_by',
    ];

    protected $casts = [
        'purchase_price' => AppConstants::MONEY_CAST,
        'selling_price' => AppConstants::MONEY_CAST,
        'mrp' => AppConstants::MONEY_CAST,
        'offer_price' => AppConstants::MONEY_CAST,
        'tax_rate' => AppConstants::MONEY_CAST,
        'opening_stock' => AppConstants::QUANTITY_CAST,
        'current_stock' => AppConstants::QUANTITY_CAST,
        'sellable_stock' => AppConstants::QUANTITY_CAST,
        'min_stock_level' => AppConstants::QUANTITY_CAST,
        'max_stock_level' => AppConstants::QUANTITY_CAST,
        'offer_starts_at' => 'date',
        'offer_ends_at' => 'date',
        'stock_status' => StockStatus::class,
        'track_expiry' => 'boolean',
        'show_expiry_to_customers' => 'boolean',
        'is_active' => 'boolean',
        'is_visible_to_customers' => 'boolean',
        'is_featured' => 'boolean',
    ];

    public function category(): BelongsTo
    {
        return $this->belongsTo(Category::class);
    }

    public function brand(): BelongsTo
    {
        return $this->belongsTo(Brand::class);
    }

    public function unit(): BelongsTo
    {
        return $this->belongsTo(Unit::class);
    }

    public function images(): HasMany
    {
        return $this->hasMany(ProductImage::class)->orderByDesc('is_primary')->orderBy('sort_order');
    }

    public function batches(): HasMany
    {
        return $this->hasMany(ProductBatch::class);
    }

    public function stockTransactions(): HasMany
    {
        return $this->hasMany(StockTransaction::class);
    }
}
