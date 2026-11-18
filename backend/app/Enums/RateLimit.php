<?php

namespace App\Enums;

/** Named rate limiters. Limits are set in config/kirana.php → rate_limits. */
enum RateLimit: string
{
    case Login = 'login';
    case PasswordReset = 'password-reset';
    case Api = 'api';
    case Public = 'public';

    /** Middleware string, e.g. 'throttle:login'. */
    public function middleware(): string
    {
        return 'throttle:'.$this->value;
    }
}
