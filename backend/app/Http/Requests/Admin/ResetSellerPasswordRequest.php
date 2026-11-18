<?php

namespace App\Http\Requests\Admin;

use App\Rules\UserRules;
use Illuminate\Foundation\Http\FormRequest;

class ResetSellerPasswordRequest extends FormRequest
{
    public function rules(): array
    {
        return ['password' => UserRules::newPassword()];
    }
}
