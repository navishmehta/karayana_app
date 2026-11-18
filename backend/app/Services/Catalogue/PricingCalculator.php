<?php

namespace App\Services\Catalogue;

use App\Models\Product;
use App\Support\Money;
use App\Support\StoreClock;

/**
 * Price maths for a product. Profit is always calculated here, never stored.
 *  - effective price: offer price while the offer is running, otherwise the selling price
 *  - markup %: profit ÷ purchase price (how much was added on top of cost)
 *  - margin %: profit ÷ effective price (share of the sale that is profit)
 */
class PricingCalculator
{
    public function isOfferActive(Product $product): bool
    {
        if ($product->offer_price === null) {
            return false;
        }

        $today = StoreClock::today()->toDateString();

        return ($product->offer_starts_at === null || $product->offer_starts_at->toDateString() <= $today)
            && ($product->offer_ends_at === null || $product->offer_ends_at->toDateString() >= $today);
    }

    public function effectivePrice(Product $product): string
    {
        return $this->isOfferActive($product) ? $product->offer_price : $product->selling_price;
    }

    /** Discount shown to customers: how far the effective price is below MRP. */
    public function discountPercent(Product $product): ?string
    {
        $effective = $this->effectivePrice($product);

        if ($product->mrp === null || Money::compare($product->mrp, $effective) <= 0) {
            return null;
        }

        return Money::percentOf(Money::sub($product->mrp, $effective), $product->mrp);
    }

    /** Full calculation for authorised users, including the inputs used. Null when purchase price is unknown. */
    public function profit(Product $product): ?array
    {
        if ($product->purchase_price === null) {
            return null;
        }

        $price = $this->effectivePrice($product);
        $amount = Money::sub($price, $product->purchase_price);

        return [
            'price_used' => $price,
            'purchase_price' => $product->purchase_price,
            'amount' => $amount,
            'markup_percent' => Money::percentOf($amount, $product->purchase_price),
            'margin_percent' => Money::percentOf($amount, $price),
        ];
    }
}
