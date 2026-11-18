<?php

namespace App\Support;

use App\Constants\AppConstants;
use Illuminate\Http\Request;

final class Pagination
{
    /** Reads ?per_page, clamped to 1..MAX_PER_PAGE. */
    public static function perPage(Request $request): int
    {
        $perPage = (int) $request->query('per_page', AppConstants::DEFAULT_PER_PAGE);

        return max(1, min($perPage, AppConstants::MAX_PER_PAGE));
    }
}
