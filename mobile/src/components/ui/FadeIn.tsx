/** Content that slides up and fades in when it first appears. `index` staggers items in a list. */
import type { PropsWithChildren } from 'react';
import type { StyleProp, ViewStyle } from 'react-native';
import Animated, { FadeInDown } from 'react-native-reanimated';

import { motion } from '@/theme/tokens';

export function FadeIn({ index = 0, style, children }: PropsWithChildren<{ index?: number; style?: StyleProp<ViewStyle> }>) {
  const delay = Math.min(index * motion.enterStaggerMs, motion.enterMaxDelayMs);
  return (
    <Animated.View entering={FadeInDown.delay(delay).springify().damping(motion.spring.damping)} style={style}>
      {children}
    </Animated.View>
  );
}
