<?php

namespace App\Models\Concerns;

use App\Models\Store;
use App\Support\CurrentStore;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

/**
 * Every query is limited to the current store, and new rows get its store_id.
 * One store can never read or change another store's data, even by guessing IDs.
 */
trait BelongsToStore
{
    public static function bootBelongsToStore(): void
    {
        static::addGlobalScope('store', fn (Builder $query) => $query->where(
            $query->qualifyColumn('store_id'),
            CurrentStore::id(),
        ));

        static::creating(function ($model) {
            $model->store_id ??= CurrentStore::id();
        });
    }

    public function store(): BelongsTo
    {
        return $this->belongsTo(Store::class);
    }
}
