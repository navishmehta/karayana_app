<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Unit extends Model
{
    protected $fillable = ['name', 'short_name', 'allows_decimal', 'is_active'];

    protected $casts = ['allows_decimal' => 'boolean', 'is_active' => 'boolean'];
}
