<?php

namespace Database\Seeders;

use App\Constants\AppConstants;
use App\Models\Store;
use Illuminate\Database\Seeder;

class StoreSeeder extends Seeder
{
    public function run(): void
    {
        Store::firstOrCreate(['slug' => AppConstants::DEFAULT_STORE_SLUG], [
            'name' => config('app.name'),
            'timezone' => config('kirana.timezone'),
            'currency' => config('kirana.currency'),
        ]);
    }
}
