<?php

namespace App\Http\Requests\Staff;

use Illuminate\Foundation\Http\FormRequest;

class UpdateProductImageRequest extends FormRequest
{
    public function rules(): array
    {
        return [
            'is_primary' => ['sometimes', 'accepted'], // only "make primary"; unsetting happens automatically
            'sort_order' => ['sometimes', 'integer', 'min:0'],
        ];
    }
}
