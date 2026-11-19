/** Theme gradient background (hero headers, primary buttons, offer badges). Colours come from theme/tokens.ts. */
import { LinearGradient } from 'expo-linear-gradient';
import type { PropsWithChildren } from 'react';
import type { StyleProp, ViewStyle } from 'react-native';

import { useAppTheme } from '@/theme/ThemeProvider';
import type { ThemeGradients } from '@/theme/tokens';

const DIAGONAL = { start: { x: 0, y: 0 }, end: { x: 1, y: 1 } } as const;
const HORIZONTAL = { start: { x: 0, y: 0.5 }, end: { x: 1, y: 0.5 } } as const;

export function Gradient({
  name,
  direction = 'diagonal',
  style,
  children,
}: PropsWithChildren<{ name: keyof ThemeGradients; direction?: 'diagonal' | 'horizontal'; style?: StyleProp<ViewStyle> }>) {
  const { gradients } = useAppTheme();
  const points = direction === 'diagonal' ? DIAGONAL : HORIZONTAL;
  return (
    <LinearGradient colors={gradients[name]} start={points.start} end={points.end} style={style}>
      {children}
    </LinearGradient>
  );
}
