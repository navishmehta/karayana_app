import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { Pressable, StyleSheet, TextInput, View } from 'react-native';

import { useTypography } from '@/hooks/useTypography';
import { useAppTheme } from '@/theme/ThemeProvider';
import { noWebOutline, radius, shadow, spacing, TOUCH_TARGET } from '@/theme/tokens';

import { AppText } from '@/components/ui';

interface SearchBarProps {
  value?: string;
  onChangeText?: (text: string) => void;
  onPress?: () => void; // when set, the bar is a button that opens the search screen
  autoFocus?: boolean;
  /** Defaults to the product search text. */
  placeholder?: string;
}

export function SearchBar({ value, onChangeText, onPress, autoFocus, placeholder }: SearchBarProps) {
  const { colors, scheme } = useAppTheme();
  const { t } = useTranslation();
  const typography = useTypography();
  const hint = placeholder ?? t('catalogue.searchPlaceholder');
  const box = [
    styles.box,
    { backgroundColor: colors.surface, borderColor: colors.border },
    shadow('medium', colors.shadow, scheme),
  ];

  if (onPress) {
    return (
      <Pressable accessibilityRole="search" onPress={onPress} style={box}>
        <View style={[styles.searchIcon, { backgroundColor: colors.primarySoft }]}>
          <Ionicons name="search" size={18} color={colors.primary} />
        </View>
        <AppText color="textMuted">{hint}</AppText>
      </Pressable>
    );
  }

  return (
    <View style={box}>
      <Ionicons name="search" size={20} color={colors.textMuted} />
      <TextInput
        accessibilityLabel={hint}
        placeholder={hint}
        placeholderTextColor={colors.textMuted}
        value={value}
        onChangeText={onChangeText}
        autoFocus={autoFocus}
        autoCorrect={false}
        returnKeyType="search"
        style={[styles.input, noWebOutline, typography('body'), { color: colors.text }]}
      />
      {!!value && (
        <Pressable accessibilityRole="button" accessibilityLabel={t('catalogue.clearSearch')} onPress={() => onChangeText?.('')} hitSlop={spacing.sm}>
          <Ionicons name="close-circle" size={20} color={colors.textMuted} />
        </Pressable>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  box: {
    minHeight: TOUCH_TARGET + 6,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingHorizontal: spacing.md,
    borderWidth: StyleSheet.hairlineWidth,
    borderRadius: radius.pill,
  },
  searchIcon: { width: 34, height: 34, borderRadius: radius.pill, alignItems: 'center', justifyContent: 'center' },
  input: { flex: 1, paddingVertical: spacing.sm },
});
