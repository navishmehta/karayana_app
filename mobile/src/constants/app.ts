/** Fixed app-wide values. Change them here only. */

export const LANGUAGES = [
  { code: 'en', nativeName: 'English' },
  { code: 'pa', nativeName: 'ਪੰਜਾਬੀ' },
] as const; // add { code: 'hi', nativeName: 'हिन्दी' } + locales/hi.json for Hindi

export type LanguageCode = (typeof LANGUAGES)[number]['code'];
export const DEFAULT_LANGUAGE: LanguageCode = 'en';

export const THEME_PREFERENCES = ['system', 'light', 'dark'] as const;
export type ThemePreference = (typeof THEME_PREFERENCES)[number];

/** Keys for on-device storage. */
export const STORAGE_KEYS = {
  language: 'pref.language',
  theme: 'pref.theme',
  accessToken: 'auth.access_token',
  refreshToken: 'auth.refresh_token',
  lastUser: 'auth.last_user', // staff profile, so the staff side opens offline
  queryCache: 'cache.queries', // data saved for offline viewing
  offlineQueue: 'offline.queue', // stock changes waiting for the internet
} as const;

export const ROLES = { admin: 'admin', seller: 'seller' } as const;
export type Role = (typeof ROLES)[keyof typeof ROLES];

/** Data fetching */
export const QUERY_STALE_MS = 60_000;
export const QUERY_RETRY_COUNT = 1;

/** Offline */
const DAY_MS = 24 * 60 * 60 * 1000;
export const OFFLINE_CACHE_MAX_AGE_MS = 7 * DAY_MS; // saved data older than this is thrown away
export const OFFLINE_BANNER_BOTTOM_OFFSET = 84; // keeps the offline pill above the tab bar

/** Catalogue */
export const CATALOGUE_PAGE_SIZE = 20; // API maximum is 50
export const SEARCH_DEBOUNCE_MS = 350;
export const PRODUCT_CARD_MIN_WIDTH = 160; // grid columns adapt to screen width
export const MAX_GRID_COLUMNS = 5;

/** Validation limits shared with the API */
export const PASSWORD_MIN_LENGTH = 8;
export const RESET_CODE_LENGTH = 6;
/** Shown on the privacy policy page; change it whenever the policy text changes (DD-MM-YYYY). */
export const PRIVACY_UPDATED = '19-11-2026';
/** Order of the privacy policy sections (text in the locale files under privacy.sections.<key>). */
export const PRIVACY_SECTIONS = ['customers', 'staff', 'photos', 'notifications', 'sharing', 'deleting'] as const;
export const DEVICE_NAME = 'Ramesh Karayana Store app';

/** Currency and dates */
export const CURRENCY = 'INR';
export const NUMBER_LOCALE = 'en-IN'; // Indian digit grouping: 1,23,456.00 (Western digits in every language)
export const STORE_TIME_ZONE = 'Asia/Kolkata';
