<?php

namespace Tests;

use App\Models\User;
use Database\Seeders\RolePermissionSeeder;
use Database\Seeders\StoreSeeder;
use Illuminate\Foundation\Testing\RefreshDatabase;

/** Base for API feature tests: fresh DB with store, roles and permissions seeded. */
abstract class ApiTestCase extends TestCase
{
    use RefreshDatabase;

    protected function afterRefreshingDatabase(): void
    {
        $this->seed([StoreSeeder::class, RolePermissionSeeder::class]);
    }

    /** Authenticate with a real Sanctum token (like the app does). */
    protected function actingAsToken(User $user): static
    {
        $this->app['auth']->forgetGuards(); // don't reuse the previous request's user

        return $this->withToken($user->createToken('test')->plainTextToken);
    }

    protected function admin(): User
    {
        return User::factory()->admin()->create();
    }

    protected function seller(array $permissions = []): User
    {
        return User::factory()->seller($permissions)->create();
    }
}
