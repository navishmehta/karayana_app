<?php

// Labels for App\Enums\Permission (nested by group).
return [
    'groups' => [
        'dashboard' => 'Dashboard',
        'products' => 'Products',
        'categories' => 'Categories',
        'pricing' => 'Pricing',
        'stock' => 'Stock',
        'expiry' => 'Expiry',
        'reports' => 'Reports',
    ],
    'dashboard' => ['view' => 'View dashboard'],
    'products' => ['view' => 'View products', 'create' => 'Add products', 'update' => 'Edit products', 'delete' => 'Delete products'],
    'categories' => ['view' => 'View categories', 'create' => 'Add categories', 'update' => 'Edit categories', 'delete' => 'Delete categories'],
    'pricing' => ['view_purchase' => 'View purchase price', 'view_selling' => 'View selling price', 'update_selling' => 'Edit selling price'],
    'stock' => ['view' => 'View stock', 'update' => 'Update stock'],
    'expiry' => ['view' => 'View expiry', 'update' => 'Update expiry'],
    'reports' => ['view' => 'View reports', 'export' => 'Export reports'],
];
