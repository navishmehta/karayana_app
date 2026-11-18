<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class NotificationPreference extends Model
{
    protected $fillable = ['user_id', 'type', 'push_enabled', 'in_app_enabled'];

    protected $casts = ['push_enabled' => 'boolean', 'in_app_enabled' => 'boolean'];
}
