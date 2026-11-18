<?php

namespace Tests\Feature\Catalogue;

use App\Enums\ActivityAction;
use App\Enums\Permission;
use App\Models\Brand;
use App\Models\Category;
use App\Models\Product;
use App\Models\Store;
use App\Models\Unit;
use App\Models\User;
use Database\Seeders\UnitSeeder;
use Tests\ApiTestCase;

class ProductTest extends ApiTestCase
{
    private Category $category;

    protected function setUp(): void
    {
        parent::setUp();
        $this->seed(UnitSeeder::class);
        $this->category = Category::factory()->create(['name' => 'Dairy']);
    }

    private function payload(array $overrides = []): array
    {
        return $overrides + [
            'name' => 'Amul Butter 500g',
            'category_id' => $this->category->id,
            'unit_id' => Unit::where('short_name', 'pcs')->value('id'),
            'selling_price' => '285',
            'mrp' => '290',
            'purchase_price' => '250',
        ];
    }

    public function test_admin_creates_product_with_auto_sku_slug_and_profit(): void
    {
        $this->actingAsToken($this->admin())->postJson('/api/v1/products', $this->payload())
            ->assertCreated()
            ->assertJsonPath('data.slug', 'amul-butter-500g')
            ->assertJsonPath('data.sku', 'SK-'.str_pad((string) Product::first()->id, 6, '0', STR_PAD_LEFT))
            ->assertJsonPath('data.category.name', 'Dairy')
            ->assertJsonPath('data.profit.amount', '35.00')
            ->assertJsonPath('data.profit.markup_percent', '14.00')
            ->assertJsonPath('data.current_stock', '0.000')
            ->assertJsonPath('data.stock_status', 'out_of_stock');

        $this->assertDatabaseHas('activity_log', ['event' => ActivityAction::ProductCreated->value]);
    }

    public function test_stock_fields_cannot_be_set_through_product_api(): void
    {
        $this->actingAsToken($this->admin())->postJson('/api/v1/products', $this->payload(['current_stock' => 500, 'sellable_stock' => 500]));

        $this->assertSame('0.000', Product::first()->current_stock);
    }

    public function test_price_rules_are_enforced(): void
    {
        $this->actingAsToken($this->admin());

        $this->postJson('/api/v1/products', $this->payload(['selling_price' => '300', 'mrp' => '290']))
            ->assertJsonValidationErrors(['selling_price' => 'Selling price cannot be more than the MRP.']);
        $this->postJson('/api/v1/products', $this->payload(['offer_price' => '285']))->assertJsonValidationErrors('offer_price');
        $this->postJson('/api/v1/products', $this->payload(['offer_starts_at' => '2026-12-10', 'offer_ends_at' => '2026-12-01', 'offer_price' => '280']))
            ->assertJsonValidationErrors('offer_ends_at');
        $this->postJson('/api/v1/products', $this->payload(['selling_price' => '10.555']))->assertJsonValidationErrors('selling_price');
        $this->postJson('/api/v1/products', $this->payload(['min_stock_level' => '2.5']))->assertJsonValidationErrors('min_stock_level');
    }

    public function test_decimal_stock_levels_allowed_for_kg_items(): void
    {
        $this->actingAsToken($this->admin())
            ->postJson('/api/v1/products', $this->payload(['unit_id' => Unit::where('short_name', 'kg')->value('id'), 'min_stock_level' => '2.5']))
            ->assertCreated();
    }

    public function test_update_checks_mrp_against_stored_selling_price(): void
    {
        $product = Product::factory()->create(['selling_price' => '50', 'mrp' => '55']);

        $this->actingAsToken($this->admin())->patchJson("/api/v1/products/{$product->id}", ['mrp' => '45'])
            ->assertJsonValidationErrors('selling_price');
    }

    public function test_price_changes_are_logged_separately_from_detail_changes(): void
    {
        $product = Product::factory()->create();

        $this->actingAsToken($this->admin())->patchJson("/api/v1/products/{$product->id}", ['selling_price' => '52', 'name' => 'Renamed'])->assertOk();

        $this->assertDatabaseHas('activity_log', ['event' => ActivityAction::ProductPriceChanged->value]);
        $this->assertDatabaseHas('activity_log', ['event' => ActivityAction::ProductUpdated->value]);
        $this->assertSame(Product::first()->slug, $product->slug); // slug unchanged after rename
    }

    public function test_private_fields_are_absent_without_permission(): void
    {
        $product = Product::factory()->create(['internal_notes' => 'supplier gives 5% extra']);
        $seller = $this->seller([Permission::ProductsView->value]);

        $json = $this->actingAsToken($seller)->getJson("/api/v1/products/{$product->id}")->assertOk()->json('data');

        foreach (['purchase_price', 'profit', 'internal_notes', 'selling_price', 'mrp', 'current_stock', 'stock_status'] as $field) {
            $this->assertArrayNotHasKey($field, $json, "$field should be hidden");
        }
    }

