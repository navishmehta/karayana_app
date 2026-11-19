/** Swipeable product photos with page dots. */
import { useState } from 'react';
import { FlatList, StyleSheet, useWindowDimensions, View } from 'react-native';

import type { PublicImage } from '@/api/types';
import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, spacing } from '@/theme/tokens';

import { ProductImage } from './ProductImage';

const MAX_WIDTH = 720;
const DOT_SIZE = 8;

export function ImageCarousel({ images }: { images: PublicImage[] }) {
  const { colors } = useAppTheme();
  const { width: screenWidth } = useWindowDimensions();
  const width = Math.min(screenWidth, MAX_WIDTH);
  const [index, setIndex] = useState(0);

  if (images.length <= 1) return <ProductImage uri={images[0]?.url} style={{ width, alignSelf: 'center' }} iconSize={64} />;

  return (
    <View style={{ width, alignSelf: 'center' }}>
      <FlatList
        horizontal
        pagingEnabled
        data={images}
        keyExtractor={(img) => img.url}
        renderItem={({ item }) => <ProductImage uri={item.url} style={{ width }} />}
        showsHorizontalScrollIndicator={false}
        onMomentumScrollEnd={(e) => setIndex(Math.round(e.nativeEvent.contentOffset.x / width))}
      />
      <View style={styles.dots}>
        {images.map((img, i) => (
          <View key={img.url} style={[styles.dot, i === index ? [styles.dotActive, { backgroundColor: colors.primary }] : { backgroundColor: colors.border }]} />
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  // Sits over the bottom of the photo, above the product card that overlaps it.
  dots: { position: 'absolute', left: 0, right: 0, bottom: spacing.xxl, flexDirection: 'row', justifyContent: 'center', gap: spacing.xs },
  dot: { width: DOT_SIZE, height: DOT_SIZE, borderRadius: radius.pill },
  dotActive: { width: DOT_SIZE * 2.5 },
});
