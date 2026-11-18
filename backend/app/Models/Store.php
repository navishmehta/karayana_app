<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Store extends Model
{
    protected $fillable = ['name', 'slug', 'phone', 'address', 'gstin', 'timezone', 'currency', 'is_active'];

    protected $casts = ['is_active' => 'boolean'];

    /** V1 is single-store: the first active store. */
    public static function default(): self
    {
        return static::where('is_active', true)->orderBy('id')->firstOrFail();
    }

    public function users(): HasMany
    {
        return $this->hasMany(User::class);
    }

    public function categories(): HasMany
    {
        return $this->hasMany(Category::class);
    }

    public function products(): HasMany
    {
        return $this->hasMany(Product::class);
    }
}
