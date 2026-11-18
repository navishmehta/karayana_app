<?php

namespace App\Http\Controllers\Api\V1\Auth;

use App\Http\Controllers\Controller;
use App\Http\Requests\Auth\ChangePasswordRequest;
use App\Http\Requests\Auth\UpdateProfileRequest;
use App\Http\Resources\Auth\AuthUserResource;
use App\Services\Auth\AuthService;
use App\Support\ApiResponse;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class ProfileController extends Controller
{
    public function __construct(private readonly AuthService $auth) {}

    public function show(Request $request): AuthUserResource
    {
        return new AuthUserResource($request->user());
    }

    public function update(UpdateProfileRequest $request): AuthUserResource
    {
        return new AuthUserResource($this->auth->updateProfile($request->user(), $request->validated()));
    }

    public function changePassword(ChangePasswordRequest $request): JsonResponse
    {
        $this->auth->changePassword($request->user(), $request->password);

        return ApiResponse::message('password_changed');
    }
}
