<?php

namespace App\Services\Users;

use App\Enums\ActivityAction;
use App\Enums\Role;
use App\Models\User;
use App\Services\Audit\AuditLogger;
use Illuminate\Support\Facades\DB;

/** Admin operations on seller accounts. Permission input is validated by the FormRequests. */
class SellerService
{
    public function __construct(private readonly AuditLogger $audit) {}

    /** @param  list<string>  $permissions */
    public function create(User $admin, array $data, array $permissions): User
    {
        $seller = DB::transaction(function () use ($admin, $data, $permissions) {
            $seller = User::create($data + [
                'store_id' => $admin->store_id,
                'created_by' => $admin->id,
                'email_verified_at' => now(),
            ]);
            $seller->assignRole(Role::Seller->value);
            $seller->syncPermissions($permissions);

            return $seller;
        });

        $this->audit->record(ActivityAction::SellerCreated, $seller, ['permissions' => $permissions]);

        return $seller;
    }

    public function update(User $seller, array $data): User
    {
        $seller->fill($data);
        $changes = $seller->getDirty();
        $original = array_intersect_key($seller->getOriginal(), $changes);
        $seller->save();

        if ($changes) {
            $this->audit->record(ActivityAction::SellerUpdated, $seller, ['old' => $original, 'new' => $changes]);
        }

        return $seller;
    }

    /** Replaces the seller's permission set. Takes effect on their next request. @param list<string> $permissions */
    public function syncPermissions(User $seller, array $permissions): User
    {
        $old = $seller->permissionKeys();
        $seller->syncPermissions($permissions);

        $this->audit->record(ActivityAction::SellerPermissionsUpdated, $seller, [
            'old' => $old,
            'new' => $seller->permissionKeys(),
        ]);

        return $seller;
    }

    /** Deactivating signs the seller out of every device immediately. */
    public function setActive(User $seller, bool $active): User
    {
        DB::transaction(function () use ($seller, $active) {
            $seller->update(['is_active' => $active]);
            if (! $active) {
                $seller->revokeAllSessions();
            }
        });

        $this->audit->record($active ? ActivityAction::SellerActivated : ActivityAction::SellerDeactivated, $seller);

        return $seller;
    }

    public function resetPassword(User $seller, string $password): void
    {
        DB::transaction(function () use ($seller, $password) {
            $seller->update(['password' => $password]);
            $seller->revokeAllSessions();
        });

        $this->audit->record(ActivityAction::SellerPasswordReset, $seller);
    }

    /** Soft delete: history (stock movements, activity) keeps pointing at this user. */
    public function delete(User $seller): void
    {
        DB::transaction(function () use ($seller) {
            $seller->revokeAllSessions();
            $seller->delete();
        });

        $this->audit->record(ActivityAction::SellerDeleted, $seller, ['email' => $seller->email]);
    }
}
