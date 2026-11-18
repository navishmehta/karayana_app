<?php

namespace App\Enums;

enum StockTransactionType: string
{
    case Opening = 'opening';
    case StockIn = 'stock_in';
    case StockOut = 'stock_out';
    case AdjustmentIn = 'adjustment_in';
    case AdjustmentOut = 'adjustment_out';
    case Damaged = 'damaged';
    case Expired = 'expired';
    // Future (V2 POS / purchasing):
    case Sale = 'sale';
    case SaleReturn = 'sale_return';
    case PurchaseReturn = 'purchase_return';
}
