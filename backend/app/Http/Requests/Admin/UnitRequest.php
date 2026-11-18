<?php

namespace App\Http\Requests\Admin;

use App\Models\Unit;
use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;

class UnitRequest extends FormRequest
{
    public function rules(): array
    {
        $unit = $this->route('unit');
        $creating = ! $unit instanceof Unit;
        $required = $creating ? 'required' : 'sometimes';

        return [
            'name' => [$required, 'string', 'max:50'],
            'short_name' => [$required, 'string', 'max:10', Rule::unique('units', 'short_name')->ignore($unit?->id)],
            'allows_decimal' => [$creating ? 'required' : 'sometimes', 'boolean'],
            'is_active' => ['sometimes', 'boolean'],
        ];
    }
}
