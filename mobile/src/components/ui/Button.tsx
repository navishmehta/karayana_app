import { ActivityIndicator, Pressable, StyleSheet, View } from 'react-native';

import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, spacing, TOUCH_TARGET } from '@/theme/tokens';

import { AppText } from './AppText';

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger';

export interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: Variant;
  loading?: boolean;
  disabled?: boolean;
  icon?: React.ReactNode;
  fullWidth?: boolean;
  testID?: string;
}

export function Button({ title, onPress, variant = 'primary', loading, disabled, icon, fullWidth, testID }: ButtonProps) {
  const { colors } = useAppTheme();
  const inactive = disabled || loading;

  const background = {
    primary: colors.primary,
    secondary: colors.primarySoft,
    ghost: 'transparent',
    danger: colors.danger,
  }[variant];
  const textColor = variant === 'primary' || variant === 'danger' ? 'textOnPrimary' : 'primary';

  return (
    <Pressable
      testID={testID}
      accessibilityRole="button"
      accessibilityState={{ disabled: !!inactive, busy: !!loading }}
      onPress={onPress}
      disabled={inactive}
      style={({ pressed }) => [
        styles.base,
        { backgroundColor: background, opacity: inactive ? 0.55 : pressed ? 0.85 : 1 },
        variant === 'ghost' && { borderWidth: 1, borderColor: colors.border },
        fullWidth && styles.fullWidth,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={colors[textColor]} />
      ) : (
        <View style={styles.content}>
          {icon}
          <AppText weight="semibold" color={textColor}>
            {title}
          </AppText>
        </View>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    minHeight: TOUCH_TARGET,
    paddingHorizontal: spacing.xl,
    borderRadius: radius.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  fullWidth: { alignSelf: 'stretch' },
  content: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
});
