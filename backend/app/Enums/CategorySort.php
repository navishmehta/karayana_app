<?php

namespace App\Enums;

use Illuminate\Database\Eloquent\Builder;

enum CategorySort: string
{
    case Position = 'position';
    case NameAsc = 'name_asc';
    case NameDesc = 'name_desc';
    case Newest = 'newest';

    public const DEFAULT = self::Position;

    public function apply(Builder $query): Builder
    {
        return match ($this) {
            self::Position => $query->orderBy('sort_order')->orderBy('name'),
            self::NameAsc => $query->orderBy('name'),
            self::NameDesc => $query->orderByDesc('name'),
            self::Newest => $query->orderByDesc('created_at')->orderByDesc('id'),
        };
    }
}
