<?php

namespace App\Http\Controllers\Api\V1\Staff;

use App\Http\Controllers\Controller;
use App\Http\Requests\Staff\ProductIndexRequest;
use App\Http\Requests\Staff\ProductRequest;
use App\Http\Resources\Staff\ProductResource;
use App\Models\Product;
use App\Services\Catalogue\ProductQuery;
use App\Services\Catalogue\ProductService;
use App\Support\Pagination;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\AnonymousResourceCollection;
use Illuminate\Http\Response;

class ProductController extends Controller
{
    /** Relations every product response includes. */
    private const RELATIONS = ['category', 'brand', 'unit', 'images'];

    public function __construct(private readonly ProductService $products) {}

    public function index(ProductIndexRequest $request, ProductQuery $query): AnonymousResourceCollection
    {
        $products = $query->build($request->validated())
            ->with(self::RELATIONS)
            ->paginate(Pagination::perPage($request));

        return ProductResource::collection($products);
    }

    /** Exact match by ?barcode= or ?sku= (for the future barcode scanner). */
    public function lookup(Request $request): ProductResource
    {
        $request->validate([
            'barcode' => ['required_without:sku', 'string', 'max:64'],
            'sku' => ['required_without:barcode', 'string', 'max:64'],
        ]);

        $product = Product::query()
            ->when($request->query('barcode'), fn ($q, $code) => $q->where('barcode', $code))
            ->when($request->query('sku'), fn ($q, $sku) => $q->where('sku', $sku))
            ->firstOrFail();

        return new ProductResource($product->load(self::RELATIONS));
    }

    public function store(ProductRequest $request): JsonResponse
    {
        $product = $this->products->create($request->user(), $request->validated());

        return (new ProductResource($product->fresh(self::RELATIONS)))->response()->setStatusCode(201);
    }

    public function show(Product $product): ProductResource
    {
        return new ProductResource($product->load(self::RELATIONS));
    }

    public function update(ProductRequest $request, Product $product): ProductResource
    {
        $product = $this->products->update($request->user(), $product, $request->validated());

        return new ProductResource($product->fresh(self::RELATIONS));
    }

    public function destroy(Product $product): Response
    {
        $this->products->delete($product);

        return response()->noContent();
    }

    /** Admin only (route is in the admin group). */
    public function restore(Product $product): ProductResource
    {
        return new ProductResource($this->products->restore($product)->load(self::RELATIONS));
    }
}
