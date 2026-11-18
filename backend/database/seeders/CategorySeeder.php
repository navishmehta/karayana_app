<?php

namespace Database\Seeders;

use App\Models\Category;
use App\Models\Store;
use Illuminate\Database\Seeder;
use Illuminate\Support\Str;

/** Starter categories only. They are normal rows the admin can edit or delete. */
class CategorySeeder extends Seeder
{
    public function run(): void
    {
        $store = Store::default();

        $categories = [
            'Grocery' => 'ਕਰਿਆਨਾ',
            'Dairy' => 'ਡੇਅਰੀ',
            'Snacks' => 'ਸਨੈਕਸ',
            'Cold Drinks' => 'ਠੰਢੇ ਪੀਣ ਵਾਲੇ',
            'Personal Care' => 'ਨਿੱਜੀ ਦੇਖਭਾਲ',
            'Household' => 'ਘਰੇਲੂ ਸਾਮਾਨ',
            'Bakery' => 'ਬੇਕਰੀ',
            'Spices' => 'ਮਸਾਲੇ',
            'Cleaning Products' => 'ਸਫ਼ਾਈ ਦਾ ਸਾਮਾਨ',
            'Stationery' => 'ਸਟੇਸ਼ਨਰੀ',
        ];

        $order = 0;
        foreach ($categories as $name => $pa) {
            Category::withTrashed()->firstOrCreate(
                ['store_id' => $store->id, 'slug' => Str::slug($name)],
                ['name' => $name, 'name_translations' => ['pa' => $pa], 'sort_order' => $order++],
            );
        }
    }
}
