<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class AppSetting extends Model
{
    protected $fillable = ['store_id', 'key', 'value', 'is_public'];

    protected $casts = ['value' => 'json', 'is_public' => 'boolean'];
}
