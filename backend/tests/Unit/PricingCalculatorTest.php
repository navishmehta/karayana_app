<?php

namespace Tests\Unit;

use App\Models\Product;
use App\Services\Catalogue\PricingCalculator;
use App\Support\Money;
use App\Support\StoreClock;
use PHPUnit\Framework\Attributes\DataProvider;
use Tests\TestCase;

class PricingCalculatorTest extends TestCase
{
    private function product(array $attributes): Product
    {
        return (new Product)->forceFill($attributes + ['selling_price' => '50.00', 'mrp' => '60.00', 'purchase_price' => '40.00']);
    }

    public function test_profit_shows_amount_markup_margin_and_inputs(): void
    {
        $this->assertSame([
            'price_used' => '50.00',
            'purchase_price' => '40.00',
            'amount' => '10.00',
            'markup_percent' => '25.00',
            'margin_percent' => '20.00',
        ], (new PricingCalculator)->profit($this->product([])));
    }

    public function test_profit_is_null_without_purchase_price(): void
    {
        $this->assertNull((new PricingCalculator)->profit($this->product(['purchase_price' => null])));
    }

    public function test_active_offer_is_used_for_price_discount_and_profit(): void
    {
        $today = StoreClock::today()->toDateString();
        $product = $this->product(['offer_price' => '45.00', 'offer_starts_at' => $today, 'offer_ends_at' => $today]);
        $calc = new PricingCalculator;

        $this->assertTrue($calc->isOfferActive($product));
        $this->assertSame('45.00', $calc->effectivePrice($product));
        $this->assertSame('25.00', $calc->discountPercent($product)); // 15 off 60
        $this->assertSame('5.00', $calc->profit($product)['amount']);
    }

    public function test_expired_or_future_offer_is_ignored(): void
    {
        $calc = new PricingCalculator;
        $yesterday = StoreClock::today()->subDay()->toDateString();
        $tomorrow = StoreClock::today()->addDay()->toDateString();

        $this->assertSame('50.00', $calc->effectivePrice($this->product(['offer_price' => '45.00', 'offer_ends_at' => $yesterday])));
        $this->assertSame('50.00', $calc->effectivePrice($this->product(['offer_price' => '45.00', 'offer_starts_at' => $tomorrow])));
    }

    public function test_no_discount_without_mrp_or_when_price_equals_mrp(): void
    {
        $calc = new PricingCalculator;
        $this->assertNull($calc->discountPercent($this->product(['mrp' => null])));
        $this->assertNull($calc->discountPercent($this->product(['mrp' => '50.00'])));
    }

    #[DataProvider('roundingCases')]
    public function test_money_rounds_half_up_without_float_errors(string $value, string $expected): void
    {
        $this->assertSame($expected, Money::round($value));
    }

    public static function roundingCases(): array
    {
        return [['0.125', '0.13'], ['0.124', '0.12'], ['-0.125', '-0.13'], ['33.333333', '33.33'], ['0.1', '0.10']];
    }
}
