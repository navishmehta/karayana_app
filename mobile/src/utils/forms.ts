import type { FieldValues, Path, UseFormSetError } from 'react-hook-form';

import { isApiError } from '@/api/errors';

/**
 * Put the server's per-field messages on the form. `aliases` maps API field names to form field names
 * (e.g. category_id -> category). Returns the messages that didn't match a form field.
 */
export function applyServerErrors<T extends FieldValues>(
  error: unknown,
  setError: UseFormSetError<T>,
  fields: readonly Path<T>[],
  aliases: Record<string, Path<T>> = {},
): string[] {
  if (!isApiError(error)) return [];
  const leftovers: string[] = [];
  for (const [apiField, messages] of Object.entries(error.fieldErrors)) {
    const field = aliases[apiField] ?? (apiField as Path<T>);
    if (fields.includes(field)) setError(field, { message: messages[0] });
    else leftovers.push(...messages);
  }
  return leftovers;
}

/** A fresh Idempotency-Key for one form submit. */
export const newRequestKey = () => `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;

/** Empty text -> null, otherwise trimmed text (for optional API fields). */
export const orNull = (value: string | undefined | null): string | null => (value?.trim() ? value.trim() : null);
