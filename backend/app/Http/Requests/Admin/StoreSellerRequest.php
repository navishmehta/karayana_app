<?php

namespace App\Http\Requests\Admin;

use App\Rules\PermissionSet;
use App\Rules\UserRules;
use Illuminate\Foundation\Http\FormRequest;

class StoreSellerRequest extends FormRequest
{
    public function rules(): array
    {
        return [
            'name' => ['required', ...UserRules::name()],
            'email' => ['required', ...UserRules::email()],
            'phone' => UserRules::phone(),
            'locale' => ['sometimes', ...UserRules::locale()],
            'password' => UserRules::newPassword(),
            ...PermissionSet::rules(),
        ];
    }
}
