/** Header for pages opened on top of the tabs (category, product): back button + title. */
import Ionicons from '@expo/vector-icons/Ionicons';
import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { Pressable, StyleSheet, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { AppText } from './AppText';
import { useAppTheme } from '@/theme/ThemeProvider';
import { spacing, TOUCH_TARGET } from '@/theme/tokens';

export function ScreenHeader({ title, right }: { title: string; right?: React.ReactNode }) {
  const { colors } = useAppTheme();
  const { t } = useTranslation();
  const insets = useSafeAreaInsets();
  return (
    <View style={[styles.bar, { paddingTop: insets.top, backgroundColor: colors.surface, borderBottomColor: colors.border }]}>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={t('common.back')}
        onPress={() => (router.canGoBack() ? router.back() : router.replace('/'))}
        style={styles.button}
      >
        <Ionicons name="arrow-back" size={24} color={colors.text} />
      </Pressable>
      <AppText size="subtitle" weight="semibold" numberOfLines={1} style={styles.title}>
        {title}
      </AppText>
      <View style={styles.button}>{right}</View>
    </View>
  );
}

const styles = StyleSheet.create({
  bar: { flexDirection: 'row', alignItems: 'center', borderBottomWidth: StyleSheet.hairlineWidth, paddingHorizontal: spacing.xs },
  button: { width: TOUCH_TARGET, height: TOUCH_TARGET, alignItems: 'center', justifyContent: 'center' },
  title: { flex: 1, textAlign: 'center' },
});
