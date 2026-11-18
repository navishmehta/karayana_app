<?php

namespace App\Http\Controllers\Api\V1\Auth;

use App\Constants\AppConstants;
use App\Http\Controllers\Controller;
use App\Http\Requests\Auth\LoginRequest;
use App\Http\Resources\Auth\AuthUserResource;
use App\Services\Auth\AuthService;
use App\Support\StoreClock;
use Illuminate\Http\JsonResponse;

class LoginController extends Controller
{
    public function __invoke(LoginRequest $request, AuthService $auth): JsonResponse
    {
        $token = $auth->login($request->email, $request->password, $request->device_name);

        return response()->json([
            'data' => [
                'token' => $token->plainTextToken,
                'token_type' => AppConstants::TOKEN_TYPE,
                'expires_at' => StoreClock::toApi($token->accessToken->expires_at),
                'user' => new AuthUserResource($token->accessToken->tokenable),
            ],
        ]);
    }
}
