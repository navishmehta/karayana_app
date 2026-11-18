<?php

namespace App\Http\Requests\Staff;

use App\Rules\CatalogueRules;
use Illuminate\Foundation\Http\FormRequest;

class ReorderCategoriesRequest extends FormRequest
{
    public function rules(): array
    {
        return [
            'ids' => ['required', 'array', 'min:1'],
            'ids.*' => ['integer', 'distinct', CatalogueRules::existsInStore('categories')],
        ];
    }
}
