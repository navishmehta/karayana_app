<?php

namespace App\Models;

use App\Constants\AppConstants;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\MorphMany;

class InventoryAdjustment extends Model
{
    public const UPDATED_AT = null;

    protected $fillable = ['store_id', 'type', 'reason_code', 'notes', 'attachment_path', 'cost_impact', 'created_by'];

    protected $casts = ['cost_impact' => AppConstants::MONEY_CAST];

    public function lines(): MorphMany
    {
        return $this->morphMany(StockTransaction::class, 'reference');
    }

    public function creator(): BelongsTo
    {
        return $this->belongsTo(User::class, 'created_by');
    }
}
