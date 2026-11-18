/** Form validation rules (zod). Messages are translated; the server re-checks everything. */
import type { TFunction } from 'i18next';
import { z } from 'zod';

import { PASSWORD_MIN_LENGTH, RESET_CODE_LENGTH } from '@/constants/app';

export const emailField = (t: TFunction) =>
  z.string().trim().min(1, t('validation.required')).email(t('validation.email'));

export const newPasswordField = (t: TFunction) =>
  z
    .string()
    .min(PASSWORD_MIN_LENGTH, t('validation.passwordWeak', { min: PASSWORD_MIN_LENGTH }))
    .regex(/[A-Za-z]/, t('validation.passwordWeak', { min: PASSWORD_MIN_LENGTH }))
    .regex(/\d/, t('validation.passwordWeak', { min: PASSWORD_MIN_LENGTH }));

export const loginSchema = (t: TFunction) =>
  z.object({ email: emailField(t), password: z.string().min(1, t('validation.required')) });

export const forgotSchema = (t: TFunction) => z.object({ email: emailField(t) });

export const resetSchema = (t: TFunction) =>
  z
    .object({
      code: z
        .string()
        .trim()
        .regex(new RegExp(`^\\d{${RESET_CODE_LENGTH}}$`), t('validation.codeLength', { length: RESET_CODE_LENGTH })),
      password: newPasswordField(t),
      confirm: z.string(),
    })
    .refine((v) => v.password === v.confirm, { path: ['confirm'], message: t('validation.passwordMismatch') });
