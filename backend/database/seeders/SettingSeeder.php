<?php

namespace Database\Seeders;

use App\Enums\SettingKey;
use App\Models\AppSetting;
use App\Models\Store;
use Illuminate\Database\Seeder;

/** Defaults come from App\Enums\SettingKey. Existing values are never overwritten. */
class SettingSeeder extends Seeder
{
    public function run(): void
    {
        $storeId = Store::default()->id;

        foreach (SettingKey::cases() as $setting) {
            AppSetting::firstOrCreate(
                ['store_id' => $storeId, 'key' => $setting->value],
                ['value' => $setting->default(), 'is_public' => $setting->isPublic()],
            );
        }
    }
}
