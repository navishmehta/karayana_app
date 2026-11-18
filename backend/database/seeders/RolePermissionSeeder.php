<?php

namespace Database\Seeders;

use App\Constants\AppConstants;
use App\Enums\Permission as PermissionEnum;
use App\Enums\Role as RoleEnum;
use Illuminate\Database\Seeder;
use Spatie\Permission\Models\Permission;
use Spatie\Permission\Models\Role;
use Spatie\Permission\PermissionRegistrar;

class RolePermissionSeeder extends Seeder
{
    public function run(): void
    {
        app(PermissionRegistrar::class)->forgetCachedPermissions();

        foreach (PermissionEnum::cases() as $permission) {
            Permission::findOrCreate($permission->value, AppConstants::GUARD);
        }

        // Admin passes every check via Gate::before; seller role carries no permissions of its own.
        foreach (RoleEnum::cases() as $role) {
            Role::findOrCreate($role->value, AppConstants::GUARD);
        }
    }
}
