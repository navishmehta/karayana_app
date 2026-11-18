<?php

namespace App\Http\Requests\Staff;

use App\Models\Brand;
use App\Rules\CatalogueRules;
use Illuminate\Foundation\Http\FormRequest;

class BrandRequest extends FormRequest
{
    public function rules(): array
    {
        $brand = $this->route('brand');
        $creating = ! $brand instanceof Brand;

        return [
            'name' => [$creating ? 'required' : 'sometimes', 'string', 'max:120', CatalogueRules::uniqueActiveName('brands', $brand?->id)],
            'is_active' => ['sometimes', 'boolean'],
        ];
    }
}
