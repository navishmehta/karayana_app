<?php

namespace App\Http\Controllers\Api\V1\Staff;

use App\Http\Controllers\Controller;
use App\Http\Requests\Staff\BrandRequest;
use App\Http\Resources\Staff\BrandResource;
use App\Models\Brand;
use App\Services\Catalogue\BrandService;
use App\Support\Pagination;
use App\Support\Search;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\AnonymousResourceCollection;
use Illuminate\Http\Response;

class BrandController extends Controller
{
    public function __construct(private readonly BrandService $brands) {}

    /** ?search= for autocomplete in the product form. */
    public function index(Request $request): AnonymousResourceCollection
    {
        $brands = Brand::query()
            ->withCount('products')
            ->when($request->query('search'), fn ($q, $term) => $q->where('name', 'like', Search::contains((string) $term)))
            ->orderBy('name')
            ->paginate(Pagination::perPage($request));

        return BrandResource::collection($brands);
    }

    public function store(BrandRequest $request): JsonResponse
    {
        return (new BrandResource($this->brands->create($request->validated())))->response()->setStatusCode(201);
    }

    public function update(BrandRequest $request, Brand $brand): BrandResource
    {
        return new BrandResource($this->brands->update($brand, $request->validated()));
    }

    public function destroy(Brand $brand): Response
    {
        $this->brands->delete($brand);

        return response()->noContent();
    }
}
