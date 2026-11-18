<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class StockAlert extends Model
{
    public $timestamps = false;

    protected $fillable = [
        'store_id', 'type', 'product_id', 'batch_id', 'dedupe_key', 'status',
        'triggered_at', 'resolved_at', 'last_notified_at',
    ];

    protected $casts = ['triggered_at' => 'datetime', 'resolved_at' => 'datetime', 'last_notified_at' => 'datetime'];

    public function product(): BelongsTo
    {
        return $this->belongsTo(Product::class);
    }

    public function batch(): BelongsTo
    {
        return $this->belongsTo(ProductBatch::class, 'batch_id');
    }
}
