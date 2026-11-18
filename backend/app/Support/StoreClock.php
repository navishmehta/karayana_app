<?php

namespace App\Support;

use App\Constants\AppConstants;
use Carbon\CarbonImmutable;
use DateTimeInterface;

/**
 * Store-local time helpers. DB timestamps stay in UTC; anything about "today"
 * (expiry buckets, daily reports) must use the store's timezone (Asia/Kolkata).
 */
final class StoreClock
{
    public static function timezone(): string
    {
        return config('kirana.timezone');
    }

    public static function now(): CarbonImmutable
    {
        return CarbonImmutable::now(self::timezone());
    }

    public static function today(): CarbonImmutable
    {
        return CarbonImmutable::today(self::timezone());
    }

    /** ISO-8601 with +05:30 offset, for API responses. */
    public static function toApi(?DateTimeInterface $value): ?string
    {
        return $value ? CarbonImmutable::instance($value)->setTimezone(self::timezone())->toIso8601String() : null;
    }

    /** YYYY-MM-DD, for date-only API fields such as expiry dates. */
    public static function toApiDate(?DateTimeInterface $value): ?string
    {
        return $value?->format(AppConstants::API_DATE_FORMAT);
    }

    /** DD-MM-YYYY, for exports and push notification text. */
    public static function toDisplayDate(?DateTimeInterface $value): ?string
    {
        return $value?->format(AppConstants::DISPLAY_DATE_FORMAT);
    }
}
