<?php

use App\Enums\RateLimit;
use App\Http\Controllers\Api\V1\Auth\DeviceTokenController;
use App\Http\Controllers\Api\V1\Auth\LoginController;
use App\Http\Controllers\Api\V1\Auth\PasswordResetController;
use App\Http\Controllers\Api\V1\Auth\ProfileController;
use App\Http\Controllers\Api\V1\Auth\SessionController;
use Illuminate\Support\Facades\Route;

Route::prefix('auth')->name('auth.')->group(function () {
    Route::post('login', LoginController::class)->middleware(RateLimit::Login->middleware())->name('login');

    Route::middleware(RateLimit::PasswordReset->middleware())->group(function () {
        Route::post('forgot-password', [PasswordResetController::class, 'sendCode'])->name('password.forgot');
        Route::post('reset-password', [PasswordResetController::class, 'reset'])->name('password.reset');
    });

    Route::middleware(['auth:sanctum', 'active', RateLimit::Api->middleware()])->group(function () {
        Route::post('logout', [SessionController::class, 'logout'])->name('logout');
        Route::post('logout-all', [SessionController::class, 'logoutAll'])->name('logout-all');
        Route::get('me', [ProfileController::class, 'show'])->name('me');
        Route::patch('me', [ProfileController::class, 'update'])->name('me.update');
        Route::put('password', [ProfileController::class, 'changePassword'])->name('password.change');
    });
});

Route::middleware(['auth:sanctum', 'active', RateLimit::Api->middleware()])->group(function () {
    Route::post('devices', [DeviceTokenController::class, 'store'])->name('devices.store');
    Route::delete('devices/{token}', [DeviceTokenController::class, 'destroy'])->name('devices.destroy');
});
