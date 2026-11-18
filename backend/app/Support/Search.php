<?php

namespace App\Support;

final class Search
{
    /** '%term%' for LIKE, with the user's % and _ treated as plain characters. */
    public static function contains(string $term): string
    {
        return '%'.self::escape($term).'%';
    }

    public static function startsWith(string $term): string
    {
        return self::escape($term).'%';
    }

    private static function escape(string $term): string
    {
        return addcslashes(trim($term), '%_\\');
    }
}
