/** Loading, error and empty states used on every screen that loads data. */
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTranslation } from 'react-i18next';
import { ActivityIndicator, StyleSheet, View } from 'react-native';

import { useAppTheme } from '@/theme/ThemeProvider';
import { spacing } from '@/theme/tokens';

import { AppText } from './AppText';
import { Button } from './Button';

export function LoadingView({ label }: { label?: string }) {
  const { colors } = useAppTheme();
  const { t } = useTranslation();
  return (
    <View style={styles.center} accessibilityRole="progressbar" accessibilityLabel={label ?? t('common.loading')}>
      <ActivityIndicator size="large" color={colors.primary} />
      <AppText color="textMuted">{label ?? t('common.loading')}</AppText>
    </View>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  const { colors } = useAppTheme();
  const { t } = useTranslation();
  return (
    <View style={styles.center}>
      <Ionicons name="cloud-offline-outline" size={48} color={colors.textMuted} />
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
  const { colors } = useAppTheme();
  return (
    <View style={styles.center}>
      <Ionicons name={icon} size={48} color={colors.textMuted} />
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
});
