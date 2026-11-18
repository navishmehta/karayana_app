<?php

use App\Enums\Permission;
use App\Enums\RateLimit;
use App\Http\Controllers\Api\V1\Staff\BrandController;
use App\Http\Controllers\Api\V1\Staff\CategoryController;
use App\Http\Controllers\Api\V1\Staff\ProductController;
use App\Http\Controllers\Api\V1\Staff\ProductImageController;
use App\Http\Controllers\Api\V1\Staff\UnitController;
use Illuminate\Support\Facades\Route;

/**
 * Staff area (admin + sellers). Every route names the permission it needs;
 * the admin passes all checks. Field-level rules live in the FormRequests and Resources.
 */
Route::middleware(['auth:sanctum', 'active', RateLimit::Api->middleware()])->group(function () {
    // Categories
    Route::middleware(Permission::CategoriesView->middleware())->group(function () {
        Route::get('categories', [CategoryController::class, 'index'])->name('categories.index');
        Route::get('categories/{category}', [CategoryController::class, 'show'])->name('categories.show');
    });
    Route::post('categories', [CategoryController::class, 'store'])
        ->middleware(Permission::CategoriesCreate->middleware())->name('categories.store');
    Route::middleware(Permission::CategoriesUpdate->middleware())->group(function () {
        Route::patch('categories/reorder', [CategoryController::class, 'reorder'])->name('categories.reorder');
        Route::patch('categories/{category}', [CategoryController::class, 'update'])->name('categories.update');
        Route::post('categories/{category}/image', [CategoryController::class, 'uploadImage'])->name('categories.image.store');
        Route::delete('categories/{category}/image', [CategoryController::class, 'deleteImage'])->name('categories.image.destroy');
    });
    Route::delete('categories/{category}', [CategoryController::class, 'destroy'])
        ->middleware(Permission::CategoriesDelete->middleware())->name('categories.destroy');

    // Lookups used by the product form
    Route::middleware(Permission::ProductsView->middleware())->group(function () {
        Route::get('units', [UnitController::class, 'index'])->name('units.index');
        Route::get('brands', [BrandController::class, 'index'])->name('brands.index');
    });
    Route::post('brands', [BrandController::class, 'store'])
        ->middleware(Permission::anyMiddleware(Permission::ProductsCreate, Permission::ProductsUpdate))->name('brands.store');

    // Products
    Route::middleware(Permission::ProductsView->middleware())->group(function () {
        Route::get('products', [ProductController::class, 'index'])->name('products.index');
        Route::get('products/lookup', [ProductController::class, 'lookup'])->name('products.lookup');
        Route::get('products/{product}', [ProductController::class, 'show'])->name('products.show');
    });
    Route::post('products', [ProductController::class, 'store'])
        ->middleware(Permission::ProductsCreate->middleware())->name('products.store');
    Route::middleware(Permission::ProductsUpdate->middleware())->scopeBindings()->group(function () {
        Route::patch('products/{product}', [ProductController::class, 'update'])->name('products.update');
        Route::post('products/{product}/images', [ProductImageController::class, 'store'])->name('products.images.store');
        Route::patch('products/{product}/images/{image}', [ProductImageController::class, 'update'])->name('products.images.update');
        Route::delete('products/{product}/images/{image}', [ProductImageController::class, 'destroy'])->name('products.images.destroy');
    });
    Route::delete('products/{product}', [ProductController::class, 'destroy'])
        ->middleware(Permission::ProductsDelete->middleware())->name('products.destroy');
});
