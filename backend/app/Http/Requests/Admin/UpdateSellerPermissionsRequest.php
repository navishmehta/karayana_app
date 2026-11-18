<?php

namespace App\Http\Requests\Admin;

use App\Rules\PermissionSet;
use Illuminate\Foundation\Http\FormRequest;

class UpdateSellerPermissionsRequest extends FormRequest
{
    public function rules(): array
    {
        return PermissionSet::rules();
    }
}
