<?php

namespace App\Http\Requests\Auth;

use App\Rules\UserRules;
use Illuminate\Foundation\Http\FormRequest;

class ChangePasswordRequest extends FormRequest
{
    public function rules(): array
    {
        return [
            'current_password' => ['required', 'string', 'current_password:sanctum'],
            'password' => [...UserRules::newPassword(), 'different:current_password'],
        ];
    }
}
