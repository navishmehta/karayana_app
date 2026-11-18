<?php

namespace App\Http\Controllers\Api\V1\Staff;

use App\Http\Controllers\Controller;
use App\Http\Requests\Staff\ImageUploadRequest;
use App\Http\Requests\Staff\UpdateProductImageRequest;
use App\Http\Resources\Staff\ProductImageResource;
use App\Models\Product;
use App\Models\ProductImage;
use App\Services\Catalogue\ProductImageService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Resources\Json\AnonymousResourceCollection;
use Illuminate\Http\Response;

class ProductImageController extends Controller
{
    public function __construct(private readonly ProductImageService $images) {}

    public function store(ImageUploadRequest $request, Product $product): JsonResponse
    {
        $image = $this->images->add($product, $request->file('image'));

        return (new ProductImageResource($image))->response()->setStatusCode(201);
    }

    /** Returns the product's full image list so the app can redraw the gallery in one go. */
    public function update(UpdateProductImageRequest $request, Product $product, ProductImage $image): AnonymousResourceCollection
    {
        $this->images->update($image, $request->validated());

        return ProductImageResource::collection($product->images()->get());
    }

    public function destroy(Product $product, ProductImage $image): Response
    {
        $this->images->delete($image);

        return response()->noContent();
    }
}
