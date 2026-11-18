<?php

namespace App\Exceptions;

use App\Enums\ErrorCode;
use Illuminate\Auth\Access\AuthorizationException;
use Illuminate\Auth\AuthenticationException;
use Illuminate\Database\Eloquent\ModelNotFoundException;
use Illuminate\Http\Exceptions\ThrottleRequestsException;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Validation\ValidationException;
use Spatie\Permission\Exceptions\UnauthorizedException as PermissionDenied;
use Symfony\Component\HttpKernel\Exception\AccessDeniedHttpException;
use Symfony\Component\HttpKernel\Exception\HttpExceptionInterface;
use Symfony\Component\HttpKernel\Exception\NotFoundHttpException;
use Throwable;

/** Turns any exception on an API route into: { message, code, errors? }. */
final class ApiExceptionRenderer
{
    public function __invoke(Throwable $e, Request $request): ?JsonResponse
    {
        if (! $request->is('api/*')) {
            return null;
        }

        $code = $this->codeFor($e);
        $status = $e instanceof HttpExceptionInterface && $code === ErrorCode::HttpError
            ? $e->getStatusCode()
            : $code->httpStatus();

        $body = ['message' => $code->message(), 'code' => $code->value];

        if ($e instanceof ValidationException) {
            $body['errors'] = $e->errors();
        } elseif ($e instanceof ApiException && $e->errors) {
            $body['errors'] = $e->errors;
        }

        if ($code === ErrorCode::ServerError && config('app.debug')) {
            $body['debug'] = ['exception' => $e::class, 'message' => $e->getMessage()];
        }

        $headers = $e instanceof HttpExceptionInterface ? $e->getHeaders() : [];

        return new JsonResponse($body, $status, $headers);
    }

    private function codeFor(Throwable $e): ErrorCode
    {
        return match (true) {
            $e instanceof ApiException => $e->errorCode,
            $e instanceof ValidationException => ErrorCode::ValidationFailed,
            $e instanceof AuthenticationException => ErrorCode::Unauthenticated,
            $e instanceof AuthorizationException,
            $e instanceof AccessDeniedHttpException,
            $e instanceof PermissionDenied => ErrorCode::Forbidden,
            $e instanceof ModelNotFoundException,
            $e instanceof NotFoundHttpException => ErrorCode::NotFound,
            $e instanceof ThrottleRequestsException => ErrorCode::TooManyRequests,
            $e instanceof HttpExceptionInterface => ErrorCode::HttpError,
            default => ErrorCode::ServerError,
        };
    }
}
