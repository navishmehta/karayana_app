<?php

/*
| App-specific settings. Values that differ per environment come from .env.
| Change a value here (or in .env) and it applies everywhere.
*/
return [
    // Business timezone: "today" for expiry and DD-MM-YYYY display. DB timestamps stay in UTC.
    'timezone' => env('STORE_TIMEZONE', 'Asia/Kolkata'),
    'currency' => env('STORE_CURRENCY', 'INR'),

    'locales' => ['en', 'pa'], // add 'hi' later

    'admin' => [
        'name' => env('ADMIN_NAME', 'Store Admin'),
        'email' => env('ADMIN_EMAIL'),
        'password' => env('ADMIN_PASSWORD'),
    ],

    'auth' => [
        'token_ttl_days' => (int) env('TOKEN_TTL_DAYS', 30),
        'password_min_length' => 8,
        'reset_code_length' => 6,
        'reset_code_ttl_minutes' => 15,
    ],

    // Uploaded images are re-encoded to WebP (also strips EXIF/GPS and any embedded payload).
    'media' => [
        'disk' => env('MEDIA_DISK', 'public'), // 'public' locally; an S3-compatible disk (R2/Spaces) in production
        'max_upload_kb' => 5120,
        'allowed_mimes' => ['jpg', 'jpeg', 'png', 'webp'],
        'full_width' => 1200,
        'thumb_width' => 400,
        'webp_quality' => 80,
        'max_images_per_product' => 6,
    ],

    // Requests per minute.
    'rate_limits' => [
        'login' => 5,           // per email + IP
        'password_reset' => 3,  // per email + IP
        'api' => 300,           // per logged-in user
        'public' => 120,        // per IP (customer catalogue)
    ],
];
