import type { TFunction } from 'i18next';

import { isApiError } from '@/api/errors';

/** A message for any error: the server's translated message, or a generic one. */
export function errorMessage(error: unknown, t: TFunction): string {
  if (isApiError(error)) return error.message;
  return t('errors.generic');
}
