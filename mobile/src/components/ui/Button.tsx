import { ActivityIndicator, StyleSheet, View } from 'react-native';

import { useAppTheme } from '@/theme/ThemeProvider';
import { glow, radius, spacing, TOUCH_TARGET } from '@/theme/tokens';

import { AppText } from './AppText';
import { Gradient } from './Gradient';
import { PressableScale } from './PressableScale';

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

/** Primary buttons use the brand gradient with a soft glow; the others are flat. */
export function Button({ title, onPress, variant = 'primary', loading, disabled, icon, fullWidth, testID }: ButtonProps) {
  const { colors } = useAppTheme();
  const inactive = disabled || loading;
  const textColor = variant === 'primary' || variant === 'danger' ? 'textOnPrimary' : 'primary';

  const content = loading ? (
    <ActivityIndicator color={colors[textColor]} />
  ) : (
    <View style={styles.content}>
      {icon}
      <AppText weight="semibold" color={textColor}>
        {title}
      </AppText>
    </View>
  );

  const flat = {
    secondary: { backgroundColor: colors.primarySoft },
    ghost: { borderWidth: 1, borderColor: colors.border, backgroundColor: 'transparent' },
    danger: { backgroundColor: colors.danger, ...glow(colors.danger) },
    primary: glow(colors.primary),
  }[variant];

  return (
    <PressableScale
      testID={testID}
      accessibilityRole="button"
      accessibilityState={{ disabled: !!inactive, busy: !!loading }}
      onPress={onPress}
      disabled={inactive}
      style={[styles.shell, flat, inactive && styles.inactive, fullWidth && styles.fullWidth]}
    >
      {variant === 'primary' ? (
        <Gradient name="primary" direction="horizontal" style={styles.base}>
          {content}
        </Gradient>
      ) : (
        <View style={styles.base}>{content}</View>
      )}
    </PressableScale>
  );
}

const styles = StyleSheet.create({
  shell: { borderRadius: radius.md },
  base: {
    minHeight: TOUCH_TARGET + 4,
    paddingHorizontal: spacing.xl,
    borderRadius: radius.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  inactive: { opacity: 0.5, shadowOpacity: 0, elevation: 0 },
  fullWidth: { alignSelf: 'stretch' },
  content: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
});
