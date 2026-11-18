<?php

namespace App\Http\Requests\Auth;

use App\Rules\UserRules;
use Illuminate\Foundation\Http\FormRequest;

/** Email is changed only by the admin (it's the login identity). */
class UpdateProfileRequest extends FormRequest
{
    public function rules(): array
    {
        return [
            'name' => ['sometimes', 'required', ...UserRules::name()],
            'phone' => ['sometimes', ...UserRules::phone()],
            'locale' => ['sometimes', 'required', ...UserRules::locale()],
        ];
    }
}
