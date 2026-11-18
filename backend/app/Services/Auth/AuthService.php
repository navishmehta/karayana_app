<?php

namespace App\Services\Auth;

use App\Enums\ActivityAction;
use App\Enums\ErrorCode;
use App\Exceptions\ApiException;
use App\Models\User;
use App\Services\Audit\AuditLogger;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Str;
use Laravel\Sanctum\NewAccessToken;

class AuthService
{
    public function __construct(private readonly AuditLogger $audit) {}

    /** Verifies credentials and issues a device token that expires after kirana.auth.token_ttl_days. */
    public function login(string $email, string $password, string $deviceName): NewAccessToken
    {
        $user = User::where('email', Str::lower(trim($email)))->first();

        if (! $user || ! Hash::check($password, $user->password)) {
            $this->audit->record(ActivityAction::LoginFailed, properties: ['email' => $email]);

            throw new ApiException(ErrorCode::InvalidCredentials);
        }

        if (! $user->is_active) {
            throw new ApiException(ErrorCode::AccountInactive);
        }

        $token = $user->createToken($deviceName, ['*'], now()->addDays(config('kirana.auth.token_ttl_days')));
        $user->forceFill(['last_login_at' => now()])->save();

        $this->audit->record(ActivityAction::Login, $user, ['device' => $deviceName], $user);

        return $token;
    }

    public function logout(User $user): void
    {
        $user->currentAccessToken()?->delete();
        $this->audit->record(ActivityAction::Logout, $user);
    }

    public function logoutAll(User $user): void
    {
        $user->revokeAllSessions();
        $this->audit->record(ActivityAction::LogoutAll, $user);
    }

    public function updateProfile(User $user, array $data): User
    {
        $user->fill($data);
        $changes = $user->getDirty();
        $user->save();

        if ($changes) {
            $this->audit->record(ActivityAction::ProfileUpdated, $user, ['changed' => array_keys($changes)]);
        }

        return $user;
    }

    /** Changes the password and signs out every other device. */
    public function changePassword(User $user, string $newPassword): void
    {
        DB::transaction(function () use ($user, $newPassword) {
            $user->update(['password' => $newPassword]);
            $user->tokens()->whereKeyNot($user->currentAccessToken()?->getKey())->delete();
        });

        $this->audit->record(ActivityAction::PasswordChanged, $user);
    }
}
