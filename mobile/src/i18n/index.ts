/**
 * Translations (i18next). UI text lives in locales/<code>.json — never in components.
 * Product and category names typed by the admin are shown as entered (not auto-translated).
 */
import { getLocales } from 'expo-localization';
import i18n, { changeLanguage } from 'i18next';
import { initReactI18next } from 'react-i18next';

import { DEFAULT_LANGUAGE, LANGUAGES, type LanguageCode, STORAGE_KEYS } from '@/constants/app';
import { preferences } from '@/lib/storage';

import en from './locales/en.json';
import pa from './locales/pa.json';

export const resources = { en: { translation: en }, pa: { translation: pa } } as const;

const isSupported = (code: string | null | undefined): code is LanguageCode =>
  LANGUAGES.some((l) => l.code === code);

function deviceLanguage(): LanguageCode {
  const code = getLocales()[0]?.languageCode;
  return isSupported(code) ? code : DEFAULT_LANGUAGE;
}

// i18next's plugin API is a method on the instance (not a React hook).
// eslint-disable-next-line import/no-named-as-default-member
void i18n.use(initReactI18next).init({
  resources,
  lng: deviceLanguage(),
  fallbackLng: DEFAULT_LANGUAGE,
  interpolation: { escapeValue: false }, // React already escapes
  returnNull: false,
});

/** Saved choice wins over the device language. */
export async function restoreLanguage(): Promise<void> {
  const saved = await preferences.get(STORAGE_KEYS.language);
  if (isSupported(saved) && saved !== i18n.language) await changeLanguage(saved);
}

export async function setLanguage(code: LanguageCode): Promise<void> {
  await changeLanguage(code);
  await preferences.set(STORAGE_KEYS.language, code);
}

export const currentLanguage = (): LanguageCode => (isSupported(i18n.language) ? i18n.language : DEFAULT_LANGUAGE);

export default i18n;
