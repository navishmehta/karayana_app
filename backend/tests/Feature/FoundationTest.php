<?php

namespace Tests\Feature;

use App\Enums\Permission;
use App\Models\Category;
use App\Models\Product;
use App\Models\ProductBatch;
use App\Models\StockTransaction;
use App\Models\Store;
use App\Models\Unit;
use App\Models\User;
use Database\Seeders\DatabaseSeeder;
use Illuminate\Database\QueryException;
use Illuminate\Support\Facades\Gate;
use LogicException;
use Tests\ApiTestCase;

class FoundationTest extends ApiTestCase
{
    protected function afterRefreshingDatabase(): void
    {
        $this->seed(DatabaseSeeder::class);
    }

    public function test_health_endpoint_returns_json(): void
    {
        $this->getJson('/api/v1/health')->assertOk()->assertJson(['status' => 'ok']);
    }

    public function test_errors_use_uniform_shape_and_are_translated(): void
    {
        $this->get('/api/v1/does-not-exist')
            ->assertNotFound()
            ->assertJson(['code' => 'NOT_FOUND', 'message' => 'The requested item was not found.']);

        $this->get('/api/v1/does-not-exist', ['Accept-Language' => 'pa'])
            ->assertNotFound()
            ->assertHeader('Content-Language', 'pa')
            ->assertJson(['code' => 'NOT_FOUND', 'message' => 'ਮੰਗੀ ਗਈ ਚੀਜ਼ ਨਹੀਂ ਮਿਲੀ।']);
    }

    public function test_seeders_create_store_admin_permissions_units_and_categories(): void
    {
        $this->assertSame(1, Store::count());
        $this->assertSame(count(Permission::cases()), \Spatie\Permission\Models\Permission::count());
        $this->assertTrue(User::where('email', config('kirana.admin.email'))->first()->isAdmin());
        $this->assertSame(10, Category::count());
        $this->assertFalse(Unit::where('short_name', 'pcs')->first()->allows_decimal);

        $this->seed(DatabaseSeeder::class); // idempotent
        $this->assertSame(10, Category::count());
    }

    public function test_admin_passes_every_gate_and_seller_only_granted_ones(): void
    {
        $admin = User::factory()->admin()->create();
        $seller = User::factory()->seller([Permission::ProductsView->value])->create();

        $this->assertTrue(Gate::forUser($admin)->allows(Permission::PricingViewPurchase->value));
        $this->assertTrue(Gate::forUser($seller)->allows(Permission::ProductsView->value));
        $this->assertFalse(Gate::forUser($seller)->allows(Permission::PricingViewPurchase->value));
    }

    public function test_every_permission_dependency_is_a_real_permission(): void
    {
        foreach (Permission::cases() as $permission) {
            foreach ($permission->dependsOn() as $dependency) {
                $this->assertContains($dependency, Permission::cases());
                $this->assertNotSame($permission, $dependency);
            }
        }
    }

    public function test_product_stock_status_is_generated_and_price_rules_enforced(): void
    {
        $product = $this->makeProduct(['min_stock_level' => 5]);
        $this->assertSame('out_of_stock', $product->fresh()->stock_status->value);

        Product::whereKey($product->id)->update(['sellable_stock' => 3]);
        $this->assertSame('low_stock', $product->fresh()->stock_status->value);

        Product::whereKey($product->id)->update(['sellable_stock' => 50]);
        $this->assertSame('in_stock', $product->fresh()->stock_status->value);

        $this->expectException(QueryException::class); // selling price above MRP
        Product::whereKey($product->id)->update(['mrp' => 10, 'selling_price' => 20]);
    }

    public function test_batch_quantity_cannot_go_negative(): void
    {
        $batch = $this->makeBatch($this->makeProduct());

        $this->expectException(QueryException::class);
        $batch->update(['quantity_remaining' => -1]);
    }

    public function test_stock_ledger_is_append_only_and_math_is_checked(): void
    {
        $product = $this->makeProduct();
        $batch = $this->makeBatch($product);
        $tx = StockTransaction::create($this->ledgerRow($product, $batch, 10));

        try {
            $tx->update(['quantity_change' => 99]);
            $this->fail('Ledger update should be refused');
        } catch (LogicException) {
        }

        try {
            $tx->delete();
            $this->fail('Ledger delete should be refused');
        } catch (LogicException) {
        }

        $this->expectException(QueryException::class); // before + change != after
        StockTransaction::create(['product_qty_after' => 5] + $this->ledgerRow($product, $batch, 10));
    }

    private function makeProduct(array $overrides = []): Product
    {
        return Product::create($overrides + [
            'store_id' => Store::default()->id,
            'category_id' => Category::first()->id,
            'unit_id' => Unit::first()->id,
            'name' => 'Test Product',
            'slug' => 'test-product-'.uniqid(),
            'sku' => 'SK-'.uniqid(),
            'selling_price' => 50,
            'mrp' => 60,
        ]);
    }

    private function makeBatch(Product $product): ProductBatch
    {
        return ProductBatch::create([
            'store_id' => $product->store_id,
            'product_id' => $product->id,
            'quantity_received' => 10,
            'quantity_remaining' => 10,
            'received_at' => now(),
            'created_by' => User::first()->id,
        ]);
    }

    private function ledgerRow(Product $product, ProductBatch $batch, int $qty): array
    {
        return [
            'store_id' => $product->store_id,
            'product_id' => $product->id,
            'batch_id' => $batch->id,
            'type' => 'stock_in',
            'quantity_change' => $qty,
            'product_qty_before' => 0,
            'product_qty_after' => $qty,
            'batch_qty_before' => 0,
            'batch_qty_after' => $qty,
            'user_id' => User::first()->id,
        ];
    }
}
