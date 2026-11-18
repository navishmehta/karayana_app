<?php

namespace App\Http\Controllers\Api\V1\Auth;

use App\Http\Controllers\Controller;
use App\Http\Requests\Auth\StoreDeviceTokenRequest;
use App\Models\DeviceToken;
use App\Support\ApiResponse;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Http\Response;

/** FCM registration tokens for push notifications. A token moves to whoever logged in last on that device. */
class DeviceTokenController extends Controller
{
    public function store(StoreDeviceTokenRequest $request): JsonResponse
    {
        DeviceToken::updateOrCreate(
            ['token' => $request->token],
            ['user_id' => $request->user()->id, 'platform' => $request->platform, 'last_seen_at' => now()],
        );

        return ApiResponse::message('device_registered', 201);
    }

    public function destroy(Request $request, string $token): Response
    {
        $request->user()->deviceTokens()->where('token', $token)->delete();

        return response()->noContent();
    }
}
