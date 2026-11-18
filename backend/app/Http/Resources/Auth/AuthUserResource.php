<?php

namespace App\Http\Resources\Auth;

use App\Models\User;
use App\Support\StoreClock;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

/**
 * The logged-in user. `permissions` drives which screens the app shows;
 * the server still checks every request on its own.
 *
 * @mixin User
 */
class AuthUserResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'name' => $this->name,
            'email' => $this->email,
            'phone' => $this->phone,
            'locale' => $this->locale,
            'role' => $this->roleName(),
            'permissions' => $this->permissionKeys(),
            'last_login_at' => StoreClock::toApi($this->last_login_at),
        ];
    }
}
