import { StyleSheet, View, type ViewProps } from 'react-native';

import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, spacing } from '@/theme/tokens';

export function Card({ style, ...rest }: ViewProps) {
  const { colors, scheme } = useAppTheme();
  return (
    <View
      style={[
        styles.card,
        { backgroundColor: colors.surface, borderColor: colors.border },
        scheme === 'light' && styles.shadow,
        style,
      ]}
      {...rest}
    />
  );
}

const styles = StyleSheet.create({
  card: { borderRadius: radius.lg, borderWidth: 1, padding: spacing.lg, gap: spacing.md },
  shadow: {
    shadowColor: '#0E1412',
    shadowOpacity: 0.06,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 4 },
    elevation: 2,
  },
});
