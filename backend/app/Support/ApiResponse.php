<?php

namespace App\Support;

use Illuminate\Http\JsonResponse;

final class ApiResponse
{
    /** Simple success response with a translated message from lang/{locale}/messages.php. */
    public static function message(string $key, int $status = 200): JsonResponse
    {
        return response()->json(['message' => __('messages.'.$key)], $status);
    }
}
