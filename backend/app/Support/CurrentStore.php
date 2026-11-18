<?php

namespace App\Support;

use App\Models\Store;

/**
 * The store the current request works on: the logged-in user's store,
 * or the default store for guests (public catalogue). V4 multi-store changes only this class.
 */
final class CurrentStore
{
    public static function id(): int
    {
        return auth()->user()?->store_id ?? once(fn () => Store::default()->id);
    }
}
