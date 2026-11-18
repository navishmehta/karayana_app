import { buildUrl, configureAuth, request } from '@/api/client';
import { ApiError } from '@/api/errors';
import i18n from '@/i18n';

const json = (status: number, body: unknown) =>
  ({ ok: status < 400, status, json: async () => body, clone() { return this; } }) as unknown as Response;

const fetchMock = jest.fn();
globalThis.fetch = fetchMock as unknown as typeof fetch;

let token = 'old-token';
const refresh = jest.fn(async () => {
  await new Promise((r) => setTimeout(r, 10));
  token = 'new-token';
  return true;
});
const onSessionEnded = jest.fn();

beforeEach(() => {
  fetchMock.mockReset();
  refresh.mockClear();
  onSessionEnded.mockClear();
  token = 'old-token';
  configureAuth({ getAccessToken: () => token, refresh, onSessionEnded });
});

it('builds URLs with query strings, skipping empty values and repeating lists', () => {
  expect(buildUrl('/products', { search: 'amul dahi', page: 2, category_id: [1, 3], brand: '', x: undefined })).toBe(
    'http://127.0.0.1:8000/api/v1/products?search=amul%20dahi&page=2&category_id=1&category_id=3',
  );
});

it('sends the language and the access token', async () => {
  await i18n.changeLanguage('pa');
  fetchMock.mockResolvedValueOnce(json(200, { data: 1 }));
  await request('/auth/me');
  const [, init] = fetchMock.mock.calls[0];
  expect(init.headers['Accept-Language']).toBe('pa');
  expect(init.headers.Authorization).toBe('Bearer old-token');
  await i18n.changeLanguage('en');
});

it('does not send the token to public endpoints', async () => {
  fetchMock.mockResolvedValueOnce(json(200, { data: 1 }));
  await request('/public/store', { auth: false });
  expect(fetchMock.mock.calls[0][1].headers.Authorization).toBeUndefined();
});

it('turns server errors into ApiError with field messages', async () => {
  fetchMock.mockResolvedValueOnce(
    json(422, { message: 'Please check', code: 'VALIDATION_FAILED', errors: { email: ['Email is required.'] } }),
  );
  const error = (await request('/auth/login', { method: 'POST', body: {}, auth: false }).catch((e) => e)) as ApiError;
  expect(error).toBeInstanceOf(ApiError);
  expect(error.code).toBe('VALIDATION_FAILED');
  expect(error.fieldError('email')).toBe('Email is required.');
});

it('reports network failures in the user language', async () => {
  fetchMock.mockRejectedValueOnce(new TypeError('Network request failed'));
  const error = (await request('/public/store', { auth: false }).catch((e) => e)) as ApiError;
  expect(error.code).toBe('NETWORK_ERROR');
  expect(error.message).toBe(i18n.t('errors.network'));
});

it('refreshes once for several expired requests, then retries them', async () => {
  fetchMock.mockImplementation(async (_url: string, init: RequestInit) => {
    const auth = (init.headers as Record<string, string>).Authorization;
    return auth === 'Bearer new-token'
      ? json(200, { data: 'ok' })
      : json(401, { message: 'expired', code: 'TOKEN_EXPIRED' });
  });

  const results = await Promise.all([request('/a'), request('/b'), request('/c')]);

  expect(results).toEqual([{ data: 'ok' }, { data: 'ok' }, { data: 'ok' }]);
  expect(refresh).toHaveBeenCalledTimes(1);
});

it('ends the session when the token is no longer valid', async () => {
  fetchMock.mockResolvedValueOnce(json(401, { message: 'Please log in', code: 'UNAUTHENTICATED' }));
  await expect(request('/auth/me')).rejects.toBeInstanceOf(ApiError);
  expect(onSessionEnded).toHaveBeenCalledTimes(1);
  expect(refresh).not.toHaveBeenCalled();
});
