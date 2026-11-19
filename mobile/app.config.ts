import { existsSync } from 'node:fs';

import type { ConfigContext, ExpoConfig } from 'expo/config';

/**
 * Adds the build-time values that differ per machine / account on top of app.json.
 * Set them in eas.json profiles or as EAS environment variables — never commit secrets.
 */
const EAS_PROJECT_ID = process.env.EAS_PROJECT_ID;
const GOOGLE_SERVICES_FILE = process.env.GOOGLE_SERVICES_FILE ?? './google-services.json';
/**
 * Test builds only: lets an installed Android app reach a plain-http backend on the local Wi-Fi
 * (e.g. http://192.168.1.79:8000). Store builds must leave this off and use the HTTPS server.
 */
const ALLOW_HTTP_API = process.env.ALLOW_HTTP_API === '1';

export default ({ config }: ConfigContext): ExpoConfig => ({
  ...(config as ExpoConfig),
  android: {
    ...config.android,
    // Firebase config for Android push. Only used when the file is present (it is git-ignored).
    ...(existsSync(GOOGLE_SERVICES_FILE) ? { googleServicesFile: GOOGLE_SERVICES_FILE } : {}),
  },
  plugins: [
    ...(config.plugins ?? []),
    ...(ALLOW_HTTP_API ? [['expo-build-properties', { android: { usesCleartextTraffic: true } }] as [string, unknown]] : []),
  ],
  extra: {
    ...config.extra,
    ...(EAS_PROJECT_ID ? { eas: { projectId: EAS_PROJECT_ID } } : {}),
  },
});
