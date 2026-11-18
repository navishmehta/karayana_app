<?php

namespace Tests\Feature\Auth;

use Tests\ApiTestCase;

class SessionAndProfileTest extends ApiTestCase
{
    public function test_logout_revokes_only_the_current_token(): void
    {
        $user = $this->seller();
        $current = $user->createToken('phone')->plainTextToken;
        $user->createToken('tablet');

        $this->withToken($current)->postJson('/api/v1/auth/logout')->assertOk();

        $this->assertSame(1, $user->tokens()->count());
    }

    public function test_logout_all_revokes_every_token_and_device(): void
    {
        $user = $this->seller();
        $user->createToken('tablet');
        $user->deviceTokens()->create(['token' => 'fcm-1', 'platform' => 'android']);

        $this->actingAsToken($user)->postJson('/api/v1/auth/logout-all')->assertOk();

        $this->assertSame(0, $user->tokens()->count());
        $this->assertSame(0, $user->deviceTokens()->count());
    }

    public function test_user_updates_own_name_and_language_but_not_email(): void
    {
        $user = $this->seller();

        $this->actingAsToken($user)
            ->patchJson('/api/v1/auth/me', ['name' => 'Raju', 'locale' => 'pa', 'email' => 'hacker@example.com'])
            ->assertOk()
            ->assertJsonPath('data.name', 'Raju')
            ->assertJsonPath('data.locale', 'pa')
            ->assertJsonPath('data.email', $user->email);
    }

    public function test_invalid_locale_and_phone_are_rejected(): void
    {
        $this->actingAsToken($this->seller())
            ->patchJson('/api/v1/auth/me', ['locale' => 'fr', 'phone' => '12345'])
            ->assertJsonValidationErrors(['locale', 'phone']);
    }

    public function test_change_password_requires_current_password_and_signs_out_other_devices(): void
    {
        $user = $this->seller();
        $user->createToken('other-device');

        $this->actingAsToken($user)->putJson('/api/v1/auth/password', [
            'current_password' => 'wrong',
            'password' => 'NewPass123',
            'password_confirmation' => 'NewPass123',
        ])->assertJsonValidationErrors('current_password');

        $this->putJson('/api/v1/auth/password', [
            'current_password' => 'password',
            'password' => 'NewPass123',
            'password_confirmation' => 'NewPass123',
        ])->assertOk();

        $this->assertSame(1, $user->tokens()->count()); // only the current device
    }

    public function test_weak_password_is_rejected(): void
    {
        $this->actingAsToken($this->seller())->putJson('/api/v1/auth/password', [
            'current_password' => 'password',
            'password' => 'short',
            'password_confirmation' => 'short',
        ])->assertJsonValidationErrors('password');
    }

    public function test_device_token_registration_moves_token_to_latest_user(): void
    {
        $first = $this->seller();
        $second = $this->seller();
        $payload = ['token' => 'fcm-shared', 'platform' => 'ios'];

        $this->actingAsToken($first)->postJson('/api/v1/devices', $payload)->assertCreated();
        $this->actingAsToken($second)->postJson('/api/v1/devices', $payload)->assertCreated();

        $this->assertDatabaseHas('device_tokens', ['token' => 'fcm-shared', 'user_id' => $second->id]);
        $this->assertDatabaseCount('device_tokens', 1);
    }

    public function test_deactivated_users_token_stops_working_immediately(): void
    {
        $user = $this->seller();
        $token = $user->createToken('phone')->plainTextToken;
        $user->update(['is_active' => false]);

        $this->withToken($token)->getJson('/api/v1/auth/me')->assertForbidden()->assertJsonPath('code', 'ACCOUNT_INACTIVE');
    }
}
