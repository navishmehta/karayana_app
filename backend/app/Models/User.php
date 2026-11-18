<?php

namespace App\Models;

use App\Enums\Permission;
use App\Enums\Role;
use Database\Factories\UserFactory;
use Illuminate\Contracts\Translation\HasLocalePreference;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\Casts\Attribute;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Database\Eloquent\SoftDeletes;
use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;
use Illuminate\Support\Str;
use Laravel\Sanctum\HasApiTokens;
use Spatie\Permission\Traits\HasRoles;

class User extends Authenticatable implements HasLocalePreference
{
    /** @use HasFactory<UserFactory> */
    use HasApiTokens, HasFactory, HasRoles, Notifiable, SoftDeletes;

    protected $fillable = ['store_id', 'name', 'email', 'phone', 'password', 'locale', 'is_active', 'created_by'];

    protected $hidden = ['password', 'remember_token'];

    protected function casts(): array
    {
        return [
            'email_verified_at' => 'datetime',
            'last_login_at' => 'datetime',
            'is_active' => 'boolean',
            'password' => 'hashed',
        ];
    }

    /** Emails are stored lowercase so login is case-insensitive. */
    protected function email(): Attribute
    {
        return Attribute::set(fn (string $value) => Str::lower(trim($value)));
    }

    public function store(): BelongsTo
    {
        return $this->belongsTo(Store::class);
    }

    public function deviceTokens(): HasMany
    {
        return $this->hasMany(DeviceToken::class);
    }

    public function scopeSellers(Builder $query): void
    {
        $query->role(Role::Seller->value);
    }

    public function isAdmin(): bool
    {
        return $this->hasRole(Role::Admin->value);
    }

    public function roleName(): ?string
    {
        return $this->isAdmin() ? Role::Admin->value : ($this->hasRole(Role::Seller->value) ? Role::Seller->value : null);
    }

    /** Effective permission keys. Admin implicitly has all of them. @return list<string> */
    public function permissionKeys(): array
    {
        return $this->isAdmin()
            ? Permission::values()
            : $this->getAllPermissions()->pluck('name')->sort()->values()->all();
    }

    /** Signs the user out everywhere: API tokens and push registrations. */
    public function revokeAllSessions(): void
    {
        $this->tokens()->delete();
        $this->deviceTokens()->delete();
    }

    /** Used by Laravel for mails and notifications sent to this user. */
    public function preferredLocale(): string
    {
        return $this->locale;
    }
}
