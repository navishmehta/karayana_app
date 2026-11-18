<?php

namespace App\Http\Controllers\Api\V1\Staff;

use App\Enums\CategorySort;
use App\Http\Controllers\Controller;
use App\Http\Requests\Staff\CategoryIndexRequest;
use App\Http\Requests\Staff\CategoryRequest;
use App\Http\Requests\Staff\ImageUploadRequest;
use App\Http\Requests\Staff\ReorderCategoriesRequest;
use App\Http\Resources\Staff\CategoryResource;
use App\Models\Category;
use App\Services\Catalogue\CategoryService;
use App\Support\Pagination;
use App\Support\Search;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Resources\Json\AnonymousResourceCollection;
use Illuminate\Http\Response;

class CategoryController extends Controller
{
    public function __construct(private readonly CategoryService $categories) {}

    /** ?search= &status=active|inactive &sort=position|name_asc|name_desc|newest */
    public function index(CategoryIndexRequest $request): AnonymousResourceCollection
    {
        $filters = $request->validated();
        $sort = CategorySort::tryFrom($filters['sort'] ?? '') ?? CategorySort::DEFAULT;

        $query = Category::query()
            ->withCount('products')
            ->when($filters['search'] ?? null, fn ($q, $term) => $q->where('name', 'like', Search::contains($term)))
            ->when($filters['status'] ?? null, fn ($q, $status) => $q->where('is_active', $status === 'active'));

        return CategoryResource::collection($sort->apply($query)->paginate(Pagination::perPage($request)));
    }

    public function store(CategoryRequest $request): JsonResponse
    {
        $category = $this->categories->create($request->user(), $request->safe()->except('image'), $request->file('image'));

        return (new CategoryResource($category))->response()->setStatusCode(201);
    }

    public function show(Category $category): CategoryResource
    {
        return new CategoryResource($category->loadCount('products'));
    }

    public function update(CategoryRequest $request, Category $category): CategoryResource
    {
        return new CategoryResource($this->categories->update($request->user(), $category, $request->validated()));
    }

    public function reorder(ReorderCategoriesRequest $request): Response
    {
        $this->categories->reorder($request->validated('ids'));

        return response()->noContent();
    }

    public function uploadImage(ImageUploadRequest $request, Category $category): CategoryResource
    {
        return new CategoryResource($this->categories->replaceImage($category, $request->file('image')));
    }

    public function deleteImage(Category $category): CategoryResource
    {
        return new CategoryResource($this->categories->removeImage($category));
    }

    public function destroy(Category $category): Response
    {
        $this->categories->delete($category);

        return response()->noContent();
    }
}
