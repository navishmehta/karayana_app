import { zodResolver } from '@hookform/resolvers/zod';
import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { StyleSheet, View } from 'react-native';

import { isApiError } from '@/api/errors';
import { useSession } from '@/auth/session';
import { AppText, Button, Card, Screen, TextField } from '@/components/ui';
import { loginSchema } from '@/lib/validation';
import { spacing } from '@/theme/tokens';
import { errorMessage } from '@/utils/errors';

interface LoginForm {
  email: string;
  password: string;
}

export default function LoginScreen() {
  const { t } = useTranslation();
  const { notice } = useLocalSearchParams<{ notice?: string }>();
  const login = useSession((s) => s.login);
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
    <Screen center edges={['top', 'bottom']}>
      <View style={styles.header}>
        <AppText size="heading" weight="bold">
          {t('auth.loginTitle')}
        </AppText>
        <AppText color="textMuted">{t('auth.loginSubtitle')}</AppText>
      </View>
      <Card>
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

const styles = StyleSheet.create({ header: { gap: spacing.xs } });
