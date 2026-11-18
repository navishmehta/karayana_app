<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\QueryException;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

/**
 * Rules:
 *  - Every unit of stock lives in a batch (expiry_date NULL for non-perishables).
 *  - product_batches.quantity_remaining is the source of truth.
 *  - stock_transactions is an append-only ledger; corrections are new reversing rows.
 */
return new class extends Migration
{
    public function up(): void
    {
        Schema::create('product_batches', function (Blueprint $table) {
            $table->id();
            $table->foreignId('store_id')->constrained()->restrictOnDelete();
            $table->foreignId('product_id')->constrained()->restrictOnDelete();
            $table->string('batch_number', 64)->nullable();
            $table->date('manufacturing_date')->nullable();
            $table->date('expiry_date')->nullable();
            $table->decimal('quantity_received', 12, 3);
            $table->decimal('quantity_remaining', 12, 3);
            $table->decimal('purchase_price', 12, 2)->nullable(); // PRIVATE: cost per unit for this batch
            $table->timestamp('received_at');
            $table->unsignedBigInteger('purchase_item_id')->nullable(); // V2 purchases link
            $table->string('notes')->nullable();
            $table->foreignId('created_by')->constrained('users')->restrictOnDelete();
            $table->timestamps();

            $table->index(['product_id', 'expiry_date', 'id'], 'batches_fefo_idx');
            $table->index(['store_id', 'expiry_date', 'quantity_remaining'], 'batches_expiry_idx');
        });

        DB::statement('ALTER TABLE product_batches
            ADD CONSTRAINT batches_qty_received_positive CHECK (quantity_received > 0),
            ADD CONSTRAINT batches_qty_remaining_non_negative CHECK (quantity_remaining >= 0),
            ADD CONSTRAINT batches_cost_non_negative CHECK (purchase_price IS NULL OR purchase_price >= 0),
            ADD CONSTRAINT batches_dates_order CHECK (expiry_date IS NULL OR manufacturing_date IS NULL OR expiry_date >= manufacturing_date)');

        Schema::create('inventory_adjustments', function (Blueprint $table) {
            $table->id();
            $table->foreignId('store_id')->constrained()->restrictOnDelete();
            $table->string('type', 20);        // stock_in, stock_out, adjustment, damage, expiry_writeoff
            $table->string('reason_code', 40);
            $table->text('notes')->nullable();
            $table->string('attachment_path')->nullable();
            $table->decimal('cost_impact', 12, 2)->nullable(); // PRIVATE
            $table->foreignId('created_by')->constrained('users')->restrictOnDelete();
            $table->timestamp('created_at')->useCurrent();
            $table->index(['store_id', 'type', 'created_at']);
        });

        Schema::create('stock_transactions', function (Blueprint $table) {
            $table->id();
            $table->foreignId('store_id')->constrained()->restrictOnDelete();
            $table->foreignId('product_id')->constrained()->restrictOnDelete();
            $table->foreignId('batch_id')->constrained('product_batches')->restrictOnDelete();
            $table->string('type', 24);
            $table->decimal('quantity_change', 12, 3); // signed
            $table->decimal('product_qty_before', 12, 3);
            $table->decimal('product_qty_after', 12, 3);
            $table->decimal('batch_qty_before', 12, 3);
            $table->decimal('batch_qty_after', 12, 3);
            $table->decimal('unit_cost', 12, 2)->nullable(); // PRIVATE snapshot
            $table->string('reason')->nullable();
            $table->string('reference_type', 60)->nullable(); // inventory_adjustment now; sale_item / purchase_item later
            $table->unsignedBigInteger('reference_id')->nullable();
            $table->string('idempotency_key', 64)->nullable();
            $table->foreignId('user_id')->constrained()->restrictOnDelete();
            $table->timestamp('created_at', 3)->useCurrent();

            $table->index(['product_id', 'created_at']);
            $table->index(['store_id', 'type', 'created_at']);
            $table->index(['user_id', 'created_at']);
            $table->index(['reference_type', 'reference_id']);
            $table->unique(['store_id', 'idempotency_key', 'batch_id'], 'stock_tx_idempotency_unique');
        });

        DB::statement('ALTER TABLE stock_transactions
            ADD CONSTRAINT stock_tx_nonzero CHECK (quantity_change <> 0),
            ADD CONSTRAINT stock_tx_product_math CHECK (product_qty_after = product_qty_before + quantity_change),
            ADD CONSTRAINT stock_tx_batch_math CHECK (batch_qty_after = batch_qty_before + quantity_change)');

        // Defence in depth: the StockTransaction model already refuses update/delete. The DB triggers need
        // SUPER (or log_bin_trust_function_creators=1) when binary logging is on, which many hosts don't grant.
        try {
            DB::unprepared("CREATE TRIGGER stock_transactions_no_update BEFORE UPDATE ON stock_transactions
                FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'stock_transactions is append-only'");
            DB::unprepared("CREATE TRIGGER stock_transactions_no_delete BEFORE DELETE ON stock_transactions
                FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'stock_transactions is append-only'");
        } catch (QueryException $e) {
            if (! str_contains($e->getMessage(), '1419')) {
                throw $e;
            }
            fwrite(STDERR, "  WARN  Ledger triggers skipped (DB user lacks trigger privilege). Model-level guard still applies.\n");
        }
    }

    public function down(): void
    {
        DB::unprepared('DROP TRIGGER IF EXISTS stock_transactions_no_update');
        DB::unprepared('DROP TRIGGER IF EXISTS stock_transactions_no_delete');
        Schema::dropIfExists('stock_transactions');
        Schema::dropIfExists('inventory_adjustments');
        Schema::dropIfExists('product_batches');
    }
};
