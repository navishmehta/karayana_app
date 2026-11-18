<?php

namespace App\Support;

use App\Constants\AppConstants;

/**
 * Exact decimal arithmetic for rupee amounts (bcmath on strings, never floats).
 * All results are strings with MONEY_DECIMALS places, rounded half-up.
 */
final class Money
{
    private const WORK_SCALE = 6;

    public static function sub(string $a, string $b): string
    {
        return self::round(bcsub($a, $b, self::WORK_SCALE));
    }

    /** ($part / $whole) × 100, or null when $whole is zero. */
    public static function percentOf(string $part, string $whole): ?string
    {
        if (bccomp($whole, '0', self::WORK_SCALE) === 0) {
            return null;
        }

        return self::round(bcmul(bcdiv($part, $whole, self::WORK_SCALE), '100', self::WORK_SCALE));
    }

    public static function round(string $value, int $scale = AppConstants::MONEY_DECIMALS): string
    {
        $offset = '0.'.str_repeat('0', $scale).'5';

        return bcadd($value, str_starts_with($value, '-') ? '-'.$offset : $offset, $scale);
    }

    public static function compare(string $a, string $b): int
    {
        return bccomp($a, $b, self::WORK_SCALE);
    }
}
