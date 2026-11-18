<?php

namespace App\Http\Requests\Staff;

use App\Rules\CatalogueRules;
use Illuminate\Foundation\Http\FormRequest;

class ImageUploadRequest extends FormRequest
{
    public function rules(): array
    {
        return ['image' => ['required', ...CatalogueRules::image()]];
    }
}
