<?php

namespace App\Rules;

use App\Constants\AppConstants;
use Illuminate\Validation\Rule;
use Illuminate\Validation\Rules\Password;

/** Field rules shared by every request that accepts user data. */
final class UserRules
{
    public static function name(): array
    {
        return ['string', 'max:120'];
    }

    /** Unique across all users, including deleted ones (their history still references the email). */
    public static function email(?int $ignoreUserId = null): array
    {
        return ['string', 'email', 'max:191', Rule::unique('users', 'email')->ignore($ignoreUserId)];
    }

    public static function phone(): array
    {
        return ['nullable', 'string', 'regex:'.AppConstants::PHONE_REGEX];
    }

    public static function locale(): array
    {
        return ['string', Rule::in(config('kirana.locales'))];
    }

    public static function newPassword(): array
    {
        return ['required', 'string', 'confirmed', Password::defaults()];
    }
}
