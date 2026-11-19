/** A Pressable that springs down slightly when touched and gives a light haptic tick — used by every tappable surface. */
import { Pressable, type PressableProps, type StyleProp, type ViewStyle } from 'react-native';
import Animated, { useAnimatedStyle, useSharedValue, withSpring } from 'react-native-reanimated';

import { tapFeedback } from '@/lib/haptics';
import { motion } from '@/theme/tokens';

const AnimatedPressable = Animated.createAnimatedComponent(Pressable);

export interface PressableScaleProps extends Omit<PressableProps, 'style'> {
  style?: StyleProp<ViewStyle>;
  /** Set false for very frequent taps (e.g. list rows) where a vibration would be tiring. */
  haptic?: boolean;
}

export function PressableScale({ style, haptic = true, onPressIn, onPressOut, onPress, disabled, ...rest }: PressableScaleProps) {
  const scale = useSharedValue(1);
  const animated = useAnimatedStyle(() => ({ transform: [{ scale: scale.get() }] }));

  return (
    <AnimatedPressable
      {...rest}
      disabled={disabled}
      onPress={
        onPress &&
        ((e) => {
          if (haptic) tapFeedback();
          onPress(e);
        })
      }
      onPressIn={(e) => {
        scale.set(withSpring(motion.pressScale, motion.spring));
        onPressIn?.(e);
      }}
      onPressOut={(e) => {
        scale.set(withSpring(1, motion.spring));
        onPressOut?.(e);
      }}
      style={[style, animated]}
    />
  );
}
