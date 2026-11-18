<?php

namespace App\Services\Catalogue;

use App\Enums\ActivityAction;
use App\Enums\ErrorCode;
use App\Enums\MediaFolder;
use App\Exceptions\ApiException;
use App\Models\Category;
use App\Models\User;
use App\Services\Audit\AuditLogger;
use App\Services\Media\ImageService;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\DB;

class CategoryService
{
    public function __construct(
        private readonly AuditLogger $audit,
        private readonly ImageService $images,
    ) {}

    public function create(User $user, array $data, ?UploadedFile $image = null): Category
    {
        $category = new Category($data);
        $category->sort_order ??= (int) Category::max('sort_order') + 1;
        $category->created_by = $user->id;

        if ($image) {
            $this->applyImage($category, $image);
        }
        $category->save();

        $this->audit->record(ActivityAction::CategoryCreated, $category, ['name' => $category->name]);

        return $category;
    }

    public function update(User $user, Category $category, array $data): Category
    {
        $category->fill($data);
        $changes = $category->getDirty();
        $original = array_intersect_key($category->getOriginal(), $changes);
        $category->updated_by = $user->id;
        $category->save();

        if ($changes) {
            $this->audit->record(ActivityAction::CategoryUpdated, $category, ['old' => $original, 'new' => $changes]);
        }

        return $category;
    }

    public function replaceImage(Category $category, UploadedFile $image): Category
    {
        $old = [$category->image_path, $category->image_thumb_path];
        $this->applyImage($category, $image);
        $category->save();
        $this->images->delete(...$old);

        $this->audit->record(ActivityAction::CategoryImageUpdated, $category);

        return $category;
    }

    public function removeImage(Category $category): Category
    {
        $this->images->delete($category->image_path, $category->image_thumb_path);
        $category->update(['image_path' => null, 'image_thumb_path' => null]);

        $this->audit->record(ActivityAction::CategoryImageRemoved, $category);

        return $category;
    }

    /** @param  list<int>  $orderedIds  Category IDs in the new display order. */
    public function reorder(array $orderedIds): void
    {
        DB::transaction(function () use ($orderedIds) {
            foreach (array_values($orderedIds) as $position => $id) {
                Category::whereKey($id)->update(['sort_order' => $position]);
            }
        });

        $this->audit->record(ActivityAction::CategoriesReordered, properties: ['order' => $orderedIds]);
    }

    /** Only empty categories can be deleted; otherwise deactivate it or move its products first. */
    public function delete(Category $category): void
    {
        if ($category->products()->exists()) {
            throw new ApiException(ErrorCode::CategoryNotEmpty);
        }

        $category->delete();
        $this->images->delete($category->image_path, $category->image_thumb_path);

        $this->audit->record(ActivityAction::CategoryDeleted, $category, ['name' => $category->name]);
    }

    private function applyImage(Category $category, UploadedFile $image): void
    {
        $stored = $this->images->store($image, MediaFolder::Categories);
        $category->image_path = $stored->path;
        $category->image_thumb_path = $stored->thumbPath;
    }
}
