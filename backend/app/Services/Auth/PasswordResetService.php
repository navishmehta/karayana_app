<?php

namespace App\Services\Auth;

use App\Enums\ActivityAction;
use App\Enums\ErrorCode;
use App\Exceptions\ApiException;
use App\Models\User;
use App\Notifications\PasswordResetCodeNotification;
use App\Services\Audit\AuditLogger;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Str;

/**
 * Mobile-friendly reset: a short numeric code is emailed and typed into the app.
 * Only a hash of the code is stored. Unknown emails get the same response (no account enumeration).
 */
class PasswordResetService
{
    private const TABLE = 'password_reset_tokens';

    public function __construct(private readonly AuditLogger $audit) {}

    public function sendCode(string $email): void
    {
        $user = User::where('email', Str::lower(trim($email)))->where('is_active', true)->first();

        if (! $user) {
            return;
        }

        $code = $this->generateCode();

        DB::table(self::TABLE)->updateOrInsert(
            ['email' => $user->email],
            ['token' => Hash::make($code), 'created_at' => now()],
        );

        $user->notify(new PasswordResetCodeNotification($code));
        $this->audit->record(ActivityAction::PasswordResetRequested, $user, causer: $user);
    }

    /** Sets the new password if the code is valid, then signs the user out everywhere. */
    public function reset(string $email, string $code, string $newPassword): void
    {
        $email = Str::lower(trim($email));
        $record = DB::table(self::TABLE)->where('email', $email)->first();
        $user = User::where('email', $email)->where('is_active', true)->first();

        $expired = $record && now()->subMinutes(config('kirana.auth.reset_code_ttl_minutes'))->gt($record->created_at);

        if (! $record || ! $user || $expired || ! Hash::check($code, $record->token)) {
            throw new ApiException(ErrorCode::InvalidResetCode);
        }

        DB::transaction(function () use ($user, $newPassword) {
            $user->update(['password' => $newPassword]);
            $user->revokeAllSessions();
            DB::table(self::TABLE)->where('email', $user->email)->delete();
        });

        $this->audit->record(ActivityAction::PasswordReset, $user, causer: $user);
    }

    private function generateCode(): string
    {
        $length = config('kirana.auth.reset_code_length');

        return str_pad((string) random_int(0, 10 ** $length - 1), $length, '0', STR_PAD_LEFT);
    }
}
