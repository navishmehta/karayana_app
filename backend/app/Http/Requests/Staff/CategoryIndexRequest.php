<?php

namespace App\Http\Requests\Staff;

use App\Constants\AppConstants;
use App\Enums\CategorySort;
use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;

class CategoryIndexRequest extends FormRequest
{
    public function rules(): array
    {
        return [
            'search' => ['sometimes', 'nullable', 'string', 'max:'.AppConstants::MAX_SEARCH_LENGTH],
            'status' => ['sometimes', Rule::in(['active', 'inactive'])],
            'sort' => ['sometimes', Rule::enum(CategorySort::class)],
            'per_page' => ['sometimes', 'integer', 'min:1', 'max:'.AppConstants::MAX_PER_PAGE],
        ];
    }
}
