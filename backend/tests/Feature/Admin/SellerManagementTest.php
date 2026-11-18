<?php

namespace Tests\Feature\Admin;

use App\Enums\ActivityAction;
use App\Enums\Permission;
use App\Models\Store;
use App\Models\User;
use Tests\ApiTestCase;

class SellerManagementTest extends ApiTestCase
{
    private function newSellerPayload(array $overrides = []): array
    {
        return $overrides + [
            'name' => 'Raju',
            'email' => 'raju@example.com',
            'phone' => '9876543210',
            'password' => 'Seller123',
            'password_confirmation' => 'Seller123',
            'permissions' => [Permission::ProductsView->value, Permission::StockView->value],
        ];
    }

    public function test_admin_creates_seller_who_can_then_log_in(): void
    {
        $this->actingAsToken($this->admin())
            ->postJson('/api/v1/admin/sellers', $this->newSellerPayload())
            ->assertCreated()
            ->assertJsonPath('data.email', 'raju@example.com')
            ->assertJsonPath('data.permissions', [Permission::ProductsView->value, Permission::StockView->value]);

        $this->postJson('/api/v1/auth/login', ['email' => 'raju@example.com', 'password' => 'Seller123', 'device_name' => 'x'])
            ->assertOk()->assertJsonPath('data.user.role', 'seller');

        $this->assertDatabaseHas('activity_log', ['event' => ActivityAction::SellerCreated->value]);
    }

    public function test_permission_dependencies_are_enforced(): void
    {
        $this->actingAsToken($this->admin())
            ->postJson('/api/v1/admin/sellers', $this->newSellerPayload(['permissions' => [Permission::StockUpdate->value]]))
            ->assertJsonValidationErrors(['permissions' => 'View stock, View products']); // indirect dependency too
    }

    public function test_unknown_permission_is_rejected(): void
    {
        $this->actingAsToken($this->admin())
            ->postJson('/api/v1/admin/sellers', $this->newSellerPayload(['permissions' => ['everything.all']]))
            ->assertJsonValidationErrors('permissions.0');
    }

    public function test_admin_updates_permissions_and_they_apply_immediately(): void
    {
        $seller = $this->seller([Permission::ProductsView->value]);
        $sellerToken = $seller->createToken('phone')->plainTextToken;

        $this->actingAsToken($this->admin())
            ->putJson("/api/v1/admin/sellers/{$seller->id}/permissions", ['permissions' => []])
            ->assertOk()->assertJsonPath('data.permissions', []);

        $this->app['auth']->forgetGuards();
        $this->withToken($sellerToken)->getJson('/api/v1/auth/me')->assertJsonPath('data.permissions', []);
        $this->assertDatabaseHas('activity_log', ['event' => ActivityAction::SellerPermissionsUpdated->value]);
    }

    public function test_deactivating_seller_revokes_all_sessions(): void
    {
        $seller = $this->seller();
        $seller->createToken('phone');

        $this->actingAsToken($this->admin())
            ->patchJson("/api/v1/admin/sellers/{$seller->id}/status", ['is_active' => false])
            ->assertOk()->assertJsonPath('data.is_active', false);

        $this->assertSame(0, $seller->tokens()->count());
    }

    public function test_admin_resets_seller_password(): void
    {
        $seller = $this->seller();

        $this->actingAsToken($this->admin())
            ->postJson("/api/v1/admin/sellers/{$seller->id}/reset-password", ['password' => 'Reset1234', 'password_confirmation' => 'Reset1234'])
            ->assertOk();

        $this->postJson('/api/v1/auth/login', ['email' => $seller->email, 'password' => 'Reset1234', 'device_name' => 'x'])->assertOk();
    }

    public function test_deleted_seller_cannot_log_in_and_email_stays_reserved(): void
    {
        $admin = $this->admin();
        $seller = $this->seller();

        $this->actingAsToken($admin)->deleteJson("/api/v1/admin/sellers/{$seller->id}")->assertNoContent();
        $this->assertSoftDeleted($seller);

        $this->postJson('/api/v1/auth/login', ['email' => $seller->email, 'password' => 'password', 'device_name' => 'x'])
            ->assertUnauthorized();

        $this->postJson('/api/v1/admin/sellers', $this->newSellerPayload(['email' => $seller->email]))
            ->assertJsonValidationErrors('email');
    }

    public function test_list_supports_search_and_status_filter(): void
    {
        $admin = $this->admin();
        $this->seller()->update(['name' => 'Aman Singh']);
        User::factory()->seller()->inactive()->create(['name' => 'Bunty']);

        $this->actingAsToken($admin)->getJson('/api/v1/admin/sellers?search=aman')
            ->assertOk()->assertJsonCount(1, 'data')->assertJsonPath('data.0.name', 'Aman Singh');

        $this->getJson('/api/v1/admin/sellers?status=inactive')->assertJsonCount(1, 'data')->assertJsonPath('data.0.name', 'Bunty');
    }

    public function test_seller_routes_never_resolve_admins_or_other_stores(): void
    {
        $admin = $this->admin();
        $otherAdmin = $this->admin();
        $otherStore = Store::create(['name' => 'Other', 'slug' => 'other']);
        $foreignSeller = User::factory()->seller()->create(['store_id' => $otherStore->id]);

        $this->actingAsToken($admin)->getJson("/api/v1/admin/sellers/{$otherAdmin->id}")->assertNotFound();
        $this->getJson("/api/v1/admin/sellers/{$foreignSeller->id}")->assertNotFound();
    }

    public function test_sellers_cannot_access_admin_area_even_with_every_permission(): void
    {
        $seller = $this->seller(Permission::values());

        $this->actingAsToken($seller);
        $this->getJson('/api/v1/admin/sellers')->assertForbidden()->assertJsonPath('code', 'FORBIDDEN');
        $this->getJson('/api/v1/admin/permissions')->assertForbidden();
        $this->getJson('/api/v1/admin/activity-logs')->assertForbidden();
        $this->postJson('/api/v1/admin/sellers', $this->newSellerPayload())->assertForbidden();
    }

    public function test_guests_get_401(): void
    {
        $this->getJson('/api/v1/admin/sellers')->assertUnauthorized()->assertJsonPath('code', 'UNAUTHENTICATED');
    }

    public function test_permission_catalogue_is_grouped_and_translated(): void
    {
        $this->actingAsToken($this->admin())
            ->getJson('/api/v1/admin/permissions', ['Accept-Language' => 'pa'])
            ->assertOk()
            ->assertJsonPath('data.0.key', 'dashboard')
            ->assertJsonPath('data.0.label', 'ਡੈਸ਼ਬੋਰਡ')
            ->assertJsonFragment(['key' => Permission::StockUpdate->value, 'depends_on' => [Permission::StockView->value]]);
    }

    public function test_activity_log_lists_and_filters_by_seller(): void
    {
        $admin = $this->admin();
        $seller = $this->seller();
        $this->postJson('/api/v1/auth/login', ['email' => $seller->email, 'password' => 'password', 'device_name' => 'x']);

        $this->actingAsToken($admin)->getJson("/api/v1/admin/sellers/{$seller->id}/activity")
            ->assertOk()
            ->assertJsonPath('data.0.event', ActivityAction::Login->value)
            ->assertJsonPath('data.0.causer.id', $seller->id)
            ->assertJsonPath('data.0.description', 'Logged in');

        $this->getJson('/api/v1/admin/activity-logs?event=sellers.created')->assertOk()->assertJsonCount(0, 'data');
    }
}
