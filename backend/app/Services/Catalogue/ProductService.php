<?php

namespace App\Services\Catalogue;

use App\Constants\AppConstants;
use App\Enums\ActivityAction;
use App\Models\Product;
use App\Models\User;
use App\Services\Audit\AuditLogger;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Str;

/**
 * Product details and prices. Stock quantities are NOT changed here —
 * only the inventory service may change stock, so every change has a ledger entry.
 */
class ProductService
{
    public function __construct(private readonly AuditLogger $audit) {}

    public function create(User $user, array $data): Product
    {
        $product = DB::transaction(function () use ($user, $data) {
            $product = new Product($data);
            $product->created_by = $user->id;
            $product->sku = $data['sku'] ?? 'TMP-'.Str::uuid(); // replaced by SK-000123 once the ID exists
            $product->save();

            if (empty($data['sku'])) {
                $product->update(['sku' => $this->generateSku($product)]);
            }

            return $product;
        });

        $this->audit->record(ActivityAction::ProductCreated, $product, ['name' => $product->name, 'sku' => $product->sku]);

        return $product;
    }

    /** Price changes are logged separately so price history is easy to find. */
    public function update(User $user, Product $product, array $data): Product
    {
        $product->fill($data);
        $changes = $product->getDirty();
        $original = array_intersect_key($product->getOriginal(), $changes);
        $product->updated_by = $user->id;
        $product->save();

        $priceKeys = array_flip([...Product::SELLING_PRICE_FIELDS, 'purchase_price']);
        $priceChanges = array_intersect_key($changes, $priceKeys);
        $otherChanges = array_diff_key($changes, $priceKeys);

        if ($priceChanges) {
            $this->audit->record(ActivityAction::ProductPriceChanged, $product, [
                'old' => array_intersect_key($original, $priceChanges),
                'new' => $priceChanges,
            ]);
        }
        if ($otherChanges) {
            $this->audit->record(ActivityAction::ProductUpdated, $product, [
                'old' => array_intersect_key($original, $otherChanges),
                'new' => $otherChanges,
            ]);
        }

        return $product;
    }

    /** Soft delete: stock history keeps pointing at the product; the admin can restore it. */
    public function delete(Product $product): void
    {
        $product->delete();
        $this->audit->record(ActivityAction::ProductDeleted, $product, ['name' => $product->name]);
    }

    public function restore(Product $product): Product
    {
        $product->restore();
        $this->audit->record(ActivityAction::ProductRestored, $product, ['name' => $product->name]);

        return $product;
    }

    private function generateSku(Product $product): string
    {
        $sku = AppConstants::SKU_PREFIX.str_pad((string) $product->id, AppConstants::SKU_PAD_LENGTH, '0', STR_PAD_LEFT);

        // Extremely rare: someone manually typed this code for another product.
        for ($i = 2; Product::withTrashed()->where('sku', $sku)->exists(); $i++) {
            $sku = AppConstants::SKU_PREFIX.str_pad((string) $product->id, AppConstants::SKU_PAD_LENGTH, '0', STR_PAD_LEFT)."-{$i}";
        }

        return $sku;
    }
}
