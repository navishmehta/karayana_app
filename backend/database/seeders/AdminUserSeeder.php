<?php

namespace Database\Seeders;

use App\Enums\Role;
use App\Models\Store;
use App\Models\User;
use Illuminate\Database\Seeder;

/** Creates the first admin from ADMIN_* env values. Credentials are never hard-coded. */
class AdminUserSeeder extends Seeder
{
    public function run(): void
    {
        $email = config('kirana.admin.email');
        $password = config('kirana.admin.password');

        if (! $email || ! $password) {
            $this->command?->warn('ADMIN_EMAIL / ADMIN_PASSWORD not set: admin user not created.');

            return;
        }

        $admin = User::firstOrCreate(['email' => $email], [
            'store_id' => Store::default()->id,
            'name' => config('kirana.admin.name'),
            'password' => $password,
            'email_verified_at' => now(),
        ]);

        $admin->syncRoles([Role::Admin->value]);
    }
}
