import { StyleSheet, Switch, View } from 'react-native';

import { useAppTheme } from '@/theme/ThemeProvider';
import { spacing, TOUCH_TARGET } from '@/theme/tokens';

import { AppText } from './AppText';

export function SwitchRow({
  label,
  hint,
  value,
  onChange,
  disabled,
}: {
  label: string;
  hint?: string;
  value: boolean;
  onChange: (value: boolean) => void;
  disabled?: boolean;
}) {
  const { colors } = useAppTheme();
  return (
    <View style={styles.row}>
      <View style={styles.text}>
        <AppText>{label}</AppText>
        {hint && (
          <AppText size="small" color="textMuted">
            {hint}
          </AppText>
        )}
      </View>
      <Switch
        accessibilityLabel={label}
        value={value}
        onValueChange={onChange}
        disabled={disabled}
        trackColor={{ true: colors.primary, false: colors.border }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  row: { minHeight: TOUCH_TARGET, flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  text: { flex: 1, gap: spacing.xxs },
});
