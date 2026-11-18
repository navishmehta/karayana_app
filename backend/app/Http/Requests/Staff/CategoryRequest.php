<?php

namespace App\Http\Requests\Staff;

use App\Models\Category;
use App\Rules\CatalogueRules;
use Illuminate\Foundation\Http\FormRequest;

/** Create (POST, may include an image) and update (PATCH) share these rules. */
class CategoryRequest extends FormRequest
{
    public function rules(): array
    {
        $category = $this->route('category');
        $creating = ! $category instanceof Category;

        return [
            'name' => [$creating ? 'required' : 'sometimes', 'string', 'max:120', CatalogueRules::uniqueActiveName('categories', $category?->id)],
            ...CatalogueRules::translations('name_translations', 120),
            'description' => ['sometimes', 'nullable', 'string', 'max:1000'],
            'sort_order' => ['sometimes', 'integer', 'min:0'],
            'is_active' => ['sometimes', 'boolean'],
            'image' => $creating ? ['sometimes', ...CatalogueRules::image()] : ['prohibited'],
        ];
    }
}
