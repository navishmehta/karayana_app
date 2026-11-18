<?php

namespace App\Http\Controllers\Api\V1\Admin;

use App\Enums\Permission;
use App\Http\Controllers\Controller;
use Illuminate\Http\JsonResponse;

/** Permission catalogue for the admin's permission editor, grouped by module, with translated labels. */
class PermissionController extends Controller
{
    public function __invoke(): JsonResponse
    {
        $groups = collect(Permission::cases())
            ->groupBy(fn (Permission $p) => $p->group())
            ->map(fn ($permissions, $group) => [
                'key' => $group,
                'label' => __('permissions.groups.'.$group),
                'permissions' => $permissions->map(fn (Permission $p) => [
                    'key' => $p->value,
                    'label' => $p->label(),
                    'depends_on' => array_map(fn (Permission $d) => $d->value, $p->dependsOn()),
                ])->values(),
            ])
            ->values();

        return response()->json(['data' => $groups]);
    }
}
