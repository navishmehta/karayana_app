<?php

namespace App\Http\Controllers\Api\V1\Admin;

use App\Http\Controllers\Controller;
use App\Http\Requests\Admin\ResetSellerPasswordRequest;
use App\Http\Requests\Admin\StoreSellerRequest;
use App\Http\Requests\Admin\UpdateSellerPermissionsRequest;
use App\Http\Requests\Admin\UpdateSellerRequest;
use App\Http\Requests\Admin\UpdateSellerStatusRequest;
use App\Http\Resources\Admin\SellerResource;
use App\Models\User;
use App\Services\Users\SellerService;
use App\Support\ApiResponse;
use App\Support\Pagination;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\AnonymousResourceCollection;
use Illuminate\Http\Response;

class SellerController extends Controller
{
    public function __construct(private readonly SellerService $sellers) {}

    /** ?search= (name/email/phone) &status=active|inactive */
    public function index(Request $request): AnonymousResourceCollection
    {
        $sellers = User::sellers()
            ->where('store_id', $request->user()->store_id)
            ->when($request->query('search'), fn ($q, $term) => $q->where(fn ($q) => $q
                ->where('name', 'like', "%{$term}%")
                ->orWhere('email', 'like', "%{$term}%")
                ->orWhere('phone', 'like', "%{$term}%")))
            ->when($request->query('status'), fn ($q, $status) => $q->where('is_active', $status === 'active'))
            ->with('permissions')
            ->withCount('tokens')
            ->orderBy('name')
            ->paginate(Pagination::perPage($request));

        return SellerResource::collection($sellers);
    }

    public function store(StoreSellerRequest $request): JsonResponse
    {
        $data = $request->safe()->except('permissions');
        $seller = $this->sellers->create($request->user(), $data, $request->validated('permissions'));

        return (new SellerResource($seller))->response()->setStatusCode(201);
    }

    public function show(User $seller): SellerResource
    {
        return new SellerResource($seller->loadCount('tokens'));
    }

    public function update(UpdateSellerRequest $request, User $seller): SellerResource
    {
        return new SellerResource($this->sellers->update($seller, $request->validated()));
    }

    public function updatePermissions(UpdateSellerPermissionsRequest $request, User $seller): SellerResource
    {
        return new SellerResource($this->sellers->syncPermissions($seller, $request->validated('permissions')));
    }

    public function updateStatus(UpdateSellerStatusRequest $request, User $seller): SellerResource
    {
        return new SellerResource($this->sellers->setActive($seller, $request->boolean('is_active')));
    }

    public function resetPassword(ResetSellerPasswordRequest $request, User $seller): JsonResponse
    {
        $this->sellers->resetPassword($seller, $request->password);

        return ApiResponse::message('seller_password_reset');
    }

    public function destroy(User $seller): Response
    {
        $this->sellers->delete($seller);

        return response()->noContent();
    }
}
