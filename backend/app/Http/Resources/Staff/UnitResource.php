<?php

namespace App\Http\Resources\Staff;

use App\Models\Unit;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

/** @mixin Unit */
class UnitResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'name' => $this->name,
            'short_name' => $this->short_name,
            'allows_decimal' => $this->allows_decimal,
            'is_active' => $this->is_active,
        ];
    }
}
