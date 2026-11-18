<?php

namespace App\Models;

use App\Models\Concerns\BelongsToStore;
use Illuminate\Database\Eloquent\Model;

class AppSetting extends Model
{
    use BelongsToStore;

    protected $fillable = ['store_id', 'key', 'value', 'is_public'];

    protected $casts = ['value' => 'json', 'is_public' => 'boolean'];
}
