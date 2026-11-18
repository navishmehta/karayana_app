<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        // One open alert per condition, so users get one push per problem, not one per stock movement.
        Schema::create('stock_alerts', function (Blueprint $table) {
            $table->id();
            $table->foreignId('store_id')->constrained()->restrictOnDelete();
            $table->string('type', 20); // low_stock, out_of_stock, expiring_soon, expired
            $table->foreignId('product_id')->constrained()->cascadeOnDelete();
            $table->foreignId('batch_id')->nullable()->constrained('product_batches')->cascadeOnDelete();
            $table->string('dedupe_key', 100)->unique();
            $table->string('status', 10)->default('open'); // open | resolved
            $table->timestamp('triggered_at');
            $table->timestamp('resolved_at')->nullable();
            $table->timestamp('last_notified_at')->nullable();
            $table->index(['store_id', 'status', 'type']);
        });

        Schema::create('device_tokens', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->constrained()->cascadeOnDelete();
            $table->string('token')->unique();
            $table->string('platform', 10); // android | ios | web
            $table->timestamp('last_seen_at')->nullable();
            $table->timestamps();
        });

        Schema::create('notification_preferences', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->constrained()->cascadeOnDelete();
            $table->string('type', 20);
            $table->boolean('push_enabled')->default(true);
            $table->boolean('in_app_enabled')->default(true);
            $table->timestamps();
            $table->unique(['user_id', 'type']);
        });

        Schema::create('app_settings', function (Blueprint $table) {
            $table->id();
            $table->foreignId('store_id')->constrained()->cascadeOnDelete();
            $table->string('key', 80);
            $table->json('value')->nullable();
            $table->boolean('is_public')->default(false); // public subset served to the customer catalogue
            $table->timestamps();
            $table->unique(['store_id', 'key']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('app_settings');
        Schema::dropIfExists('notification_preferences');
        Schema::dropIfExists('device_tokens');
        Schema::dropIfExists('stock_alerts');
    }
};
