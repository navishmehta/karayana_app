<?php

use App\Enums\RateLimit;
use App\Enums\Role;
use App\Http\Controllers\Api\V1\Admin\ActivityLogController;
use App\Http\Controllers\Api\V1\Admin\PermissionController;
use App\Http\Controllers\Api\V1\Admin\SellerController;
use Illuminate\Support\Facades\Route;

/** Admin-only area. Sellers can never be granted access to these routes. */
Route::prefix('admin')->name('admin.')
    ->middleware(['auth:sanctum', 'active', RateLimit::Api->middleware(), 'role:'.Role::Admin->value])
    ->group(function () {
        Route::get('permissions', PermissionController::class)->name('permissions.index');

        Route::apiResource('sellers', SellerController::class);
        Route::put('sellers/{seller}/permissions', [SellerController::class, 'updatePermissions'])->name('sellers.permissions');
        Route::patch('sellers/{seller}/status', [SellerController::class, 'updateStatus'])->name('sellers.status');
        Route::post('sellers/{seller}/reset-password', [SellerController::class, 'resetPassword'])->name('sellers.reset-password');
        Route::get('sellers/{seller}/activity', [ActivityLogController::class, 'forSeller'])->name('sellers.activity');

        Route::get('activity-logs', [ActivityLogController::class, 'index'])->name('activity-logs.index');
    });
