<?php

use App\Http\Controllers\Api\V1\HealthController;
use Illuminate\Support\Facades\Route;

Route::prefix('v1')->name('v1.')->group(function () {
    Route::get('health', HealthController::class)->name('health');

    require __DIR__.'/api/v1/auth.php';
    require __DIR__.'/api/v1/admin.php';
    // Later phases: public.php (catalogue), staff.php (products, stock, expiry, reports)
});
