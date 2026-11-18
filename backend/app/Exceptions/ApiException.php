<?php

namespace App\Exceptions;

use App\Enums\ErrorCode;
use RuntimeException;

/** Business-rule failure with a stable error code, e.g. throw new ApiException(ErrorCode::AccountInactive). */
class ApiException extends RuntimeException
{
    public function __construct(public readonly ErrorCode $errorCode, public readonly array $errors = [])
    {
        parent::__construct($errorCode->value);
    }
}
