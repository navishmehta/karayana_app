<?php

// Descriptions for App\Enums\ActivityAction.
return [
    'auth' => [
        'login' => 'Logged in',
        'login_failed' => 'Failed login attempt',
        'logout' => 'Logged out',
        'logout_all' => 'Logged out from all devices',
        'profile_updated' => 'Updated profile',
        'password_changed' => 'Changed password',
        'password_reset_requested' => 'Requested a password reset code',
        'password_reset' => 'Reset password with code',
    ],
    'sellers' => [
        'created' => 'Created seller',
        'updated' => 'Updated seller details',
        'permissions_updated' => 'Changed seller permissions',
        'activated' => 'Activated seller',
        'deactivated' => 'Deactivated seller',
        'password_reset' => 'Reset seller password',
        'deleted' => 'Deleted seller',
    ],
    'categories' => [
        'created' => 'Created category',
        'updated' => 'Updated category',
        'image_updated' => 'Changed category image',
        'image_removed' => 'Removed category image',
        'reordered' => 'Reordered categories',
        'deleted' => 'Deleted category',
    ],
    'products' => [
        'created' => 'Created product',
        'updated' => 'Updated product details',
        'price_changed' => 'Changed product prices',
        'image_added' => 'Added product image',
        'image_removed' => 'Removed product image',
        'deleted' => 'Deleted product',
        'restored' => 'Restored product',
    ],
    'brands' => ['created' => 'Created brand', 'updated' => 'Updated brand', 'deleted' => 'Deleted brand'],
    'units' => ['created' => 'Created unit', 'updated' => 'Updated unit', 'deleted' => 'Deleted unit'],
];
