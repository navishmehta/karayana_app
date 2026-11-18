/**
 * Download a protected file (report export) and hand it to the user:
 *  - phone: save to the cache, then open the share sheet (WhatsApp, Drive, email, Files…);
 *  - web: a normal browser download.
 */
import { File, Paths } from 'expo-file-system';
import * as Sharing from 'expo-sharing';
import { Platform } from 'react-native';

import { buildUrl } from '@/api/client';
import { ApiError } from '@/api/errors';
import { useSession } from '@/auth/session';
import i18n from '@/i18n';

type Query = Record<string, string | number | boolean | undefined>;

export async function downloadAndShare(path: string, query: Query, filename: string, mimeType: string): Promise<void> {
  // Fresh access token first: the download itself can't go through the client's automatic refresh.
  await useSession.getState().refresh();
  const token = useSession.getState().accessToken;
  const url = buildUrl(path, query);
  const headers: Record<string, string> = { 'Accept-Language': i18n.language, ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  if (Platform.OS === 'web') {
    const response = await fetch(url, { headers });
    if (!response.ok) throw await errorFrom(response);
    const blobUrl = URL.createObjectURL(await response.blob());
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(blobUrl);
    return;
  }

  const target = new File(Paths.cache, filename);
  if (target.exists) target.delete();
  const file = await File.createDownloadTask(url, target, { headers }).downloadAsync();
  if (!file) throw new ApiError(0, 'DOWNLOAD_FAILED', i18n.t('errors.generic'));
  if (await Sharing.isAvailableAsync()) {
    await Sharing.shareAsync(file.uri, { mimeType, dialogTitle: filename });
  }
}

async function errorFrom(response: Response): Promise<ApiError> {
  try {
    const body = (await response.json()) as { message: string; code: string };
    return new ApiError(response.status, body.code, body.message);
  } catch {
    return new ApiError(response.status, 'HTTP_ERROR', i18n.t('errors.generic'));
  }
}
