<?php

namespace App\Http\Resources\Staff;

use App\Models\ProductImage;
use App\Services\Media\ImageService;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

/** @mixin ProductImage */
class ProductImageResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        $images = app(ImageService::class);

        return [
            'id' => $this->id,
            'url' => $images->url($this->path),
            'thumb_url' => $images->url($this->thumb_path),
            'is_primary' => $this->is_primary,
            'sort_order' => $this->sort_order,
        ];
    }
}
