/** Navigation helpers. */
import { type Href, router } from 'expo-router';

/**
 * Go back after saving — or, when there is nothing to go back to (the screen was opened directly,
 * e.g. from a notification, a link or a web page refresh), open `fallback` instead.
 */
export function goBack(fallback: Href): void {
  if (router.canGoBack()) router.back();
  else router.replace(fallback);
}
