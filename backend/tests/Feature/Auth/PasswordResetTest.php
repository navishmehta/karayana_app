<?php

namespace Tests\Feature\Auth;

use App\Models\User;
use App\Notifications\PasswordResetCodeNotification;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Facades\Notification;
use Tests\ApiTestCase;

class PasswordResetTest extends ApiTestCase
{
    public function test_full_reset_flow_with_emailed_code(): void
    {
        Notification::fake();
        $user = User::factory()->seller()->create(['email' => 'seller@example.com']);
        $user->createToken('phone');

        $this->postJson('/api/v1/auth/forgot-password', ['email' => 'seller@example.com'])->assertOk();

        $code = null;
        Notification::assertSentTo($user, PasswordResetCodeNotification::class, function ($n) use (&$code, $user) {
            $code = (fn () => $this->code)->call($n);

            return str_contains($n->toMail($user)->render(), $code);
        });

        $this->postJson('/api/v1/auth/reset-password', [
            'email' => 'seller@example.com',
            'code' => $code,
            'password' => 'BrandNew123',
            'password_confirmation' => 'BrandNew123',
        ])->assertOk();

        $this->assertTrue(Hash::check('BrandNew123', $user->fresh()->password));
        $this->assertSame(0, $user->tokens()->count());
        $this->assertDatabaseMissing('password_reset_tokens', ['email' => 'seller@example.com']);
    }

    public function test_unknown_email_gets_same_response_and_no_mail(): void
    {
        Notification::fake();

        $this->postJson('/api/v1/auth/forgot-password', ['email' => 'nobody@example.com'])
            ->assertOk()
            ->assertJsonPath('message', __('messages.reset_code_sent'));

        Notification::assertNothingSent();
    }

    public function test_wrong_or_expired_code_is_rejected(): void
    {
        User::factory()->seller()->create(['email' => 'seller@example.com']);
        DB::table('password_reset_tokens')->insert([
            'email' => 'seller@example.com',
            'token' => Hash::make('123456'),
            'created_at' => now(),
        ]);
        $payload = ['email' => 'seller@example.com', 'password' => 'BrandNew123', 'password_confirmation' => 'BrandNew123'];

        $this->postJson('/api/v1/auth/reset-password', $payload + ['code' => '654321'])
            ->assertUnprocessable()->assertJsonPath('code', 'INVALID_RESET_CODE');

        $this->travel(config('kirana.auth.reset_code_ttl_minutes') + 1)->minutes();

        $this->postJson('/api/v1/auth/reset-password', $payload + ['code' => '123456'])
            ->assertUnprocessable()->assertJsonPath('code', 'INVALID_RESET_CODE');
    }
}
