<?php

namespace App\Rules;

use App\Constants\AppConstants;
use App\Support\CurrentStore;
use Illuminate\Validation\Rule;
use Illuminate\Validation\Rules\Exists;
use Illuminate\Validation\Rules\Unique;

/** Field rules shared by catalogue requests (categories, products, brands, units). */
final class CatalogueRules
{
    public static function price(): array
    {
        return ['numeric', 'min:0', 'max:'.AppConstants::MAX_PRICE, 'decimal:0,'.AppConstants::MONEY_DECIMALS];
    }

    public static function quantity(): array
    {
        return ['numeric', 'min:0', 'max:'.AppConstants::MAX_QUANTITY, 'decimal:0,'.AppConstants::QUANTITY_DECIMALS];
    }

    public static function image(): array
    {
        $media = config('kirana.media');

        return ['image', 'mimes:'.implode(',', $media['allowed_mimes']), 'max:'.$media['max_upload_kb']];
    }

    public static function date(): array
    {
        return ['date_format:'.AppConstants::API_DATE_FORMAT];
    }

    /** Optional admin-entered names in other languages, e.g. {"pa": "ਡੇਅਰੀ"}. */
    public static function translations(string $field, int $max): array
    {
        $locales = array_diff(config('kirana.locales'), [config('app.fallback_locale')]);

        return [
            $field => ['sometimes', 'nullable', 'array:'.implode(',', $locales)],
            "{$field}.*" => ['nullable', 'string', "max:{$max}"],
        ];
    }

    /** Row exists in the current store and is not deleted. */
    public static function existsInStore(string $table): Exists
    {
        return Rule::exists($table, 'id')->where('store_id', CurrentStore::id())->whereNull('deleted_at');
    }

    /** Value is unique within the current store (deleted rows included, as the DB index is). */
    public static function uniqueInStore(string $table, string $column, ?int $ignoreId = null): Unique
    {
        return Rule::unique($table, $column)->where('store_id', CurrentStore::id())->ignore($ignoreId);
    }

    /** Name unique among the store's non-deleted rows. */
    public static function uniqueActiveName(string $table, ?int $ignoreId = null): Unique
    {
        return self::uniqueInStore($table, 'name', $ignoreId)->whereNull('deleted_at');
    }
}
