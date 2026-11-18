<?php

namespace Tests\Feature\Catalogue;

use App\Enums\Permission;
use App\Models\Product;
use App\Models\ProductImage;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Storage;
use Tests\ApiTestCase;

class ProductImageTest extends ApiTestCase
{
    private Product $product;

    protected function setUp(): void
    {
        parent::setUp();
        Storage::fake(config('kirana.media.disk'));
        $this->product = Product::factory()->create();
    }

    private function upload(?Product $product = null)
    {
        $id = ($product ?? $this->product)->id;

        return $this->post("/api/v1/products/{$id}/images", ['image' => UploadedFile::fake()->image('p.jpg', 1600, 1600)]);
    }

    public function test_first_image_is_primary_and_files_are_webp_resized(): void
    {
        $this->actingAsToken($this->admin());
        $this->upload()->assertCreated()->assertJsonPath('data.is_primary', true);
        $this->upload()->assertCreated()->assertJsonPath('data.is_primary', false);

        $image = ProductImage::first();
        $disk = Storage::disk(config('kirana.media.disk'));
        [$width] = getimagesizefromstring($disk->get($image->path));
        [$thumbWidth] = getimagesizefromstring($disk->get($image->thumb_path));

        $this->assertSame(config('kirana.media.full_width'), $width);
        $this->assertSame(config('kirana.media.thumb_width'), $thumbWidth);
        $this->assertSame('image/webp', $disk->mimeType($image->path));
    }

    public function test_image_limit_is_enforced(): void
    {
        $this->actingAsToken($this->admin());
        foreach (range(1, config('kirana.media.max_images_per_product')) as $_) {
            $this->upload()->assertCreated();
        }

        $this->upload()->assertUnprocessable()->assertJsonPath('code', 'IMAGE_LIMIT_REACHED');
    }

    public function test_set_primary_and_delete_promotes_next_image(): void
    {
        $this->actingAsToken($this->admin());
        $first = $this->upload()->json('data.id');
        $second = $this->upload()->json('data.id');

        $this->patchJson("/api/v1/products/{$this->product->id}/images/{$second}", ['is_primary' => true])
            ->assertOk()->assertJsonPath('data.0.id', $second);
        $this->assertFalse(ProductImage::find($first)->is_primary);

        $this->deleteJson("/api/v1/products/{$this->product->id}/images/{$second}")->assertNoContent();
        $this->assertTrue(ProductImage::find($first)->is_primary);
    }

    public function test_image_of_another_product_cannot_be_touched_through_this_product(): void
    {
        $other = Product::factory()->create();
        $this->actingAsToken($this->admin());
        $foreignImage = $this->upload($other)->json('data.id');

        $this->deleteJson("/api/v1/products/{$this->product->id}/images/{$foreignImage}")->assertNotFound();
    }

    public function test_corrupt_image_is_rejected(): void
    {
        $fake = UploadedFile::fake()->createWithContent('fake.jpg', 'not really an image');

        $this->actingAsToken($this->admin())
            ->post("/api/v1/products/{$this->product->id}/images", ['image' => $fake])
            ->assertUnprocessable();
    }

    public function test_upload_needs_product_update_permission(): void
    {
        $this->actingAsToken($this->seller([Permission::ProductsView->value]));
        $this->upload()->assertForbidden();
    }
}
