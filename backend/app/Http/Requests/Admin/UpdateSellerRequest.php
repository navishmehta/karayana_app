<?php

namespace App\Http\Requests\Admin;

use App\Rules\UserRules;
use Illuminate\Foundation\Http\FormRequest;

class UpdateSellerRequest extends FormRequest
{
    public function rules(): array
    {
        return [
            'name' => ['sometimes', 'required', ...UserRules::name()],
            'email' => ['sometimes', 'required', ...UserRules::email($this->route('seller')->id)],
            'phone' => ['sometimes', ...UserRules::phone()],
            'locale' => ['sometimes', 'required', ...UserRules::locale()],
        ];
    }
}
