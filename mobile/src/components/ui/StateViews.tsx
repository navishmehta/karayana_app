/** Loading, error and empty states used on every screen that loads data. */
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { useEffect } from 'react';
import { StyleSheet, View } from 'react-native';
import Animated, { useAnimatedStyle, useSharedValue, withRepeat, withTiming } from 'react-native-reanimated';

import { withAlpha } from '@/theme/color';
import { useAppTheme } from '@/theme/ThemeProvider';
import { motion, radius, spacing } from '@/theme/tokens';

import { AppText } from './AppText';
import { Button } from './Button';
import { Gradient } from './Gradient';

const PULSE_SCALE = 1.08;
const MARK_SIZE = 64;
const ICON_CIRCLE = 80;
const ICON_TINT = 0.1;

/** Brand mark gently breathing while data loads. */
export function LoadingView({ label }: { label?: string }) {
  const { colors } = useAppTheme();
  const { t } = useTranslation();
  const pulse = useSharedValue(1);
  useEffect(() => {
    pulse.set(withRepeat(withTiming(PULSE_SCALE, { duration: motion.pulseMs }), -1, true));
  }, [pulse]);
  const animated = useAnimatedStyle(() => ({ transform: [{ scale: pulse.get() }] }));

  return (
    <View
      style={[styles.center, { backgroundColor: colors.background }]}
      accessibilityRole="progressbar"
      accessibilityLabel={label ?? t('common.loading')}
    >
      <Animated.View style={animated}>
        <Gradient name="primary" style={styles.mark}>
          <Ionicons name="basket" size={30} color={colors.textOnPrimary} />
        </Gradient>
      </Animated.View>
      <AppText color="textMuted">{label ?? t('common.loading')}</AppText>
    </View>
  );
}

/** Large icon inside a soft tinted circle, for empty and error states. */
function StateIcon({ name, tone }: { name: keyof typeof Ionicons.glyphMap; tone: 'primary' | 'textMuted' }) {
  const { colors } = useAppTheme();
  return (
    <View style={[styles.iconCircle, { backgroundColor: withAlpha(colors[tone], ICON_TINT) }]}>
      <Ionicons name={name} size={36} color={colors[tone]} />
    </View>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  const { t } = useTranslation();
  return (
    <View style={styles.center}>
      <StateIcon name="cloud-offline-outline" tone="textMuted" />
      <AppText align="center" color="textMuted">
        {message}
      </AppText>
      {onRetry && <Button title={t('common.retry')} variant="secondary" onPress={onRetry} />}
    </View>
  );
}

export function EmptyState({
  icon = 'file-tray-outline',
  title,
  body,
}: {
  icon?: keyof typeof Ionicons.glyphMap;
  title: string;
  body?: string;
}) {
  return (
    <View style={styles.center}>
      <StateIcon name={icon} tone="primary" />
      <AppText size="subtitle" weight="semibold" align="center">
        {title}
      </AppText>
      {body && (
        <AppText align="center" color="textMuted">
          {body}
        </AppText>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: spacing.md, padding: spacing.xl },
  mark: { width: MARK_SIZE, height: MARK_SIZE, borderRadius: radius.lg, alignItems: 'center', justifyContent: 'center' },
  iconCircle: { width: ICON_CIRCLE, height: ICON_CIRCLE, borderRadius: ICON_CIRCLE / 2, alignItems: 'center', justifyContent: 'center' },
});
