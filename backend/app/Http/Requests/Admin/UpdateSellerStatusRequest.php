<?php

namespace App\Http\Requests\Admin;

use Illuminate\Foundation\Http\FormRequest;

class UpdateSellerStatusRequest extends FormRequest
{
    public function rules(): array
    {
        return ['is_active' => ['required', 'boolean']];
    }
}
