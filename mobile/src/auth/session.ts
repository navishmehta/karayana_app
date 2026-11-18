/**
 * Login session (zustand store).
 *  - The access token lives in memory; the refresh token in secure storage (Keychain / Keystore).
 *  - On app start `restore()` exchanges the saved refresh token for a fresh session.
 *  - The API client calls back into this store to refresh tokens or end the session.
 */
import { create } from 'zustand';

import { configureAuth } from '@/api/client';
import { authApi } from '@/api/endpoints';
import { API_ERROR_CODES, isApiError } from '@/api/errors';
import type { AuthUser, TokenPair } from '@/api/types';
import { STORAGE_KEYS } from '@/constants/app';
import { secure } from '@/lib/storage';

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
}

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
      set({ status: 'staff', user });
    } catch (error) {
      // Offline at start-up: keep the saved login and open the customer side; next start retries.
      if (isApiError(error) && (error.code === API_ERROR_CODES.network || error.code === API_ERROR_CODES.timeout)) {
        set({ status: 'guest' });
        return;
      }
      await get().endSession();
    }
  },

  async login(email, password) {
    const { data } = await authApi.login(email, password);
    await saveTokens(data);
    set({ status: 'staff', user: data.user, accessToken: data.access_token });
    return data.user;
  },

  async logout() {
    try {
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
      if (isApiError(error) && (error.code === API_ERROR_CODES.network || error.code === API_ERROR_CODES.timeout)) {
        throw error;
      }
      await get().endSession();
      return false;
    }
  },

  async reloadUser() {
    if (get().status !== 'staff') return;
    try {
      const { data: user } = await authApi.me();
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
  refresh: () => useSession.getState().refresh(),
  onSessionEnded: () => void useSession.getState().endSession(),
  onForbidden: () => {
    const now = Date.now();
    if (now - lastForbiddenReload < FORBIDDEN_RELOAD_GAP_MS) return;
    lastForbiddenReload = now;
    void useSession.getState().reloadUser();
  },
});
