<?php

namespace App\Constants;

/**
 * Fixed technical constants used across the codebase.
 *
 * Where values live:
 *  - Changes per environment or by the shop owner → config/kirana.php (reads .env)
 *  - Fixed set of named options (roles, permissions, types) → app/Enums
 *  - Fixed technical numbers/strings → here
 */
final class AppConstants
{
    /** Auth guard that roles and permissions are registered under. */
    public const GUARD = 'web';

    /** Slug of the single store in V1. */
    public const DEFAULT_STORE_SLUG = 'main';

    /** Decimal places: money in rupees and paise, quantity allows loose items (1.250 kg). */
    public const MONEY_DECIMALS = 2;

    public const QUANTITY_DECIMALS = 3;

    /** Ready-made Eloquent casts so models don't repeat 'decimal:N'. */
    public const MONEY_CAST = 'decimal:'.self::MONEY_DECIMALS;

    public const QUANTITY_CAST = 'decimal:'.self::QUANTITY_DECIMALS;

    /** API date formats. The app displays dates as DD-MM-YYYY. */
    public const API_DATE_FORMAT = 'Y-m-d';

    public const DISPLAY_DATE_FORMAT = 'd-m-Y';

    /** List endpoints: default and maximum page size. */
    public const DEFAULT_PER_PAGE = 20;

    public const MAX_PER_PAGE = 100;

    /** Sanctum token type returned on login. */
    public const TOKEN_TYPE = 'Bearer';

    /** Indian mobile number: 10 digits starting 6-9. */
    public const PHONE_REGEX = '/^[6-9]\\d{9}$/';

    private function __construct() {}
}
