/**
 * On-device storage.
 *  - preferences: AsyncStorage (language, theme) — not sensitive.
 *  - secure: Keychain / Keystore via expo-secure-store for login tokens.
 *    expo-secure-store has no web support, so the web build falls back to localStorage.
 */
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

export const preferences = {
  get: (key: string): Promise<string | null> => AsyncStorage.getItem(key),
  set: (key: string, value: string): Promise<void> => AsyncStorage.setItem(key, value),
};

const isWeb = Platform.OS === 'web';

export const secure = {
  async get(key: string): Promise<string | null> {
    if (isWeb) return globalThis.localStorage?.getItem(key) ?? null;
    return SecureStore.getItemAsync(key);
  },
  async set(key: string, value: string): Promise<void> {
    if (isWeb) {
      globalThis.localStorage?.setItem(key, value);
      return;
    }
    await SecureStore.setItemAsync(key, value);
  },
  async remove(key: string): Promise<void> {
    if (isWeb) {
      globalThis.localStorage?.removeItem(key);
      return;
    }
    await SecureStore.deleteItemAsync(key);
  },
};
