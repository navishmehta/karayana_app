<?php

namespace App\Services\Audit;

use App\Enums\ActivityAction;
use App\Models\User;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Http\Request;

/** Single entry point for writing to the activity log, so every entry has the same shape. */
class AuditLogger
{
    public function __construct(private readonly Request $request) {}

    public function record(ActivityAction $action, ?Model $subject = null, array $properties = [], ?User $causer = null): void
    {
        $logger = activity($action->logName())
            ->event($action->value)
            ->withProperties($properties + [
                'ip' => $this->request->ip(),
                'user_agent' => substr((string) $this->request->userAgent(), 0, 255),
            ]);

        if ($subject) {
            $logger->performedOn($subject);
        }

        $causer ??= $this->request->user();
        $causer ? $logger->causedBy($causer) : $logger->causedByAnonymous();

        $logger->log($action->value);
    }
}
