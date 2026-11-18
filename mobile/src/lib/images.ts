/** Pick a photo and wrap it for upload (multipart field "image"). Works on Android, iOS and web. */
import * as ImagePicker from 'expo-image-picker';
import { Platform } from 'react-native';

const IMAGE_QUALITY = 0.85; // the server re-encodes to WebP anyway

export async function pickImageForm(): Promise<FormData | null> {
  const result = await ImagePicker.launchImageLibraryAsync({
    mediaTypes: ['images'],
    allowsEditing: true,
    aspect: [1, 1],
    quality: IMAGE_QUALITY,
  });
  if (result.canceled || !result.assets[0]) return null;

  const asset = result.assets[0];
  const name = asset.fileName ?? 'photo.jpg';
  const type = asset.mimeType ?? 'image/jpeg';
  const form = new FormData();
  if (Platform.OS === 'web') {
    const blob = await (await fetch(asset.uri)).blob();
    form.append('image', blob, name);
  } else {
    // React Native's FormData accepts a file descriptor object.
    form.append('image', { uri: asset.uri, name, type } as unknown as Blob);
  }
  return form;
}
