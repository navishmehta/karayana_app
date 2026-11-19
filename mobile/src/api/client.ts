/**
 * HTTP client for the Smart Kirana API.
 *  - adds the base URL, JSON headers, Accept-Language and the access token;
 *  - turns every failure into an ApiError (server message + code, or a network/timeout error);
 *  - on TOKEN_EXPIRED, refreshes the session once and retries (parallel requests share one refresh).
 */
import { API_PREFIX, API_URL, REQUEST_TIMEOUT_MS } from '@/constants/config';
import i18n from '@/i18n';

import { API_ERROR_CODES, ApiError } from './errors';
import type { ApiErrorBody } from './types';

type Method = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
type QueryValue = string | number | boolean | null | undefined | (string | number)[];

export interface RequestOptions {
  method?: Method;
  body?: unknown;
  query?: Record<string, QueryValue>;
  auth?: boolean; // send the access token (default true)
  headers?: Record<string, string>;
  signal?: AbortSignal;
}

/** Provided by the session store so the client never imports it (no import cycle). */
export interface AuthBridge {
  getAccessToken: () => string | null;
  /** Logged in but without an access token yet (the app was opened offline): get one before sending. */
  needsToken?: () => boolean;
  refresh: () => Promise<boolean>; // true when new tokens were obtained
  onSessionEnded: () => void;
  /** The server refused an action: permissions may have changed, so reload them. */
  onForbidden?: () => void;
}

let auth: AuthBridge | null = null;
let refreshing: Promise<boolean> | null = null;

export function configureAuth(bridge: AuthBridge): void {
  auth = bridge;
}

export function buildUrl(path: string, query?: RequestOptions['query']): string {
  const url = `${API_URL}${API_PREFIX}${path}`;
  if (!query) return url;
  const params: string[] = [];
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === null || value === '') continue;
    for (const item of Array.isArray(value) ? value : [value]) {
      params.push(`${encodeURIComponent(key)}=${encodeURIComponent(String(item))}`);
    }
  }
  return params.length ? `${url}?${params.join('&')}` : url;
}

async function send(path: string, options: RequestOptions): Promise<Response> {
  const headers: Record<string, string> = {
    Accept: 'application/json',
    'Accept-Language': i18n.language,
    ...options.headers,
  };
  const isForm = typeof FormData !== 'undefined' && options.body instanceof FormData;
  if (options.body !== undefined && !isForm) headers['Content-Type'] = 'application/json';
  const token = options.auth === false ? null : auth?.getAccessToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort('timeout'), REQUEST_TIMEOUT_MS);
  options.signal?.addEventListener('abort', () => controller.abort(options.signal?.reason));
  try {
    return await fetch(buildUrl(path, options.query), {
      method: options.method ?? 'GET',
      headers,
      body: options.body === undefined ? undefined : isForm ? (options.body as FormData) : JSON.stringify(options.body),
      signal: controller.signal,
    });
  } catch {
    const timedOut = controller.signal.aborted && controller.signal.reason === 'timeout';
    throw timedOut
      ? new ApiError(0, API_ERROR_CODES.timeout, i18n.t('errors.timeout'))
      : new ApiError(0, API_ERROR_CODES.network, i18n.t('errors.network'));
  } finally {
    clearTimeout(timer);
  }
}

async function toApiError(response: Response): Promise<ApiError> {
  try {
    const body = (await response.json()) as ApiErrorBody;
    return new ApiError(response.status, body.code, body.message, body.errors ?? {});
  } catch {
    return new ApiError(response.status, 'HTTP_ERROR', i18n.t('errors.generic'));
  }
}

function refreshOnce(): Promise<boolean> {
  if (!auth) return Promise.resolve(false);
  refreshing ??= auth.refresh().finally(() => {
    refreshing = null;
  });
  return refreshing;
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  if (options.auth !== false && auth?.needsToken?.()) await refreshOnce();
  let response = await send(path, options);

  if (response.status === 401 && options.auth !== false && auth) {
    const error = await toApiError(response.clone());
    if (error.code === API_ERROR_CODES.tokenExpired && (await refreshOnce())) {
      response = await send(path, options);
    } else if (error.code !== API_ERROR_CODES.invalidCredentials) {
      auth.onSessionEnded();
      throw error;
    }
  }

  if (!response.ok) {
    const error = await toApiError(response);
    if (response.status === 403 && options.auth !== false && auth) {
      if (error.code === API_ERROR_CODES.accountInactive) auth.onSessionEnded(); // deactivated by the admin
      else if (error.code === API_ERROR_CODES.forbidden) auth.onForbidden?.();
    }
    throw error;
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  get: <T>(path: string, options?: Omit<RequestOptions, 'method' | 'body'>) => request<T>(path, options),
  post: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    request<T>(path, { ...options, method: 'POST', body }),
  put: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    request<T>(path, { ...options, method: 'PUT', body }),
  patch: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    request<T>(path, { ...options, method: 'PATCH', body }),
  delete: <T>(path: string, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    request<T>(path, { ...options, method: 'DELETE' }),
};
