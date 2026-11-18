<?php

namespace Tests\Feature\Auth;

use App\Enums\ActivityAction;
use App\Enums\Permission;
use App\Models\User;
use Spatie\Activitylog\Models\Activity;
use Tests\ApiTestCase;

class LoginTest extends ApiTestCase
{
    private function login(array $overrides = [])
    {
        return $this->postJson('/api/v1/auth/login', $overrides + [
            'email' => 'seller@example.com',
            'password' => 'password',
            'device_name' => 'Pixel 8',
        ]);
    }

    public function test_seller_logs_in_and_receives_token_role_and_permissions(): void
    {
        User::factory()->seller([Permission::ProductsView->value])->create(['email' => 'seller@example.com']);

        $this->login(['email' => 'SELLER@Example.com'])
            ->assertOk()
            ->assertJsonPath('data.token_type', 'Bearer')
            ->assertJsonPath('data.user.role', 'seller')
            ->assertJsonPath('data.user.permissions', [Permission::ProductsView->value])
            ->assertJsonStructure(['data' => ['token', 'expires_at']]);

        $this->assertDatabaseHas('activity_log', ['event' => ActivityAction::Login->value]);
    }

    public function test_admin_receives_every_permission(): void
    {
        User::factory()->admin()->create(['email' => 'seller@example.com']);

        $this->login()->assertOk()
            ->assertJsonPath('data.user.role', 'admin')
            ->assertJsonCount(count(Permission::cases()), 'data.user.permissions');
    }

    public function test_wrong_password_is_rejected_and_logged(): void
    {
        $this->seller()->update(['email' => 'seller@example.com']);

        $this->login(['password' => 'wrong'])->assertUnauthorized()->assertJsonPath('code', 'INVALID_CREDENTIALS');
        $this->assertSame(1, Activity::where('event', ActivityAction::LoginFailed->value)->count());
    }

    public function test_inactive_user_cannot_log_in(): void
    {
        User::factory()->seller()->inactive()->create(['email' => 'seller@example.com']);

        $this->login()->assertForbidden()->assertJsonPath('code', 'ACCOUNT_INACTIVE');
    }

    public function test_validation_errors_are_translated_to_punjabi(): void
    {
        $this->postJson('/api/v1/auth/login', [], ['Accept-Language' => 'pa'])
            ->assertUnprocessable()
            ->assertJsonPath('code', 'VALIDATION_FAILED')
            ->assertJsonPath('errors.email.0', 'ਈਮੇਲ ਭਰਨਾ ਲਾਜ਼ਮੀ ਹੈ।');
    }

    public function test_login_is_rate_limited(): void
    {
        foreach (range(1, config('kirana.rate_limits.login')) as $_) {
            $this->login(['password' => 'wrong']);
        }

        $this->login()->assertTooManyRequests()->assertJsonPath('code', 'TOO_MANY_REQUESTS');
    }

    public function test_expired_token_is_rejected(): void
    {
        $user = $this->seller();
        $token = $user->createToken('old', ['*'], now()->subMinute())->plainTextToken;

        $this->withToken($token)->getJson('/api/v1/auth/me')->assertUnauthorized()->assertJsonPath('code', 'UNAUTHENTICATED');
    }
}
