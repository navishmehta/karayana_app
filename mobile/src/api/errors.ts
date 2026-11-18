/** Error codes from the backend (backend/app/enums/error_code.py) that the app reacts to. */
export const API_ERROR_CODES = {
  validationFailed: 'VALIDATION_FAILED',
  unauthenticated: 'UNAUTHENTICATED',
  tokenExpired: 'TOKEN_EXPIRED',
  invalidCredentials: 'INVALID_CREDENTIALS',
  accountInactive: 'ACCOUNT_INACTIVE',
  forbidden: 'FORBIDDEN',
  notFound: 'NOT_FOUND',
  tooManyRequests: 'TOO_MANY_REQUESTS',
  // Raised by the app itself:
  network: 'NETWORK_ERROR',
  timeout: 'TIMEOUT',
} as const;

/**
 * Any failed API call. `message` is already translated by the server (Accept-Language),
 * `fieldErrors` holds per-field messages for forms.
 */
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
    public readonly fieldErrors: Record<string, string[]> = {},
  ) {
    super(message);
    this.name = 'ApiError';
  }

  fieldError(field: string): string | undefined {
    return this.fieldErrors[field]?.[0];
  }
}

export const isApiError = (error: unknown): error is ApiError => error instanceof ApiError;
