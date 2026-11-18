<?php

namespace App\Enums;

/** Stable machine-readable error codes returned as `code` in every API error. */
enum ErrorCode: string
{
    case ValidationFailed = 'VALIDATION_FAILED';
    case Unauthenticated = 'UNAUTHENTICATED';
    case InvalidCredentials = 'INVALID_CREDENTIALS';
    case AccountInactive = 'ACCOUNT_INACTIVE';
    case InvalidResetCode = 'INVALID_RESET_CODE';
    case Forbidden = 'FORBIDDEN';
    case NotFound = 'NOT_FOUND';
    case TooManyRequests = 'TOO_MANY_REQUESTS';
    case HttpError = 'HTTP_ERROR';
    case ServerError = 'SERVER_ERROR';

    public function httpStatus(): int
    {
        return match ($this) {
            self::ValidationFailed, self::InvalidResetCode => 422,
            self::Unauthenticated, self::InvalidCredentials => 401,
            self::Forbidden, self::AccountInactive => 403,
            self::NotFound => 404,
            self::TooManyRequests => 429,
            self::HttpError, self::ServerError => 500,
        };
    }

    /** Translated message from lang/{locale}/errors.php. */
    public function message(): string
    {
        return __('errors.'.strtolower($this->value));
    }
}
