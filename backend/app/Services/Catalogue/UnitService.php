<?php

namespace App\Services\Catalogue;

use App\Enums\ActivityAction;
use App\Enums\ErrorCode;
use App\Exceptions\ApiException;
use App\Models\Product;
use App\Models\Unit;
use App\Services\Audit\AuditLogger;

class UnitService
{
    public function __construct(private readonly AuditLogger $audit) {}

    public function create(array $data): Unit
    {
        $unit = Unit::create($data);
        $this->audit->record(ActivityAction::UnitCreated, $unit, ['short_name' => $unit->short_name]);

        return $unit;
    }

    public function update(Unit $unit, array $data): Unit
    {
        $unit->fill($data);
        $changes = $unit->getDirty();
        $original = array_intersect_key($unit->getOriginal(), $changes);
        $unit->save();

        if ($changes) {
            $this->audit->record(ActivityAction::UnitUpdated, $unit, ['old' => $original, 'new' => $changes]);
        }

        return $unit;
    }

    /** Units in use (even by deleted products) can only be deactivated. */
    public function delete(Unit $unit): void
    {
        if (Product::withoutGlobalScopes()->where('unit_id', $unit->id)->exists()) {
            throw new ApiException(ErrorCode::InUse);
        }

        $unit->delete();
        $this->audit->record(ActivityAction::UnitDeleted, properties: ['short_name' => $unit->short_name]);
    }
}
