<?php

namespace App\Enums;

/**
 * Every app setting in one place: key, default value, and whether customers may see it.
 * The seeder, the settings service and the public API all read from here.
 */
enum SettingKey: string
{
    case StoreName = 'store.name';
    case StoreTagline = 'store.tagline';
    case StoreLogo = 'store.logo';
    case StorePhone = 'store.phone';
    case StoreWhatsapp = 'store.whatsapp';
    case StoreAddress = 'store.address';
    case StoreHours = 'store.hours';

    case OffersEnabled = 'catalogue.offers_enabled';
    case ShowOutOfStock = 'catalogue.show_out_of_stock';

    case DefaultMinStock = 'inventory.default_min_stock';
    case ExpiryBuckets = 'expiry.buckets';

    case NotifyLowStock = 'notifications.low_stock.enabled';
    case NotifyOutOfStock = 'notifications.out_of_stock.enabled';
    case NotifyExpiry = 'notifications.expiry.enabled';
    case ExpiryDigestTime = 'notifications.expiry.digest_time';

    public function default(): mixed
    {
        return match ($this) {
            self::StoreName => config('app.name'),
            self::OffersEnabled, self::ShowOutOfStock,
            self::NotifyLowStock, self::NotifyOutOfStock, self::NotifyExpiry => true,
            self::DefaultMinStock => 5,
            self::ExpiryBuckets => [7, 15, 30],
            self::ExpiryDigestTime => '08:00',
            default => null,
        };
    }

    /** Public settings are served to customers by the catalogue API. */
    public function isPublic(): bool
    {
        return str_starts_with($this->value, 'store.') || str_starts_with($this->value, 'catalogue.');
    }
}
