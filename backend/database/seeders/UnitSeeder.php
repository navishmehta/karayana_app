<?php

namespace Database\Seeders;

use App\Models\Unit;
use Illuminate\Database\Seeder;

class UnitSeeder extends Seeder
{
    public function run(): void
    {
        $units = [
            ['Piece', 'pcs', false],
            ['Kilogram', 'kg', true],
            ['Gram', 'g', true],
            ['Litre', 'L', true],
            ['Millilitre', 'ml', true],
            ['Packet', 'pkt', false],
            ['Box', 'box', false],
            ['Dozen', 'dozen', false],
            ['Bottle', 'btl', false],
        ];

        foreach ($units as [$name, $short, $decimal]) {
            Unit::firstOrCreate(['short_name' => $short], ['name' => $name, 'allows_decimal' => $decimal]);
        }
    }
}