    public function test_field_groups_appear_with_matching_permissions(): void
    {
        $product = Product::factory()->create();
        $seller = $this->seller([Permission::ProductsView->value, Permission::PricingViewSelling->value, Permission::StockView->value]);

        $json = $this->actingAsToken($seller)->getJson("/api/v1/products/{$product->id}")->json('data');

        $this->assertArrayHasKey('selling_price', $json);
        $this->assertArrayHasKey('current_stock', $json);
        $this->assertArrayNotHasKey('purchase_price', $json);
        $this->assertArrayNotHasKey('profit', $json);
    }

    public function test_seller_cannot_set_purchase_price_or_notes_without_permission(): void
    {
        $seller = $this->seller([Permission::ProductsView->value, Permission::ProductsCreate->value]);

        $this->actingAsToken($seller)->postJson('/api/v1/products', $this->payload(['internal_notes' => 'x']))
            ->assertJsonValidationErrors(['purchase_price', 'internal_notes']);

        $payload = $this->payload();
        unset($payload['purchase_price']);
        $this->postJson('/api/v1/products', $payload)->assertCreated(); // allowed without private fields
    }

    public function test_changing_prices_after_creation_needs_update_selling_permission(): void
    {
        $product = Product::factory()->create();
        $editor = $this->seller([Permission::ProductsView->value, Permission::ProductsUpdate->value]);

        $this->actingAsToken($editor);
        $this->patchJson("/api/v1/products/{$product->id}", ['selling_price' => '1'])->assertJsonValidationErrors('selling_price');
        $this->patchJson("/api/v1/products/{$product->id}", ['name' => 'New name', 'is_active' => false])->assertOk();

        $pricer = $this->seller([Permission::ProductsView->value, Permission::ProductsUpdate->value,
            Permission::PricingViewSelling->value, Permission::PricingUpdateSelling->value]);
        $this->actingAsToken($pricer)->patchJson("/api/v1/products/{$product->id}", ['selling_price' => '45'])
            ->assertOk()->assertJsonPath('data.selling_price', '45.00');
    }

    public function test_search_matches_name_brand_category_sku_and_barcode(): void
    {
        $brand = Brand::factory()->create(['name' => 'Haldiram']);
        Product::factory()->create(['name' => 'Bhujia', 'brand_id' => $brand->id]);
        Product::factory()->create(['name' => 'Milk', 'category_id' => $this->category->id, 'barcode' => '8901234567890', 'sku' => 'MLK-1']);
        Product::factory()->create(['name' => '50% Off Soap']);

        $this->actingAsToken($this->admin());
        $this->getJson('/api/v1/products?search=haldi')->assertJsonCount(1, 'data')->assertJsonPath('data.0.name', 'Bhujia');
        $this->getJson('/api/v1/products?search=dairy')->assertJsonCount(1, 'data')->assertJsonPath('data.0.name', 'Milk');
        $this->getJson('/api/v1/products?search=89012')->assertJsonCount(1, 'data');
        $this->getJson('/api/v1/products?search=MLK')->assertJsonCount(1, 'data');
        $this->getJson('/api/v1/products?search=%25')->assertJsonCount(1, 'data'); // literal %, not wildcard
    }

    public function test_filters_and_sorting(): void
    {
        Product::factory()->create(['name' => 'A', 'selling_price' => '30', 'mrp' => null, 'is_active' => false]);
        Product::factory()->create(['name' => 'B', 'selling_price' => '10', 'mrp' => null]);
        Product::factory()->create(['name' => 'C', 'selling_price' => '20', 'mrp' => null, 'is_visible_to_customers' => false]);

        $this->actingAsToken($this->admin());
        $this->getJson('/api/v1/products?sort=price_asc')->assertJsonPath('data.0.name', 'B');
        $this->getJson('/api/v1/products?sort=name_desc')->assertJsonPath('data.0.name', 'C');
        $this->getJson('/api/v1/products?min_price=15&max_price=25')->assertJsonCount(1, 'data')->assertJsonPath('data.0.name', 'C');
        $this->getJson('/api/v1/products?status=inactive')->assertJsonCount(1, 'data')->assertJsonPath('data.0.name', 'A');
        $this->getJson('/api/v1/products?visibility=hidden')->assertJsonCount(1, 'data')->assertJsonPath('data.0.name', 'C');
        $this->getJson('/api/v1/products?stock_status=out_of_stock')->assertJsonCount(3, 'data');
    }

