<?php

namespace App\Http\Controllers\Api\V1\Auth;

use App\Http\Controllers\Controller;
use App\Http\Requests\Auth\ForgotPasswordRequest;
use App\Http\Requests\Auth\ResetPasswordRequest;
use App\Services\Auth\PasswordResetService;
use App\Support\ApiResponse;
use Illuminate\Http\JsonResponse;

class PasswordResetController extends Controller
{
    public function __construct(private readonly PasswordResetService $resets) {}

    /** Always the same response, whether or not the email exists. */
    public function sendCode(ForgotPasswordRequest $request): JsonResponse
    {
        $this->resets->sendCode($request->email);

        return ApiResponse::message('reset_code_sent');
    }

    public function reset(ResetPasswordRequest $request): JsonResponse
    {
        $this->resets->reset($request->email, $request->code, $request->password);

        return ApiResponse::message('password_reset');
    }
}
