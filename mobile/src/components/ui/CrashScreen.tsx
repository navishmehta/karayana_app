/**
 * Shown instead of a blank screen when something unexpected breaks while drawing a screen.
 * Deliberately self-contained (no theme provider, no data, system font): it must work even when those failed.
 */
import Ionicons from '@expo/vector-icons/Ionicons';
import type { ErrorBoundaryProps } from 'expo-router';
import { router } from 'expo-router';
import { Pressable, StyleSheet, Text, useColorScheme, View } from 'react-native';

import i18n from '@/i18n';
import { colors as palette, radius, spacing, TOUCH_TARGET } from '@/theme/tokens';

export function CrashScreen({ error, retry }: ErrorBoundaryProps) {
  const colors = palette[useColorScheme() === 'dark' ? 'dark' : 'light'];
  if (__DEV__) console.error(error); // developers see the details; users never do

  return (
    <View style={[styles.root, { backgroundColor: colors.background }]}>
      <View style={[styles.icon, { backgroundColor: colors.primarySoft }]}>
        <Ionicons name="construct-outline" size={36} color={colors.primary} />
      </View>
      <Text style={[styles.title, { color: colors.text }]}>{i18n.t('crash.title')}</Text>
      <Text style={[styles.body, { color: colors.textMuted }]}>{i18n.t('crash.body')}</Text>
      <Pressable
        accessibilityRole="button"
        onPress={() => void retry()}
        style={[styles.button, { backgroundColor: colors.primary }]}
      >
        <Text style={[styles.buttonText, { color: colors.textOnPrimary }]}>{i18n.t('crash.retry')}</Text>
      </Pressable>
      <Pressable accessibilityRole="button" onPress={() => router.replace('/')} style={styles.link}>
        <Text style={[styles.linkText, { color: colors.primary }]}>{i18n.t('crash.home')}</Text>
      </Pressable>
    </View>
  );
}

const ICON = 80;

const styles = StyleSheet.create({
  root: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing.xl, gap: spacing.md },
  icon: { width: ICON, height: ICON, borderRadius: ICON / 2, alignItems: 'center', justifyContent: 'center' },
  title: { fontSize: 20, fontWeight: '700', textAlign: 'center' },
  body: { fontSize: 16, textAlign: 'center', maxWidth: 360 },
  button: {
    minHeight: TOUCH_TARGET,
    paddingHorizontal: spacing.xl,
    borderRadius: radius.md,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: spacing.md,
  },
  buttonText: { fontSize: 16, fontWeight: '600' },
  link: { minHeight: TOUCH_TARGET, justifyContent: 'center' },
  linkText: { fontSize: 16, fontWeight: '600' },
});