    public function test_filtering_or_sorting_by_hidden_values_is_forbidden(): void
    {
        $this->actingAsToken($this->seller([Permission::ProductsView->value]));

        $this->getJson('/api/v1/products')->assertOk();
        $this->getJson('/api/v1/products?sort=price_desc')->assertForbidden();
        $this->getJson('/api/v1/products?min_price=10')->assertForbidden();
        $this->getJson('/api/v1/products?stock_status=low_stock')->assertForbidden();
        $this->getJson('/api/v1/products?sort=stock_asc')->assertForbidden();
    }

    public function test_lookup_by_barcode_and_sku(): void
    {
        Product::factory()->create(['barcode' => '8900000000001', 'sku' => 'ABC-1']);
        $this->actingAsToken($this->admin());

        $this->getJson('/api/v1/products/lookup?barcode=8900000000001')->assertOk()->assertJsonPath('data.sku', 'ABC-1');
        $this->getJson('/api/v1/products/lookup?sku=ABC-1')->assertOk();
        $this->getJson('/api/v1/products/lookup?barcode=000')->assertNotFound();
    }

    public function test_barcode_and_sku_must_be_unique(): void
    {
        Product::factory()->create(['barcode' => '111', 'sku' => 'DUP']);

        $this->actingAsToken($this->admin())->postJson('/api/v1/products', $this->payload(['barcode' => '111', 'sku' => 'DUP']))
            ->assertJsonValidationErrors(['barcode', 'sku']);
    }

    public function test_soft_delete_hides_product_and_admin_restores_it(): void
    {
        $product = Product::factory()->create();
        $this->actingAsToken($this->admin());

        $this->deleteJson("/api/v1/products/{$product->id}")->assertNoContent();
        $this->getJson("/api/v1/products/{$product->id}")->assertNotFound();
        $this->postJson("/api/v1/admin/products/{$product->id}/restore")->assertOk();
        $this->getJson("/api/v1/products/{$product->id}")->assertOk();
    }

    public function test_seller_needs_delete_permission_and_cannot_restore(): void
    {
        $product = Product::factory()->create();
        $seller = $this->seller([Permission::ProductsView->value, Permission::ProductsDelete->value]);

        $this->actingAsToken($seller)->deleteJson("/api/v1/products/{$product->id}")->assertNoContent();
        $this->postJson("/api/v1/admin/products/{$product->id}/restore")->assertForbidden();
    }

    public function test_products_of_another_store_are_invisible(): void
    {
        $other = Store::create(['name' => 'Other', 'slug' => 'other']);
        $foreignAdmin = User::factory()->admin()->create(['store_id' => $other->id]);
        $product = Product::factory()->create();

        $this->actingAsToken($foreignAdmin);
        $this->getJson("/api/v1/products/{$product->id}")->assertNotFound();
        $this->getJson('/api/v1/products')->assertJsonCount(0, 'data');
        $this->postJson('/api/v1/products', $this->payload())->assertJsonValidationErrors('category_id');
    }

    public function test_brand_autocomplete_and_create_permissions(): void
    {
        Brand::factory()->create(['name' => 'Amul']);

        $this->actingAsToken($this->seller([Permission::ProductsView->value]));
        $this->getJson('/api/v1/brands?search=am')->assertOk()->assertJsonCount(1, 'data');
        $this->postJson('/api/v1/brands', ['name' => 'Mother Dairy'])->assertForbidden();

        $this->actingAsToken($this->seller([Permission::ProductsView->value, Permission::ProductsCreate->value]));
        $this->postJson('/api/v1/brands', ['name' => 'Mother Dairy'])->assertCreated();
        $this->postJson('/api/v1/brands', ['name' => 'Amul'])->assertJsonValidationErrors('name');
    }

    public function test_units_admin_managed_and_in_use_units_cannot_be_deleted(): void
    {
        $product = Product::factory()->create();
        $this->actingAsToken($this->admin());

        $this->getJson('/api/v1/units?active=1')->assertOk();
        $unit = $this->postJson('/api/v1/admin/units', ['name' => 'Tray', 'short_name' => 'tray', 'allows_decimal' => false])
            ->assertCreated()->json('data');
        $this->deleteJson("/api/v1/admin/units/{$unit['id']}")->assertNoContent();
        $this->deleteJson("/api/v1/admin/units/{$product->unit_id}")->assertStatus(409)->assertJsonPath('code', 'IN_USE');

        $this->actingAsToken($this->seller(Permission::values()));
        $this->postJson('/api/v1/admin/units', ['name' => 'X', 'short_name' => 'x', 'allows_decimal' => true])->assertForbidden();
    }
}
