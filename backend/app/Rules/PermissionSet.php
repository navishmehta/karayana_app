<?php

namespace App\Rules;

use App\Enums\Permission;
use Closure;
use Illuminate\Contracts\Validation\ValidationRule;
use Illuminate\Validation\Rule;

/** A seller's permission list must include every dependency (e.g. stock.update needs stock.view). */
class PermissionSet implements ValidationRule
{
    public function validate(string $attribute, mixed $value, Closure $fail): void
    {
        if (! is_array($value)) {
            return;
        }

        foreach (Permission::missingDependencies($value) as $permission => $missing) {
            $fail('validation.permission_dependency')->translate([
                'permission' => Permission::from($permission)->label(),
                'required' => collect($missing)->map(fn ($p) => Permission::from($p)->label())->join(', '),
            ]);
        }
    }

    /** Full rule set for a `permissions` array field. */
    public static function rules(): array
    {
        return [
            'permissions' => ['present', 'array', new self],
            'permissions.*' => ['string', 'distinct', Rule::in(Permission::values())],
        ];
    }
}
