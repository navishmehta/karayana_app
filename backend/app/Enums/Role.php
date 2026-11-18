<?php

namespace App\Enums;

enum Role: string
{
    case Admin = 'admin';
    case Seller = 'seller';
    // case Customer = 'customer'; // reserved for V3 customer accounts
}
