/**
 * Environment configuration. Values come from EXPO_PUBLIC_* variables in mobile/.env
 * (inlined at build time). Never put secrets here: everything in the app bundle is public.
 */
export const API_URL = (process.env.EXPO_PUBLIC_API_URL ?? 'http://127.0.0.1:8000').replace(/\/$/, '');
export const API_PREFIX = '/api/v1';
export const REQUEST_TIMEOUT_MS = 20_000;
