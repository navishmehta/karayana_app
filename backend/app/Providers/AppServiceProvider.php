<?php

namespace App\Providers;

use App\Models;
use Illuminate\Database\Eloquent\Relations\Relation;
use Illuminate\Support\Facades\Gate;
use Illuminate\Support\Facades\Route;
use Illuminate\Support\ServiceProvider;
use Illuminate\Validation\Rules\Password;

class AppServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        //
    }

    public function boot(): void
    {
        // Short, stable names in polymorphic columns (ledger references, activity log, roles) instead of class names.
        Relation::enforceMorphMap([
            'user' => Models\User::class,
            'store' => Models\Store::class,
            'category' => Models\Category::class,
            'brand' => Models\Brand::class,
            'unit' => Models\Unit::class,
            'product' => Models\Product::class,
            'product_image' => Models\ProductImage::class,
            'product_batch' => Models\ProductBatch::class,
            'inventory_adjustment' => Models\InventoryAdjustment::class,
            'stock_transaction' => Models\StockTransaction::class,
            'app_setting' => Models\AppSetting::class,
        ]);

        // Admin has every permission. Sellers are checked against their individually granted permissions.
        Gate::before(fn (Models\User $user) => $user->isAdmin() ? true : null);

        Password::defaults(fn () => Password::min(config('kirana.auth.password_min_length'))->letters()->numbers());

        // {seller} only resolves to a seller of the logged-in admin's store; anything else is a 404.
        Route::bind('seller', fn (string $id) => Models\User::sellers()
            ->where('store_id', request()->user()?->store_id)
            ->findOrFail($id));
    }
}
