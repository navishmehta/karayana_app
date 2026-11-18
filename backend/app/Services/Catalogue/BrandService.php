<?php

namespace App\Services\Catalogue;

use App\Enums\ActivityAction;
use App\Enums\ErrorCode;
use App\Exceptions\ApiException;
use App\Models\Brand;
use App\Services\Audit\AuditLogger;

class BrandService
{
    public function __construct(private readonly AuditLogger $audit) {}

    public function create(array $data): Brand
    {
        $brand = Brand::create($data);
        $this->audit->record(ActivityAction::BrandCreated, $brand, ['name' => $brand->name]);

        return $brand;
    }

    public function update(Brand $brand, array $data): Brand
    {
        $brand->fill($data);
        $changes = $brand->getDirty();
        $original = array_intersect_key($brand->getOriginal(), $changes);
        $brand->save();

        if ($changes) {
            $this->audit->record(ActivityAction::BrandUpdated, $brand, ['old' => $original, 'new' => $changes]);
        }

        return $brand;
    }

    public function delete(Brand $brand): void
    {
        if ($brand->products()->exists()) {
            throw new ApiException(ErrorCode::InUse);
        }

        $brand->delete();
        $this->audit->record(ActivityAction::BrandDeleted, $brand, ['name' => $brand->name]);
    }
}
