<?php

namespace App\Enums;

/** Storage folders for uploaded images. */
enum MediaFolder: string
{
    case Categories = 'categories';
    case Products = 'products';
    case Store = 'store';
}
