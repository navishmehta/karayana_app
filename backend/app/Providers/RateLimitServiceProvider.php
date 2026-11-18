<?php

namespace App\Providers;

use App\Enums\RateLimit;
use Illuminate\Cache\RateLimiting\Limit;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\RateLimiter;
use Illuminate\Support\ServiceProvider;
use Illuminate\Support\Str;

/** Registers the named limiters from App\Enums\RateLimit using limits from config/kirana.php. */
class RateLimitServiceProvider extends ServiceProvider
{
    public function boot(): void
    {
        $limits = config('kirana.rate_limits');

        RateLimiter::for(RateLimit::Login->value, fn (Request $request) => Limit::perMinute($limits['login'])
            ->by($this->emailAndIp($request)));

        RateLimiter::for(RateLimit::PasswordReset->value, fn (Request $request) => Limit::perMinute($limits['password_reset'])
            ->by($this->emailAndIp($request)));

        RateLimiter::for(RateLimit::Api->value, fn (Request $request) => Limit::perMinute($limits['api'])
            ->by($request->user()?->id ?: $request->ip()));

        RateLimiter::for(RateLimit::Public->value, fn (Request $request) => Limit::perMinute($limits['public'])
            ->by($request->ip()));
    }

    private function emailAndIp(Request $request): string
    {
        return Str::lower((string) $request->input('email')).'|'.$request->ip();
    }
}
