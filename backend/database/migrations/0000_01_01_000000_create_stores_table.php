<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

/**
 * One row in V1. Store-scoped tables carry store_id so multi-store (V4) needs no schema rewrite.
 */
return new class extends Migration
{
    public function up(): void
    {
        Schema::create('stores', function (Blueprint $table) {
            $table->id();
            $table->string('name', 150);
            $table->string('slug', 160)->unique();
            $table->string('phone', 20)->nullable();
            $table->text('address')->nullable();
            $table->string('gstin', 15)->nullable();
            $table->string('timezone', 40)->default('Asia/Kolkata');
            $table->char('currency', 3)->default('INR');
            $table->boolean('is_active')->default(true);
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('stores');
    }
};
