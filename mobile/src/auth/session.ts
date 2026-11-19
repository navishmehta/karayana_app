/**
 * Login session (zustand store).
 *  - The access token lives in memory; the refresh token in secure storage (Keychain / Keystore).
 *  - On app start `restore()` exchanges the saved refresh token for a fresh session.
 *  - The API client calls back into this store to refresh tokens or end the session.
 *  - The staff profile is also kept on the device, so staff can open the app and keep working offline;
 *    a fresh access token is fetched automatically before the first request once the internet is back.
 */
import { create } from 'zustand';

import { configureAuth } from '@/api/client';
import { authApi } from '@/api/endpoints';
import { API_ERROR_CODES, isApiError } from '@/api/errors';
import type { AuthUser, TokenPair } from '@/api/types';
import { STORAGE_KEYS } from '@/constants/app';
import { preferences, secure } from '@/lib/storage';

export type SessionStatus = 'loading' | 'guest' | 'staff';

interface SessionState {
  status: SessionStatus;
  user: AuthUser | null;
  accessToken: string | null;
  restore: () => Promise<void>;
  login: (email: string, password: string) => Promise<AuthUser>;
  logout: () => Promise<void>;
  refresh: () => Promise<boolean>;
  reloadUser: () => Promise<void>;
  endSession: () => Promise<void>;
}

async function saveTokens(tokens: TokenPair): Promise<void> {
  await secure.set(STORAGE_KEYS.refreshToken, tokens.refresh_token);
}

async function clearTokens(): Promise<void> {
  await secure.remove(STORAGE_KEYS.refreshToken);
  await secure.remove(STORAGE_KEYS.accessToken);
  await preferences.remove(STORAGE_KEYS.lastUser);
}

/** Profile + permissions only (no secrets): lets the staff side open without internet. */
const rememberUser = (user: AuthUser) => preferences.set(STORAGE_KEYS.lastUser, JSON.stringify(user));

async function savedUser(): Promise<AuthUser | null> {
  try {
    const raw = await preferences.get(STORAGE_KEYS.lastUser);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  } catch {
    return null;
  }
}

const isConnectionProblem = (error: unknown) =>
  isApiError(error) && (error.code === API_ERROR_CODES.network || error.code === API_ERROR_CODES.timeout);

export const useSession = create<SessionState>((set, get) => ({
  status: 'loading',
  user: null,
  accessToken: null,

  async restore() {
    const refreshToken = await secure.get(STORAGE_KEYS.refreshToken);
    if (!refreshToken) {
      set({ status: 'guest' });
      return;
    }
    try {
      if (!(await get().refresh())) return; // refresh() already ended the session
      const { data: user } = await authApi.me();
      await rememberUser(user);
      set({ status: 'staff', user });
    } catch (error) {
      if (isConnectionProblem(error)) {
        // Offline at start-up: keep the saved login. Staff work offline with the saved profile;
        // the token is renewed by the first request once the internet is back.
        const user = await savedUser();
        set(user ? { status: 'staff', user, accessToken: null } : { status: 'guest' });
        return;
      }
      await get().endSession();
    }
  },

  async login(email, password) {
    const { data } = await authApi.login(email, password);
    await saveTokens(data);
    await rememberUser(data.user);
    set({ status: 'staff', user: data.user, accessToken: data.access_token });
    return data.user;
  },

  async logout() {
    try {
      const { unregisterPush } = await import('@/lib/push'); // loaded lazily: notifications are native-only
      await unregisterPush();
      await authApi.logout();
    } catch {
      // Even if the server can't be reached, the device forgets the session.
    }
    await get().endSession();
  },

  async refresh() {
    const refreshToken = await secure.get(STORAGE_KEYS.refreshToken);
    if (!refreshToken) return false;
    try {
      const { data } = await authApi.refresh(refreshToken);
      await saveTokens(data);
      set({ accessToken: data.access_token });
      return true;
    } catch (error) {
      if (isConnectionProblem(error)) throw error;
      await get().endSession();
      return false;
    }
  },

  async reloadUser() {
    if (get().status !== 'staff') return;
    try {
      const { data: user } = await authApi.me();
      await rememberUser(user);
      set({ user });
    } catch {
      // Offline or session ended: the client already handles an ended session.
    }
  },

  async endSession() {
    await clearTokens();
    set({ status: 'guest', user: null, accessToken: null });
  },
}));

/** Reload permissions at most this often when the server refuses actions. */
const FORBIDDEN_RELOAD_GAP_MS = 5_000;
let lastForbiddenReload = 0;

configureAuth({
  getAccessToken: () => useSession.getState().accessToken,
  needsToken: () => useSession.getState().status === 'staff' && !useSession.getState().accessToken,
  refresh: () => useSession.getState().refresh(),
  onSessionEnded: () => void useSession.getState().endSession(),
  onForbidden: () => {
    const now = Date.now();
    if (now - lastForbiddenReload < FORBIDDEN_RELOAD_GAP_MS) return;
    lastForbiddenReload = now;
    void useSession.getState().reloadUser();
  },
});
