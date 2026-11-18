<?php

namespace App\Http\Resources\Admin;

use App\Enums\ActivityAction;
use App\Support\StoreClock;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;
use Spatie\Activitylog\Models\Activity;

/** @mixin Activity */
class ActivityResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'log' => $this->log_name,
            'event' => $this->event,
            'description' => ActivityAction::tryFrom((string) $this->event)?->description() ?? $this->description,
            'causer' => $this->causer ? ['id' => $this->causer->id, 'name' => $this->causer->name] : null,
            'subject' => $this->subject_type ? ['type' => $this->subject_type, 'id' => $this->subject_id] : null,
            'properties' => $this->properties,
            'created_at' => StoreClock::toApi($this->created_at),
        ];
    }
}
