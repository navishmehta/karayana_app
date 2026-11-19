/** Helpers for data-loading states. */

/**
 * Show the error screen only when there is nothing to show. If saved data exists (e.g. offline, or the server
 * is briefly unreachable), the screen keeps showing it instead of an error.
 * Also a type guard: after `if (showError(q)) return …`, TypeScript knows `q.data` is loaded.
 */
export function showError<Q extends { isError: boolean; data: unknown }>(
  query: Q,
): query is Extract<Q, { isError: true; data: undefined }> {
  return query.isError && query.data === undefined;
}
