<?php

namespace App\Models\Concerns;

use Illuminate\Database\Eloquent\SoftDeletes;
use Illuminate\Support\Str;

/**
 * Generates a URL slug from the model's name on create (amul-butter, amul-butter-2, …).
 * Slugs never change afterwards, so shared customer links keep working.
 */
trait HasUniqueSlug
{
    public static function bootHasUniqueSlug(): void
    {
        static::creating(function ($model) {
            $model->slug ??= $model->uniqueSlug((string) $model->name);
        });
    }

    protected function uniqueSlug(string $source): string
    {
        // Names may be in Gurmukhi only; fall back to a generic base.
        $base = Str::limit(Str::slug($source), 150, '') ?: Str::singular($this->getTable());

        $query = static::query();
        if (in_array(SoftDeletes::class, class_uses_recursive(static::class), true)) {
            $query->withTrashed();
        }

        $taken = $query->where(fn ($q) => $q->where('slug', $base)->orWhere('slug', 'like', $base.'-%'))
            ->pluck('slug')
            ->flip();

        $slug = $base;
        for ($i = 2; $taken->has($slug); $i++) {
            $slug = "{$base}-{$i}";
        }

        return $slug;
    }
}
