<?php

namespace App\Models;

use App\Constants\AppConstants;
use App\Enums\StockTransactionType;
use App\Models\Concerns\BelongsToStore;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\MorphTo;
use LogicException;

/** Append-only stock ledger. Mistakes are corrected with a new reversing transaction. */
class StockTransaction extends Model
{
    use BelongsToStore;

    public const UPDATED_AT = null;

    protected $fillable = [
        'store_id', 'product_id', 'batch_id', 'type', 'quantity_change',
        'product_qty_before', 'product_qty_after', 'batch_qty_before', 'batch_qty_after',
        'unit_cost', 'reason', 'reference_type', 'reference_id', 'idempotency_key', 'user_id',
    ];

    protected $casts = [
        'type' => StockTransactionType::class,
        'quantity_change' => AppConstants::QUANTITY_CAST,
        'product_qty_before' => AppConstants::QUANTITY_CAST,
        'product_qty_after' => AppConstants::QUANTITY_CAST,
        'batch_qty_before' => AppConstants::QUANTITY_CAST,
        'batch_qty_after' => AppConstants::QUANTITY_CAST,
        'unit_cost' => AppConstants::MONEY_CAST,
        'created_at' => 'datetime',
    ];

    protected static function booted(): void
    {
        static::updating(fn () => throw new LogicException('Stock transactions are append-only.'));
        static::deleting(fn () => throw new LogicException('Stock transactions are append-only.'));
    }

    public function product(): BelongsTo
    {
        return $this->belongsTo(Product::class);
    }

    public function batch(): BelongsTo
    {
        return $this->belongsTo(ProductBatch::class, 'batch_id');
    }

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    public function reference(): MorphTo
    {
        return $this->morphTo();
    }
}
