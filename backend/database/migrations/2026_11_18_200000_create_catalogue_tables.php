<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('units', function (Blueprint $table) {
            $table->id();
            $table->string('name', 50);
            $table->string('short_name', 10)->unique();
            $table->boolean('allows_decimal')->default(false); // kg/L allow 1.5, pcs does not
            $table->boolean('is_active')->default(true);
            $table->timestamps();
        });

        Schema::create('brands', function (Blueprint $table) {
            $table->id();
            $table->foreignId('store_id')->constrained()->restrictOnDelete();
            $table->string('name', 120);
            $table->string('slug', 140);
            $table->boolean('is_active')->default(true);
            $table->timestamps();
            $table->softDeletes();
            $table->unique(['store_id', 'slug']);
        });

        Schema::create('categories', function (Blueprint $table) {
            $table->id();
            $table->foreignId('store_id')->constrained()->restrictOnDelete();
            $table->foreignId('parent_id')->nullable()->constrained('categories')->restrictOnDelete();
            $table->string('name', 120);
            $table->json('name_translations')->nullable(); // optional admin-entered {"pa": "..."}
            $table->string('slug', 140);
            $table->text('description')->nullable();
            $table->string('image_path')->nullable();
            $table->string('image_thumb_path')->nullable();
            $table->integer('sort_order')->default(0);
            $table->boolean('is_active')->default(true);
            $table->foreignId('created_by')->nullable()->constrained('users')->nullOnDelete();
            $table->foreignId('updated_by')->nullable()->constrained('users')->nullOnDelete();
            $table->timestamps();
            $table->softDeletes();
            $table->unique(['store_id', 'slug']);
            $table->index(['store_id', 'is_active', 'sort_order']);
        });

        Schema::create('products', function (Blueprint $table) {
            $table->id();
            $table->foreignId('store_id')->constrained()->restrictOnDelete();
            $table->foreignId('category_id')->constrained()->restrictOnDelete();
            $table->foreignId('brand_id')->nullable()->constrained()->nullOnDelete();
            $table->foreignId('unit_id')->constrained()->restrictOnDelete();
            $table->string('name', 191);
            $table->string('slug', 210);
            $table->text('description')->nullable();
            $table->string('sku', 64);
            $table->string('barcode', 64)->nullable();

            // Pricing. purchase_price is PRIVATE (never in public API). Profit is computed, never stored.
            $table->decimal('purchase_price', 12, 2)->nullable();
            $table->decimal('selling_price', 12, 2);
            $table->decimal('mrp', 12, 2)->nullable();
            $table->decimal('offer_price', 12, 2)->nullable();
            $table->date('offer_starts_at')->nullable();
            $table->date('offer_ends_at')->nullable();
            $table->decimal('tax_rate', 5, 2)->nullable(); // future GST billing
            $table->string('hsn_code', 10)->nullable();    // future

            // Stock. current_stock / sellable_stock are caches of product_batches, maintained by InventoryService.
            $table->decimal('opening_stock', 12, 3)->default(0);
            $table->decimal('current_stock', 12, 3)->default(0);
            $table->decimal('sellable_stock', 12, 3)->default(0); // excludes expired batches
            $table->decimal('min_stock_level', 12, 3)->default(0);
            $table->decimal('max_stock_level', 12, 3)->nullable();
            $table->string('stock_status', 12)->storedAs(
                "CASE WHEN sellable_stock <= 0 THEN 'out_of_stock' WHEN sellable_stock <= min_stock_level THEN 'low_stock' ELSE 'in_stock' END"
            );

            $table->boolean('track_expiry')->default(true);
            $table->boolean('show_expiry_to_customers')->default(false);
            $table->boolean('is_active')->default(true);
            $table->boolean('is_visible_to_customers')->default(true);
            $table->boolean('is_featured')->default(false);
            $table->text('internal_notes')->nullable(); // PRIVATE

            $table->foreignId('created_by')->nullable()->constrained('users')->nullOnDelete();
            $table->foreignId('updated_by')->nullable()->constrained('users')->nullOnDelete();
            $table->timestamps();
            $table->softDeletes();

            $table->unique(['store_id', 'slug']);
            $table->unique(['store_id', 'sku']);
            $table->unique(['store_id', 'barcode']);
            $table->index(['store_id', 'is_active', 'is_visible_to_customers', 'category_id'], 'products_catalogue_idx');
            $table->index(['store_id', 'stock_status']);
            $table->index(['store_id', 'selling_price']);
            $table->index(['store_id', 'created_at']);
            $table->fullText(['name', 'description']);
        });

        DB::statement('ALTER TABLE products
            ADD CONSTRAINT products_prices_non_negative CHECK (selling_price >= 0 AND (purchase_price IS NULL OR purchase_price >= 0)),
            ADD CONSTRAINT products_selling_le_mrp CHECK (mrp IS NULL OR selling_price <= mrp),
            ADD CONSTRAINT products_offer_lt_selling CHECK (offer_price IS NULL OR (offer_price >= 0 AND offer_price < selling_price)),
            ADD CONSTRAINT products_stock_levels CHECK (min_stock_level >= 0 AND (max_stock_level IS NULL OR max_stock_level >= min_stock_level))');

        Schema::create('product_images', function (Blueprint $table) {
            $table->id();
            $table->foreignId('product_id')->constrained()->cascadeOnDelete();
            $table->string('path');
            $table->string('thumb_path');
            $table->boolean('is_primary')->default(false);
            $table->unsignedSmallInteger('sort_order')->default(0);
            $table->timestamps();
            $table->index(['product_id', 'sort_order']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('product_images');
        Schema::dropIfExists('products');
        Schema::dropIfExists('categories');
        Schema::dropIfExists('brands');
        Schema::dropIfExists('units');
    }
};
