<?php

namespace App\Models;

use App\Constants\AppConstants;
use App\Models\Concerns\BelongsToStore;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

/** quantity_remaining is the source of truth for stock; change it only via the inventory service. */
class ProductBatch extends Model
{
    use BelongsToStore;

    protected $fillable = [
        'store_id', 'product_id', 'batch_number', 'manufacturing_date', 'expiry_date',
        'quantity_received', 'quantity_remaining', 'purchase_price', 'received_at',
        'purchase_item_id', 'notes', 'created_by',
    ];

    protected $casts = [
        'manufacturing_date' => 'date',
        'expiry_date' => 'date',
        'received_at' => 'datetime',
        'quantity_received' => AppConstants::QUANTITY_CAST,
        'quantity_remaining' => AppConstants::QUANTITY_CAST,
        'purchase_price' => AppConstants::MONEY_CAST,
    ];

    public function product(): BelongsTo
    {
        return $this->belongsTo(Product::class);
    }

    public function transactions(): HasMany
    {
        return $this->hasMany(StockTransaction::class, 'batch_id');
    }
}
