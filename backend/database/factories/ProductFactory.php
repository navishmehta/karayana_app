<?php

namespace Database\Factories;

use App\Models\Category;
use App\Models\Product;
use App\Models\Unit;
use Illuminate\Database\Eloquent\Factories\Factory;

/** @extends Factory<Product> */
class ProductFactory extends Factory
{
    public function definition(): array
    {
        return [
            'category_id' => Category::factory(),
            'unit_id' => fn () => Unit::firstOrCreate(['short_name' => 'pcs'], ['name' => 'Piece', 'allows_decimal' => false])->id,
            'name' => ucfirst(fake()->unique()->words(3, true)),
            'sku' => 'T-'.fake()->unique()->numerify('######'),
            'purchase_price' => '40.00',
            'selling_price' => '50.00',
            'mrp' => '55.00',
            'min_stock_level' => 5,
        ];
    }
}
