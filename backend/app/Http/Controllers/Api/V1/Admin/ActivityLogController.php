<?php

namespace App\Http\Controllers\Api\V1\Admin;

use App\Http\Controllers\Controller;
use App\Http\Requests\Admin\ActivityLogIndexRequest;
use App\Http\Resources\Admin\ActivityResource;
use App\Models\User;
use App\Support\Pagination;
use App\Support\StoreClock;
use Carbon\CarbonImmutable;
use Illuminate\Http\Resources\Json\AnonymousResourceCollection;
use Spatie\Activitylog\Models\Activity;

class ActivityLogController extends Controller
{
    /** ?causer_id= &event= &log= &from=YYYY-MM-DD &to=YYYY-MM-DD (store-local dates) */
    public function index(ActivityLogIndexRequest $request): AnonymousResourceCollection
    {
        $filters = $request->validated();

        $activities = Activity::query()
            ->with('causer')
            ->when($filters['causer_id'] ?? null, fn ($q, $id) => $q->where('causer_type', 'user')->where('causer_id', $id))
            ->when($filters['event'] ?? null, fn ($q, $event) => $q->where('event', $event))
            ->when($filters['log'] ?? null, fn ($q, $log) => $q->where('log_name', $log))
            ->when($filters['from'] ?? null, fn ($q, $from) => $q->where('created_at', '>=', $this->startOfDay($from)))
            ->when($filters['to'] ?? null, fn ($q, $to) => $q->where('created_at', '<', $this->startOfDay($to)->addDay()))
            ->latest('id')
            ->paginate(Pagination::perPage($request));

        return ActivityResource::collection($activities);
    }

    /** Everything a given seller did. */
    public function forSeller(ActivityLogIndexRequest $request, User $seller): AnonymousResourceCollection
    {
        $request->merge(['causer_id' => $seller->id]);

        return $this->index($request);
    }

    /** Store-local midnight converted to UTC for the query. */
    private function startOfDay(string $date): CarbonImmutable
    {
        return CarbonImmutable::parse($date, StoreClock::timezone())->startOfDay()->utc();
    }
}
