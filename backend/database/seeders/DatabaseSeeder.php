<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;

class DatabaseSeeder extends Seeder
{
    /** Every seeder is idempotent: safe to run again on an existing database. */
    public function run(): void
    {
        $this->call([
            StoreSeeder::class,
            RolePermissionSeeder::class,
            AdminUserSeeder::class,
            UnitSeeder::class,
            SettingSeeder::class,
            CategorySeeder::class,
        ]);
    }
}
