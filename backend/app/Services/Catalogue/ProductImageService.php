<?php

namespace App\Services\Catalogue;

use App\Enums\ActivityAction;
use App\Enums\ErrorCode;
use App\Enums\MediaFolder;
use App\Exceptions\ApiException;
use App\Models\Product;
use App\Models\ProductImage;
use App\Services\Audit\AuditLogger;
use App\Services\Media\ImageService;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\DB;

/** A product has up to N images (config kirana.media.max_images_per_product) and exactly one primary. */
class ProductImageService
{
    public function __construct(
        private readonly AuditLogger $audit,
        private readonly ImageService $images,
    ) {}

    public function add(Product $product, UploadedFile $file): ProductImage
    {
        if ($product->images()->count() >= config('kirana.media.max_images_per_product')) {
            throw new ApiException(ErrorCode::ImageLimitReached);
        }

        $stored = $this->images->store($file, MediaFolder::Products);

        $image = $product->images()->create([
            'path' => $stored->path,
            'thumb_path' => $stored->thumbPath,
            'is_primary' => ! $product->images()->exists(),
            'sort_order' => (int) $product->images()->max('sort_order') + 1,
        ]);

        $this->audit->record(ActivityAction::ProductImageAdded, $product, ['image_id' => $image->id]);

        return $image;
    }

    public function update(ProductImage $image, array $data): ProductImage
    {
        DB::transaction(function () use ($image, $data) {
            if ($data['is_primary'] ?? false) {
                ProductImage::where('product_id', $image->product_id)->whereKeyNot($image->id)->update(['is_primary' => false]);
            }
            $image->update($data);
        });

        return $image;
    }

    /** Deleting the primary image promotes the next one. */
    public function delete(ProductImage $image): void
    {
        DB::transaction(function () use ($image) {
            $image->delete();

            if ($image->is_primary) {
                ProductImage::where('product_id', $image->product_id)->orderBy('sort_order')->first()?->update(['is_primary' => true]);
            }
        });

        $this->images->delete($image->path, $image->thumb_path);
        $this->audit->record(ActivityAction::ProductImageRemoved, $image->product, ['image_id' => $image->id]);
    }
}
