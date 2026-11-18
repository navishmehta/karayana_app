<?php

namespace App\Http\Requests\Auth;

use App\Rules\UserRules;
use Illuminate\Foundation\Http\FormRequest;

class ResetPasswordRequest extends FormRequest
{
    public function rules(): array
    {
        return [
            'email' => ['required', 'string', 'email'],
            'code' => ['required', 'digits:'.config('kirana.auth.reset_code_length')],
            'password' => UserRules::newPassword(),
        ];
    }
}
