<?php

namespace App\Http\Controllers\Api\V1\Staff;

use App\Http\Controllers\Controller;
use App\Http\Requests\Admin\UnitRequest;
use App\Http\Resources\Staff\UnitResource;
use App\Models\Unit;
use App\Services\Catalogue\UnitService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\AnonymousResourceCollection;
use Illuminate\Http\Response;

class UnitController extends Controller
{
    public function __construct(private readonly UnitService $units) {}

    /** Small fixed list: not paginated. ?active=1 for the product form dropdown. */
    public function index(Request $request): AnonymousResourceCollection
    {
        $units = Unit::query()
            ->when($request->boolean('active'), fn ($q) => $q->where('is_active', true))
            ->orderBy('name')
            ->get();

        return UnitResource::collection($units);
    }

    public function store(UnitRequest $request): JsonResponse
    {
        return (new UnitResource($this->units->create($request->validated())))->response()->setStatusCode(201);
    }

    public function update(UnitRequest $request, Unit $unit): UnitResource
    {
        return new UnitResource($this->units->update($unit, $request->validated()));
    }

    public function destroy(Unit $unit): Response
    {
        $this->units->delete($unit);

        return response()->noContent();
    }
}
