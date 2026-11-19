import { zodResolver } from '@hookform/resolvers/zod';
import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import Ionicons from '@expo/vector-icons/Ionicons';
import { StyleSheet, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { isApiError } from '@/api/errors';
import { useSession } from '@/auth/session';
import { AppText, Button, Card, Gradient, Screen, TextField } from '@/components/ui';
import { useHeroStatusBar } from '@/hooks/useHeroStatusBar';
import { loginSchema } from '@/lib/validation';
import { useAppTheme } from '@/theme/ThemeProvider';
import { radius, spacing } from '@/theme/tokens';
import { errorMessage } from '@/utils/errors';

interface LoginForm {
  email: string;
  password: string;
}

export default function LoginScreen() {
  const { t } = useTranslation();
  const { notice } = useLocalSearchParams<{ notice?: string }>();
  const login = useSession((s) => s.login);
  const { colors } = useAppTheme();
  const insets = useSafeAreaInsets();
  useHeroStatusBar();
  const [formError, setFormError] = useState<string | null>(null);
  const { control, handleSubmit, setError, formState } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema(t)),
    defaultValues: { email: '', password: '' },
  });

  const submit = handleSubmit(async ({ email, password }) => {
    setFormError(null);
    try {
      await login(email, password);
      router.replace('/staff');
    } catch (error) {
      if (isApiError(error) && Object.keys(error.fieldErrors).length) {
        for (const field of ['email', 'password'] as const) {
          const message = error.fieldError(field);
          if (message) setError(field, { message });
        }
      } else {
        setFormError(errorMessage(error, t));
      }
    }
  });

  return (
    <Screen edges={['bottom']}>
      <Gradient name="hero" style={[styles.hero, { paddingTop: insets.top + spacing.xxl }]}>
        <View style={[styles.blob, styles.blobLarge]} />
        <View style={[styles.blob, styles.blobSmall]} />
        <View style={styles.mark}>
          <Ionicons name="basket" size={32} color={colors.textOnHero} />
        </View>
        <AppText size="heading" weight="bold" color="textOnHero">
          {t('auth.loginTitle')}
        </AppText>
        <AppText style={styles.heroMuted}>{t('auth.loginSubtitle')}</AppText>
      </Gradient>
      <Card elevation="high" style={styles.formCard}>
        {notice === 'reset' && <AppText color="success">{t('auth.resetDone')}</AppText>}
        <Controller
          control={control}
          name="email"
          render={({ field, fieldState }) => (
            <TextField
              label={t('auth.email')}
              value={field.value}
              onChangeText={field.onChange}
              onBlur={field.onBlur}
              error={fieldState.error?.message}
              keyboardType="email-address"
              autoCapitalize="none"
              autoComplete="email"
              textContentType="username"
            />
          )}
        />
        <Controller
          control={control}
          name="password"
          render={({ field, fieldState }) => (
            <TextField
              label={t('auth.password')}
              value={field.value}
              onChangeText={field.onChange}
              onBlur={field.onBlur}
              error={fieldState.error?.message}
              secure
              autoComplete="current-password"
              textContentType="password"
              onSubmitEditing={() => void submit()}
            />
          )}
        />
        {formError && (
          <AppText color="danger" accessibilityLiveRegion="polite">
            {formError}
          </AppText>
        )}
        <Button title={t('auth.login')} onPress={() => void submit()} loading={formState.isSubmitting} fullWidth />
        <Button title={t('auth.forgotPassword')} variant="ghost" onPress={() => router.push('/forgot-password')} />
      </Card>
      <Button title={t('common.back')} variant="ghost" onPress={() => (router.canGoBack() ? router.back() : router.replace('/'))} />
    </Screen>
  );
}

// Frosted-glass whites on the green hero (same in both themes).
const HERO_GLASS = 'rgba(255, 255, 255, 0.14)';
const HERO_MUTED = 'rgba(255, 255, 255, 0.85)';
const MARK_SIZE = 64;

const styles = StyleSheet.create({
  hero: {
    marginHorizontal: -spacing.lg,
    marginTop: -spacing.lg,
    paddingHorizontal: spacing.xl,
    paddingBottom: spacing.xxxl + spacing.xl,
    gap: spacing.xs,
    borderBottomLeftRadius: radius.xl,
    borderBottomRightRadius: radius.xl,
    overflow: 'hidden',
  },
  blob: { position: 'absolute', borderRadius: 999, backgroundColor: HERO_GLASS },
  blobLarge: { width: 220, height: 220, top: -80, right: -60 },
  blobSmall: { width: 120, height: 120, bottom: -50, left: -20 },
  mark: {
    width: MARK_SIZE,
    height: MARK_SIZE,
    borderRadius: radius.lg,
    backgroundColor: HERO_GLASS,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.md,
  },
  heroMuted: { color: HERO_MUTED },
  formCard: { marginTop: -(spacing.xxxl + spacing.md) },
});
