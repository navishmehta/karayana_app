import { StyleSheet, View, type ViewProps } from 'react-native';

import { useAppTheme } from '@/theme/ThemeProvider';
import { type Elevation, radius, shadow, spacing } from '@/theme/tokens';

export interface CardProps extends ViewProps {
  /** How far the card floats. Light mode shows a soft shadow; dark mode a subtle border. */
  elevation?: Elevation;
  /** Remove the inner padding (e.g. for edge-to-edge images or lists). */
  flush?: boolean;
}

export function Card({ style, elevation = 'medium', flush, ...rest }: CardProps) {
  const { colors, scheme } = useAppTheme();
  return (
    <View
      style={[
        styles.card,
        { backgroundColor: colors.surface },
        scheme === 'dark' ? { borderWidth: StyleSheet.hairlineWidth, borderColor: colors.border } : null,
        shadow(elevation, colors.shadow, scheme),
        flush && styles.flush,
        style,
      ]}
      {...rest}
    />
  );
}

const styles = StyleSheet.create({
  card: { borderRadius: radius.lg, padding: spacing.lg, gap: spacing.md },
  flush: { padding: 0, gap: 0, overflow: 'hidden' },
});
