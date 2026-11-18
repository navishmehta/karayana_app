import Ionicons from '@expo/vector-icons/Ionicons';
import { Image } from 'expo-image';
import { StyleSheet, View, type ViewStyle } from 'react-native';

import { useAppTheme } from '@/theme/ThemeProvider';

/** Only box properties that both the photo and its placeholder support. */
type PhotoBoxStyle = Pick<ViewStyle, 'width' | 'alignSelf' | 'opacity' | 'borderRadius'>;

/** Product photo with a neutral placeholder when there is none. Images are cached by expo-image. */
export function ProductImage({ uri, style, iconSize = 32 }: { uri?: string | null; style?: PhotoBoxStyle; iconSize?: number }) {
  const { colors } = useAppTheme();
  if (!uri) {
    return (
      <View style={[styles.fill, styles.placeholder, { backgroundColor: colors.surfaceAlt }, style]}>
        <Ionicons name="basket-outline" size={iconSize} color={colors.textMuted} />
      </View>
    );
  }
  return (
    <Image
      source={uri}
      style={[styles.fill, { backgroundColor: colors.surfaceAlt }, style]}
      contentFit="cover"
      transition={150}
      accessibilityIgnoresInvertColors
    />
  );
}

const styles = StyleSheet.create({
  fill: { width: '100%', aspectRatio: 1 },
  placeholder: { alignItems: 'center', justifyContent: 'center' },
});
