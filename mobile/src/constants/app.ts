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
} as const;

export const ROLES = { admin: 'admin', seller: 'seller' } as const;
export type Role = (typeof ROLES)[keyof typeof ROLES];

/** Data fetching */
export const QUERY_STALE_MS = 60_000;
export const QUERY_RETRY_COUNT = 1;

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
export const DEVICE_NAME = 'Smart Kirana app';

/** Currency and dates */
export const CURRENCY = 'INR';
export const NUMBER_LOCALE = 'en-IN'; // Indian digit grouping: 1,23,456.00 (Western digits in every language)
export const STORE_TIME_ZONE = 'Asia/Kolkata';
