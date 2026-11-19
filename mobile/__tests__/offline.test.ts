import { ApiError } from '@/api/errors';
import { inventoryApi } from '@/api/staff/endpoints';
import { useSession } from '@/auth/session';
import { authApi } from '@/api/endpoints';
import { useOfflineQueue } from '@/lib/offlineQueue';
import { preferences, secure } from '@/lib/storage';
import { showError } from '@/utils/query';

jest.mock('@/lib/network', () => ({ isOnline: jest.fn(() => true) }));
jest.mock('@/hooks/useStaff', () => ({ refreshAfterChange: jest.fn(async () => undefined) }));

const network = jest.requireMock('@/lib/network') as { isOnline: jest.Mock };
const offline = () => new ApiError(0, 'NETWORK_ERROR', 'offline');
const move = jest.spyOn(inventoryApi, 'move');

const queue = (...labels: string[]) => {
  useOfflineQueue.setState({ items: [], syncing: false });
  for (const label of labels) useOfflineQueue.getState().add({ key: `key-${label}`, kind: 'stock-out', body: { label }, label });
};

beforeEach(() => {
  move.mockReset();
  network.isOnline.mockReturnValue(true);
});

describe('offline stock changes', () => {
  it('sends queued changes oldest first, with the key they were saved with', async () => {
    queue('a', 'b');
    move.mockResolvedValue({ data: {} } as never);
    await useOfflineQueue.getState().sync();
    expect(move.mock.calls.map((c) => c[2])).toEqual(['key-a', 'key-b']); // same key: never counted twice
    expect(useOfflineQueue.getState().items).toEqual([]);
  });

  it('stops while the connection is down and keeps the rest in order', async () => {
    queue('a', 'b');
    move.mockRejectedValueOnce(offline());
    await useOfflineQueue.getState().sync();
    expect(move).toHaveBeenCalledTimes(1);
    expect(useOfflineQueue.getState().items.map((i) => i.label)).toEqual(['a', 'b']);
  });

  it('keeps a refused change with the reason and carries on with the others', async () => {
    queue('a', 'b');
    move.mockRejectedValueOnce(new ApiError(409, 'STOCK_INSUFFICIENT', 'Only 2 left.')).mockResolvedValueOnce({ data: {} } as never);
    await useOfflineQueue.getState().sync();
    expect(useOfflineQueue.getState().items).toMatchObject([{ label: 'a', error: 'Only 2 left.' }]);
  });

  it('does nothing while offline', async () => {
    queue('a');
    network.isOnline.mockReturnValue(false);
    await useOfflineQueue.getState().sync();
    expect(move).not.toHaveBeenCalled();
  });
});

describe('opening the app without internet', () => {
  const user = { id: 1, name: 'Ramesh', email: 'a@example.com', phone: null, locale: 'en', role: 'admin', permissions: [], last_login_at: null };

  let removeSecure: jest.SpyInstance;
  beforeEach(() => {
    jest.spyOn(secure, 'get').mockResolvedValue('saved-refresh-token'); // a login saved on the phone
    removeSecure = jest.spyOn(secure, 'remove').mockResolvedValue();
    jest.spyOn(authApi, 'refresh').mockRejectedValue(offline());
  });

  it('opens the staff side with the saved profile', async () => {
    await preferences.set('auth.last_user', JSON.stringify(user));
    await useSession.getState().restore();
    expect(useSession.getState()).toMatchObject({ status: 'staff', user: { name: 'Ramesh' }, accessToken: null });
  });

  it('opens the customer side if no profile was saved (and keeps the login for later)', async () => {
    await preferences.remove('auth.last_user');
    await useSession.getState().restore();
    expect(useSession.getState().status).toBe('guest');
    expect(removeSecure).not.toHaveBeenCalled(); // the saved login is kept for when the internet is back
  });
});

it('shows the error screen only when there is no saved data', () => {
  expect(showError({ isError: true, data: undefined })).toBe(true);
  expect(showError({ isError: true, data: [1] })).toBe(false);
  expect(showError({ isError: false, data: undefined })).toBe(false);
});
