<?php

namespace App\Http\Requests\Admin;

use App\Constants\AppConstants;
use App\Enums\ActivityAction;
use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;

class ActivityLogIndexRequest extends FormRequest
{
    public function rules(): array
    {
        return [
            'causer_id' => ['sometimes', 'integer'],
            'event' => ['sometimes', Rule::enum(ActivityAction::class)],
            'log' => ['sometimes', 'string', 'max:40'],
            'from' => ['sometimes', 'date_format:'.AppConstants::API_DATE_FORMAT],
            'to' => ['sometimes', 'date_format:'.AppConstants::API_DATE_FORMAT, 'after_or_equal:from'],
            'per_page' => ['sometimes', 'integer', 'min:1', 'max:'.AppConstants::MAX_PER_PAGE],
        ];
    }
}
