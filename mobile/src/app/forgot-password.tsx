import { zodResolver } from '@hookform/resolvers/zod';
import { router } from 'expo-router';
import { useState } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { authApi } from '@/api/endpoints';
import { AppText, Button, Card, Screen, TextField } from '@/components/ui';
import { RESET_CODE_LENGTH } from '@/constants/app';
import { forgotSchema, resetSchema } from '@/lib/validation';
import { errorMessage } from '@/utils/errors';

/** Step 1: email → code is sent. Step 2: code + new password. */
export default function ForgotPasswordScreen() {
  const { t } = useTranslation();
  const [email, setEmail] = useState<string | null>(null);

  return (
    <Screen center edges={['top', 'bottom']}>
      <AppText size="heading" weight="bold">
        {t('auth.forgotTitle')}
      </AppText>
      <Card>{email ? <ResetStep email={email} /> : <EmailStep onSent={setEmail} />}</Card>
      <Button title={t('common.back')} variant="ghost" onPress={() => router.back()} />
    </Screen>
  );
}

function EmailStep({ onSent }: { onSent: (email: string) => void }) {
  const { t } = useTranslation();
  const [formError, setFormError] = useState<string | null>(null);
  const { control, handleSubmit, formState } = useForm<{ email: string }>({
    resolver: zodResolver(forgotSchema(t)),
    defaultValues: { email: '' },
  });

  const submit = handleSubmit(async ({ email }) => {
    setFormError(null);
    try {
      await authApi.forgotPassword(email);
      onSent(email.trim());
    } catch (error) {
      setFormError(errorMessage(error, t));
    }
  });

  return (
    <>
      <AppText color="textMuted">{t('auth.forgotSubtitle', { length: RESET_CODE_LENGTH })}</AppText>
      <Controller
        control={control}
        name="email"
        render={({ field, fieldState }) => (
          <TextField
            label={t('auth.email')}
            value={field.value}
            onChangeText={field.onChange}
            error={fieldState.error?.message}
            keyboardType="email-address"
            autoCapitalize="none"
            autoComplete="email"
          />
        )}
      />
      {formError && <AppText color="danger">{formError}</AppText>}
      <Button title={t('auth.sendCode')} onPress={() => void submit()} loading={formState.isSubmitting} fullWidth />
    </>
  );
}

interface ResetForm {
  code: string;
  password: string;
  confirm: string;
}

function ResetStep({ email }: { email: string }) {
  const { t } = useTranslation();
  const [formError, setFormError] = useState<string | null>(null);
  const { control, handleSubmit, formState } = useForm<ResetForm>({
    resolver: zodResolver(resetSchema(t)),
    defaultValues: { code: '', password: '', confirm: '' },
  });

  const submit = handleSubmit(async ({ code, password }) => {
    setFormError(null);
    try {
      await authApi.resetPassword(email, code, password);
      router.replace({ pathname: '/login', params: { notice: 'reset' } });
    } catch (error) {
      setFormError(errorMessage(error, t));
    }
  });

  return (
    <>
      <AppText color="textMuted">{t('auth.codeSentTo', { email })}</AppText>
      <Controller
        control={control}
        name="code"
        render={({ field, fieldState }) => (
          <TextField
            label={t('auth.code')}
            value={field.value}
            onChangeText={field.onChange}
            error={fieldState.error?.message}
            keyboardType="number-pad"
            maxLength={RESET_CODE_LENGTH}
            autoComplete="one-time-code"
            textContentType="oneTimeCode"
          />
        )}
      />
      <Controller
        control={control}
        name="password"
        render={({ field, fieldState }) => (
          <TextField
            label={t('auth.newPassword')}
            value={field.value}
            onChangeText={field.onChange}
            error={fieldState.error?.message}
            secure
            autoComplete="new-password"
          />
        )}
      />
      <Controller
        control={control}
        name="confirm"
        render={({ field, fieldState }) => (
          <TextField
            label={t('auth.confirmPassword')}
            value={field.value}
            onChangeText={field.onChange}
            error={fieldState.error?.message}
            secure
            autoComplete="new-password"
          />
        )}
      />
      {formError && <AppText color="danger">{formError}</AppText>}
      <Button title={t('auth.resetPassword')} onPress={() => void submit()} loading={formState.isSubmitting} fullWidth />
    </>
  );
}
