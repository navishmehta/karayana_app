<?php

namespace App\Http\Resources\Staff;

use App\Models\Category;
use App\Services\Media\ImageService;
use App\Support\StoreClock;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

/** @mixin Category */
class CategoryResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        $images = app(ImageService::class);

        return [
            'id' => $this->id,
            'name' => $this->name,
            'name_translations' => (object) ($this->name_translations ?? []),
            'slug' => $this->slug,
            'description' => $this->description,
            'image_url' => $images->url($this->image_path),
            'image_thumb_url' => $images->url($this->image_thumb_path),
            'sort_order' => $this->sort_order,
            'is_active' => $this->is_active,
            'products_count' => $this->whenCounted('products'),
            'created_at' => StoreClock::toApi($this->created_at),
            'updated_at' => StoreClock::toApi($this->updated_at),
        ];
    }
}
