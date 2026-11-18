<?php

namespace Database\Factories;

use App\Constants\AppConstants;
use App\Enums\Role;
use App\Models\Store;
use App\Models\User;
use Illuminate\Database\Eloquent\Factories\Factory;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Str;

/**
 * @extends Factory<User>
 */
class UserFactory extends Factory
{
    protected static ?string $password;

    public function definition(): array
    {
        return [
            'store_id' => fn () => Store::query()->value('id') ?? Store::create(['name' => 'Test Store', 'slug' => AppConstants::DEFAULT_STORE_SLUG])->id,
            'name' => fake()->name(),
            'email' => fake()->unique()->safeEmail(),
            'email_verified_at' => now(),
            'password' => static::$password ??= Hash::make('password'),
            'locale' => 'en',
            'is_active' => true,
            'remember_token' => Str::random(10),
        ];
    }

    public function admin(): static
    {
        return $this->afterCreating(fn (User $user) => $user->assignRole(Role::Admin->value));
    }

    public function seller(array $permissions = []): static
    {
        return $this->afterCreating(function (User $user) use ($permissions) {
            $user->assignRole(Role::Seller->value);
            $user->givePermissionTo($permissions);
        });
    }

    public function inactive(): static
    {
        return $this->state(fn () => ['is_active' => false]);
    }
}
