<?php

namespace App\Http\Resources\Admin;

use App\Models\User;
use App\Support\StoreClock;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

/** @mixin User */
class SellerResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'name' => $this->name,
            'email' => $this->email,
            'phone' => $this->phone,
            'locale' => $this->locale,
            'is_active' => $this->is_active,
            'permissions' => $this->permissionKeys(),
            'active_sessions' => $this->whenCounted('tokens'),
            'last_login_at' => StoreClock::toApi($this->last_login_at),
            'created_at' => StoreClock::toApi($this->created_at),
        ];
    }
}
