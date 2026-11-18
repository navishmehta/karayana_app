<?php

namespace Tests\Feature\Catalogue;

use App\Enums\ActivityAction;
use App\Enums\Permission;
use App\Models\Category;
use App\Models\Product;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Storage;
use Tests\ApiTestCase;

class CategoryTest extends ApiTestCase
{
    protected function setUp(): void
    {
        parent::setUp();
        Storage::fake(config('kirana.media.disk'));
    }

    public function test_admin_creates_category_with_image_and_punjabi_name(): void
    {
        $response = $this->actingAsToken($this->admin())->post('/api/v1/categories', [
            'name' => 'Dairy',
            'name_translations' => ['pa' => 'ਡੇਅਰੀ'],
            'image' => UploadedFile::fake()->image('dairy.jpg', 2000, 1500),
        ])->assertCreated()
            ->assertJsonPath('data.slug', 'dairy')
            ->assertJsonPath('data.name_translations.pa', 'ਡੇਅਰੀ');

        $category = Category::first();
        Storage::disk(config('kirana.media.disk'))->assertExists([$category->image_path, $category->image_thumb_path]);
        $this->assertStringEndsWith('.webp', $category->image_path);
        $this->assertNotNull($response->json('data.image_url'));
        $this->assertDatabaseHas('activity_log', ['event' => ActivityAction::CategoryCreated->value]);
    }

    public function test_duplicate_name_and_unknown_translation_locale_are_rejected(): void
    {
        Category::factory()->create(['name' => 'Snacks']);

        $this->actingAsToken($this->admin())
            ->postJson('/api/v1/categories', ['name' => 'Snacks', 'name_translations' => ['fr' => 'Collations']])
            ->assertJsonValidationErrors(['name', 'name_translations']);
    }

    public function test_slug_stays_unique_and_stable(): void
    {
        $admin = $this->admin();
        $first = $this->actingAsToken($admin)->postJson('/api/v1/categories', ['name' => 'Cold Drinks'])->json('data');
        $this->deleteJson("/api/v1/categories/{$first['id']}")->assertNoContent();

        $this->postJson('/api/v1/categories', ['name' => 'Cold Drinks'])->assertJsonPath('data.slug', 'cold-drinks-2');
        $this->patchJson("/api/v1/categories/{$first['id']}", ['name' => 'x'])->assertNotFound(); // deleted
    }

    public function test_list_search_filter_sort_and_counts(): void
    {
        $dairy = Category::factory()->create(['name' => 'Dairy', 'sort_order' => 2]);
        Category::factory()->create(['name' => 'Bakery', 'sort_order' => 1, 'is_active' => false]);
        Product::factory()->count(2)->create(['category_id' => $dairy->id]);

        $this->actingAsToken($this->seller([Permission::CategoriesView->value]));

        $this->getJson('/api/v1/categories')->assertOk()->assertJsonPath('data.0.name', 'Bakery');
        $this->getJson('/api/v1/categories?sort=name_desc')->assertJsonPath('data.0.name', 'Dairy');
        $this->getJson('/api/v1/categories?search=dai')->assertJsonCount(1, 'data')->assertJsonPath('data.0.products_count', 2);
        $this->getJson('/api/v1/categories?status=inactive')->assertJsonCount(1, 'data');
    }

    public function test_category_with_products_cannot_be_deleted(): void
    {
        $category = Category::factory()->create();
        Product::factory()->create(['category_id' => $category->id]);

        $this->actingAsToken($this->admin())->deleteJson("/api/v1/categories/{$category->id}")
            ->assertStatus(409)->assertJsonPath('code', 'CATEGORY_NOT_EMPTY');
    }

    public function test_reorder_and_image_replace_and_remove(): void
    {
        [$a, $b] = Category::factory()->count(2)->create();
        $this->actingAsToken($this->admin());

        $this->patchJson('/api/v1/categories/reorder', ['ids' => [$b->id, $a->id]])->assertNoContent();
        $this->assertSame([0, 1], [$b->fresh()->sort_order, $a->fresh()->sort_order]);

        $this->post("/api/v1/categories/{$a->id}/image", ['image' => UploadedFile::fake()->image('a.png')])->assertOk();
        $oldPath = $a->fresh()->image_path;
        $this->post("/api/v1/categories/{$a->id}/image", ['image' => UploadedFile::fake()->image('b.png')])->assertOk();
        Storage::disk(config('kirana.media.disk'))->assertMissing($oldPath);

        $this->deleteJson("/api/v1/categories/{$a->id}/image")->assertOk()->assertJsonPath('data.image_url', null);
    }

    public function test_non_image_upload_is_rejected(): void
    {
        $this->actingAsToken($this->admin())
            ->post('/api/v1/categories', ['name' => 'X', 'image' => UploadedFile::fake()->create('virus.php', 10, 'application/x-php')])
            ->assertJsonValidationErrors('image');
    }

    public function test_each_action_needs_its_own_permission(): void
    {
        $category = Category::factory()->create();
        $viewer = $this->seller([Permission::CategoriesView->value]);

        $this->actingAsToken($viewer);
        $this->getJson('/api/v1/categories')->assertOk();
        $this->postJson('/api/v1/categories', ['name' => 'New'])->assertForbidden();
        $this->patchJson("/api/v1/categories/{$category->id}", ['name' => 'New'])->assertForbidden();
        $this->deleteJson("/api/v1/categories/{$category->id}")->assertForbidden();

        $this->actingAsToken($this->seller());
        $this->getJson('/api/v1/categories')->assertForbidden();
    }
}
